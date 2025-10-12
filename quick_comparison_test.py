#!/usr/bin/env python3
"""
Quick Test: Vergleicht alte vs. neue Bitmap-Konvertierung

Zeigt genau wo der Unterschied liegt und ob der Fix korrekt ist.
"""

import sys
import os
from PIL import Image
import logging

# Setup
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))


def old_image_to_printer_format(img, width_pixels=384, bytes_per_line=48):
    """
    ALTE VERSION: Dein Original-Code
    """
    if img.mode != '1':
        img = img.convert('1')
    
    width, height = img.size
    
    # OLD: Resize mit NEAREST (zerstört Dithering)
    if width != width_pixels:
        img = img.resize((width_pixels, height), Image.Resampling.NEAREST)
        width = width_pixels
    
    pixels = list(img.getdata())
    image_bytes = []
    
    for y in range(height):
        line_bytes = [0] * bytes_per_line
        
        for pixel_x in range(width_pixels):
            pixel_idx = y * width + pixel_x
            
            if pixel_idx < len(pixels):
                pixel_value = pixels[pixel_idx]
            else:
                pixel_value = 1  # Weiß
            
            byte_index = pixel_x // 8
            bit_index = pixel_x % 8
            
            # OLD: Annahme pixel_value ist 0 oder 1
            if pixel_value == 0:
                line_bytes[byte_index] |= (1 << (7 - bit_index))
        
        image_bytes.extend(line_bytes)
    
    return bytes(image_bytes)


def new_image_to_printer_format(img, width_pixels=384, bytes_per_line=48):
    """
    NEUE VERSION: Fixed mit korrekter PIL-Pixel-Wert-Behandlung
    """
    if img.mode != '1':
        img = img.convert('1')
    
    width, height = img.size
    
    # NEW: Bild MUSS bereits korrekt skaliert sein
    if width != width_pixels:
        logger.error(f"Image must be {width_pixels}px wide, got {width}px")
        return None
    
    pixels = list(img.getdata())
    image_bytes = []
    
    for y in range(height):
        line_bytes = bytearray(bytes_per_line)
        
        for x in range(width_pixels):
            pixel_idx = y * width + x
            
            if pixel_idx < len(pixels):
                # NEW: PIL gibt 0 oder 255 zurück, nicht 0 oder 1!
                pixel_value = pixels[pixel_idx]
            else:
                pixel_value = 255  # Weiß
            
            # NEW: Explizite Prüfung auf schwarz
            is_black = (pixel_value == 0)
            
            byte_idx = x // 8
            bit_idx = x % 8
            
            if is_black:
                line_bytes[byte_idx] |= (1 << (7 - bit_idx))
        
        image_bytes.extend(line_bytes)
    
    return bytes(image_bytes)


