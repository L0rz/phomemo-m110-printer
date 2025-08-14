"""
API Routes für Phomemo M110 Robust Server
"""

import os
import time
import logging
import subprocess
import queue
from flask import request, jsonify
from datetime import datetime
from printer_controller import PrintJob, ConnectionStatus

logger = logging.getLogger(__name__)

def setup_api_routes(app, printer):
    """Registriert alle API-Routes"""
    
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
            logger.info(f"Trust result: {trust_result.returncode}")
            
            # 3. rfcomm connect im Hintergrund starten
            logger.info("Step 3: Starting rfcomm connect...")
            cmd = ['sudo', 'rfcomm', 'connect', '0', printer.mac_address, '1']
            
            # Cleanup old process
            printer._cleanup_rfcomm_process()
            
            # Start new process
            printer.rfcomm_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait and check
            time.sleep(4)
            
            if printer.is_connected():
                with printer._lock:
                    printer.connection_status = ConnectionStatus.CONNECTED
                    printer.last_successful_connection = datetime.now()
                    printer.connection_attempts = 0
                    printer.stats['reconnections'] += 1
                
                # Test with heartbeat
                heartbeat_success = printer._send_heartbeat()
                
                return jsonify({
                    'success': True,
                    'message': 'Manual connection successful',
                    'heartbeat_ok': heartbeat_success,
                    'device_exists': os.path.exists(printer.rfcomm_device),
                    'process_running': printer.rfcomm_process.poll() is None
                })
            else:
                # Get error from process
                error_msg = "Device not accessible"
                if printer.rfcomm_process.poll() is not None:
                    _, stderr = printer.rfcomm_process.communicate()
                    error_msg = f"rfcomm failed: {stderr}"
                
                return jsonify({
                    'success': False,
                    'error': error_msg,
                    'device_exists': os.path.exists(printer.rfcomm_device),
                    'process_running': printer.rfcomm_process is not None and printer.rfcomm_process.poll() is None
                })
            
        except Exception as e:
            logger.error(f"Manual connect error: {e}")
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
            return jsonify({
                'size': printer.print_queue.qsize(),
                'running': printer.queue_processor_running,
                'recent_jobs': []  # Könnte erweitert werden mit Job-History
            })
        except Exception as e:
            return jsonify({'error': str(e)})
