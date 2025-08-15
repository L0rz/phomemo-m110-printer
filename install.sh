#!/bin/bash
"""
Installations-Skript für Phomemo M110 Server
Mit Bildvorschau und X-Offset-Konfiguration
"""

echo "🖨️  PHOMEMO M110 INSTALLATION"
echo "============================="

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funktionen
print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# System-Updates
print_step "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Python und Dependencies installieren
print_step "Installing Python and system dependencies..."
sudo apt install -y python3 python3-pip python3-venv bluetooth bluez python3-dev libjpeg-dev zlib1g-dev

# Virtual Environment erstellen
print_step "Creating Python virtual environment..."
python3 -m venv phomemo_env
source phomemo_env/bin/activate

# Python-Pakete installieren
print_step "Installing Python packages..."
pip install --upgrade pip
pip install flask pillow

# Bluetooth-Service aktivieren
print_step "Enabling Bluetooth service..."
sudo systemctl enable bluetooth
sudo systemctl start bluetooth

# Benutzer zur bluetooth-Gruppe hinzufügen
print_step "Adding user to bluetooth group..."
sudo usermod -a -G bluetooth $USER

# Konfigurationsdatei erstellen
print_step "Setting up configuration..."

# MAC-Adresse vom Benutzer abfragen
echo ""
echo "📱 BLUETOOTH-KONFIGURATION"
echo "=========================="
echo "Bitte stellen Sie sicher, dass Ihr Phomemo M110 Drucker eingeschaltet ist."
echo ""
read -p "Geben Sie die MAC-Adresse Ihres Phomemo M110 ein (Format: 12:34:56:78:9A:BC): " PRINTER_MAC

if [[ ! $PRINTER_MAC =~ ^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$ ]]; then
    print_error "Ungültige MAC-Adresse! Bitte Format 12:34:56:78:9A:BC verwenden."
    exit 1
fi

# Konfigurationsdatei anpassen
print_step "Updating configuration file..."
sed -i "s/12:7E:5A:E9:E5:22/$PRINTER_MAC/g" config.py

# Bluetooth-Pairing
print_step "Pairing with printer..."
echo "Versuche Drucker zu pairen..."

# Bluetooth-Scan und Pairing
timeout 10 bluetoothctl scan on &
sleep 5
bluetoothctl pair $PRINTER_MAC
bluetoothctl trust $PRINTER_MAC

# RFCOMM-Verbindung testen
print_step "Testing RFCOMM connection..."
sudo rfcomm bind 0 $PRINTER_MAC
sleep 2

if [ -e "/dev/rfcomm0" ]; then
    print_success "RFCOMM connection established successfully!"
    sudo rfcomm release 0
else
    print_warning "RFCOMM connection failed, but this can be normal on first setup."
fi

# Systemd Service erstellen
print_step "Creating systemd service..."
cat > phomemo-enhanced.service << EOF
[Unit]
Description=Phomemo M110 Enhanced Print Server
After=network.target bluetooth.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/phomemo_env/bin
ExecStart=$(pwd)/phomemo_env/bin/python main_enhanced.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo cp phomemo-enhanced.service /etc/systemd/system/
sudo systemctl daemon-reload

# Berechtigungen setzen
print_step "Setting permissions..."
chmod +x main_enhanced.py
sudo chown $USER:$USER *.py

# Firewall-Regel hinzufügen (falls ufw aktiv)
if command -v ufw &> /dev/null; then
    print_step "Configuring firewall..."
    sudo ufw allow 8080/tcp
fi

# Abschluss
echo ""
echo "🎉 INSTALLATION ABGESCHLOSSEN!"
echo "=============================="
echo ""
echo "📋 NÄCHSTE SCHRITTE:"
echo ""
echo "1. Konfiguration prüfen:"
echo "   nano config_enhanced.py"
echo ""
echo "2. Server manuell starten:"
echo "   source phomemo_env/bin/activate"
echo "   python main_enhanced.py"
echo ""
echo "3. Service automatisch starten:"
echo "   sudo systemctl enable phomemo-enhanced"
echo "   sudo systemctl start phomemo-enhanced"
echo ""
echo "4. Web-Interface öffnen:"
echo "   http://$(hostname -I | awk '{print $1}'):8080"
echo ""
echo "🔧 KONFIGURIERTE EINSTELLUNGEN:"
echo "   MAC-Adresse: $PRINTER_MAC"
echo "   X-Offset: 40 Pixel (Standard)"
echo "   Web-Port: 8080"
echo ""
echo "📖 WEITERE KOMMANDOS:"
echo "   Status prüfen: sudo systemctl status phomemo-enhanced"
echo "   Logs anzeigen: sudo journalctl -u phomemo-enhanced -f"
echo "   Service stoppen: sudo systemctl stop phomemo-enhanced"
echo ""
echo "💡 TIPPS:"
echo "   - Drucker muss eingeschaltet sein"
echo "   - Bei Problemen: sudo rfcomm bind 0 $PRINTER_MAC"
echo "   - Bluetooth-Reichweite beachten"
echo ""
print_success "Setup erfolgreich abgeschlossen!"

# Test-Verbindung anbieten
echo ""
read -p "Möchten Sie eine Test-Verbindung zum Drucker durchführen? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_step "Testing printer connection..."
    
    # Virtual Environment aktivieren für Test
    source phomemo_env/bin/activate
    
    # Kurzer Verbindungstest
    python3 << EOF
try:
    from printer_controller_enhanced import EnhancedPhomemoM110
    printer = EnhancedPhomemoM110("$PRINTER_MAC")
    if printer.connect_bluetooth():
        print("✅ Drucker-Verbindung erfolgreich!")
        # Einfacher Test-Print
        if printer.print_text_immediate("PHOMEMO M110\\nEnhanced Setup\\nTest erfolgreich!"):
            print("✅ Test-Druck erfolgreich!")
        else:
            print("⚠️  Test-Druck fehlgeschlagen")
    else:
        print("❌ Drucker-Verbindung fehlgeschlagen")
        print("💡 Überprüfen Sie:")
        print("   - Drucker ist eingeschaltet")
        print("   - MAC-Adresse ist korrekt")
        print("   - Bluetooth-Reichweite")
except Exception as e:
    print(f"❌ Test-Fehler: {e}")
EOF
fi

echo ""
echo "🚀 Bereit zum Drucken!"
