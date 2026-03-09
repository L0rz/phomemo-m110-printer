# 🔧 Bitmap Fix - Quick Start

## 🎯 Was ist das Problem?

Text druckt perfekt, aber **Bilder** (besonders komplexe mit Dithering) haben Verschiebungen oder werden falsch gedruckt.

## 🚀 Schnellstart (3 Minuten)

### 1. Vergleichstest ausführen
```bash
python quick_comparison_test.py
```

**Das zeigt dir:**
- Ob deine PIL-Version 0/1 oder 0/255 zurückgibt
- Wo genau der Unterschied zwischen alt und neu liegt
- Ob das Hauptproblem das Resize-Timing ist

### 2. Fix testen (ohne Drucker)
```bash
python apply_bitmap_fix.py --test
```

**Erwartete Ausgabe:**
```
✅ Test 1 passed: 4800 bytes generated
   First byte: 0xFF (expected: 0xFF for 8 black pixels)
   Mid byte (pos 24): 0x00 (expected: 0x00 for 8 white pixels)
```

### 3. Backup erstellen
```bash
python apply_bitmap_fix.py --backup
```

### 4. Fix anwenden
```bash
python apply_bitmap_fix.py --apply
```

### 5. Server neu starten und testen
```bash
# Server neu starten
python main.py

# In anderem Terminal: Testdruck
curl -X POST http://localhost:5000/api/test-pattern
```

## 📋 Was wurde gefixt?

### Problem 1: Resize-Algorithmus
- **Alt**: `Image.NEAREST` → zerstört Dithering
- **Neu**: `Image.LANCZOS` → erhält Dithering

### Problem 2: Resize-Timing  
- **Alt**: Resize in `image_to_printer_format()` (zu spät)
- **Neu**: Resize in `process_image_for_preview()` (rechtzeitig)

### Problem 3: Pixel-Wert-Annahmen
- **Alt**: Implizite Annahme PIL gibt 0/1 zurück
- **Neu**: Explizite Prüfung auf 0/255

## 🧪 Tests

### Test 1: Vergleich Alt vs. Neu
```bash
python quick_comparison_test.py
```

### Test 2: Testmuster drucken
```python
from printer_controller import EnhancedPhomemoM110

printer = EnhancedPhomemoM110("DC:0D:30:90:23:C7")
printer.connect_bluetooth()
printer.print_test_pattern()
```

**Erwartetes Ergebnis:**
```
┌────────────────────────────────────┐
│████████        ████████████████████│  ← Links schwarz
│████████        ████████████████████│     Mitte weiß
│████████        ████████████████████│     Rechts schwarz
│████████        ████████████████████│
│────────────────────────────────────│  ← Horizontale Linie
│████████        ████████████████████│
│████████        ████████████████████│
└────────────────────────────────────┘
```

### Test 3: Einfaches Bild
```python
from PIL import Image

# Erstelle einfaches Testbild
img = Image.new('RGB', (320, 240), 'white')
# ... Zeichne etwas ...

# Drucke
printer.print_image_immediate(img)
```

### Test 4: Komplexes Bild mit Dithering
```python
# Foto laden und mit Dithering konvertieren
photo = Image.open('test_photo.jpg')
result = printer.process_image_for_preview(
    photo,
    fit_to_label=True,
    enable_dither=True
)

# Drucke
printer.print_image_immediate(photo, enable_dither=True)
```

## 🔄 Rollback

Falls Probleme auftreten:
```bash
python apply_bitmap_fix.py --rollback
```

## 📊 Wichtige Änderungen

### In `printer_controller.py`:

1. **`image_to_printer_format()`**
   ```python
   # NEU: Strikte Validierung
   if width != self.width_pixels:
       logger.error(f"Image must be exactly {self.width_pixels}px wide")
       return None
   
   # NEU: Explizite Pixel-Prüfung
   pixel_value = pixels[pixel_idx]
   is_black = (pixel_value == 0)  # PIL: 0 oder 255
   ```

2. **`process_image_for_preview()`**
   ```python
   # NEU: Resize mit LANCZOS statt NEAREST
   if width != target_width:
       img = img.resize((target_width, height), Image.Resampling.LANCZOS)
   ```

## ❓ FAQ

### Q: Muss ich etwas an der API ändern?
**A:** Nein! Die API bleibt gleich. Nur die interne Konvertierung wird gefixt.

### Q: Funktioniert Text-Druck noch?
**A:** Ja! Text funktionierte bereits perfekt und bleibt unverändert.

### Q: Was ist mit meinen Custom-Settings?
**A:** Bleiben alle erhalten! Der Fix ändert nur zwei Methoden.

### Q: Kann ich zwischen alt und neu wechseln?
**A:** Ja, mit `--rollback` kommst du zur alten Version zurück.

### Q: Wird meine Adaptive Speed Control behalten?
**A:** Ja! Die bleibt komplett erhalten und funktioniert weiterhin.

## 🐛 Troubleshooting

