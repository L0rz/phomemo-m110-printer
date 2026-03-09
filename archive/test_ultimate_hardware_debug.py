#!/usr/bin/env python3
"""
ULTIMATIVER DEBUG: RAW-Bytes-Analyse und Hardware-Limit-Test
Wenn alle Korrekturen versagen, liegt das Problem in der Hardware/Firmware
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

def save_raw_bytes_to_file(data, filename):
    """Speichert Raw-Bytes in eine Datei zur Analyse"""
    try:
        with open(filename, 'wb') as f:
            f.write(data)
        logger.info(f"📁 Raw bytes saved to: {filename}")
        return True
    except Exception as e:
        logger.error(f"❌ Could not save raw bytes: {e}")
        return False

def create_ultra_simple_test():
    """Erstellt das einfachste mögliche Testbild"""
    # Nur 100x100, sehr einfach
    img = Image.new('1', (100, 100), 1)  # Weiß
    draw = ImageDraw.Draw(img)
    
    # Nur ein einfaches Kreuz
    draw.line([0, 50, 99, 50], fill=0, width=2)  # Horizontal
    draw.line([50, 0, 50, 99], fill=0, width=2)  # Vertikal
    
    logger.info(f"✅ Created ultra-simple test: {img.width}x{img.height}")
    return img

def create_problematic_clone():
    """Erstellt eine exakte Kopie des problematischen Bildes"""
    img = Image.new('1', (320, 240), 1)  # Weiß
    draw = ImageDraw.Draw(img)
    
    # Rahmen
    draw.rectangle([0, 0, 319, 239], outline=0, width=2)
    
    # Text
    draw.text((10, 20), "TEST IMAGE", fill=0)
    draw.text((10, 50), "X-OFFSET = 0", fill=0)
    draw.text((10, 80), "NO WRAPPING", fill=0)
    
    # Marker
    draw.rectangle([5, 5, 25, 25], outline=0, width=3)
    draw.text((8, 8), "L", fill=0)
    draw.rectangle([295, 5, 315, 25], outline=0, width=3)
    draw.text((298, 8), "R", fill=0)
    
    # Gesicht
    center_x, center_y = 160, 120
    draw.ellipse([center_x-40, center_y-40, center_x+40, center_y+40], outline=0, width=2)
    draw.ellipse([center_x-15, center_y-15, center_x-5, center_y-5], fill=0)
    draw.ellipse([center_x+5, center_y-15, center_x+15, center_y-5], fill=0)
    
    # Horizontale Linien
    for y in [160, 180, 200, 220]:
        draw.line([30, y, 290, y], fill=0, width=1)
    
    logger.info(f"✅ Created problematic clone: {img.width}x{img.height}")
    return img

def analyze_raw_byte_patterns():
    """Analysiert die RAW-Byte-Muster beider Bilder"""
    logger.info("🔬 ULTIMATE ANALYSIS: Raw byte patterns")
    
    try:
        printer = EnhancedPhomemoM110(PRINTER_MAC)
        
        # Beide Bilder erstellen
        simple_img = create_ultra_simple_test()
        problem_img = create_problematic_clone()
        
        # Zu RAW-Bytes konvertieren
        simple_data = printer.image_to_printer_format(simple_img)
        problem_data = printer.image_to_printer_format(problem_img)
        
        if not simple_data or not problem_data:
            logger.error("❌ Could not convert images to raw data")
            return False
        
        logger.info(f"📊 Simple image: {len(simple_data)} bytes")
        logger.info(f"📊 Problem image: {len(problem_data)} bytes")
        
        # RAW-Bytes speichern für externe Analyse
        save_raw_bytes_to_file(simple_data, "simple_image_raw.bin")
        save_raw_bytes_to_file(problem_data, "problem_image_raw.bin")
        
        # Analysiere Zeile 80 speziell
        if len(problem_data) >= 80 * PRINTER_BYTES_PER_LINE:
            logger.info("🔍 CRITICAL LINE 80 ANALYSIS:")
            
            # Zeilen 78, 79, 80, 81, 82
            for line_num in range(78, 83):
                line_start = line_num * PRINTER_BYTES_PER_LINE
                line_end = line_start + PRINTER_BYTES_PER_LINE
                
                if line_end <= len(problem_data):
                    line_data = problem_data[line_start:line_end]
                    
                    # Analysiere erste 16 Bytes
                    hex_data = ' '.join(f'{b:02x}' for b in line_data[:16])
                    non_zero = sum(1 for b in line_data if b != 0)
                    
                    marker = " ⚠️ CRITICAL LINE!" if line_num == 80 else ""
                    logger.info(f"   Line {line_num}: {hex_data}... ({non_zero} non-zero){marker}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Raw analysis error: {e}")
        return False

def test_hardware_limit_hypothesis():
    """Testet die Hardware-Limit-Hypothese"""
    logger.info("🔧 TESTING: Hardware limit hypothesis")
    
    try:
        printer = EnhancedPhomemoM110(PRINTER_MAC)
        
        if not printer.is_connected():
            if not printer.connect_bluetooth():
                return False
        
        logger.info("🔧 Testing hardware limit theory:")
        logger.info("   If M110 has a 80-line buffer limitation,")
        logger.info("   then splitting the image should fix the problem!")
        
        # Problematisches Bild in zwei Hälften teilen
        full_img = create_problematic_clone()
        width, height = full_img.size
        
        # Erste Hälfte (Zeilen 0-119)
        first_half = full_img.crop((0, 0, width, 120))
        
        # Zweite Hälfte (Zeilen 120-239)  
        second_half = full_img.crop((0, 120, width, height))
        
        logger.info(f"📐 Split image: {width}x{height} -> {first_half.width}x{first_half.height} + {second_half.width}x{second_half.height}")
        
        print("Print SPLIT image test? (y/n): ", end="")
        if input().lower().startswith('y'):
            logger.info("🖨️ Printing first half...")
            success1 = printer._print_image_direct(first_half)
            
            if success1:
                time.sleep(1)  # Kurze Pause
                logger.info("🖨️ Printing second half...")
                success2 = printer._print_image_direct(second_half)
                
                if success2:
                    logger.info("✅ SPLIT TEST: Both halves printed!")
                    logger.info("👀 Check results:")
                    logger.info("   ✅ If BOTH halves are perfect → Hardware buffer limit!")
                    logger.info("   ❌ If second half still shifts → Different problem")
                else:
                    logger.error("❌ Second half failed")
            else:
                logger.error("❌ First half failed")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Hardware limit test error: {e}")
        return False

def test_alternative_transmission_method():
    """Testet alternative Übertragungsmethode"""
    logger.info("📡 TESTING: Alternative transmission method")
    
    try:
        printer = EnhancedPhomemoM110(PRINTER_MAC)
        
        if not printer.is_connected():
            if not printer.connect_bluetooth():
                return False
        
        # Sehr kleines Testbild
        test_img = Image.new('1', (384, 50), 1)  # Nur 50 Zeilen
        draw = ImageDraw.Draw(test_img)
        
        # Einfaches Muster
        for y in range(0, 50, 5):
            draw.line([0, y, 383, y], fill=0, width=1)
            draw.text((10, y), f"Line {y}", fill=0)
        
        logger.info("📡 Testing ULTRA-CONSERVATIVE transmission...")
        
        # Manuelle, ultra-langsame Übertragung
        raw_data = printer.image_to_printer_format(test_img)
        
        if raw_data:
            # Manueller Send-Prozess
            height = test_img.height
            width_bytes = PRINTER_BYTES_PER_LINE
            
            # 1. Init
            logger.info("   Step 1: Init...")
            printer.send_command(b'\x1b\x40')
            time.sleep(0.5)
            
            # 2. Header
            logger.info("   Step 2: Header...")
            header = bytes([
                0x1D, 0x76, 0x30, 0,
                width_bytes & 0xFF, (width_bytes >> 8) & 0xFF,
                height & 0xFF, (height >> 8) & 0xFF
            ])
            printer.send_command(header)
            time.sleep(0.5)
            
            # 3. Daten ZEILE FÜR ZEILE mit Pausen
            logger.info("   Step 3: Line-by-line transmission...")
            for line_num in range(height):
                line_start = line_num * width_bytes
                line_end = line_start + width_bytes
                line_data = raw_data[line_start:line_end]
                
                printer.send_command(line_data)
                time.sleep(0.05)  # 50ms pro Zeile!
                
                if line_num % 10 == 0:
                    logger.info(f"     Sent line {line_num}/{height}")
            
            time.sleep(0.5)
            logger.info("✅ ULTRA-CONSERVATIVE: Transmission completed!")
            logger.info("👀 Check if this eliminates any shifting")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Alternative transmission error: {e}")
        return False

def main():
    """Ultimative Hardware-Debugging-Hauptfunktion"""
    logger.info("=" * 60)
    logger.info("🔬 PHOMEMO M110 - ULTIMATE HARDWARE DEBUG")
    logger.info("=" * 60)
    logger.info("All software fixes failed → Testing hardware limitations")
    logger.info("Hypothesis: M110 has buffer/timing issues after ~80 lines")
    logger.info("=" * 60)
    
    tests_completed = 0
    
    # Test 1: RAW-Byte-Analyse
    logger.info("\n🔬 TEST 1: Raw byte pattern analysis")
    if analyze_raw_byte_patterns():
        tests_completed += 1
        logger.info("✅ TEST 1: COMPLETED - Check raw files!")
    else:
        logger.error("❌ TEST 1: FAILED")
    
    # Test 2: Hardware-Limit-Hypothese
    logger.info("\n🔧 TEST 2: Hardware limit hypothesis (split image)")
    if test_hardware_limit_hypothesis():
        tests_completed += 1
        logger.info("✅ TEST 2: COMPLETED")
    else:
        logger.error("❌ TEST 2: FAILED")
    
    # Test 3: Alternative Übertragung
    logger.info("\n📡 TEST 3: Ultra-conservative transmission")
    print("Run ultra-conservative transmission test? (y/n): ", end="")
    if input().lower().startswith('y'):
        if test_alternative_transmission_method():
            tests_completed += 1
            logger.info("✅ TEST 3: COMPLETED")
        else:
            logger.error("❌ TEST 3: FAILED")
    else:
        logger.info("⏭️ TEST 3: SKIPPED")
    
    # Finale Auswertung
    logger.info("\n" + "=" * 60)
    logger.info(f"🏁 ULTIMATE DEBUG COMPLETED: {tests_completed} tests run")
    
    logger.info("🔍 POSSIBLE CONCLUSIONS:")
    logger.info("   1. If SPLIT images work → M110 buffer limit at ~80 lines")
    logger.info("   2. If ultra-slow transmission works → Timing issue")
    logger.info("   3. If nothing works → Fundamental M110 firmware bug")
    logger.info("")
    logger.info("📁 Check the raw byte files for external analysis:")
    logger.info("   • simple_image_raw.bin")
    logger.info("   • problem_image_raw.bin")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
