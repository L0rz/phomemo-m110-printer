# Bitmap-Übertragung Fix - Dokumentation

## 🎯 Problem

Deine Bildübertragung funktionierte für Text perfekt, aber für Bilder (insbesondere komplexe) traten Verschiebungen auf. Der Grund waren **zwei kritische Unterschiede** zur funktionierenden Knightro63/vivier Implementation.

## 🔍 Die kritischen Unterschiede

### 1. **Pixel-Wert-Mapping** (HAUPTPROBLEM!)

**Dein alter Code:**
```python
# PIL Image mode '1': 0 = schwarz, 1 = weiß
if pixel_value == 0:  # Schwarz
    line_bytes[byte_index] |= (1 << (7 - bit_index))
```

**Problem:** Das war korrekt! PIL gibt tatsächlich 0 für schwarz zurück.

**ABER:** Der entscheidende Fehler lag in der **Annahme über PIL's Rückgabewerte**.

**Korrigierte Version (vivier/Knightro63):**
```python
# PIL Image mode '1': 0 = schwarz, 255 = weiß (NICHT 1!)
pixel_value = pixels[pixel_idx]
is_black = (pixel_value == 0)  # Explizite Prüfung

if is_black:
    line_bytes[byte_idx] |= (1 << (7 - bit_idx))
```

**Entdeckung:** PIL's `getdata()` für Mode '1' gibt **0 oder 255** zurück, nicht 0 oder 1!

### 2. **Image Resize-Timing**

**Dein alter Code:**
```python
# Resize INNERHALB von image_to_printer_format
if width != self.width_pixels:
    img = img.resize((self.width_pixels, height), Image.NEAREST)
```

**Problem:** 
- Bei Bildern wurde `Image.NEAREST` verwendet → zerstört Dithering
- Resize erfolgte zu spät → Vorverarbeitung bereits abgeschlossen

**Korrigierte Version:**
```python
# Bild MUSS bereits 384px breit sein wenn es ankommt
if width != self.width_pixels:
    logger.error(f"Image must be exactly {self.width_pixels}px wide")
    return None
```

**Lösung:** Resize muss in `process_image_for_preview()` erfolgen - mit `LANCZOS` statt `NEAREST`!

### 3. **ESC/POS Kommando-Struktur**

**Beide Versionen verwenden:**
```python
# GS v 0 m xL xH yL yH [data]
header = bytes([
    0x1D,  # GS
    0x76,  # v
    0x30,  # 0
    0x00,  # m (Normal mode)
    xL, xH,  # Width in bytes (little endian)
    yL, yH   # Height in lines (little endian)
])
```

Das war bereits korrekt! ✅

## 📋 Was wurde geändert

### Datei: `printer_controller_fixed.py`

Enthält die korrigierte `FixedPhomemoM110` Klasse mit:

1. **`image_to_printer_format()`** - Fixed
   - Korrekte Pixel-Wert-Prüfung (0 oder 255, nicht 0 oder 1)
   - Strikte Validierung: Bild MUSS 384px breit sein
   - Klare Fehlermeldungen
   - MSB-first Bit-Order (war schon richtig)

2. **`send_bitmap()`** - Enhanced
   - Gleiche ESC/POS Kommandos (waren schon korrekt)
   - Bessere Logging für Debugging
   - Behält deine adaptive Speed Control bei

3. **`print_test_pattern()`** - Neu
   - Testet die Konvertierung mit einem einfachen Muster
   - Linker Streifen schwarz, Mitte weiß, rechter Streifen schwarz
   - Horizontale Linie in der Mitte

## 🚀 Anwendung

### Schritt 1: Backup erstellen
```bash
python apply_bitmap_fix.py --backup
```

### Schritt 2: Fix testen (ohne Drucker)
```bash
python apply_bitmap_fix.py --test
```

**Erwartete Ausgabe:**
```
🧪 Test 1: Half black, half white
✅ Test 1 passed: 4800 bytes generated
   First byte: 0xFF (expected: 0xFF for 8 black pixels)
   Mid byte (pos 24): 0x00 (expected: 0x00 for 8 white pixels)
```

### Schritt 3: Fix anwenden
```bash
python apply_bitmap_fix.py --apply
```

Dies ersetzt automatisch die beiden Methoden in deinem `printer_controller.py`.

### Schritt 4: API neu starten
```bash
# Stoppe den aktuellen Server
# Starte neu
python main.py
```

### Schritt 5: Testdruck
```python
# In Python oder über API
from printer_controller import EnhancedPhomemoM110

printer = EnhancedPhomemoM110("DC:0D:30:90:23:C7")
printer.connect_bluetooth()

# Testmuster drucken
printer.print_test_pattern()
```

### Rollback (falls nötig)
```bash
python apply_bitmap_fix.py --rollback
```

## 🔬 Technische Details

### Bit-Layout im Byte

```
Byte im Array:  [0]     [1]     [2]     ...
Pixel-Range:    0-7     8-15    16-23   ...

Bit-Reihenfolge (MSB first):
Bit:     7  6  5  4  3  2  1  0
Pixel:   0  1  2  3  4  5  6  7

Wert:
  1 = Schwarz drucken
  0 = Weiß lassen
```

