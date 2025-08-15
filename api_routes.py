"""
Erweiterte API Routes für Phomemo M110 Robust Server
Mit Bildvorschau, X-Offset und konfigurierbaren Einstellungen
"""

import os
import time
import logging
import subprocess
import queue
import base64
from flask import request, jsonify, Blueprint
from datetime import datetime
from printer_controller import PrintJob, ConnectionStatus
from werkzeug.utils import secure_filename
from config import SUPPORTED_IMAGE_FORMATS, MAX_UPLOAD_SIZE
from io import BytesIO
from PIL import Image, UnidentifiedImageError

# ---- Helpers: Upload holen & Bildformat aus Bytes erkennen ----
def _get_uploaded_file() -> "FileStorage|None":
    """Akzeptiere multipart Feldnamen 'data' ODER 'image' (rückwärtskompatibel)."""
    return request.files.get('data') or request.files.get('image')

def _detect_image_format(image_bytes: bytes) -> str | None:
    """
    Erkenne Bildformat robust aus Bytes (nicht nur Dateiendung).
    Normalisiert 'JPG' -> 'JPEG'. Gibt z. B. 'PNG', 'JPEG', 'BMP', 'GIF', 'WEBP' zurück.
    """
    try:
        img = Image.open(BytesIO(image_bytes))
        fmt = (img.format or '').upper()
        if fmt == 'JPG':
            fmt = 'JPEG'
        return fmt if fmt in {f.upper() for f in SUPPORTED_IMAGE_FORMATS} else None
    except UnidentifiedImageError:
        return None
    except Exception:
        return None
bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)

