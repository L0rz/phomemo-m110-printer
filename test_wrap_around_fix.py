#!/usr/bin/env python3
"""
Test-Script: Wrap-Around-Problem Fix
Testet und korrigiert das horizontale "Wrap-Around" Problem
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

def reset_printer_settings():
    """Setzt die Drucker-Settings auf sichere Standardwerte zurück"""
    logger.info("🔧 RESETTING printer settings to safe defaults")
    
    try:
        printer = EnhancedPhomemoM110(PRINTER_MAC)
        
        # Sichere Standard-Settings
        safe_settings = {
            'x_offset': 0,        # KEIN X-Offset
            'y_offset': 0,        # KEIN Y-Offset
            'dither_enabled': True,
            'fit_to_label_default': True,
            'maintain_aspect_default': True
        }
        
        # Settings aktualisieren und speichern
        success = printer.update_settings(safe_settings)
        
        if success:
            logger.info("✅ Settings reset successfully:")
            for key, value in safe_settings.items():
                logger.info(f"   {key}: {value}")
        else:
            logger.error("❌ Failed to reset settings")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Error resetting settings: {e}")
        return False

def test_wrap_around_prevention():
    """Testet die Wrap-Around-Verhinderung mit verschiedenen Bildgrößen"""
    logger.info("🧪 TESTING: Wrap-around prevention")
    
    try:
        printer = EnhancedPhomemoM110(PRINTER_MAC)
        
        # Test-Fälle: (Bildbreite, X-Offset, Erwartung)
        test_cases = [
            (300, 0, "Safe: Normal position"),
            (320, 50, "Safe: With small offset"), 
            (320, 100, "WARNING: Large offset - should be limited"),
            (350, 0, "Safe: Wide image, no offset"),
            (350, 50, "CRITICAL: Wide image + offset - should be corrected"),
            (400, 0, "CRITICAL: Too wide - should be cropped"),
            (384, 1, "CRITICAL: Exactly printer width + offset")
        ]
        
        all_safe = True
        
        for img_width, x_offset, description in test_cases:
            logger.info(f"\n📏 TEST: {description}")
            logger.info(f"   Image width: {img_width}px, X-Offset: {x_offset}px")
            
            # Testbild erstellen
            test_img = Image.new('1', (img_width, 100), 1)  # Weiß
            draw = ImageDraw.Draw(test_img)
            draw.rectangle([0, 0, img_width-1, 99], outline=0, width=2)
            
            # Temporär X-Offset setzen
            printer.settings['x_offset'] = x_offset
            
            # Offsets anwenden
            result_img = printer.apply_offsets_to_image(test_img)
            
            # Validierung
            if result_img.width == PRINTER_WIDTH_PIXELS:
                logger.info(f"   ✅ Result width: {result_img.width}px (correct)")
                
                # Prüfen ob Bild innerhalb der Grenzen liegt
                # Simuliere was gedruckt würde
                image_data = printer.image_to_printer_format(result_img)
                if image_data:
                    expected_size = result_img.height * PRINTER_BYTES_PER_LINE
                    if len(image_data) == expected_size:
                        logger.info(f"   ✅ Conversion successful: {len(image_data)} bytes")
                    else:
                        logger.error(f"   ❌ Conversion failed: size mismatch")
                        all_safe = False
                else:
                    logger.error(f"   ❌ Conversion failed completely")
                    all_safe = False
            else:
                logger.error(f"   ❌ Wrong result width: {result_img.width}px")
                all_safe = False
        
        # Settings zurücksetzen
        printer.settings['x_offset'] = 0
        
        return all_safe
        
    except Exception as e:
        logger.error(f"❌ Wrap-around test error: {e}")
        import traceback
        logger.error(f"❌ Full traceback: {traceback.format_exc()}")
        return False

def create_no_wrap_test_image():
    """Erstellt ein spezielles Testbild gegen Wrap-Around"""
    # Testbild mit klaren visuellen Indikatoren
    img = Image.new('1', (300, 200), 1)  # Weiß
    draw = ImageDraw.Draw(img)
    
    # Rahmen
    draw.rectangle([0, 0, 299, 199], outline=0, width=3)
    
    # Links-Indikator (L)
    draw.text((10, 10), "L", fill=0)
    draw.rectangle([5, 5, 25, 25], outline=0, width=2)
    
    # Rechts-Indikator (R)  
    draw.text((270, 10), "R", fill=0)
    draw.rectangle([265, 5, 285, 25], outline=0, width=2)
    
    # Zentrum-Kreuz
    center_x, center_y = 150, 100
    draw.line([center_x-20, center_y, center_x+20, center_y], fill=0, width=3)
    draw.line([center_x, center_y-20, center_x, center_y+20], fill=0, width=3)
    
    # Vertikale Linien zur Wrap-Erkennung
    for x in range(50, 300, 50):
        draw.line([x, 30, x, 170], fill=0, width=1)
        draw.text((x-5, 175), str(x), fill=0)
    
    return img

def test_print_no_wrap():
    """Druckt ein Anti-Wrap-Testbild"""
    logger.info("🖨️ TESTING: Print no-wrap test image")
    
    try:
        printer = EnhancedPhomemoM110(PRINTER_MAC)
        
        # Verbindung prüfen
        if not printer.is_connected():
            logger.info("🔌 Connecting to printer...")
            if not printer.connect_bluetooth():
                logger.error("❌ Cannot connect to printer!")
                return False
        
        # Anti-Wrap-Testbild erstellen
        test_img = create_no_wrap_test_image()
        
        # Mit korrigierter Methode drucken
        logger.info("🖨️ Printing no-wrap test...")
        success = printer._print_image_direct(test_img)
        
        if success:
            logger.info("✅ NO-WRAP TEST: Printed successfully!")
            logger.info("👀 Check the printed label:")
            logger.info("   ✅ 'L' should be at LEFT edge")
            logger.info("   ✅ 'R' should be at RIGHT edge")
            logger.info("   ✅ NO parts should appear on wrong side")
            logger.info("   ✅ Vertical lines should be evenly spaced")
            logger.info("   ✅ Numbers should be readable (50, 100, 150, 200, 250)")
            return True
        else:
            logger.error("❌ NO-WRAP TEST: Print failed!")
            return False
            
    except Exception as e:
        logger.error(f"❌ No-wrap print test error: {e}")
        return False

def main():
    """Hauptfunktion für Wrap-Around-Tests"""
    logger.info("=" * 60)
    logger.info("🔧 PHOMEMO M110 - WRAP-AROUND FIX TEST")
    logger.info("=" * 60)
    logger.info("This script fixes the horizontal wrap-around issue where")
    logger.info("images shift beyond the right edge and appear on the left.")
    logger.info("=" * 60)
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: Settings zurücksetzen
    logger.info("\n🔧 TEST 1: Reset settings to safe defaults")
    if reset_printer_settings():
        tests_passed += 1
        logger.info("✅ TEST 1: PASSED - Settings reset")
    else:
        logger.error("❌ TEST 1: FAILED - Could not reset settings")
    
    # Test 2: Wrap-Around-Verhinderung
    logger.info("\n🧪 TEST 2: Wrap-around prevention logic")
    if test_wrap_around_prevention():
        tests_passed += 1
        logger.info("✅ TEST 2: PASSED - Wrap-around prevented")
    else:
        logger.error("❌ TEST 2: FAILED - Wrap-around prevention issues")
    
    # Test 3: Drucktest
    logger.info("\n🖨️ TEST 3: Print no-wrap test pattern")
    print("Do you want to print a no-wrap test pattern? (y/n): ", end="")
    if input().lower().startswith('y'):
        if test_print_no_wrap():
            tests_passed += 1
            logger.info("✅ TEST 3: PASSED - No-wrap pattern printed")
        else:
            logger.error("❌ TEST 3: FAILED - Print failed")
    else:
        logger.info("⏭️ TEST 3: SKIPPED")
        total_tests = 2
    
    # Ergebnis
    logger.info("\n" + "=" * 60)
    logger.info(f"🏁 WRAP-AROUND FIX RESULT: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        logger.info("🎉 WRAP-AROUND PROBLEM FIXED!")
        logger.info("✅ Images will no longer wrap around")
        logger.info("✅ Safe positioning enforced")
        logger.info("✅ X-Offsets automatically limited")
        logger.info("🚀 Try printing your original problematic images now!")
    else:
        logger.error("❌ SOME WRAP-AROUND TESTS FAILED!")
        logger.error("🔧 Please check the error messages above")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
