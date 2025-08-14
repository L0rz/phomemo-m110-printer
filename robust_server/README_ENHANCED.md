# Phomemo M110 Enhanced Edition

## 🎯 Übersicht der Implementierten Features

Die Enhanced Edition erweitert Ihren Phomemo M110 Drucker um folgende **tatsächlich implementierte** Features:

### ✨ Hauptfeatures

1. **🖼️ Schwarz-Weiß-Bildvorschau**
   - Live-Vorschau vor dem Drucken mit Base64-kodierter Anzeige
   - Floyd-Steinberg Dithering für bessere Graustufen-Konvertierung
   - Konfigurierbare Dithering-Schwellenwerte (0-255)
   - Dithering-Stärke-Anpassung (0.1-2.0)
   - Kontrast-Verstärkung (0.5-2.0)
   - Automatische Label-Anpassung auf 40×30mm (320×240px)

2. **📐 X/Y-Offset Konfiguration**
   - Konfigurierbare horizontale Verschiebung (0-100 Pixel)
   - Konfigurierbare vertikale Verschiebung (-50 bis +50 Pixel)
   - Standard: 0 Pixel für beide Achsen
   - Persistente Speicherung in JSON-Datei
   - Live-Test der Offset-Einstellungen mit Kalibrierungs-Mustern

3. **⚙️ Erweiterte Einstellungen**
   - Persistente Konfiguration in `printer_settings.json`
   - Verschiedene Bildanpassungs-Modi:
     - An Label anpassen (Seitenverhältnis beibehalten)
     - Volle Label-Größe (stretchen)
     - Zentriert zuschneiden
     - Zentriert mit Rand
   - Auto-Connect-Optionen für zuverlässige Bluetooth-Verbindung

4. **🎯 Kalibrierungs-Tools**
   - Multiple Kalibrierungs-Muster verfügbar:
     - Vollständiger Test (Rand + Gitter)
     - Nur Rand-Test
     - Nur Gitter-Test
     - Eck-Test für Positionierung
   - Quick-Test für aktuelle Offset-Einstellungen
   - Offset zurücksetzen auf 0/0

5. **🔄 Robuste Print-Queue**
   - Asynchrone Druckjob-Verarbeitung
   - Auto-Retry bei Fehlern (bis zu 3 Versuche)
   - Detaillierte Job-Statistiken
   - Immediate-Print und Queue-Modus

## 📂 Dateistruktur

```
robust_server/
├── main_enhanced.py              # Hauptserver mit Enhanced Features
├── printer_controller_enhanced.py # Erweiterte Printer-Logik mit Bildverarbeitung
├── api_routes_enhanced.py        # REST API mit Bildvorschau
├── web_template_enhanced.py      # Modernes Web-Interface
├── config_enhanced.py            # Erweiterte Konfiguration
├── calibration_tool.py           # Kalibrierungs-Muster-Generator
├── calibration_api.py            # Kalibrierungs-API (separates Modul)
├── install_enhanced.sh           # Installations-Skript
└── printer_settings.json         # Persistente Einstellungen (wird automatisch erstellt)
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

# Python-Pakete installieren
pip3 install flask pillow

# Optional für erweiterte Bildverarbeitung
pip3 install numpy

# MAC-Adresse in config_enhanced.py anpassen
nano config_enhanced.py
# Ändern Sie: PRINTER_MAC = "12:7E:5A:E9:E5:22"  # IHRE MAC-ADRESSE!

# Server starten
python3 main_enhanced.py
```

## 🎛️ Konfiguration

### Standard-Einstellungen

| Setting | Standard | Bereich | Beschreibung |
|---------|----------|---------|--------------|
| `x_offset` | 0 | 0-100 | Horizontale Verschiebung (Pixel) |
| `y_offset` | 0 | -50 bis +50 | Vertikale Verschiebung (Pixel) |
| `dither_threshold` | 128 | 0-255 | SW-Konvertierungs-Schwelle |
| `dither_enabled` | true | bool | Floyd-Steinberg Dithering |
| `dither_strength` | 1.0 | 0.1-2.0 | Dithering-Intensität |
| `contrast_boost` | 1.0 | 0.5-2.0 | Kontrast-Verstärkung |
| `fit_to_label_default` | true | bool | Auto-Label-Anpassung |
| `maintain_aspect_default` | true | bool | Seitenverhältnis beibehalten |

