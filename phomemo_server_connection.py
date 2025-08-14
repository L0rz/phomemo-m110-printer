#!/usr/bin/env python3
"""
Phomemo M110 Server - ROBUSTE VERSION mit automatischer Bluetooth-Wiederverbindung
Basiert auf phomemo_server_simple.py mit erweiterten Connection-Management Features
"""

from flask import Flask, request, jsonify, render_template_string
from PIL import Image, ImageDraw, ImageFont
import io
import time
import os
import logging
import subprocess
import socket
import threading
import queue
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import signal
import sys
from datetime import datetime, timedelta

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('phomemo_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class ConnectionStatus(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"

@dataclass
class PrintJob:
    """Repräsentiert einen Druckauftrag in der Queue"""
    job_id: str
    job_type: str  # 'text', 'image', 'calibration', etc.
    data: Dict[Any, Any]
    timestamp: float
    retry_count: int = 0
    max_retries: int = 3

class RobustPhomemoM110:
    def __init__(self, mac_address):
        self.mac_address = mac_address
        self.rfcomm_device = "/dev/rfcomm0"
        self.width_pixels = 384  # Phomemo M110 Standard
        self.bytes_per_line = 48  # 384 / 8
        
        # Connection Management
        self.connection_status = ConnectionStatus.DISCONNECTED
        self.last_successful_connection = None
        self.connection_attempts = 0
        self.max_connection_attempts = 5
        self.base_retry_delay = 2  # Seconds
        self.max_retry_delay = 30  # Seconds
        
        # Print Queue
        self.print_queue = queue.Queue()
        self.queue_processor_running = False
        self.queue_thread = None
        
        # Connection Monitoring
        self.monitor_thread = None
        self.monitor_running = False
        self.heartbeat_interval = 30  # Seconds
        self.last_heartbeat = None
        
        # Statistics
        self.stats = {
            'total_jobs': 0,
            'successful_jobs': 0,
            'failed_jobs': 0,
            'reconnections': 0,
            'uptime_start': time.time()
        }
        
        self._lock = threading.Lock()
        self.start_services()
    
    def start_services(self):
        """Startet Background-Services"""
        try:
            # Queue-Processor starten
            self.queue_processor_running = True
            self.queue_thread = threading.Thread(target=self._process_print_queue, daemon=True)
            self.queue_thread.start()
            
            # Connection Monitor starten
            self.monitor_running = True
            self.monitor_thread = threading.Thread(target=self._connection_monitor, daemon=True)
            self.monitor_thread.start()
            
            logger.info("Background services started successfully")
        except Exception as e:
            logger.error(f"Failed to start services: {e}")
    
    def stop_services(self):
        """Stoppt Background-Services"""
        self.queue_processor_running = False
        self.monitor_running = False
        
        if self.queue_thread and self.queue_thread.is_alive():
            self.queue_thread.join(timeout=5)
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        
        logger.info("Background services stopped")
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Gibt detaillierten Verbindungsstatus zurück"""
        with self._lock:
            return {
                'status': self.connection_status.value,
                'connected': self.is_connected(),
                'mac': self.mac_address,
                'device': self.rfcomm_device,
                'last_successful': self.last_successful_connection.isoformat() if self.last_successful_connection else None,
                'connection_attempts': self.connection_attempts,
                'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
                'queue_size': self.print_queue.qsize(),
                'stats': self.stats.copy()
            }
    
    def is_connected(self) -> bool:
        """Prüft ob Drucker physisch verbunden ist"""
        try:
            return os.path.exists(self.rfcomm_device) and os.access(self.rfcomm_device, os.W_OK)
        except Exception:
            return False
    
    def connect_bluetooth(self, force_reconnect: bool = False) -> bool:
        """Verbindet mit dem Bluetooth-Drucker mit Retry-Logic"""
        with self._lock:
            if self.connection_status == ConnectionStatus.CONNECTING and not force_reconnect:
                return False
            
            self.connection_status = ConnectionStatus.CONNECTING
            
        try:
            logger.info(f"Attempting Bluetooth connection (attempt {self.connection_attempts + 1})")
            
            # Release existing connection
            self._release_rfcomm()
            time.sleep(1)
            
            # Create new connection
            result = subprocess.run(
                ['sudo', 'rfcomm', 'bind', '0', self.mac_address], 
                capture_output=True, text=True, timeout=20
            )
            
            if result.returncode == 0:
                time.sleep(2)
                
                if self.is_connected():
                    with self._lock:
                        self.connection_status = ConnectionStatus.CONNECTED
                        self.last_successful_connection = datetime.now()
                        self.connection_attempts = 0
                        self.stats['reconnections'] += 1
                    
                    logger.info("Bluetooth connection established successfully")
                    
                    # Test connection mit Heartbeat
                    if self._send_heartbeat():
                        return True
                    else:
                        logger.warning("Connection established but heartbeat failed")
                        return False
                else:
                    raise Exception("Device file not accessible after binding")
            else:
                raise Exception(f"rfcomm bind failed: {result.stderr}")
                
        except Exception as e:
            with self._lock:
                self.connection_attempts += 1
                if self.connection_attempts >= self.max_connection_attempts:
                    self.connection_status = ConnectionStatus.FAILED
                else:
                    self.connection_status = ConnectionStatus.DISCONNECTED
            
            logger.error(f"Bluetooth connection failed: {e}")
            return False
    
    def _release_rfcomm(self):
        """Gibt rfcomm-Verbindung frei"""
        try:
            subprocess.run(['sudo', 'rfcomm', 'release', '0'], 
                         capture_output=True, timeout=10)
        except Exception as e:
            logger.debug(f"rfcomm release failed (expected): {e}")
    
    def _auto_reconnect(self) -> bool:
        """Automatische Wiederverbindung mit exponential backoff"""
        if self.connection_attempts >= self.max_connection_attempts:
            logger.error("Max connection attempts reached, giving up")
            return False
        
        # Exponential backoff
        delay = min(self.base_retry_delay * (2 ** self.connection_attempts), self.max_retry_delay)
        logger.info(f"Auto-reconnecting in {delay} seconds...")
        time.sleep(delay)
        
        with self._lock:
            self.connection_status = ConnectionStatus.RECONNECTING
        
        return self.connect_bluetooth()
    
    def _connection_monitor(self):
        """Background-Thread für Connection-Monitoring"""
        logger.info("Connection monitor started")
        
        while self.monitor_running:
            try:
                time.sleep(self.heartbeat_interval)
                
                if not self.monitor_running:
                    break
                
                # Heartbeat senden
                if self.connection_status == ConnectionStatus.CONNECTED:
                    if not self._send_heartbeat():
                        logger.warning("Heartbeat failed, connection lost")
                        with self._lock:
                            self.connection_status = ConnectionStatus.DISCONNECTED
                        
                        # Automatische Wiederverbindung versuchen
                        if self.monitor_running:
                            self._auto_reconnect()
                
                # Bei Disconnected automatisch reconnecten
                elif self.connection_status == ConnectionStatus.DISCONNECTED:
                    if self.monitor_running and self.connection_attempts < self.max_connection_attempts:
                        self._auto_reconnect()
                        
            except Exception as e:
                logger.error(f"Connection monitor error: {e}")
                time.sleep(5)
        
        logger.info("Connection monitor stopped")
    
    def _send_heartbeat(self) -> bool:
        """Sendet Heartbeat-Befehl zum Testen der Verbindung"""
        try:
            success = self._send_command_direct(b'\x1b\x40')  # ESC @ Reset
            if success:
                with self._lock:
                    self.last_heartbeat = datetime.now()
            return success
        except Exception as e:
            logger.debug(f"Heartbeat failed: {e}")
            return False
    
    def _send_command_direct(self, command_bytes: bytes) -> bool:
        """Sendet Befehl direkt ohne Queue"""
        try:
            if not self.is_connected():
                return False
            
            with open(self.rfcomm_device, 'wb') as printer:
                printer.write(command_bytes)
                printer.flush()
                time.sleep(0.1)
            return True
        except Exception as e:
            logger.debug(f"Direct command send error: {e}")
            return False
    
    def send_command(self, command_bytes: bytes) -> bool:
        """Sendet Befehl mit automatischer Wiederverbindung"""
        try:
            # Erst direkt versuchen
            if self._send_command_direct(command_bytes):
                return True
            
            # Bei Fehler Wiederverbindung versuchen
            logger.info("Command failed, attempting reconnection...")
            if self.connect_bluetooth(force_reconnect=True):
                return self._send_command_direct(command_bytes)
            
            return False
        except Exception as e:
            logger.error(f"Send command error: {e}")
            return False
    
    def queue_print_job(self, job: PrintJob) -> str:
        """Fügt Druckauftrag zur Queue hinzu"""
        self.print_queue.put(job)
        with self._lock:
            self.stats['total_jobs'] += 1
        logger.info(f"Print job {job.job_id} queued (type: {job.job_type})")
        return job.job_id
    
    def print_text_async(self, text: str, font_size: int = 24) -> str:
        """Fügt Text-Druckauftrag zur Queue hinzu"""
        job_id = f"text_{int(time.time() * 1000)}"
        job = PrintJob(
            job_id=job_id,
            job_type='text',
            data={'text': text, 'font_size': font_size},
            timestamp=time.time()
        )
        return self.queue_print_job(job)
    
    def _process_print_queue(self):
        """Background-Thread für Print-Queue-Verarbeitung"""
        logger.info("Print queue processor started")
        
        while self.queue_processor_running:
            try:
                # Job aus Queue holen (mit Timeout)
                try:
                    job = self.print_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                if not self.queue_processor_running:
                    break
                
                logger.info(f"Processing job {job.job_id} (type: {job.job_type})")
                
                # Job verarbeiten
                success = self._process_job(job)
                
                with self._lock:
                    if success:
                        self.stats['successful_jobs'] += 1
                        logger.info(f"Job {job.job_id} completed successfully")
                    else:
                        self.stats['failed_jobs'] += 1
                        
                        # Bei Fehler Retry
                        if job.retry_count < job.max_retries:
                            job.retry_count += 1
                            logger.info(f"Job {job.job_id} failed, retrying ({job.retry_count}/{job.max_retries})")
                            time.sleep(2 ** job.retry_count)  # Exponential backoff
                            self.print_queue.put(job)
                        else:
                            logger.error(f"Job {job.job_id} failed permanently after {job.max_retries} retries")
                
                self.print_queue.task_done()
                
            except Exception as e:
                logger.error(f"Queue processor error: {e}")
                time.sleep(1)
        
        logger.info("Print queue processor stopped")
    
    def _process_job(self, job: PrintJob) -> bool:
        """Verarbeitet einzelnen Druckauftrag"""
        try:
            if job.job_type == 'text':
                return self.print_text(job.data['text'], job.data['font_size'])
            elif job.job_type == 'init':
                return self._init_printer()
            else:
                logger.error(f"Unknown job type: {job.job_type}")
                return False
        except Exception as e:
            logger.error(f"Job processing error: {e}")
            return False
    
    def _init_printer(self) -> bool:
        """Initialisiert Drucker mit mehreren Befehlen"""
        commands = [
            b'\x1b\x40',      # ESC @ - Reset
            b'\x1b\x33\x00',  # ESC 3 0 - Set line spacing
            b'\x1b\x61\x01'   # ESC a 1 - Center align
        ]
        
        for cmd in commands:
            if not self.send_command(cmd):
                return False
            time.sleep(0.2)
        
        return True
    
    def print_text(self, text: str, font_size: int = 24) -> bool:
        """Druckt Text (synchron)"""
        try:
            logger.info(f"Printing text: {text[:50]}...")
            
            # Drucker initialisieren
            if not self.send_command(b'\x1b\x40'):  # ESC @
                return False
            time.sleep(0.5)
            
            # Bild erstellen
            img = self.create_text_image(text, font_size)
            if img is None:
                return False
            
            # Bild zu Bytes konvertieren
            image_data = self.image_to_printer_format(img)
            if not image_data:
                return False
            
            # Bild senden
            success = self.send_bitmap(image_data, img.height)
            
            if success:
                time.sleep(0.5)
            
            return success
            
        except Exception as e:
            logger.error(f"Print text error: {e}")
            return False
    
    def create_text_image(self, text: str, font_size: int) -> Optional[Image.Image]:
        """Erstellt Bild aus Text (gleich wie Original)"""
        try:
            # Font laden
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf", font_size)
                except:
                    font = ImageFont.load_default()
            
            # Text vorbereiten
            lines = text.replace('\\n', '\n').split('\n')
            
            # Bildgröße berechnen
            temp_img = Image.new('RGB', (1, 1), 'white')
            temp_draw = ImageDraw.Draw(temp_img)
            
            line_heights = []
            max_width = 0
            
            for line in lines:
                bbox = temp_draw.textbbox((0, 0), line, font=font)
                line_width = bbox[2] - bbox[0]
                line_height = bbox[3] - bbox[1]
                max_width = max(max_width, line_width)
                line_heights.append(line_height)
            
            # Bild erstellen
            total_height = sum(line_heights) + (len(lines) - 1) * 5 + 40  # Padding
            img = Image.new('RGB', (self.width_pixels, total_height), 'white')
            draw = ImageDraw.Draw(img)
            
            # Text zeichnen
            y_pos = 20
            for i, line in enumerate(lines):
                if line.strip():  # Nur nicht-leere Zeilen
                    bbox = draw.textbbox((0, 0), line, font=font)
                    line_width = bbox[2] - bbox[0]
                    x_pos = (self.width_pixels - line_width) // 2  # Zentriert
                    
                    draw.text((x_pos, y_pos), line, fill='black', font=font)
                
                y_pos += line_heights[i] + 5
            
            # Zu schwarz-weiß konvertieren
            return img.convert('1')
            
        except Exception as e:
            logger.error(f"Image creation error: {e}")
            return None
    
    def image_to_printer_format(self, img: Image.Image) -> Optional[bytes]:
        """Konvertiert Bild zu Drucker-Format (gleich wie Original)"""
        try:
            width, height = img.size
            pixels = list(img.getdata())
            
            # Bild-Daten für Drucker vorbereiten
            image_bytes = []
            
            for y in range(height):
                line_bytes = []
                for x in range(0, self.width_pixels, 8):
                    byte_value = 0
                    for bit in range(8):
                        pixel_x = x + bit
                        if pixel_x < width:
                            pixel_idx = y * width + pixel_x
                            if pixel_idx < len(pixels):
                                # Schwarz = 1 bit, Weiß = 0 bit
                                if pixels[pixel_idx] == 0:  # Schwarz
                                    byte_value |= (1 << (7 - bit))
                    line_bytes.append(byte_value)
                
                # Padding auf bytes_per_line
                while len(line_bytes) < self.bytes_per_line:
                    line_bytes.append(0)
                
                image_bytes.extend(line_bytes[:self.bytes_per_line])
            
            return bytes(image_bytes)
            
        except Exception as e:
            logger.error(f"Image conversion error: {e}")
            return None
    
    def send_bitmap(self, image_data: bytes, height: int) -> bool:
        """Sendet Bitmap an Drucker (gleich wie Original)"""
        try:
            width_bytes = self.bytes_per_line  # 48 (384px / 8)
            m = 0  # 0=normal, 1=dunkler
    
            # Drucker resetten
            if not self.send_command(b'\x1b\x40'):  # ESC @
                return False
            time.sleep(0.05)
    
            # GS v 0 m xL xH yL yH
            xL = width_bytes & 0xFF
            xH = (width_bytes >> 8) & 0xFF
            yL = height & 0xFF
            yH = (height >> 8) & 0xFF
            header = bytes([0x1D, 0x76, 0x30, m, xL, xH, yL, yH])
    
            if not self.send_command(header):
                return False
    
            # In Chunks senden
            CHUNK = 1024
            for i in range(0, len(image_data), CHUNK):
                if not self.send_command(image_data[i:i+CHUNK]):
                    return False
                time.sleep(0.005)
    
            return True
        except Exception as e:
            logger.error(f"Bitmap send error: {e}")
            return False

# Web Interface (erweitert)
WEB_INTERFACE = """
<!DOCTYPE html>
<html>
<head>
    <title>Phomemo M110 Drucker - Robust</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1000px; margin: 0 auto; }
        .card { background: white; padding: 20px; margin: 20px 0; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; }
        .btn { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
        .btn:hover { background: #0056b3; }
        .btn-success { background: #28a745; }
        .btn-success:hover { background: #1e7e34; }
        .btn-warning { background: #ffc107; color: #212529; }
        .btn-warning:hover { background: #e0a800; }
        .btn-danger { background: #dc3545; }
        .btn-danger:hover { background: #c82333; }
        textarea, input, select { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }
        .status { padding: 15px; margin: 10px 0; border-radius: 5px; }
        .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        .warning { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; }
        @media (max-width: 768px) { .grid, .grid-3 { grid-template-columns: 1fr; } }
        .debug { background: #f8f9fa; border: 1px solid #dee2e6; padding: 10px; margin: 10px 0; border-radius: 5px; font-family: monospace; font-size: 12px; }
        .stats { display: flex; justify-content: space-around; text-align: center; }
        .stat-item { flex: 1; }
        .stat-value { font-size: 24px; font-weight: bold; color: #007bff; }
        .status-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
        .status-connected { background: #28a745; }
        .status-connecting { background: #ffc107; }
        .status-disconnected { background: #dc3545; }
        .status-failed { background: #6c757d; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🖨️ Phomemo M110 Drucker (Robust)</h1>
        
        <div class="card">
            <h2>🔗 Verbindungsstatus</h2>
            <div class="grid">
                <div>
                    <div id="connectionStatus"></div>
                    <button class="btn btn-success" onclick="checkConnection()">🔍 Status prüfen</button>
                    <button class="btn btn-warning" onclick="forceReconnect()">🔄 Force Reconnect</button>
                    <button class="btn btn-danger" onclick="clearQueue()">🗑️ Queue leeren</button>
                </div>
                <div>
                    <h3>📊 Statistiken</h3>
                    <div class="stats">
                        <div class="stat-item">
                            <div class="stat-value" id="totalJobs">0</div>
                            <div>Total Jobs</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value" id="successJobs">0</div>
                            <div>Erfolgreich</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value" id="failedJobs">0</div>
                            <div>Fehlgeschlagen</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value" id="queueSize">0</div>
                            <div>Queue</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="grid-3">
            <div class="card">
                <h2>📝 Text drucken</h2>
                <textarea id="textInput" rows="4" placeholder="Text eingeben...">PHOMEMO M110\\nRobust Connection\\n✓ Auto-Reconnect\\nZeit: $TIME$</textarea>
                <select id="fontSize">
                    <option value="14">Sehr Klein (14px)</option>
                    <option value="18">Klein (18px)</option>
                    <option value="22" selected>Normal (22px)</option>
                    <option value="26">Groß (26px)</option>
                    <option value="30">Extra Groß (30px)</option>
                </select>
                <br>
                <button class="btn" onclick="printText(false)">🖨️ Sofort drucken</button>
                <button class="btn btn-success" onclick="printText(true)">📤 In Queue</button>
                <button class="btn btn-warning" onclick="testLabel()">🧪 Test Label</button>
            </div>
            
            <div class="card">
                <h2>🛠️ Debug & Test</h2>
                <button class="btn" onclick="testConnection()">🔧 Test Bluetooth</button>
                <button class="btn" onclick="initPrinter()">🔄 Init Drucker</button>
                <button class="btn" onclick="sendHeartbeat()">💓 Heartbeat</button>
                <div id="debugInfo" class="debug"></div>
            </div>
            
            <div class="card">
                <h2>📋 Print Queue</h2>
                <div id="queueInfo" class="debug"></div>
                <button class="btn" onclick="getQueueStatus()">🔄 Queue Status</button>
            </div>
        </div>
        
        <div id="status"></div>
    </div>

    <script>
        let statusUpdateInterval;
        
        function checkConnection() {
            showStatus('🔍 Prüfe Verbindung...', 'info');
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    updateConnectionDisplay(data);
                    updateStats(data.stats);
                })
                .catch(error => showStatus('❌ Fehler: ' + error, 'error'));
        }
        
        function updateConnectionDisplay(data) {
            const statusMap = {
                'connected': { icon: '✅', text: 'Verbunden', class: 'status-connected' },
                'connecting': { icon: '🔄', text: 'Verbinde...', class: 'status-connecting' },
                'reconnecting': { icon: '🔃', text: 'Reconnecting...', class: 'status-connecting' },
                'disconnected': { icon: '❌', text: 'Getrennt', class: 'status-disconnected' },
                'failed': { icon: '💀', text: 'Fehlgeschlagen', class: 'status-failed' }
            };
            
            const status = statusMap[data.status] || statusMap['disconnected'];
            
            const html = `
                <div class="status ${data.connected ? 'success' : 'error'}">
                    <span class="status-indicator ${status.class}"></span>
                    <strong>${status.icon} ${status.text}</strong><br>
                    MAC: ${data.mac}<br>
                    Device: ${data.device}<br>
                    Attempts: ${data.connection_attempts}<br>
                    Last Success: ${data.last_successful ? new Date(data.last_successful).toLocaleString() : 'Never'}<br>
                    Last Heartbeat: ${data.last_heartbeat ? new Date(data.last_heartbeat).toLocaleString() : 'Never'}
                </div>
            `;
            
            document.getElementById('connectionStatus').innerHTML = html;
            document.getElementById('queueSize').textContent = data.queue_size;
        }
        
        function updateStats(stats) {
            if (stats) {
                document.getElementById('totalJobs').textContent = stats.total_jobs;
                document.getElementById('successJobs').textContent = stats.successful_jobs;
                document.getElementById('failedJobs').textContent = stats.failed_jobs;
            }
        }
        
        function forceReconnect() {
            showStatus('🔄 Force Reconnect...', 'info');
            fetch('/api/force-reconnect', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showStatus('✅ Reconnect erfolgreich!', 'success');
                        setTimeout(checkConnection, 1000);
                    } else {
                        showStatus('❌ Reconnect fehlgeschlagen: ' + (data.error || ''), 'error');
                    }
                })
                .catch(error => showStatus('❌ Fehler: ' + error, 'error'));
        }
        
        function clearQueue() {
            if (confirm('Alle Jobs in der Queue löschen?')) {
                fetch('/api/clear-queue', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        showStatus('🗑️ Queue geleert', 'info');
                        checkConnection();
                    })
                    .catch(error => showStatus('❌ Fehler: ' + error, 'error'));
            }
        }
        
        function printText(useQueue = false) {
            const text = document.getElementById('textInput').value;
            const fontSize = document.getElementById('fontSize').value;
            
            if (!text.trim()) {
                showStatus('❌ Bitte Text eingeben!', 'error');
                return;
            }
            
            // Replace $TIME$ placeholder
            const finalText = text.replace('$TIME, new Date().toLocaleTimeString());
            
            const formData = new FormData();
            formData.append('text', finalText);
            formData.append('font_size', fontSize);
            formData.append('use_queue', useQueue);
            
            const action = useQueue ? 'zur Queue hinzufügen' : 'drucken';
            showStatus(`🖨️ ${action}...`, 'info');
            
            fetch('/api/print-text', { method: 'POST', body: formData })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const msg = useQueue ? 
                            `✅ Job ${data.job_id} zur Queue hinzugefügt!` : 
                            '✅ Text gedruckt!';
                        showStatus(msg, 'success');
                        setTimeout(checkConnection, 500);
                    } else {
                        showStatus('❌ Fehler: ' + (data.error || 'Unbekannter Fehler'), 'error');
                    }
                })
                .catch(error => showStatus('❌ Fehler: ' + error, 'error'));
        }
        
        function testLabel() {
            document.getElementById('textInput').value = 
                'PHOMEMO M110\\nRobust Server\\n' + 
                new Date().toLocaleDateString() + '\\n' +
                new Date().toLocaleTimeString() + '\\n' +
                '✓ Test erfolgreich';
            printText(false);
        }
        
        function testConnection() {
            showStatus('🔧 Teste Bluetooth-Verbindung...', 'info');
            fetch('/api/test-connection', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    document.getElementById('debugInfo').innerHTML = 
                        `Test Result: ${data.success}<br>` +
                        `Message: ${data.message || ''}<br>` +
                        `Error: ${data.error || 'None'}<br>` +
                        `Timestamp: ${new Date().toLocaleTimeString()}`;
                    
                    if (data.success) {
                        showStatus('✅ Bluetooth-Test erfolgreich!', 'success');
                    } else {
                        showStatus('❌ Bluetooth-Test fehlgeschlagen', 'error');
                    }
                })
                .catch(error => showStatus('❌ Test-Fehler: ' + error, 'error'));
        }
        
        function initPrinter() {
            showStatus('🔄 Initialisiere Drucker...', 'info');
            fetch('/api/init-printer', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showStatus('✅ Drucker initialisiert!', 'success');
                    } else {
                        showStatus('❌ Init fehlgeschlagen: ' + (data.error || ''), 'error');
                    }
                })
                .catch(error => showStatus('❌ Init-Fehler: ' + error, 'error'));
        }
        
        function sendHeartbeat() {
            showStatus('💓 Sende Heartbeat...', 'info');
            fetch('/api/heartbeat', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showStatus('✅ Heartbeat OK!', 'success');
                        document.getElementById('debugInfo').innerHTML = 
                            `Heartbeat: OK<br>Response Time: ${data.response_time}ms<br>Timestamp: ${new Date().toLocaleTimeString()}`;
                    } else {
                        showStatus('❌ Heartbeat fehlgeschlagen', 'error');
                    }
                })
                .catch(error => showStatus('❌ Heartbeat-Fehler: ' + error, 'error'));
        }
        
        function getQueueStatus() {
            fetch('/api/queue-status')
                .then(response => response.json())
                .then(data => {
                    let html = `Queue Size: ${data.size}<br>Processor Running: ${data.running}<br><br>`;
                    
                    if (data.recent_jobs && data.recent_jobs.length > 0) {
                        html += 'Recent Jobs:<br>';
                        data.recent_jobs.forEach(job => {
                            const time = new Date(job.timestamp * 1000).toLocaleTimeString();
                            html += `${time} - ${job.job_type} (${job.status})<br>`;
                        });
                    } else {
                        html += 'No recent jobs';
                    }
                    
                    document.getElementById('queueInfo').innerHTML = html;
                })
                .catch(error => {
                    document.getElementById('queueInfo').innerHTML = 'Error loading queue status';
                });
        }
        
        function showStatus(message, type) {
            const statusDiv = document.getElementById('status');
            statusDiv.innerHTML = '<div class="status ' + type + '">' + message + '</div>';
            setTimeout(() => statusDiv.innerHTML = '', 8000);
        }
        
        function startStatusUpdates() {
            // Auto-update every 10 seconds
            statusUpdateInterval = setInterval(checkConnection, 10000);
        }
        
        function stopStatusUpdates() {
            if (statusUpdateInterval) {
                clearInterval(statusUpdateInterval);
            }
        }
        
        // Auto-check connection on load and start updates
        window.onload = function() {
            checkConnection();
            getQueueStatus();
            startStatusUpdates();
        };
        
        // Stop updates when page is hidden
        document.addEventListener('visibilitychange', function() {
            if (document.hidden) {
                stopStatusUpdates();
            } else {
                startStatusUpdates();
            }
        });
    </script>
</body>
</html>
"""

# API Routes (erweitert)
@app.route('/')
def index():
    return render_template_string(WEB_INTERFACE)

@app.route('/api/status')
def api_status():
    try:
        return jsonify(printer.get_connection_status())
    except Exception as e:
        return jsonify({'connected': False, 'error': str(e)})

@app.route('/api/force-reconnect', methods=['POST'])
def api_force_reconnect():
    try:
        success = printer.connect_bluetooth(force_reconnect=True)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/clear-queue', methods=['POST'])
def api_clear_queue():
    try:
        # Queue leeren
        while not printer.print_queue.empty():
            try:
                printer.print_queue.get_nowait()
                printer.print_queue.task_done()
            except queue.Empty:
                break
        
        return jsonify({'success': True, 'message': 'Queue cleared'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/print-text', methods=['POST'])
def api_print_text():
    try:
        text = request.form.get('text', '')
        font_size = int(request.form.get('font_size', 22))
        use_queue = request.form.get('use_queue', 'false').lower() == 'true'
        
        if not text.strip():
            return jsonify({'success': False, 'error': 'Kein Text'})
        
        if use_queue:
            # Asynchron über Queue
            job_id = printer.print_text_async(text, font_size)
            return jsonify({'success': True, 'job_id': job_id, 'message': 'Job queued'})
        else:
            # Synchron
            success = printer.print_text(text, font_size)
            return jsonify({'success': success})
            
    except Exception as e:
        logger.error(f"API print error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/test-connection', methods=['POST'])
def api_test_connection():
    try:
        start_time = time.time()
        
        # Test basic connectivity
        connected = printer.is_connected()
        if not connected:
            reconnect_success = printer.connect_bluetooth()
            response_time = int((time.time() - start_time) * 1000)
            return jsonify({
                'success': reconnect_success,
                'message': 'Reconnected' if reconnect_success else 'Failed to connect',
                'response_time': response_time
            })
        
        # Test sending a simple command
        test_success = printer._send_command_direct(b'\x1b\x40')  # Reset command
        response_time = int((time.time() - start_time) * 1000)
        
        return jsonify({
            'success': test_success,
            'message': 'Command sent successfully' if test_success else 'Failed to send command',
            'response_time': response_time
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/init-printer', methods=['POST'])
def api_init_printer():
    try:
        job_id = f"init_{int(time.time() * 1000)}"
        job = PrintJob(
            job_id=job_id,
            job_type='init',
            data={},
            timestamp=time.time()
        )
        printer.queue_print_job(job)
        return jsonify({'success': True, 'job_id': job_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/heartbeat', methods=['POST'])
def api_heartbeat():
    try:
        start_time = time.time()
        success = printer._send_heartbeat()
        response_time = int((time.time() - start_time) * 1000)
        
        return jsonify({
            'success': success,
            'response_time': response_time,
            'timestamp': time.time()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/queue-status')
def api_queue_status():
    try:
        # Vereinfachter Queue-Status (da wir nicht alle Jobs tracken)
        return jsonify({
            'size': printer.print_queue.qsize(),
            'running': printer.queue_processor_running,
            'recent_jobs': []  # Könnte erweitert werden mit Job-History
        })
    except Exception as e:
        return jsonify({'error': str(e)})

# Graceful Shutdown
def signal_handler(signum, frame):
    logger.info("Received shutdown signal, stopping services...")
    printer.stop_services()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Configuration
PRINTER_MAC = "12:7E:5A:E9:E5:22"  # ÄNDERN SIE DIESE MAC-ADRESSE!
printer = RobustPhomemoM110(PRINTER_MAC)

if __name__ == '__main__':
    print("🍓 Phomemo M110 ROBUST Server")
    print(f"🔵 Drucker MAC: {PRINTER_MAC}")
    print(f"📡 Device: {printer.rfcomm_device}")
    print("🌐 Web-Interface: http://RASPBERRY_IP:8080")
    print("💡 WICHTIG: MAC-Adresse in Code anpassen!")
    print("🔧 Features: Auto-Reconnect, Print Queue, Connection Monitoring")
    print("📊 Background Services: Queue Processor, Connection Monitor")
    
    try:
        app.run(host='0.0.0.0', port=8080, debug=False)
    finally:
        printer.stop_services()