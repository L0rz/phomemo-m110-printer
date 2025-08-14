# Phomemo M110 Enhanced Edition - Neue Features

## 🎯 Übersicht der Erweiterungen

Die Enhanced Edition erweitert Ihren Phomemo M110 Drucker um folgende Features:

### ✨ Hauptfeatures

1. **🖼️ Schwarz-Weiß-Bildvorschau**
   - Live-Vorschau vor dem Drucken
   - Floyd-Steinberg Dithering für bessere Qualität
   - Konfigurierbare Schwellenwerte
   - Automatische Label-Anpassung (40×30mm)

2. **📐 X-Offset Konfiguration**
   - Konfigurierbare horizontale Verschiebung (0-100 Pixel)
   - Standard: 40 Pixel Offset
   - Persistente Speicherung der Einstellungen
   - Live-Test der Offset-Einstellungen

3. **⚙️ Erweiterte Konfiguration**
   - Persistente Einstellungen in JSON-Datei
   - Y-Offset für vertikale Anpassung (-50 bis +50 Pixel)
   - Dithering-Schwellenwert konfigurierbar
   - Auto-Connect-Optionen

4. **🎯 Erweiterte Kalibrierung**
   - Multiple Kalibrierungs-Muster (Gitter, Linien, Volltest)
   - Konfigurierbare Testmuster-Größen
   - Quick-Test für aktuelle Offsets
   - Visuelle Kalibrierungs-Hilfen

## 📂 Dateistruktur

```
robust_server/
├── main_enhanced.py              # Hauptserver mit neuen Features
├── printer_controller_enhanced.py # Erweiterte Printer-Logik
├── api_routes_enhanced.py        # REST API mit Bildverarbeitung
├── web_template_enhanced.py      # Modernes Web-Interface
├── config_enhanced.py            # Erweiterte Konfiguration
├── install_enhanced.sh           # Installations-Skript
└── printer_settings.json         # Persistente Einstellungen (wird erstellt)
```

## 🚀 Installation

### Schnelle Installation
```bash
chmod +x install_enhanced.sh
./install_enhanced.sh
```

### Manuelle Installation
```bash
# Dependencies installieren
sudo apt install python3 python3-pip bluetooth bluez python3-dev libjpeg-dev

# Python-Pakete
pip3 install flask pillow

# MAC-Adresse in config_enhanced.py anpassen
nano config_enhanced.py

# Server starten
python3 main_enhanced.py
```

## 🎛️ Konfiguration

### Standard-Einstellungen

| Setting | Standard | Bereich | Beschreibung |
|---------|----------|---------|--------------|
| `x_offset` | 40 | 0-100 | Horizontale Verschiebung (Pixel) |
| `y_offset` | 0 | -50 bis +50 | Vertikale Verschiebung (Pixel) |
| `dither_threshold` | 128 | 0-255 | SW-Konvertierungs-Schwelle |
| `dither_enabled` | true | bool | Floyd-Steinberg Dithering |
| `fit_to_label_default` | true | bool | Auto-Label-Anpassung |
| `maintain_aspect_default` | true | bool | Seitenverhältnis beibehalten |

### Konfigurationsdatei
```json
{
  "x_offset": 40,
  "y_offset": 0,
  "dither_threshold": 128,
  "dither_enabled": true,
  "fit_to_label_default": true,
  "maintain_aspect_default": true,
  "auto_connect": true
}
```

## 🖼️ Bildverarbeitung

### Unterstützte Formate
- PNG, JPEG, JPG, BMP, GIF, WebP
- Maximum: 10MB Upload-Größe

### Verarbeitungs-Pipeline
1. **Upload**: Datei-Validierung und Größenprüfung
2. **Skalierung**: Anpassung an Label-Größe (320×240px)
3. **Konvertierung**: RGB → Schwarz-Weiß mit Dithering
4. **Offset**: Anwendung von X/Y-Verschiebungen
5. **Vorschau**: Base64-kodierte Vorschau für Web
6. **Druck**: Konvertierung zu Drucker-Format

### Bildoptionen
- **An Label anpassen**: Skaliert auf 40×30mm
- **Seitenverhältnis**: Behält Original-Proportionen bei
- **Dithering**: Floyd-Steinberg für bessere Graustufen

## 📐 Offset-System

### X-Offset (Horizontal)
- **Zweck**: Korrigiert horizontale Position
- **Standard**: 40 Pixel (≈5mm bei 203 DPI)
- **Anwendung**: Verschiebt gesamtes Druckbild nach rechts

### Y-Offset (Vertikal)
- **Zweck**: Korrigiert vertikale Position
- **Standard**: 0 Pixel
- **Bereich**: -50 bis +50 Pixel
- **Anwendung**: Verschiebt Druckbild nach oben (+) oder unten (-)