### Konfigurationsdatei (printer_settings.json)
```json
{
  "x_offset": 0,
  "y_offset": 0,
  "dither_threshold": 128,
  "dither_enabled": true,
  "dither_strength": 1.0,
  "contrast_boost": 1.0,
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
2. **Skalierung**: Anpassung nach gewähltem Modus
3. **Konvertierung**: RGB → Schwarz-Weiß mit konfigurierbarem Dithering
4. **Offset**: Anwendung von X/Y-Verschiebungen
5. **Vorschau**: Base64-kodierte Vorschau für Web-Interface
6. **Druck**: Konvertierung zu Drucker-Format mit Byte-Array

### Bildanpassungs-Modi
- **fit_aspect**: An Label anpassen (Seitenverhältnis beibehalten)
- **stretch_full**: Volle Label-Größe (stretchen)
- **crop_center**: Zentriert zuschneiden (volle Größe)
- **pad_center**: Zentriert mit Rand (volle Größe)

## 📐 Offset-System

### X-Offset (Horizontal)
- **Zweck**: Korrigiert horizontale Position
- **Standard**: 0 Pixel (keine Verschiebung)
- **Bereich**: 0-100 Pixel
- **Anwendung**: Verschiebt gesamtes Druckbild nach rechts

### Y-Offset (Vertikal)
- **Zweck**: Korrigiert vertikale Position
- **Standard**: 0 Pixel
- **Bereich**: -50 bis +50 Pixel
- **Anwendung**: Verschiebt Druckbild nach oben (+) oder unten (-)

### Kalibrierung
1. **Test drucken**: "Offsets testen" Button verwenden
2. **Messung**: Abweichung mit Lineal messen
3. **Anpassung**: X/Y-Offsets entsprechend justieren
4. **Speichern**: "💾 Einstellungen speichern" klicken

## 🔌 API-Endpoints

### Implementierte Endpoints

#### `GET /api/status`
Gibt Verbindungsstatus und Drucker-Info zurück

#### `GET /api/settings`
Gibt aktuelle Einstellungen zurück
```json
{
  "success": true,
  "settings": {
    "x_offset": 0,
    "y_offset": 0,
    "dither_threshold": 128,
    "dither_enabled": true
  }
}
```

#### `POST /api/settings`
Aktualisiert Drucker-Einstellungen
```javascript
{
  "x_offset": 40,
  "y_offset": 0,
  "dither_threshold": 128,
  "dither_enabled": true,
  "dither_strength": 1.0
}
```

#### `POST /api/preview-image`
Erstellt Schwarz-Weiß-Vorschau eines Bildes
```javascript
FormData: {
  image: File,
  fit_to_label: "true",
  maintain_aspect: "true",
  enable_dither: "true",
  dither_threshold: "128",
  dither_strength: "1.0",
  scaling_mode: "fit_aspect"
}
```

#### `POST /api/print-image`
Druckt ein Bild mit Vorschau-Verarbeitung
```javascript
FormData: {
  image: File,
  immediate: "false",
  fit_to_label: "true",
  maintain_aspect: "true",
  enable_dither: "true",
  dither_threshold: "128",
  scaling_mode: "fit_aspect"
}
```

#### `POST /api/print-text`
Druckt Text mit konfigurierbarer Ausrichtung
```javascript
FormData: {
  text: "Hello World",
  font_size: "22",
  immediate: "false",
  alignment: "center"  // left, center, right
}
```

#### `POST /api/print-calibration`
Druckt Kalibrierungs-Muster
```javascript
FormData: {
  pattern: "full",  // full, border, grid, corners
  width: "320",
  height: "240",
  immediate: "true"
}
```

#### `POST /api/test-offsets`
Testet aktuelle Offset-Einstellungen

#### `POST /api/reset-offsets`
Setzt X/Y-Offsets auf 0 zurück

## 🎨 Web-Interface Features

### Sections
1. **Konfigurationsbereich**: 
   - X/Y-Offset-Einstellungen mit Schiebereglern
   - Dithering-Optionen und Schwellenwerte
   - Bildanpassungs-Modi

2. **Bildvorschau**: 
   - Live-Vorschau mit Verarbeitungsinfo
   - Before/After-Vergleich
   - Detaillierte Bildstatistiken

3. **Kalibrierungs-Tools**: 
   - Verschiedene Testmuster
   - Quick-Test für Offsets
   - Reset-Funktionen

4. **Job-Queue**: 
   - Live-Anzeige der Druckjobs
   - Retry-Status und Fehlerinfo
   - Detaillierte Statistiken

### Keyboard Shortcuts
- `Ctrl+Enter`: Text sofort drucken
- `Ctrl+Shift+Enter`: Text in Queue einreihen
- `F5`: Verbindungsstatus aktualisieren

## 🔧 Fehlerbehebung

### Bildvorschau funktioniert nicht
```bash
# Pillow mit JPEG-Support neu installieren
pip3 install --upgrade pillow

# System-Dependencies prüfen
sudo apt install python3-dev libjpeg-dev zlib1g-dev
```

### Offsets werden nicht angewendet
1. Einstellungen mit "💾 Einstellungen speichern" speichern
2. `printer_settings.json` überprüfen: `cat printer_settings.json`
3. Bei Problemen Datei löschen: `rm printer_settings.json`

### Dithering-Probleme
- Schwellenwert anpassen (Standard: 128)
- Dithering-Stärke reduzieren (Standard: 1.0)
- Für einfache SW-Bilder Dithering deaktivieren

### Bluetooth-Verbindungsprobleme
```bash
# Bluetooth-Service neu starten
sudo systemctl restart bluetooth

