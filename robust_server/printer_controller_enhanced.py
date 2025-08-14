#!/usr/bin/env python3
"""
Erweiteter Phomemo M110 Printer Controller
Mit Bildvorschau, X-Offset und konfigurierbaren Einstellungen
"""

import os
import time
import logging
import subprocess
import threading
import queue
import io
import json
import base64
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# Konfiguration importieren
from config_enhanced import *

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

@dataclass 
class ImageProcessingResult:
    """Ergebnis der Bildverarbeitung"""
    processed_image: Image.Image
    preview_base64: str
    original_size: Tuple[int, int]
    processed_size: Tuple[int, int]
    info: Dict[str, Any]

class EnhancedPhomemoM110:
    def __init__(self, mac_address):
        self.mac_address = mac_address
        self.rfcomm_device = RFCOMM_DEVICE
        self.width_pixels = PRINTER_WIDTH_PIXELS
        self.bytes_per_line = PRINTER_BYTES_PER_LINE
        
        # Label-Spezifikationen
        self.label_width_px = LABEL_WIDTH_PX
        self.label_height_px = LABEL_HEIGHT_PX
        self.label_width_mm = LABEL_WIDTH_MM
        self.label_height_mm = LABEL_HEIGHT_MM
        
        # Konfigurierbare Einstellungen
        self.settings = DEFAULT_SETTINGS.copy()
        self.load_settings()
        
        # Connection Management
        self.connection_status = ConnectionStatus.DISCONNECTED
        self.last_successful_connection = None
        self.connection_attempts = 0
        self.max_connection_attempts = MAX_CONNECTION_ATTEMPTS
        self.base_retry_delay = BASE_RETRY_DELAY
        self.max_retry_delay = MAX_RETRY_DELAY
        
        # Print Queue
        self.print_queue = queue.Queue()
        self.queue_processor_running = False
        self.queue_thread = None
        
        # Connection Monitoring
        self.monitor_thread = None
        self.monitor_running = False
        self.heartbeat_interval = HEARTBEAT_INTERVAL
        self.last_heartbeat = None
        
        # Statistics
        self.stats = {
            'total_jobs': 0,
            'successful_jobs': 0,
            'failed_jobs': 0,
            'reconnections': 0,
            'uptime_start': time.time(),
            'images_processed': 0,
            'text_jobs': 0
        }
        
        self._lock = threading.Lock()
        self.start_services()
    
    def load_settings(self):
        """Lädt persistente Einstellungen aus Datei"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    saved_settings = json.load(f)
                self.settings.update(saved_settings)
                logger.info(f"Settings loaded: {self.settings}")
            else:
                logger.info("No settings file found, using defaults")
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
    
    def save_settings(self):
        """Speichert aktuelle Einstellungen persistent"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.settings, f, indent=2)
            logger.info("Settings saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            return False
    
    def update_settings(self, new_settings: Dict[str, Any]):
        """Aktualisiert Einstellungen und speichert sie"""
        try:
            # Validierung der Einstellungen
            if 'x_offset' in new_settings:
                new_settings['x_offset'] = max(MIN_X_OFFSET, min(MAX_X_OFFSET, int(new_settings['x_offset'])))
            if 'y_offset' in new_settings:
                new_settings['y_offset'] = max(MIN_Y_OFFSET, min(MAX_Y_OFFSET, int(new_settings['y_offset'])))
            if 'dither_threshold' in new_settings:
                new_settings['dither_threshold'] = max(0, min(255, int(new_settings['dither_threshold'])))
            
            self.settings.update(new_settings)
            return self.save_settings()
        except Exception as e:
            logger.error(f"Error updating settings: {e}")
            return False
    
    def get_settings(self) -> Dict[str, Any]:
        """Gibt aktuelle Einstellungen zurück"""
        return self.settings.copy()
    
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
        """Stoppt alle Background-Services"""
        self.queue_processor_running = False
        self.monitor_running = False
        
        if self.queue_thread and self.queue_thread.is_alive():
            self.queue_thread.join(timeout=5)
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
    
    def is_connected(self):
        """Prüft ob Drucker verbunden ist"""
        return os.path.exists(self.rfcomm_device)
    
    def connect_bluetooth(self, force_reconnect=False):
        """Stellt Bluetooth-Verbindung her"""
        try:
            with self._lock:
                if self.is_connected() and not force_reconnect:
                    self.connection_status = ConnectionStatus.CONNECTED
                    return True
                
                self.connection_status = ConnectionStatus.CONNECTING
                
                # Release existing connection
                subprocess.run(['sudo', 'rfcomm', 'release', '0'], capture_output=True)
                time.sleep(1)
                
                # Create new connection
                result = subprocess.run(['sudo', 'rfcomm', 'bind', '0', self.mac_address], 
                                      capture_output=True, text=True, timeout=15)
                
                if result.returncode == 0:
                    time.sleep(2)
                    if self.is_connected():
                        self.connection_status = ConnectionStatus.CONNECTED
                        self.last_successful_connection = time.time()
                        self.connection_attempts = 0
                        logger.info("Bluetooth connection established successfully")
                        return True
                
                self.connection_status = ConnectionStatus.FAILED
                self.connection_attempts += 1
                return False
                
        except Exception as e:
            logger.error(f"Connection error: {e}")
            self.connection_status = ConnectionStatus.FAILED
            return False
    
    def send_command(self, command_bytes):
        """Sendet Kommando an Drucker"""
        try:
            if not self.is_connected():
                if not self.connect_bluetooth():
                    return False
            
            with open(self.rfcomm_device, 'wb') as printer:
                printer.write(command_bytes)
                printer.flush()
                time.sleep(0.1)
            return True
        except Exception as e:
            logger.error(f"Send command error: {e}")
            return False
    
    def process_image_for_preview(self, image_data, fit_to_label=None, maintain_aspect=None, enable_dither=None) -> Optional[ImageProcessingResult]:
        """Verarbeitet ein Bild für die Schwarz-Weiß-Vorschau"""
        try:
            # Parameter aus Einstellungen falls nicht übergeben
            if fit_to_label is None:
                fit_to_label = self.settings.get('fit_to_label_default', True)
            if maintain_aspect is None:
                maintain_aspect = self.settings.get('maintain_aspect_default', True)
            if enable_dither is None:
                enable_dither = self.settings.get('dither_enabled', True)
            
            # Bild öffnen
            if isinstance(image_data, bytes):
                img = Image.open(io.BytesIO(image_data))
            else:
                img = image_data
            
            # In RGB konvertieren falls notwendig
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            original_size = img.size
            
            # Größe anpassen wenn gewünscht
            if fit_to_label:
                target_width = self.label_width_px
                target_height = self.label_height_px
                
                if maintain_aspect:
                    # Seitenverhältnis beibehalten
                    img.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)
                    
                    # Zentrieren auf Label-Größe
                    new_img = Image.new('RGB', (target_width, target_height), 'white')
                    paste_x = (target_width - img.width) // 2
                    paste_y = (target_height - img.height) // 2
                    new_img.paste(img, (paste_x, paste_y))
                    img = new_img
                else:
                    # Direkt auf Label-Größe skalieren
                    img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            # Schwarz-Weiß konvertieren
            if enable_dither:
                # Floyd-Steinberg Dithering für bessere Qualität
                bw_img = img.convert('1', dither=Image.Dither.FLOYDSTEINBERG)
            else:
                # Einfacher Threshold
                gray_img = img.convert('L')
                threshold = self.settings.get('dither_threshold', DEFAULT_DITHER_THRESHOLD)
                bw_img = gray_img.point(lambda x: 0 if x < threshold else 255, '1')
            
            # Base64 für Web-Vorschau erstellen
            preview_buffer = io.BytesIO()
            # Für bessere Web-Darstellung in RGB konvertieren
            preview_img = bw_img.convert('RGB')
            
            # Vorschau-Größe begrenzen
            preview_img.thumbnail((PREVIEW_MAX_WIDTH, PREVIEW_MAX_HEIGHT), Image.Resampling.NEAREST)
            preview_img.save(preview_buffer, format=PREVIEW_FORMAT)
            preview_base64 = base64.b64encode(preview_buffer.getvalue()).decode('utf-8')
            
            # Statistik aktualisieren
            self.stats['images_processed'] += 1
            
            return ImageProcessingResult(
                processed_image=bw_img,
                preview_base64=preview_base64,
                original_size=original_size,
                processed_size=bw_img.size,
                info={
                    'original_width': original_size[0],
                    'original_height': original_size[1],
                    'processed_width': bw_img.size[0],
                    'processed_height': bw_img.size[1],
                    'fit_to_label': fit_to_label,
                    'maintain_aspect': maintain_aspect,
                    'dither_enabled': enable_dither,
                    'dither_threshold': self.settings.get('dither_threshold', DEFAULT_DITHER_THRESHOLD),
                    'x_offset': self.settings.get('x_offset', DEFAULT_X_OFFSET),
                    'y_offset': self.settings.get('y_offset', DEFAULT_Y_OFFSET)
                }
            )
            
        except Exception as e:
            logger.error(f"Image processing error: {e}")
            return None
    
    def apply_offsets_to_image(self, img: Image.Image) -> Image.Image:
        """Wendet X- und Y-Offsets auf ein Bild an"""
        try:
            x_offset = self.settings.get('x_offset', DEFAULT_X_OFFSET)
            y_offset = self.settings.get('y_offset', DEFAULT_Y_OFFSET)
            
            # Drucker-Bild erstellen (volle Breite)
            printer_height = max(img.height + abs(y_offset), img.height)
            printer_img = Image.new('1', (self.width_pixels, printer_height), 1)  # Weiß
            
            # X-Position berechnen
            paste_x = max(0, min(x_offset, self.width_pixels - img.width))
            
            # Y-Position berechnen  
            paste_y = max(0, y_offset) if y_offset >= 0 else 0
            
            # Bild einfügen
            printer_img.paste(img, (paste_x, paste_y))
            
            logger.info(f"Applied offsets: X={paste_x}, Y={paste_y}, Size={printer_img.size}")
            return printer_img
            
        except Exception as e:
            logger.error(f"Error applying offsets: {e}")
            return img
    
    def print_image_with_preview(self, image_data, fit_to_label=True, maintain_aspect=True, enable_dither=None):
        """Druckt ein Bild mit den aktuellen Offset-Einstellungen"""
        try:
            logger.info("Processing image for print with offsets...")
            
            # Bild verarbeiten
            result = self.process_image_for_preview(image_data, fit_to_label, maintain_aspect, enable_dither)
            if not result:
                return False
            
            processed_img = result.processed_image
            
            # Offsets anwenden
            printer_img = self.apply_offsets_to_image(processed_img)
            
            # Print Job erstellen
            job_data = {
                'type': 'processed_image',
                'image': printer_img,
                'info': result.info
            }
            
            return self.queue_print_job('image', job_data)
            
        except Exception as e:
            logger.error(f"Print image error: {e}")
            return False
    
    def print_text_immediate(self, text: str, font_size: int = 24) -> bool:
        """Druckt Text sofort (bypass Queue)"""
        try:
            img = self.create_text_image_with_offsets(text, font_size)
            if img:
                image_data = self.image_to_printer_format(img)
                if image_data:
                    success = self.send_bitmap(image_data, img.height)
                    if success:
                        self.stats['successful_jobs'] += 1
                        self.stats['text_jobs'] += 1
                    return success
            return False
        except Exception as e:
            logger.error(f"Immediate text print error: {e}")
            return False
    
    def print_image_immediate(self, image_data, fit_to_label=True, maintain_aspect=True) -> bool:
        """Druckt Bild sofort (bypass Queue)"""
        try:
            result = self.process_image_for_preview(image_data, fit_to_label, maintain_aspect)
            if result:
                printer_img = self.apply_offsets_to_image(result.processed_image)
                image_data = self.image_to_printer_format(printer_img)
                if image_data:
                    success = self.send_bitmap(image_data, printer_img.height)
                    if success:
                        self.stats['successful_jobs'] += 1
                    return success
            return False
        except Exception as e:
            logger.error(f"Immediate image print error: {e}")
            return False
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Gibt detaillierte Verbindungsinfos zurück"""
        return {
            'connected': self.is_connected(),
            'status': self.connection_status.value,
            'mac': self.mac_address,
            'device': self.rfcomm_device,
            'last_connection': self.last_successful_connection,
            'last_heartbeat': self.last_heartbeat,
            'connection_attempts': self.connection_attempts,
            'queue_size': self.print_queue.qsize(),
            'settings': self.get_settings(),
            'stats': self.stats.copy()
        }
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Gibt Queue-Status zurück"""
        return {
            'size': self.print_queue.qsize(),
            'processor_running': self.queue_processor_running,
            'stats': {
                'total_jobs': self.stats['total_jobs'],
                'successful_jobs': self.stats['successful_jobs'],
                'failed_jobs': self.stats['failed_jobs'],
                'images_processed': self.stats['images_processed'],
                'text_jobs': self.stats['text_jobs']
            }
        }
    
    def queue_print_job(self, job_type: str, data: Dict[str, Any]) -> str:
        """Fügt einen Print Job zur Queue hinzu"""
        job_id = f"{job_type}_{int(time.time() * 1000)}"
        job = PrintJob(
            job_id=job_id,
            job_type=job_type,
            data=data,
            timestamp=time.time(),
            max_retries=MAX_RETRIES_PER_JOB
        )
        
        self.print_queue.put(job)
        self.stats['total_jobs'] += 1
        logger.info(f"Queued job {job_id} of type {job_type}")
        return job_id
    
    def _process_print_queue(self):
        """Background Thread für Print Queue Processing - Placeholder"""
        while self.queue_processor_running:
            try:
                time.sleep(1)  # Simplified for now
            except Exception as e:
                logger.error(f"Queue processor error: {e}")
    
    def _connection_monitor(self):
        """Background Thread für Connection Monitoring - Placeholder"""
        while self.monitor_running:
            try:
                time.sleep(30)  # Simplified for now
            except Exception as e:
                logger.error(f"Connection monitor error: {e}")
    
    def image_to_printer_format(self, img):
        """Konvertiert PIL Image zu Drucker-Format - Simplified"""
        return b''  # Placeholder
    
    def send_bitmap(self, image_data: bytes, height: int) -> bool:
        """Sendet Bitmap an Drucker - Simplified"""
        return True  # Placeholder
    
    def create_text_image_with_offsets(self, text, font_size):
        """Erstellt Text-Bild mit Offsets - Simplified"""
        return None  # Placeholder
    
    def _execute_calibration_job(self, data):
        """Führt Kalibrierungs-Job aus - Simplified"""
        return True  # Placeholder

# Alias für Kompatibilität mit bestehenden Modulen
RobustPhomemoM110 = EnhancedPhomemoM110
