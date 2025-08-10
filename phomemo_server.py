#!/usr/bin/env python3
"""
Phomemo M110 Text-zu-Bild Drucker
Konvertiert Text in Bilder und druckt sie
Korrigiert für 40x30mm Labels mit Y-Offset Funktionalität
"""

from flask import Flask, request, jsonify, render_template_string
from PIL import Image, ImageDraw, ImageFont
import io
import time
import os

WEB_INTERFACE = """
<div class="font-controls">
    <label for="fontSize">Schriftgröße:</label>

        .catch(error => {
            showStatus('❌ Verbindungsfehler: ' + error, 'error');
        });
    }
    
    function testText() {
        document.getElementById('textInput').value = 'Test Label\n40×30mm\n✓ OK';
        printText();
    }
    
    function printImage() {
        const fileInput = document.getElementById('imageFile');
        
        if (!fileInput.files[0]) {
            showStatus('Bitte wähle ein Bild aus!', 'error');
            return;
        }
        
        const formData = new FormData();
        formData.append('image', fileInput.files[0]);
        
        showStatus('🖨️ Drucke Bild...', 'info');
        
        fetch('/api/print-image', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showStatus('✅ Bild erfolgreich gedruckt!', 'success');
            } else {
                showStatus('❌ Fehler: ' + data.error, 'error');
            }
        })
        .catch(error => {
            showStatus('❌ Verbindungsfehler: ' + error, 'error');
        });
    }
    
    function showStatus(message, type) {
        const statusDiv = document.getElementById('status');
        statusDiv.innerHTML = '<div class="status ' + type + '">' + message + '</div>';
    }
</script>
</body>
</html>
"""

    
    def print_calibration_text(self, text, font_size=16, offset_x=72, offset_y=0, show_frame=True, feed_lines=1):
        """Spezieller Kalibrierungs-Druck mit anpassbaren X/Y-Parametern"""
        logger.info(f"Kalibrierungs-Druck: X={offset_x}px, Y={offset_y}px, Frame={show_frame}, Feed={feed_lines}")
        
        if not self.is_connected():
            logger.error("Keine rfcomm-Verbindung")
            return False
        
        try:
            # Drucker initialisieren
            self.initialize_printer()
            
            # Bild mit Kalibrierungs-Text erstellen
            img = self.create_calibration_image(text, font_size, offset_x, offset_y, show_frame)
            image_bytes, height = self.image_to_bytes(img)
            
            # Drucken
            self._send_image_block(image_bytes, height)
            
            # Konfigurierbarer Feed
            if feed_lines > 0:
                feed_cmd = bytes([0x1b, 0x64, feed_lines])  # ESC d n
                self.send_command(feed_cmd)
            
            logger.info(f"Kalibrierung gedruckt: {height} Zeilen, Feed: {feed_lines}")
            return True
            
        except Exception as e:
            logger.error(f"Kalibrierungs-Druckfehler: {e}")
            return False
    
    def create_calibration_image(self, text, font_size, offset_x, offset_y, show_frame):
        """Kalibrierungs-Bild für 30mm Label - KORRIGIERT für exakte Positionierung"""
        try:
            # Font laden
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            # Text-Höhe berechnen
            temp_img = Image.new('RGB', (1, 1), 'white')
            temp_draw = ImageDraw.Draw(temp_img)
            lines = text.split('\\n')
            text_height = sum([temp_draw.textbbox((0, 0), line, font=font)[3] - temp_draw.textbbox((0, 0), line, font=font)[1] for line in lines])
            
            # FEST: 80px für garantiert 1 Label (wie Minimal-Test)
            img_height = 80  # FEST! Keine Variabilität
            
            img = Image.new('RGB', (self.width_pixels, img_height), 'white')
            draw = ImageDraw.Draw(img)
            
            # Text positionieren mit Y-Offset
            label_center_x = offset_x + (self.label_width_pixels // 2)
            
            # Y-KORREKTUR: Y-Offset direkt verwenden - KORRIGIERT (6mm tiefer) 
            y_start = 35 + offset_y  # 35px statt 25px für korrekte Position
            
            # Sicherstellen dass Text ins Bild passt
            if y_start < 0:
                y_start = 0
            if y_start + text_height > img_height:
                y_start = img_height - text_height - 5
            
            y_offset = y_start
            
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                line_width = bbox[2] - bbox[0]
                line_height = bbox[3] - bbox[1]
                x_offset = label_center_x - (line_width // 2)
                
                if y_offset + line_height <= img_height and y_offset >= 0:
                    draw.text((x_offset, y_offset), line, fill='black', font=font)
                
                y_offset += line_height + 3
            
            # Debug-Rahmen - zeigt Label-Grenzen
            if show_frame:
                # Label-Bereich im verfügbaren Raum
                frame_height = min(img_height - 1, 70)  # Nicht größer als Bild
                draw.rectangle([
                    (offset_x, 0), 
                    (offset_x + self.label_width_pixels - 1, frame_height)
                ], outline='black', width=1)
                
                # Ecken markieren
                corner_size = 8
                draw.rectangle([
                    (offset_x, 0), 
                    (offset_x + corner_size, corner_size)
                ], fill='black')
                draw.rectangle([
                    (offset_x + self.label_width_pixels - corner_size, frame_height - corner_size), 
                    (offset_x + self.label_width_pixels - 1, frame_height)
                ], fill='black')
                
                # Y-Offset Marker
                if offset_y != 0:
                    marker_y = max(0, min(35 + offset_y, img_height - 1))  # Basis 35px + Offset
                    draw.line([
                        (offset_x + 5, marker_y), 
                        (offset_x + 30, marker_y)
                    ], fill='black', width=2)
            
            img = img.convert('1')
            
            logger.info(f"Kalibrierungs-Bild: {img.size} (FEST 80px für 1 Label, Y-Offset: {offset_y}px)")
            return img
            
        except Exception as e:
            logger.error(f"Kalibrierungs-Bild-Fehler: {e}")
            return Image.new('1', (self.width_pixels, 80), 'white')

    def print_full_height_test(self, offset_x, offset_y):
        """KORRIGIERTER Volltest - 80px für EIN EINZIGES Label (nicht 2 Segmente)"""
        try:
            self.initialize_printer()
            
            # NEUE STRATEGIE: NUR 80px für 1 Label (wie bei anderen Tests)
            img_height = 80  # FEST! Nicht 200px
            img = Image.new('RGB', (self.width_pixels, img_height), 'white')
            draw = ImageDraw.Draw(img)
            
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
                font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
            except:
                font = ImageFont.load_default()
                font_big = ImageFont.load_default()
            
            # Label-Rahmen (nur 80px hoch)
            draw.rectangle([
                (offset_x, 0), 
                (offset_x + self.label_width_pixels - 1, img_height - 1)
            ], outline='black', width=2)
            
            # Alle 4 Ecken markieren
            corner = 10
            draw.rectangle((offset_x, 0, offset_x + corner, corner), fill='black')  # Links oben
            draw.rectangle((offset_x + self.label_width_pixels - corner, 0, offset_x + self.label_width_pixels, corner), fill='black')  # Rechts oben
            draw.rectangle((offset_x, img_height - corner, offset_x + corner, img_height), fill='black')  # Links unten
            draw.rectangle((offset_x + self.label_width_pixels - corner, img_height - corner, offset_x + self.label_width_pixels, img_height), fill='black')  # Rechts unten
            
            # Text mit Y-Offset positionieren (VOLLTEST hat keine Y-Anpassung - bleibt perfekt)
            center_x = offset_x + (self.label_width_pixels // 2)
            center_y = (img_height // 2)  # Zentriert im 80px Bild
            
            text_lines = [
                "VOLLTEST 80px",
                f"X: {offset_x//8}mm",
                "1 Label komplett"
            ]
            
            y_pos = center_y - 20
            for line in text_lines:
                bbox = draw.textbbox((0, 0), line, font=font_big if line.startswith("VOLLTEST") else font)
                line_width = bbox[2] - bbox[0]
                x_pos = center_x - (line_width // 2)
                
                if y_pos >= 0 and y_pos + bbox[3] - bbox[1] <= img_height:
                    draw.text((x_pos, y_pos), line, fill='black', font=font_big if line.startswith("VOLLTEST") else font)
                
                y_pos += bbox[3] - bbox[1] + 3
            
            # Raster für Orientierung
            for y in range(20, img_height, 15):  # Alle 15px eine Linie
                draw.line([
                    (offset_x + 10, y), 
                    (offset_x + self.label_width_pixels - 10, y)
                ], fill='gray', width=1)
            
            # In Schwarz/Weiß konvertieren
            img = img.convert('1')
            
            # Als EIN Block drucken (nicht segmentiert)
            image_bytes, height = self.image_to_bytes(img)
            self._send_image_block(image_bytes, height)
            
            # Feed für Label-Ende
            self.send_command(b'\x1b\x64\x01')
            
            logger.info(f"Volltest gedruckt: 80px (1 Label) mit X={offset_x//8}mm")
            return True
            
        except Exception as e:
            logger.error(f"Volltest-Fehler: {e}")
            return False

# Konfiguration
PRINTER_MAC = "12:7E:5A:E9:E5:22"  # Deine Drucker-MAC

# Drucker-Instanz mit Label-Spezifikationen
printer = PhomemoM110(PRINTER_MAC, label_width_mm=40, label_height_mm=30)
        
        <div class="font-controls">
            <label for="fontSize">Schriftgröße:</label>
            <select id="fontSize">
                <option value="12">Sehr Klein (12px)</option>
                <option value="16">Klein (16px)</option>
                <option value="20" selected>Normal (20px)</option>
                <option value="24">Groß (24px)</option>
                <option value="28">Extra Groß (28px)</option>
            </select>
            <span style="margin-left: 20px; color: #666;">
                📏 Label: 40×30mm (320×240px)
            </span>
        </div>
        
        <button class="text-btn" onclick="printText()">🖨️ Text drucken</button>
        <button class="text-btn" onclick="testText()">🧪 Test drucken</button>
    </div>
    
    <!-- Bild-Druck Sektion -->
    html_font_controls = """
    <div class="font-controls">
        <label for="fontSize">Schriftgröße:</label>
        <select id="fontSize">
            <option value="12">Sehr Klein (12px)</option>
            <option value="16">Klein (16px)</option>
            <option value="20" selected>Normal (20px)</option>
            <option value="24">Groß (24px)</option>
            <option value="28">Extra Groß (28px)</option>
        </select>
        <span style="margin-left: 20px; color: #666;">
            📏 Label: 40×30mm (320×240px)
        </span>
    </div>
    <button class="text-btn" onclick="printText()">🖨️ Text drucken</button>
    <button class="text-btn" onclick="testText()">🧪 Test drucken</button>
    """
        <div class="section image-section">
            <h2>🖼️ Bild drucken</h2>
            <div class="upload-area">
                <h3>Bild zum Drucken auswählen</h3>
            <input type="file" id="imageFile" accept="image/*">
            <br><br>
            <button onclick="printImage()">🖨️ Bild drucken</button>
        </div>
    </div>
    
    <div id="status"></div>
    
    <h3>📋 Label-Spezifikationen:</h3>
    <ul>
        <li><strong>Label-Größe:</strong> 40mm × 30mm (320×240px)</li>
        <li><strong>Hardware:</strong> M110 mit 384px Breite (48mm bei 203 DPI)</li>
        <li><strong>Position korrigiert:</strong> Alle Tests 6mm tiefer (korrekte Positionierung)</li>
        <li><strong>Volltest:</strong> 80px für garantiert 1 Label</li>
        <li><strong>Y-Offset:</strong> Funktioniert in Kalibrierung (-30px bis +50px)</li>
        <li><strong>Kalibrierung:</strong> Feste 80px für 1 Label</li>
    </ul>
    
    <script>
        // Offset-Steuerung
        document.getElementById('offsetX').addEventListener('input', function() {
            const value = this.value;
            const mm = Math.round(value / 8);
            document.getElementById('offsetXValue').textContent = value + 'px (' + mm + 'mm)';
        });
        
        document.getElementById('offsetY').addEventListener('input', function() {
            const value = this.value;
            const mm = Math.round(value / 8);
            document.getElementById('offsetYValue').textContent = value + 'px (' + mm + 'mm)';
        });
        
        function testMinimal() {
            const formData = new FormData();
            formData.append('text', 'MINIMAL\\nTEST');
            formData.append('font_size', '14');
            formData.append('height', '80');
            
            showStatus('🔬 Drucke Minimal-Test (80px)...', 'info');
            
            fetch('/api/print-minimal', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showStatus('✅ Minimal-Test: ' + data.message, 'success');
                } else {
                    showStatus('❌ Fehler: ' + data.error, 'error');
                }
            })
            .catch(error => {
                showStatus('❌ Fehler: ' + error, 'error');
            });
        }
        
        function testFullHeight() {
            const offsetX = document.getElementById('offsetX').value;
            const offsetY = document.getElementById('offsetY').value;
            
            const formData = new FormData();
            formData.append('offset_x', offsetX);
            formData.append('offset_y', offsetY);
            
            showStatus('📏 Drucke Volltest (80px = 1 Label)...', 'info');
            
            fetch('/api/print-full-height', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showStatus('✅ Volltest gedruckt! Ein 80px Label mit perfekter Positionierung.', 'success');
                } else {
                    showStatus('❌ Fehler: ' + data.error, 'error');
                }
            })
            .catch(error => {
                showStatus('❌ Fehler: ' + error, 'error');
            });
        }
        
        function testCalibration() {
            const offsetX = document.getElementById('offsetX').value;
            const offsetY = document.getElementById('offsetY').value;
            const showFrame = document.getElementById('showFrame').checked;
            const feedLines = document.getElementById('feedLines').value;
            
            const formData = new FormData();
            formData.append('text', 'Kalibrierung\\nX: ' + Math.round(offsetX/8) + 'mm\\nY: ' + Math.round(offsetY/8) + 'mm\\n✓ Test');
            formData.append('font_size', '16');
            formData.append('offset_x', offsetX);
            formData.append('offset_y', offsetY);
            formData.append('show_frame', showFrame);
            formData.append('feed_lines', feedLines);
            
            showStatus('🎯 Drucke Kalibrierungs-Test...', 'info');
            
            fetch('/api/print-calibration', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showStatus('✅ Kalibrierung gedruckt! Prüfe Position und justiere nach.', 'success');
                } else {
                    showStatus('❌ Fehler: ' + data.error, 'error');
                }
            })
            .catch(error => {
                showStatus('❌ Fehler: ' + error, 'error');
            });
        }
        
        function saveCalibration() {
            const offsetX = document.getElementById('offsetX').value;
            const offsetY = document.getElementById('offsetY').value;
            
            const formData = new FormData();
            formData.append('offset_x', offsetX);
            formData.append('offset_y', offsetY);
            
            fetch('/api/save-calibration', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showStatus('💾 Kalibrierung gespeichert! Gilt ab sofort für alle Drucke.', 'success');
                } else {
                    showStatus('❌ Fehler beim Speichern: ' + data.error, 'error');
                }
            })
            .catch(error => {
                showStatus('❌ Fehler: ' + error, 'error');
            });
        }
        
        function printText() {
            const text = document.getElementById('textInput').value;
            const fontSize = document.getElementById('fontSize').value;
            
            if (!text.trim()) {
                showStatus('Bitte gib Text ein!', 'error');
                return;
            }
            
            const formData = new FormData();
            formData.append('text', text);
            formData.append('font_size', fontSize);
            
            showStatus('🖨️ Drucke Text...', 'info');
            
            fetch('/api/print-text', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showStatus('✅ Text erfolgreich gedruckt!', 'success');
                } else {
                    showStatus('❌ Fehler: ' + data.error, 'error');
                }
            })
            .catch(error => {
                showStatus('❌ Verbindungsfehler: ' + error, 'error');
            });
        }
        
        function testText() {
            document.getElementById('textInput').value = 'Test Label\\n40×30mm\\n✓ OK';
            printText();
        }
        
        function printImage() {
            const fileInput = document.getElementById('imageFile');
            
            if (!fileInput.files[0]) {
                showStatus('Bitte wähle ein Bild aus!', 'error');
                return;
            }
            
            const formData = new FormData();
            formData.append('image', fileInput.files[0]);
            
            showStatus('🖨️ Drucke Bild...', 'info');
            
            fetch('/api/print-image', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showStatus('✅ Bild erfolgreich gedruckt!', 'success');
                } else {
                    showStatus('❌ Fehler: ' + data.error, 'error');
                }
            })
            .catch(error => {
                showStatus('❌ Verbindungsfehler: ' + error, 'error');
            });
        }
        
        function showStatus(message, type) {
            const statusDiv = document.getElementById('status');
            statusDiv.innerHTML = '<div class="status ' + type + '">' + message + '</div>';
        }
    </script>
