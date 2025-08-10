#!/usr/bin/env python3
"""
Phomemo M110 - DEBUG VERSION für Problemdiagnose
"""

from flask import Flask, request, jsonify, render_template_string
from PIL import Image, ImageDraw, ImageFont
import io
import time
import os
import logging
import subprocess

# Detailliertes Logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

class PhomemoM110:
    def __init__(self, mac_address):
        self.mac_address = mac_address
        self.rfcomm_device = "/dev/rfcomm0"
        self.width_pixels = 384
        self.label_width_pixels = 320
        self.label_offset_x = 72
        logger.info(f"🔵 Initialisiert mit MAC: {mac_address}")
        
    def is_connected(self):
        exists = os.path.exists(self.rfcomm_device)
        logger.debug(f"📡 Device {self.rfcomm_device} exists: {exists}")
        return exists
    
    def check_bluetooth_service(self):
        try:
            result = subprocess.run(['systemctl', 'is-active', 'bluetooth'], 
                                  capture_output=True, text=True)
            status = result.stdout.strip()
            logger.info(f"🔵 Bluetooth service: {status}")
            return status == 'active'
        except Exception as e:
            logger.error(f"❌ Bluetooth service check failed: {e}")
            return False
    
    def scan_devices(self):
        try:
            logger.info("🔍 Scanning for Bluetooth devices...")
            result = subprocess.run(['hcitool', 'scan'], capture_output=True, text=True, timeout=10)
            logger.info(f"📱 Found devices:\n{result.stdout}")
            return self.mac_address in result.stdout
        except Exception as e:
            logger.error(f"❌ Device scan failed: {e}")
            return False
    
    def connect_bluetooth(self):
        try:
            logger.info(f"🔄 Connecting to {self.mac_address}...")
            
            # Check Bluetooth service first
            if not self.check_bluetooth_service():
                logger.error("❌ Bluetooth service not active!")
                return False
            
            # Release existing connection
            logger.debug("🔓 Releasing existing rfcomm connection...")
            subprocess.run(['sudo', 'rfcomm', 'release', '0'], capture_output=True)
            time.sleep(1)
            
            # Try to pair first
            logger.debug("🤝 Attempting to pair/connect...")
            pair_result = subprocess.run([
                'bluetoothctl', '--', 'connect', self.mac_address
            ], capture_output=True, text=True, timeout=10)
            logger.debug(f"Pair result: {pair_result.stdout} | Error: {pair_result.stderr}")
            
            # Create rfcomm connection
            logger.debug("🔗 Creating rfcomm bind...")
            result = subprocess.run([
                'sudo', 'rfcomm', 'bind', '0', self.mac_address
            ], capture_output=True, text=True, timeout=15)
            
            logger.debug(f"rfcomm bind result: {result.returncode}")
            logger.debug(f"stdout: {result.stdout}")
            logger.debug(f"stderr: {result.stderr}")
            
            if result.returncode == 0:
                time.sleep(2)
                success = os.path.exists(self.rfcomm_device)
                logger.info(f"✅ Connection {'successful' if success else 'failed'}")
                return success
            else:
                logger.error(f"❌ rfcomm bind failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("⏱️ Connection timeout")
            return False
        except Exception as e:
            logger.error(f"❌ Connection error: {e}")
            return False
    
    def send_command(self, command_bytes):
        try:
            logger.debug(f"📤 Sending {len(command_bytes)} bytes...")
            
            if not self.is_connected():
                logger.warning("⚠️ Not connected, attempting reconnect...")
                if not self.connect_bluetooth():
                    logger.error("❌ Reconnect failed")
                    return False
            
            with open(self.rfcomm_device, 'wb') as printer:
                printer.write(command_bytes)
                printer.flush()
                logger.debug("✅ Command sent successfully")
            return True
            
        except FileNotFoundError:
            logger.error(f"❌ Device {self.rfcomm_device} not found")
            return False
        except PermissionError:
            logger.error("❌ Permission denied - check sudo rights")
            return False
        except Exception as e:
            logger.error(f"❌ Send error: {e}")
            return False
    
    def print_text(self, text, font_size=24):
        try:
            logger.info(f"🖨️ Printing text: '{text}' (size: {font_size})")
            
            # Initialize printer
            logger.debug("🔧 Initializing printer...")
            if not self.send_command(b'\x1b\x40'):  # Reset
                return False
            time.sleep(0.5)
            
            # Create image
            logger.debug("🖼️ Creating image...")
            img = self.create_text_image(text, font_size)
            image_bytes, height = self.image_to_bytes(img)
            logger.debug(f"📏 Image: {len(image_bytes)} bytes, {height} lines")
            
            # Send image
            logger.debug("📤 Sending image data...")
            return self.send_image_data(image_bytes, height)
            
        except Exception as e:
            logger.error(f"❌ Print error: {e}")
            return False
    
    def create_text_image(self, text, font_size):
        try:
            # Load font
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
                logger.debug("✅ TrueType font loaded")
            except:
                font = ImageFont.load_default()
                logger.debug("⚠️ Using default font")
            
            # Calculate size
            lines = text.replace('\\n', '\n').split('\n')
            img_height = max(80, len(lines) * (font_size + 10))
            logger.debug(f"📐 Image size: {self.width_pixels}x{img_height}")
            
            # Create image
            img = Image.new('RGB', (self.width_pixels, img_height), 'white')
            draw = ImageDraw.Draw(img)
            
            # Draw text
            y_pos = 20
            for i, line in enumerate(lines):
                bbox = draw.textbbox((0, 0), line, font=font)
                line_width = bbox[2] - bbox[0]
                x_pos = self.label_offset_x + (self.label_width_pixels - line_width) // 2
                
                draw.text((x_pos, y_pos), line, fill='black', font=font)
                logger.debug(f"📝 Line {i+1}: '{line}' at ({x_pos}, {y_pos})")
                y_pos += font_size + 5
            
            # Add debug border
            draw.rectangle([(self.label_offset_x, 0), 
                           (self.label_offset_x + self.label_width_pixels, img_height-1)], 
                          outline='gray', width=2)
            
            return img.convert('1')
            
        except Exception as e:
            logger.error(f"❌ Image creation error: {e}")
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
        
        logger.debug(f"🔢 Converted to {len(image_bytes)} bytes")
        return bytes(image_bytes), height
    
    def send_image_data(self, image_bytes, height):
        try:
            bytes_per_line = self.width_pixels // 8  # 48 bytes
            logger.debug(f"📊 Sending {height} lines, {bytes_per_line} bytes per line")
            
            # Send image command
            header = bytes([0x1b, 0x2a, 0x00, bytes_per_line & 0xFF, (bytes_per_line >> 8) & 0xFF])
            logger.debug(f"📋 Header: {header.hex()}")
            
            if not self.send_command(header + image_bytes):
                return False
            
            # Feed paper
            logger.debug("📄 Feeding paper...")
            self.send_command(b'\x1b\x64\x02')
            
            logger.info("✅ Image sent successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Image send error: {e}")
            return False
    
    def get_debug_info(self):
        info = {
            'mac_address': self.mac_address,
            'rfcomm_device': self.rfcomm_device,
            'device_exists': os.path.exists(self.rfcomm_device),
            'bluetooth_service': 'unknown',
            'device_in_scan': False
        }
        
        # Check bluetooth service
        try:
            result = subprocess.run(['systemctl', 'is-active', 'bluetooth'], 
                                  capture_output=True, text=True, timeout=5)
            info['bluetooth_service'] = result.stdout.strip()
        except:
            pass
        
        # Quick device scan
        try:
            result = subprocess.run(['hcitool', 'scan'], capture_output=True, text=True, timeout=8)
            info['device_in_scan'] = self.mac_address in result.stdout
            info['scan_output'] = result.stdout
        except:
            info['scan_output'] = 'Scan failed'
        
        return info

# Web Interface with Debug
WEB_INTERFACE = """
<!DOCTYPE html>
<html>
<head>
    <title>Phomemo M110 DEBUG</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: monospace; margin: 20px; background: #1a1a1a; color: #00ff00; }
        .container { max-width: 1000px; margin: 0 auto; }
        .card { background: #2a2a2a; padding: 20px; margin: 20px 0; border-radius: 10px; border: 1px solid #444; }
        h1 { color: #00ffff; text-align: center; }
        h2 { color: #ffff00; }
        .btn { background: #0066cc; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
        .btn:hover { background: #0088ff; }
        .btn-success { background: #00aa00; }
        .btn-warning { background: #ff8800; }
        .btn-danger { background: #cc0000; }
        textarea, input, select { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #666; border-radius: 5px; background: #333; color: #fff; }
        .status { padding: 15px; margin: 10px 0; border-radius: 5px; font-family: monospace; }
        .success { background: #004400; color: #00ff00; border: 1px solid #008800; }
        .error { background: #440000; color: #ff4444; border: 1px solid #880000; }
        .info { background: #004444; color: #44ffff; border: 1px solid #008888; }
        .debug-info { background: #332200; color: #ffcc00; border: 1px solid #664400; white-space: pre-wrap; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔧 Phomemo M110 DEBUG</h1>
        
        <div class="card">
            <h2>🔍 Debug Information</h2>
            <button class="btn btn-warning" onclick="getDebugInfo()">📊 Debug Info abrufen</button>
            <button class="btn btn-success" onclick="testConnection()">🔌 Verbindung testen</button>
            <button class="btn btn-danger" onclick="scanDevices()">📡 Geräte scannen</button>
            <div id="debugInfo" class="debug-info"></div>
        </div>
        
        <div class="card">
            <h2>🔗 Verbindung</h2>
            <button class="btn btn-success" onclick="checkConnection()">🔍 Status prüfen</button>
            <button class="btn btn-warning" onclick="reconnect()">🔄 Reconnect</button>
            <div id="connectionStatus"></div>
        </div>
        
        <div class="card">
            <h2>📝 Text drucken (DEBUG)</h2>
            <textarea id="textInput" rows="4">DEBUG TEST
Timestamp: ${new Date().toLocaleTimeString()}
Raspberry Pi
✓ Test</textarea>
            <select id="fontSize">
                <option value="16">Klein (16px)</option>
                <option value="20" selected>Normal (20px)</option>
                <option value="24">Groß (24px)</option>
            </select>
            <br>
            <button class="btn" onclick="printText()">🖨️ Text drucken</button>
            <button class="btn btn-success" onclick="testPrint()">🧪 Debug Test</button>
        </div>
        
        <div id="status"></div>
    </div>

    <script>
        function getDebugInfo() {
            showStatus('🔍 Sammle Debug-Informationen...', 'info');
            fetch('/api/debug-info')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('debugInfo').textContent = JSON.stringify(data, null, 2);
                    showStatus('📊 Debug-Info geladen', 'success');
                })
                .catch(error => showStatus('❌ Debug-Info Fehler: ' + error, 'error'));
        }
        
        function testConnection() {
            showStatus('🔌 Teste Verbindung ausführlich...', 'info');
            fetch('/api/test-connection', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    const result = data.success ? 
                        `✅ Verbindungstest erfolgreich\\nDetails: ${JSON.stringify(data, null, 2)}` :
                        `❌ Verbindungstest fehlgeschlagen\\nFehler: ${data.error}`;
                    showStatus(result, data.success ? 'success' : 'error');
                })
                .catch(error => showStatus('❌ Test-Fehler: ' + error, 'error'));
        }
        
        function scanDevices() {
            showStatus('📡 Scanne Bluetooth-Geräte... (10s)', 'info');
            fetch('/api/scan-devices', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    showStatus(`📱 Scan abgeschlossen\\n${data.output}`, 'info');
                })
                .catch(error => showStatus('❌ Scan-Fehler: ' + error, 'error'));
        }
        
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
            
            showStatus('🖨️ Drucke Text... (Debug-Modus)', 'info');
            
            fetch('/api/print-text', { method: 'POST', body: formData })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showStatus('✅ Text gedruckt!', 'success');
                    } else {
                        showStatus('❌ Druckfehler: ' + data.error + '\\nDetails: ' + JSON.stringify(data), 'error');
                    }
                })
                .catch(error => showStatus('❌ Fehler: ' + error, 'error'));
        }
        
        function testPrint() {
            document.getElementById('textInput').value = `DEBUG TEST\\nTimestamp: ${new Date().toLocaleString()}\\nRaspberry Pi\\n✓ Test`;
            printText();
        }
        
        function showStatus(message, type) {
            const statusDiv = document.getElementById('status');
            statusDiv.innerHTML = '<div class="status ' + type + '">' + message.replace(/\\n/g, '<br>') + '</div>';
        }
        
        // Auto-load debug info on start
        window.onload = () => {
            getDebugInfo();
            checkConnection();
        };
    </script>
</body>
</html>
"""

# API Routes with Debug
@app.route('/')
def index():
    return render_template_string(WEB_INTERFACE)

@app.route('/api/debug-info')
def api_debug_info():
    try:
        info = printer.get_debug_info()
        return jsonify(info)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/test-connection', methods=['POST'])
def api_test_connection():
    try:
        logger.info("🧪 Starting connection test...")
        success = printer.connect_bluetooth()
        info = printer.get_debug_info()
        return jsonify({
            'success': success,
            'debug_info': info,
            'message': 'Connection test completed'
        })
    except Exception as e:
        logger.error(f"❌ Connection test error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/scan-devices', methods=['POST'])
def api_scan_devices():
    try:
        logger.info("📡 Starting device scan...")
        found = printer.scan_devices()
        return jsonify({
            'found': found,
            'output': f"Device scan completed. Target device {'found' if found else 'not found'}."
        })
    except Exception as e:
        return jsonify({'found': False, 'output': f'Scan error: {str(e)}'})

@app.route('/api/status')
def api_status():
    try:
        connected = printer.is_connected()
        debug_info = printer.get_debug_info()
        return jsonify({
            'connected': connected,
            'mac': printer.mac_address,
            'device': printer.rfcomm_device,
            'debug': debug_info
        })
    except Exception as e:
        return jsonify({'connected': False, 'error': str(e)})

@app.route('/api/reconnect', methods=['POST'])
def api_reconnect():
    try:
        logger.info("🔄 API Reconnect called")
        success = printer.connect_bluetooth()
        return jsonify({'success': success})
    except Exception as e:
        logger.error(f"❌ API Reconnect error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/print-text', methods=['POST'])
def api_print_text():
    try:
        text = request.form.get('text', '')
        font_size = int(request.form.get('font_size', 20))
        
        logger.info(f"📝 API Print request: '{text}' (size: {font_size})")
        
        if not text.strip():
            return jsonify({'success': False, 'error': 'Kein Text'})
        
        success = printer.print_text(text, font_size)
        return jsonify({'success': success, 'debug': printer.get_debug_info()})
    except Exception as e:
        logger.error(f"❌ API Print error: {e}")
        return jsonify({'success': False, 'error': str(e)})

# Configuration
PRINTER_MAC = "12:7E:5A:E9:E5:22"  # ÄNDERN SIE DIESE MAC-ADRESSE!
printer = PhomemoM110(PRINTER_MAC)

if __name__ == '__main__':
    print("🔧 Phomemo M110 DEBUG VERSION")
    print(f"🔵 Drucker MAC: {PRINTER_MAC}")
    print(f"📡 Device: {printer.rfcomm_device}")
    print("🌐 Web-Interface: http://RASPBERRY_IP:8080")
    print("💡 WICHTIG: MAC-Adresse im Code anpassen!")
    print("🔍 Diese Version zeigt detaillierte Debug-Informationen!")
    
    # Initial debug check
    logger.info("🔍 Starting initial system check...")
    printer.check_bluetooth_service()
    printer.is_connected()
    
    app.run(host='0.0.0.0', port=8080, debug=True)
