#!/usr/bin/env python3
"""
POSITIONSABHÄNGIGE FEHLER-ANALYSE
Test 4 zeigt: Erste cm perfekt, dann Fehler
→ Das Problem tritt nach einer bestimmten Byte-Position auf!
"""

import sys
import time
import logging
from PIL import Image, ImageDraw
import os

from printer_controller import EnhancedPhomemoM110
from config import *

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def load_real_test_image():
    """Lädt das echte Test-PNG"""
    try:
        test_png_path = "2025-08-15 16_49_38-Kamera (Benutzerdefiniert).png"
        
        if os.path.exists(test_png_path):
            img = Image.open(test_png_path)
            if img.mode != '1':
                img = img.convert('L').convert('1')
            logger.info(f"✅ Loaded real test PNG: {img.size}")
            return img
        else:
            logger.error(f"❌ PNG not found: {test_png_path}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error loading PNG: {e}")
        return None

def create_position_test_patterns():
    """Erstellt Test-Muster um positionsabhängige Fehler zu identifizieren"""
    
    patterns = []
    
    # Pattern 1: Nur linke Hälfte (erste cm)
    img1 = Image.new('1', (192, 240), 1)  # Halbe Breite
    draw1 = ImageDraw.Draw(img1)
    draw1.rectangle([0, 0, 191, 239], outline=0, width=2)
    draw1.text((20, 50), "LEFT HALF", fill=0)
    draw1.text((20, 80), "ONLY", fill=0)
    # Komplexes Muster nur links
    for y in range(120, 200, 10):
        draw1.line([10, y, 180, y], fill=0, width=1)
    patterns.append(("Left Half Only (should be perfect)", img1))
    
    # Pattern 2: Nur rechte Hälfte (wo der Fehler auftritt)
    img2 = Image.new('1', (192, 240), 1)
    draw2 = ImageDraw.Draw(img2)
    draw2.rectangle([0, 0, 191, 239], outline=0, width=2)
    draw2.text((20, 50), "RIGHT HALF", fill=0)
    draw2.text((20, 80), "ONLY", fill=0)
    # Komplexes Muster nur rechts
    for y in range(120, 200, 10):
        draw2.line([10, y, 180, y], fill=0, width=1)
    patterns.append(("Right Half Only (should show error)", img2))
    
    # Pattern 3: Vertikale Linien alle 8 Pixel (Byte-Grenzen)
    img3 = Image.new('1', (384, 240), 1)
    draw3 = ImageDraw.Draw(img3)
    # Jede 8. Pixel-Position = Byte-Grenze
    for x in range(0, 384, 8):
        draw3.line([x, 0, x, 239], fill=0, width=1)
    draw3.text((50, 100), "BYTE BOUNDARIES", fill=0)
    patterns.append(("Byte Boundaries (8px grid)", img3))
    
    # Pattern 4: Progressiver Test - von einfach zu komplex
    img4 = Image.new('1', (384, 240), 1)
    draw4 = ImageDraw.Draw(img4)
    # Linker Teil: Einfach
    draw4.rectangle([10, 10, 120, 50], outline=0, width=1)
    draw4.text((20, 25), "SIMPLE", fill=0)
    
    # Mittlerer Teil: Mittel
    for y in range(60, 120, 5):
        draw4.line([130, y, 250, y], fill=0, width=1)
    draw4.text((140, 80), "MEDIUM", fill=0)
    
    # Rechter Teil: Komplex
    for y in range(130, 220, 3):
        for x in range(260, 370, 6):
            draw4.point((x, y), fill=0)
    draw4.text((270, 150), "COMPLEX", fill=0)
    patterns.append(("Progressive Complexity", img4))
    
    return patterns

