#!/usr/bin/env python3
"""
Erweiteter Phomemo M110 Printer Controller
Mit Bildvorschau, X-Offset und konfigurierbaren Einstellungen
Plus QR-Code und Barcode-Unterstützung
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
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

# Optional numpy import für erweiterte Bildverarbeitung
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    print("WARNING: Numpy not available, advanced dithering features disabled")

# Konfiguration importieren
from config import *

# Code Generator import mit Fallback
try:
    from code_generator import CodeGenerator
    HAS_CODE_GENERATOR = True
except ImportError as e:
    HAS_CODE_GENERATOR = False
    print(f"WARNING: Code generator not available: {e}")
    print("QR/Barcode features will be disabled. Install with: pip3 install qrcode pillow")

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
        
        # Label-Spezifikationen - Standard aus Config
        self.current_label_size = DEFAULT_LABEL_SIZE
        self.label_width_px = LABEL_WIDTH_PX
        self.label_height_px = LABEL_HEIGHT_PX
        self.label_width_mm = LABEL_WIDTH_MM
        self.label_height_mm = LABEL_HEIGHT_MM
        
        # Konfigurierbare Einstellungen
        self.settings = DEFAULT_SETTINGS.copy()
        self.load_settings()
        
        # Label-Größe aus Settings laden
        self.update_label_size(self.settings.get('label_size', DEFAULT_LABEL_SIZE))
        
        # Connection Management
        self.connection_status = ConnectionStatus.DISCONNECTED
        self.last_successful_connection = None
        self.connection_attempts = 0
        self.max_connection_attempts = MAX_CONNECTION_ATTEMPTS
        self.base_retry_delay = BASE_RETRY_DELAY
        self.max_retry_delay = MAX_RETRY_DELAY
        self.rfcomm_process = None  # Process für rfcomm connect
        
        # Print Queue
        self.print_queue = queue.Queue()
        self.queue_processor_running = False
        self.queue_thread = None
        
        # Code Generator für QR/Barcodes (falls verfügbar)
        if HAS_CODE_GENERATOR:
            self.code_generator = CodeGenerator(self.label_width_px, self.label_height_px)
        else:
            self.code_generator = None
        
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
            if 'dither_strength' in new_settings:
                new_settings['dither_strength'] = max(0.1, min(2.0, float(new_settings['dither_strength'])))
            if 'contrast_boost' in new_settings:
                new_settings['contrast_boost'] = max(0.5, min(2.0, float(new_settings['contrast_boost'])))
            
            self.settings.update(new_settings)
            return self.save_settings()
        except Exception as e:
            logger.error(f"Error updating settings: {e}")
            return False
    
    def get_settings(self) -> Dict[str, Any]:
        """Gibt aktuelle Einstellungen zurück"""
        return self.settings.copy()
    
    def get_available_label_sizes(self) -> Dict[str, Any]:
        """Gibt verfügbare Label-Größen zurück"""
        return LABEL_SIZES.copy()
    
    def get_current_label_size(self) -> Dict[str, Any]:
        """Gibt aktuelle Label-Größe zurück"""
        return {
            'current': self.current_label_size,
            'width_px': self.label_width_px,
            'height_px': self.label_height_px,
            'width_mm': self.label_width_mm,
            'height_mm': self.label_height_mm,
            **LABEL_SIZES[self.current_label_size]
        }
    
    def update_label_size(self, label_size_key: str) -> bool:
        """Aktualisiert die Label-Größe"""
        try:
            if label_size_key not in LABEL_SIZES:
                logger.error(f"Unknown label size: {label_size_key}")
                return False
            
            label_config = LABEL_SIZES[label_size_key]
            
            # Label-Dimensionen aktualisieren
            self.current_label_size = label_size_key
            self.label_width_mm = label_config['width_mm']
            self.label_height_mm = label_config['height_mm']
            
            # Pixel-Dimensionen - begrenzt auf Drucker-Breite
            self.label_width_px = min(label_config['width_px'], PRINTER_WIDTH_PIXELS)
            self.label_height_px = label_config['height_px']
            
            # Code Generator aktualisieren falls vorhanden
            if hasattr(self, 'code_generator') and self.code_generator:
                self.code_generator.label_width_px = self.label_width_px
                self.code_generator.label_height_px = self.label_height_px
            
            # Settings speichern
            self.settings['label_size'] = label_size_key
            self.save_settings()
            
            logger.info(f"📏 Label size updated to {label_config['name']}: {self.label_width_px}x{self.label_height_px}px")
            return True
            
        except Exception as e:
            logger.error(f"Error updating label size: {e}")
            return False
    
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
        
        # rfcomm-Prozess beenden
        self._cleanup_rfcomm_process()
    
    def is_connected(self):
        """Prüft ob Drucker verbunden ist"""
        return os.path.exists(self.rfcomm_device)
    
    def connect_bluetooth(self, force_reconnect=False):
        """Stellt Bluetooth-Verbindung her mit der stabilen Manual Connect Methode"""
        return self.manual_connect_bluetooth()
    
    def manual_connect_bluetooth(self):
        """Manuelle Bluetooth-Verbindung mit der bewährten rfcomm connect Methode"""
        try:
            with self._lock:
                logger.info("Starting manual Bluetooth connection sequence...")
                
                # 1. Alte rfcomm-Verbindung beenden
                logger.info("Step 1: Releasing old rfcomm connection...")
                subprocess.run(['sudo', 'rfcomm', 'release', '0'], capture_output=True, timeout=10)
                time.sleep(1)
                
                # 2. Trust setzen
                logger.info("Step 2: Ensuring pairing and trust...")
                trust_result = subprocess.run(
                    ['bluetoothctl', 'trust', self.mac_address],
                    capture_output=True, text=True, timeout=15
                )
                logger.info(f"Trust result: {trust_result.returncode}")
                
                # 3. rfcomm connect im Hintergrund starten
                logger.info("Step 3: Starting rfcomm connect...")
                cmd = ['sudo', 'rfcomm', 'connect', '0', self.mac_address, '1']
                
                # Cleanup old process
                self._cleanup_rfcomm_process()
                
                # Start new process
                self.rfcomm_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Wait and check
                time.sleep(4)
                
                if self.is_connected():
                    self.connection_status = ConnectionStatus.CONNECTED
                    self.last_successful_connection = time.time()
                    self.connection_attempts = 0
                    self.stats['reconnections'] += 1
                    
                    # Test with heartbeat
                    heartbeat_success = self._send_heartbeat()
                    logger.info(f"Manual connection successful, heartbeat: {heartbeat_success}")
                    return True
                else:
                    # Get error from process
                    error_msg = "Device not accessible"
                    if self.rfcomm_process and self.rfcomm_process.poll() is not None:
                        _, stderr = self.rfcomm_process.communicate()
                        error_msg = f"rfcomm failed: {stderr}"
                    
                    logger.error(f"Manual connect failed: {error_msg}")
                    self.connection_status = ConnectionStatus.FAILED
                    return False
                    
        except Exception as e:
            logger.error(f"Manual connect error: {e}")
            self.connection_status = ConnectionStatus.FAILED
            return False
    
    def _cleanup_rfcomm_process(self):
        """Bereinigt alte rfcomm-Prozesse"""
        try:
            if hasattr(self, 'rfcomm_process') and self.rfcomm_process:
                if self.rfcomm_process.poll() is None:  # Still running
                    self.rfcomm_process.terminate()
                    time.sleep(1)
                    if self.rfcomm_process.poll() is None:
                        self.rfcomm_process.kill()
        except Exception as e:
            logger.warning(f"Error cleaning up rfcomm process: {e}")
    
    def _send_heartbeat(self):
        """Sendet einen Heartbeat-Test an den Drucker"""
        try:
            return self.send_command(b'\x1b\x40')  # ESC @ Reset command
        except Exception:
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
    
    def process_image_for_preview(self, image_data, fit_to_label=None, maintain_aspect=None, enable_dither=None, dither_threshold=None, dither_strength=None, scaling_mode='fit_aspect') -> Optional[ImageProcessingResult]:
        """Verarbeitet ein Bild für die Schwarz-Weiß-Vorschau"""
        try:
            # Parameter aus Einstellungen falls nicht übergeben
            if fit_to_label is None:
                fit_to_label = self.settings.get('fit_to_label_default', True)
            if maintain_aspect is None:
                maintain_aspect = self.settings.get('maintain_aspect_default', True)
            if enable_dither is None:
                enable_dither = self.settings.get('dither_enabled', True)
            if dither_threshold is None:
                dither_threshold = self.settings.get('dither_threshold', DEFAULT_DITHER_THRESHOLD)
            if dither_strength is None:
                dither_strength = self.settings.get('dither_strength', DEFAULT_DITHER_STRENGTH)
            
            # Bild öffnen
            if isinstance(image_data, bytes):
                img = Image.open(io.BytesIO(image_data))
            else:
                img = image_data
            
            # In RGB konvertieren falls notwendig
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            original_size = img.size
            
            # Größe anpassen basierend auf Skalierungsmodus
            if fit_to_label:
                target_width = self.label_width_px
                target_height = self.label_height_px
                
                if scaling_mode == 'fit_aspect':
                    # Original-Verhalten: Seitenverhältnis beibehalten
                    if maintain_aspect:
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
                
                elif scaling_mode == 'stretch_full':
                    # Volle Label-Größe (stretchen/verzerren falls nötig)
                    img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                
                elif scaling_mode == 'crop_center':
                    # Zentriert zuschneiden für volle Label-Größe
                    # Berechne Skalierung um kleinste Dimension zu füllen
                    scale_w = target_width / img.width
                    scale_h = target_height / img.height
                    scale = max(scale_w, scale_h)  # Größere Skalierung für vollständige Abdeckung
                    
                    # Skalieren
                    new_width = int(img.width * scale)
                    new_height = int(img.height * scale)
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # Zentriert zuschneiden
                    left = (new_width - target_width) // 2
                    top = (new_height - target_height) // 2
                    img = img.crop((left, top, left + target_width, top + target_height))
                
                elif scaling_mode == 'pad_center':
                    # Zentriert mit Rand für volle Label-Größe
                    # Berechne Skalierung um größte Dimension zu füllen
                    scale_w = target_width / img.width
                    scale_h = target_height / img.height
                    scale = min(scale_w, scale_h)  # Kleinere Skalierung um vollständig sichtbar zu bleiben
                    
                    # Skalieren
                    new_width = int(img.width * scale)
                    new_height = int(img.height * scale)
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # Auf Label-Größe mit Rand zentrieren
                    new_img = Image.new('RGB', (target_width, target_height), 'white')
                    paste_x = (target_width - new_width) // 2
                    paste_y = (target_height - new_height) // 2
                    new_img.paste(img, (paste_x, paste_y))
                    img = new_img
            
            # Schwarz-Weiß konvertieren mit erweiterten Dithering-Optionen
            if enable_dither:
                # Kontrast-Verstärkung anwenden falls konfiguriert
                contrast_boost = self.settings.get('contrast_boost', DEFAULT_CONTRAST_BOOST)
                if contrast_boost != 1.0:
                    try:
                        enhancer = ImageEnhance.Contrast(img)
                        img = enhancer.enhance(contrast_boost)
                    except Exception:
                        logger.warning("Contrast enhancement failed, using original image")
                
                # Floyd-Steinberg Dithering mit angepasster Stärke
                if dither_strength != 1.0 and HAS_NUMPY:
                    try:
                        # Dithering-Stärke durch Gamma-Korrektur simulieren
                        gamma = 1.0 / dither_strength
                        img_array = np.array(img)
                        img_array = np.power(img_array / 255.0, gamma) * 255.0
                        img = Image.fromarray(np.uint8(img_array))
                    except Exception:
                        logger.warning("Advanced dithering failed, using standard dithering")
                
                bw_img = img.convert('1', dither=Image.Dither.FLOYDSTEINBERG)
            else:
                # Einfacher Threshold
                gray_img = img.convert('L')
                bw_img = gray_img.point(lambda x: 0 if x < dither_threshold else 255, '1')
            
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
                    'scaling_mode': scaling_mode,
                    'dither_enabled': enable_dither,
                    'dither_threshold': dither_threshold,
                    'dither_strength': dither_strength,
                    'contrast_boost': self.settings.get('contrast_boost', DEFAULT_CONTRAST_BOOST),
                    'x_offset': self.settings.get('x_offset', DEFAULT_X_OFFSET),
                    'y_offset': self.settings.get('y_offset', DEFAULT_Y_OFFSET)
                }
            )
            
        except Exception as e:
            logger.error(f"Image processing error: {e}")
            return None
    
    def apply_offsets_to_image(self, img: Image.Image) -> Image.Image:
        """
        Wendet X- und Y-Offsets auf ein Bild an - KORRIGIERT gegen Wrap-Around
        WICHTIG: Verhindert, dass Bilder über den Druckerrand hinaus geschoben werden
        """
        try:
            x_offset = self.settings.get('x_offset', DEFAULT_X_OFFSET)
            y_offset = self.settings.get('y_offset', DEFAULT_Y_OFFSET)
            
            logger.info(f"📐 Original image size: {img.width}x{img.height}")
            logger.info(f"⚙️ Current offset settings: X={x_offset}, Y={y_offset}")
            logger.info(f"📏 Printer width: {self.width_pixels}px")
            
            # KRITISCHE KORREKTUR: Bild darf NIEMALS über Druckerbreite hinaus
            max_allowed_width = min(img.width, self.width_pixels)
            
            # Falls Bild breiter als Drucker ist: beschneiden!
            if img.width > self.width_pixels:
                logger.warning(f"⚠️ Image too wide ({img.width}px), cropping to {self.width_pixels}px")
                img = img.crop((0, 0, self.width_pixels, img.height))
            
            # Drucker-Bild erstellen (volle Breite)
            printer_height = max(img.height + abs(y_offset), img.height)
            printer_img = Image.new('1', (self.width_pixels, printer_height), 1)  # Weiß
            
            # X-Position berechnen - KEIN WRAP-AROUND!
            # Max X-Position so berechnen, dass Bild komplett in Druckerbreite passt
            max_x_position = self.width_pixels - img.width
            
            if x_offset > max_x_position:
                logger.warning(f"⚠️ X-Offset too large ({x_offset}), limiting to {max_x_position}")
                paste_x = max_x_position
            else:
                paste_x = max(0, x_offset)
            
            # Y-Position berechnen  
            paste_y = max(0, y_offset) if y_offset >= 0 else 0
            
            # SICHERHEITSPRÜFUNG vor dem Einfügen
            if paste_x + img.width > self.width_pixels:
                logger.error(f"❌ WRAP-AROUND DETECTED! paste_x={paste_x}, img_width={img.width}, total={paste_x + img.width}")
                logger.error(f"❌ This would exceed printer width of {self.width_pixels}px")
                # Erzwinge sichere Position
                paste_x = max(0, self.width_pixels - img.width)
                logger.info(f"🔧 CORRECTED to safe position: X={paste_x}")
            
            logger.info(f"📍 Final paste position: X={paste_x}, Y={paste_y}")
            logger.info(f"📊 Image will occupy: X={paste_x} to {paste_x + img.width} (max: {self.width_pixels})")
            
            # Bild einfügen
            printer_img.paste(img, (paste_x, paste_y))
            
            logger.info(f"✅ Applied offsets safely: X={paste_x}, Y={paste_y}, Size={printer_img.size}")
            return printer_img
            
        except Exception as e:
            logger.error(f"❌ Error applying offsets: {e}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            return img
    
    def print_image_with_preview(self, image_data, fit_to_label=True, maintain_aspect=True, enable_dither=None, dither_threshold=None, dither_strength=None, scaling_mode='fit_aspect'):
        """Druckt ein Bild mit den aktuellen Offset-Einstellungen"""
        try:
            logger.info("Processing image for print with offsets...")
            
            # Bild verarbeiten
            result = self.process_image_for_preview(image_data, fit_to_label, maintain_aspect, enable_dither, dither_threshold, dither_strength, scaling_mode)
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
    
    def print_text_immediate(self, text: str, font_size: int = 24, alignment: str = 'center') -> dict:
        """Druckt Text sofort (bypass Queue)"""
        try:
            logger.info(f"🖨️ Starting immediate text print: '{text[:50]}...'")
            
            img = self.create_text_image_with_offsets(text, font_size, alignment)
            if img:
                logger.info(f"✅ Text image created, size: {img.width}x{img.height}")
                
                logger.info("🔄 Converting image to printer format...")
                image_data = self.image_to_printer_format(img)
                if image_data:
                    logger.info(f"✅ Image converted to printer format ({len(image_data)} bytes)")
                    
                    logger.info("📤 Sending bitmap to printer...")
                    success = self.send_bitmap(image_data, img.height)
                    if success:
                        logger.info("✅ Text printed successfully!")
                        self.stats['successful_jobs'] += 1
                        self.stats['text_jobs'] += 1
                        return {'success': True}
                    else:
                        logger.error("❌ Failed to send bitmap to printer")
                        return {'success': False, 'error': 'Bitmap senden fehlgeschlagen'}
                else:
                    logger.error("❌ Failed to convert image to printer format")
                    return {'success': False, 'error': 'Bildkonvertierung fehlgeschlagen'}
            else:
                logger.error("❌ Failed to create text image")
                return {'success': False, 'error': 'Bild konnte nicht erstellt werden'}
        except Exception as e:
            logger.error(f"❌ Immediate text print error: {e}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            return {'success': False, 'error': str(e)}
            return {'success': False, 'error': str(e)}
    
    def print_image_immediate(self, image_data, fit_to_label=True, maintain_aspect=True, enable_dither=True, dither_threshold=None, dither_strength=None, scaling_mode='fit_aspect') -> bool:
        """Druckt Bild sofort mit FUNKTIONIERENDER TEXT-STRUKTUR"""
        try:
            logger.info("🖨️ Starting immediate image print with PROVEN TEXT STRUCTURE")
            
            logger.info("📷 Processing image data with all parameters...")
            # GENAU WIE BEI TEXT: Erst verarbeiten, dann direkt drucken
            result = self.process_image_for_preview(
                image_data, 
                fit_to_label, 
                maintain_aspect, 
                enable_dither, 
                dither_threshold=dither_threshold, 
                dither_strength=dither_strength, 
                scaling_mode=scaling_mode
            )
            
            if result:
                logger.info(f"✅ Image processed, size: {result.processed_image.size}")
                
                # GENAU WIE BEI TEXT: Offsets anwenden
                printer_img = self.apply_offsets_to_image(result.processed_image)
                logger.info(f"✅ Offsets applied, final size: {printer_img.width}x{printer_img.height}")
                
                # GENAU WIE BEI TEXT: Zu Drucker-Format konvertieren
                logger.info("🔄 Converting image to printer format...")
                final_image_data = self.image_to_printer_format(printer_img)
                
                if final_image_data:
                    logger.info(f"✅ Image converted to printer format ({len(final_image_data)} bytes)")
                    
                    # GENAU WIE BEI TEXT: Bitmap senden
                    logger.info("📤 Sending bitmap to printer...")
                    success = self.send_bitmap(final_image_data, printer_img.height)
                    
                    if success:
                        logger.info("✅ Image printed successfully with TEXT STRUCTURE!")
                        self.stats['successful_jobs'] += 1
                        return True
                    else:
                        logger.error("❌ Failed to send bitmap to printer")
                        return False
                else:
                    logger.error("❌ Failed to convert image to printer format")
                    return False
            else:
                logger.error("❌ Failed to process image")
                return False
            
        except Exception as e:
            logger.error(f"❌ Immediate image print error: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
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
            'rfcomm_process_running': self.rfcomm_process.poll() is None if self.rfcomm_process else False,
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
        """Background Thread für Connection Monitoring mit stabiler Verbindungsmethode"""
        while self.monitor_running:
            try:
                if self.connection_status == ConnectionStatus.CONNECTED:
                    if not self.is_connected():
                        logger.warning("Connection lost, attempting reconnect with manual method...")
                        self.connection_status = ConnectionStatus.RECONNECTING
                        self.stats['reconnections'] += 1
                        
                        if self.manual_connect_bluetooth():
                            logger.info("Automatic reconnection successful")
                        else:
                            logger.error("Automatic reconnection failed")
                
                # Heartbeat senden wenn verbunden
                if self.connection_status == ConnectionStatus.CONNECTED:
                    self.last_heartbeat = time.time()
                
                time.sleep(self.heartbeat_interval)
                
            except Exception as e:
                logger.error(f"Connection monitor error: {e}")
                time.sleep(10)
    
    def image_to_printer_format(self, img):
        """
        Konvertiert PIL Image zu Drucker-Format mit garantiertem 48-Byte-Alignment
        NEUE VERSION: Eliminiert Segmentierung und stellt sicher, dass jede Zeile exakt 48 Bytes hat
        """
        try:
            # Bild zu Schwarz-Weiß konvertieren
            if img.mode != '1':
                img = img.convert('1')
            
            width, height = img.size
            pixels = list(img.getdata())
            
            logger.info(f"🔧 Converting image: {width}x{height} -> {self.width_pixels}x{height} (48 bytes per line)")
            
            # GARANTIERT 48 BYTES PRO ZEILE - KEINE SEGMENTIERUNG
            image_bytes = []
            
            for y in range(height):
                # Exakt 48 Bytes für diese Zeile erstellen
                line_bytes = [0] * self.bytes_per_line  # Immer exakt 48 Bytes
                
                # Pixel in Bytes konvertieren (8 Pixel pro Byte)
                for byte_index in range(self.bytes_per_line):  # 0 bis 47
                    byte_value = 0
                    
                    for bit_index in range(8):  # 8 Bits pro Byte
                        pixel_x = byte_index * 8 + bit_index
                        
                        # Nur wenn Pixel innerhalb der Bildbreite liegt
                        if pixel_x < width:
                            pixel_idx = y * width + pixel_x
                            if pixel_idx < len(pixels):
                                # Schwarz = 1 Bit setzen, Weiß = 0 Bit lassen
                                if pixels[pixel_idx] == 0:  # PIL: 0 = schwarz
                                    byte_value |= (1 << (7 - bit_index))
                    
                    line_bytes[byte_index] = byte_value
                
                # Zeile zu Gesamtbild hinzufügen
                image_bytes.extend(line_bytes)
            
            final_bytes = bytes(image_bytes)
            expected_size = height * self.bytes_per_line
            
            logger.info(f"✅ Image converted: {len(final_bytes)} bytes (expected: {expected_size})")
            
            # Größen-Validierung
            if len(final_bytes) != expected_size:
                logger.error(f"❌ BYTE ALIGNMENT ERROR: Got {len(final_bytes)}, expected {expected_size}")
                return None
            
            return final_bytes
            
        except Exception as e:
            logger.error(f"❌ Image conversion error: {e}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            return None
    
    def send_bitmap(self, image_data: bytes, height: int) -> bool:
        """
        Optimierte Bitmap-Übertragung ohne Segmentierung
        NEUE VERSION: Sendet das gesamte Bild als zusammenhängenden Block
        """
        try:
            width_bytes = self.bytes_per_line  # Immer 48 Bytes
            
            logger.info(f"📤 SENDING BITMAP: {len(image_data)} bytes, {height} lines (48 bytes/line)")
            
            # Validierung: Daten müssen exakt height * 48 Bytes sein
            expected_size = height * width_bytes
            if len(image_data) != expected_size:
                logger.error(f"❌ DATA SIZE ERROR: Got {len(image_data)}, expected {expected_size}")
                return False
            
            # Anti-Drift: Mindestabstand zwischen Druckvorgängen
            if hasattr(self, 'last_print_time'):
                time_since_last = time.time() - self.last_print_time
                if time_since_last < 0.15:  # 150ms Mindestabstand
                    time.sleep(0.15 - time_since_last)
            
            # 1. Drucker initialisieren
            logger.info("🔄 Step 1: Initialize printer")
            if not self.send_command(b'\x1b\x40'):  # ESC @ - Reset
                logger.error("❌ Failed to initialize printer")
                return False
            time.sleep(0.02)  # 20ms für Initialisierung
            
            # 2. Raster-Bitmap-Header senden
            logger.info("🔄 Step 2: Send bitmap header")
            m = 0  # Normal mode
            header = bytes([
                0x1D, 0x76, 0x30, m,                    # GS v 0 - Print raster bitmap
                width_bytes & 0xFF, (width_bytes >> 8) & 0xFF,  # Width in bytes (48)
                height & 0xFF, (height >> 8) & 0xFF             # Height in lines
            ])
            
            if not self.send_command(header):
                logger.error("❌ Failed to send bitmap header")
                return False
            time.sleep(0.01)  # 10ms für Header-Verarbeitung
            
            # 3. VOLLSTÄNDIGE BILDÜBERTRAGUNG OHNE SEGMENTIERUNG
            logger.info("🔄 Step 3: Send complete image data (NO SEGMENTATION)")
            
            # Für kleine Bilder: Direkt senden
            if len(image_data) <= 2048:  # <= 2KB
                logger.info("📦 DIRECT TRANSFER: Sending complete image at once")
                success = self.send_command(image_data)
                if not success:
                    logger.error("❌ Direct transfer failed")
                    return False
            else:
                # Für größere Bilder: Größere zusammenhängende Blöcke
                logger.info("📦 BLOCK TRANSFER: Using larger consistent blocks")
                BLOCK_SIZE = 1536  # 1.5KB Blöcke (48 bytes * 32 lines)
                
                # Stelle sicher, dass Blockgröße ein Vielfaches von 48 ist
                lines_per_block = BLOCK_SIZE // width_bytes
                actual_block_size = lines_per_block * width_bytes
                
                success = True
                for i in range(0, len(image_data), actual_block_size):
                    block = image_data[i:i + actual_block_size]
                    
                    logger.debug(f"📦 Sending block {i//actual_block_size + 1}: {len(block)} bytes")
                    
                    if not self.send_command(block):
                        logger.warning(f"⚠️ Block {i//actual_block_size + 1} failed, retrying...")
                        time.sleep(0.02)  # 20ms Retry-Pause
                        if not self.send_command(block):
                            logger.error(f"❌ Block {i//actual_block_size + 1} failed after retry")
                            success = False
                            break
                    
                    # Kurze Pause zwischen Blöcken für Stabilität
                    time.sleep(0.01)  # 10ms zwischen Blöcken
            
            # 4. Abschluss
            time.sleep(0.02)  # 20ms Post-Processing
            self.last_print_time = time.time()
            
            if success:
                logger.info("✅ BITMAP SENT SUCCESSFULLY - NO SEGMENTATION")
            else:
                logger.error("❌ BITMAP TRANSMISSION FAILED")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Bitmap transmission error: {e}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            return False
    
    def create_text_image_with_offsets(self, text, font_size, alignment='center'):
        """Erstellt Text-Bild mit Offsets und Ausrichtung - MIT MARKDOWN SUPPORT"""
        try:
            # Erst das Markdown-formatierte Bild ohne Offsets erstellen
            markdown_img = self.create_text_image_preview(text, font_size, alignment)
            
            if markdown_img is None:
                logger.error("❌ Failed to create markdown image")
                return None
            
            # Dann Offsets anwenden
            x_offset = self.settings.get('x_offset', 0)
            y_offset = self.settings.get('y_offset', 0)
            
            if x_offset != 0 or y_offset != 0:
                logger.info(f"📐 Applying offsets to markdown text: X={x_offset}, Y={y_offset}")
                final_img = self.apply_offsets_to_image(markdown_img)
                logger.info(f"📐 Final markdown text image size: {final_img.width}x{final_img.height}")
                return final_img
            else:
                logger.info(f"📐 No offsets applied to markdown text, image size: {markdown_img.width}x{markdown_img.height}")
                return markdown_img
                
        except Exception as e:
            logger.error(f"❌ Markdown text image creation error: {e}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            return None
    
    def parse_markdown_text(self, text, base_font_size):
        try:
            import os
            from PIL import Image, ImageDraw, ImageFont
            
            logger.info(f"📝 Creating text image with font size {font_size}, alignment: {alignment}")
            
            # Font laden mit besserer Fehlerbehandlung
            font = None
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf", 
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/System/Library/Fonts/Arial.ttf",  # macOS
                "C:/Windows/Fonts/arial.ttf"  # Windows
            ]
            
            for font_path in font_paths:
                try:
                    if os.path.exists(font_path):
                        font = ImageFont.truetype(font_path, font_size)
                        logger.info(f"✅ Font loaded: {font_path}")
                        break
                except Exception as e:
                    logger.debug(f"Font {font_path} failed: {e}")
                    continue
            
            if font is None:
                logger.warning("⚠️ Using default font - no TrueType font found")
                font = ImageFont.load_default()
            
            # Text-Verarbeitung - verbesserte Zeilumbruch-Behandlung
            processed_text = text.replace('\\r\\n', '\n')  # Windows CRLF literal
            processed_text = processed_text.replace('\\n', '\n')  # Escaped newlines
            processed_text = processed_text.replace('\r\n', '\n')  # Windows CRLF
            processed_text = processed_text.replace('\r', '\n')   # Mac CR
            
            # Zusätzliche Bereinigung für bessere Font-Kompatibilität
            processed_text = processed_text.replace('\x00', '')  # Null-Bytes entfernen
            processed_text = processed_text.replace('\t', '    ')  # Tabs zu Spaces
            
            lines = processed_text.split('\n')
            # Leere Zeilen am Ende entfernen
            while lines and not lines[-1].strip():
                lines.pop()
            
            # Leere Zeilen in der Mitte beibehalten, aber als Leerstring
            for i, line in enumerate(lines):
                if not line.strip():
                    lines[i] = ''  # Explizit leer setzen
            
            logger.info(f"📄 Processing {len(lines)} lines: {[line[:20] + '...' if len(line) > 20 else line for line in lines[:3]]}")
            
            # Bildgröße berechnen
            temp_img = Image.new('RGB', (1, 1), 'white')
            temp_draw = ImageDraw.Draw(temp_img)
            
            line_heights = []
            max_width = 0
            
            for line in lines:
                try:
                    bbox = temp_draw.textbbox((0, 0), line, font=font)
                    line_width = bbox[2] - bbox[0]
                    line_height = bbox[3] - bbox[1]
                    max_width = max(max_width, line_width)
                    line_heights.append(max(line_height, 20))  # Mindesthöhe
                except Exception as e:
                    logger.warning(f"⚠️ Problem with line '{line}': {e}")
                    line_heights.append(20)
                    max_width = max(max_width, 100)
            
            # Bild erstellen
            total_height = sum(line_heights) + (len(lines) - 1) * 5 + 40
            total_height = max(total_height, 50)  # Mindesthöhe
            
            logger.info(f"📐 Base image size: {self.label_width_px}x{total_height}")
            img = Image.new('RGB', (self.label_width_px, total_height), 'white')
            draw = ImageDraw.Draw(img)
            
            # Text zeichnen mit Ausrichtung
            y_pos = 20
            for i, line in enumerate(lines):
                if line.strip():
                    try:
                        bbox = draw.textbbox((0, 0), line, font=font)
                        line_width = bbox[2] - bbox[0]
                        
                        # X-Position basierend auf Ausrichtung berechnen
                        if alignment == 'left':
                            x_pos = 10  # 10px Rand links
                        elif alignment == 'right':
                            x_pos = max(10, self.label_width_px - line_width - 10)  # 10px Rand rechts
                        else:  # center (default)
                            x_pos = max(10, (self.label_width_px - line_width) // 2)
                        
                        draw.text((x_pos, y_pos), line, fill='black', font=font)
                        logger.debug(f"✏️ Drew line {i+1} ({alignment}): '{line}' at ({x_pos}, {y_pos})")
                    except Exception as e:
                        logger.warning(f"⚠️ Could not draw line '{line}': {e}")
                
                y_pos += line_heights[i] + 5
            
            # Bild zu S/W konvertieren
            bw_img = img.convert('1')
            
            # Offsets anwenden
            x_offset = self.settings.get('x_offset', 0)
            y_offset = self.settings.get('y_offset', 0)
            
            if x_offset != 0 or y_offset != 0:
                logger.info(f"📐 Applying offsets: X={x_offset}, Y={y_offset}")
                final_img = self.apply_offsets_to_image(bw_img)
                logger.info(f"📐 Final image size: {final_img.width}x{final_img.height}")
                return final_img
            else:
                logger.info(f"📐 No offsets applied, image size: {bw_img.width}x{bw_img.height}")
                return bw_img
                
        except Exception as e:
            logger.error(f"❌ Text image creation error: {e}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            return None
    
    def parse_markdown_text(self, text, base_font_size):
        """
        Parst Markdown-Text und gibt eine Liste von formatierten Text-Segmenten zurück
        
        Unterstützte Markdown-Syntax:
        - **fett** oder __fett__
        - # Überschrift (große Schrift)
        - ## Unterüberschrift (mittlere Schrift)
        
        Returns: List of tuples (text, font_size, bold)
        """
        import re
        
        # SCHRITT 1: Komplette Text-Bereinigung VOR dem Parsen
        # Windows CRLF und andere Zeilenende-Formate normalisieren
        clean_text = text.replace('\r\n', '\n')  # Windows CRLF
        clean_text = clean_text.replace('\r', '\n')   # Mac CR
        clean_text = clean_text.replace('\\n', '\n')  # Escaped newlines
        clean_text = clean_text.replace('\\r\\n', '\n')  # Windows CRLF literal
        
        # Problematische Zeichen entfernen
        clean_text = clean_text.replace('\x00', '')  # Null-Bytes entfernen
        clean_text = clean_text.replace('\t', '    ')  # Tabs zu 4 Spaces
        
        # Alle anderen Steuerzeichen entfernen (außer \n und Space)
        clean_text = ''.join(char for char in clean_text if ord(char) >= 32 or char in ['\n', ' '])
        
        lines = clean_text.split('\n')
        parsed_lines = []
        
        for line in lines:
            line_segments = []
            
            # Überschriften prüfen (müssen am Zeilenanfang stehen)
            if line.strip().startswith('# '):
                # H1 - Große Überschrift
                clean_text = line.strip()[2:].strip()
                line_segments.append((clean_text, base_font_size + 8, True))
            elif line.strip().startswith('## '):
                # H2 - Mittlere Überschrift  
                clean_text = line.strip()[3:].strip()
                line_segments.append((clean_text, base_font_size + 4, True))
            else:
                # Normale Zeile - inline Formatierung parsen
                segments = self._parse_inline_markdown(line, base_font_size)
                line_segments.extend(segments)
            
            parsed_lines.append(line_segments)
        
        return parsed_lines
    
    def _parse_inline_markdown(self, text, base_font_size):
        """Parst inline Markdown-Formatierung in einem Text - NUR FETT"""
        import re
        
        # Text ist bereits in parse_markdown_text bereinigt worden
        segments = []
        current_pos = 0
        
        # Regex-Patterns für Markdown - NUR FETT, KEIN KURSIV
        patterns = [
            (r'\*\*(.*?)\*\*', True),    # **fett**
            (r'__(.*?)__', True),        # __fett__
        ]
        
        # Alle Matches finden und sortieren
        all_matches = []
        for pattern, is_bold in patterns:
            for match in re.finditer(pattern, text):
                # Prüfen ob es sich überschneidet mit bereits gefundenen Matches
                overlaps = False
                for existing_start, existing_end, _, _ in all_matches:
                    if (match.start() < existing_end and match.end() > existing_start):
                        overlaps = True
                        break
                
                if not overlaps:
                    all_matches.append((match.start(), match.end(), match.group(1), is_bold))
        
        # Nach Position sortieren
        all_matches.sort(key=lambda x: x[0])
        
        # Text in Segmente aufteilen
        for match_start, match_end, match_text, is_bold in all_matches:
            # Text vor dem Match hinzufügen
            if current_pos < match_start:
                plain_text = text[current_pos:match_start]
                if plain_text:
                    segments.append((plain_text, base_font_size, False))
            
            # Formatierten Text hinzufügen
            segments.append((match_text, base_font_size, is_bold))
            current_pos = match_end
        
        # Restlichen Text hinzufügen
        if current_pos < len(text):
            remaining_text = text[current_pos:]
            if remaining_text:
                segments.append((remaining_text, base_font_size, False))
        
        # Wenn keine Formatierung gefunden wurde, ganzen Text als plain zurückgeben
        if not segments:
            segments.append((text, base_font_size, False))
        
        return segments
    
    def create_text_image_preview(self, text, font_size, alignment='center'):
        """Erstellt Text-Bild für Vorschau OHNE Offsets - mit Markdown-Support"""
        try:
            import os
            from PIL import Image, ImageDraw, ImageFont
            
            logger.info(f"📝 Creating MARKDOWN text preview with font size {font_size}, alignment: {alignment}")
            
            # Markdown-Text parsen
            parsed_lines = self.parse_markdown_text(text, font_size)
            
            # Font-Cache für verschiedene Größen und Stile
            font_cache = {}
            
            def get_font(size, bold=False):
                key = (size, bold)
                if key not in font_cache:
                    # Basis-Font laden (fett wenn nötig)
                    font_paths = [
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/TTF/DejaVuSans.ttf",
                        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                        "/System/Library/Fonts/Arial.ttf",  # macOS
                        "C:/Windows/Fonts/arial.ttf"  # Windows
                    ]
                    
                    font_obj = None
                    for font_path in font_paths:
                        try:
                            if os.path.exists(font_path):
                                font_obj = ImageFont.truetype(font_path, size)
                                break
                        except Exception:
                            continue
                    
                    if font_obj is None:
                        font_obj = ImageFont.load_default()
                    
                    font_cache[key] = font_obj
                
                return font_cache[key]
            
            # Bildgröße berechnen
            temp_img = Image.new('RGB', (1, 1), 'white')
            temp_draw = ImageDraw.Draw(temp_img)
            
            line_heights = []
            max_width = 0
            
            for line_segments in parsed_lines:
                line_width = 0
                line_height = 0
                
                for segment_text, seg_font_size, is_bold in line_segments:
                    if segment_text.strip():
                        seg_font = get_font(seg_font_size, is_bold)
                        try:
                            bbox = temp_draw.textbbox((0, 0), segment_text, font=seg_font)
                            seg_width = bbox[2] - bbox[0]
                            seg_height = bbox[3] - bbox[1]
                            line_width += seg_width
                            line_height = max(line_height, seg_height)
                        except Exception:
                            line_width += len(segment_text) * (seg_font_size // 2)
                            line_height = max(line_height, seg_font_size)
                
                max_width = max(max_width, line_width)
                line_heights.append(max(line_height, 20))
            
            # Bild erstellen
            total_height = sum(line_heights) + (len(parsed_lines) - 1) * 5 + 40
            total_height = max(total_height, 50)
            
            logger.info(f"📐 Markdown preview image size: {self.label_width_px}x{total_height}")
            img = Image.new('RGB', (self.label_width_px, total_height), 'white')
            draw = ImageDraw.Draw(img)
            
            # Markdown-Text mit Formatierung zeichnen
            y_pos = 20
            for i, line_segments in enumerate(parsed_lines):
                line_x_positions = []
                line_width = 0
                
                # Gesamtbreite der Zeile berechnen für Ausrichtung
                for segment_text, seg_font_size, is_bold in line_segments:
                    if segment_text.strip():
                        seg_font = get_font(seg_font_size, is_bold)
                        try:
                            bbox = draw.textbbox((0, 0), segment_text, font=seg_font)
                            seg_width = bbox[2] - bbox[0]
                            line_width += seg_width
                        except Exception:
                            line_width += len(segment_text) * (seg_font_size // 2)
                
                # X-Startposition basierend auf Ausrichtung
                if alignment == 'left':
                    start_x = 10
                elif alignment == 'right':
                    start_x = max(10, self.label_width_px - line_width - 10)
                else:  # center
                    start_x = max(10, (self.label_width_px - line_width) // 2)
                
                # Segmente zeichnen
                current_x = start_x
                for segment_text, seg_font_size, is_bold in line_segments:
                    if segment_text:
                        # Spezielle Zeichen bereinigen für bessere Font-Kompatibilität
                        clean_text = segment_text.replace('\x00', '').replace('\t', '    ')
                        # Zusätzliche Unicode-Bereinigung
                        clean_text = ''.join(char for char in clean_text if ord(char) >= 32 or char in '\n\r')
                        
                        if clean_text.strip():  # Nur nicht-leere Texte zeichnen
                            seg_font = get_font(seg_font_size, is_bold)
                            try:
                                # Einfaches Zeichnen - kein Kursiv
                                draw.text((current_x, y_pos), clean_text, fill='black', font=seg_font)
                                # X-Position für nächstes Segment aktualisieren
                                bbox = draw.textbbox((0, 0), clean_text, font=seg_font)
                                current_x += bbox[2] - bbox[0]
                                
                                logger.debug(f"✏️ Drew segment '{clean_text[:20]}...' (size:{seg_font_size}, bold:{is_bold}) at ({current_x}, {y_pos})")
                            except Exception as e:
                                logger.warning(f"⚠️ Could not draw segment '{clean_text[:20]}...': {e}")
                                current_x += len(clean_text) * (seg_font_size // 2)
                
                y_pos += line_heights[i] + 5
            
            # Bild zu S/W konvertieren OHNE Offsets!
            bw_img = img.convert('1')
            
            logger.info(f"📐 Markdown preview image created (NO offsets): {bw_img.width}x{bw_img.height}")
            return bw_img
            
        except Exception as e:
            logger.error(f"❌ Markdown text preview image creation error: {e}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            return None
    
    def _execute_calibration_job(self, data):
        """Führt Kalibrierungs-Job aus"""
        try:
            pattern = data.get('pattern', 'border')
            width = data.get('width', self.label_width_px)
            height = data.get('height', self.label_height_px)
            
            logger.info(f"🧪 Executing calibration job: {pattern} ({width}x{height})")
            
            # Erstelle Testbild
            if pattern == 'full':
                # Vollständiges Rechteck mit Rahmen
                img = Image.new('1', (width, height), 1)  # Weiß
                draw = ImageDraw.Draw(img)
                
                # Äußerer Rahmen
                draw.rectangle([0, 0, width-1, height-1], outline=0, width=2)
                
                # Innere Kreuz-Linien
                draw.line([width//4, 0, width//4, height], fill=0, width=1)
                draw.line([width//2, 0, width//2, height], fill=0, width=1)
                draw.line([3*width//4, 0, 3*width//4, height], fill=0, width=1)
                
                draw.line([0, height//4, width, height//4], fill=0, width=1)
                draw.line([0, height//2, width, height//2], fill=0, width=1)
                draw.line([0, 3*height//4, width, 3*height//4], fill=0, width=1)
                
                # Offset-Marker in den Ecken
                corner_size = 10
                draw.rectangle([5, 5, 5+corner_size, 5+corner_size], fill=0)
                draw.rectangle([width-15, 5, width-5, 5+corner_size], fill=0)
                draw.rectangle([5, height-15, 5+corner_size, height-5], fill=0)
                draw.rectangle([width-15, height-15, width-5, height-5], fill=0)
                
            else:
                # Einfacher Rahmen
                img = Image.new('1', (width, height), 1)  # Weiß
                draw = ImageDraw.Draw(img)
                draw.rectangle([0, 0, width-1, height-1], outline=0, width=3)
            
            # Offsets anwenden
            final_img = self.apply_offsets_to_image(img)
            
            # Zu Drucker-Format konvertieren
            image_data = self.image_to_printer_format(final_img)
            if not image_data:
                logger.error("❌ Failed to convert calibration image")
                return False
            
            # Drucken
            success = self.send_bitmap(image_data, final_img.height)
            if success:
                logger.info("✅ Calibration pattern printed successfully!")
            else:
                logger.error("❌ Failed to print calibration pattern")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Calibration job error: {e}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            return False

    def create_text_image_with_codes(self, text: str, font_size: int = 22, alignment: str = 'center') -> Optional[Image.Image]:
        """Erstellt Text-Bild mit QR/Barcode-Unterstützung"""
        try:
            if not HAS_CODE_GENERATOR or self.code_generator is None:
                logger.warning("Code generator not available, falling back to regular text image")
                return self.create_text_image_with_offsets(text, font_size, alignment)
            
            logger.info(f"📝 Creating text image with codes: font_size={font_size}, alignment={alignment}")
            
            # Code Generator verwenden
            img = self.code_generator.create_combined_image(text, font_size, alignment)
            
            if img:
                # Offsets anwenden (falls gesetzt)
                x_offset = self.settings.get('x_offset', 0)
                y_offset = self.settings.get('y_offset', 0)
                
                if x_offset != 0 or y_offset != 0:
                    logger.info(f"🔧 Applying offsets: x={x_offset}, y={y_offset}")
                    img = self.apply_offsets_to_image(img)
                
                logger.info(f"✅ Text image with codes created: {img.width}x{img.height}")
                return img
            else:
                logger.error("❌ Failed to create image with codes")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creating text image with codes: {e}")
            return None

    def create_text_image_with_codes_preview(self, text: str, font_size: int = 22, alignment: str = 'center') -> Optional[Image.Image]:
        """Erstellt Text-Bild mit QR/Barcode-Unterstützung OHNE OFFSETS (für Vorschau)"""
        try:
            if not HAS_CODE_GENERATOR or self.code_generator is None:
                logger.warning("Code generator not available, falling back to regular text preview")
                return self.create_text_image_preview(text, font_size, alignment)
            
            logger.info(f"📝 Creating PREVIEW with codes (NO offsets): font_size={font_size}, alignment={alignment}")
            
            # Code Generator verwenden - OHNE Offsets!
            img = self.code_generator.create_combined_image(text, font_size, alignment)
            
            if img:
                logger.info(f"✅ Text PREVIEW with codes created (NO offsets): {img.width}x{img.height}")
                return img
            else:
                logger.error("❌ Failed to create text preview with codes")
                return None
                
        except Exception as e:
            logger.error(f"❌ Text preview with codes error: {e}")
            return None

    def print_text_with_codes_immediate(self, text: str, font_size: int = 22, alignment: str = 'center') -> Dict[str, Any]:
        """Druckt Text mit QR-Codes und Barcodes sofort"""
        try:
            if not HAS_CODE_GENERATOR or self.code_generator is None:
                return {'success': False, 'message': 'QR/Barcode features not available. Install with: pip3 install qrcode pillow'}
            
            logger.info(f"🖨️ Starting immediate text with codes print: '{text[:50]}...'")
            
            img = self.create_text_image_with_codes(text, font_size, alignment)
            if img:
                logger.info(f"✅ Text image with codes created, size: {img.width}x{img.height}")
                
                success = self._print_image_direct(img)
                if success:
                    logger.info("✅ Text with codes printed successfully!")
                    self.stats['successful_jobs'] += 1
                    self.stats['text_jobs'] += 1
                    return {'success': True, 'message': 'Text mit Codes gedruckt'}
                else:
                    logger.error("❌ Failed to print image with codes")
                    self.stats['failed_jobs'] += 1
                    return {'success': False, 'message': 'Druckfehler'}
            else:
                logger.error("❌ Failed to create text image with codes")
                self.stats['failed_jobs'] += 1
                return {'success': False, 'message': 'Bild-Erstellung fehlgeschlagen'}
                
        except Exception as e:
            logger.error(f"❌ Print text with codes error: {e}")
            self.stats['failed_jobs'] += 1
            return {'success': False, 'message': str(e)}

    def _print_image_direct(self, img: Image.Image) -> bool:
        """Druckt ein PIL Image direkt (ohne Queue)"""
        try:
            logger.info(f"🔄 Converting image to printer format...")
            image_data = self.image_to_printer_format(img)
            if image_data:
                logger.info(f"✅ Image converted to printer format ({len(image_data)} bytes)")
                
                logger.info("📤 Sending bitmap to printer...")
                success = self.send_bitmap(image_data, img.height)
                if success:
                    logger.info("✅ Image printed successfully!")
                    return True
                else:
                    logger.error("❌ Failed to send bitmap to printer")
                    return False
            else:
                logger.error("❌ Failed to convert image to printer format")
                return False
        except Exception as e:
            logger.error(f"❌ Direct image print error: {e}")
            return False

    def _execute_text_with_codes_job(self, data: Dict[str, Any]) -> bool:
        """Führt Text-mit-Codes-Job aus der Queue aus"""
        try:
            text = data.get('text', '')
            font_size = data.get('font_size', 22)
            alignment = data.get('alignment', 'center')
            
            result = self.print_text_with_codes_immediate(text, font_size, alignment)
            return result.get('success', False)
            
        except Exception as e:
            logger.error(f"❌ Execute text with codes job error: {e}")
            return False

# Alias für Kompatibilität mit bestehenden Modulen
RobustPhomemoM110 = EnhancedPhomemoM110
