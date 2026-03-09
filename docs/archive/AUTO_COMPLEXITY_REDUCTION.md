# 🔧 AUTOMATISCHE KOMPLEXITÄTS-REDUKTION

## Schnellanleitung

### In `config.py` hinzufügen:

```python
# =================== AUTOMATISCHE KOMPLEXITÄTS-REDUKTION ===================

# Aktiviert automatische Reduktion bei hoher Komplexität
AUTO_REDUCE_COMPLEXITY = True

# Schwellwert: Ab welcher Komplexität soll reduziert werden? (Standard: 10%)
AUTO_REDUCE_THRESHOLD = 0.10  # 10% = Komplexe Bilder

# Reduktionsmethode
AUTO_REDUCE_METHOD = 'adaptive'  # 'adaptive', 'threshold', 'brightness'

# Adaptive Methode: Wählt automatisch die beste Reduktion
#   - <12%: Helligkeit leicht erhöhen
#   - 12-15%: Helligkeit stark erhöhen + leichtes Blur
#   - >15%: Threshold (kein Dithering)

# Threshold-Methode: Schwellwert für Schwarz/Weiß (80-200)
AUTO_REDUCE_THRESHOLD_VALUE = 140  # Höher = mehr Weiß = niedrigere Komplexität

# Brightness-Methode: Helligkeitsfaktor (1.0-2.0)
AUTO_REDUCE_BRIGHTNESS_FACTOR = 1.3  # 1.3 = 30% heller
```

### Im Code aktivieren (in `printer_controller.py`):

**Füge in `process_image_for_preview` ein (Zeile ~550):**

```python
# NACH dem Dithering, VOR dem Return:
if enable_dither:
    # ... Dithering-Code ...
    bw_img = img.convert('1', dither=Image.Dither.FLOYDSTEINBERG)
    
    # ============= AUTOMATISCHE KOMPLEXITÄTS-REDUKTION =============
    if self.settings.get('auto_reduce_complexity', AUTO_REDUCE_COMPLEXITY):
        bw_img = self._auto_reduce_complexity_if_needed(bw_img)
    # ===============================================================
```

**Füge neue Methode hinzu (nach `process_image_for_preview`):**

```python
def _auto_reduce_complexity_if_needed(self, img: Image.Image) -> Image.Image:
    """
    Automatische Komplexitäts-Reduktion wenn Bild zu komplex
    
    Args:
        img: Schwarz-Weiß PIL Image
        
    Returns:
        Optimiertes Image mit reduzierter Komplexität (falls nötig)
    """
    try:
        # Aktuelle Komplexität schätzen
        pixels = list(img.getdata())
        black_pixels = pixels.count(0)
        complexity = black_pixels / len(pixels)
        
        threshold = self.settings.get('auto_reduce_threshold', AUTO_REDUCE_THRESHOLD)
        
        if complexity < threshold:
            # Komplexität OK - keine Reduktion nötig
            logger.info(f"✅ Complexity OK: {complexity*100:.1f}% < {threshold*100:.1f}% threshold")
            return img
        
        # Komplexität zu hoch - Reduktion durchführen
        logger.warning(f"⚠️ High complexity detected: {complexity*100:.1f}%")
        logger.info(f"🔧 AUTO-REDUCING complexity...")
        
        method = self.settings.get('auto_reduce_method', AUTO_REDUCE_METHOD)
        
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
                from PIL import ImageFilter
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
                threshold_val = self.settings.get('auto_reduce_threshold_value', 140)
                result = gray_img.point(lambda x: 0 if x < threshold_val else 255, '1')
        
        elif method == 'threshold':
            # Einfacher Threshold
            logger.info("   → Using: Threshold method")
            gray_img = img.convert('L')
            threshold_val = self.settings.get('auto_reduce_threshold_value', 140)
            result = gray_img.point(lambda x: 0 if x < threshold_val else 255, '1')
        
        elif method == 'brightness':
            # Helligkeit erhöhen
            logger.info("   → Using: Brightness method")
            rgb_img = img.convert('RGB')
            factor = self.settings.get('auto_reduce_brightness_factor', 1.3)
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
        return img  # Fallback: Original zurückgeben
```

## ✅ FERTIG!

Jetzt wird **automatisch** die Komplexität reduziert wenn sie > 10% ist!

### Test:
```bash
# Server neu starten
python main.py

# Bild mit hoher Komplexität drucken
# → Wird automatisch optimiert!
```

### Logs zeigen:
```
⚠️ High complexity detected: 12.5%
🔧 AUTO-REDUCING complexity...
   → Using: Brightness +30% + Blur
✅ Complexity reduced: 12.5% → 7.2% (-5.3%)
```
