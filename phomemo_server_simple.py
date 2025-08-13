#!/usr/bin/env python3
"""
Phomemo M110 Printer - KORRIGIERTE VERSION für Raspberry Pi
Fixes für korrekten Text-Druck
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
        self.width_pixels = 384  # Phomemo M110 Standard
        self.bytes_per_line = 48  # 384 / 8
        
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
                time.sleep(0.1)  # Kurze Pause zwischen Befehlen
            return True
        except Exception as e:
            logger.error(f"Send error: {e}")
            return False
    
    def print_text(self, text, font_size=24):
        try:
            logger.info(f"Printing text: {text[:50]}...")
            
            # Drucker initialisieren
            if not self.send_command(b'\x1b\x40'):  # ESC @
                return False
            time.sleep(0.5)
            
            # Bild erstellen
            img = self.create_text_image(text, font_size)
            if img is None:
                return False
            
            # Bild zu Bytes konvertieren
            image_data = self.image_to_printer_format(img)
            if not image_data:
                return False
            
            # Bild senden
            success = self.send_bitmap(image_data, img.height)
            
            if success:
                # Papier vorschub
                self.send_command(b'\x1b\x64\x03')  # ESC d 3 - Feed 3 lines
                time.sleep(0.5)
            
            return success
            
        except Exception as e:
            logger.error(f"Print error: {e}")
            return False
    
    def create_text_image(self, text, font_size):
        try:
            # Font laden
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf", font_size)
                except:
                    font = ImageFont.load_default()
            
            # Text vorbereiten
            lines = text.replace('\\n', '\n').split('\n')
            
            # Bildgröße berechnen
            temp_img = Image.new('RGB', (1, 1), 'white')
            temp_draw = ImageDraw.Draw(temp_img)
            
            line_heights = []
            max_width = 0
            
            for line in lines:
                bbox = temp_draw.textbbox((0, 0), line, font=font)
                line_width = bbox[2] - bbox[0]
                line_height = bbox[3] - bbox[1]
                max_width = max(max_width, line_width)
                line_heights.append(line_height)
            
            # Bild erstellen
            total_height = sum(line_heights) + (len(lines) - 1) * 5 + 40  # Padding
            img = Image.new('RGB', (self.width_pixels, total_height), 'white')
            draw = ImageDraw.Draw(img)
            
            # Text zeichnen
            y_pos = 20
            for i, line in enumerate(lines):
                if line.strip():  # Nur nicht-leere Zeilen
                    bbox = draw.textbbox((0, 0), line, font=font)
                    line_width = bbox[2] - bbox[0]
                    x_pos = (self.width_pixels - line_width) // 2  # Zentriert
                    
                    draw.text((x_pos, y_pos), line, fill='black', font=font)
                
                y_pos += line_heights[i] + 5
            
            # Zu schwarz-weiß konvertieren
            return img.convert('1')
            
        except Exception as e:
            logger.error(f"Image creation error: {e}")
            return None
    
    def image_to_printer_format(self, img):
        try:
            width, height = img.size
            pixels = list(img.getdata())
            
            # Bild-Daten für Drucker vorbereiten
            image_bytes = []
            
            for y in range(height):
                line_bytes = []
                for x in range(0, self.width_pixels, 8):
                    byte_value = 0
                    for bit in range(8):
                        pixel_x = x + bit
                        if pixel_x < width:
                            pixel_idx = y * width + pixel_x
                            if pixel_idx < len(pixels):
                                # Schwarz = 1 bit, Weiß = 0 bit
                                if pixels[pixel_idx] == 0:  # Schwarz
                                    byte_value |= (1 << (7 - bit))
                    line_bytes.append(byte_value)
                
                # Padding auf bytes_per_line
                while len(line_bytes) < self.bytes_per_line:
                    line_bytes.append(0)
                
                image_bytes.extend(line_bytes[:self.bytes_per_line])
            
            return bytes(image_bytes)
            
        except Exception as e:
            logger.error(f"Image conversion error: {e}")
            return None
    
    def send_bitmap(self, image_data, height):
        """
        Sends a raster bitmap to the M110 using the ESC/POS GS v 0 command.
        This implementation correctly constructs the raster header (width in bytes and height in dots) and sends the
        image data in small chunks. A small feed is applied afterwards to avoid clipping.
        """
        try:
            logger.info(f"Sending raster bitmap: {len(image_data)} bytes, height: {height}")
            
            # Prepare ESC/POS raster header: GS v 0 m xL xH yL yH
            # m = 0 (normal density). Width (in bytes) and height (in dots).
            width_bytes = self.bytes_per_line
            xL = width_bytes & 0xFF
            xH = (width_bytes >> 8) & 0xFF
            yL = height & 0xFF
            yH = (height >> 8) & 0xFF
            header = bytes([0x1D, 0x76, 0x30, 0x00, xL, xH, yL, yH])
            
            # Send header
            if not self.send_command(header):
                return False
            
            # Send image data in manageable chunks
            chunk_size = 1024
            for i in range(0, len(image_data), chunk_size):
                chunk = image_data[i : i + chunk_size]
                if not self.send_command(chunk):
                    return False
                time.sleep(0.01)  # Brief pause between chunks
            
            # Add a small feed after printing to ensure the last line is clear
            self.send_command(b'\x1b\x64\x03')  # ESC d 3
            return True
            
        except Exception as e:
            logger.error(f"Bitmap send error: {e}")
            return False

# Web Interface (gleich wie vorher)
WEB_INTERFACE = """



 Phomemo M110 Drucker - Fixed 
 
 
 
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
        .debug { background: #f8f9fa; border: 1px solid #dee2e6; padding: 10px; margin: 10px 0; border-radius: 5px; font-family: monospace; font-size: 12px; }
 


 
 🖨️ Phomemo M110 Drucker (Fixed) 
        
 
 🔗 Verbindung 
 🔍 Status prüfen 
 🔄 Reconnect 
 
 
        
 
 
 📝 Text drucken 
 PHOMEMO TEST
40×30mm Label
✓ Funktioniert!
Zeit: $TIME$ 
 
 Sehr Klein (14px) 
 Klein (18px) 
 Normal (22px) 
 Groß (26px) 
 Extra Groß (30px) 
 
 
 🖨️ Text drucken 
 🧪 Test Label 
 
            
 
 🛠️ Debug 
 🔧 Test Bluetooth 
 🔄 Init Drucker 
 
 
 
        
 
 

 
        function checkConnection() {
            showStatus('🔍 Prüfe Verbindung...', 'info');
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    const status = data.connected ? 
                        '<div class="success">✅ Drucker verbunden</div>' : 
                        '<div class="error">❌ Drucker nicht verbunden</div>';
                    document.getElementById('connectionStatus').innerHTML = status;
                    
                    document.getElementById('debugInfo').innerHTML = 
                        `MAC: ${data.mac}<br>Device: ${data.device}<br>Connected: ${data.connected}`;
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
                        showStatus('❌ Reconnect fehlgeschlagen: ' + (data.error || ''), 'error');
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
            
            // Replace $TIME$ placeholder
            const finalText = text.replace('$TIME$', new Date().toLocaleTimeString());
            
            const formData = new FormData();
            formData.append('text', finalText);
            formData.append('font_size', fontSize);
            
            showStatus('🖨️ Drucke Text...', 'info');
            
            fetch('/api/print-text', { method: 'POST', body: formData })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showStatus('✅ Text gedruckt!', 'success');
                    } else {
                        showStatus('❌ Druckfehler: ' + (data.error || 'Unbekannter Fehler'), 'error');
                    }
                })
                .catch(error => showStatus('❌ Fehler: ' + error, 'error'));
        }
        
        function testLabel() {
            document.getElementById('textInput').value = 
                'PHOMEMO M110\nRaspberry Pi\n' + 
                new Date().toLocaleDateString() + '\n' +
                new Date().toLocaleTimeString() + '\n' +
                '✓ Test erfolgreich';
            printText();
        }
        
        function testConnection() {
            showStatus('🔧 Teste Bluetooth-Verbindung...', 'info');
            fetch('/api/test-connection', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    document.getElementById('debugInfo').innerHTML = 
                        `Test Result: ${data.success}<br>` +
                        `Message: ${data.message || ''}<br>` +
                        `Error: ${data.error || 'None'}`;
                    
                    if (data.success) {
                        showStatus('✅ Bluetooth-Test erfolgreich!', 'success');
                    } else {
                        showStatus('❌ Bluetooth-Test fehlgeschlagen', 'error');
                    }
                })
                .catch(error => showStatus('❌ Test-Fehler: ' + error, 'error'));
        }
        
        function initPrinter() {
            showStatus('🔄 Initialisiere Drucker...', 'info');
            fetch('/api/init-printer', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showStatus('✅ Drucker initialisiert!', 'success');
                    } else {
                        showStatus('❌ Init fehlgeschlagen: ' + (data.error || ''), 'error');
                    }
                })
                .catch(error => showStatus('❌ Init-Fehler: ' + error, 'error'));
        }
        
        function showStatus(message, type) {
            const statusDiv = document.getElementById('status');
            statusDiv.innerHTML = '<div class="status ' + type + '">' + message + '</div>';
            setTimeout(() => statusDiv.innerHTML = '', 8000);
        }
        
        // Auto-check connection on load
        window.onload = checkConnection;
 


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
        font_size = int(request.form.get('font_size', 22))
        
        if not text.strip():
            return jsonify({'success': False, 'error': 'Kein Text'})
        
        success = printer.print_text(text, font_size)
        return jsonify({'success': success})
    except Exception as e:
        logger.error(f"API print error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/test-connection', methods=['POST'])
def api_test_connection():
    try:
        # Test basic connectivity
        connected = printer.is_connected()
        if not connected:
            reconnect_success = printer.connect_bluetooth()
            return jsonify({
                'success': reconnect_success,
                'message': 'Reconnected' if reconnect_success else 'Failed to connect'
            })
        
        # Test sending a simple command
        test_success = printer.send_command(b'\x1b\x40')  # Reset command
        return jsonify({
            'success': test_success,
            'message': 'Command sent successfully' if test_success else 'Failed to send command'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/init-printer', methods=['POST'])
def api_init_printer():
    try:
        # Initialize printer with multiple commands
        commands = [
            b'\x1b\x40',      # ESC @ - Reset
            b'\x1b\x33\x00',  # ESC 3 0 - Set line spacing
            b'\x1b\x61\x01'   # ESC a 1 - Center align
        ]
        
        success = True
        for cmd in commands:
            if not printer.send_command(cmd):
                success = False
                break
            time.sleep(0.2)
        
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Configuration
PRINTER_MAC = "12:7E:5A:E9:E5:22"  # ÄNDERN SIE DIESE MAC-ADRESSE!
printer = PhomemoM110(PRINTER_MAC)

if __name__ == '__main__':
    print("🍓 Phomemo M110 für Raspberry Pi (FIXED VERSION)")
    print(f"🔵 Drucker MAC: {PRINTER_MAC}")
    print(f"📡 Device: {printer.rfcomm_device}")
    print("🌐 Web-Interface: http://RASPBERRY_IP:8080")
    print("💡 WICHTIG: MAC-Adresse in Code anpassen!")
    print("🔧 Neue Features: Debug-Tools, verbesserte Bitmap-Übertragung")
    
    app.run(host='0.0.0.0', port=8080, debug=False)
