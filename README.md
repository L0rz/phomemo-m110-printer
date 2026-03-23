# 🏷️ Phomemo M110 Printer Controller

Web-basierter Druckserver für den Phomemo M110 Thermodrucker auf Raspberry Pi via Bluetooth.

## Features

### 🖨️ Drucken
- **Bilder**: PNG, JPEG, BMP, GIF, WebP — mit Live-Vorschau vor dem Druck
- **Text**: Konfigurierbarer Font, Größe und Ausrichtung
- **QR-Codes & Barcodes**: Inline via `#qr#Inhalt#qr#` und `#bar#Inhalt#bar#` Syntax
- **Print Queue**: Asynchrone Job-Verarbeitung mit Auto-Retry

### 📐 Label-Konfiguration
- **Label-Größen-Selector** im Web-UI: 40×30mm, 30×40mm, 50×30mm, 50×80mm, 25×25mm, etc.
- **X/Y-Offset Kalibrierung** mit persistenter Speicherung
- **Kalibrierungs-Muster** zum Ausrichten (Rand, Gitter, Ecken)
- Max. Druckbreite: 50mm (384px bei 203 DPI)

### 🎨 Bildverarbeitung
- Floyd-Steinberg Dithering (Threshold + Stärke konfigurierbar)
- Kontrast-Verstärkung
- Automatische Label-Anpassung mit Seitenverhältnis-Erhaltung
- QR-Code Aspect Ratio Korrektur für korrekte Quadrate auf dem Thermaldruck

### ⚡ Adaptive Druckübertragung
- **Line-by-Line Transfer**: Jede 48-Byte-Zeile einzeln gesendet
- **Adaptive Pausen**: Bit-Dichte pro Zeile bestimmt die Wartezeit — verhindert Bluetooth Buffer Overrun bei komplexen Bildern
- Auto-Reconnect bei Verbindungsabbruch

## Hardware

| Komponente | Details |
|---|---|
| Drucker | Phomemo M110 (Thermodruck, 203 DPI) |
| Verbindung | Bluetooth RFCOMM |
| Host | Raspberry Pi |
| Druckkopf | 384px breit, 48 Bytes/Zeile |

## Installation

```bash
# Dependencies
sudo apt install python3 python3-pip bluetooth bluez python3-dev libjpeg-dev

# Python-Pakete
pip3 install flask pillow qrcode python-barcode

# MAC-Adresse in config.py anpassen
nano config.py

# Starten
python3 main.py
```

Web-UI: `http://<pi-ip>:8080`

## API

| Endpoint | Methode | Beschreibung |
|---|---|---|
| `/api/status` | GET | Verbindungsstatus |
| `/api/settings` | GET/POST | Einstellungen lesen/schreiben |
| `/api/print-image` | POST | Bild drucken (FormData: image) |
| `/api/print-text` | POST | Text drucken (FormData: text) |
| `/api/print-text-with-codes` | POST | Text mit QR/Barcodes drucken |
| `/api/preview-image` | POST | Vorschau generieren |
| `/api/print-calibration` | POST | Kalibrierungsmuster drucken |
| `/api/label-sizes` | GET | Verfügbare Label-Größen |

### QR-Code & Barcode Syntax

```
#qr#https://example.com#qr#           → QR-Code
#qr:150#https://example.com#qr#       → QR-Code mit 150px Größe
#bar#1234567890128#bar#                → Barcode (EAN13)
#bar:code128#ABC-123#bar#              → Barcode (Code128)
```

## Konfiguration

Einstellungen werden in `printer_settings.json` persistent gespeichert:

```json
{
  "label_size": "40x30",
  "x_offset": 36,
  "y_offset": 0,
  "dither_threshold": 128,
  "dither_enabled": true,
  "dither_strength": 1.0,
  "contrast_boost": 1.0
}
```

## Dateistruktur

```
├── main.py               # Flask Server
├── printer_controller.py # Drucklogik + Bitmap-Übertragung
├── api_routes.py         # REST API Endpunkte
├── code_generator.py     # QR-Code & Barcode Generator
├── config.py             # Konfiguration + Label-Größen
├── web_template.py       # Web-Interface
├── calibration_tool.py   # Kalibrierungsmuster
└── printer_settings.json # Persistente Einstellungen
```

## Druckprotokoll

```
ESC @ (0x1B 0x40)        → Drucker Reset
GS v 0 (0x1D 0x76 0x30)  → Raster Bitmap Header
  + width_bytes (2B LE)   → 48 (0x30 0x00)
  + height (2B LE)        → z.B. 240 (0xF0 0x00)
  + image_data            → height × 48 Bytes (zeilenweise, adaptiv)
```

## Lizenz

MIT
