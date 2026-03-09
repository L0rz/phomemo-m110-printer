"""
Drucker-Protokoll: Adaptive Speed Control, Bitmap-Uebertragung und Checksums
fuer den Phomemo M110 Drucker.
"""

import time
import logging
from typing import Dict, Tuple

from PIL import Image, ImageDraw
from config import (
    CHUNK_SIZE_BYTES, INTER_CHUNK_SLEEP_MS, BLOCK_WRITE_RETRIES,
    DEFAULT_BLOCK_DELAY_MS,
)
from .models import TransmissionSpeed

logger = logging.getLogger(__name__)


class ProtocolMixin:
    """Mixin fuer Drucker-Protokoll, Speed Control und Bitmap-Uebertragung."""

    # =================== ADAPTIVE SPEED CONTROL ===================

    def calculate_image_complexity(self, image_data: bytes) -> float:
        """Berechnet die Komplexitaet der Bilddaten als Prozentsatz non-zero bytes"""
        try:
            if not image_data:
                return 0.0

            total_bytes = len(image_data)
            zero_bytes = image_data.count(0)
            non_zero_bytes = total_bytes - zero_bytes

            complexity = non_zero_bytes / total_bytes

            logger.info(f"Image complexity: {complexity*100:.1f}% ({non_zero_bytes}/{total_bytes} non-zero bytes)")

            return complexity

        except Exception as e:
            logger.error(f"Error calculating image complexity: {e}")
            return 0.1

    def determine_transmission_speed(self, complexity: float) -> TransmissionSpeed:
        """Bestimmt die optimale Uebertragungsgeschwindigkeit basierend auf Komplexitaet"""
        if not self.settings.get('adaptive_speed_enabled', True):
            return TransmissionSpeed.NORMAL

        max_for_fast = self.settings.get('max_complexity_for_fast', 0.02)
        min_for_slow = self.settings.get('min_complexity_for_slow', 0.08)
        force_slow_threshold = 0.12

        if complexity < max_for_fast:
            return TransmissionSpeed.ULTRA_FAST
        elif complexity < 0.05:
            return TransmissionSpeed.FAST
        elif complexity < min_for_slow:
            return TransmissionSpeed.NORMAL
        elif complexity < force_slow_threshold:
            return TransmissionSpeed.SLOW
        else:
            if self.settings.get('force_slow_for_complex', True):
                return TransmissionSpeed.ULTRA_SLOW
            else:
                return TransmissionSpeed.SLOW

    def get_speed_config(self, speed: TransmissionSpeed) -> Dict[str, float]:
        """Gibt die Timing-Konfiguration fuer eine bestimmte Geschwindigkeit zurueck"""
        base_configs = {
            TransmissionSpeed.ULTRA_FAST: {
                'block_delay': 0.005,
                'line_delay': 0.001,
                'init_delay': 0.01,
                'header_delay': 0.005,
                'post_delay': 0.01,
                'description': 'Ultra Fast (sehr einfache Bilder)'
            },
            TransmissionSpeed.FAST: {
                'block_delay': 0.01,
                'line_delay': 0.002,
                'init_delay': 0.02,
                'header_delay': 0.01,
                'post_delay': 0.02,
                'description': 'Fast (einfache Bilder)'
            },
            TransmissionSpeed.NORMAL: {
                'block_delay': 0.02,
                'line_delay': 0.005,
                'init_delay': 0.02,
                'header_delay': 0.01,
                'post_delay': 0.02,
                'description': 'Normal (mittlere Komplexitaet)'
            },
            TransmissionSpeed.SLOW: {
                'block_delay': 0.05,
                'line_delay': 0.01,
                'init_delay': 0.05,
                'header_delay': 0.02,
                'post_delay': 0.05,
                'description': 'Slow (komplexe Bilder)'
            },
            TransmissionSpeed.ULTRA_SLOW: {
                'block_delay': 0.1,
                'line_delay': 0.02,
                'init_delay': 0.1,
                'header_delay': 0.05,
                'post_delay': 0.1,
                'description': 'Ultra Slow (sehr komplexe Bilder)'
            }
        }

        config = base_configs.get(speed, base_configs[TransmissionSpeed.NORMAL]).copy()

        timing_multiplier = self.settings.get('timing_multiplier', 1.0)

        if timing_multiplier != 1.0:
            for key in ['block_delay', 'line_delay', 'init_delay', 'header_delay', 'post_delay']:
                if key in config:
                    config[key] *= timing_multiplier

            if timing_multiplier > 1.0:
                config['description'] += f" (x{timing_multiplier:.1f} slower)"
            elif timing_multiplier < 1.0:
                config['description'] += f" (x{1/timing_multiplier:.1f} faster)"

        if speed == TransmissionSpeed.ULTRA_FAST and self.settings.get('adaptive_speed_aggressive', False):
            config['block_delay'] *= 0.5
            config['line_delay'] *= 0.5
            config['description'] += " (aggressive)"

        return config

    def analyze_and_determine_speed(self, image_data: bytes) -> Tuple[TransmissionSpeed, Dict[str, float]]:
        """Analysiert Bilddaten und bestimmt optimale Uebertragungsgeschwindigkeit"""
        complexity = self.calculate_image_complexity(image_data)
        speed = self.determine_transmission_speed(complexity)
        config = self.get_speed_config(speed)

        logger.info(f"Adaptive Speed Control:")
        logger.info(f"   Complexity: {complexity*100:.1f}%")
        logger.info(f"   Speed: {speed.value}")
        logger.info(f"   Config: {config['description']}")

        return speed, config

    # =================== BITMAP TRANSMISSION ===================

    def send_bitmap(self, image_data: bytes, height: int) -> bool:
        """Adaptive Speed Bitmap-Uebertragung basierend auf Datenkomplexitaet"""
        try:
            width_bytes = self.bytes_per_line  # Immer 48 Bytes

            logger.info(f"ADAPTIVE BITMAP TRANSMISSION: {len(image_data)} bytes, {height} lines")

            # Validierung
            expected_size = height * width_bytes
            if len(image_data) != expected_size:
                logger.error(f"DATA SIZE ERROR: Got {len(image_data)}, expected {expected_size}")
                return False

            # Adaptive Speed Analysis
            speed, timing_config = self.analyze_and_determine_speed(image_data)
            logger.info(f"Using {timing_config['description']}")

            # Anti-Drift: Mindestabstand zwischen Druckvorgaengen
            if hasattr(self, 'last_print_time'):
                time_since_last = time.time() - self.last_print_time
                min_delay = max(0.15, timing_config['post_delay'] * 2)
                if time_since_last < min_delay:
                    time.sleep(min_delay - time_since_last)

            # 1. Drucker initialisieren
            logger.info("Step 1: Initialize printer")
            if not self.send_command(b'\x1b\x40'):  # ESC @ - Reset
                logger.error("Failed to initialize printer")
                return False
            time.sleep(timing_config['init_delay'])

            # 2. Raster-Bitmap-Header senden
            logger.info("Step 2: Send bitmap header")
            m = 0  # Normal mode
            header = bytes([
                0x1D, 0x76, 0x30, m,
                width_bytes & 0xFF, (width_bytes >> 8) & 0xFF,
                height & 0xFF, (height >> 8) & 0xFF
            ])

            if not self.send_command(header):
                logger.error("Failed to send bitmap header")
                return False
            time.sleep(timing_config['header_delay'])

            # 3. Adaptive Bilduebertragung
            logger.info(f"Step 3: Adaptive image transmission ({speed.value})")

            if len(image_data) <= 1024 and speed in [TransmissionSpeed.ULTRA_FAST, TransmissionSpeed.FAST]:
                logger.info("DIRECT TRANSFER: Sending complete simple image at once")
                success = self.send_command(image_data)
                if not success:
                    logger.error("Direct transfer failed")
                    return False
            else:
                logger.info("ADAPTIVE BLOCK TRANSFER")

                if speed == TransmissionSpeed.ULTRA_FAST:
                    BLOCK_SIZE = 2400
                elif speed == TransmissionSpeed.FAST:
                    BLOCK_SIZE = 1440
                elif speed == TransmissionSpeed.NORMAL:
                    BLOCK_SIZE = 960
                elif speed == TransmissionSpeed.SLOW:
                    BLOCK_SIZE = 480
                else:  # ULTRA_SLOW
                    BLOCK_SIZE = 240

                lines_per_block = BLOCK_SIZE // width_bytes
                actual_block_size = lines_per_block * width_bytes

                logger.info(f"Block size: {actual_block_size} bytes ({lines_per_block} lines)")

                success = True
                total_blocks = (len(image_data) + actual_block_size - 1) // actual_block_size

                with self._comm_lock:
                    try:
                        with open(self.rfcomm_device, 'wb') as printer_fd:
                            for i in range(0, len(image_data), actual_block_size):
                                block_num = i // actual_block_size + 1
                                block = image_data[i:i + actual_block_size]

                                logger.debug(f"Sending block {block_num}/{total_blocks}: {len(block)} bytes")

                                written = 0
                                total = len(block)
                                try_count = 0
                                ok = False
                                MAX_RETRIES = int(BLOCK_WRITE_RETRIES)
                                CHUNK_SIZE = int(CHUNK_SIZE_BYTES)
                                INTER_CHUNK_SLEEP = float(INTER_CHUNK_SLEEP_MS) / 1000.0
                                while try_count < MAX_RETRIES and not ok:
                                    try:
                                        while written < total:
                                            chunk = block[written:written+CHUNK_SIZE]
                                            n = printer_fd.write(chunk)
                                            if n is None:
                                                n = len(chunk)
                                            written += n
                                            printer_fd.flush()
                                            if INTER_CHUNK_SLEEP > 0:
                                                time.sleep(INTER_CHUNK_SLEEP)
                                        ok = True
                                    except Exception as e:
                                        logger.warning(f"Write error on block {block_num}: {e}")
                                        try_count += 1
                                        written = 0
                                        backoff = timing_config.get('block_delay', 0.02) * 2 + (DEFAULT_BLOCK_DELAY_MS / 1000.0)
                                        time.sleep(backoff)

                                if ok:
                                    logger.info(f"Block {block_num} written: {written}/{total} bytes (tries={try_count+1})")

                                if not ok:
                                    logger.error(f"Block {block_num} failed after retry")
                                    success = False
                                    break

                                if i + actual_block_size < len(image_data):
                                    time.sleep(timing_config['block_delay'])
                    except Exception as e:
                        logger.error(f"Error opening/writing device: {e}")
                        success = False

            # 4. Adaptive Abschluss
            time.sleep(timing_config['post_delay'])
            self.last_print_time = time.time()

            if success:
                logger.info(f"ADAPTIVE BITMAP SENT SUCCESSFULLY using {speed.value}")
            else:
                logger.error("ADAPTIVE BITMAP TRANSMISSION FAILED")

            return success

        except Exception as e:
            logger.error(f"Adaptive bitmap transmission error: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return False

    # =================== ADAPTIVE SPEED TESTING ===================

    def test_adaptive_speed_with_images(self) -> Dict:
        """Testet die adaptive Geschwindigkeitssteuerung mit verschiedenen Komplexitaetsgraden"""
        import os
        logger.info("TESTING ADAPTIVE SPEED CONTROL")

        test_results = {
            'tests_run': 0,
            'successful_tests': 0,
            'results': []
        }

        try:
            # Test 1: Ultra-einfaches Bild (< 2% non-zero)
            logger.info("\nTest 1: Ultra-Simple Image")
            simple_img = Image.new('1', (320, 240), 1)
            draw = ImageDraw.Draw(simple_img)
            draw.line([160, 0, 160, 239], fill=0, width=1)

            simple_data = self.image_to_printer_format(simple_img)
            if simple_data:
                speed, config = self.analyze_and_determine_speed(simple_data)
                test_results['results'].append({
                    'test': 'Ultra-Simple',
                    'complexity': self.calculate_image_complexity(simple_data),
                    'speed': speed.value,
                    'description': config['description']
                })
                test_results['tests_run'] += 1
                test_results['successful_tests'] += 1

            # Test 2: Mittlere Komplexitaet (~ 5-8% non-zero)
            logger.info("\nTest 2: Medium Complexity Image")
            medium_img = Image.new('1', (320, 240), 1)
            draw = ImageDraw.Draw(medium_img)
            for y in range(20, 220, 20):
                draw.line([10, y, 310, y], fill=0, width=1)
            draw.text((50, 100), "MEDIUM TEST", fill=0)
            draw.rectangle([20, 20, 300, 220], outline=0, width=2)

            medium_data = self.image_to_printer_format(medium_img)
            if medium_data:
                speed, config = self.analyze_and_determine_speed(medium_data)
                test_results['results'].append({
                    'test': 'Medium Complexity',
                    'complexity': self.calculate_image_complexity(medium_data),
                    'speed': speed.value,
                    'description': config['description']
                })
                test_results['tests_run'] += 1
                test_results['successful_tests'] += 1

            # Test 3: Hohe Komplexitaet (> 12% non-zero)
            logger.info("\nTest 3: High Complexity Image")
            complex_img = Image.new('1', (320, 240), 1)
            draw = ImageDraw.Draw(complex_img)
            for x in range(0, 320, 10):
                draw.line([x, 0, x, 239], fill=0, width=1)
            for y in range(0, 240, 10):
                draw.line([0, y, 319, y], fill=0, width=1)
            for i in range(0, 300, 40):
                draw.rectangle([i, 50, i+20, 70], fill=0)
                draw.ellipse([i, 150, i+30, 180], fill=0)
            draw.text((10, 200), "VERY COMPLEX IMAGE TEST", fill=0)

            complex_data = self.image_to_printer_format(complex_img)
            if complex_data:
                speed, config = self.analyze_and_determine_speed(complex_data)
                test_results['results'].append({
                    'test': 'High Complexity',
                    'complexity': self.calculate_image_complexity(complex_data),
                    'speed': speed.value,
                    'description': config['description']
                })
                test_results['tests_run'] += 1
                test_results['successful_tests'] += 1

            # Test 4: Real problem image data (falls verfuegbar)
            try:
                problem_path = r'C:\Users\marcu\Downloads\problem_image_raw.bin'
                if os.path.exists(problem_path):
                    logger.info("\nTest 4: Real Problem Image Data")
                    with open(problem_path, 'rb') as f:
                        problem_data = f.read()

                    speed, config = self.analyze_and_determine_speed(problem_data)
                    test_results['results'].append({
                        'test': 'Real Problem Image',
                        'complexity': self.calculate_image_complexity(problem_data),
                        'speed': speed.value,
                        'description': config['description']
                    })
                    test_results['tests_run'] += 1
                    test_results['successful_tests'] += 1
                else:
                    logger.info("Test 4: Skipped (problem_image_raw.bin not found)")
            except Exception as e:
                logger.warning(f"Test 4 failed: {e}")

            # Zusammenfassung
            logger.info(f"\nADAPTIVE SPEED TEST SUMMARY:")
            logger.info(f"   Tests run: {test_results['tests_run']}")
            logger.info(f"   Successful: {test_results['successful_tests']}")

            for result in test_results['results']:
                logger.info(f"   {result['test']}: {result['complexity']*100:.1f}% complexity -> {result['speed']} ({result['description']})")

            return test_results

        except Exception as e:
            logger.error(f"Adaptive speed test error: {e}")
            return test_results

    def force_speed_test_print(self, complexity_level: str = 'medium') -> bool:
        """Forciert einen Testdruck mit bestimmter Komplexitaet"""
        try:
            logger.info(f"FORCE SPEED TEST: {complexity_level}")

            if complexity_level == 'simple':
                img = Image.new('1', (320, 240), 1)
                draw = ImageDraw.Draw(img)
                draw.text((100, 100), "SIMPLE TEST", fill=0)
                draw.line([160, 0, 160, 239], fill=0, width=2)
            elif complexity_level == 'complex':
                img = Image.new('1', (320, 240), 1)
                draw = ImageDraw.Draw(img)
                for x in range(0, 320, 8):
                    draw.line([x, 0, x, 239], fill=0, width=1)
                for y in range(0, 240, 8):
                    draw.line([0, y, 319, y], fill=0, width=1)
                draw.text((10, 100), "ULTRA COMPLEX", fill=0)
            else:  # medium
                img = Image.new('1', (320, 240), 1)
                draw = ImageDraw.Draw(img)
                draw.rectangle([10, 10, 310, 230], outline=0, width=3)
                draw.text((50, 100), "MEDIUM COMPLEXITY", fill=0)
                for y in range(50, 200, 20):
                    draw.line([30, y, 290, y], fill=0, width=1)

            if not self.is_connected():
                logger.error("Printer not connected")
                return False

            return self._print_image_direct(img)

        except Exception as e:
            logger.error(f"Force speed test error: {e}")
            return False
