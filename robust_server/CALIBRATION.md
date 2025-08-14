# 📐 Phomemo M110 Kalibrierungs-Tool

## 🎯 Zweck

Das Kalibrierungs-Tool hilft dabei, die **Druckausrichtung** und **Offset-Einstellungen** für den Phomemo M110 Label-Drucker zu optimieren. Es druckt verschiedene Testmuster, um die korrekte Positionierung auf 40×30mm Labels zu gewährleisten.

## 🔧 Verwendung

### **1. Kommandozeile (Standalone)**

```bash
# Basis-Rahmen-Test
python3 calibration_tool.py --mode border

# Mit Offset-Anpassung
python3 calibration_tool.py --mode border --offset-x 3 --offset-y -2

# Gitter-Test für präzise Ausrichtung
python3 calibration_tool.py --mode grid --offset-x 0 --offset-y 0

# Lineal-Test mit Messskala
python3 calibration_tool.py --mode rulers

# Ecken-Test für Label-Grenzen
python3 calibration_tool.py --mode corners

# Offset-Serie (automatisch mehrere Tests)
python3 calibration_tool.py --mode series --offset-x 0

# Nur Vorschau (nicht drucken)
python3 calibration_tool.py --mode border --preview
```

### **2. Web Interface**

1. **Server starten:** `python3 main.py`
2. **Browser öffnen:** `http://RASPBERRY_IP:8080`
3. **Kalibrierung-Sektion** im Web Interface verwenden
4. **Offset-Werte** einstellen
5. **Gewünschten Test** drucken

## 📊 Test-Modi

### **🔲 Rahmen-Test (`border`)**
- **Zweck:** Grundlegende Ausrichtung prüfen
- **Druckt:** Rechteck mit dickem Rahmen am Label-Rand
- **Parameter:** 
  - `offset_x/y`: Position anpassen
  - `thickness`: Rahmendicke (1-5px)
- **Verwendung:** Ersten groben Offset bestimmen

### **📐 Gitter-Test (`grid`)**
- **Zweck:** Präzise Ausrichtung und Messung
- **Druckt:** 5mm-Raster über gesamtes Label
- **Parameter:**
  - `offset_x/y`: Position anpassen
  - `spacing`: Rasterabstand (Standard: 5mm)
- **Verwendung:** Feinabstimmung und Vermessung

### **📏 Lineal-Test (`rulers`)**
- **Zweck:** Vermessung und Positionsbestimmung
- **Druckt:** Lineale mit mm-Markierungen
- **Parameter:** `offset_x/y`: Position anpassen
- **Verwendung:** Exakte Abmessungen bestimmen

### **📍 Ecken-Test (`corners`)**
- **Zweck:** Label-Grenzen markieren
- **Druckt:** L-förmige Ecken-Markierungen
- **Parameter:**
  - `offset_x/y`: Position anpassen
  - `corner_size`: Größe der L-Markierungen
- **Verwendung:** Label-Ränder exakt bestimmen

### **📊 Offset-Serie (`series`)**
- **Zweck:** Mehrere Offset-Werte testen
- **Druckt:** 5 Tests mit verschiedenen X-Offsets (-6, -3, 0, +3, +6)
- **Parameter:** `offset_x`: Basis-Offset
- **Verwendung:** Optimalen Offset finden

## 🎛️ Parameter

### **Offset-Einstellungen**
- **X-Offset:** Horizontale Verschiebung in Pixeln
  - **Negativ:** Nach links verschieben
  - **Positiv:** Nach rechts verschieben
  - **Empfohlen:** -10 bis +10 Pixel

- **Y-Offset:** Vertikale Verschiebung in Pixeln
  - **Negativ:** Nach oben verschieben
  - **Positiv:** Nach unten verschieben
  - **Empfohlen:** -10 bis +10 Pixel

### **Physische Maße**
- **Drucker-Breite:** 48mm (384 Pixel)
- **Label-Größe:** 40×30mm (320×240 Pixel)
- **Auflösung:** ~8 Pixel/mm
- **Label-Position:** Zentriert auf Drucker-Breite

## 🔄 Kalibrierungs-Workflow

### **Schritt 1: Grosse Ausrichtung**
```bash
python3 calibration_tool.py --mode border --offset-x 0 --offset-y 0
```
- Rahmen sollte zentriert auf Label sein
- Falls nicht: X/Y-Offset anpassen

### **Schritt 2: Offset-Serie**
```bash
python3 calibration_tool.py --mode series --offset-x 0
```
- Besten Offset aus den 5 Tests wählen
- Den Test mit der besten Zentrierung merken

### **Schritt 3: Feinabstimmung**
```bash
python3 calibration_tool.py --mode grid --offset-x [BESTER_WERT] --offset-y 0
```
- Mit dem besten X-Offset aus Schritt 2
- Y-Offset bei Bedarf anpassen

### **Schritt 4: Verifikation**
```bash
python3 calibration_tool.py --mode corners --offset-x [FINAL_X] --offset-y [FINAL_Y]
```
- Finale Offset-Werte testen
- Ecken sollten genau auf Label-Rändern sein

## 💾 Offset-Werte speichern

Nach der Kalibrierung die optimalen Werte in der Konfiguration speichern:

```python
# In config.py oder printer_controller.py:
DEFAULT_OFFSET_X = 3  # Ihr optimaler X-Offset
DEFAULT_OFFSET_Y = -1  # Ihr optimaler Y-Offset
```

## 🐛 Troubleshooting

### **Problem: Label nicht zentriert**
- **Lösung:** X-Offset anpassen (±5 Pixel Schritte)
- **Test:** `--mode border --offset-x [WERT]`

### **Problem: Label zu hoch/niedrig**
- **Lösung:** Y-Offset anpassen
- **Test:** `--mode border --offset-y [WERT]`

### **Problem: Unklare Ausrichtung**
- **Lösung:** Gitter-Test verwenden
- **Test:** `--mode grid` für präzise Messung

### **Problem: Bluetooth-Verbindung**
- **Prüfen:** `python3 main.py` (Server-Logs)
- **Manuell:** Web Interface → "Manual Connect"

### **Problem: Kein Druck**
- **MAC-Adresse** in `config.py` prüfen
- **Drucker-Status** über Web Interface prüfen
- **rfcomm-Verbindung:** `ls -la /dev/rfcomm0`

## 📏 Messwerte interpretieren

### **Pixel zu Millimeter umrechnen:**
- **1mm ≈ 8 Pixel**
- **5mm = 40 Pixel**
- **10mm = 80 Pixel**

### **Label-Dimensionen:**
- **Label:** 40×30mm (320×240px)
- **Drucker:** 48mm breit (384px)
- **Zentrierung:** (384-320)/2 = 32px Rand links/rechts

## 🎯 Optimale Einstellungen finden

1. **Starten Sie mit Offset (0,0)**
2. **Verwenden Sie die Offset-Serie** für X-Achse
3. **Testen Sie Y-Offset einzeln**
4. **Verifizieren mit Ecken-Test**
5. **Speichern Sie die Werte** in der Konfiguration

Mit diesen Tools und diesem Workflow sollten Sie eine perfekte Label-Ausrichtung erreichen! 🎯
