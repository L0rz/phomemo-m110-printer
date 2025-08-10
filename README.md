# Phomemo M110 Label Drucker

Ein Web-Interface für den Phomemo M110 Label-Drucker mit präziser Kalibrierung und optimierter Label-Positionierung.
Der kommplette code wurde von mir mit Claude IA erstellt und enthält noch fehler!

## 🎯 Features

- **Web-Interface**: Benutzerfreundliche Bedienung über Browser
- **Y-Offset Kalibrierung**: Präzise vertikale Positionierung
- **Text & Bilder**: Druckt Text und Bilder auf 40×30mm Labels
- **Segmentierter Volltest**: Nutzt komplette 30mm Label-Höhe
- **Optimiert für M110**: Angepasst an Hardware-Limits

## 📋 Technische Spezifikationen

- **Label-Größe**: 40mm × 30mm (320×240px)
- **Hardware**: Phomemo M110 mit 384px Breite (48mm bei 203 DPI)
- **Verbindung**: Bluetooth über rfcomm
- **Segmentierung**: Max 100px pro Block für garantiert 1 Label

## 🚀 Installation

### Voraussetzungen

```bash
sudo apt update
sudo apt install python3 python3-pip bluetooth bluez
pip3 install -r requirements.txt
```

### Bluetooth-Verbindung einrichten

```bash
# Drucker pairing
sudo bluetoothctl
> scan on
> pair 12:7E:5A:E9:E5:22
> trust 12:7E:5A:E9:E5:22
> exit

# rfcomm-Verbindung erstellen
sudo rfcomm bind 0 12:7E:5A:E9:E5:22
```

## 🎛️ Verwendung

1. **Server starten**:
   ```bash
   python3 phomemo_m110_printer.py
   ```

2. **Web-Interface öffnen**:
   ```
   http://localhost:8080
   ```

3. **Kalibrierung**:
   - X-Offset: Links/Rechts Position (Standard: 72px = 9mm)
   - Y-Offset: Oben/Unten Position (-30px bis +50px)
   - Kalibrierungs-Test drucken und justieren

4. **Tests**:
   - **Minimal-Test**: 80px Referenz-Test
   - **Kalibrierungs-Test**: Max 100px mit Y-Offset
   - **Volltest**: 30mm Label in 2×100px Segmenten

## 🔧 Konfiguration

Passen Sie in `phomemo_m110_printer.py` an:

```python
# Drucker-MAC-Adresse
PRINTER_MAC = "12:7E:5A:E9:E5:22"

# Standard-Offsets
printer.label_offset_x = 72  # 9mm von links
printer.calibration_offset_y = 0  # Y-Offset
```

## 📁 Projektstruktur

```
phomemo-m110-printer/
├── phomemo_m110_printer.py    # Hauptskript
├── requirements.txt           # Python-Abhängigkeiten
├── README.md                 # Diese Datei
└── LICENSE                   # MIT-Lizenz
```

## 🛠️ API Endpoints

- `GET /` - Web-Interface
- `POST /api/print-text` - Text drucken
- `POST /api/print-image` - Bild drucken
- `POST /api/print-calibration` - Kalibrierungs-Test
- `POST /api/print-full-height` - Volltest (30mm)
- `POST /api/save-calibration` - Kalibrierung speichern
- `GET /api/status` - Drucker-Status

## 🔍 Fehlerbehebung

### Bluetooth-Probleme
```bash
# Verbindung prüfen
ls -la /dev/rfcomm0

# Neuverbindung
sudo rfcomm release 0
sudo rfcomm bind 0 12:7E:5A:E9:E5:22
```

### Drucker antwortet nicht
1. rfcomm-Verbindung prüfen
2. Drucker einschalten
3. Bluetooth-Entfernung verringern

### Labels zu weit links/rechts
- X-Offset im Web-Interface anpassen
- Kalibrierungs-Test drucken
- Einstellungen speichern

## 📝 Changelog

### Version 2.0 (Korrigiert)
- ✅ Y-Offset funktioniert korrekt
- ✅ Nur 1 Label pro Test
- ✅ Segmentierter Volltest für 30mm Labels
- ✅ Optimierte Kalibrierung (max 100px)

### Version 1.0
- Grundfunktionalität
- Web-Interface
- Text- und Bilddruck

## 📄 Lizenz

MIT License - siehe [LICENSE](LICENSE) Datei.

## 🤝 Beitragen

1. Fork das Repository
2. Feature-Branch erstellen (`git checkout -b feature/AmazingFeature`)
3. Änderungen committen (`git commit -m 'Add some AmazingFeature'`)
4. Branch pushen (`git push origin feature/AmazingFeature`)
5. Pull Request öffnen

## 🏷️ Label-Design-Tipps

- **Text**: Automatische Skalierung bei zu langem Text
- **Schriftgröße**: 12-28px je nach Textmenge
- **Bilder**: Werden automatisch auf Label-Größe angepasst
- **Rahmen**: Debug-Rahmen für Kalibrierung aktivieren
