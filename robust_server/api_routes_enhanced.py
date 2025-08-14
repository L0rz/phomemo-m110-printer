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
from flask import request, jsonify
from datetime import datetime
from printer_controller_enhanced import PrintJob, ConnectionStatus
from werkzeug.utils import secure_filename
from config_enhanced import SUPPORTED_IMAGE_FORMATS, MAX_UPLOAD_SIZE

logger = logging.getLogger(__name__)

def setup_enhanced_api_routes(app, printer):
    """Registriert alle erweiterten API-Routes"""
    
    @app.route('/api/status')
    def api_status():
        try:
            return jsonify(printer.get_connection_status())
        except Exception as e:
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
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/preview-image', methods=['POST'])
    def api_preview_image():
        """Erstellt Schwarz-Weiß-Vorschau eines Bildes"""
        try:
            if 'image' not in request.files:
                return jsonify({'success': False, 'error': 'Kein Bild hochgeladen'})
            
            file = request.files['image']
            if file.filename == '':
                return jsonify({'success': False, 'error': 'Keine Datei ausgewählt'})
            
            # Datei-Validierung
            filename = secure_filename(file.filename)
            file_ext = filename.rsplit('.', 1)[1].upper() if '.' in filename else ''
            
            if file_ext not in SUPPORTED_IMAGE_FORMATS:
                return jsonify({
                    'success': False, 
                    'error': f'Nicht unterstütztes Format. Erlaubt: {", ".join(SUPPORTED_IMAGE_FORMATS)}'
                })
            
            # Größe prüfen
            file.seek(0, 2)  # Zum Ende
            file_size = file.tell()
            file.seek(0)  # Zurück zum Anfang
            
            if file_size > MAX_UPLOAD_SIZE:
                return jsonify({
                    'success': False, 
                    'error': f'Datei zu groß. Maximum: {MAX_UPLOAD_SIZE // (1024*1024)}MB'
                })
            
            # Parameter aus Request
            fit_to_label = request.form.get('fit_to_label', 'true').lower() == 'true'
            maintain_aspect = request.form.get('maintain_aspect', 'true').lower() == 'true'
            enable_dither = request.form.get('enable_dither', 'true').lower() == 'true'
            dither_threshold = int(request.form.get('dither_threshold', '128'))
            dither_strength = float(request.form.get('dither_strength', '1.0'))
            scaling_mode = request.form.get('scaling_mode', 'fit_aspect')
            
            # Bild verarbeiten mit erweiterten Parametern
            image_data = file.read()
            result = printer.process_image_for_preview(
                image_data, fit_to_label, maintain_aspect, enable_dither,
                dither_threshold=dither_threshold, dither_strength=dither_strength,
                scaling_mode=scaling_mode
            )
            
            if result:
                return jsonify({
                    'success': True,
                    'preview_base64': result.preview_base64,
                    'info': result.info
                })
            else:
                return jsonify({'success': False, 'error': 'Bildverarbeitung fehlgeschlagen'})
                
        except Exception as e:
            logger.error(f"Preview error: {e}")
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/print-image', methods=['POST'])
    def api_print_image():
        """Druckt ein Bild mit Vorschau-Verarbeitung"""
        try:
            if 'image' not in request.files:
                return jsonify({'success': False, 'error': 'Kein Bild hochgeladen'})
            
            file = request.files['image']
            immediate = request.form.get('immediate', 'false').lower() == 'true'
            fit_to_label = request.form.get('fit_to_label', 'true').lower() == 'true'
            maintain_aspect = request.form.get('maintain_aspect', 'true').lower() == 'true'
            enable_dither = request.form.get('enable_dither', 'true').lower() == 'true'
            dither_threshold = int(request.form.get('dither_threshold', '128'))
            dither_strength = float(request.form.get('dither_strength', '1.0'))
            scaling_mode = request.form.get('scaling_mode', 'fit_aspect')
            
            image_data = file.read()
            
            if immediate:
                success = printer.print_image_immediate(
                    image_data, fit_to_label, maintain_aspect, enable_dither,
                    dither_threshold=dither_threshold, dither_strength=dither_strength,
                    scaling_mode=scaling_mode
                )
                return jsonify({'success': success})
            else:
                job_id = printer.print_image_with_preview(
                    image_data, fit_to_label, maintain_aspect, enable_dither,
                    dither_threshold=dither_threshold, dither_strength=dither_strength,
                    scaling_mode=scaling_mode
                )
                return jsonify({'success': bool(job_id), 'job_id': job_id})
                
        except Exception as e:
            logger.error(f"Print image error: {e}")
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/print-text', methods=['POST'])
    def api_print_text():
        """Druckt Text mit Offset-Einstellungen"""
        try:
            text = request.form.get('text', '')
            font_size = int(request.form.get('font_size', 22))
            immediate = request.form.get('immediate', 'false').lower() == 'true'
            
            if not text.strip():
                return jsonify({'success': False, 'error': 'Kein Text'})
            
            # Replace $TIME$ placeholder
            text = text.replace('$TIME$', datetime.now().strftime('%H:%M:%S'))
            
            if immediate:
                success = printer.print_text_immediate(text, font_size)
                return jsonify({'success': success})
            else:
                job_id = printer.queue_print_job('text', {'text': text, 'font_size': font_size})
                return jsonify({'success': True, 'job_id': job_id})
                
        except Exception as e:
            logger.error(f"Print text error: {e}")
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
            logger.error(f"Calibration error: {e}")
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/queue-status', methods=['GET'])
    def api_queue_status():
        """Gibt Queue-Status zurück"""
        try:
            return jsonify(printer.get_queue_status())
        except Exception as e:
            return jsonify({'error': str(e)})

    @app.route('/api/clear-queue', methods=['POST'])
    def api_clear_queue():
        """Leert die Print Queue"""
        try:
            cleared_count = printer.clear_queue()
            return jsonify({'success': True, 'cleared_jobs': cleared_count})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/force-reconnect', methods=['POST'])
    def api_force_reconnect():
        """Erzwingt Bluetooth-Reconnect mit der stabilen Manual Connect Methode"""
        try:
            success = printer.manual_connect_bluetooth()
            return jsonify({'success': success})
        except Exception as e:
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
            logger.error(f"Manual connect error: {e}")
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
            return jsonify({'success': False, 'error': str(e)})
        @bp.route('/api/preview-image-json', methods=['POST'])
    def api_preview_image_json():
        """
        JSON: { image_base64, fit_to_label?, maintain_aspect?, enable_dither?,
                dither_threshold?, dither_strength?, scaling_mode? }
        """
        try:
            data = request.get_json(silent=True) or {}
            b64 = (data.get('image_base64') or '').split(',', 1)[-1].strip()
            if not b64:
                return jsonify({'success': False, 'error': 'Kein Bild (image_base64)'}), 400

            img_bytes = base64.b64decode(b64 + '===')

            fit_to_label     = bool(data.get('fit_to_label', True))
            maintain_aspect  = bool(data.get('maintain_aspect', True))
            enable_dither    = data.get('enable_dither', True)
            dither_threshold = int(data.get('dither_threshold', 128))
            dither_strength  = float(data.get('dither_strength', 1.0))
            scaling_mode     = data.get('scaling_mode', 'fit_aspect')

            result = printer.process_image_for_preview(
                img_bytes, fit_to_label, maintain_aspect, enable_dither,
                dither_threshold=dither_threshold, dither_strength=dither_strength,
                scaling_mode=scaling_mode
            )
            if not result:
                return jsonify({'success': False, 'error': 'Bildverarbeitung fehlgeschlagen'}), 500

            return jsonify({'success': True,
                            'preview_base64': result.preview_base64,
                            'meta': result.meta})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @bp.route('/api/print-image-json', methods=['POST'])
    def api_print_image_json():
        """
        JSON: { image_base64, immediate?, fit_to_label?, maintain_aspect?, enable_dither?,
                dither_threshold?, dither_strength?, scaling_mode? }
        """
        try:
            data = request.get_json(silent=True) or {}
            b64 = (data.get('image_base64') or '').split(',', 1)[-1].strip()
            if not b64:
                return jsonify({'success': False, 'error': 'Kein Bild (image_base64)'}), 400

            img_bytes = base64.b64decode(b64 + '===')

            immediate        = str(data.get('immediate', 'true')).lower() == 'true'
            fit_to_label     = bool(data.get('fit_to_label', True))
            maintain_aspect  = bool(data.get('maintain_aspect', True))
            enable_dither    = data.get('enable_dither', True)
            dither_threshold = int(data.get('dither_threshold', 128))
            dither_strength  = float(data.get('dither_strength', 1.0))
            scaling_mode     = data.get('scaling_mode', 'fit_aspect')

            if immediate:
                ok = printer.print_image_immediate(
                    img_bytes, fit_to_label, maintain_aspect,
                    dither_threshold=dither_threshold, dither_strength=dither_strength,
                    scaling_mode=scaling_mode
                )
                return jsonify({'success': ok})
            else:
                job_id = printer.print_image_with_preview(
                    img_bytes, fit_to_label, maintain_aspect, enable_dither,
                    dither_threshold=dither_threshold, dither_strength=dither_strength,
                    scaling_mode=scaling_mode
                )
                return jsonify({'success': bool(job_id), 'job_id': job_id})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    return app
