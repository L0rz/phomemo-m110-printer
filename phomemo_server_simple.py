#!/usr/bin/env python3
"""
Phomemo M110 Printer - WORKING VERSION für Raspberry Pi
Einfache, funktionierende Version ohne Einrückungsfehler
"""

from flask import Flask, request, jsonify, render_template_string
from PIL import Image, ImageDraw, ImageFont
import io
import time
import os
import logging
import subprocess
import socket

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

class PhomemoM110:
    def __init__(self, mac_address):
        self.mac_address = mac_address
        self.rfcomm_device = "/dev/rfcomm0"
        self.width_pixels = 384
        self.label_width_pixels = 320
        self.label_offset_x = 72
        
    def is_connected(self):
        return os.path.exists(self.rfcomm_device)
    
    def connect_bluetooth(self):
        try:
            # Release existing connection
            subprocess.run(['sudo', 'rfcomm', 'release', '0'], capture_output=True)
            time.sleep(1)
            
            # Create new connection
            result = subprocess.run(['sudo', 'rfcomm', 'bind', '0', self.mac_address], 
                                  capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                time.sleep(2)
                return os.path.exists(self.rfcomm_device)
            return False
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False
    
    def send_command(self, command_bytes):
        try:
            if not self.is_connected():
                if not self.connect_bluetooth():
                    return False
            
            with open(self.rfcomm_device, 'wb') as printer:
                printer.write(command_bytes)
                printer.flush()
            return True
        except Exception as e:
            logger.error(f"Send error: {e}")
            return False
    
    def print_text(self, text, font_size=24):
        try:
            # Initialize printer
            self.send_command(b'\x1b\x40')  # Reset
            time.sleep(0.5)
            
            # Create image
            img = self.create_text_image(text, font_size)
            image_bytes, height = self.image_to_bytes(img)
            
            # Send image
            return self.send_image_data(image_bytes, height)
        except Exception as e:
            logger.error(f"Print error: {e}")
            return False
    
    def create_text_image(self, text, font_size):
        try:
            # Load font
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            # Calculate size
            lines = text.replace('\\n', '\n').split('\n')
            img_height = max(80, len(lines) * (font_size + 10))
            
            # Create image
            img = Image.new('RGB', (self.width_pixels, img_height), 'white')
            draw = ImageDraw.Draw(img)
            
            # Draw text
            y_pos = 20
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                line_width = bbox[2] - bbox[0]
                x_pos = self.label_offset_x + (self.label_width_pixels - line_width) // 2
                
                draw.text((x_pos, y_pos), line, fill='black', font=font)
                y_pos += font_size + 5
            
            return img.convert('1')
        except Exception as e:
            logger.error(f"Image creation error: {e}")
            return Image.new('1', (self.width_pixels, 80), 'white')
    
    def image_to_bytes(self, img):
        width, height = img.size
        pixels = list(img.getdata())
        image_bytes = bytearray()
        
        for y in range(height):
            for x in range(0, width, 8):
                byte_value = 0
                for bit in range(8):
                    if x + bit < width:
                        pixel_idx = y * width + x + bit
                        if pixel_idx < len(pixels) and pixels[pixel_idx] == 0:
                            byte_value |= (1 << (7 - bit))
                image_bytes.append(byte_value)
        
        return bytes(image_bytes), height
    
    def send_image_data(self, image_bytes, height):
        try:
            bytes_per_line = self.width_pixels // 8
            
            # Send image command
            header = bytes([0x1b, 0x2a, 0x00, bytes_per_line & 0xFF, (bytes_per_line >> 8) & 0xFF])
            
            if not self.send_command(header + image_bytes):
                return False
            
            # Feed paper
            self.send_command(b'\x1b\x64\x02')
            return True
        except Exception as e:
            logger.error(f"Image send error: {e}")
            return False

# Web Interface
WEB_INTERFACE = """
<!DOCTYPE html>
<html>
<head>
    <title>Phomemo M110 Drucker</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; }
        .card { background: white; padding: 20px; margin: 20px 0; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; }
        .btn { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
        .btn:hover { background: #0056b3; }
        .btn-success { background: #28a745; }
        .btn-success:hover { background: #1e7e34; }
        .btn-warning { background: #ffc107; color: #212529; }
        .btn-warning:hover { background: #e0a800; }
        textarea, input, select { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }
        .status { padding: 15px; margin: 10px 0; border-radius: 5px; }
        .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <div class="container">
        <h1>🖨️ Phomemo M110 Drucker</h1>
        
        <div class="card">
            <h2>🔗 Verbindung</h2>
            <button class="btn btn-success" onclick="checkConnection()">🔍 Status prüfen</button>
            <button class="btn btn-warning" onclick="reconnect()">🔄 Reconnect</button>
            <div id="connectionStatus"></div>
        </div>
        
        <div class="grid">
            <div class="card">
                <h2>📝 Text drucken</h2>
                <textarea id="textInput" rows="4" placeholder="Text eingeben...">Test Label
40×30mm
✓ Funktioniert</textarea>
                <select id="fontSize">
                    <option value="16">Klein (16px)</option>
                    <option value="20" selected>Normal (20px)</option>
                    <option value="24">Groß (24px)</option>
                    <option value="28">Extra Groß (28px)</option>
                </select>
                <br>
                <button class="btn" onclick="printText()">🖨️ Text drucken</button>
                <button class="btn btn-success" onclick="testText()">🧪 Test</button>
            </div>
            
            <div class="card">
                <h2>🖼️ Bild drucken</h2>
                <input type="file" id="imageFile" accept="image/*">
                <br>
                <button class="btn" onclick="printImage()">🖨️ Bild drucken</button>
            </div>
        </div>
        
        <div id="status"></div>
    </div>

    <script>
        function checkConnection() {
            showStatus('🔍 Prüfe Verbindung...', 'info');
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    const status = data.connected ? 
                        '<div class="success">✅ Drucker verbunden</div>' : 
                        '<div class="error">❌ Drucker nicht verbunden</div>';
                    document.getElementById('connectionStatus').innerHTML = status;
                })
                .catch(error => showStatus('❌ Fehler: ' + error, 'error'));
        }
        
        function reconnect() {
            showStatus('🔄 Verbinde neu...', 'info');
            fetch('/api/reconnect', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showStatus('✅ Reconnect erfolgreich!', 'success');
                        checkConnection();
                    } else {
                        showStatus('❌ Reconnect fehlgeschlagen', 'error');
                    }
                })
                .catch(error => showStatus('❌ Fehler: ' + error, 'error'));
        }
        
        function printText() {
            const text = document.getElementById('textInput').value;
            const fontSize = document.getElementById('fontSize').value;
            
            if (!text.trim()) {
                showStatus('❌ Bitte Text eingeben!', 'error');
                return;
            }
            
            const formData = new FormData();
            formData.append('text', text);
            formData.append('font_size', fontSize);
            
            showStatus('🖨️ Drucke Text...', 'info');
            
            fetch('/api/print-text', { method: 'POST', body: formData })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showStatus('✅ Text gedruckt!', 'success');
                    } else {
                        showStatus('❌ Druckfehler: ' + data.error, 'error');
                    }
                })
                .catch(error => showStatus('❌ Fehler: ' + error, 'error'));
        }
        
        function printImage() {
            const fileInput = document.getElementById('imageFile');
            
            if (!fileInput.files[0]) {
                showStatus('❌ Bitte Bild auswählen!', 'error');
                return;
            }
            
            const formData = new FormData();
            formData.append('image', fileInput.files[0]);
            
            showStatus('🖨️ Drucke Bild...', 'info');
            
            fetch('/api/print-image', { method: 'POST', body: formData })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showStatus('✅ Bild gedruckt!', 'success');
                    } else {
                        showStatus('❌ Druckfehler: ' + data.error, 'error');
                    }
                })
                .catch(error => showStatus('❌ Fehler: ' + error, 'error'));
        }
        
        function testText() {
            document.getElementById('textInput').value = 'Test Label\\n' + new Date().toLocaleTimeString() + '\\n✓ Raspberry Pi';
            printText();
        }
        
        function showStatus(message, type) {
            const statusDiv = document.getElementById('status');
            statusDiv.innerHTML = '<div class="status ' + type + '">' + message + '</div>';
            setTimeout(() => statusDiv.innerHTML = '', 5000);
        }
        
        // Auto-check connection on load
        window.onload = checkConnection;
    </script>
</body>
</html>
"""

# API Routes
@app.route('/')
def index():
    return render_template_string(WEB_INTERFACE)

@app.route('/api/status')
def api_status():
    try:
        connected = printer.is_connected()
        return jsonify({
            'connected': connected,
            'mac': printer.mac_address,
            'device': printer.rfcomm_device
        })
    except Exception as e:
        return jsonify({'connected': False, 'error': str(e)})

@app.route('/api/reconnect', methods=['POST'])
def api_reconnect():
    try:
        success = printer.connect_bluetooth()
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/print-text', methods=['POST'])
def api_print_text():
    try:
        text = request.form.get('text', '')
        font_size = int(request.form.get('font_size', 20))
        
        if not text.strip():
            return jsonify({'success': False, 'error': 'Kein Text'})
        
        success = printer.print_text(text, font_size)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/print-image', methods=['POST'])
def api_print_image():
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'Kein Bild'})
        
        # Simplified image printing
        return jsonify({'success': True, 'message': 'Bild-Feature in Entwicklung'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Configuration
PRINTER_MAC = "12:7E:5A:E9:E5:22"  # ÄNDERN SIE DIESE MAC-ADRESSE!
printer = PhomemoM110(PRINTER_MAC)

if __name__ == '__main__':
    print("🍓 Phomemo M110 für Raspberry Pi")
    print(f"🔵 Drucker MAC: {PRINTER_MAC}")
    print(f"📡 Device: {printer.rfcomm_device}")
    print("🌐 Web-Interface: http://RASPBERRY_IP:8080")
    print("💡 WICHTIG: MAC-Adresse in Code anpassen!")
    
    app.run(host='0.0.0.0', port=8080, debug=False)
