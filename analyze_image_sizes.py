#!/usr/bin/env python3
"""
BILDGROSSEN-ANALYSE
Prüft die ursprüngliche PNG-Größe und was mit ihr passiert
"""

import os
from PIL import Image
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

def analyze_image_sizes():
    """Analysiert die Bildgrößen-Transformation"""
    
    test_png_path = "2025-08-15 16_49_38-Kamera (Benutzerdefiniert).png"
    
    if not os.path.exists(test_png_path):
        logger.error(f"❌ PNG not found: {test_png_path}")
        return
    
    # Original PNG laden
    original_img = Image.open(test_png_path)
    logger.info(f"📷 ORIGINAL PNG:")
    logger.info(f"   Size: {original_img.size} ({original_img.width} x {original_img.height})")
    logger.info(f"   Mode: {original_img.mode}")
    logger.info(f"   Format: {original_img.format}")
    
    # Zu Schwarz-Weiß konvertieren
    if original_img.mode != '1':
        gray_img = original_img.convert('L')
        bw_img = gray_img.convert('1')
    else:
        bw_img = original_img
    
    logger.info(f"📷 NACH B&W KONVERTIERUNG:")
    logger.info(f"   Size: {bw_img.size} ({bw_img.width} x {bw_img.height})")
    logger.info(f"   Mode: {bw_img.mode}")
    
    # Was passiert beim Resize auf 384px?
    target_width = 384
    
    if bw_img.width != target_width:
        logger.info(f"🔧 RESIZE TRANSFORMATION:")
        logger.info(f"   Original: {bw_img.width} x {bw_img.height}")
        
        # Test verschiedene Resize-Modi
        resize_modes = [
            ("NEAREST", Image.NEAREST),
            ("LANCZOS", Image.LANCZOS),
            ("BILINEAR", Image.BILINEAR),
            ("BICUBIC", Image.BICUBIC),
        ]
        
        for mode_name, mode in resize_modes:
            resized = bw_img.resize((target_width, bw_img.height), mode)
            logger.info(f"   {mode_name:8s}: {bw_img.width}x{bw_img.height} → {resized.width}x{resized.height}")
            
            # Berechne Skalierungsfaktor
            scale_factor = target_width / bw_img.width
            logger.info(f"              Scale factor: {scale_factor:.3f}x")
            
            if scale_factor > 1:
                logger.info(f"              → IMAGE STRETCHED by {scale_factor:.1f}x")
            elif scale_factor < 1:
                logger.info(f"              → IMAGE COMPRESSED by {1/scale_factor:.1f}x")
            else:
                logger.info(f"              → NO SCALING NEEDED")
        
        logger.info(f"")
        logger.info(f"🎯 CRITICAL ANALYSIS:")
        
        if bw_img.width < target_width:
            stretch_factor = target_width / bw_img.width
            logger.info(f"   Your image is STRETCHED by {stretch_factor:.1f}x horizontally!")
            logger.info(f"   Original width: {bw_img.width}px")
            logger.info(f"   Printer width:  {target_width}px")
            logger.info(f"   → This could introduce artifacts and increase complexity!")
            
        elif bw_img.width > target_width:
            compress_factor = bw_img.width / target_width
            logger.info(f"   Your image is COMPRESSED by {compress_factor:.1f}x horizontally!")
            logger.info(f"   Original width: {bw_img.width}px")
            logger.info(f"   Printer width:  {target_width}px")
            logger.info(f"   → This reduces detail but may simplify complexity")
        
        else:
            logger.info(f"   ✅ Your image width exactly matches printer width!")
    
    else:
        logger.info(f"✅ NO RESIZE NEEDED - image already {target_width}px wide")
    
    # Komplexitäts-Vergleich
    logger.info(f"")
    logger.info(f"🔍 COMPLEXITY IMPACT OF RESIZING:")
    
    # Original Komplexität
    original_pixels = list(bw_img.getdata())
    original_black = sum(1 for p in original_pixels if p == 0)
    original_complexity = original_black / len(original_pixels) * 100
    
    logger.info(f"   Original complexity: {original_complexity:.1f}%")
    
    # Nach Resize
    if bw_img.width != target_width:
        resized_img = bw_img.resize((target_width, bw_img.height), Image.NEAREST)
        resized_pixels = list(resized_img.getdata())
        resized_black = sum(1 for p in resized_pixels if p == 0)
        resized_complexity = resized_black / len(resized_pixels) * 100
        
        logger.info(f"   Resized complexity:  {resized_complexity:.1f}%")
        logger.info(f"   Complexity change:   {resized_complexity - original_complexity:+.1f}%")
        
        if resized_complexity > original_complexity:
            logger.warning(f"   ⚠️ RESIZE INCREASES COMPLEXITY!")
        elif resized_complexity < original_complexity:
            logger.info(f"   ✅ Resize reduces complexity")
        else:
            logger.info(f"   → Complexity unchanged")
    
    # Alternative Ansätze vorschlagen
    logger.info(f"")
    logger.info(f"💡 OPTIMIZATION SUGGESTIONS:")
    
    if bw_img.width != target_width:
        logger.info(f"1. Pre-scale image to exactly 384px before printing")
        logger.info(f"2. Use different resize algorithm (LANCZOS vs NEAREST)")
        logger.info(f"3. Apply image processing BEFORE resize to reduce complexity")
        logger.info(f"4. Consider maintaining aspect ratio with padding instead of stretching")
    
    # Zeige konkrete Resize-Auswirkung
    if bw_img.width != target_width:
        logger.info(f"")
        logger.info(f"🔬 PIXEL-LEVEL IMPACT:")
        logger.info(f"   Original: {bw_img.width} pixels → {len(original_pixels)} total pixels")
        
        resized_img = bw_img.resize((target_width, bw_img.height), Image.NEAREST)
        resized_pixels = list(resized_img.getdata())
        
        logger.info(f"   Resized:  {resized_img.width} pixels → {len(resized_pixels)} total pixels")
        logger.info(f"   Pixel change: {len(resized_pixels) - len(original_pixels):+d} pixels")
        
        # Zeige erste paar Zeilen als Beispiel
        bytes_per_line = 48
        pixels_per_line = 384
        
        if len(resized_pixels) >= pixels_per_line:
            first_line = resized_pixels[:pixels_per_line]
            black_in_first_line = sum(1 for p in first_line if p == 0)
            logger.info(f"   First line: {black_in_first_line}/{pixels_per_line} black pixels ({black_in_first_line/pixels_per_line*100:.1f}%)")

def main():
    logger.info("🔍 BILDGROSSEN-ANALYSE")
    logger.info("=" * 60)
    logger.info("Analysiert was mit deinem PNG beim Resize passiert")
    logger.info("=" * 60)
    
    analyze_image_sizes()
    
    logger.info("")
    logger.info("📋 ZUSAMMENFASSUNG:")
    logger.info("Wenn dein Bild gestreckt wird, kann das die Komplexität erhöhen!")
    logger.info("Wenn es komprimiert wird, kann das die Komplexität reduzieren!")

if __name__ == "__main__":
    main()
