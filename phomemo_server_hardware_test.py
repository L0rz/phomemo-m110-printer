#!/usr/bin/env python3
"""
Phomemo M110 - ALTERNATIVE PRINTER COMMANDS
Testet verschiedene Druckerbefehle und -initialisierungen
"""

from flask import Flask, request, jsonify, render_template_string
from PIL import Image, ImageDraw, ImageFont
import time
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

class PhomemoM110Alternative:
    def __init__(self, mac_address):
        self.mac_address = mac_address
        self.rfcomm_device = "/dev/rfcomm0"
        self.width_pixels = 384
        
    def send_command(self, command_bytes):
        try:
            with open(self.rfcomm_device, 'wb') as printer:
                printer.write(command_bytes)
                printer.flush()
            return True
        except Exception as e:
            logger.error(f"Send error: {e}")
            return False
    
    def test_basic_commands(self):
        """Testet verschiedene Grundbefehle"""
        commands = {
            "ESC @": b'\x1b\x40',           # Reset
            "GS V": b'\x1d\x56\x00',       # Cut paper
            "ESC d": b'\x1b\x64\x05',      # Feed 5 lines
            "ESC J": b'\x1b\x4a\x10',      # Feed n/216 inch
            "LF": b'\x0a',                 # Line feed
            "CR": b'\x0d',                 # Carriage return
            "GS !": b'\x1d\x21\x00',      # Character size
        }
        
        results = {}
        for name, cmd in commands.items():
            logger.info(f"Testing command: {name}")
            result = self.send_command(cmd)
            results[name] = result
            time.sleep(0.5)
        
        return results
    
    def test_text_commands(self):
        """Testet Text-Druckbefehle"""
        test_text = "TEST\n"
        
        # Method 1: Direct text
        logger.info("Testing direct text...")
        self.send_command(b'\x1b\x40')  # Reset
        time.sleep(0.1)
        result1 = self.send_command(test_text.encode('utf-8'))
        time.sleep(0.5)
        
        # Method 2: With line feed
        logger.info("Testing text with LF...")
        self.send_command(b'\x1b\x40')  # Reset
        time.sleep(0.1)
        result2 = self.send_command(test_text.encode('utf-8') + b'\x0a\x0a')
        time.sleep(0.5)
        
        # Method 3: ESC/POS style
        logger.info("Testing ESC/POS style...")
        self.send_command(b'\x1b\x40')  # Reset
        time.sleep(0.1)
        self.send_command(b'\x1b\x61\x01')  # Center align
        result3 = self.send_command(test_text.encode('utf-8'))
        self.send_command(b'\x1b\x64\x03')  # Feed 3 lines
        time.sleep(0.5)
        
        return {"direct": result1, "with_lf": result2, "escpos": result3}
    
    def test_alternative_image_method(self, text="ALTERNATIVE"):
        """Alternative Bildübertragung"""
        try:
            # Einfaches 8x8 Test-Pattern
            logger.info("Creating simple test pattern...")
            
            # Reset printer
            self.send_command(b'\x1b\x40')
            time.sleep(0.5)
            
            # Alternative 1: GS v 0 (Raster bit image)
            logger.info("Method 1: GS v 0...")
            width_bytes = 48  # 384/8
            height = 24  # Kleine Testhöhe
            
            # Create simple pattern: diagonal lines
            image_data = bytearray()
            for y in range(height):
                for x in range(width_bytes):
                    if y < 8:
                        # Top: solid line
                        image_data.append(0xFF)
                    elif y < 16:
                        # Middle: diagonal pattern
                        image_data.append(0xAA if x % 2 == 0 else 0x55)
                    else:
                        # Bottom: dots
                        image_data.append(0x88)
            
            # GS v 0 command
            cmd = bytes([
                0x1d, 0x76, 0x30, 0x00,  # GS v 0 (normal)
                width_bytes & 0xFF, (width_bytes >> 8) & 0xFF,  # Width
                height & 0xFF, (height >> 8) & 0xFF,  # Height
            ]) + bytes(image_data)
            
            result1 = self.send_command(cmd)
            time.sleep(1)
            
            # Alternative 2: ESC * (bit image)
            logger.info("Method 2: ESC *...")
            self.send_command(b'\x1b\x40')  # Reset
            time.sleep(0.1)
            
            # Simpler ESC * command
            simple_data = b'\xFF' * 48  # One line of solid black
            cmd2 = b'\x1b\x2a\x00\x30\x00' + simple_data  # ESC * mode width_lo width_hi data
            result2 = self.send_command(cmd2)
            self.send_command(b'\x0a')  # Line feed
            time.sleep(1)
            
            # Alternative 3: Direct bitmap with different header
            logger.info("Method 3: Alternative bitmap...")
            self.send_command(b'\x1b\x40')  # Reset
            time.sleep(0.1)
            
            # Different ESC * variant
            cmd3 = b'\x1b\x2a\x21\x30\x00' + simple_data  # Mode 33 (24-dot)
            result3 = self.send_command(cmd3)
            self.send_command(b'\x0a\x0a')  # Double line feed
            
            return {"gs_v": result1, "esc_star": result2, "alt_bitmap": result3}
            
        except Exception as e:
            logger.error(f"Alternative image method error: {e}")
            return {"error": str(e)}
    
    def test_paper_feed(self):
        """Testet verschiedene Paper-Feed Methoden"""
        feeds = {
            "LF": b'\x0a',
            "CR+LF": b'\x0d\x0a', 
            "ESC d 1": b'\x1b\x64\x01',
            "ESC d 3": b'\x1b\x64\x03',
            "ESC d 5": b'\x1b\x64\x05',
            "ESC J": b'\x1b\x4a\x20',
            "GS V cut": b'\x1d\x56\x00',
        }
        
        results = {}
        for name, cmd in feeds.items():
            logger.info(f"Testing feed: {name}")
            result = self.send_command(cmd)
            results[name] = result
            time.sleep(1)
        
        return results

