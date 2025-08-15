#!/bin/bash
# Raspberry Pi OS Bookworm Fix - QR/Barcode Dependencies
# Für neuere Pi OS Versionen mit externally-managed-environment

echo "🔧 Fixing QR-Code dependencies on Raspberry Pi OS Bookworm..."
echo ""

echo "📋 Option 1: System packages (Recommended)"
echo "Installing system-wide Python packages..."

# Update package list
sudo apt-get update

# Install QR-Code related packages from system repository
echo "📦 Installing python3-qrcode..."
sudo apt-get install -y python3-qrcode python3-pil python3-pil.imagetk

# Install additional packages that might be needed
echo "📊 Installing additional dependencies..."
sudo apt-get install -y python3-numpy python3-pip

# Install fonts
echo "🔤 Installing fonts..."
sudo apt-get install -y fonts-dejavu-core fonts-liberation

echo ""
echo "✅ System packages installed!"
echo ""

echo "🧪 Testing installation..."
python3 -c "
try:
    import qrcode
    print('✅ qrcode imported successfully')
    
    import PIL
    print('✅ PIL imported successfully')
    
    # Test QR code generation
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data('Test')
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    print('✅ QR code generation test successful')
    
    print('')
    print('🎉 All QR/Barcode dependencies are working!')
    
except ImportError as e:
    print('❌ Import error:', e)
    print('')
    print('🔧 Trying alternative installation methods...')
    print('')
    
    # Try alternative method
    print('📋 Option 2: Virtual Environment')
    print('If system packages do not work, create a virtual environment:')
    print('')
    print('   python3 -m venv ~/phomemo-venv')
    print('   source ~/phomemo-venv/bin/activate')
    print('   pip install qrcode pillow')
    print('   # Then run the server from within the venv')
    print('')
    print('📋 Option 3: Break system packages (not recommended)')
    print('   pip3 install qrcode pillow --break-system-packages')
    print('')
except Exception as e:
    print('⚠️ Test error:', e)
"

echo ""
echo "🚀 You can now start the server:"
echo "   python3 main.py"
echo ""
echo "💡 If the system packages don't work, here are alternatives:"
echo ""
echo "📋 Alternative 1: Virtual Environment (Recommended)"
echo "   cd ~/phomemo-m110-printer"
echo "   python3 -m venv venv"
echo "   source venv/bin/activate"
echo "   pip install qrcode pillow"
echo "   python3 main.py"
echo ""
echo "📋 Alternative 2: Break system packages (Use with caution)"
echo "   pip3 install qrcode pillow --break-system-packages"
echo ""
echo "📋 Alternative 3: Use without QR/Barcode features"
echo "   The server will run normally, just without QR/Barcode functionality"
