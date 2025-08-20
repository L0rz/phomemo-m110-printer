#!/usr/bin/env python3
"""
ANALYSE DER BILDGENERIERUNG - Vergleich mit Print Master
Das Problem könnte in der Art liegen, wie wir das Bild erstellen/verarbeiten
"""

import sys
import time
import logging
from PIL import Image, ImageDraw, ImageOps

from printer_controller import EnhancedPhomemoM110
from config import *

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def create_simple_test_patterns():
    """Erstellt verschiedene einfache Testmuster um Print Master zu imitieren"""
    
    patterns = []
    
    # Pattern 1: Nur horizontale Linien (wie Print Master könnte sie machen)
    img1 = Image.new('1', (320, 240), 1)
    draw1 = ImageDraw.Draw(img1)
    for y in range(20, 220, 20):
        draw1.line([10, y, 310, y], fill=0, width=1)
    draw1.text((50, 100), "HORIZONTAL LINES", fill=0)
    patterns.append(("Horizontal Lines Only", img1))
    
    # Pattern 2: Reine geometrische Formen (ohne Text-Rendering-Probleme)
    img2 = Image.new('1', (320, 240), 1)
    draw2 = ImageDraw.Draw(img2)
    draw2.rectangle([10, 10, 310, 230], outline=0, width=2)
    draw2.ellipse([50, 50, 150, 150], outline=0, width=2)
    draw2.ellipse([170, 50, 270, 150], outline=0, width=2)
    for y in range(180, 220, 10):
        draw2.line([20, y, 300, y], fill=0, width=1)
    patterns.append(("Pure Geometry", img2))
    
    # Pattern 3: Vertikale vs Horizontale Strukturen
    img3 = Image.new('1', (320, 240), 1)
    draw3 = ImageDraw.Draw(img3)
    # Linker Teil: Vertikale Linien
    for x in range(20, 140, 20):
        draw3.line([x, 20, x, 100], fill=0, width=1)
    # Rechter Teil: Horizontale Linien  
    for y in range(20, 100, 10):
        draw3.line([180, y, 300, y], fill=0, width=1)
    # Unten: Gemischt
    for y in range(140, 220, 20):
        draw3.line([20, y, 300, y], fill=0, width=1)
    patterns.append(("Vertical vs Horizontal", img3))
    
    # Pattern 4: Sehr einfach - nur ein Rechteck
    img4 = Image.new('1', (320, 240), 1)
    draw4 = ImageDraw.Draw(img4)
    draw4.rectangle([50, 50, 270, 190], outline=0, width=3)
    draw4.text((100, 100), "SIMPLE", fill=0)
    patterns.append(("Very Simple Rectangle", img4))
    
    # Pattern 5: Print Master Style - minimalistisch
    img5 = Image.new('1', (320, 240), 1)
    draw5 = ImageDraw.Draw(img5)
    # Nur äußerer Rahmen
    draw5.rectangle([5, 5, 315, 235], outline=0, width=1)
    # Ein zentrales Element
    draw5.ellipse([120, 80, 200, 160], outline=0, width=2)
    # Wenige horizontale Linien
    draw5.line([20, 200, 300, 200], fill=0, width=1)
    draw5.line([20, 220, 300, 220], fill=0, width=1)
    patterns.append(("Print Master Style", img5))
    
    return patterns

