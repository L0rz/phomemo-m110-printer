#!/usr/bin/env python3
"""
REAL PNG TEST - Verwendet das echte Test-PNG aus dem Git Repository
Das gibt uns das authentische Bild das normalerweise Probleme verursacht
"""

import sys
import time
import logging
from PIL import Image, ImageOps
import os

from printer_controller import EnhancedPhomemoM110
from config import *

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Pfad zum echten Test-PNG (relativ)
TEST_PNG_PATH = "2025-08-15 16_49_38-Kamera (Benutzerdefiniert).png"

def load_real_test_image():
    """Lädt das echte Test-PNG aus dem Git Repository"""
    try:
        # Prüfe verschiedene mögliche Pfade
        possible_paths = [
            TEST_PNG_PATH,  # Direkter relativer Pfad
            os.path.join(".", TEST_PNG_PATH),  # Aktuelles Verzeichnis
            os.path.join(os.path.dirname(__file__), TEST_PNG_PATH),  # Skript-Verzeichnis
        ]
        
        img_path = None
        for path in possible_paths:
            if os.path.exists(path):
                img_path = path
                break
        
        if not img_path:
            logger.error(f"❌ Test PNG not found in any of these locations:")
            for path in possible_paths:
                logger.error(f"   - {os.path.abspath(path)}")
            return None
        
        img = Image.open(img_path)
        logger.info(f"✅ Loaded real test PNG: {img.size} ({img.mode}) from {img_path}")
        
        # Zu Schwarz-Weiß konvertieren
        if img.mode != '1':
            # Erst zu Graustufen, dann zu Schwarz-Weiß
            gray_img = img.convert('L')
            bw_img = gray_img.convert('1')
            logger.info(f"✅ Converted to B&W: {bw_img.size}")
            return bw_img
        
        return img
        
    except Exception as e:
        logger.error(f"❌ Error loading test PNG: {e}")
        return None

