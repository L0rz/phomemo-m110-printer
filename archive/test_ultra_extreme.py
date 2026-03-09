#!/usr/bin/env python3
"""
ULTRA-EXTREME KOMPLEXITÄTS-LÖSUNG
Problem: 67% durchschnittliche Bildkomplexität (normal: 2-8%)
Lösung: Zeilenweise Übertragung mit extremen Delays
"""

import sys
import time
import logging
from PIL import Image
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

def test_ultra_extreme_approaches():
    """Testet Ultra-Extreme Ansätze für 67% Komplexität"""
    logger.info("🚀 ULTRA-EXTREME COMPLEXITY HANDLING")
    
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
        
        print(f"\n🚀 ULTRA-EXTREME APPROACHES")
        print(f"Your image has 67% average complexity (normal: 2-8%)")
        print(f"This requires EXTREME measures!")
        print(f"")
        
        # Ultra-Extreme Test-Ansätze
        approaches = [
            ("1. Insane Slow (50x slower)", 50.0),
            ("2. Line-by-Line Mode", "line_by_line"),
            ("3. Reduced Complexity", "reduce_complexity"),
            ("4. Print Master Simulation", "print_master_sim"),
            ("5. Raw Bitmap Ultra-Slow", "raw_ultra_slow"),
        ]
        
        for approach_name, approach_config in approaches:
            logger.info(f"\n📤 {approach_name}")
            
            print(f"Test {approach_name}? (y/n/s): ", end="")
            response = input()
            
            if response.lower().startswith('s'):
                break
            elif not response.lower().startswith('y'):
                continue
            
            try:
                # Backup original settings
                original_multiplier = printer.settings.get('timing_multiplier', 1.0)
                original_adaptive = printer.settings.get('adaptive_speed_enabled', True)
                
                if isinstance(approach_config, float):
                    # Insane Slow: 50x langsamer
                    logger.info(f"🐌 Setting timing_multiplier to {approach_config}x")
                    printer.update_settings({
                        'timing_multiplier': approach_config,
                        'adaptive_speed_enabled': True
                    })
                    
                    success = printer.print_image_immediate(real_img)
                
                elif approach_config == "line_by_line":
                    # Line-by-Line Mode: Jede Zeile einzeln mit Pause
                    logger.info("📏 Line-by-line transmission mode")
                    
                    # Bild vorbereiten
                    if real_img.width != 384:
                        work_img = real_img.resize((384, real_img.height), Image.NEAREST)
                    else:
                        work_img = real_img
                    
                    # Zu Drucker-Format konvertieren
                    image_data = printer.image_to_printer_format(work_img)
                    if not image_data:
                        logger.error("❌ Could not convert image")
                        continue
                    
                    # Line-by-line senden
                    bytes_per_line = 48
                    total_lines = len(image_data) // bytes_per_line
                    
                    logger.info(f"📤 Sending {total_lines} lines individually...")
                    
                    # Drucker initialisieren (korrekte Methode)
                    if not printer.send_command(b'\x1b\x40'):  # ESC @ - Reset
                        logger.error("❌ Init failed")
                        continue
                    
                    time.sleep(0.5)  # 500ms init delay
                    
                    # Header senden (korrekte Methode)
                    header = bytes([
                        0x1D, 0x76, 0x30, 0,                    # GS v 0 - Print raster bitmap
                        48, 0,                                   # Width in bytes (48)
                        total_lines & 0xFF, (total_lines >> 8) & 0xFF  # Height in lines
                    ])
                    
                    if not printer.send_command(header):
                        logger.error("❌ Header failed")
                        continue
                    
                    time.sleep(0.5)  # 500ms header delay
                    
                    # Zeilen einzeln senden mit extremen Delays
                    for line_num in range(total_lines):
                        line_start = line_num * bytes_per_line
                        line_end = line_start + bytes_per_line
                        line_data = image_data[line_start:line_end]
                        
                        # Sende eine Zeile (korrekte Methode)
                        if not printer.send_command(line_data):
                            logger.error(f"❌ Line {line_num} failed")
                            break
                        
                        # EXTREME Pause zwischen Zeilen (200ms)
                        time.sleep(0.2)
                        
                        if line_num % 20 == 0:
                            logger.info(f"📤 Sent line {line_num}/{total_lines}")
                    
                    # Finalize (korrekte Methode)
                    printer.send_command(b'\x0A')  # Line feed
                    success = True
                
                elif approach_config == "reduce_complexity":
                    # Reduced Complexity: Bild vereinfachen
                    logger.info("🎨 Reducing image complexity")
                    
                    # Bild stark glätten und Details reduzieren
                    if real_img.width != 384:
                        work_img = real_img.resize((384, real_img.height), Image.NEAREST)
                    else:
                        work_img = real_img.copy()
                    
                    # Zu Graustufen -> Schwarz-Weiß mit höherem Threshold
                    gray_img = work_img.convert('L')
                    
                    # Threshold erhöhen um Details zu reduzieren
                    def reduce_complexity_threshold(image, threshold=180):
                        """Reduziert Komplexität durch höheren Threshold"""
                        pixels = list(image.getdata())
                        new_pixels = [255 if p > threshold else 0 for p in pixels]
                        new_img = Image.new('L', image.size)
                        new_img.putdata(new_pixels)
                        return new_img.convert('1')
                    
                    reduced_img = reduce_complexity_threshold(gray_img, 180)
                    
                    # Mit normaler Geschwindigkeit drucken
                    printer.update_settings({
                        'timing_multiplier': 2.0,  # Nur 2x langsamer
                        'adaptive_speed_enabled': True
                    })
                    
                    success = printer._print_image_direct(reduced_img)
                
                elif approach_config == "print_master_sim":
                    # Print Master Simulation: Wie die App es macht
                    logger.info("📱 Print Master simulation mode")
                    
                    # Versuche zu simulieren wie Print Master arbeitet
                    if real_img.width != 384:
                        work_img = real_img.resize((384, real_img.height), Image.NEAREST)
                    else:
                        work_img = real_img.copy()
                    
                    # Print Master könnte andere Dithering/Processing verwenden
                    # Versuche verschiedene Konvertierungsansätze
                    
                    # Ansatz 1: Direkte Konvertierung ohne Preprocessing
                    raw_data = []
                    pixels = list(work_img.getdata())
                    width, height = work_img.size
                    
                    for y in range(height):
                        line_bytes = [0] * 48
                        for x in range(384):
                            pixel_idx = y * width + x
                            if pixel_idx < len(pixels) and pixels[pixel_idx] == 0:
                                byte_idx = x // 8
                                bit_idx = 7 - (x % 8)
                                line_bytes[byte_idx] |= (1 << bit_idx)
                        raw_data.extend(line_bytes)
                    
                    raw_bytes = bytes(raw_data)
                    
                    # Ultra-konservative Übertragung
                    printer.update_settings({
                        'timing_multiplier': 20.0,  # 20x langsamer
                        'adaptive_speed_enabled': False  # Adaptive deaktiviert
                    })
                    
                    success = printer.send_bitmap(raw_bytes, height)
                
                elif approach_config == "raw_ultra_slow":
                    # Raw Bitmap Ultra-Slow (korrigierte Methoden)
                    logger.info("🐌 Raw bitmap ultra-slow mode")
                    
                    if real_img.width != 384:
                        work_img = real_img.resize((384, real_img.height), Image.NEAREST)
                    else:
                        work_img = real_img.copy()
                    
                    # Direkter Raw-Bitmap-Ansatz
                    pixels = list(work_img.getdata())
                    width, height = work_img.size
                    raw_data = []
                    
                    for y in range(height):
                        line_bytes = [0] * 48
                        for x in range(384):
                            pixel_idx = y * width + x
                            if pixel_idx < len(pixels) and pixels[pixel_idx] == 0:
                                byte_idx = x // 8
                                bit_idx = 7 - (x % 8)
                                line_bytes[byte_idx] |= (1 << bit_idx)
                        raw_data.extend(line_bytes)
                    
                    raw_bytes = bytes(raw_data)
                    
                    # ULTRA-ULTRA-SLOW (100x langsamer) mit korrekten Methoden
                    logger.info(f"🐌 Using 100x slower transmission")
                    
                    # Manuell mit extremen Delays
                    if not printer.send_command(b'\x1b\x40'):  # ESC @ - Reset
                        continue
                    
                    time.sleep(0.5)  # 500ms init delay
                    
                    # Header senden
                    header = bytes([
                        0x1D, 0x76, 0x30, 0,                    # GS v 0 - Print raster bitmap
                        48, 0,                                   # Width in bytes (48)
                        height & 0xFF, (height >> 8) & 0xFF     # Height in lines
                    ])
                    
                    if not printer.send_command(header):
                        continue
                    
                    time.sleep(0.5)  # 500ms header delay
                    
                    # Daten in kleinen Blöcken mit extremen Delays
                    block_size = 48  # Eine Zeile
                    for i in range(0, len(raw_bytes), block_size):
                        block = raw_bytes[i:i+block_size]
                        printer.send_command(block)
                        time.sleep(0.5)  # 500ms pro Zeile!
                        
                        if i % (block_size * 10) == 0:
                            logger.info(f"📤 Sent {i//block_size} lines")
                    
                    printer.send_command(b'\x0A')  # Line feed
                    success = True
                
                if success:
                    logger.info(f"✅ {approach_name} completed")
                    print(f"📝 Check result:")
                    print(f"   - Perfect alignment (no shifting)?")
                    print(f"   - Image quality acceptable?")
                    
                    quality_check = input(f"   Is this result PERFECT? (y/n): ")
                    if quality_check.lower().startswith('y'):
                        logger.info(f"🎉 ULTRA-EXTREME SOLUTION FOUND: {approach_name}")
                        print(f"🎯 Success with extreme complexity handling!")
                        return True
                    
                    input(f"   Press Enter to continue...")
                else:
                    logger.error(f"❌ {approach_name} failed")
                
                # Restore original settings
                printer.update_settings({
                    'timing_multiplier': original_multiplier,
                    'adaptive_speed_enabled': original_adaptive
                })
                
            except Exception as e:
                logger.error(f"❌ {approach_name} error: {e}")
        
        print(f"\n💡 ULTRA-EXTREME ANALYSIS:")
        print(f"Your image complexity is EXTREME (67% avg, 78% peak)")
        print(f"Normal images: 2-8% complexity")
        print(f"Your image: 60-78% complexity (10x higher!)")
        print(f"")
        print(f"If none worked, consider:")
        print(f"1. Reduce image resolution before printing")
        print(f"2. Apply heavy blur/simplification")
        print(f"3. Use Print Master app (it has optimized handling)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ultra-extreme test error: {e}")
        return False

def main():
    logger.info("🚀 ULTRA-EXTREME COMPLEXITY HANDLING")
    logger.info("=" * 60)
    logger.info("Problem: Extreme image complexity (67% average)")
    logger.info("Solution: Ultra-extreme timing and processing")
    logger.info("=" * 60)
    
    success = test_ultra_extreme_approaches()
    
    if success:
        logger.info("✅ Ultra-extreme test completed")
    else:
        logger.info("❌ No solution found - image too complex for current approach")

if __name__ == "__main__":
    main()
