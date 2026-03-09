"""
Automatische Komplexitäts-Reduktion für Phomemo M110
Wird von printer_controller.py verwendet
"""

import logging
from PIL import Image, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)


def auto_reduce_complexity_if_needed(img: Image.Image, settings: dict) -> Image.Image:
    """
    Automatische Komplexitäts-Reduktion wenn Bild zu komplex
    
    Args:
        img: Schwarz-Weiß PIL Image (mode '1')
        settings: Dictionary mit Einstellungen
        
    Returns:
        Optimiertes Image mit reduzierter Komplexität (falls nötig)
    """
    try:
        # Aktuelle Komplexität schätzen
        pixels = list(img.getdata())
        black_pixels = pixels.count(0)
        complexity = black_pixels / len(pixels)
        
        threshold = settings.get('auto_reduce_threshold', 0.10)
        
        if complexity < threshold:
            # Komplexität OK - keine Reduktion nötig
            logger.info(f"✅ Complexity OK: {complexity*100:.1f}% < {threshold*100:.1f}% threshold")
            return img
        
        # Komplexität zu hoch - Reduktion durchführen
        logger.warning(f"⚠️ High complexity detected: {complexity*100:.1f}%")
        logger.info(f"🔧 AUTO-REDUCING complexity...")
        
        method = settings.get('auto_reduce_method', 'adaptive')
        
        if method == 'adaptive':
            # Adaptive Reduktion basierend auf Komplexität
            if complexity < 0.12:  # 10-12%: Leichte Reduktion
                logger.info("   → Using: Brightness +20%")
                # Zurück zu RGB für Bearbeitung
                rgb_img = img.convert('RGB')
                enhancer = ImageEnhance.Brightness(rgb_img)
                rgb_img = enhancer.enhance(1.2)
                # Wieder zu S/W mit Dithering
                result = rgb_img.convert('1', dither=Image.Dither.FLOYDSTEINBERG)
                
            elif complexity < 0.15:  # 12-15%: Mittlere Reduktion
                logger.info("   → Using: Brightness +30% + Blur")
                rgb_img = img.convert('RGB')
                # Helligkeit
                enhancer = ImageEnhance.Brightness(rgb_img)
                rgb_img = enhancer.enhance(1.3)
                # Leichtes Blur
                rgb_img = rgb_img.filter(ImageFilter.GaussianBlur(radius=0.8))
                result = rgb_img.convert('1', dither=Image.Dither.FLOYDSTEINBERG)
                
            else:  # >15%: Aggressive Reduktion
                logger.info("   → Using: Threshold (no dithering)")
                # Threshold ohne Dithering
                rgb_img = img.convert('RGB')
                enhancer = ImageEnhance.Brightness(rgb_img)
                rgb_img = enhancer.enhance(1.4)
                gray_img = rgb_img.convert('L')
                threshold_val = settings.get('auto_reduce_threshold_value', 140)
                result = gray_img.point(lambda x: 0 if x < threshold_val else 255, '1')
        
        elif method == 'threshold':
            # Einfacher Threshold
            logger.info("   → Using: Threshold method")
            gray_img = img.convert('L')
            threshold_val = settings.get('auto_reduce_threshold_value', 140)
            result = gray_img.point(lambda x: 0 if x < threshold_val else 255, '1')
        
        elif method == 'brightness':
            # Helligkeit erhöhen
            logger.info("   → Using: Brightness method")
            rgb_img = img.convert('RGB')
            factor = settings.get('auto_reduce_brightness_factor', 1.3)
            enhancer = ImageEnhance.Brightness(rgb_img)
            rgb_img = enhancer.enhance(factor)
            result = rgb_img.convert('1', dither=Image.Dither.FLOYDSTEINBERG)
        
        else:
            logger.warning(f"Unknown method '{method}', skipping reduction")
            return img
        
        # Neue Komplexität prüfen
        new_pixels = list(result.getdata())
        new_black = new_pixels.count(0)
        new_complexity = new_black / len(new_pixels)
        
        reduction = (complexity - new_complexity) * 100
        logger.info(f"✅ Complexity reduced: {complexity*100:.1f}% → {new_complexity*100:.1f}% (-{reduction:.1f}%)")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Auto-reduce complexity error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return img  # Fallback: Original zurückgeben
