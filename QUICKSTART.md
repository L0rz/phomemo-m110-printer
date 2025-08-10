## 📊 Technische Details

### Hardware-Spezifikationen
- **Drucker**: Phomemo M110
- **Auflösung**: 203 DPI
- **Druckbreite**: 48mm (384px)
- **Label-Format**: 40×30mm (320×240px)
- **Verbindung**: Bluetooth (rfcomm)

### Software-Architektur
- **Backend**: Python 3 + Flask
- **Frontend**: HTML5 + JavaScript
- **Bildverarbeitung**: Pillow (PIL)
- **Protokoll**: ESC/POS kompatibel

### Optimierungen
- **Segmentierung**: 2×100px für 30mm Labels
- **Caching**: Drucker-Initialisierung optimiert
- **Error-Handling**: Robuste Bluetooth-Verbindung
- **Feed-Control**: Minimaler Papiervorschub

## 🎨 Anpassungen

### Eigene Label-Größen
```python
# In phomemo_m110_printer.py
printer = PhomemoM110(
    PRINTER_MAC, 
    label_width_mm=50,   # Ihre Breite
    label_height_mm=25   # Ihre Höhe
)
```

### Custom Fonts
```python
# Eigene Schriftart laden
font_path = "/path/to/your/font.ttf"
font = ImageFont.truetype(font_path, font_size)
```

### API Integration
```bash
# Text drucken via curl
curl -X POST http://localhost:8080/api/print-text \
  -F "text=Hello World" \
  -F "font_size=20"

# Bild drucken via curl
curl -X POST http://localhost:8080/api/print-image \
  -F "image=@/path/to/image.png"
```

## 📈 Performance-Tipps

1. **Bluetooth-Optimierung**:
   - Drucker nah am Computer (< 2m)
   - Keine anderen Bluetooth-Geräte aktiv
   - USB-Bluetooth-Adapter für bessere Stabilität

2. **Bild-Optimierung**:
   - Schwarz/Weiß-Bilder verwenden
   - Auflösung 320×240px vorab anpassen
   - Kontrast maximieren

3. **Text-Optimierung**:
   - Kurze Zeilen bevorzugen
   - Schriftgröße 16-24px optimal
   - Max 4-5 Zeilen pro Label

## 🔄 Git-Workflow

```bash
# Änderungen vorbereiten
git add .
git commit -m "feat: Y-Offset Kalibrierung korrigiert"

# Branch erstellen
git checkout -b feature/neue-funktion

# Push to GitHub
git push origin main
```

## 📋 TODO / Roadmap

- [ ] QR-Code Generation
- [ ] Barcode-Support  
- [ ] Template-System
- [ ] Batch-Druck
- [ ] Drucker-Queue
- [ ] Config-File-Support
- [ ] Multi-Language Support
- [ ] Docker-Container

## 🧪 Testing

```bash
# Unit Tests (falls implementiert)
python3 -m pytest tests/

# Manueller Test-Workflow
1. Minimal-Test → ✅ 1 Label
2. Kalibrierung → ✅ Y-Offset funktioniert  
3. Volltest → ✅ 30mm in 2 Segmenten
4. Text-Druck → ✅ Automatische Skalierung
5. Bild-Druck → ✅ Aspect-Ratio erhalten
```

## 🏆 Features v2.0

### ✅ Gelöst
- Y-Offset funktioniert korrekt
- Nur 1 Label pro Test
- Segmentierter 30mm Volltest
- Optimierte Kalibrierung
- Standard X-Offset 72px (9mm)

### 🆕 Neu hinzugefügt
- `_send_image_block()` Hilfsfunktion
- Dynamische Bildhöhe für Kalibrierung
- Y-Offset Marker im Debug-Rahmen
- Erweiterte Fehlerbehandlung
- Performance-Optimierungen

## 📞 Support

Bei Problemen:
1. Issues auf GitHub erstellen
2. Logs in der Konsole prüfen
3. rfcomm-Verbindung testen
4. Hardware-Reset (Drucker aus/ein)

**Erfolgreich getestet mit**:
- Ubuntu 20.04 LTS
- Python 3.8+
- Phomemo M110
- Chrome/Firefox Browser
