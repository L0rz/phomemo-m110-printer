# 🏷️ Phomemo M110 Printer Controller

[🇩🇪 Deutsch](README.md) • **[🇬🇧 English](README.en.md)**

Web-based print server and Android app for the Phomemo M110 thermal label printer via Bluetooth.

---

## Features

### 🖨️ Printing
- **Images**: PNG, JPEG, BMP, GIF, WebP — with live pre-print preview
- **Text**: Configurable font, size, and alignment
- **QR Codes & Barcodes**: Inline via `#qr#content#qr#` and `#bar#content#bar#` syntax
- **Print Queue**: Asynchronous background job processing with auto-retry

### 📐 Label Configuration
- **Label Size Selector** in Web UI & Android App: 40×30mm, 30×40mm, 50×30mm, 50×80mm, 25×25mm, etc.
- **X/Y Offset Calibration** with persistent storage
- **Calibration Patterns** for alignment (borders, grids, corners)
- Max print width: 50mm (384px at 203 DPI)

### 🎨 Image Processing
- Floyd-Steinberg dithering (configurable threshold and strength)
- Contrast enhancement
- Automatic label fitting preserving aspect ratio
- QR code aspect ratio correction for perfect squares on thermal output

### ⚡ Adaptive Print Streaming
- **Line-by-Line Transfer**: Each 48-byte line sent individually
- **Adaptive Pauses**: Bit density per line dynamically determines wait time — prevents Bluetooth buffer overrun during dense prints
- Auto-reconnect on connection loss

---

## Hardware Compatibility

| Component | Details |
|---|---|
| **Printer** | Phomemo M110 (Thermal, 203 DPI) |
| **Connection** | Bluetooth RFCOMM / SPP |
| **Host** | Raspberry Pi, Linux PC, or Android Device |
| **Printhead** | 384px width, 48 Bytes/line |

---

## Installation (Python Web Server)

```bash
# System dependencies (Debian/Ubuntu/Raspberry Pi OS)
sudo apt install python3 python3-pip bluetooth bluez python3-dev libjpeg-dev

# Python packages
pip3 install flask pillow qrcode python-barcode

# Adjust printer MAC address in config.py
nano config.py

# Start the server
python3 main.py
```

Web UI: `http://<host-ip>:8080`

---

## 📱 Android App

The repository includes a native Android app in `android-app/`:
- Instant Bluetooth connection to paired M110 printers
- Real-time text, barcode, QR code, and image rendering
- OpenAI DALL-E / GPT pictogram generation
- Local label gallery with deduplication and re-printing
- Automated CI build: check the [GitHub Actions tab](../../actions) to download pre-built APKs (`m110-debug-apk`)

---

## REST API

| Endpoint | Method | Description |
|---|---|---|
| `/api/status` | GET | Connection and printer status |
| `/api/settings` | GET/POST | Read/write printer settings |
| `/api/print-image` | POST | Print image (`FormData: image`) |
| `/api/print-text` | POST | Print text (`FormData: text`) |
| `/api/print-text-with-codes` | POST | Print text with embedded QR/barcodes |
| `/api/preview-image` | POST | Generate pre-print preview |
| `/api/print-calibration` | POST | Print alignment calibration pattern |
| `/api/label-sizes` | GET | List available label sizes |

### QR Code & Barcode Syntax

```text
#qr#https://example.com#qr#           → QR Code
#qr:150#https://example.com#qr#       → QR Code with 150px size
#bar#1234567890128#bar#                → Barcode (EAN13)
#bar:code128#ABC-123#bar#              → Barcode (Code128)
```

---

## Configuration

Settings are persistently saved to `printer_settings.json`:

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

---

## Project Structure

```text
├── main.py               # Flask Web Server
├── printer_controller.py # Print logic & ESC/POS bitmap streaming
├── api_routes.py         # REST API endpoints
├── code_generator.py     # QR Code & Barcode generator
├── config.py             # Configuration & label dimensions
├── translations.py       # Localization (EN/DE)
├── web_template.py       # Web interface (HTML/JS/CSS)
├── calibration_tool.py   # Calibration pattern generator
├── android-app/          # Native Android companion application
└── printer_settings.json # Persistent settings
```

---

## Print Protocol

```text
ESC @ (0x1B 0x40)        → Printer Reset
GS v 0 (0x1D 0x76 0x30)  → Raster Bitmap Header
  + width_bytes (2B LE)   → 48 (0x30 0x00)
  + height (2B LE)        → e.g. 240 (0xF0 0x00)
  + image_data            → height × 48 Bytes (line-by-line, adaptive delay)
```

---

## License

MIT
