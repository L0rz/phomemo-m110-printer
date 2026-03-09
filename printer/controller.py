"""
Haupt-Controller-Klasse fuer den Phomemo M110 Drucker.
Kombiniert alle Mixins und enthaelt Settings, Services und Print-Orchestrierung.
"""

import os
import time
import json
import logging
import threading
import queue as queue_mod
from typing import Optional, Dict, Any

from PIL import Image, ImageDraw

from config import (
    RFCOMM_DEVICE, PRINTER_WIDTH_PIXELS, PRINTER_BYTES_PER_LINE,
    DEFAULT_LABEL_SIZE, LABEL_WIDTH_PX, LABEL_HEIGHT_PX,
    LABEL_WIDTH_MM, LABEL_HEIGHT_MM, DEFAULT_SETTINGS, CONFIG_FILE,
    LABEL_SIZES, MAX_CONNECTION_ATTEMPTS, BASE_RETRY_DELAY, MAX_RETRY_DELAY,
    HEARTBEAT_INTERVAL, MAX_RETRIES_PER_JOB,
    MIN_X_OFFSET, MAX_X_OFFSET, MIN_Y_OFFSET, MAX_Y_OFFSET,
    DEFAULT_X_OFFSET, DEFAULT_Y_OFFSET,
)
from .models import ConnectionStatus, TransmissionSpeed, PrintJob, ImageProcessingResult
from .bluetooth import BluetoothMixin
from .image_processing import ImageProcessingMixin
from .protocol import ProtocolMixin
from .text_rendering import TextRenderingMixin
from .queue import QueueMixin

# Code Generator import mit Fallback
try:
    from code_generator import CodeGenerator
    HAS_CODE_GENERATOR = True
except ImportError as e:
    HAS_CODE_GENERATOR = False
    print(f"WARNING: Code generator not available: {e}")
    print("QR/Barcode features will be disabled. Install with: pip3 install qrcode pillow")

logger = logging.getLogger(__name__)