def compare_conversions():
    """Vergleicht alte und neue Konvertierung"""
    
    logger.info("=" * 80)
    logger.info("VERGLEICH: ALTE vs. NEUE BITMAP-KONVERTIERUNG")
    logger.info("=" * 80)
    
    # Test 1: Einfaches Testbild
    logger.info("\n📊 Test 1: Einfaches Testbild (linke Hälfte schwarz)")
    
    # Erstelle Testbild: 384x100, linke Hälfte schwarz
    img = Image.new('1', (384, 100), 1)  # Weiß
    for y in range(100):
        for x in range(192):  # Linke Hälfte
            img.putpixel((x, y), 0)  # Schwarz
    
    # Prüfe PIL Pixel-Werte
    pixels = list(img.getdata())
    unique_values = set(pixels)
    logger.info(f"   PIL Pixel-Werte im Bild: {unique_values}")
    
    if unique_values == {0, 255}:
        logger.info("   ✅ PIL gibt korrekt 0 und 255 zurück")
    elif unique_values == {0, 1}:
        logger.warning("   ⚠️ PIL gibt 0 und 1 zurück (ungewöhnlich)")
    else:
        logger.error(f"   ❌ Unerwartete Pixel-Werte: {unique_values}")
    
    # Alte Konvertierung
    logger.info("\n🔧 Alte Konvertierung:")
    old_data = old_image_to_printer_format(img)
    logger.info(f"   Bytes generiert: {len(old_data)}")
    logger.info(f"   Erste 5 Bytes: {' '.join(f'0x{b:02X}' for b in old_data[:5])}")
    logger.info(f"   Bytes 24-28 (Mitte): {' '.join(f'0x{b:02X}' for b in old_data[24:29])}")
    
    # Erwartung prüfen
    if old_data[0] == 0xFF:
        logger.info("   ✅ Erstes Byte korrekt (0xFF = 8 schwarze Pixel)")
    else:
        logger.warning(f"   ⚠️ Erstes Byte: 0x{old_data[0]:02X} (erwartet: 0xFF)")
    
    if old_data[24] == 0x00:
        logger.info("   ✅ Byte 24 korrekt (0x00 = 8 weiße Pixel)")
    else:
        logger.warning(f"   ⚠️ Byte 24: 0x{old_data[24]:02X} (erwartet: 0x00)")
    
    # Neue Konvertierung
    logger.info("\n🔧 Neue Konvertierung:")
    new_data = new_image_to_printer_format(img)
    if new_data:
        logger.info(f"   Bytes generiert: {len(new_data)}")
        logger.info(f"   Erste 5 Bytes: {' '.join(f'0x{b:02X}' for b in new_data[:5])}")
        logger.info(f"   Bytes 24-28 (Mitte): {' '.join(f'0x{b:02X}' for b in new_data[24:29])}")
        
        if new_data[0] == 0xFF:
            logger.info("   ✅ Erstes Byte korrekt (0xFF = 8 schwarze Pixel)")
        else:
            logger.warning(f"   ⚠️ Erstes Byte: 0x{new_data[0]:02X} (erwartet: 0xFF)")
        
        if new_data[24] == 0x00:
            logger.info("   ✅ Byte 24 korrekt (0x00 = 8 weiße Pixel)")
        else:
            logger.warning(f"   ⚠️ Byte 24: 0x{new_data[24]:02X} (erwartet: 0x00)")
    else:
        logger.error("   ❌ Neue Konvertierung fehlgeschlagen")
    
    # Vergleich
    logger.info("\n📊 VERGLEICH:")
    if old_data == new_data:
        logger.info("   ℹ️ Beide Konvertierungen identisch")
        logger.info("   → PIL gibt wahrscheinlich bereits 0/255 zurück")
        logger.info("   → Hauptproblem war das Resize-Timing/Algorithmus!")
    else:
        differences = sum(1 for a, b in zip(old_data, new_data) if a != b)
        logger.warning(f"   ⚠️ {differences} unterschiedliche Bytes gefunden")
        logger.info("   → Zeigt erste Unterschiede:")
        
        for i in range(min(100, len(old_data))):
            if old_data[i] != new_data[i]:
                logger.info(f"      Byte {i}: Alt=0x{old_data[i]:02X}, Neu=0x{new_data[i]:02X}")
                if i >= 5:  # Zeige nur erste 5 Unterschiede
                    logger.info(f"      ... ({differences - 5} weitere Unterschiede)")
                    break
    
    # Test 2: Mit Dithering (realistische Bedingung)
    logger.info("\n" + "=" * 80)
    logger.info("📊 Test 2: Bild mit Dithering (realistischer Fall)")
    logger.info("=" * 80)
    
    # Erstelle Graustufenbild und wende Dithering an
    gray_img = Image.new('L', (384, 100), 128)  # 50% Grau
    dithered_img = gray_img.convert('1', dither=Image.Dither.FLOYDSTEINBERG)
    
    logger.info("   Bild erstellt: 384x100px mit Floyd-Steinberg Dithering")
    
    # Alte Version (mit NEAREST resize - würde Dithering zerstören wenn resize nötig wäre)
    old_dither_data = old_image_to_printer_format(dithered_img)
    
    # Neue Version
    new_dither_data = new_image_to_printer_format(dithered_img)
    
    if old_dither_data and new_dither_data:
        logger.info(f"   Alte Version: {len(old_dither_data)} bytes")
        logger.info(f"   Neue Version: {len(new_dither_data)} bytes")
        
        if old_dither_data == new_dither_data:
            logger.info("   ✅ Beide Versionen identisch bei Dithering")
        else:
            dither_diff = sum(1 for a, b in zip(old_dither_data, new_dither_data) if a != b)
            logger.warning(f"   ⚠️ {dither_diff} unterschiedliche Bytes bei Dithering")
    
    # Fazit
    logger.info("\n" + "=" * 80)
    logger.info("🎯 FAZIT")
    logger.info("=" * 80)
    logger.info("\nHAUPTPROBLEM war wahrscheinlich:")
    logger.info("1. ❌ Resize mit Image.NEAREST statt LANCZOS")
    logger.info("   → Zerstört Dithering-Muster komplett")
    logger.info("2. ❌ Resize ZU SPÄT (in image_to_printer_format)")
    logger.info("   → Nach Dithering-Verarbeitung")
    logger.info("\nFIX:")
    logger.info("1. ✅ Resize in process_image_for_preview() mit LANCZOS")
    logger.info("2. ✅ Bild kommt bereits mit korrekter Breite an")
    logger.info("3. ✅ Explizite Pixel-Wert-Prüfung (0 vs. 255)")
    
    logger.info("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        compare_conversions()
    except Exception as e:
        logger.error(f"❌ Fehler: {e}")
        import traceback
        logger.error(traceback.format_exc())
