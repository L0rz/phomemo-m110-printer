#!/usr/bin/env python3
"""
Phomemo M110 Printer - Robuste Bluetooth-Verbindungsklasse
"""

import os
import time
import logging
import subprocess
import threading
import queue
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

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
        self.rfcomm_process = None  # Process für rfcomm connect
        
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
        """Stoppt Background-Services und cleanup"""
        self.queue_processor_running = False
        self.monitor_running = False
        
        # Cleanup rfcomm process
        self._cleanup_rfcomm_process()
        
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
                'rfcomm_process_running': self.rfcomm_process is not None and self.rfcomm_process.poll() is None,
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
        """Verbindet mit dem Bluetooth-Drucker mit korrekter rfcomm connect Methode"""
        with self._lock:
            if self.connection_status == ConnectionStatus.CONNECTING and not force_reconnect:
                return False
            
            self.connection_status = ConnectionStatus.CONNECTING
            
        try:
            logger.info(f"Attempting Bluetooth connection (attempt {self.connection_attempts + 1})")
            
            # Release existing connection
            self._release_rfcomm()
            time.sleep(2)
            
            # Ensure pairing first (non-blocking)
            self._ensure_pairing()
            
            # Create new connection using rfcomm connect (wie in deinen Befehlen)
            cmd = ['sudo', 'rfcomm', 'connect', '0', self.mac_address, '1']
            logger.info(f"Starting rfcomm connect: {' '.join(cmd)}")
            
            self.rfcomm_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Warte kurz und prüfe ob Verbindung erfolgreich
            time.sleep(3)
            
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
                # Prüfe rfcomm Process
                if self.rfcomm_process.poll() is not None:
                    _, stderr = self.rfcomm_process.communicate()
                    raise Exception(f"rfcomm connect failed: {stderr}")
                else:
                    raise Exception("rfcomm connect running but device not accessible")
                
        except Exception as e:
            with self._lock:
                self.connection_attempts += 1
                if self.connection_attempts >= self.max_connection_attempts:
                    self.connection_status = ConnectionStatus.FAILED
                else:
                    self.connection_status = ConnectionStatus.DISCONNECTED
            
            # Cleanup bei Fehler
            self._cleanup_rfcomm_process()
            logger.error(f"Bluetooth connection failed: {e}")
            return False
    
    def _release_rfcomm(self):
        """Gibt rfcomm-Verbindung frei und beendet rfcomm connect process"""
        try:
            self._cleanup_rfcomm_process()
            subprocess.run(['sudo', 'rfcomm', 'release', '0'], 
                         capture_output=True, timeout=10)
            time.sleep(1)
        except Exception as e:
            logger.debug(f"rfcomm release failed (expected): {e}")
    
    def _cleanup_rfcomm_process(self):
        """Beendet den rfcomm connect Process"""
        if self.rfcomm_process:
            try:
                if self.rfcomm_process.poll() is None:
                    self.rfcomm_process.terminate()
                    try:
                        self.rfcomm_process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self.rfcomm_process.kill()
                        self.rfcomm_process.wait()
                self.rfcomm_process = None
            except Exception as e:
                logger.debug(f"rfcomm process cleanup failed: {e}")
    
    def _ensure_pairing(self):
        """Stellt sicher, dass der Drucker gepairt und trusted ist"""
        try:
            result = subprocess.run(
                ['bluetoothctl', 'info', self.mac_address],
                capture_output=True, text=True, timeout=10
            )
            
            if 'Device' not in result.stdout:
                logger.info("Drucker nicht gefunden, versuche pairing...")
                subprocess.run(['bluetoothctl', 'pair', self.mac_address], 
                             capture_output=True, timeout=15)
            
            subprocess.run(['bluetoothctl', 'trust', self.mac_address], 
                         capture_output=True, timeout=10)
            
        except Exception as e:
            logger.warning(f"Pairing check/setup failed: {e}")
    
    def _auto_reconnect(self) -> bool:
        """Automatische Wiederverbindung mit exponential backoff"""
        if self.connection_attempts >= self.max_connection_attempts:
            logger.error("Max connection attempts reached, giving up")
            return False
        
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
                
                if self.connection_status == ConnectionStatus.CONNECTED:
                    if not self._send_heartbeat():
                        logger.warning("Heartbeat failed, connection lost")
                        with self._lock:
                            self.connection_status = ConnectionStatus.DISCONNECTED
                        
                        if self.monitor_running:
                            self._auto_reconnect()
                
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
            if self._send_command_direct(command_bytes):
                return True
            
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
                try:
                    job = self.print_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                if not self.queue_processor_running:
                    break
                
                logger.info(f"Processing job {job.job_id} (type: {job.job_type})")
                
                success = self._process_job(job)
                
                with self._lock:
                    if success:
                        self.stats['successful_jobs'] += 1
                        logger.info(f"Job {job.job_id} completed successfully")
                    else:
                        self.stats['failed_jobs'] += 1
                        
                        if job.retry_count < job.max_retries:
                            job.retry_count += 1
                            logger.info(f"Job {job.job_id} failed, retrying ({job.retry_count}/{job.max_retries})")
                            time.sleep(2 ** job.retry_count)
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
            
            if not self.send_command(b'\x1b\x40'):  # ESC @
                return False
            time.sleep(0.5)
            
            img = self.create_text_image(text, font_size)
            if img is None:
                return False
            
            image_data = self.image_to_printer_format(img)
            if not image_data:
                return False
            
            success = self.send_bitmap(image_data, img.height)
            
            if success:
                time.sleep(0.5)
            
            return success
            
        except Exception as e:
            logger.error(f"Print text error: {e}")
            return False
    
    def create_text_image(self, text: str, font_size: int) -> Optional[Image.Image]:
        """Erstellt Bild aus Text"""
        try:
            # Font laden
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf", font_size)
                except:
                    font = ImageFont.load_default()
            
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
            
            total_height = sum(line_heights) + (len(lines) - 1) * 5 + 40
            img = Image.new('RGB', (self.width_pixels, total_height), 'white')
            draw = ImageDraw.Draw(img)
            
            # Text zeichnen
            y_pos = 20
            for i, line in enumerate(lines):
                if line.strip():
                    bbox = draw.textbbox((0, 0), line, font=font)
                    line_width = bbox[2] - bbox[0]
                    x_pos = (self.width_pixels - line_width) // 2
                    
                    draw.text((x_pos, y_pos), line, fill='black', font=font)
                
                y_pos += line_heights[i] + 5
            
            return img.convert('1')
            
        except Exception as e:
            logger.error(f"Image creation error: {e}")
            return None
    
    def image_to_printer_format(self, img: Image.Image) -> Optional[bytes]:
        """Konvertiert Bild zu Drucker-Format"""
        try:
            width, height = img.size
            pixels = list(img.getdata())
            
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
                                if pixels[pixel_idx] == 0:  # Schwarz
                                    byte_value |= (1 << (7 - bit))
                    line_bytes.append(byte_value)
                
                while len(line_bytes) < self.bytes_per_line:
                    line_bytes.append(0)
                
                image_bytes.extend(line_bytes[:self.bytes_per_line])
            
            return bytes(image_bytes)
            
        except Exception as e:
            logger.error(f"Image conversion error: {e}")
            return None
    
    def send_bitmap(self, image_data: bytes, height: int) -> bool:
        """Sendet Bitmap an Drucker"""
        try:
            width_bytes = self.bytes_per_line
            m = 0
    
            if not self.send_command(b'\x1b\x40'):  # ESC @
                return False
            time.sleep(0.05)
    
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
