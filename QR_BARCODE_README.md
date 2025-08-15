# 🔲 QR-Code & Barcode Erweiterung

## Neue Features

Das Phomemo M110 System wurde um **QR-Code und Barcode-Funktionalität** erweitert mit einer eleganten **Markdown-ähnlichen Syntax**.

### ✨ Features

- **QR-Codes** mit konfigurierbarer Größe
- **Barcodes (Code128)** mit konfigurierbarer Höhe  
- **Markdown-Syntax** für einfache Eingabe
- **Live-Vorschau** im Web-Interface
- **Kombinierte Labels** mit Text + Codes
- **Template-System** für häufige Anwendungen

### 📖 Syntax

#### QR-Codes
```
#qr#Inhalt#qr#                    → Standard QR-Code (100px)
#qr:150#Größerer Inhalt#qr#       → QR-Code mit 150px Größe
#qr#https://example.com#qr#       → QR mit URL
```

#### Barcodes
```
#bar#1234567890#bar#              → Standard Barcode (50px hoch)
#bar:80#Code mit Text#bar#        → Barcode mit 80px Höhe
#bar#ART-12345#bar#               → Artikel-Code
```

#### Kombinierte Beispiele
```
Produkt Info:
#qr#https://shop.example.com/product/123#qr#

Artikel: #bar#ART-456789#bar#

Datum: $TIME$
```

### 🌐 Spezielle QR-Codes

#### WLAN-Zugang
```
#qr#WIFI:S:MeinWLAN;T:WPA;P:passwort123;H:false;;#qr#
```

#### vCard Kontakt
```
#qr#BEGIN:VCARD
FN:Max Mustermann
TEL:+49123456789
EMAIL:max@example.com
ORG:Firma GmbH
END:VCARD#qr#
```

#### SMS
```
#qr#SMSTO:+49123456789:Hallo Welt#qr#
```

#### E-Mail
```
#qr#mailto:test@example.com?subject=Betreff&body=Nachricht#qr#
```

## 🚀 Installation

### 1. Dependencies installieren
```bash
chmod +x install_codes.sh
./install_codes.sh
```

Oder manuell:
```bash
pip3 install qrcode==7.4.2 code128==0.3 numpy>=1.21.0
```

### 2. Testen
```bash
python3 demo_codes.py
```

### 3. Server starten
```bash
python3 main.py
```

## 🔧 Verwendung

### Web-Interface
1. Öffne `http://localhost:5000`
2. Nutze die neue **"🔲 QR-Codes & Barcodes"** Sektion
3. Eingabe mit Markdown-Syntax
4. **Live-Vorschau** anzeigen
5. Drucken oder zur Queue hinzufügen

### API-Endpunkte

#### Text mit Codes drucken
```bash
curl -X POST http://localhost:5000/api/print-text-with-codes \
  -F "text=Produkt: #qr#https://example.com#qr#" \
  -F "font_size=22" \
  -F "alignment=center" \
  -F "immediate=true"
```

#### Vorschau erstellen
```bash
curl -X POST http://localhost:5000/api/preview-text-with-codes \
  -F "text=Test: #bar#12345#bar#" \
  -F "font_size=20"
```

#### Syntax-Hilfe abrufen
```bash
curl http://localhost:5000/api/code-syntax-help
```

## 📁 Neue Dateien

- `code_generator.py` - Haupt-Code-Generator
- `qr_barcode_interface.py` - Web-Interface-Komponenten  
- `demo_codes.py` - Test- und Demo-Skript
- `install_codes.sh` - Installations-Skript

## 🔧 Konfiguration

### Code-Größen anpassen
In `code_generator.py`:
```python
self.qr_default_size = 100        # Standard QR-Größe
self.barcode_height = 50          # Standard Barcode-Höhe
self.barcode_width_factor = 2     # Barcode-Breite pro Strich
```

### Label-Abmessungen
Automatische Anpassung an `config.py`:
```python
LABEL_WIDTH_PX = 384   # Pixel
LABEL_HEIGHT_PX = 240  # Pixel
```

## 🎯 Anwendungsfälle

### Einzelhandel
- **Produkt-Etiketten** mit QR zu Online-Shop
- **Preisschilder** mit Barcode für Kasse
- **Inventar-Labels** mit QR zu Datenbank

### Events
- **Tickets** mit QR für Check-in
- **Nametags** mit QR zu Social Media
- **Standort-Schilder** mit QR zu Maps

### Büro
- **Asset-Tags** mit QR zu Inventar-System  
- **WLAN-Zugangsdaten** als QR-Code
- **Kontaktdaten** als vCard QR

### Logistik
- **Paket-Labels** mit Tracking-Barcode
- **Lager-Etiketten** mit QR zu WMS
- **Versand-Labels** kombiniert

## 🐛 Troubleshooting

### Font-Probleme
```bash
# Ubuntu/Debian
sudo apt-get install fonts-dejavu-core fonts-liberation

# Oder Font-Pfad in code_generator.py anpassen
```

### QR-Code zu groß
- Kleinere Größe verwenden: `#qr:80#content#qr#`
- Kürzeren Inhalt verwenden
- Label-Layout optimieren

### Barcode nicht lesbar
- Höhere Auflösung: `#bar:80#content#bar#`
- Kürzeren Text verwenden  
- Code128-kompatible Zeichen verwenden

## 📊 Performance

- **QR-Code Generation**: ~50ms pro Code
- **Barcode Generation**: ~20ms pro Code  
- **Kombinierte Labels**: ~100-200ms je nach Komplexität
- **Memory Usage**: ~5-10MB zusätzlich für numpy/PIL

## 🔄 Updates

Das System ist modular aufgebaut und kann einfach erweitert werden:

- **Neue Code-Typen** in `code_generator.py` hinzufügen
- **Template-System** in `qr_barcode_interface.py` erweitern  
- **API-Endpunkte** in `api_routes.py` hinzufügen

## 🎉 Beispiel-Output

Das System generiert Labels wie:
```
    Produkt Information
    
    [QR-Code 100x100px]
    https://shop.example.com
    
    Artikel: [Barcode 150x50px]
             ART-456789
             
    Datum: 15.08.2025
```

Alle Codes werden automatisch **zentriert** und optimal auf dem Label platziert.
