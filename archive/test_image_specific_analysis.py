#!/usr/bin/env python3
"""
BILDSPEZIFISCHE ANALYSE: Warum bestimmte Bilder Verschiebungen verursachen
Analysiert das problematische Bild aus test_zero_offset.py im Detail
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

def recreate_problematic_image():
    """Rekonstruiert das problematische Bild aus test_zero_offset.py"""
    try:
        # Ähnlich dem Original: 320x240
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
        
        logger.info(f"✅ Recreated problematic image: {img.width}x{img.height}")
        return img
        
    except Exception as e:
        logger.error(f"❌ Error recreating image: {e}")
        return None

def create_simple_working_image():
    """Erstellt ein einfaches Bild das funktioniert (wie aus den neuen Tests)"""
    img = Image.new('1', (320, 240), 1)  # Weiß
    draw = ImageDraw.Draw(img)
    
    # Nur einfache geometrische Formen
    draw.rectangle([0, 0, 319, 239], outline=0, width=2)
    
    # Vertikale Linien
    for x in range(50, 320, 50):
        draw.line([x, 0, x, 239], fill=0, width=1)
    
    # Horizontale Linien
    for y in range(50, 240, 50):
        draw.line([0, y, 319, y], fill=0, width=1)
    
    logger.info(f"✅ Created simple working image: {img.width}x{img.height}")
    return img

def analyze_byte_differences(img1, img2, printer):
    """Analysiert Byte-Unterschiede zwischen zwei Bildern"""
    logger.info("🔬 ANALYZING: Byte differences between images")
    
    try:
        # Beide Bilder durch den gleichen Prozess
        data1 = printer.image_to_printer_format(img1)
        data2 = printer.image_to_printer_format(img2)
        
        if not data1 or not data2:
            logger.error("❌ Could not convert images to printer format")
            return False
        
        logger.info(f"📊 Image 1 data: {len(data1)} bytes")
        logger.info(f"📊 Image 2 data: {len(data2)} bytes")
        
        if len(data1) != len(data2):
            logger.error("❌ Different data sizes!")
            return False
        
        # Zeile-für-Zeile-Vergleich
        height1, height2 = img1.height, img2.height
        bytes_per_line = PRINTER_BYTES_PER_LINE
        
        differences_found = 0
        
        for line_num in range(min(height1, height2)):
            line_start = line_num * bytes_per_line
            line_end = line_start + bytes_per_line
            
            line1 = data1[line_start:line_end]
            line2 = data2[line_start:line_end]
            
            # Vergleiche Zeilen
            if line1 != line2:
                differences_found += 1
                
                # Zeige Unterschiede in ersten 10 verschiedenen Zeilen
                if differences_found <= 10:
                    diff_bytes = sum(1 for i in range(len(line1)) if line1[i] != line2[i])
                    logger.info(f"   Line {line_num}: {diff_bytes} different bytes")
                    
                    # Zeige erste 8 Bytes
                    hex1 = ' '.join(f'{b:02x}' for b in line1[:8])
                    hex2 = ' '.join(f'{b:02x}' for b in line2[:8])
                    logger.info(f"     Image1: {hex1}...")
                    logger.info(f"     Image2: {hex2}...")
        
        logger.info(f"🔍 Total different lines: {differences_found}/{min(height1, height2)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Byte analysis error: {e}")
        return False

def analyze_problematic_image_structure():
    """Analysiert die Struktur des problematischen Bildes"""
    logger.info("🔍 ANALYZING: Problematic image structure")
    
    try:
        printer = EnhancedPhomemoM110(PRINTER_MAC)
        problematic_img = recreate_problematic_image()
        
        if not problematic_img:
            return False
        
        # Analysiere verschiedene Bereiche des Bildes
        width, height = problematic_img.size
        
        logger.info("🔍 Image structure analysis:")
        logger.info(f"   Size: {width}x{height}")
        
        # Analysiere Pixel-Dichte in verschiedenen Bereichen
        regions = [
            ("Top 80 lines (0-79)", 0, 79),
            ("Lines 80-159", 80, 159), 
            ("Bottom lines (160+)", 160, height-1)
        ]
        
        for region_name, start_y, end_y in regions:
            if end_y < height:
                # Zähle schwarze Pixel in diesem Bereich
                black_pixels = 0
                total_pixels = 0
                
                for y in range(start_y, min(end_y + 1, height)):
                    for x in range(width):
                        pixel = problematic_img.getpixel((x, y))
                        total_pixels += 1
                        if pixel == 0:  # Schwarz
                            black_pixels += 1
                
                density = (black_pixels / total_pixels) * 100 if total_pixels > 0 else 0
                logger.info(f"   {region_name}: {black_pixels}/{total_pixels} black pixels ({density:.1f}%)")
        
        # Konvertiere zu Printer-Format und analysiere
        printer_data = printer.image_to_printer_format(problematic_img)
        
        if printer_data:
            logger.info(f"✅ Problematic image converted: {len(printer_data)} bytes")
            
            # Analysiere Bytes um Zeile 80 herum
            logger.info("🔍 Bytes around line 80:")
            for line_num in range(75, 85):
                if line_num < height:
                    line_start = line_num * PRINTER_BYTES_PER_LINE
                    line_end = line_start + PRINTER_BYTES_PER_LINE
                    line_data = printer_data[line_start:line_end]
                    
                    non_zero_bytes = sum(1 for b in line_data if b != 0)
                    first_bytes = ' '.join(f'{b:02x}' for b in line_data[:8])
                    
                    marker = " ⚠️ CRITICAL!" if line_num == 80 else ""
                    logger.info(f"     Line {line_num}: {non_zero_bytes} non-zero bytes | {first_bytes}...{marker}")
            
            return True
        else:
            logger.error("❌ Could not convert problematic image")
            return False
            
    except Exception as e:
        logger.error(f"❌ Structure analysis error: {e}")
        return False

def test_isolated_problem_reproduction():
    """Testet isolierte Reproduktion des Problems"""
    logger.info("🎯 TESTING: Isolated problem reproduction")
    
    try:
        printer = EnhancedPhomemoM110(PRINTER_MAC)
        
        # Verbindung prüfen
        if not printer.is_connected():
            logger.info("🔌 Connecting to printer...")
            if not printer.connect_bluetooth():
                logger.error("❌ Cannot connect to printer!")
                return False
        
        logger.info("🎯 Testing BOTH images:")
        
        # Test 1: Problematisches Bild
        logger.info("\n📋 TEST A: Problematic image (should show shift)")
        print("Print problematic image? (y/n): ", end="")
        if input().lower().startswith('y'):
            problematic_img = recreate_problematic_image()
            if problematic_img:
                success = printer._print_image_direct(problematic_img)
                if success:
                    logger.info("✅ Problematic image printed")
                    logger.info("👀 Expected: Shift at ~10mm from top")
                else:
                    logger.error("❌ Print failed")
        
        # Test 2: Einfaches funktionierendes Bild
        logger.info("\n📋 TEST B: Simple working image (should be perfect)")
        print("Print simple working image? (y/n): ", end="")
        if input().lower().startswith('y'):
            simple_img = create_simple_working_image()
            success = printer._print_image_direct(simple_img)
            if success:
                logger.info("✅ Simple image printed")
                logger.info("👀 Expected: Perfect alignment, no shifts")
            else:
                logger.error("❌ Print failed")
        
        # Test 3: Vergleichsanalyse
        logger.info("\n📋 TEST C: Byte comparison analysis")
        problematic_img = recreate_problematic_image()
        simple_img = create_simple_working_image()
        
        if problematic_img and simple_img:
            analyze_byte_differences(problematic_img, simple_img, printer)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Reproduction test error: {e}")
        return False

def main():
    """Hauptfunktion für bildspezifische Analyse"""
    logger.info("=" * 60)
    logger.info("🎯 PHOMEMO M110 - IMAGE-SPECIFIC PROBLEM ANALYSIS")
    logger.info("=" * 60)
    logger.info("Goal: Find why certain images cause shifts while others don't")
    logger.info("Known: Simple patterns work, complex images fail reproducibly")
    logger.info("=" * 60)
    
    tests_completed = 0
    
    # Test 1: Struktur-Analyse
    logger.info("\n🔍 TEST 1: Problematic image structure analysis")
    if analyze_problematic_image_structure():
        tests_completed += 1
        logger.info("✅ TEST 1: COMPLETED")
    else:
        logger.error("❌ TEST 1: FAILED")
    
    # Test 2: Isolierte Reproduktion
    logger.info("\n🎯 TEST 2: Isolated reproduction test")
    if test_isolated_problem_reproduction():
        tests_completed += 1
        logger.info("✅ TEST 2: COMPLETED")
    else:
        logger.error("❌ TEST 2: FAILED")
    
    # Auswertung
    logger.info("\n" + "=" * 60)
    logger.info(f"🏁 IMAGE ANALYSIS COMPLETED: {tests_completed}/2 tests run")
    
    if tests_completed >= 1:
        logger.info("🔍 KEY INSIGHTS:")
        logger.info("   • Problem is IMAGE-DEPENDENT and REPRODUCIBLE")
        logger.info("   • Simple geometric patterns work perfectly")
        logger.info("   • Complex images with text/curves cause shifts")
        logger.info("   • Shift occurs at specific line (~80) consistently")
        logger.info("")
        logger.info("🎯 NEXT STEPS:")
        logger.info("   • Compare byte patterns between working/failing images")
        logger.info("   • Identify what image features trigger the problem")
        logger.info("   • Possibly related to pixel density or specific patterns")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
