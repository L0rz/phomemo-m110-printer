#!/bin/bash
# Quick Fix für Raspberry Pi - QR/Barcode Dependencies

echo "🔧 Installing QR-Code dependencies on Raspberry Pi..."

# Update package list
sudo apt-get update

# Install Python QR-Code library
echo "📦 Installing qrcode library..."
pip3 install qrcode[pil]

# Install Pillow if not already installed
echo "🖼️ Installing Pillow..."
pip3 install pillow

# Optional: Install better barcode support
echo "📊 Installing barcode support..."
pip3 install python-barcode[images] || echo "⚠️ python-barcode installation failed, simple barcode fallback will be used"

# Install system fonts for better text rendering
echo "🔤 Installing fonts..."
sudo apt-get install -y fonts-dejavu-core fonts-liberation

echo ""
echo "✅ Installation completed!"
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
    print('')
    print('🚀 You can now start the server:')
    print('   python3 main.py')
    
except ImportError as e:
    print('❌ Import error:', e)
    print('')
    print('🔧 Try manual installation:')
    print('   pip3 install qrcode pillow')
    print('   sudo apt-get install python3-pil python3-pip')
except Exception as e:
    print('⚠️ Test error:', e)
    print('Dependencies might be installed but with issues')
"

echo ""
echo "📋 If you still have issues, try:"
echo "   sudo apt-get install python3-pil python3-pip"
echo "   pip3 install --upgrade qrcode pillow"
echo ""
echo "💡 The server will work without QR/Barcode features if dependencies are missing"
