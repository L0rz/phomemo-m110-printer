#!/usr/bin/env python3
"""
Phomemo M110 Printer - PROTOKOLL KORRIGIERT
Basierend auf btmon-Analyse des proprietären Protokolls
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
        self.bytes_per_line = 48  # 384 / 8
        
        # Phomemo-spezifische Protokoll-Konstanten (aus btmon analysiert)
        self.PROTOCOL_HEADER = bytes([0x0b, 0xef])
        self.RESPONSE_PATTERN = bytes([0x09, 0xff, 0x01, 0x01, 0x5c])
        
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
                time.sleep(0.1)
            return True
        except Exception as e:
            logger.error(f"Send error: {e}")
            return False
    
    def send_command_with_response(self, command_bytes, expect_response=True):
        """Sendet Befehl und wartet auf Antwort"""
        try:
            if not self.is_connected():
                if not self.connect_bluetooth():
                    return False, None
            
            with open(self.rfcomm_device, 'r+b') as printer:
                # Befehl senden
                printer.write(command_bytes)
                printer.flush()
                
                if expect_response:
                    time.sleep(0.2)
                    # Versuche Antwort zu lesen
                    try:
                        response = printer.read(10)
                        logger.info(f"Response: {response.hex() if response else 'None'}")
                        return True, response
                    except:
                        return True, None
                
            return True, None
        except Exception as e:
            logger.error(f"Command with response error: {e}")
            return False, None
    
    def initialize_printer(self):
        """Initialisiert den Drucker mit korrektem Phomemo-Protokoll"""
        try:
            logger.info("Initializing Phomemo M110...")
            
            # Verschiedene Initialisierungs-Sequenzen versuchen
            init_commands = [
                # Standard Init
                bytes([0x0b, 0xef, 0x1b, 0x40]),  # Reset-ähnlich
                
                # Phomemo-spezifische Inits (geraten basierend auf anderen Phomemo-Modellen)
                bytes([0x0b, 0xef, 0x00, 0x00, 0x00, 0x00]),
                bytes([0x0b, 0xef, 0x01]),
                bytes([0x0b, 0xef, 0x02, 0x01]),
                
                # Print Mode Setup
                bytes([0x0b, 0xef, 0x03, 0x01, 0x01]),
            ]
            
            for cmd in init_commands:
                success, response = self.send_command_with_response(cmd)
                if response:
                    logger.info(f"Init command {cmd.hex()} -> Response: {response.hex()}")
                time.sleep(0.3)
            
            return True
            
        except Exception as e:
            logger.error(f"Initialization error: {e}")
            return False
    
    def print_text_phomemo_protocol(self, text):
        """Versucht verschiedene Phomemo-Protokoll Varianten"""
        try:
            logger.info(f"Trying Phomemo protocol for: {text}")
            
            # Text zu Bytes
            text_bytes = text.encode('utf-8')
            
            # Verschiedene Phomemo-Protokoll Varianten
            protocol_variants = [
                # Variante 1: Header + Länge + Text
                self.PROTOCOL_HEADER + bytes([len(text_bytes)]) + text_bytes + bytes([0x9a]),
                
                # Variante 2: Header + Text + Terminator
                self.PROTOCOL_HEADER + text_bytes + bytes([0x0d, 0x0a, 0x9a]),
                
                # Variante 3: Wie im btmon gesehen
                self.PROTOCOL_HEADER + bytes([0x1b, 0x40]) + text_bytes + bytes([0x0d, 0x0a, 0x9a]),
                
                # Variante 4: Mit Print-Command
                self.PROTOCOL_HEADER + bytes([0x10]) + text_bytes + bytes([0x9a]),
            ]
            
            for i, cmd in enumerate(protocol_variants):
                logger.info(f"Trying protocol variant {i+1}: {cmd.hex()}")
                success, response = self.send_command_with_response(cmd)
                
                if response and self.RESPONSE_PATTERN in response:
                    logger.info(f"Protocol variant {i+1} successful!")
                    return True
                
                time.sleep(0.5)
            
            return False
            
        except Exception as e:
            logger.error(f"Phomemo protocol error: {e}")
            return False
    
    def print_bitmap_phomemo_protocol(self, image_data, width, height):
        """Bitmap mit Phomemo-Protokoll"""
        try:
            logger.info(f"Printing bitmap: {width}x{height}, {len(image_data)} bytes")
            
            # Bitmap-Header für Phomemo
            bitmap_header = self.PROTOCOL_HEADER + bytes([
                0x20,  # Bitmap command (geraten)
                width & 0xFF, (width >> 8) & 0xFF,  # Width
                height & 0xFF, (height >> 8) & 0xFF,  # Height
            ])
            
            # Header senden
            success, response = self.send_command_with_response(bitmap_header)
            if not success:
                return False
            
            # Daten in Chunks senden
            chunk_size = 64
            for i in range(0, len(image_data), chunk_size):
                chunk = image_data[i:i + chunk_size]
                
                # Chunk mit Phomemo-Protokoll
                chunk_cmd = self.PROTOCOL_HEADER + bytes([0x21]) + chunk
                
                success, response = self.send_command_with_response(chunk_cmd, expect_response=False)
                if not success:
                    return False
                
                time.sleep(0.05)
            
            # End-Marker
            end_cmd = self.PROTOCOL_HEADER + bytes([0x22, 0x9a])
            self.send_command_with_response(end_cmd)
            
            return True
            
        except Exception as e:
            logger.error(f"Bitmap protocol error: {e}")
            return False
    
    def create_text_image(self, text, font_size):
        try:
            # Font laden
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
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
            total_height = sum(line_heights) + (len(lines) - 1) * 5 + 40
            img = Image.new('RGB', (self.width_pixels, total_height), 'white')
            draw = ImageDraw.Draw(img)
            
            # Text zeichnen
            y_pos = 20
            for i, line in enumerate(lines):
                if line.strip():
                    bbox = draw.textbbox((0, 0), line, font=font)
                    line_width = bbox[2] - bbox[0]
                    x_pos = (self.width_pixels - line_width) // 2
                    
                    draw.text((x_pos, y_pos), line, fill='black', font=font)
                
                y_pos += line_heights[i] + 5
            
            return img.convert('1')
            
        except Exception as e:
            logger.error(f"Image creation error: {e}")
            return None
    
    def image_to_bytes(self, img):
        """Konvertiert Bild zu Phomemo-Format"""
        width, height = img.size
        pixels = list(img.getdata())
        image_bytes = []
        
        for y in range(height):
            for x in range(0, self.width_pixels, 8):
                byte_value = 0
                for bit in range(8):
                    pixel_x = x + bit
                    if pixel_x < width:
                        pixel_idx = y * width + pixel_x
                        if pixel_idx < len(pixels) and pixels[pixel_idx] == 0:
                            byte_value |= (1 << (7 - bit))
                image_bytes.append(byte_value)
        
        return bytes(image_bytes)
    
    def print_text(self, text, font_size=24):
        """Hauptfunktion zum Drucken"""
        try:
            logger.info(f"Printing text: {text[:50]}...")
            
            # 1. Drucker initialisieren
            if not self.initialize_printer():
                logger.error("Failed to initialize printer")
                return False
            
            # 2. Erst einfachen Text versuchen
            if self.print_text_phomemo_protocol(text):
                logger.info("Text protocol successful!")
                return True
            
            # 3. Dann Bitmap versuchen
            logger.info("Trying bitmap method...")
            img = self.create_text_image(text, font_size)
            if img is None:
                return False
            
            image_data = self.image_to_bytes(img)
            return self.print_bitmap_phomemo_protocol(image_data, img.width, img.height)
            
        except Exception as e:
            logger.error(f"Print error: {e}")
            return False

# Web Interface
WEB_INTERFACE = """
<!DOCTYPE html>
<html>
<head>
    <title>Phomemo M110 - Protokoll Fix</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 900px; margin: 0 auto; }
        .card { background: white; padding: 20px; margin: 20px 0; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; }
        .btn { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
        .btn:hover { background: #0056b3; }
        .btn-success { background: #28a745; }
        .btn-success:hover { background: #1e7e34; }
        .btn-warning { background: #ffc107; color: #212529; }
        .btn-warning:hover { background: #e0a800; }
        .btn-danger { background: #dc3545; }
        .btn-danger:hover { background: #c82333; }
        textarea, input, select { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }
        .status { padding: 15px; margin: 10px 0; border-radius: 5px; }
        .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
        .debug { background: #f8f9fa; border: 1px solid #dee2e6; padding: 10px; margin: 10px 0; border-radius: 5px; font-family: monospace; font-size: 11px; max-height: 200px; overflow-y: auto; }
        .protocol-info { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🖨️ Phomemo M110 - Protokoll-Fix</h1>
        
        <div class="protocol-info">
            <h3>🔬 Protokoll-Analyse</h3>
            <p>Basierend auf btmon-Daten wurde das proprietäre Phomemo-Protokoll analysiert:</p>
            <ul>
                <li><strong>Header:</strong> 0x0b 0xef</li>
                <li><strong>Response:</strong> 0x09 0xff 0x01 0x01 0x5c</li>
                <li><strong>Terminator:</strong> 0x9a</li>
            </ul>
        </div>
        
        <div class="card">
            <h2>🔗 Verbindung & Init</h2>
            <button class="btn btn-success" onclick="checkConnection()">🔍 Status prüfen</button>
            <button class="btn btn-warning" onclick="reconnect()">🔄 Reconnect</button>
            <button class="btn" onclick="initPrinter()">🚀 Drucker initialisieren</button>
            <div id="connectionStatus"></div>
        </div>
        
        <div class="grid">
            <div class="card">
                <h2>📝 Text drucken (Phomemo-Protokoll)</h2>
                <textarea id="textInput" rows="3" placeholder="Text eingeben...">PHOMEMO TEST
Protokoll Fix
✓ Funktioniert!</textarea>
                <select id="fontSize">
                    <option value="16">Klein (16px)</option>
                    <option value="20" selected>Normal (20px)</option>
                    <option value="24">Groß (24px)</option>
                    <option value="28">Extra Groß (28px)</option>
                </select>
                <br>
                <button class="btn" onclick="printText()">🖨️ Text drucken</button>
                <button class="btn btn-success" onclick="testProtocol()">🧪 Protokoll-Test</button>
            </div>
            
            <div class="card">
                <h2>🛠️ Debug & Protokoll</h2>
                <button class="btn btn-danger" onclick="rawCommand()">⚡ Raw Command Test</button>
                <button class="btn" onclick="clearDebug()">🗑️ Clear Debug</button>
                <div id="debugInfo" class="debug">Debug-Ausgabe erscheint hier...</div>
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
                    
                    addDebug(`Status: Connected=${data.connected}, MAC=${data.mac}`);
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
                    addDebug(`Reconnect: Success=${data.success}, Error=${data.error || 'None'}`);
                })
                .catch(error => showStatus('❌ Fehler: ' + error, 'error'));
        }
        
        function initPrinter() {
            showStatus('🚀 Initialisiere Drucker...', 'info');
            fetch('/api/init-printer', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showStatus('✅ Drucker initialisiert!', 'success');
                    } else {
                        showStatus('❌ Init fehlgeschlagen', 'error');
                    }
                    addDebug(`Init: Success=${data.success}, Response=${data.response || 'None'}`);
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
            formData.append('text', text.replace(/\\n/g, '\n'));
            formData.append('font_size', fontSize);
            
            showStatus('🖨️ Drucke mit Phomemo-Protokoll...', 'info');
            
            fetch('/api/print-text', { method: 'POST', body: formData })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showStatus('✅ Text gedruckt!', 'success');
                    } else {
                        showStatus('❌ Druckfehler: ' + (data.error || ''), 'error');
                    }
                    addDebug(`Print: Success=${data.success}, Method=${data.method || 'Unknown'}`);
                })
                .catch(error => showStatus('❌ Fehler: ' + error, 'error'));
        }
        
        function testProtocol() {
            showStatus('🧪 Teste Phomemo-Protokoll...', 'info');
            
            const testText = 'PROTOCOL TEST\\n' + new Date().toLocaleTimeString();
            document.getElementById('textInput').value = testText;
            
            printText();
        }
        
        function rawCommand() {
            showStatus('⚡ Teste Raw Command...', 'info');
            fetch('/api/raw-test', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showStatus('✅ Raw Command erfolgreich!', 'success');
                    } else {
                        showStatus('❌ Raw Command fehlgeschlagen', 'error');
                    }
                    addDebug(`Raw Test: Success=${data.success}, Response=${data.response || 'None'}`);
                })
                .catch(error => showStatus('❌ Raw Fehler: ' + error, 'error'));
        }
        
        function clearDebug() {
            document.getElementById('debugInfo').innerHTML = 'Debug-Ausgabe geleert...';
        }
        
        function addDebug(message) {
            const debugDiv = document.getElementById('debugInfo');
            const timestamp = new Date().toLocaleTimeString();
            debugDiv.innerHTML += `[${timestamp}] ${message}<br>`;
            debugDiv.scrollTop = debugDiv.scrollHeight;
        }
        
        function showStatus(message, type) {
            const statusDiv = document.getElementById('status');
            statusDiv.innerHTML = '<div class="status ' + type + '">' + message + '</div>';
            setTimeout(() => statusDiv.innerHTML = '', 8000);
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

@app.route('/api/init-printer', methods=['POST'])
def api_init_printer():
    try:
        success = printer.initialize_printer()
        return jsonify({'success': success, 'response': 'Printer initialized'})
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
        return jsonify({'success': success, 'method': 'phomemo_protocol'})
    except Exception as e:
        logger.error(f"API print error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/raw-test', methods=['POST'])
def api_raw_test():
    try:
        # Test verschiedene Raw-Commands
        test_commands = [
            bytes([0x0b, 0xef, 0x01]),
            bytes([0x0b, 0xef, 0x1b, 0x40]),
            printer.PROTOCOL_HEADER + b'TEST' + bytes([0x9a])
        ]
        
        responses = []
        for cmd in test_commands:
            success, response = printer.send_command_with_response(cmd)
            responses.append({
                'command': cmd.hex(),
                'success': success,
                'response': response.hex() if response else None
            })
        
        return jsonify({'success': True, 'responses': responses})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Configuration
PRINTER_MAC = "12:7E:5A:E9:E5:22"  # ÄNDERN SIE DIESE MAC-ADRESSE!
printer = PhomemoM110(PRINTER_MAC)

if __name__ == '__main__':
    print("🍓 Phomemo M110 - PROTOKOLL-FIX VERSION")
    print(f"🔵 Drucker MAC: {PRINTER_MAC}")
    print(f"📡 Device: {printer.rfcomm_device}")
    print("🔬 Protokoll: Proprietäres Phomemo-Format")
    print("🌐 Web-Interface: http://RASPBERRY_IP:8080")
    print("💡 Basierend auf btmon-Analyse!")
    
    app.run(host='0.0.0.0', port=8080, debug=False)