def test_image_processing_variants():
    """Testet verschiedene Bildverarbeitungs-Ansätze"""
    logger.info("🖼️ TESTING IMAGE PROCESSING VARIANTS")
    
    try:
        printer = EnhancedPhomemoM110(PRINTER_MAC)
        
        if not printer.is_connected():
            if not printer.connect_bluetooth():
                logger.error("❌ Cannot connect to printer")
                return False
        
        patterns = create_simple_test_patterns()
        
        # Teste verschiedene Verarbeitungsschritte
        processing_variants = [
            ("Direct Print", lambda img: img),
            ("Invert Colors", lambda img: ImageOps.invert(img.convert('L')).convert('1')),
            ("No Offset Processing", lambda img: img),  # Skip apply_offsets_to_image
            ("Force Exact Size", lambda img: img.resize((384, img.height), Image.NEAREST)),
            ("Crop to 384", lambda img: img.crop((0, 0, min(384, img.width), img.height))),
        ]
        
        print(f"\n🧪 IMAGE PROCESSING ANALYSIS")
        print(f"We'll test {len(patterns)} different image patterns")
        print(f"Each with {len(processing_variants)} processing methods")
        print(f"Goal: Find which approach matches Print Master quality")
        print(f"")
        
        for pattern_name, base_img in patterns:
            logger.info(f"\n📷 Testing Pattern: {pattern_name}")
            
            print(f"\nTest pattern '{pattern_name}'? (y/n/s to skip): ", end="")
            if not input().lower().startswith('y'):
                if input() == 's':
                    break
                continue
            
            for proc_name, processor in processing_variants:
                logger.info(f"   🔄 Processing: {proc_name}")
                
                try:
                    # Bild verarbeiten
                    processed_img = processor(base_img)
                    
                    # Prüfe ob wir apply_offsets_to_image überspringen
                    if proc_name == "No Offset Processing":
                        # Direkt zur Drucker-Konvertierung
                        if processed_img.width != 384:
                            # Erweitere auf 384 Pixel Breite
                            expanded = Image.new('1', (384, processed_img.height), 1)
                            expanded.paste(processed_img, (0, 0))
                            processed_img = expanded
                        
                        final_img = processed_img
                    else:
                        # Normale Verarbeitung durch apply_offsets_to_image
                        final_img = printer.apply_offsets_to_image(processed_img)
                    
                    print(f"     Print {pattern_name} + {proc_name}? (y/n): ", end="")
                    if input().lower().startswith('y'):
                        success = printer._print_image_direct(final_img)
                        if success:
                            logger.info(f"     ✅ Printed successfully")
                            print(f"     📝 Check: Does this look like Print Master quality?")
                            input(f"     Press Enter to continue...")
                        else:
                            logger.error(f"     ❌ Print failed")
                    else:
                        logger.info(f"     ⏭️ Skipped")
                
                except Exception as e:
                    logger.error(f"     ❌ Processing error: {e}")
        
        print(f"\n🎯 ANALYSIS QUESTIONS:")
        print(f"1. Which pattern + processing combination looked PERFECT?")
        print(f"2. Did any match the Print Master quality exactly?")
        print(f"3. Did 'No Offset Processing' eliminate the shifting?")
        print(f"4. Which simple pattern had no issues at all?")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Image processing test error: {e}")
        return False

def test_raw_bitmap_approach():
    """Testet direkten Bitmap-Ansatz wie Print Master"""
    logger.info("\n🔧 TESTING RAW BITMAP APPROACH")
    
    try:
        printer = EnhancedPhomemoM110(PRINTER_MAC)
        
        # Erstelle RAW-Bitmap direkt (wie Print Master es machen könnte)
        width_pixels = 384
        height_lines = 100
        bytes_per_line = 48
        
        # Einfaches Muster direkt als Bytes
        raw_data = []
        
        for y in range(height_lines):
            line_bytes = [0] * bytes_per_line
            
            # Einfaches Muster: Rahmen + horizontale Linien
            if y < 5 or y > height_lines - 5:  # Oberer/unterer Rahmen
                for b in range(bytes_per_line):
                    line_bytes[b] = 0xFF  # Alle Bits gesetzt
            elif y % 10 == 0:  # Alle 10 Zeilen eine Linie
                for b in range(5, bytes_per_line - 5):  # Nicht ganz bis zum Rand
                    line_bytes[b] = 0xFF
            
            raw_data.extend(line_bytes)
        
        raw_bytes = bytes(raw_data)
        
        print(f"Test RAW bitmap approach? (y/n): ", end="")
        if input().lower().startswith('y'):
            logger.info(f"📤 Sending RAW bitmap: {len(raw_bytes)} bytes")
            success = printer.send_bitmap(raw_bytes, height_lines)
            
            if success:
                logger.info("✅ RAW bitmap printed successfully")
                print("📝 Check: Is this PERFECT (no shifting, clean lines)?")
                input("Press Enter to continue...")
                
                if input("Was the RAW bitmap perfect? (y/n): ").lower().startswith('y'):
                    logger.info("🎉 RAW BITMAP APPROACH WORKS!")
                    print("This means the problem is in our image-to-bitmap conversion!")
                    print("We need to analyze how Print Master converts images.")
            else:
                logger.error("❌ RAW bitmap failed")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ RAW bitmap test error: {e}")
        return False

def main():
    logger.info("🔍 IMAGE GENERATION ANALYSIS")
    logger.info("=" * 60)
    logger.info("Comparing our image processing with Print Master approach")
    logger.info("=" * 60)
    
    # Test 1: Verschiedene Bildmuster und Verarbeitung
    logger.info("\n🧪 TEST 1: Image Processing Variants")
    test_image_processing_variants()
    
    # Test 2: RAW Bitmap Ansatz
    logger.info("\n🧪 TEST 2: Raw Bitmap Approach")
    test_raw_bitmap_approach()
    
    logger.info("✅ Image generation analysis completed")
    print(f"\n💡 Next steps based on results:")
    print(f"- If RAW bitmap was perfect → Problem is in image conversion")
    print(f"- If 'No Offset Processing' was perfect → Problem is in apply_offsets_to_image")
    print(f"- If simple patterns work → Problem is complexity-related")

if __name__ == "__main__":
    main()