### Problem: "Image must be exactly 384px wide"
**Lösung:** Das Bild wird in `process_image_for_preview()` nicht korrekt skaliert.
```python
# Prüfe ob diese Zeile in process_image_for_preview() existiert:
target_width = self.width_pixels  # 384px statt self.label_width_px
```

### Problem: Bild sieht "verpixelt" aus
**Lösung:** Resize-Algorithmus prüfen:
```python
# FALSCH:
img.resize((width, height), Image.NEAREST)

# RICHTIG:
img.resize((width, height), Image.Resampling.LANCZOS)
```

### Problem: Dithering verschwindet
**Lösung:** Resize muss VOR dem Dithering erfolgen!
```python
# RICHTIGE Reihenfolge in process_image_for_preview():
# 1. Resize auf 384px mit LANCZOS
# 2. Dann Dithering anwenden
# 3. Dann zu image_to_printer_format()
```

### Problem: Testmuster druckt nicht korrekt
**Ursache:** Grundlegende Konvertierung fehlerhaft
```bash
# Führe Debug-Test aus:
python quick_comparison_test.py

# Prüfe die Ausgabe - soll zeigen:
# First byte: 0xFF (8 schwarze Pixel)
# Mid byte: 0x00 (8 weiße Pixel)
```

### Problem: Bilder haben noch Verschiebungen nach ~80 Zeilen
**Lösung:** Das war wahrscheinlich ein Timing-Problem:
```python
# Adaptive Speed Control sollte helfen:
# 1. Prüfe ob aktiviert: self.settings.get('adaptive_speed_enabled', True)
# 2. Erhöhe timing_multiplier für langsamere Übertragung:
printer.update_settings({'timing_multiplier': 1.5})
```

## 🎓 Technischer Hintergrund

### Warum funktionierte Text, aber keine Bilder?

**Text:**
- Klare Schwarz/Weiß-Bereiche
- Kein Dithering
- Resize hatte wenig Einfluss

**Bilder:**
- Komplexe Dithering-Muster
- `Image.NEAREST` zerstörte das Muster
- Resize zur falschen Zeit

### Was ist Dithering?

Dithering simuliert Graustufen durch geschickte Anordnung von schwarzen/weißen Pixeln:

```
Grauwert 50%:        Dithered:
█████████            █ █ █ █ █
█████████            █ █ █ █ █
█████████     →      █ █ █ █ █
█████████            █ █ █ █ █
```

**Image.NEAREST** zerstört dieses Muster beim Resize!

### Bit-Layout verstehen

```python
# Ein Byte = 8 Pixel
Byte:    0xFF
Binär:   11111111
Pixel:   ████████  (8 schwarze Pixel)

Byte:    0x00
Binär:   00000000
Pixel:   ········  (8 weiße Pixel)

Byte:    0xAA
Binär:   10101010
Pixel:   █·█·█·█·  (abwechselnd)
```

## 📈 Performance-Tipps

### 1. Adaptive Speed optimal nutzen
```python
# Für sehr einfache Bilder (Logo, Text):
printer.update_settings({
    'adaptive_speed_aggressive': True,
    'max_complexity_for_fast': 0.03  # 3% statt 2%
})

# Für komplexe Fotos:
printer.update_settings({
    'force_slow_for_complex': True,
    'min_complexity_for_slow': 0.06  # 6% statt 8%
})
```

### 2. Bild-Optimierung vor dem Druck
```python
# Kontrast erhöhen für bessere Druckqualität
printer.update_settings({
    'contrast_boost': 1.3,  # 30% mehr Kontrast
    'dither_strength': 1.2   # Stärkeres Dithering
})
```

### 3. Block-Größe anpassen
```python
# In send_bitmap() wird Block-Größe automatisch angepasst
# Aber du kannst timing_multiplier ändern:
printer.update_settings({
    'timing_multiplier': 1.2  # 20% langsamer = stabiler
})
```

## 🔗 Siehe auch

- **BITMAP_FIX_DOCUMENTATION.md** - Vollständige technische Dokumentation
- **printer_controller_fixed.py** - Die Fixed-Implementation
- **apply_bitmap_fix.py** - Automatisches Fix-Script
- **quick_comparison_test.py** - Vergleichs-Test

## 📞 Support

Bei Problemen:

1. ✅ Führe `quick_comparison_test.py` aus
2. ✅ Teste mit `printer.print_test_pattern()`
3. ✅ Aktiviere Debug-Logging:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```
4. ✅ Prüfe die ersten 100 Bytes der Ausgabe

## ✨ Zusammenfassung

### Vor dem Fix:
- ❌ Text: ✅ Perfekt
- ❌ Einfache Bilder: ✅ OK
- ❌ Komplexe Bilder: ❌ Verschiebungen

### Nach dem Fix:
- ✅ Text: ✅ Perfekt (unverändert)
- ✅ Einfache Bilder: ✅ Perfekt
- ✅ Komplexe Bilder: ✅ Perfekt mit Dithering

---

**Viel Erfolg! 🚀**
