#!/bin/bash
"""
Installation der QR-Code und Barcode-Dependencies für Phomemo M110
"""

echo "🔲 Installing QR-Code and Barcode dependencies..."

# Python packages installieren
echo "📦 Installing Python packages..."
pip3 install qrcode==7.4.2
pip3 install code128==0.3
pip3 install numpy>=1.21.0

# Optional: PIL/Pillow update für bessere Kompatibilität
echo "🖼️ Updating Pillow..."
pip3 install --upgrade Pillow

echo "✅ Installation completed!"
echo ""
echo "🧪 Testing installation..."

# Test-Skript ausführen
python3 -c "
import qrcode
import code128
import numpy as np
from PIL import Image

print('✅ qrcode:', qrcode.__version__)
print('✅ code128 imported successfully')
print('✅ numpy:', np.__version__)
print('✅ PIL/Pillow:', Image.__version__)
print('')
print('🎉 All dependencies installed successfully!')
print('')
print('📝 Next steps:')
print('   1. Run: python3 demo_codes.py')
print('   2. Start server: python3 main.py')
print('   3. Open: http://localhost:5000')
print('   4. Test QR/Barcode functionality in web interface')
"

echo ""
echo "🔧 Optional: System packages for better font support"
echo "   sudo apt-get install fonts-dejavu-core fonts-liberation"
