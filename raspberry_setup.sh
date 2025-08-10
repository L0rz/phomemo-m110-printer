#!/bin/bash
# Raspberry Pi Setup Script für Phomemo M110

echo "🍓 Phomemo M110 Setup für Raspberry Pi"
echo "======================================"

# 1. System aktualisieren
echo "📦 System-Update..."
sudo apt update && sudo apt upgrade -y

# 2. Git installieren (falls nicht vorhanden)
echo "📁 Git installieren..."
sudo apt install git -y

# 3. Python-Dependencies
echo "🐍 Python-Dependencies installieren..."
sudo apt install python3 python3-pip bluetooth bluez -y

# 4. Repository klonen
echo "⬇️ Repository klonen..."
cd /home/pi
git clone https://github.com/L0rz/phomemo-m110-printer.git

# 5. In Projektordner wechseln
cd phomemo-m110-printer

# 6. Python-Pakete installieren
echo "📚 Python-Pakete installieren..."
pip3 install -r requirements.txt

# 7. Berechtigungen setzen
echo "🔐 Berechtigungen setzen..."
chmod +x *.py

# 8. Bluetooth-Service aktivieren
echo "🔵 Bluetooth aktivieren..."
sudo systemctl enable bluetooth
sudo systemctl start bluetooth

echo ""
echo "✅ Setup abgeschlossen!"
echo ""
echo "🚀 Starten:"
echo "   cd phomemo-m110-printer"
echo "   python3 phomemo_server_extended.py"
echo ""
echo "🌐 Web-Interface: http://RASPBERRY_IP:8080"
echo ""