# Web Interface für Tests
WEB_INTERFACE = """
<!DOCTYPE html>
<html>
<head>
    <title>Phomemo M110 Hardware Tests</title>
    <meta charset="UTF-8">
    <style>
        body { font-family: monospace; margin: 20px; background: #000; color: #0f0; }
        .container { max-width: 1000px; margin: 0 auto; }
        .card { background: #111; padding: 20px; margin: 20px 0; border: 1px solid #333; border-radius: 5px; }
        h1 { color: #0ff; text-align: center; }
        h2 { color: #ff0; }
        .btn { background: #006600; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
        .btn:hover { background: #008800; }
        .btn-test { background: #cc6600; }
        .btn-danger { background: #cc0000; }
        pre { background: #222; padding: 10px; border-radius: 3px; overflow-x: auto; }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .success { background: #004400; color: #00ff00; }
        .error { background: #440000; color: #ff4444; }
        .info { background: #004444; color: #44ffff; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔧 Phomemo M110 Hardware Tests</h1>
        
        <div class="card">
            <h2>🎯 Basis-Kommandos testen</h2>
            <p>Testet grundlegende Druckerbefehle (Reset, Feed, etc.)</p>
            <button class="btn btn-test" onclick="testBasicCommands()">📋 Basis-Kommandos</button>
            <button class="btn btn-test" onclick="testTextCommands()">📝 Text-Kommandos</button>
            <button class="btn btn-test" onclick="testPaperFeed()">📄 Paper Feed Tests</button>
        </div>
        
        <div class="card">
            <h2>🖼️ Alternative Bild-Methoden</h2>
            <p>Testet verschiedene Bildübertragungsarten</p>
            <button class="btn" onclick="testAlternativeImage()">🎨 Alternative Bildmethoden</button>
        </div>
        
        <div class="card">
            <h2>⚡ Notfall-Kommandos</h2>
            <p>Für hartnäckige Fälle</p>
            <button class="btn btn-danger" onclick="emergencyReset()">🔴 Emergency Reset</button>
            <button class="btn btn-danger" onclick="emergencyFeed()">📄 Emergency Feed</button>
        </div>
        
        <div id="results"></div>
    </div>

    <script>
        function testBasicCommands() {
            showStatus('🧪 Teste Basis-Kommandos...', 'info');
            fetch('/api/test-basic', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    showResults('Basis-Kommandos', data);
                })
                .catch(error => showStatus('❌ Fehler: ' + error, 'error'));
        }
        
        function testTextCommands() {
            showStatus('📝 Teste Text-Kommandos...', 'info');
            fetch('/api/test-text', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    showResults('Text-Kommandos', data);
                })
                .catch(error => showStatus('❌ Fehler: ' + error, 'error'));
        }
        
        function testPaperFeed() {
            showStatus('📄 Teste Paper Feed...', 'info');
            fetch('/api/test-feed', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    showResults('Paper Feed', data);
                })
                .catch(error => showStatus('❌ Fehler: ' + error, 'error'));
        }
        
        function testAlternativeImage() {
            showStatus('🎨 Teste alternative Bildmethoden...', 'info');
            fetch('/api/test-alt-image', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    showResults('Alternative Bildmethoden', data);
                })
                .catch(error => showStatus('❌ Fehler: ' + error, 'error'));
        }
        
        function emergencyReset() {
            showStatus('🔴 Emergency Reset...', 'info');
            fetch('/api/emergency-reset', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    showStatus('🔴 Emergency Reset ausgeführt', data.success ? 'success' : 'error');
                })
                .catch(error => showStatus('❌ Fehler: ' + error, 'error'));
        }
        
        function emergencyFeed() {
            showStatus('📄 Emergency Feed...', 'info');
            fetch('/api/emergency-feed', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    showStatus('📄 Emergency Feed ausgeführt', data.success ? 'success' : 'error');
                })
                .catch(error => showStatus('❌ Fehler: ' + error, 'error'));
        }
        
        function showResults(title, data) {
            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = `
                <div class="card">
                    <h2>📊 ${title} - Ergebnisse</h2>
                    <pre>${JSON.stringify(data, null, 2)}</pre>
                </div>
            ` + resultsDiv.innerHTML;
        }
        
        function showStatus(message, type) {
            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = `
                <div class="status ${type}">${message}</div>
            ` + resultsDiv.innerHTML;
        }
    </script>
</body>
</html>
"""