class EnhancedPhomemoM110(
    BluetoothMixin,
    ImageProcessingMixin,
    ProtocolMixin,
    TextRenderingMixin,
    QueueMixin,
):
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

        # Label-Groesse aus Settings laden
        self.update_label_size(self.settings.get('label_size', DEFAULT_LABEL_SIZE))

        # Connection Management
        self.connection_status = ConnectionStatus.DISCONNECTED
        self.last_successful_connection = None
        self.connection_attempts = 0
        self.max_connection_attempts = MAX_CONNECTION_ATTEMPTS
        self.base_retry_delay = BASE_RETRY_DELAY
        self.max_retry_delay = MAX_RETRY_DELAY
        self.rfcomm_process = None

        # Print Queue
        self.print_queue = queue_mod.Queue()
        self.queue_processor_running = False
        self.queue_thread = None

        # Code Generator fuer QR/Barcodes (falls verfuegbar)
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
        self._comm_lock = threading.Lock()
        self.start_services()

    # =================== SETTINGS ===================

    def load_settings(self):
        """Laedt persistente Einstellungen aus Datei"""
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
        """Gibt aktuelle Einstellungen zurueck"""
        return self.settings.copy()

    # =================== LABEL SIZES ===================

    def get_available_label_sizes(self) -> Dict[str, Any]:
        """Gibt verfuegbare Label-Groessen zurueck"""
        return LABEL_SIZES.copy()

    def get_current_label_size(self) -> Dict[str, Any]:
        """Gibt aktuelle Label-Groesse zurueck"""
        return {
            'current': self.current_label_size,
            'width_px': self.label_width_px,
            'height_px': self.label_height_px,
            'width_mm': self.label_width_mm,
            'height_mm': self.label_height_mm,
            **LABEL_SIZES[self.current_label_size]
        }

    def update_label_size(self, label_size_key: str) -> bool:
        """Aktualisiert die Label-Groesse"""
        try:
            if label_size_key not in LABEL_SIZES:
                logger.error(f"Unknown label size: {label_size_key}")
                return False

            label_config = LABEL_SIZES[label_size_key]

            self.current_label_size = label_size_key
            self.label_width_mm = label_config['width_mm']
            self.label_height_mm = label_config['height_mm']

            self.label_width_px = min(label_config['width_px'], PRINTER_WIDTH_PIXELS)
            self.label_height_px = label_config['height_px']

            if hasattr(self, 'code_generator') and self.code_generator:
                self.code_generator.label_width_px = self.label_width_px
                self.code_generator.label_height_px = self.label_height_px

            self.settings['label_size'] = label_size_key
            self.save_settings()

            logger.info(f"Label size updated to {label_config['name']}: {self.label_width_px}x{self.label_height_px}px")
            return True

        except Exception as e:
            logger.error(f"Error updating label size: {e}")
            return False

    # =================== SERVICES ===================

    def start_services(self):
        """Startet Background-Services"""
        try:
            self.queue_processor_running = True
            self.queue_thread = threading.Thread(target=self._process_print_queue, daemon=True)
            self.queue_thread.start()

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

        self._cleanup_rfcomm_process()

    # =================== STATUS ===================

    def get_connection_status(self) -> Dict[str, Any]:
        """Gibt detaillierte Verbindungsinfos zurueck"""
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

    # =================== PRINT ORCHESTRATION ===================

    def print_image_with_preview(self, image_data, fit_to_label=True, maintain_aspect=True,
                                 enable_dither=None, dither_threshold=None, dither_strength=None,
                                 scaling_mode='fit_aspect'):
        """Druckt ein Bild mit den aktuellen Offset-Einstellungen"""
        try:
            logger.info("Processing image for print with offsets...")

            result = self.process_image_for_preview(image_data, fit_to_label, maintain_aspect,
                                                    enable_dither, dither_threshold, dither_strength, scaling_mode)
            if not result:
                return False

            processed_img = result.processed_image
            printer_img = self.apply_offsets_to_image(processed_img)

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
            logger.info(f"Starting immediate text print: '{text[:50]}...'")

            img = self.create_text_image_with_offsets(text, font_size, alignment)
            if img:
                logger.info(f"Text image created, size: {img.width}x{img.height}")

                logger.info("Converting image to printer format...")
                image_data = self.image_to_printer_format(img)
                if image_data:
                    logger.info(f"Image converted to printer format ({len(image_data)} bytes)")

                    logger.info("Sending bitmap to printer...")
                    success = self.send_bitmap(image_data, img.height)
                    if success:
                        logger.info("Text printed successfully!")
                        self.stats['successful_jobs'] += 1
                        self.stats['text_jobs'] += 1
                        return {'success': True}
                    else:
                        logger.error("Failed to send bitmap to printer")
                        return {'success': False, 'error': 'Bitmap senden fehlgeschlagen'}
                else:
                    logger.error("Failed to convert image to printer format")
                    return {'success': False, 'error': 'Bildkonvertierung fehlgeschlagen'}
            else:
                logger.error("Failed to create text image")
                return {'success': False, 'error': 'Bild konnte nicht erstellt werden'}
        except Exception as e:
            logger.error(f"Immediate text print error: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return {'success': False, 'error': str(e)}

    def print_image_immediate(self, image_data, fit_to_label=True, maintain_aspect=True,
                              enable_dither=True, dither_threshold=None, dither_strength=None,
                              scaling_mode='fit_aspect') -> bool:
        """Druckt Bild sofort mit FUNKTIONIERENDER TEXT-STRUKTUR"""
        try:
            logger.info("Starting immediate image print with PROVEN TEXT STRUCTURE")

            logger.info("Processing image data with all parameters...")
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
                logger.info(f"Image processed, size: {result.processed_image.size}")

                printer_img = self.apply_offsets_to_image(result.processed_image)
                logger.info(f"Offsets applied, final size: {printer_img.width}x{printer_img.height}")

                logger.info("Converting image to printer format...")
                final_image_data = self.image_to_printer_format(printer_img)

                if final_image_data:
                    logger.info(f"Image converted to printer format ({len(final_image_data)} bytes)")

                    logger.info("Sending bitmap to printer...")
                    success = self.send_bitmap(final_image_data, printer_img.height)

                    if success:
                        logger.info("Image printed successfully with TEXT STRUCTURE!")
                        self.stats['successful_jobs'] += 1
                        return True
                    else:
                        logger.error("Failed to send bitmap to printer")
                        return False
                else:
                    logger.error("Failed to convert image to printer format")
                    return False
            else:
                logger.error("Failed to process image")
                return False

        except Exception as e:
            logger.error(f"Immediate image print error: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return False

    def _print_image_direct(self, img: Image.Image) -> bool:
        """Druckt ein PIL Image direkt (ohne Queue)"""
        try:
            logger.info(f"Converting image to printer format...")
            image_data = self.image_to_printer_format(img)
            if image_data:
                logger.info(f"Image converted to printer format ({len(image_data)} bytes)")

                logger.info("Sending bitmap to printer...")
                success = self.send_bitmap(image_data, img.height)
                if success:
                    logger.info("Image printed successfully!")
                    return True
                else:
                    logger.error("Failed to send bitmap to printer")
                    return False
            else:
                logger.error("Failed to convert image to printer format")
                return False
        except Exception as e:
            logger.error(f"Direct image print error: {e}")
            return False

    # =================== CALIBRATION ===================

    def _execute_calibration_job(self, data):
        """Fuehrt Kalibrierungs-Job aus"""
        try:
            pattern = data.get('pattern', 'border')
            width = data.get('width', self.label_width_px)
            height = data.get('height', self.label_height_px)

            logger.info(f"Executing calibration job: {pattern} ({width}x{height})")

            if pattern == 'full':
                img = Image.new('1', (width, height), 1)
                draw = ImageDraw.Draw(img)

                draw.rectangle([0, 0, width-1, height-1], outline=0, width=2)

                draw.line([width//4, 0, width//4, height], fill=0, width=1)
                draw.line([width//2, 0, width//2, height], fill=0, width=1)
                draw.line([3*width//4, 0, 3*width//4, height], fill=0, width=1)

                draw.line([0, height//4, width, height//4], fill=0, width=1)
                draw.line([0, height//2, width, height//2], fill=0, width=1)
                draw.line([0, 3*height//4, width, 3*height//4], fill=0, width=1)

                corner_size = 10
                draw.rectangle([5, 5, 5+corner_size, 5+corner_size], fill=0)
                draw.rectangle([width-15, 5, width-5, 5+corner_size], fill=0)
                draw.rectangle([5, height-15, 5+corner_size, height-5], fill=0)
                draw.rectangle([width-15, height-15, width-5, height-5], fill=0)

            else:
                img = Image.new('1', (width, height), 1)
                draw = ImageDraw.Draw(img)
                draw.rectangle([0, 0, width-1, height-1], outline=0, width=3)

            final_img = self.apply_offsets_to_image(img)

            image_data = self.image_to_printer_format(final_img)
            if not image_data:
                logger.error("Failed to convert calibration image")
                return False

            success = self.send_bitmap(image_data, final_img.height)
            if success:
                logger.info("Calibration pattern printed successfully!")
            else:
                logger.error("Failed to print calibration pattern")

            return success

        except Exception as e:
            logger.error(f"Calibration job error: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return False

    # =================== QR/BARCODE ===================

    def create_text_image_with_codes(self, text: str, font_size: int = 22, alignment: str = 'center') -> Optional[Image.Image]:
        """Erstellt Text-Bild mit QR/Barcode-Unterstuetzung"""
        try:
            if not HAS_CODE_GENERATOR or self.code_generator is None:
                logger.warning("Code generator not available, falling back to regular text image")
                return self.create_text_image_with_offsets(text, font_size, alignment)

            logger.info(f"Creating text image with codes: font_size={font_size}, alignment={alignment}")

            img = self.code_generator.create_combined_image(text, font_size, alignment)

            if img:
                x_offset = self.settings.get('x_offset', 0)
                y_offset = self.settings.get('y_offset', 0)

                if x_offset != 0 or y_offset != 0:
                    logger.info(f"Applying offsets: x={x_offset}, y={y_offset}")
                    img = self.apply_offsets_to_image(img)

                logger.info(f"Text image with codes created: {img.width}x{img.height}")
                return img
            else:
                logger.error("Failed to create image with codes")
                return None

        except Exception as e:
            logger.error(f"Error creating text image with codes: {e}")
            return None

    def create_text_image_with_codes_preview(self, text: str, font_size: int = 22, alignment: str = 'center') -> Optional[Image.Image]:
        """Erstellt Text-Bild mit QR/Barcode-Unterstuetzung OHNE OFFSETS (fuer Vorschau)"""
        try:
            if not HAS_CODE_GENERATOR or self.code_generator is None:
                logger.warning("Code generator not available, falling back to regular text preview")
                return self.create_text_image_preview(text, font_size, alignment)

            logger.info(f"Creating PREVIEW with codes (NO offsets): font_size={font_size}, alignment={alignment}")

            img = self.code_generator.create_combined_image(text, font_size, alignment)

            if img:
                logger.info(f"Text PREVIEW with codes created (NO offsets): {img.width}x{img.height}")
                return img
            else:
                logger.error("Failed to create text preview with codes")
                return None

        except Exception as e:
            logger.error(f"Text preview with codes error: {e}")
            return None

    def print_text_with_codes_immediate(self, text: str, font_size: int = 22, alignment: str = 'center') -> Dict[str, Any]:
        """Druckt Text mit QR-Codes und Barcodes sofort"""
        try:
            if not HAS_CODE_GENERATOR or self.code_generator is None:
                return {'success': False, 'message': 'QR/Barcode features not available. Install with: pip3 install qrcode pillow'}

            logger.info(f"Starting immediate text with codes print: '{text[:50]}...'")

            img = self.create_text_image_with_codes(text, font_size, alignment)
            if img:
                logger.info(f"Text image with codes created, size: {img.width}x{img.height}")

                success = self._print_image_direct(img)
                if success:
                    logger.info("Text with codes printed successfully!")
                    self.stats['successful_jobs'] += 1
                    self.stats['text_jobs'] += 1
                    return {'success': True, 'message': 'Text mit Codes gedruckt'}
                else:
                    logger.error("Failed to print image with codes")
                    self.stats['failed_jobs'] += 1
                    return {'success': False, 'message': 'Druckfehler'}
            else:
                logger.error("Failed to create text image with codes")
                self.stats['failed_jobs'] += 1
                return {'success': False, 'message': 'Bild-Erstellung fehlgeschlagen'}

        except Exception as e:
            logger.error(f"Print text with codes error: {e}")
            self.stats['failed_jobs'] += 1
            return {'success': False, 'message': str(e)}

    def _execute_text_with_codes_job(self, data: Dict[str, Any]) -> bool:
        """Fuehrt Text-mit-Codes-Job aus der Queue aus"""
        try:
            text = data.get('text', '')
            font_size = data.get('font_size', 22)
            alignment = data.get('alignment', 'center')

            result = self.print_text_with_codes_immediate(text, font_size, alignment)
            return result.get('success', False)

        except Exception as e:
            logger.error(f"Execute text with codes job error: {e}")
            return False


# Alias fuer Kompatibilitaet mit bestehenden Modulen
RobustPhomemoM110 = EnhancedPhomemoM110