def setup_api_routes(app, printer):
    """Registriert alle erweiterten API-Routes"""
    
    @app.route('/api/status')
    def api_status():
        try:
            return jsonify(printer.get_connection_status())
        except Exception as e:
            logger.error(f"Status error: {e}", exc_info=True)
            return jsonify({'connected': False, 'error': str(e)})

    @app.route('/api/settings', methods=['GET'])
    def api_get_settings():
        """Gibt aktuelle Einstellungen zurück"""
        try:
            return jsonify({
                'success': True,
                'settings': printer.get_settings()
            })
        except Exception as e:
            logger.error(f"Get settings error: {e}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/settings', methods=['POST'])
    def api_update_settings():
        """Aktualisiert Drucker-Einstellungen"""
        try:
            new_settings = request.get_json()
            success = printer.update_settings(new_settings)
            
            return jsonify({
                'success': success,
                'settings': printer.get_settings() if success else None
            })
        except Exception as e:
            logger.error(f"Update settings error: {e}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/preview-image', methods=['POST'])
    def api_preview_image():
        """Erstellt Schwarz-Weiß-Vorschau eines Bildes"""
        try:
            # Verwende robuste Datei-Erkennung wie bei print-image
            file = _get_uploaded_file()
            if not file:
                return jsonify({'success': False, 'error': 'Kein Bild hochgeladen (erwarte Feld: data oder image)'}), 400
            if (file.filename or '') == '':
                return jsonify({'success': False, 'error': 'Keine Datei ausgewählt'})
            
            # Datei lesen
            image_data = file.read()
            if not image_data:
                return jsonify({'success': False, 'error': 'Datei ist leer'})
            
            # Größe prüfen
            if len(image_data) > MAX_UPLOAD_SIZE:
                return jsonify({
                    'success': False, 
                    'error': f'Datei zu groß. Maximum: {MAX_UPLOAD_SIZE // (1024*1024)}MB'
                })
            
            # Robuste Format-Erkennung (wie bei print-image)
            detected_format = _detect_image_format(image_data)
            if not detected_format:
                filename = secure_filename(file.filename or 'unknown')
                return jsonify({
                    'success': False, 
                    'error': f'Nicht unterstütztes Bildformat. Datei: "{filename}". Erlaubt: {", ".join(SUPPORTED_IMAGE_FORMATS)}'
                })
            
            logger.info(f"📸 Preview for {detected_format} image, size: {len(image_data)} bytes")
            
            # Parameter aus Request
            fit_to_label = request.form.get('fit_to_label', 'true').lower() == 'true'
            maintain_aspect = request.form.get('maintain_aspect', 'true').lower() == 'true'
            enable_dither = request.form.get('enable_dither', 'true').lower() == 'true'
            dither_threshold = int(request.form.get('dither_threshold', '128'))
            dither_strength = float(request.form.get('dither_strength', '1.0'))
            scaling_mode = request.form.get('scaling_mode', 'fit_aspect')
            
            # Bild verarbeiten mit erweiterten Parametern (image_data bereits gelesen)
            result = printer.process_image_for_preview(
                image_data, fit_to_label, maintain_aspect, enable_dither,
                dither_threshold=dither_threshold, dither_strength=dither_strength,
                scaling_mode=scaling_mode
            )
            
            if result:
                return jsonify({
                    'success': True,
                    'preview_base64': result.preview_base64,
                    'info': {
                        **result.info,
                        # Für Vorschau: Offsets auf 0 setzen, da sie nicht angewendet werden
                        'x_offset': 0,
                        'y_offset': 0
                    }
                })
            else:
                return jsonify({'success': False, 'error': 'Bildverarbeitung fehlgeschlagen'})
                
        except Exception as e:
            logger.error(f"Preview error: {e}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/print-image', methods=['POST'])
    def api_print_image():
        """Druckt hochgeladenes Bild (multipart Feld 'data' ODER 'image')."""
        try:
            # ---- Datei holen (data ODER image) ----
            file = _get_uploaded_file()
            if not file:
                return jsonify({'success': False, 'error': 'Kein Bild hochgeladen (erwarte Feld: data oder image)'}), 400
            if (file.filename or '') == '':
                return jsonify({'success': False, 'error': 'Keine Datei ausgewählt'}), 400

            # ---- Einstellungen aus Form (bestehende Keys unverändert lassen) ----
            use_queue = request.form.get('use_queue', 'false').lower() == 'true'
            fit_to_label = request.form.get('fit_to_label', 'true').lower() == 'true'
            maintain_aspect = request.form.get('maintain_aspect', 'true').lower() == 'true'
            dither = request.form.get('dither', 'true').lower() == 'true'

            # ---- Datei lesen & Basis-Checks ----
            image_data = file.read()
            if not image_data:
                return jsonify({'success': False, 'error': 'Datei ist leer'}), 400

            if len(image_data) > (MAX_UPLOAD_SIZE or 10 * 1024 * 1024):
                return jsonify({'success': False, 'error': 'Datei zu groß (max 10MB)'}), 413

            # ---- Format robust aus Bytes erkennen ----
            detected_fmt = _detect_image_format(image_data)
            if not detected_fmt:
                return jsonify({'success': False, 'error': f'Nicht unterstütztes Format. Erlaubt: {", ".join(SUPPORTED_IMAGE_FORMATS)}'}), 415

            # Für Log/Dateiname (optional)
            filename = secure_filename(file.filename or f"image.{detected_fmt.lower()}")

            # ---- Drucken (wie gehabt) ----
            if use_queue:
                job_id = printer.print_image_async(image_data, filename)
                return jsonify({
                    'success': True,
                    'job_id': job_id,
                    'message': 'Image queued',
                    'filename': filename,
                    'format': detected_fmt,
                    'size_bytes': len(image_data)
                })
            else:
                success = printer.print_image_from_data(image_data, filename)
                return jsonify({
                    'success': success,
                    'filename': filename,
                    'format': detected_fmt,
                    'size_bytes': len(image_data)
                })

        except Exception as e:
            logger.error(f"API print image error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    @app.route('/api/print-text', methods=['POST'])
    def api_print_text():
        """Druckt Text mit Offset-Einstellungen"""
        try:
            text = request.form.get('text', '')
            font_size = int(request.form.get('font_size', 22))
            immediate = request.form.get('immediate', 'false').lower() == 'true'
            alignment = request.form.get('alignment', 'center')  # left, center, right
            
            # Gültige Ausrichtungen prüfen
            if alignment not in ['left', 'center', 'right']:
                alignment = 'center'
            
            if not text.strip():
                return jsonify({'success': False, 'error': 'Kein Text'})
            
            # Replace $TIME$ placeholder
            text = text.replace('$TIME$', datetime.now().strftime('%H:%M:%S'))
            
            if immediate:
                result = printer.print_text_immediate(text, font_size, alignment)
                return jsonify(result)
            else:
                job_id = printer.queue_print_job('text', {
                    'text': text, 
                    'font_size': font_size,
                    'alignment': alignment
                })
                return jsonify({'success': True, 'job_id': job_id})
        except Exception as e:
            logger.error(f"Print text error: {e}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/preview-text', methods=['POST'])
    def api_preview_text():
        """Erstellt Schwarz-Weiß-Vorschau für Text"""
        try:
            text = request.form.get('text', '')
            font_size = int(request.form.get('font_size', 22))
            alignment = request.form.get('alignment', 'center')
            
            if not text.strip():
                return jsonify({'success': False, 'error': 'Kein Text'})
            
            # Replace $TIME$ placeholder
            text = text.replace('$TIME$', datetime.now().strftime('%H:%M:%S'))
            
            # Prüfen ob QR/Barcode-Syntax im Text vorhanden ist
            has_codes = '#qr#' in text or '#bar#' in text
            
            if has_codes and hasattr(printer, 'code_generator') and printer.code_generator is not None:
                # Text mit Codes - OHNE Offsets für Vorschau!
                logger.info("📱 Using QR/Barcode preview (NO offsets)")
                img = printer.create_text_image_with_codes_preview(text, font_size, alignment)
            else:
                # Normaler Text - OHNE Offsets für Vorschau
                logger.info("📝 Using normal text preview (NO offsets)")
                img = printer.create_text_image_preview(text, font_size, alignment)
            
            if img:
                # Als Base64 für Vorschau konvertieren
                import io
                import base64
                
                img_buffer = io.BytesIO()
                img.save(img_buffer, format='PNG')
                img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
                
                return jsonify({
                    'success': True,
                    'preview_base64': img_base64,
                    'info': {
                        'width': img.width,
                        'height': img.height,
                        'text': text,
                        'font_size': font_size,
                        'alignment': alignment,
                        # Für Vorschau: Offsets auf 0 anzeigen, da sie nicht angewendet werden
                        'x_offset': 0,
                        'y_offset': 0
                    }
                })
            else:
                return jsonify({'success': False, 'error': 'Text-Bild konnte nicht erstellt werden'})
                
        except Exception as e:
            logger.error(f"Text preview error: {e}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/print-calibration', methods=['POST'])
    def api_print_calibration():
        """Druckt Kalibrierungs-Muster"""
        try:
            pattern = request.form.get('pattern', 'grid')
            width = int(request.form.get('width', 100))
            height = int(request.form.get('height', 50))
            immediate = request.form.get('immediate', 'true').lower() == 'true'
            
            calibration_data = {
                'pattern': pattern,
                'width': width,
                'height': height
            }
            
            if immediate:
                # Direkt ausführen
                success = printer._execute_calibration_job(calibration_data)
                return jsonify({'success': success})
            else:
                job_id = printer.queue_print_job('calibration', calibration_data)
                return jsonify({'success': True, 'job_id': job_id})
                
        except Exception as e:
            logger.error(f"Print calibration error: {e}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/queue-status', methods=['GET'])
    def api_queue_status():
        """Gibt Queue-Status zurück"""
        try:
            return jsonify(printer.get_queue_status())
        except Exception as e:
            logger.error(f"Queue status error: {e}", exc_info=True)
            return jsonify({'error': str(e)})

    @app.route('/api/clear-queue', methods=['POST'])
    def api_clear_queue():
        """Leert die Print Queue"""
        try:
            cleared_count = printer.clear_queue()
            return jsonify({'success': True, 'cleared_jobs': cleared_count})
        except Exception as e:
            logger.error(f"Clear queue error: {e}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/force-reconnect', methods=['POST'])
    def api_force_reconnect():
        """Erzwingt Bluetooth-Reconnect mit der stabilen Manual Connect Methode"""
        try:
            success = printer.manual_connect_bluetooth()
            return jsonify({'success': success})
        except Exception as e:
            logger.error(f"Force reconnect error: {e}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/manual-connect', methods=['POST'])
    def api_manual_connect():
        """Manuelle Verbindung mit der bewährten rfcomm connect Methode"""
        try:
            success = printer.manual_connect_bluetooth()
            
            if success:
                # Test connection mit Heartbeat
                heartbeat_success = printer._send_heartbeat()
                
                return jsonify({
                    'success': True,
                    'message': 'Manual connection successful',
                    'heartbeat_ok': heartbeat_success,
                    'device_exists': os.path.exists(printer.rfcomm_device),
                    'process_running': printer.rfcomm_process.poll() is None if printer.rfcomm_process else False
                })
            else:
                # Get error details
                error_msg = "Connection failed"
                if printer.rfcomm_process and printer.rfcomm_process.poll() is not None:
                    try:
                        _, stderr = printer.rfcomm_process.communicate(timeout=1)
                        error_msg = f"rfcomm failed: {stderr}"
                    except:
                        error_msg = "rfcomm process failed"
                
                return jsonify({
                    'success': False,
                    'message': error_msg,
                    'device_exists': os.path.exists(printer.rfcomm_device),
                    'process_running': printer.rfcomm_process is not None and printer.rfcomm_process.poll() is None
                })
                
        except Exception as e:
            logger.error(f"Manual connect error: {e}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/test-connection', methods=['POST'])
    def api_test_connection():
        """Testet Bluetooth-Verbindung mit Diagnose"""
        try:
            # Basis-Connectivity testen
            connected = printer.is_connected()
            if not connected:
                reconnect_success = printer.connect_bluetooth()
                return jsonify({
                    'success': reconnect_success,
                    'message': 'Reconnected' if reconnect_success else 'Failed to connect',
                    'diagnostics': {
                        'rfcomm_exists': os.path.exists('/dev/rfcomm0'),
                        'can_write': False
                    }
                })
            
            # Kommando-Test
            test_success = printer.send_command(b'\x1b\x40')  # Reset command
            
            return jsonify({
                'success': test_success,
                'message': 'Command sent successfully' if test_success else 'Failed to send command',
                'diagnostics': {
                    'rfcomm_exists': True,
                    'can_write': test_success
                }
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/init-printer', methods=['POST'])
    def api_init_printer():
        """Initialisiert Drucker mit Setup-Befehlen"""
        try:
            # Drucker-Initialisierungssequenz
            commands = [
                b'\x1b\x40',      # ESC @ - Reset
                b'\x1b\x33\x00',  # ESC 3 0 - Set line spacing
                b'\x1b\x61\x01'   # ESC a 1 - Center align
            ]
            
            success = True
            for cmd in commands:
                if not printer.send_command(cmd):
                    success = False
                    break
                time.sleep(0.2)
            
            return jsonify({'success': success})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/reset-offsets', methods=['POST'])
    def api_reset_offsets():
        """Setzt Offsets auf Standard-Werte zurück"""
        try:
            # Offsets zurücksetzen
            printer.settings['x_offset'] = 0
            printer.settings['y_offset'] = 0
            
            # Settings speichern
            printer.save_settings()
            
            return jsonify({
                'success': True,
                'message': 'Offsets auf 0 zurückgesetzt',
                'settings': {
                    'x_offset': 0,
                    'y_offset': 0
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/test-offsets', methods=['POST'])
    def api_test_offsets():
        """Testet aktuelle Offset-Einstellungen mit Testmuster"""
        try:
            # Erstelle Testmuster mit aktuellen Offsets
            calibration_data = {
                'pattern': 'full',
                'width': printer.label_width_px,
                'height': printer.label_height_px
            }
            
            # Als sofortigen Job ausführen
            success = printer._execute_calibration_job(calibration_data)
            
            return jsonify({
                'success': success,
                'current_offsets': {
                    'x_offset': printer.settings.get('x_offset', 0),
                    'y_offset': printer.settings.get('y_offset', 0)
                }
            })
            
        except Exception as e:
            logger.error(f"Test offsets error: {e}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/print-text-with-codes', methods=['POST'])
    def api_print_text_with_codes():
        """Druckt Text mit QR-Codes und Barcodes"""
        try:
            # Check if code generator is available
            if not hasattr(printer, 'code_generator') or printer.code_generator is None:
                return jsonify({
                    'success': False, 
                    'error': 'QR/Barcode features not available. Install with: pip3 install qrcode pillow'
                })
            
            text = request.form.get('text', '')
            font_size = int(request.form.get('font_size', 22))
            immediate = request.form.get('immediate', 'false').lower() == 'true'
            alignment = request.form.get('alignment', 'center')
            
            if not text.strip():
                return jsonify({'success': False, 'error': 'Kein Text'})
            
            # Replace $TIME$ placeholder
            text = text.replace('$TIME$', datetime.now().strftime('%H:%M:%S'))
            
            if immediate:
                result = printer.print_text_with_codes_immediate(text, font_size, alignment)
                return jsonify(result)
            else:
                job_id = printer.queue_print_job('text_with_codes', {
                    'text': text, 
                    'font_size': font_size,
                    'alignment': alignment
                })
                return jsonify({'success': True, 'job_id': job_id})
        except Exception as e:
            logger.error(f"Print text with codes error: {e}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/preview-text-with-codes', methods=['POST'])
    def api_preview_text_with_codes():
        """Erstellt Vorschau für Text mit QR-Codes und Barcodes"""
        try:
            # Check if code generator is available
            if not hasattr(printer, 'code_generator') or printer.code_generator is None:
                return jsonify({
                    'success': False, 
                    'error': 'QR/Barcode features not available. Install with: pip3 install qrcode pillow'
                })
            
            text = request.form.get('text', '')
            font_size = int(request.form.get('font_size', 22))
            alignment = request.form.get('alignment', 'center')
            
            if not text.strip():
                return jsonify({'success': False, 'error': 'Kein Text'})
            
            # Replace $TIME$ placeholder
            text = text.replace('$TIME$', datetime.now().strftime('%H:%M:%S'))
            
            # Bild mit Codes erstellen - OHNE OFFSETS für Vorschau!
            img = printer.create_text_image_with_codes_preview(text, font_size, alignment)
            if img:
                # Als Base64 für Vorschau konvertieren
                import io
                import base64
                
                img_buffer = io.BytesIO()
                img.save(img_buffer, format='PNG')
                img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
                
                # Codes analysieren für Info
                processed_text, codes = printer.code_generator.parse_and_process_text(text)
                
                return jsonify({
                    'success': True,
                    'preview_base64': img_base64,
                    'info': {
                        'width': img.width,
                        'height': img.height,
                        'text': text,
                        'processed_text': processed_text,
                        'font_size': font_size,
                        'alignment': alignment,
                        'codes_found': len(codes),
                        'codes': codes,
                        'x_offset': 0,
                        'y_offset': 0
                    }
                })
            else:
                return jsonify({'success': False, 'error': 'Bild mit Codes konnte nicht erstellt werden'})
                
        except Exception as e:
            logger.error(f"Text with codes preview error: {e}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/code-syntax-help', methods=['GET'])
    def api_code_syntax_help():
        """Gibt Hilfe zur QR/Barcode-Syntax zurück"""
        try:
            help_text = printer.code_generator.get_syntax_help()
            return jsonify({
                'success': True,
                'syntax_help': help_text,
                'examples': [
                    '#qr#https://example.com#qr#',
                    '#qr:150#Größerer QR-Code#qr#',
                    '#bar#1234567890#bar#',
                    '#bar:80#Höherer Barcode#bar#'
                ]
            })
        except Exception as e:
            logger.error(f"Code syntax help error: {e}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/label-sizes', methods=['GET'])
    def api_get_label_sizes():
        """Gibt verfügbare Label-Größen zurück"""
        try:
            available_sizes = printer.get_available_label_sizes()
            current_size = printer.get_current_label_size()
            
            return jsonify({
                'success': True,
                'available_sizes': available_sizes,
                'current_size': current_size
            })
        except Exception as e:
            logger.error(f"Get label sizes error: {e}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/label-size', methods=['POST'])
    def api_set_label_size():
        """Setzt neue Label-Größe"""
        try:
            label_size = request.form.get('label_size', '')
            
            if not label_size:
                return jsonify({'success': False, 'error': 'Keine Label-Größe angegeben'})
            
            success = printer.update_label_size(label_size)
            if success:
                current_size = printer.get_current_label_size()
                return jsonify({
                    'success': True,
                    'message': f'Label-Größe geändert zu {current_size["name"]}',
                    'current_size': current_size
                })
            else:
                return jsonify({'success': False, 'error': 'Ungültige Label-Größe'})
                
        except Exception as e:
            logger.error(f"Set label size error: {e}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)})

    app.register_blueprint(bp)
    return app