def test_real_png_variants():
    """Testet das echte PNG mit verschiedenen Verarbeitungs-Ansätzen"""
    logger.info("🖼️ REAL PNG TEST - Using authentic test image")
    
    try:
        printer = EnhancedPhomemoM110(PRINTER_MAC)
        
        if not printer.is_connected():
            if not printer.connect_bluetooth():
                logger.error("❌ Cannot connect to printer")
                return False
        
        # Lade das echte Bild
        real_img = load_real_test_image()
        if not real_img:
            logger.error("❌ Could not load real test image")
            return False
        
        logger.info(f"📷 Real test image loaded: {real_img.size}")
        
        # Verschiedene Verarbeitungs-Ansätze für das echte Bild
        processing_approaches = [
            ("1. Current Method (with shifting)", "current"),
            ("2. Skip Offset Processing", "skip_offsets"),
            ("3. Direct 384px Resize", "direct_resize"),
            ("4. Center on 384px Canvas", "center_canvas"),
            ("5. Crop to 384px", "crop_384"),
            ("6. Force MSB Bit Order", "force_msb"),
            ("7. Force LSB Bit Order", "force_lsb"),
            ("8. Raw Bitmap Approach", "raw_bitmap"),
        ]
        
        print(f"\n🧪 REAL PNG PROCESSING TESTS")
        print(f"Testing the authentic image from your Git repository")
        print(f"Image: {os.path.basename(TEST_PNG_PATH)}")
        print(f"Size: {real_img.size}")
        print(f"")
        
        for approach_name, approach_id in processing_approaches:
            logger.info(f"\n📤 {approach_name}")
            
            print(f"Test {approach_name}? (y/n/s to skip remaining): ", end="")
            response = input()
            
            if response.lower().startswith('s'):
                logger.info("⏭️ Skipping remaining tests")
                break
            elif not response.lower().startswith('y'):
                logger.info(f"⏭️ Skipping {approach_name}")
                continue
            
            try:
                if approach_id == "current":
                    # Aktuelle Methode (die Verschiebung verursacht)
                    processed_img = printer.apply_offsets_to_image(real_img)
                    success = printer._print_image_direct(processed_img)
                
                elif approach_id == "skip_offsets":
                    # Offset-Verarbeitung überspringen
                    if real_img.width != 384:
                        expanded = Image.new('1', (384, real_img.height), 1)
                        expanded.paste(real_img, (0, 0))
                        final_img = expanded
                    else:
                        final_img = real_img
                    success = printer._print_image_direct(final_img)
                
                elif approach_id == "direct_resize":
                    # Direkt auf 384px resizen
                    resized = real_img.resize((384, real_img.height), Image.NEAREST)
                    success = printer._print_image_direct(resized)
                
                elif approach_id == "center_canvas":
                    # Auf 384px Canvas zentrieren
                    canvas = Image.new('1', (384, real_img.height), 1)
                    x_offset = (384 - real_img.width) // 2
                    canvas.paste(real_img, (x_offset, 0))
                    success = printer._print_image_direct(canvas)
                
                elif approach_id == "crop_384":
                    # Auf 384px croppen
                    cropped = real_img.crop((0, 0, min(384, real_img.width), real_img.height))
                    if cropped.width < 384:
                        expanded = Image.new('1', (384, cropped.height), 1)
                        expanded.paste(cropped, (0, 0))
                        cropped = expanded
                    success = printer._print_image_direct(cropped)
                
                elif approach_id == "force_msb":
                    # Force MSB Bit Order
                    backup_method = printer.image_to_printer_format
                    
                    def msb_converter(img):
                        # Stelle sicher, dass MSB-First verwendet wird
                        return backup_method(img)  # Das ist bereits MSB
                    
                    printer.image_to_printer_format = msb_converter
                    processed_img = printer.apply_offsets_to_image(real_img)
                    success = printer._print_image_direct(processed_img)
                    printer.image_to_printer_format = backup_method
                
                elif approach_id == "force_lsb":
                    # Force LSB Bit Order (basierend auf unseren vorherigen Tests)
                    backup_method = printer.image_to_printer_format
                    
                    def lsb_converter(img):
                        try:
                            if img.mode != '1':
                                img = img.convert('1')
                            
                            width, height = img.size
                            if width < 384:
                                expanded = Image.new('1', (384, height), 1)
                                expanded.paste(img, (0, 0))
                                img = expanded
                                width = 384
                            elif width > 384:
                                img = img.crop((0, 0, 384, height))
                                width = 384
                            
                            pixels = list(img.getdata())
                            image_bytes = []
                            
                            for y in range(height):
                                line_bytes = [0] * 48
                                
                                for pixel_x in range(384):
                                    pixel_idx = y * width + pixel_x
                                    
                                    if pixel_idx < len(pixels):
                                        pixel_value = pixels[pixel_idx]
                                    else:
                                        pixel_value = 1
                                    
                                    byte_index = pixel_x // 8
                                    bit_index = pixel_x % 8
                                    
                                    if pixel_value == 0:  # Schwarz
                                        # LSB-First (aus unseren Tests)
                                        line_bytes[byte_index] |= (1 << bit_index)
                                
                                image_bytes.extend(line_bytes)
                            
                            return bytes(image_bytes)
                            
                        except Exception as e:
                            logger.error(f"❌ LSB converter error: {e}")
                            return None
                    
                    printer.image_to_printer_format = lsb_converter
                    success = printer._print_image_direct(real_img)
                    printer.image_to_printer_format = backup_method
                
                elif approach_id == "raw_bitmap":
                    # Raw Bitmap basierend auf dem Bild
                    try:
                        # Vereinfachtes Raw-Bitmap aus dem echten Bild
                        if real_img.width != 384:
                            canvas = Image.new('1', (384, real_img.height), 1)
                            canvas.paste(real_img, (0, 0))
                            work_img = canvas
                        else:
                            work_img = real_img
                        
                        pixels = list(work_img.getdata())
                        raw_data = []
                        
                        for y in range(work_img.height):
                            line_bytes = [0] * 48
                            for x in range(384):
                                pixel_idx = y * 384 + x
                                if pixel_idx < len(pixels) and pixels[pixel_idx] == 0:
                                    byte_idx = x // 8
                                    bit_idx = 7 - (x % 8)  # MSB-First für Raw
                                    line_bytes[byte_idx] |= (1 << bit_idx)
                            raw_data.extend(line_bytes)
                        
                        raw_bytes = bytes(raw_data)
                        logger.info(f"📤 Sending raw bitmap: {len(raw_bytes)} bytes")
                        success = printer.send_bitmap(raw_bytes, work_img.height)
                        
                    except Exception as e:
                        logger.error(f"❌ Raw bitmap error: {e}")
                        success = False
                
                if success:
                    logger.info(f"✅ {approach_name} printed successfully")
                    print(f"📝 Check this result:")
                    print(f"   - Is alignment perfect (no shifting)?")
                    print(f"   - Does image look correct?")
                    print(f"   - Any artifacts or distortions?")
                    
                    quality_check = input(f"   Is this result PERFECT? (y/n): ")
                    if quality_check.lower().startswith('y'):
                        logger.info(f"🎉 PERFECT RESULT FOUND: {approach_name}")
                        print(f"🎯 We found the solution! {approach_name} works perfectly!")
                        print(f"We can implement this approach permanently.")
                        return True
                    
                    input(f"   Press Enter to continue to next test...")
                else:
                    logger.error(f"❌ {approach_name} failed to print")
            
            except Exception as e:
                logger.error(f"❌ {approach_name} error: {e}")
        
        print(f"\n📊 REAL PNG TEST SUMMARY:")
        print(f"Which approach gave the best results?")
        print(f"- If 'Skip Offset Processing' was perfect → Problem is in apply_offsets_to_image")
        print(f"- If 'Force LSB' was perfect → Problem is bit order")
        print(f"- If 'Raw Bitmap' was perfect → Problem is in image conversion pipeline")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Real PNG test error: {e}")
        return False

def main():
    logger.info("📷 REAL PNG TEST")
    logger.info("=" * 60)
    logger.info("Using the authentic test image from Git repository")
    logger.info(f"Image: {os.path.basename(TEST_PNG_PATH)}")
    logger.info("=" * 60)
    
    success = test_real_png_variants()
    
    if success:
        logger.info("✅ Real PNG test completed")
    else:
        logger.info("❌ Real PNG test failed or no perfect solution found yet")
        print(f"\n💡 Next steps:")
        print(f"- Try Print Master app with the same image")
        print(f"- Compare which approach came closest")
        print(f"- We can refine the best approach further")

if __name__ == "__main__":
    main()
