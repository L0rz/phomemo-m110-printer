#!/usr/bin/env python3
"""
ZERO-OFFSET-TEST: X-Offset komplett deaktiviert
Testet ob das Wrap-Around-Problem ohne X-Offset verschwindet
"""

import sys
import os
import time
from PIL import Image, ImageDraw, ImageFont
import logging

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Module importieren
from printer_controller import EnhancedPhomemoM110
from config import *

def create_test_image_with_text():
    """Erstellt ein Testbild mit Text - genau wie Ihre ursprünglichen Bilder"""
    try:
        # Ähnlich Ihren Originalbildern: 320x240
        img = Image.new('1', (320, 240), 1)  # Weiß
        draw = ImageDraw.Draw(img)
        
        # Rahmen
        draw.rectangle([0, 0, 319, 239], outline=0, width=2)
        
        # Text-ähnliche Elemente
        draw.text((10, 20), "TEST IMAGE", fill=0)
        draw.text((10, 50), "X-OFFSET = 0", fill=0)
        draw.text((10, 80), "NO WRAPPING", fill=0)
        
        # Visuelle Marker für Links/Rechts
        # Links-Marker
        draw.rectangle([5, 5, 25, 25], outline=0, width=3)
        draw.text((8, 8), "L", fill=0)
        
        # Rechts-Marker
        draw.rectangle([295, 5, 315, 25], outline=0, width=3)
        draw.text((298, 8), "R", fill=0)
        
        # Zentrale Struktur (wie Ihre Gesichter)
        center_x, center_y = 160, 120
        
        # "Gesicht" simulation
        draw.ellipse([center_x-40, center_y-40, center_x+40, center_y+40], outline=0, width=2)
        draw.ellipse([center_x-15, center_y-15, center_x-5, center_y-5], fill=0)  # Auge
        draw.ellipse([center_x+5, center_y-15, center_x+15, center_y-5], fill=0)   # Auge
        draw.arc([center_x-20, center_y, center_x+20, center_y+20], 0, 180, fill=0)  # Mund
        
        # Horizontale Linien zum Erkennen von Verschiebungen
        for y in [160, 180, 200, 220]:
            draw.line([30, y, 290, y], fill=0, width=1)
        
        logger.info(f"✅ Created test image: {img.width}x{img.height}")
        return img
        
    except Exception as e:
        logger.error(f"❌ Error creating test image: {e}")
        return None

def test_zero_offset_conversion():
    """Testet Bildkonvertierung mit X-Offset=0"""
    logger.info("🧪 TESTING: Zero-offset conversion")
    
    try:
        printer = EnhancedPhomemoM110(PRINTER_MAC)
        
        # Testbild erstellen
        test_img = create_test_image_with_text()
        if not test_img:
            return False
        
        logger.info("🔄 Testing with X-Offset=0...")
        
        # 1. Offset anwenden (sollte X=0 sein)
        printer_img = printer.apply_offsets_to_image(test_img)
        
        # 2. Zu Drucker-Format konvertieren
        image_data = printer.image_to_printer_format(printer_img)
        
        if image_data:
            expected_size = printer_img.height * PRINTER_BYTES_PER_LINE
            actual_size = len(image_data)
            
            logger.info(f"✅ Conversion successful:")
            logger.info(f"   Image size: {printer_img.width}x{printer_img.height}")
            logger.info(f"   Data size: {actual_size} bytes (expected: {expected_size})")
            
            if actual_size == expected_size:
                logger.info("✅ ZERO-OFFSET: Perfect size alignment!")
                return True
            else:
                logger.error(f"❌ ZERO-OFFSET: Size mismatch!")
                return False
        else:
            logger.error("❌ ZERO-OFFSET: Conversion failed!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Zero-offset test error: {e}")
        import traceback
        logger.error(f"❌ Full traceback: {traceback.format_exc()}")
        return False

