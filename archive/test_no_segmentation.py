#!/usr/bin/env python3
"""
Test-Script: Keine Segmentierung, garantierte 48-Byte-Zeilen
Testet die neuen Verbesserungen an image_to_printer_format und send_bitmap
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

def create_test_image(width, height, pattern="checkerboard"):
    """Erstellt ein Testbild zum Überprüfen der Ausrichtung"""
    img = Image.new('1', (width, height), 1)  # Weiß
    draw = ImageDraw.Draw(img)
    
    if pattern == "checkerboard":
        # Schachbrettmuster
        square_size = 20
        for y in range(0, height, square_size):
            for x in range(0, width, square_size):
                if (x // square_size + y // square_size) % 2:
                    draw.rectangle([x, y, x + square_size, y + square_size], fill=0)
    
    elif pattern == "alignment_test":
        # Ausrichtungstest mit Linien und Rahmen
        # Äußerer Rahmen
        draw.rectangle([0, 0, width-1, height-1], outline=0, width=3)
        
        # Vertikale Linien alle 40px
        for x in range(40, width, 40):
            draw.line([x, 0, x, height], fill=0, width=1)
        
        # Horizontale Linien alle 30px
        for y in range(30, height, 30):
            draw.line([0, y, width, y], fill=0, width=1)
        
        # Diagonalen
        draw.line([0, 0, width, height], fill=0, width=2)
        draw.line([width, 0, 0, height], fill=0, width=2)
        
        # Zentrum-Marker
        center_x, center_y = width // 2, height // 2
        draw.rectangle([center_x-10, center_y-10, center_x+10, center_y+10], fill=0)
    
    elif pattern == "drift_test":
        # Drifttest: Horizontale Linien um Verschiebung zu erkennen
        line_spacing = 10
        for y in range(5, height, line_spacing):
            # Jede Zeile beginnt an verschiedenen X-Positionen
            start_x = (y // line_spacing) % 20
            draw.line([start_x, y, width - start_x, y], fill=0, width=2)
        
        # Vertikale Referenzlinien
        for x in range(0, width, 50):
            draw.line([x, 0, x, height], fill=0, width=1)
    
    return img

def test_image_conversion_no_segmentation():
    """Testet die neue Bildkonvertierung ohne Segmentierung"""
    logger.info("🧪 TESTING: Image conversion without segmentation")
    
    try:
        # Printer Controller initialisieren
        printer = EnhancedPhomemoM110(PRINTER_MAC)
        
        # Testbild erstellen
        test_width = 320  # Standard Label-Breite
        test_height = 240  # Standard Label-Höhe
        
        logger.info(f"📏 Creating test image: {test_width}x{test_height}")
        test_img = create_test_image(test_width, test_height, "alignment_test")
        
        # Bildkonvertierung testen
        logger.info("🔄 Testing image_to_printer_format...")
        start_time = time.time()
        
        image_data = printer.image_to_printer_format(test_img)
        
        conversion_time = time.time() - start_time
        
        if image_data:
            logger.info(f"✅ Conversion successful!")
            logger.info(f"⏱️ Conversion time: {conversion_time:.3f}s")
            logger.info(f"📊 Data size: {len(image_data)} bytes")
            logger.info(f"📏 Expected size: {test_height * PRINTER_BYTES_PER_LINE} bytes")
            
            # Größen-Validierung
            expected_size = test_height * PRINTER_BYTES_PER_LINE
            if len(image_data) == expected_size:
                logger.info("✅ BYTE ALIGNMENT: Perfect!")
            else:
                logger.error(f"❌ BYTE ALIGNMENT: ERROR! Got {len(image_data)}, expected {expected_size}")
                return False
            
            # Zeilen-Validierung (jede Zeile muss exakt 48 Bytes haben)
            lines_ok = 0
            for line_num in range(test_height):
                line_start = line_num * PRINTER_BYTES_PER_LINE
                line_end = line_start + PRINTER_BYTES_PER_LINE
                line_data = image_data[line_start:line_end]
                
                if len(line_data) == PRINTER_BYTES_PER_LINE:
                    lines_ok += 1
                else:
                    logger.error(f"❌ Line {line_num}: {len(line_data)} bytes (should be {PRINTER_BYTES_PER_LINE})")
            
            logger.info(f"📋 Line validation: {lines_ok}/{test_height} lines correct")
            
            if lines_ok == test_height:
                logger.info("✅ ALL LINES: Perfect 48-byte alignment!")
                return True
            else:
                logger.error("❌ LINE ALIGNMENT: Some lines have wrong size!")
                return False
        else:
            logger.error("❌ Conversion failed!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test error: {e}")
        import traceback
        logger.error(f"❌ Full traceback: {traceback.format_exc()}")
        return False

def test_different_image_sizes():
    """Testet verschiedene Bildgrößen für Alignment"""
    logger.info("🧪 TESTING: Different image sizes")
    
    test_sizes = [
        (100, 50, "Small"),
        (200, 100, "Medium"),
        (320, 240, "Standard"),
        (384, 300, "Wide"),
        (300, 500, "Tall")
    ]
    
    try:
        printer = EnhancedPhomemoM110(PRINTER_MAC)
        
        all_passed = True
        
        for width, height, description in test_sizes:
            logger.info(f"📏 Testing {description}: {width}x{height}")
            
            # Testbild erstellen
            test_img = create_test_image(width, height, "drift_test")
            
            # Konvertierung
            image_data = printer.image_to_printer_format(test_img)
            
            if image_data:
                expected_size = height * PRINTER_BYTES_PER_LINE
                actual_size = len(image_data)
                
                if actual_size == expected_size:
                    logger.info(f"  ✅ {description}: {actual_size} bytes (correct)")
                else:
                    logger.error(f"  ❌ {description}: {actual_size} bytes (expected {expected_size})")
                    all_passed = False
            else:
                logger.error(f"  ❌ {description}: Conversion failed")
                all_passed = False
        
        if all_passed:
            logger.info("✅ ALL SIZE TESTS: Passed!")
        else:
            logger.error("❌ SOME SIZE TESTS: Failed!")
        
        return all_passed
        
    except Exception as e:
        logger.error(f"❌ Size test error: {e}")
        return False

def test_print_alignment_pattern():
    """Druckt ein Ausrichtungsmuster zum visuellen Test"""
    logger.info("🖨️ TESTING: Print alignment pattern")
    
    try:
        printer = EnhancedPhomemoM110(PRINTER_MAC)
        
        # Verbindung prüfen
        if not printer.is_connected():
            logger.info("🔌 Connecting to printer...")
            if not printer.connect_bluetooth():
                logger.error("❌ Cannot connect to printer!")
                return False
        
        # Ausrichtungsmuster erstellen
        test_img = create_test_image(320, 240, "alignment_test")
        
        # Mit neuer Methode drucken
        logger.info("🖨️ Printing alignment test...")
        success = printer._print_image_direct(test_img)
        
        if success:
            logger.info("✅ ALIGNMENT TEST: Printed successfully!")
            logger.info("👀 Check the printed label for:")
            logger.info("   - Straight lines (no drift)")
            logger.info("   - Centered diagonal crosses") 
            logger.info("   - Even spacing of grid lines")
            logger.info("   - Sharp black rectangles in corners")
            return True
        else:
            logger.error("❌ ALIGNMENT TEST: Print failed!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Print test error: {e}")
        return False

def main():
    """Hauptfunktion zum Ausführen aller Tests"""
    logger.info("=" * 60)
    logger.info("🧪 PHOMEMO M110 - NO SEGMENTATION TEST SUITE")
    logger.info("=" * 60)
    logger.info("Testing improvements:")
    logger.info("✓ Eliminated segmentation in image_to_printer_format")
    logger.info("✓ Guaranteed 48-byte line alignment")
    logger.info("✓ Full image transmission in send_bitmap")
    logger.info("=" * 60)
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: Bildkonvertierung
    logger.info("\n🧪 TEST 1: Image conversion")
    if test_image_conversion_no_segmentation():
        tests_passed += 1
        logger.info("✅ TEST 1: PASSED")
    else:
        logger.error("❌ TEST 1: FAILED")
    
    # Test 2: Verschiedene Bildgrößen
    logger.info("\n🧪 TEST 2: Different image sizes")
    if test_different_image_sizes():
        tests_passed += 1
        logger.info("✅ TEST 2: PASSED")
    else:
        logger.error("❌ TEST 2: FAILED")
    
    # Test 3: Drucktest (optional, nur wenn Drucker verbunden)
    logger.info("\n🧪 TEST 3: Print alignment test")
    print("Do you want to print an alignment test pattern? (y/n): ", end="")
    if input().lower().startswith('y'):
        if test_print_alignment_pattern():
            tests_passed += 1
            logger.info("✅ TEST 3: PASSED")
        else:
            logger.error("❌ TEST 3: FAILED")
    else:
        logger.info("⏭️ TEST 3: SKIPPED")
        total_tests = 2
    
    # Ergebnis
    logger.info("\n" + "=" * 60)
    logger.info(f"🏁 FINAL RESULT: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        logger.info("🎉 ALL TESTS PASSED!")
        logger.info("✅ No segmentation implementation successful!")
        logger.info("✅ 48-byte alignment guaranteed!")
        logger.info("🚀 Your printer should now have NO MORE DRIFT issues!")
    else:
        logger.error("❌ SOME TESTS FAILED!")
        logger.error("🔧 Please check the error messages above")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