</body>
</html>
""

@app.route('/')
def index():
    """Web Interface anzeigen"""
    return render_template_string(WEB_INTERFACE)

@app.route('/api/print-minimal', methods=['POST'])
def print_minimal():
    """Minimal-Test mit fester Höhe"""
    try:
        text = request.form.get('text', 'TEST')
        height = int(request.form.get('height', 80))
        font_size = int(request.form.get('font_size', 14))
        
        # Minimal-Bild erstellen
        img = Image.new('RGB', (384, height), 'white')
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        # Text zentriert - KORRIGIERT (6mm tiefer)
        lines = text.split('\\n')
        y = 25  # 25px statt 10px für korrekte Position
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            w = bbox[2] - bbox[0]
            x = (384 - w) // 2
            draw.text((x, y), line, fill='black', font=font)
            y += bbox[3] - bbox[1] + 5
        
        # Rahmen
        draw.rectangle([(0, 0), (383, height-1)], outline='black')
        
        img = img.convert('1')
        
        # Drucken
        if printer.is_connected():
            printer.initialize_printer()
            image_bytes, img_height = printer.image_to_bytes(img)
            
            # Senden
            printer._send_image_block(image_bytes, img_height)
            # KEIN Feed für Minimal-Test
            
            return jsonify({
                'success': True, 
                'message': f'{height}px ({height//8}mm) Bild gesendet'
            })
        else:
            return jsonify({'success': False, 'error': 'Nicht verbunden'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/print-full-height', methods=['POST'])
def print_full_height():
    """API Endpoint für Volltest mit 80px"""
    try:
        offset_x = int(request.form.get('offset_x', 72))
        offset_y = int(request.form.get('offset_y', 0))
        
        success = printer.print_full_height_test(offset_x, offset_y)
        
        if success:
            return jsonify({
                'success': True, 
                'message': f'Volltest (80px) gedruckt mit X={offset_x//8}mm'
            })
        else:
            return jsonify({'success': False, 'error': 'Druckfehler'})
            
    except Exception as e:
        logger.error(f"Volltest-Fehler: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/print-calibration', methods=['POST'])
def print_calibration():
    """API Endpoint für Kalibrierungs-Druck"""
    try:
            else:
                # Bild ist höher -> an Label-Höhe anpassen
                new_height = self.label_height_pixels
                new_width = int(self.label_height_pixels * img_ratio)
        feed_lines = int(request.form.get('feed_lines', 1))  # Feed nach Druck
        show_frame = request.form.get('show_frame', 'false').lower() == 'true'
        
        # Kalibrierungs-Druck mit korrekten X/Y-Achsen
        success = printer.print_calibration_text(text, font_size, offset_x, offset_y, show_frame, feed_lines)
        
        if success:
            return jsonify({
                'success': True, 
                'message': f'Kalibrierung gedruckt: X={offset_x}px ({offset_x//8}mm), Y={offset_y}px ({offset_y//8}mm)'
            })
        else:
            return jsonify({'success': False, 'error': 'Druckfehler'})
            
    except Exception as e:
        logger.error(f"Kalibrierungs-Fehler: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/save-calibration', methods=['POST'])
def save_calibration():
    """API Endpoint um Kalibrierung zu speichern"""
    try:
        offset_x = int(request.form.get('offset_x', 72))  # Links/Rechts
        offset_y = int(request.form.get('offset_y', 0))    # Oben/Unten
        
        # Global speichern
        printer.label_offset_x = offset_x
        printer.calibration_offset_y = offset_y
        
        logger.info(f"Kalibrierung gespeichert: X={offset_x}px ({offset_x//8}mm), Y={offset_y}px ({offset_y//8}mm)")
        
        return jsonify({
            'success': True, 
            'message': f'Kalibrierung gespeichert: X={offset_x//8}mm, Y={offset_y//8}mm'
        })
        
    except Exception as e:
        logger.error(f"Speicher-Fehler: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/print-text', methods=['POST'])
def print_text():
    """API Endpoint für Text-Druck"""
    try:
        text = request.form.get('text', '')
        font_size = int(request.form.get('font_size', 24))
        
        if not text.strip():
            return jsonify({'success': False, 'error': 'Kein Text angegeben'})
        
        # Text drucken
        success = printer.print_text(text, font_size)
        
        if success:
            return jsonify({'success': True, 'message': 'Text erfolgreich gedruckt'})
        else:
            return jsonify({'success': False, 'error': 'Druckfehler - Verbindung prüfen'})
            
    except Exception as e:
        logger.error(f"API Fehler: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/print-image', methods=['POST'])
def print_image():
    """API Endpoint für Bilddruck"""
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'Kein Bild übertragen'})
        
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({'success': False, 'error': 'Keine Datei ausgewählt'})
        
        # Bild in Memory laden
        image_data = io.BytesIO(image_file.read())
        
        # Drucken
        success = printer.print_image(image_data)
        
        if success:
            return jsonify({'success': True, 'message': 'Bild erfolgreich gedruckt'})
        else:
            return jsonify({'success': False, 'error': 'Druckfehler - Verbindung prüfen'})
            
    except Exception as e:
        logger.error(f"API Fehler: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/status')
def printer_status():
    """Drucker-Status abfragen"""
    try:
        connected = printer.is_connected()
        
        return jsonify({
            'connected': connected,
            'mac': PRINTER_MAC,
            'device': printer.rfcomm_device
        })
    except Exception as e:
        return jsonify({
            'connected': False,
            'error': str(e)
        })

if __name__ == '__main__':
    print("🚀 Phomemo M110 Text & Bild Webserver startet...")
    print(f"📱 Web Interface: http://192.168.130.138:8080")
    print(f"🔵 Drucker MAC: {PRINTER_MAC}")
    print(f"📡 Gerät: {printer.rfcomm_device}")
    print("💡 Stelle sicher, dass rfcomm connect läuft!")
    print("🎯 Features: Y-Offset Kalibrierung korrigiert, Position 6mm tiefer")
    
    app.run(host='0.0.0.0', port=8080, debug=True)
