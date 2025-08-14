"""
Erweiterte API Routes für Phomemo M110 Robust Server
Mit Bildvorschau, X-Offset und konfigurierbaren Einstellungen
"""

import os
import time
import logging
import subprocess
import queue
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
            
            # Bild verarbeiten mit erweiterten Dithering-Parametern
            image_data = file.read()
            result = printer.process_image_for_preview(
                image_data, fit_to_label, maintain_aspect, enable_dither,
                dither_threshold=dither_threshold, dither_strength=dither_strength
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
            
            image_data = file.read()
            
            if immediate:
                success = printer.print_image_immediate(
                    image_data, fit_to_label, maintain_aspect, enable_dither,
                    dither_threshold=dither_threshold, dither_strength=dither_strength
                )
                return jsonify({'success': success})
            else:
                job_id = printer.print_image_with_preview(
                    image_data, fit_to_label, maintain_aspect, enable_dither,
                    dither_threshold=dither_threshold, dither_strength=dither_strength
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
        """Erzwingt Bluetooth-Reconnect"""
        try:
            success = printer.connect_bluetooth(force_reconnect=True)
            return jsonify({'success': success})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/manual-connect', methods=['POST'])
    def api_manual_connect():
        """Manuelle Verbindung mit exakten Bluetooth-Befehlen"""
        try:
            logger.info("Starting manual Bluetooth connection sequence...")
            
            # 1. Alte rfcomm-Verbindung beenden
            logger.info("Step 1: Releasing old rfcomm connection...")
            subprocess.run(['sudo', 'rfcomm', 'release', '0'], capture_output=True, timeout=10)
            time.sleep(1)
            
            # 2. Trust setzen
            logger.info("Step 2: Ensuring pairing and trust...")
            trust_result = subprocess.run(
                ['bluetoothctl', 'trust', printer.mac_address],
                capture_output=True, text=True, timeout=15
            )
            
            # 3. Neue rfcomm-Verbindung erstellen
            logger.info("Step 3: Creating new rfcomm connection...")
            connect_result = subprocess.run(
                ['sudo', 'rfcomm', 'bind', '0', printer.mac_address],
                capture_output=True, text=True, timeout=20
            )
            
            time.sleep(3)
            
            # 4. Verbindung testen
            connected = printer.is_connected()
            
            if connected:
                printer.connection_status = ConnectionStatus.CONNECTED
                printer.last_successful_connection = time.time()
                logger.info("Manual connection successful")
                
                return jsonify({
                    'success': True,
                    'message': 'Manual connection established',
                    'steps': {
                        'trust': trust_result.returncode == 0,
                        'rfcomm': connect_result.returncode == 0,
                        'connected': connected
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Manual connection failed',
                    'steps': {
                        'trust': trust_result.returncode == 0,
                        'rfcomm': connect_result.returncode == 0,
                        'connected': connected
                    },
                    'errors': {
                        'trust_error': trust_result.stderr if trust_result.returncode != 0 else None,
                        'rfcomm_error': connect_result.stderr if connect_result.returncode != 0 else None
                    }
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

    return app
