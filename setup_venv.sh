#!/bin/bash
# Schnelle Virtual Environment Lösung für Raspberry Pi

echo "🔧 Creating Python Virtual Environment for QR/Barcode features..."
echo ""

# Navigate to project directory
cd ~/phomemo-m110-printer

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "⚡ Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "🔄 Upgrading pip..."
pip install --upgrade pip

# Install required packages
echo "📋 Installing QR/Barcode packages..."
pip install qrcode[pil]
pip install pillow

# Optional: Install better barcode support
echo "📊 Installing additional barcode support..."
pip install python-barcode[images] || echo "⚠️ python-barcode failed, using fallback"

echo ""
echo "✅ Virtual environment setup complete!"
echo ""

echo "🧪 Testing installation..."
python3 -c "
try:
    import qrcode
    import PIL
    print('✅ All packages installed successfully in virtual environment!')
    
    # Test QR generation
    qr = qrcode.QRCode(version=1)
    qr.add_data('Test')
    qr.make()
    print('✅ QR code generation working!')
    
except Exception as e:
    print('❌ Error:', e)
"

echo ""
echo "🚀 To run the server with QR/Barcode support:"
echo ""
echo "   cd ~/phomemo-m110-printer"
echo "   source venv/bin/activate"
echo "   python3 main.py"
echo ""
echo "💡 To deactivate virtual environment later:"
echo "   deactivate"
echo ""
echo "📝 Create a startup script? (y/n): "
read -r create_script

if [[ $create_script =~ ^[Yy]$ ]]; then
    echo "📝 Creating startup script..."
    
    cat > start_server.sh << 'EOF'
#!/bin/bash
# Phomemo M110 Server Startup Script with QR/Barcode support

echo "🚀 Starting Phomemo M110 Server with QR/Barcode support..."

cd ~/phomemo-m110-printer
source venv/bin/activate
python3 main.py
EOF

    chmod +x start_server.sh
    
    echo "✅ Startup script created: start_server.sh"
    echo ""
    echo "🚀 To start server in future:"
    echo "   ./start_server.sh"
fi

echo ""
echo "🎉 Setup complete! Virtual environment is ready to use."