### Kalibrierung
1. **Test drucken**: Verwenden Sie "Offsets testen"
2. **Messung**: Messen Sie Abweichung mit Lineal
3. **Anpassung**: Justieren Sie X/Y-Offsets entsprechend
4. **Speichern**: Einstellungen werden persistent gespeichert

## 🔌 API-Erweiterungen

### Neue Endpoints

#### `POST /api/preview-image`
Erstellt Schwarz-Weiß-Vorschau eines Bildes
```javascript
FormData: {
  image: File,
  fit_to_label: boolean,
  maintain_aspect: boolean,
  enable_dither: boolean
}
```

#### `POST /api/settings`
Aktualisiert Drucker-Einstellungen
```javascript
{
  "x_offset": 40,
  "y_offset": 0,
  "dither_threshold": 128,
  "dither_enabled": true
}
```

#### `GET /api/settings`
Gibt aktuelle Einstellungen zurück

#### `POST /api/test-offsets`
Testet aktuelle Offset-Einstellungen mit Kalibrierungs-Muster

## 🎨 Web-Interface

### Neue Sections
1. **Konfigurationsbereich**: Offset-Einstellungen und Optionen
2. **Bildvorschau**: Live-Vorschau mit Verarbeitungsinfo
3. **Erweiterte Statistiken**: Detaillierte Job-Statistiken
4. **Kalibrierungs-Tools**: Multiple Test-Muster

### Keyboard Shortcuts
- `Ctrl+Enter`: Text sofort drucken
- `Ctrl+Shift+Enter`: Text in Queue einreihen
- `F5`: Verbindungsstatus aktualisieren

### Responsive Design
- Mobile-optimiert
- Tooltips für alle Einstellungen
- Live-Updates der Statistiken
- Auto-Refresh der Queue

## 🔧 Fehlerbehebung

### Bildvorschau funktioniert nicht
```bash
# Pillow neu installieren
pip3 install --upgrade pillow

# System-Dependencies prüfen
sudo apt install python3-dev libjpeg-dev zlib1g-dev
```

### Offsets werden nicht angewendet
1. Einstellungen speichern mit "💾 Einstellungen speichern"
2. Server neu starten: `sudo systemctl restart phomemo-enhanced`
3. Konfigurationsdatei prüfen: `cat printer_settings.json`

### Dithering-Probleme
- Schwellenwert anpassen (Standard: 128)
- Dithering deaktivieren für einfache Schwarz-Weiß-Bilder
- Originalbilder mit gutem Kontrast verwenden

## 📊 Monitoring

### Health Check
```bash
curl http://localhost:8080/health
```

### Service Status
```bash
sudo systemctl status phomemo-enhanced
sudo journalctl -u phomemo-enhanced -f
```

### Logs
- Server-Log: `phomemo_server.log`
- Systemd-Log: `journalctl -u phomemo-enhanced`

## 🆕 Migration von alter Version

### Automatische Migration
Das Enhanced System ist rückwärtskompatibel und übernimmt automatisch:
- Bestehende Bluetooth-Verbindungen
- MAC-Adresse aus alter Konfiguration

### Manuelle Schritte
1. Alte Version stoppen
2. Enhanced Version installieren
3. MAC-Adresse in `config_enhanced.py` übertragen
4. Settings nach Bedarf anpassen

## 🎯 Best Practices

### Bildoptimierung
- Verwenden Sie kontrastreiche Bilder
- Bevorzugen Sie einfache Schwarz-Weiß-Grafiken
- Testen Sie verschiedene Dithering-Schwellenwerte

### Offset-Kalibrierung
- Verwenden Sie "Vollständiger Test" für genaue Kalibrierung
- Messen Sie mit Lineal für präzise Anpassung
- Dokumentieren Sie optimale Settings für Ihr Setup

### Performance
- Große Bilder vor Upload verkleinern
- Queue für mehrere Jobs verwenden
- Auto-Connect für zuverlässige Verbindung

## 📞 Support

Bei Problemen:
1. Logs prüfen: `sudo journalctl -u phomemo-enhanced -f`
2. Verbindung testen: "🔧 Test Bluetooth" im Web-Interface
3. GitHub Issues: Melden Sie Bugs mit Log-Output

## 🔄 Updates

Das Enhanced System unterstützt rolling Updates:
```bash
git pull origin main
sudo systemctl restart phomemo-enhanced
```

## 📈 Roadmap

Geplante Features:
- [ ] QR-Code Generation
- [ ] Batch-Druck von Bildern
- [ ] Template-System für Labels
- [ ] REST API für externe Integration
- [ ] Multi-Drucker-Support
