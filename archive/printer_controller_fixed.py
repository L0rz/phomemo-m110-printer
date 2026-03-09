#!/usr/bin/env python3
"""
FIXED: Phomemo M110 Printer Controller mit EXAKTER Knightro63/vivier Bitmap-Übertragung

KRITISCHE ÄNDERUNGEN basierend auf Knightro63 Flutter Library & vivier/phomemo-tools:
1. Bit-Order: MSB first (Most Significant Bit first)
2. Pixel-Mapping: 0 = weiß, 1 = schwarz (invertiert!)
3. Exakte ESC/POS Kommandos wie in funktionierenden Implementierungen
"""

import os
import time
import logging
from typing import Optional
from PIL import Image
import io

# Importiere die Original-Klasse
import sys
sys.path.insert(0, os.path.dirname(__file__))
from printer_controller import EnhancedPhomemoM110

logger = logging.getLogger(__name__)

class FixedPhomemoM110(EnhancedPhomemoM110):
    """
    Erweitert EnhancedPhomemoM110 mit korrigierter Bitmap-Konvertierung
    basierend auf Knightro63/vivier phomemo-tools
    """
    
    def image_to_printer_format(self, img):
        """
        FIXED: Bitmap-Konvertierung mit EXAKTER vivier/Knightro63 Logik
        
        KRITISCHE UNTERSCHIEDE zur alten Version:
        1. Pixel-Wert-Invertierung: PIL '1' mode hat 0=schwarz, 1=weiß
           Aber Drucker erwartet: bit 1 = schwarz, bit 0 = weiß
        2. Bit-Order: MSB first (wie in vivier/phomemo-tools)
        3. Kein Resizing - Bild muss bereits 384px breit sein
        """
        try:
            # Bild zu Schwarz-Weiß konvertieren
            if img.mode != '1':
                img = img.convert('1')
            
            width, height = img.size
            
            logger.info(f"🔧 FIXED CONVERSION: {width}x{height} -> printer format")
            
            # KRITISCH: Breite MUSS 384 Pixel sein
            if width != self.width_pixels:
                logger.error(f"❌ CRITICAL: Image must be exactly {self.width_pixels}px wide, got {width}px")
                logger.error(f"   Bild muss VOR dieser Funktion auf {self.width_pixels}px skaliert werden!")
                return None
            
            # Pixel-Daten holen
            pixels = list(img.getdata())
            
            # VIVIER/KNIGHTRO63 EXAKTE IMPLEMENTIERUNG
            # Quelle: vivier/phomemo-tools & Knightro63/phomemo
            image_bytes = []
            
            for y in range(height):
                # Neue Zeile: Exakt 48 Bytes (384 pixels / 8 bits)
                line_bytes = bytearray(self.bytes_per_line)
                
                # Verarbeite 384 Pixel dieser Zeile
                for x in range(self.width_pixels):
                    pixel_idx = y * width + x
                    
                    # Hole Pixel-Wert
                    if pixel_idx < len(pixels):
                        # PIL '1' mode: 0 = schwarz, 255 = weiß
                        pixel_value = pixels[pixel_idx]
                    else:
                        pixel_value = 255  # Weiß als Fallback
                    
                    # *** KRITISCHER FIX 1: Pixel-Invertierung ***
                    # PIL: 0 = schwarz, 255 = weiß
                    # Drucker bit: 1 = schwarz, 0 = weiß
                    # Also: pixel_value == 0 → bit = 1 (schwarz drucken)
                    is_black = (pixel_value == 0)
                    
                    # Byte- und Bit-Position berechnen
                    byte_idx = x // 8
                    bit_idx = x % 8
                    
                    # *** KRITISCHER FIX 2: MSB First (wie vivier) ***
                    # Setze Bit von links nach rechts (MSB first)
                    if is_black:
                        line_bytes[byte_idx] |= (1 << (7 - bit_idx))
                
                # Zeile zu Gesamtbild hinzufügen
                image_bytes.extend(line_bytes)
            
            # Zu bytes konvertieren
            final_bytes = bytes(image_bytes)
            expected_size = height * self.bytes_per_line
            
            # Strenge Validierung
            if len(final_bytes) != expected_size:
                logger.error(f"❌ Size mismatch: {len(final_bytes)} != {expected_size}")
                return None
            
            logger.info(f"✅ FIXED CONVERSION SUCCESS: {len(final_bytes)} bytes")
            logger.info(f"   Pixel-Mapping: 0=schwarz → bit 1, 255=weiß → bit 0")
            logger.info(f"   Bit-Order: MSB first (7→0)")
            
            return final_bytes
            
        except Exception as e:
            logger.error(f"❌ Fixed conversion error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def send_bitmap(self, image_data: bytes, height: int) -> bool:
        """
        FIXED: Bitmap-Übertragung mit EXAKTEN vivier/Knightro63 ESC/POS Kommandos
        
        Basiert auf:
        - vivier/phomemo-tools: rastertopm110.c
        - Knightro63/phomemo: printLabel Methode
        """
        try:
            width_bytes = self.bytes_per_line  # 48 Bytes
            
            logger.info(f"📤 FIXED BITMAP SEND: {len(image_data)} bytes, {height} lines")
            
            # Validierung
            expected_size = height * width_bytes
            if len(image_data) != expected_size:
                logger.error(f"❌ Data size error: {len(image_data)} != {expected_size}")
                return False
            
            # Anti-Drift: Mindestabstand
            if hasattr(self, 'last_print_time'):
                time_since_last = time.time() - self.last_print_time
                if time_since_last < 0.2:
                    time.sleep(0.2 - time_since_last)
            
            # *** SCHRITT 1: Drucker Reset (vivier ESC @) ***
            logger.info("🔄 Step 1: Initialize printer (ESC @)")
            if not self.send_command(b'\x1b\x40'):  # ESC @ - Reset
                logger.error("❌ Failed to send ESC @")
                return False
            time.sleep(0.05)  # 50ms wie in vivier
            
            # *** SCHRITT 2: Raster Bitmap Mode (vivier GS v 0) ***
            logger.info("🔄 Step 2: Enter raster bitmap mode (GS v 0)")
            
            # GS v 0 m xL xH yL yH [data]
            # m = 0 (Normal mode, no double width/height)
            # xL xH = width in bytes (little endian)
            # yL yH = height in dots (little endian)
            
            m = 0  # Normal mode (wie in vivier)
            
            # Width in bytes (little endian)
            xL = width_bytes & 0xFF
            xH = (width_bytes >> 8) & 0xFF
            
            # Height in dots (little endian)  
            yL = height & 0xFF
            yH = (height >> 8) & 0xFF
            
            # Header zusammensetzen (EXAKT wie vivier)
            header = bytes([
                0x1D,  # GS
                0x76,  # v
                0x30,  # 0
                m,     # Mode
                xL, xH,  # Width in bytes
                yL, yH   # Height in lines
            ])
            
            logger.info(f"   Header: GS v 0 {m} {xL} {xH} {yL} {yH}")
            logger.info(f"   = 0x1D 0x76 0x30 0x{m:02X} 0x{xL:02X} 0x{xH:02X} 0x{yL:02X} 0x{yH:02X}")
            
            if not self.send_command(header):
                logger.error("❌ Failed to send GS v 0 header")
                return False
            time.sleep(0.02)  # 20ms Header-Delay
            
            # *** SCHRITT 3: Bilddaten senden ***
            logger.info("🔄 Step 3: Send image data")
            
            # Adaptive Speed basierend auf Komplexität
            speed, timing_config = self.analyze_and_determine_speed(image_data)
            logger.info(f"   Using {timing_config['description']}")
            
            # Block-Übertragung
            BLOCK_SIZE = 960  # 20 Zeilen (wie in vivier - konservativ)
            blocks_sent = 0
            total_blocks = (len(image_data) + BLOCK_SIZE - 1) // BLOCK_SIZE
            
            for i in range(0, len(image_data), BLOCK_SIZE):
                block = image_data[i:i + BLOCK_SIZE]
                blocks_sent += 1
                
                logger.debug(f"   Sending block {blocks_sent}/{total_blocks}: {len(block)} bytes")
                
                if not self.send_command(block):
                    logger.error(f"❌ Block {blocks_sent} failed")
                    return False
                
                # Adaptive Pause zwischen Blöcken
                if i + BLOCK_SIZE < len(image_data):
                    time.sleep(timing_config['block_delay'])
            
            # *** SCHRITT 4: Abschluss ***
            time.sleep(0.1)  # Post-processing
            self.last_print_time = time.time()
            
            logger.info(f"✅ FIXED BITMAP SENT SUCCESSFULLY")
            logger.info(f"   Total blocks: {blocks_sent}")
            logger.info(f"   Speed used: {speed.value}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Fixed bitmap send error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def print_test_pattern(self) -> bool:
        """
        Druckt ein einfaches Testmuster um die Konvertierung zu verifizieren
        """
        try:
            logger.info("🧪 PRINTING TEST PATTERN")
            
            # Einfaches Testbild: Vertikale Streifen
            # Links schwarz, Mitte weiß, rechts schwarz
            width = self.width_pixels
            height = 100
            
            img = Image.new('1', (width, height), 1)  # Weiß
            
            # Linker schwarzer Streifen (0-128px)
            for y in range(height):
                for x in range(128):
                    img.putpixel((x, y), 0)  # Schwarz
            
            # Rechter schwarzer Streifen (256-384px)
            for y in range(height):
                for x in range(256, width):
                    img.putpixel((x, y), 0)  # Schwarz
            
            # Horizontale Linie in der Mitte
            for x in range(width):
                img.putpixel((x, height // 2), 0)  # Schwarz
            
            logger.info(f"   Test pattern: {width}x{height}")
            logger.info(f"   Left strip: BLACK (0-128px)")
            logger.info(f"   Middle: WHITE (128-256px)")
            logger.info(f"   Right strip: BLACK (256-384px)")
            logger.info(f"   Horizontal line: BLACK at y={height//2}")
            
            # Offsets anwenden
            final_img = self.apply_offsets_to_image(img)
            
            # Konvertieren und drucken
            image_data = self.image_to_printer_format(final_img)
            if not image_data:
                logger.error("❌ Failed to convert test pattern")
                return False
            
            success = self.send_bitmap(image_data, final_img.height)
            if success:
                logger.info("✅ Test pattern printed!")
            else:
                logger.error("❌ Test pattern print failed")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Test pattern error: {e}")
            return False


# Test-Funktion
def test_fixed_conversion():
    """Testet die korrigierte Konvertierung"""
    logger.info("=" * 80)
    logger.info("TESTING FIXED BITMAP CONVERSION")
    logger.info("=" * 80)
    
    # Mock-Drucker für Test
    class MockPrinter:
        def __init__(self):
            self.width_pixels = 384
            self.bytes_per_line = 48
    
    printer = MockPrinter()
    
    # Test 1: Einfaches Bild - linke Hälfte schwarz, rechte weiß
    logger.info("\n🧪 Test 1: Half black, half white")
    img1 = Image.new('1', (384, 100), 1)  # Weiß
    for y in range(100):
        for x in range(192):  # Linke Hälfte
            img1.putpixel((x, y), 0)  # Schwarz
    
    # Konvertiere mit Fixed-Methode
    fixed = FixedPhomemoM110.__new__(FixedPhomemoM110)
    fixed.width_pixels = 384
    fixed.bytes_per_line = 48
    
    data = fixed.image_to_printer_format(img1)
    if data:
        logger.info(f"✅ Test 1 passed: {len(data)} bytes generated")
        
        # Verifiziere erstes Byte der ersten Zeile
        # Erste 8 Pixel sind schwarz → sollte 0xFF sein (alle bits 1)
        first_byte = data[0]
        logger.info(f"   First byte: 0x{first_byte:02X} (expected: 0xFF for 8 black pixels)")
        
        # Byte an Position 24 (Mitte der Zeile) sollte 0x00 sein (8 weiße Pixel)
        mid_byte = data[24]
        logger.info(f"   Mid byte (pos 24): 0x{mid_byte:02X} (expected: 0x00 for 8 white pixels)")
    else:
        logger.error("❌ Test 1 failed")
    
    logger.info("\n" + "=" * 80)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    test_fixed_conversion()