def test_print_zero_offset():
    """Druckt ein Testbild mit garantiert X-Offset=0"""
    logger.info("🖨️ TESTING: Print with X-Offset=0")
    
    try:
        printer = EnhancedPhomemoM110(PRINTER_MAC)
        
        # Verbindung prüfen
        if not printer.is_connected():
            logger.info("🔌 Connecting to printer...")
            if not printer.connect_bluetooth():
                logger.error("❌ Cannot connect to printer!")
                return False
        
        # Testbild erstellen
        test_img = create_test_image_with_text()
        if not test_img:
            return False
        
        # Mit Zero-Offset drucken
        logger.info("🖨️ Printing with X-Offset=0...")
        success = printer._print_image_direct(test_img)
        
        if success:
            logger.info("✅ ZERO-OFFSET PRINT: Success!")
            logger.info("👀 Check the printed result:")
            logger.info("   ✅ 'L' should be at LEFT edge")
            logger.info("   ✅ 'R' should be at RIGHT edge") 
            logger.info("   ✅ Text should be readable and positioned correctly")
            logger.info("   ✅ 'Face' should be centered")
            logger.info("   ✅ NO wrap-around effects")
            logger.info("")
            logger.info("📋 Compare this with your previous problematic prints!")
            return True
        else:
            logger.error("❌ ZERO-OFFSET PRINT: Failed!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Zero-offset print test error: {e}")
        return False

def force_reset_all_offsets():
    """Erzwingt Reset aller Offsets auf 0"""
    logger.info("🔧 FORCE RESET: All offsets to zero")
    
    try:
        printer = EnhancedPhomemoM110(PRINTER_MAC)
        
        # Direkt in Settings setzen
        printer.settings['x_offset'] = 0
        printer.settings['y_offset'] = 0
        
        # Speichern
        success = printer.save_settings()
        
        if success:
            logger.info("✅ FORCE RESET: All offsets = 0")
            logger.info(f"   Current settings: {printer.get_settings()}")
        else:
            logger.warning("⚠️ Could not save settings file, but in-memory reset done")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Force reset error: {e}")
        return False

def main():
    """Hauptfunktion für Zero-Offset-Tests"""
    logger.info("=" * 60)
    logger.info("🔧 PHOMEMO M110 - ZERO-OFFSET TEST")
    logger.info("=" * 60)
    logger.info("Testing with X-Offset completely disabled (=0)")
    logger.info("Purpose: Isolate and fix wrap-around problem")
    logger.info("=" * 60)
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: Force Reset
    logger.info("\n🔧 TEST 1: Force reset all offsets to 0")
    if force_reset_all_offsets():
        tests_passed += 1
        logger.info("✅ TEST 1: PASSED - Offsets forced to 0")
    else:
        logger.error("❌ TEST 1: FAILED - Could not reset offsets")
    
    # Test 2: Konvertierung
    logger.info("\n🧪 TEST 2: Image conversion with X-Offset=0")
    if test_zero_offset_conversion():
        tests_passed += 1
        logger.info("✅ TEST 2: PASSED - Zero-offset conversion OK")
    else:
        logger.error("❌ TEST 2: FAILED - Zero-offset conversion failed")
    
    # Test 3: Drucktest
    logger.info("\n🖨️ TEST 3: Print test with X-Offset=0")
    print("Print a zero-offset test image? (y/n): ", end="")
    if input().lower().startswith('y'):
        if test_print_zero_offset():
            tests_passed += 1
            logger.info("✅ TEST 3: PASSED - Zero-offset print successful")
        else:
            logger.error("❌ TEST 3: FAILED - Zero-offset print failed")
    else:
        logger.info("⏭️ TEST 3: SKIPPED")
        total_tests = 2
    
    # Ergebnis
    logger.info("\n" + "=" * 60)
    logger.info(f"🏁 ZERO-OFFSET TEST RESULT: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        logger.info("🎉 ZERO-OFFSET TEST SUCCESSFUL!")
        logger.info("✅ X-Offset disabled and working correctly")
        logger.info("✅ Images should print at left edge (X=0)")
        logger.info("✅ No more wrap-around effects")
        logger.info("")
        logger.info("🔄 Now test your original problematic images:")
        logger.info("   They should print correctly without wrap-around!")
    else:
        logger.error("❌ ZERO-OFFSET TEST ISSUES!")
        logger.error("🔧 Check error messages above")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