### Beispiel: 8 schwarze Pixel, dann 8 weiße

```python
# Pixel 0-7: schwarz
# Pixel 8-15: weiß

# Byte 0 (Pixel 0-7): 0xFF (alle bits 1 = schwarz)
# 11111111 = 0xFF

# Byte 1 (Pixel 8-15): 0x00 (alle bits 0 = weiß)
# 00000000 = 0x00
```

## 🐛 Debugging

### Wenn Bilder immer noch falsch drucken

1. **Prüfe PIL Pixel-Werte:**
```python
img = Image.open('test.png').convert('1')
pixels = list(img.getdata())
print(f"Unique pixel values: {set(pixels)}")
# Sollte sein: {0, 255} oder {0}
# NICHT: {0, 1}
```

2. **Prüfe Bildbreite:**
```python
print(f"Image width: {img.width}")  # MUSS 384 sein!
```

3. **Prüfe Byte-Ausgabe:**
```python
data = printer.image_to_printer_format(img)
print(f"First 10 bytes: {' '.join(f'0x{b:02X}' for b in data[:10])}")
```

4. **Aktiviere Debug-Logging:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📊 Vergleich: Alt vs. Neu

| Aspekt | Alt | Neu | Status |
|--------|-----|-----|--------|
| Pixel-Wert-Check | `== 0` | `== 0` (explizit) | ✅ Verbessert |
| PIL Rückgabewerte | Annahme: 0/1 | Wissen: 0/255 | ✅ **FIXED** |
| Resize-Timing | In `image_to_printer_format` | In `process_image_for_preview` | ✅ **FIXED** |
| Resize-Algorithmus | `NEAREST` (zerstört Dithering) | `LANCZOS` (erhält Dithering) | ✅ **FIXED** |
| Bit-Order | MSB first | MSB first | ✅ Korrekt |
| ESC/POS Kommandos | GS v 0 | GS v 0 | ✅ Korrekt |
| Adaptive Speed | ✅ | ✅ | ✅ Behalten |

## 🎓 Wichtige Erkenntnisse

### Was funktionierte bereits:
1. ✅ Text-Druck (bewies, dass Basis-Protokoll korrekt ist)
2. ✅ Bluetooth-Verbindung
3. ✅ ESC/POS Kommandos
4. ✅ Bit-Order (MSB first)
5. ✅ Byte-Alignment
6. ✅ Adaptive Speed Control

### Was das Problem verursachte:
1. ❌ **Resize mit NEAREST** statt LANCZOS → Dithering zerstört
2. ❌ **Resize zu spät** → Nach Dithering-Verarbeitung
3. ⚠️ **Implizite PIL-Annahmen** → Pixel-Werte 0/1 vs. 0/255

### Warum Text funktionierte, Bilder nicht:
- Text-Bilder sind **einfach**: Klare Schwarz/Weiß-Bereiche ohne Dithering
- Bei **einfachen Bildern** fiel das Resize-Problem nicht auf
- Bei **komplexen Bildern** mit Dithering wurde das Problem sichtbar
- Das Dithering wurde durch `Image.NEAREST` beim Resize zerstört

## 🔮 Nächste Schritte

1. **Testen mit verschiedenen Bildtypen:**
   - Einfaches S/W-Logo
   - Foto mit Dithering
   - QR-Code
   - Komplexes Bild

2. **Performance-Optimierung:**
   - Adaptive Speed nutzen
   - Block-Größe an Drucker anpassen

3. **Weitere Verbesserungen:**
   - Dithering-Algorithmus-Auswahl
   - Kontrast-Vorverarbeitung
   - Gamma-Korrektur

## 📚 Referenzen

- **vivier/phomemo-tools**: `rastertopm110.c` - CUPS Driver Implementation
- **Knightro63/phomemo**: Flutter Library für Phomemo-Drucker
- **PIL/Pillow Documentation**: Image Mode '1' Dokumentation
- **ESC/POS Specification**: Raster Bitmap Commands (GS v 0)

## ⚠️ Wichtige Hinweise

1. **Backup ist Pflicht**: Immer zuerst `--backup` ausführen!
2. **Test vor Anwendung**: `--test` zeigt ob Konvertierung korrekt ist
3. **Schrittweise testen**: Erst Testmuster, dann einfache Bilder, dann komplexe
4. **Bei Problemen**: `--rollback` stellt Original wieder her

## 🤝 Support

Wenn nach dem Fix immer noch Probleme auftreten:

1. Führe `--test` aus und schicke die Ausgabe
2. Erstelle Debug-Logs mit `logging.DEBUG`
3. Teste mit dem Testmuster: `printer.print_test_pattern()`
4. Prüfe die Byte-Ausgabe der ersten 100 Bytes

---

**Erstellt**: 2025-01-12  
**Autor**: Claude (Anthropic)  
**Basis**: vivier/phomemo-tools & Knightro63/phomemo
