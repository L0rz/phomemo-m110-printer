#!/usr/bin/env python3
"""
PRECISION TEST: 10mm/80-Zeilen-Problem isolieren
Testet warum nach genau 80 Zeilen eine 2mm Verschiebung auftritt
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

def create_80_line_test_pattern():
    """Erstellt ein Testmuster speziell für 80-Zeilen-Analyse"""
    # 320x160 = 80 Zeilen bei 203 DPI ≈ 10mm
    width, height = 320, 160
    
    img = Image.new('1', (width, height), 1)  # Weiß
    draw = ImageDraw.Draw(img)
    
    # Vertikale Referenzlinien (sollten immer gerade bleiben)
    for x in range(0, width, 40):  # Alle 40 Pixel
        draw.line([x, 0, x, height-1], fill=0, width=1)
        draw.text((x+2, 5), str(x), fill=0)
    
    # Horizontale Markierungen alle 10 Zeilen
    for y in range(0, height, 10):
        draw.line([0, y, 50, y], fill=0, width=1)
        draw.text((55, y-5), f"L{y}", fill=0)
    
    # KRITISCHE 80-Zeilen-Markierung
    if height >= 80:
        draw.line([0, 79, width-1, 79], fill=0, width=3)  # Dicke Linie bei Zeile 80
        draw.text((60, 75), "LINE 80!", fill=0)
    
    # Links-Rechts-Indikatoren in jeder 20. Zeile
    for y in range(0, height, 20):
        # Links-Markierung
        draw.rectangle([0, y, 10, y+5], fill=0)
        draw.text((12, y), "L", fill=0)
        
        # Rechts-Markierung  
        draw.rectangle([width-11, y, width-1, y+5], fill=0)
        draw.text((width-20, y), "R", fill=0)
    
    logger.info(f"✅ Created 80-line test pattern: {width}x{height}")
    logger.info(f"   Pattern designed to detect shift at line 80 (10mm)")
    
    return img

def create_line_by_line_analysis_pattern():
    """Erstellt ein Muster zur Zeile-für-Zeile-Analyse"""
    width, height = 200, 100  # Kleineres Testbild
    
    img = Image.new('1', (width, height), 1)  # Weiß
    draw = ImageDraw.Draw(img)
    
    # Jede Zeile hat einen schwarzen Pixel an Position = Zeilennummer
    for y in range(height):
        x = y % width  # Zyklischer X-Wert
        draw.point((x, y), fill=0)
        
        # Zusätzlich: Jede 10. Zeile vollständig markieren
        if y % 10 == 0:
            draw.line([0, y, width-1, y], fill=0, width=1)
            draw.text((width-30, y-8), f"{y}", fill=0)
    
    logger.info(f"✅ Created line-by-line analysis pattern: {width}x{height}")
    
    return img

def test_bypass_all_processing():
    """Testet mit komplett ausgeschaltetem Offset-System"""
    logger.info("🔧 TESTING: Complete bypass of offset processing")
    
    try:
        printer = EnhancedPhomemoM110(PRINTER_MAC)
        
        # Verbindung prüfen
        if not printer.is_connected():
            logger.info("🔌 Connecting to printer...")
            if not printer.connect_bluetooth():
                logger.error("❌ Cannot connect to printer!")
                return False
        
        # 80-Zeilen-Testmuster
        test_img = create_80_line_test_pattern()
        
        logger.info("🔧 Testing with BYPASSED offset processing...")
        logger.info("   apply_offsets_to_image is now DEACTIVATED")
        logger.info("   Image will be processed 1:1 without any modifications")
        
        # Mit deaktiviertem Offset-System drucken
        success = printer._print_image_direct(test_img)
        
        if success:
            logger.info("✅ BYPASS TEST: Printed successfully!")
            logger.info("👀 Check the result carefully:")
            logger.info("   ✅ Vertical lines should be PERFECTLY straight")
            logger.info("   ✅ L/R markers should stay aligned")
            logger.info("   ❌ ANY shift at line 80 means problem is in image_to_printer_format")
            logger.info("   ❌ NO shift means problem WAS in offset system")
            return True
        else:
            logger.error("❌ BYPASS TEST: Print failed!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Bypass test error: {e}")
        return False

def test_raw_data_analysis():
    """Analysiert die rohen Bilddaten um das Problem zu finden"""
    logger.info("🔬 TESTING: Raw data analysis")
    
    try:
        printer = EnhancedPhomemoM110(PRINTER_MAC)
        
        # Einfaches Testbild für Datenanalyse
        test_img = create_line_by_line_analysis_pattern()
        
        # 1. Durch apply_offsets_to_image (jetzt bypassed)
        processed_img = printer.apply_offsets_to_image(test_img)
        logger.info(f"   After apply_offsets: {processed_img.width}x{processed_img.height}")
        
        # 2. Durch image_to_printer_format
        raw_data = printer.image_to_printer_format(processed_img)
        
        if raw_data:
            logger.info(f"   Raw data size: {len(raw_data)} bytes")
            
            # Analysiere erste und letzte Zeilen
            height = processed_img.height
            bytes_per_line = PRINTER_BYTES_PER_LINE
            
            logger.info("🔍 Raw data analysis:")
            
            # Erste 5 Zeilen
            logger.info("   First 5 lines:")
            for line_num in range(min(5, height)):
                line_start = line_num * bytes_per_line
                line_end = line_start + bytes_per_line
                line_data = raw_data[line_start:line_end]
                
                # Ersten 8 Bytes zeigen
                hex_preview = ' '.join(f'{b:02x}' for b in line_data[:8])
                non_zero = sum(1 for b in line_data if b != 0)
                logger.info(f"     Line {line_num}: {hex_preview}... ({non_zero} non-zero bytes)")
            
            # Zeilen um 80 herum (falls vorhanden)
            if height >= 85:
                logger.info("   Lines around 80:")
                for line_num in range(75, min(85, height)):
                    line_start = line_num * bytes_per_line
                    line_end = line_start + bytes_per_line
                    line_data = raw_data[line_start:line_end]
                    
                    hex_preview = ' '.join(f'{b:02x}' for b in line_data[:8])
                    non_zero = sum(1 for b in line_data if b != 0)
                    marker = " ⚠️ CRITICAL LINE!" if line_num == 80 else ""
                    logger.info(f"     Line {line_num}: {hex_preview}... ({non_zero} non-zero bytes){marker}")
            
            return True
        else:
            logger.error("❌ Raw data conversion failed!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Raw data analysis error: {e}")
        return False

def test_step_by_step_processing():
    """Testet jeden Verarbeitungsschritt einzeln"""
    logger.info("📋 TESTING: Step-by-step processing analysis")
    
    try:
        printer = EnhancedPhomemoM110(PRINTER_MAC)
        
        # Sehr kleines Testbild
        original_img = Image.new('1', (100, 50), 1)  # Weiß
        draw = ImageDraw.Draw(original_img)
        
        # Einfaches Muster
        draw.rectangle([0, 0, 99, 49], outline=0, width=2)
        draw.line([0, 0, 99, 49], fill=0, width=1)
        draw.line([99, 0, 0, 49], fill=0, width=1)
        
        logger.info("📋 Step-by-step analysis:")
        logger.info(f"   1. Original image: {original_img.width}x{original_img.height}")
        
        # Schritt 1: apply_offsets_to_image
        step1_img = printer.apply_offsets_to_image(original_img)
        logger.info(f"   2. After apply_offsets: {step1_img.width}x{step1_img.height}")
        
        # Schritt 2: image_to_printer_format
        step2_data = printer.image_to_printer_format(step1_img)
        if step2_data:
            expected_size = step1_img.height * PRINTER_BYTES_PER_LINE
            logger.info(f"   3. After conversion: {len(step2_data)} bytes (expected: {expected_size})")
            
            if len(step2_data) == expected_size:
                logger.info("   ✅ Size validation: PASSED")
                
                # Optional: Drucken
                print("Print step-by-step test? (y/n): ", end="")
                if input().lower().startswith('y'):
                    if printer.is_connected() or printer.connect_bluetooth():
                        success = printer.send_bitmap(step2_data, step1_img.height)
                        if success:
                            logger.info("✅ Step-by-step test printed!")
                        else:
                            logger.error("❌ Print failed")
                
                return True
            else:
                logger.error("   ❌ Size validation: FAILED")
                return False
        else:
            logger.error("   ❌ Conversion failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Step-by-step test error: {e}")
        return False

def main():
    """Hauptfunktion für 80-Zeilen-Problem-Analyse"""
    logger.info("=" * 60)
    logger.info("🎯 PHOMEMO M110 - 80-LINE SHIFT PROBLEM ANALYSIS")
    logger.info("=" * 60)
    logger.info("Problem: After 10mm (80 lines) → 2mm right shift")
    logger.info("Strategy: Isolate exact cause with bypassed offset system")
    logger.info("=" * 60)
    
    tests_completed = 0
    
    # Test 1: Komplett ausgeschaltete Verarbeitung
    logger.info("\n🔧 TEST 1: Complete bypass test")
    print("Run bypass test (offset processing DISABLED)? (y/n): ", end="")
    if input().lower().startswith('y'):
        if test_bypass_all_processing():
            logger.info("✅ TEST 1: COMPLETED")
        else:
            logger.error("❌ TEST 1: FAILED")
        tests_completed += 1
    
    # Test 2: Rohdaten-Analyse
    logger.info("\n🔬 TEST 2: Raw data analysis")
    print("Run raw data analysis? (y/n): ", end="")
    if input().lower().startswith('y'):
        if test_raw_data_analysis():
            logger.info("✅ TEST 2: COMPLETED")
        else:
            logger.error("❌ TEST 2: FAILED")
        tests_completed += 1
    
    # Test 3: Schritt-für-Schritt
    logger.info("\n📋 TEST 3: Step-by-step processing")
    print("Run step-by-step analysis? (y/n): ", end="")
    if input().lower().startswith('y'):
        if test_step_by_step_processing():
            logger.info("✅ TEST 3: COMPLETED")
        else:
            logger.error("❌ TEST 3: FAILED")
        tests_completed += 1
    
    # Auswertung
    logger.info("\n" + "=" * 60)
    logger.info(f"🏁 80-LINE ANALYSIS COMPLETED: {tests_completed} tests run")
    
    if tests_completed > 0:
        logger.info("🔍 INTERPRETATION:")
        logger.info("   If bypass test FIXES the problem:")
        logger.info("   → Problem was in offset system (now bypassed)")
        logger.info("")
        logger.info("   If bypass test STILL shows shift:")
        logger.info("   → Problem is in image_to_printer_format function")
        logger.info("   → Need to fix pixel-to-byte conversion")
        logger.info("")
        logger.info("   Check raw data analysis for byte patterns!")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
