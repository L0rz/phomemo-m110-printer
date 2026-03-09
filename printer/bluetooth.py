"""
Bluetooth-Verbindung und RFCOMM-Transport fuer den Phomemo M110 Drucker.
"""

import os
import time
import logging
import subprocess
import socket

from config import (
    RFCOMM_DEVICE, USE_SOCKET_TRANSPORT, SOCKET_CONNECT_TIMEOUT,
    RFCOMM_CHANNEL, CHUNK_SIZE_BYTES, INTER_CHUNK_SLEEP_MS,
)
from .models import ConnectionStatus

logger = logging.getLogger(__name__)


class BluetoothMixin:
    """Mixin fuer Bluetooth-Verbindung und Kommando-Uebertragung."""

    def is_connected(self):
        """Prueft ob Drucker verbunden ist"""
        return os.path.exists(self.rfcomm_device)

    def connect_bluetooth(self, force_reconnect=False):
        """Stellt Bluetooth-Verbindung her mit der stabilen Manual Connect Methode"""
        return self.manual_connect_bluetooth()

    def manual_connect_bluetooth(self):
        """Manuelle Bluetooth-Verbindung mit der bewaehrten rfcomm connect Methode"""
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

    def _open_rfcomm_socket(self):
        """Oeffnet ein RFCOMM Socket zum Drucker (falls konfiguriert).

        Returns a connected socket.socket or raises.
        """
        try:
            s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            s.settimeout(float(SOCKET_CONNECT_TIMEOUT))
            s.connect((self.mac_address, int(RFCOMM_CHANNEL)))
            # Set blocking mode after connect
            s.settimeout(None)
            return s
        except Exception as e:
            logger.error(f"RFCOMM socket connect failed: {e}")
            raise

    def send_command(self, command_bytes):
        """Sendet Kommando an Drucker"""
        try:
            if not self.is_connected():
                if not self.connect_bluetooth():
                    return False

            # Serialize access to the device to avoid concurrent writes
            with self._comm_lock:
                # Optionally use RFCOMM socket transport
                if USE_SOCKET_TRANSPORT:
                    try:
                        s = self._open_rfcomm_socket()
                    except Exception:
                        return False
                    try:
                        total = len(command_bytes)
                        sent = 0
                        CHUNK_SIZE = int(CHUNK_SIZE_BYTES)
                        INTER_CHUNK_SLEEP = float(INTER_CHUNK_SLEEP_MS) / 1000.0
                        while sent < total:
                            chunk = command_bytes[sent:sent+CHUNK_SIZE]
                            n = s.send(chunk)
                            sent += n
                            if INTER_CHUNK_SLEEP > 0:
                                time.sleep(INTER_CHUNK_SLEEP)
                        logger.debug(f"send_command(socket): sent {sent}/{total} bytes to {self.mac_address}:{RFCOMM_CHANNEL}")
                        return True
                    finally:
                        try:
                            s.close()
                        except Exception:
                            pass
                else:
                    with open(self.rfcomm_device, 'wb') as printer:
                        # Robust write: ensure all bytes are written
                        total = len(command_bytes)
                        written = 0
                        # Use configurable chunk size and inter-chunk sleep from config.py
                        CHUNK_SIZE = int(CHUNK_SIZE_BYTES)
                        INTER_CHUNK_SLEEP = float(INTER_CHUNK_SLEEP_MS) / 1000.0
                        while written < total:
                            chunk = command_bytes[written:written+CHUNK_SIZE]
                            n = printer.write(chunk)
                            # On file-like devices, write() should return number of bytes written or None
                            if n is None:
                                # Fallback: assume whole chunk written
                                n = len(chunk)
                            written += n
                            printer.flush()
                            # small pause between chunks to give controller time
                            if INTER_CHUNK_SLEEP > 0:
                                time.sleep(INTER_CHUNK_SLEEP)
                        # small pause to allow device to process after full write
                        time.sleep(0.01)
                        logger.debug(f"send_command: wrote {written}/{total} bytes to {self.rfcomm_device} (chunks={CHUNK_SIZE})")
            return True
        except Exception as e:
            logger.error(f"Send command error: {e}")
            return False

    def _connection_monitor(self):
        """Background Thread fuer Connection Monitoring mit stabiler Verbindungsmethode"""
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