def test_position_dependent_errors():
    """Testet positionsabhängige Fehler"""
    logger.info("🔍 POSITION-DEPENDENT ERROR ANALYSIS")
    
    try:
        printer = EnhancedPhomemoM110(PRINTER_MAC)
        
        if not printer.is_connected():
            if not printer.connect_bluetooth():
                logger.error("❌ Cannot connect to printer")
                return False
        
        # Lade echtes Bild
        real_img = load_real_test_image()
        if not real_img:
            logger.error("❌ Could not load real image")
            return False
        
        print(f"\n🧪 POSITION ANALYSIS TESTS")
        print(f"Goal: Find WHERE the shifting starts")
        print(f"")
        
        # Test 1: Echtes Bild mit verschiedenen Positionierungen
        positioning_tests = [
            ("Real Image - Left Aligned", lambda img: img),  # Normal links
            ("Real Image - Centered", lambda img: center_image(img)),  # Zentriert (wie Test 4)
            ("Real Image - Right Aligned", lambda img: right_align_image(img)),  # Rechts
        ]
        
        def center_image(img):
            """Zentriert Bild auf 384px Canvas"""
            canvas = Image.new('1', (384, img.height), 1)
            x_offset = (384 - img.width) // 2
            canvas.paste(img, (x_offset, 0))
            return canvas
        
        def right_align_image(img):
            """Rechts-ausgerichtetes Bild auf 384px Canvas"""
            canvas = Image.new('1', (384, img.height), 1)
            x_offset = 384 - img.width
            canvas.paste(img, (x_offset, 0))
            return canvas
        
        for test_name, processor in positioning_tests:
            logger.info(f"\n📤 {test_name}")
            
            print(f"Test {test_name}? (y/n/s): ", end="")
            response = input()
            
            if response.lower().startswith('s'):
                break
            elif response.lower().startswith('y'):
                processed_img = processor(real_img)
                success = printer._print_image_direct(processed_img)
                
                if success:
                    logger.info(f"✅ {test_name} printed")
                    print(f"📝 Check alignment: Where does shifting start?")
                    input(f"   Press Enter to continue...")
                else:
                    logger.error(f"❌ {test_name} failed")
        
        # Test 2: Spezielle Positionsmuster
        patterns = create_position_test_patterns()
        
        print(f"\n🎯 POSITION PATTERN TESTS")
        
        for pattern_name, pattern_img in patterns:
            logger.info(f"\n📤 {pattern_name}")
            
            print(f"Test {pattern_name}? (y/n/s): ", end="")
            response = input()
            
            if response.lower().startswith('s'):
                break
            elif response.lower().startswith('y'):
                # Verwende verschiedene Positionierungsansätze
                
                # Test A: Links-ausgerichtet
                left_canvas = Image.new('1', (384, pattern_img.height), 1)
                left_canvas.paste(pattern_img, (0, 0))
                
                print(f"   Test {pattern_name} - Left aligned? (y/n): ", end="")
                if input().lower().startswith('y'):
                    success = printer._print_image_direct(left_canvas)
                    if success:
                        logger.info(f"   ✅ Left aligned printed")
                        input(f"   Check result, press Enter...")
                
                # Test B: Zentriert (wie Test 4)
                center_canvas = Image.new('1', (384, pattern_img.height), 1)
                x_offset = (384 - pattern_img.width) // 2
                center_canvas.paste(pattern_img, (x_offset, 0))
                
                print(f"   Test {pattern_name} - Centered? (y/n): ", end="")
                if input().lower().startswith('y'):
                    success = printer._print_image_direct(center_canvas)
                    if success:
                        logger.info(f"   ✅ Centered printed")
                        input(f"   Check result, press Enter...")
        
        print(f"\n🔍 ANALYSIS QUESTIONS:")
        print(f"1. Does 'Left Half Only' print perfectly?")
        print(f"2. Does 'Right Half Only' show shifting?")
        print(f"3. At which byte boundary does shifting start?")
        print(f"4. Is centered positioning better than left-aligned?")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Position analysis error: {e}")
        return False

def main():
    logger.info("🔍 POSITION-DEPENDENT ERROR ANALYSIS")
    logger.info("=" * 60)
    logger.info("Finding WHERE the shifting starts in the image")
    logger.info("Based on Test 4 observation: first cm perfect, then error")
    logger.info("=" * 60)
    
    success = test_position_dependent_errors()
    
    if success:
        logger.info("✅ Position analysis completed")
        print(f"\n💡 If we find the exact position where shifting starts,")
        print(f"we can fix the bit-mapping at that specific point!")
    else:
        logger.error("❌ Position analysis failed")

if __name__ == "__main__":
    main()
