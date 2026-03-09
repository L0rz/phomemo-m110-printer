#!/usr/bin/env python3
"""
DEEP DEBUG: Analysiert das echte Byte-Alignment Problem
Untersucht die image_to_printer_format Funktion auf Bit-Level
"""

import sys
import os
import time
from PIL import Image, ImageDraw
import logging

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Module importieren
from printer_controller import EnhancedPhomemoM110
from config import *

def create_simple_test_pattern():
    """Erstellt ein einfaches Testmuster für Bit-Level-Analyse"""
    # Einfaches Muster: Vertikale Linien alle 8 Pixel (= 1 Byte)
    img = Image.new('1', (320, 100), 1)  # Weiß
    draw = ImageDraw.Draw(img)
    
    # Vertikale Linien genau an Byte-Grenzen (alle 8 Pixel)
    for x in range(0, 320, 8):
        draw.line([x, 0, x, 99], fill=0, width=1)
        draw.text((x+1, 10), str(x), fill=0)
    
    # Horizontale Referenzlinien
    for y in range(20, 100, 20):
        draw.line([0, y, 319, y], fill=0, width=1)
    
    logger.info(f"Created simple test pattern: {img.width}x{img.height}")
    return img

def analyze_byte_conversion(img, printer):
    """Analysiert die Byte-Konvertierung auf Bit-Level"""
    logger.info("🔬 DEEP ANALYSIS: Byte conversion")
    
    try:
        # Original-Methode verwenden
        image_data = printer.image_to_printer_format(img)
        
        if not image_data:
            logger.error("❌ Conversion failed")
            return False
        
        width, height = img.size
        expected_size = height * PRINTER_BYTES_PER_LINE
        
        logger.info(f"📊 Conversion analysis:")
        logger.info(f"   Input image: {width}x{height}")
        logger.info(f"   Output data: {len(image_data)} bytes")
        logger.info(f"   Expected: {expected_size} bytes")
        logger.info(f"   Bytes per line: {PRINTER_BYTES_PER_LINE}")
        
        # Zeilen-für-Zeilen-Analyse
        logger.info("🔍 Line-by-line analysis (first 10 lines):")
        
        for line_num in range(min(10, height)):
            line_start = line_num * PRINTER_BYTES_PER_LINE
            line_end = line_start + PRINTER_BYTES_PER_LINE
            line_data = image_data[line_start:line_end]
            
            # Ersten und letzten Bytes der Zeile anzeigen
            if len(line_data) >= PRINTER_BYTES_PER_LINE:
                first_bytes = line_data[:4]
                last_bytes = line_data[-4:]
                
                logger.info(f"   Line {line_num:2d}: First 4 bytes: {[f'{b:02x}' for b in first_bytes]} | Last 4 bytes: {[f'{b:02x}' for b in last_bytes]}")
                
                # Prüfe ob Zeile nur Nullen enthält (sollte nicht bei Testmuster)
                if all(b == 0 for b in line_data):
                    logger.warning(f"   ⚠️ Line {line_num}: ALL ZEROS - potential problem!")
                
                # Prüfe auf unerwartete Muster
                non_zero_count = sum(1 for b in line_data if b != 0)
                logger.debug(f"   Line {line_num}: {non_zero_count}/{PRINTER_BYTES_PER_LINE} non-zero bytes")
            else:
                logger.error(f"   ❌ Line {line_num}: Wrong length {len(line_data)} (should be {PRINTER_BYTES_PER_LINE})")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Byte analysis error: {e}")
        return False

def debug_pixel_to_byte_conversion():
    """Debuggt die Pixel-zu-Byte-Konvertierung detailliert"""
    logger.info("🔬 DEBUGGING: Pixel-to-byte conversion")
    
    try:
        printer = EnhancedPhomemoM110(PRINTER_MAC)
        
        # Sehr einfaches Testbild: Nur erste 16 Pixel schwarz
        test_img = Image.new('1', (384, 3), 1)  # Weiß, 3 Zeilen hoch
        draw = ImageDraw.Draw(test_img)
        
        # Erste 16 Pixel der ersten Zeile schwarz machen
        draw.rectangle([0, 0, 15, 0], fill=0)  # Erste 16 Pixel = erste 2 Bytes
        
        # Zweite Zeile: Pixel 16-31 schwarz
        draw.rectangle([16, 1, 31, 1], fill=0)  # Pixel 16-31 = Bytes 2-3
        
        # Dritte Zeile: Pixel 32-47 schwarz  
        draw.rectangle([32, 2, 47, 2], fill=0)  # Pixel 32-47 = Bytes 4-5
        
        logger.info("🎯 Created precise test image:")
        logger.info("   Line 0: Pixels 0-15 black (should be bytes 0-1: 0xFF, 0xFF)")
        logger.info("   Line 1: Pixels 16-31 black (should be bytes 2-3: 0xFF, 0xFF)")
        logger.info("   Line 2: Pixels 32-47 black (should be bytes 4-5: 0xFF, 0xFF)")
        
        # Konvertierung analysieren
        image_data = printer.image_to_printer_format(test_img)
        
        if image_data:
            logger.info("🔍 Expected vs Actual byte patterns:")
            
            for line_num in range(3):
                line_start = line_num * PRINTER_BYTES_PER_LINE
                line_end = line_start + PRINTER_BYTES_PER_LINE
                line_bytes = image_data[line_start:line_end]
                
                # Erste 8 Bytes der Zeile zeigen
                first_8_bytes = line_bytes[:8]
                hex_repr = ' '.join(f'{b:02x}' for b in first_8_bytes)
                
                logger.info(f"   Line {line_num}: {hex_repr} ...")
                
                # Erwartete Muster prüfen
                if line_num == 0:
                    # Erste 2 Bytes sollten 0xFF sein
                    if first_8_bytes[0] == 0xFF and first_8_bytes[1] == 0xFF:
                        logger.info(f"     ✅ Line {line_num}: Correct pattern!")
                    else:
                        logger.error(f"     ❌ Line {line_num}: Wrong pattern! Expected 0xFF 0xFF at start")
                elif line_num == 1:
                    # Bytes 2-3 sollten 0xFF sein (da Pixel 16-31 in Byte 2-3 sind)
                    if first_8_bytes[2] == 0xFF and first_8_bytes[3] == 0xFF:
                        logger.info(f"     ✅ Line {line_num}: Correct pattern!")
                    else:
                        logger.error(f"     ❌ Line {line_num}: Wrong pattern! Expected 0xFF 0xFF at bytes 2-3")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Pixel-to-byte debug error: {e}")
        return False

