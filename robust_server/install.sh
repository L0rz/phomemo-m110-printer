#!/bin/bash
"""
Installations-Script für Phomemo M110 Robust Server
"""

echo "🍓 Phomemo M110 Robust Server - Installation"
echo "============================================="

# Verzeichnis prüfen
if [ ! -f "main.py" ]; then
    echo "❌ Fehler: main.py nicht gefunden!"
    echo "💡 Bitte das Script im robust_server/ Verzeichnis ausführen."
    exit 1
fi

echo "📋 Installiere Python-Abhängigkeiten..."

# Requirements installieren
pip3 install flask pillow

echo "🔧 Konfiguration..."

# MAC-Adresse abfragen
echo -n "📡 Bitte Drucker MAC-Adresse eingeben (z.B. 12:7E:5A:E9:E5:22): "
read MAC_ADDRESS

if [ -z "$MAC_ADDRESS" ]; then
    echo "⚠️  Keine MAC-Adresse eingegeben, verwende Standard-Wert"
    MAC_ADDRESS="12:7E:5A:E9:E5:22"
fi

# Konfiguration anpassen
echo "PRINTER_MAC = \"$MAC_ADDRESS\"" > config_local.py
echo "✅ MAC-Adresse gesetzt: $MAC_ADDRESS"

echo "🔐 Bluetooth-Berechtigungen..."

# Bluetooth-Gruppe prüfen
if groups $USER | grep -q "bluetooth"; then
    echo "✅ User ist bereits in bluetooth Gruppe"
else
    echo "⚠️  Füge User zur bluetooth Gruppe hinzu..."
    sudo usermod -a -G bluetooth $USER
    echo "💡 Bitte neu anmelden für Gruppenänderung!"
fi

echo "🧪 Teste Grundfunktionen..."

# Python-Module testen
python3 -c "
try:
    from printer_controller import RobustPhomemoM110
    from calibration_tool import PhomemoCalibration
    print('✅ Module erfolgreich importiert')
except ImportError as e:
    print(f'❌ Import-Fehler: {e}')
    exit(1)
"

echo "📄 Erstelle Service-Datei..."

# Systemd Service erstellen
SERVICE_FILE="/tmp/phomemo.service"
cat > $SERVICE_FILE << EOF
[Unit]
Description=Phomemo M110 Robust Server
After=network.target bluetooth.target

[Service]
ExecStart=/usr/bin/python3 $(pwd)/main.py
Restart=always
User=$USER
Group=$USER
WorkingDirectory=$(pwd)
Environment=PYTHONPATH=$(pwd)

[Install]
WantedBy=multi-user.target
EOF

echo "📋 Service-Datei erstellt: $SERVICE_FILE"
echo "💡 Zum Installieren als Service:"
echo "   sudo cp $SERVICE_FILE /etc/systemd/system/"
echo "   sudo systemctl enable phomemo"
echo "   sudo systemctl start phomemo"

echo ""
echo "🎯 Installation abgeschlossen!"
echo ""
echo "🚀 Starten des Servers:"
echo "   python3 main.py"
echo ""
echo "🌐 Web-Interface:"
echo "   http://$(hostname -I | awk '{print $1}'):8080"
echo ""
echo "📐 Kalibrierung:"
echo "   python3 calibration_tool.py --mode border"
echo ""
echo "📚 Dokumentation:"
echo "   - README.md (Allgemeine Nutzung)"
echo "   - CALIBRATION.md (Kalibrierungs-Anleitung)"
echo ""
echo "🔧 Konfiguration:"
echo "   - config.py (Grundeinstellungen)"
echo "   - config_local.py (Lokale MAC-Adresse)"
echo ""
echo "✅ Bereit zum Testen!"