# RFCOMM-Device prüfen
ls -la /dev/rfcomm*

# Pairing-Status prüfen
bluetoothctl devices
```

## 📊 Monitoring

### Health Check
```bash
curl http://localhost:8080/health
```
Gibt Status, Verbindung, Queue-Größe und Uptime zurück

### Service-Logs
```bash
# Entwicklungs-Logs
tail -f phomemo_server.log

# Wenn als Systemd-Service installiert
sudo journalctl -u phomemo-enhanced -f
```

## 🆕 Migration von Standard-Version

### Automatische Kompatibilität
Das Enhanced System ist rückwärtskompatibel:
- Bestehende Bluetooth-Verbindungen werden übernommen
- Alte Konfiguration wird automatisch migriert

### Manuelle Schritte
1. Standard-Version stoppen
2. Enhanced Version installieren
3. MAC-Adresse in `config_enhanced.py` anpassen
4. Server starten: `python3 main_enhanced.py`

## 🎯 Best Practices

### Bildoptimierung
- Verwenden Sie kontrastreiche Bilder
- Testen Sie verschiedene Dithering-Schwellenwerte (100-150 für dunkle Bilder, 128-180 für helle)
- Für Line-Art Dithering deaktivieren

### Offset-Kalibrierung
1. Drucken Sie "Vollständiger Test" für erste Kalibrierung
2. Messen Sie Abweichung mit Lineal (1mm ≈ 8 Pixel bei 203 DPI)
3. Adjustieren Sie Offsets entsprechend
4. Wiederholen Sie bis optimale Position erreicht

### Performance
- Nutzen Sie Queue-Modus für mehrere Jobs
- Auto-Connect für zuverlässige Verbindung aktivieren
- Bei großen Bildern Qualität vor Upload reduzieren

## 🔄 Updates

```bash
# Git Repository aktualisieren
git pull origin main

# Server neu starten
sudo systemctl restart phomemo-enhanced
# oder bei manueller Ausführung
python3 main_enhanced.py
```

## 📈 Roadmap & Geplante Features

### 🚧 **In Entwicklung / Geplant:**
- [ ] **🔳 QR-Code Generation** - Automatische QR-Code-Erstellung für URLs und Text
- [ ] **📦 Batch-Druck von Bildern** - Mehrere Bilder in einem Vorgang drucken
- [ ] **📋 Template-System für Labels** - Vordefinierte Label-Layouts und Vorlagen
- [ ] **🔌 REST API für externe Integration** - Vollständige API für Drittanbieter-Software
- [ ] **🖨️ Multi-Drucker-Support** - Verwaltung mehrerer Phomemo-Drucker gleichzeitig
- [ ] **💾 Job-Persistenz** - Druckjobs überleben Server-Neustarts
- [ ] **🎨 Erweiterte Bildfilter** - Zusätzliche Bildbearbeitungsoptionen
- [ ] **📊 Export-Funktionen** - Statistiken und Logs exportieren
- [ ] **🔔 Benachrichtigungen** - Push-Benachrichtigungen für Job-Status
- [ ] **🌐 Multi-Language Support** - Internationalisierung des Web-Interface

### 🎯 **Nächste Releases:**
- **v1.1**: QR-Code Generation und Template-System
- **v1.2**: Batch-Druck und erweiterte API
- **v1.3**: Multi-Drucker-Support
- **v2.0**: Vollständige Überarbeitung mit Plugin-System

### 💡 **Feature-Requests**
Haben Sie Ideen für neue Features? Erstellen Sie ein GitHub Issue oder kontaktieren Sie uns!

## 📞 Support

Bei Problemen:
1. **Logs prüfen**: `tail -f phomemo_server.log`
2. **Verbindung testen**: "🔧 Test Bluetooth" im Web-Interface
3. **Health Check**: `curl http://localhost:8080/health`
4. **GitHub Issues**: Melden Sie Bugs mit detailliertem Log-Output

## 📈 Technische Details

### Bildverarbeitung
- **DPI**: 203 (Label-Standard)
- **Label-Größe**: 40×30mm = 320×240 Pixel
- **Drucker-Breite**: 384 Pixel (48 Bytes pro Zeile)
- **Dithering**: Floyd-Steinberg Algorithmus
- **Formate**: PIL-kompatible Bildformate

### Offset-Berechnung
- **1mm** ≈ **8 Pixel** bei 203 DPI
- **X-Offset**: Verschiebt nach rechts (0-100px = 0-12.5mm)
- **Y-Offset**: Verschiebt vertikal (-50 bis +50px = -6.25 bis +6.25mm)