def create_drift_detection_pattern():
    """Erstellt ein Muster speziell zur Drift-Erkennung"""
    img = Image.new('1', (320, 200), 1)  # Weiß
    draw = ImageDraw.Draw(img)
    
    # Jede Zeile: Schwarzes Pixel an Position 0, dann bei Position der Zeilennummer
    for y in range(200):
        # Referenz-Pixel links (sollte immer an Position 0 bleiben)
        draw.point((0, y), fill=0)
        
        # Test-Pixel: Position entspricht Zeilennummer modulo 320
        test_x = y % 320
        draw.point((test_x, y), fill=0)
        
        # Zusätzlich: Alle 20 Zeilen eine horizontale Linie zur Orientierung
        if y % 20 == 0:
            draw.line([0, y, 50, y], fill=0, width=1)
            draw.text((60, y), f"L{y}", fill=0)
    
    logger.info(f"Created drift detection pattern: {img.width}x{img.height}")
    return img

def test_drift_detection():
    """Testet mit einem speziellen Drift-Erkennungsmuster"""
    logger.info("🔍 TESTING: Drift detection with special pattern")
    
    try:
        printer = EnhancedPhomemoM110(PRINTER_MAC)
        
        # Drift-Erkennungsmuster erstellen
        test_img = create_drift_detection_pattern()
        
        # Konvertierung analysieren
        if analyze_byte_conversion(test_img, printer):
            logger.info("✅ Drift detection analysis completed")
            
            # Optional: Drucken für visuellen Test
            print("Print drift detection pattern? (y/n): ", end="")
            if input().lower().startswith('y'):
                if printer.is_connected() or printer.connect_bluetooth():
                    success = printer._print_image_direct(test_img)
                    if success:
                        logger.info("✅ Drift detection pattern printed!")
                        logger.info("👀 Check for:")
                        logger.info("   - Left reference pixels should stay aligned")
                        logger.info("   - Test pixels should follow diagonal pattern")
                        logger.info("   - Any horizontal shifts indicate byte alignment issues")
                    else:
                        logger.error("❌ Print failed")
                else:
                    logger.error("❌ Cannot connect to printer")
            
            return True
        else:
            return False
            
    except Exception as e:
        logger.error(f"❌ Drift detection test error: {e}")
        return False

def main():
    """Hauptfunktion für Deep-Debug"""
    logger.info("=" * 60)
    logger.info("🔬 PHOMEMO M110 - DEEP BYTE-LEVEL DEBUG")
    logger.info("=" * 60)
    logger.info("Analyzing the REAL cause of line shifts and drift")
    logger.info("Focus: Pixel-to-byte conversion in image_to_printer_format")
    logger.info("=" * 60)
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: Pixel-zu-Byte-Konvertierung
    logger.info("\n🔬 TEST 1: Pixel-to-byte conversion analysis")
    if debug_pixel_to_byte_conversion():
        tests_passed += 1
        logger.info("✅ TEST 1: PASSED - Pixel-to-byte analysis completed")
    else:
        logger.error("❌ TEST 1: FAILED - Pixel-to-byte analysis failed")
    
    # Test 2: Einfaches Testmuster
    logger.info("\n🔬 TEST 2: Simple test pattern analysis")
    try:
        printer = EnhancedPhomemoM110(PRINTER_MAC)
        simple_pattern = create_simple_test_pattern()
        if analyze_byte_conversion(simple_pattern, printer):
            tests_passed += 1
            logger.info("✅ TEST 2: PASSED - Simple pattern analysis completed")
        else:
            logger.error("❌ TEST 2: FAILED - Simple pattern analysis failed")
    except Exception as e:
        logger.error(f"❌ TEST 2: ERROR - {e}")
    
    # Test 3: Drift-Erkennungsmuster
    logger.info("\n🔍 TEST 3: Drift detection pattern")
    if test_drift_detection():
        tests_passed += 1
        logger.info("✅ TEST 3: PASSED - Drift detection completed")
    else:
        logger.error("❌ TEST 3: FAILED - Drift detection failed")
    
    # Ergebnis
    logger.info("\n" + "=" * 60)
    logger.info(f"🏁 DEEP DEBUG RESULT: {tests_passed}/{total_tests} tests completed")
    
    if tests_passed >= 2:
        logger.info("🔍 DEEP ANALYSIS COMPLETED!")
        logger.info("📊 Check the byte-level analysis above for:")
        logger.info("   • Incorrect byte patterns")
        logger.info("   • Line length mismatches") 
        logger.info("   • Pixel-to-bit conversion errors")
        logger.info("🔧 The real problem is likely in image_to_printer_format!")
    else:
        logger.error("❌ DEEP ANALYSIS INCOMPLETE!")
        logger.error("🔧 Multiple analysis failures - check error messages")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