# API Routes
@app.route('/')
def index():
    return render_template_string(WEB_INTERFACE)

@app.route('/api/test-basic', methods=['POST'])
def api_test_basic():
    try:
        results = printer.test_basic_commands()
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/test-text', methods=['POST'])
def api_test_text():
    try:
        results = printer.test_text_commands()
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/test-feed', methods=['POST'])
def api_test_feed():
    try:
        results = printer.test_paper_feed()
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/test-alt-image', methods=['POST'])
def api_test_alt_image():
    try:
        results = printer.test_alternative_image_method()
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/emergency-reset', methods=['POST'])
def api_emergency_reset():
    try:
        # Multiple reset commands
        commands = [
            b'\x1b\x40',      # ESC @
            b'\x1b\x21\x00',  # ESC !
            b'\x1d\x21\x00',  # GS !
            b'\x1b\x74\x00',  # Character set
        ]
        
        for cmd in commands:
            printer.send_command(cmd)
            time.sleep(0.2)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/emergency-feed', methods=['POST'])
def api_emergency_feed():
    try:
        # Multiple feed commands
        commands = [
            b'\x0a\x0a\x0a',      # Triple LF
            b'\x1b\x64\x05',      # ESC d 5
            b'\x1b\x4a\x30',      # ESC J
            b'\x1d\x56\x00',      # Cut (if supported)
        ]
        
        for cmd in commands:
            printer.send_command(cmd)
            time.sleep(0.5)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Configuration
PRINTER_MAC = "12:7E:5A:E9:E5:22"
printer = PhomemoM110Alternative(PRINTER_MAC)

if __name__ == '__main__':
    print("🔧 Phomemo M110 HARDWARE TEST VERSION")
    print("🎯 Testet verschiedene Druckerbefehle und -methoden")
    print("🌐 Web-Interface: http://RASPBERRY_IP:8080")
    
    app.run(host='0.0.0.0', port=8080, debug=False)
