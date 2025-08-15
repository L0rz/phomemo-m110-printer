#!/bin/bash
"""
Quick Fix für QR-Code Dependencies auf Raspberry Pi
"""

echo "🔧 Installing QR-Code and Barcode dependencies on Raspberry Pi..."

# Python packages installieren
echo "📦 Installing Python packages..."
pip3 install qrcode[pil]==7.4.2
pip3 install pillow

# Optional: code128 für bessere Barcodes
echo "📊 Installing barcode support..."
pip3 install python-barcode[images]

# System packages für bessere Font-Unterstützung
echo "🔤 Installing system fonts..."
sudo apt-get update
sudo apt-get install -y fonts-dejavu-core fonts-liberation

echo "✅ Installation completed!"
echo ""
echo "🧪 Testing installation..."

python3 -c "
try:
    import qrcode
    import PIL
    print('✅ qrcode:', qrcode.__version__)
    print('✅ PIL/Pillow:', PIL.__version__)
    print('✅ All dependencies installed successfully!')
except ImportError as e:
    print('❌ Import error:', e)
"

echo ""
echo "🚀 Ready to start server:"
echo "   python3 main.py"
