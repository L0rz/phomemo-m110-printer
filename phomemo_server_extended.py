#!/usr/bin/env python3
"""
Phomemo M110 Text-zu-Bild Drucker - ERWEITERT mit Reconnect-Funktionalität
Konvertiert Text in Bilder und druckt sie
Korrigiert für 40x30mm Labels mit Y-Offset Funktionalität
NEUE FEATURES: Automatisches Reconnect, Verbindungsmanagement, Retry-Logik
"""

from flask import Flask, request, jsonify, render_template_string
from PIL import Image, ImageDraw, ImageFont
import io
import time
import os
import logging
import subprocess
import socket
import threading
from datetime import datetime

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

class PhomemoM110:
    """Phomemo M110 Drucker mit erweiterten Reconnect-Features"""
    
    def __init__(self, mac_address, label_width_mm=40, label_height_mm=30):
        self.mac_address = mac_address
        self.rfcomm_device = "/dev/rfcomm0"
        self.rfcomm_channel = 0
        
        # Label-Spezifikationen (DPI = 203)
        self.dpi = 203
        self.width_pixels = 384  # Hardware-Breite (48mm)
        self.label_width_mm = label_width_mm
        self.label_height_mm = label_height_mm
        self.label_width_pixels = int((label_width_mm / 25.4) * self.dpi)  # 320px
        self.label_height_pixels = int((label_height_mm / 25.4) * self.dpi)  # 240px
        
        # Kalibrierungs-Offsets
        self.label_offset_x = 72  # 9mm von links
        self.calibration_offset_y = 0  # Y-Verschiebung
        
        # NEUE RECONNECT-EIGENSCHAFTEN
        self.connection_socket = None
        self.last_connection_check = 0
        self.connection_check_interval = 5  # Sekunden
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 3
        self.reconnect_delay = 2  # Sekunden zwischen Versuchen
        self.auto_reconnect_enabled = True
        self.connection_lock = threading.Lock()
        
        logger.info(f"Phomemo M110 initialisiert: {label_width_mm}×{label_height_mm}mm Labels")
        logger.info(f"NEUE FEATURES: Automatisches Reconnect aktiviert")
    
    def is_connected(self):
        """Prüft rfcomm-Verbindung - ERWEITERT mit Socket-Test"""
        try:
            # Schnelle Dateisystem-Prüfung
            if not os.path.exists(self.rfcomm_device):
                return False
            
            # Erweiterte Socket-Prüfung (nur alle 5 Sekunden)
            current_time = time.time()
            if current_time - self.last_connection_check > self.connection_check_interval:
                self.last_connection_check = current_time
                return self._test_socket_connection()
            
            return True
            
        except Exception as e:
            logger.warning(f"Verbindungsprüfung fehlgeschlagen: {e}")
            return False
    
    def _test_socket_connection(self):
        """Testet die tatsächliche Socket-Verbindung"""
        try:
            # Versuche kurze Testverbindung
            with socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM) as test_sock:
                test_sock.settimeout(2)  # 2 Sekunden Timeout
                test_sock.connect((self.mac_address, 1))
                return True
        except Exception as e:
            logger.debug(f"Socket-Test fehlgeschlagen: {e}")
            return False
    
    def connect_bluetooth(self):
        """NEUE METHODE: Stellt Bluetooth-Verbindung her mit Retry-Logik"""
        with self.connection_lock:
            logger.info(f"🔵 Verbinde mit Phomemo M110: {self.mac_address}")
            
            for attempt in range(1, self.max_reconnect_attempts + 1):
                try:
                    logger.info(f"Verbindungsversuch {attempt}/{self.max_reconnect_attempts}")
                    
                    # 1. rfcomm freigeben falls bereits belegt
                    self._release_rfcomm()
                    
                    # 2. Kurz warten
                    time.sleep(1)
                    
                    # 3. rfcomm-Verbindung erstellen
                    success = self._create_rfcomm_connection()
                    
                    if success:
                        logger.info("✅ Bluetooth-Verbindung erfolgreich hergestellt!")
                        self.reconnect_attempts = 0
                        return True
                    
                except Exception as e:
                    logger.error(f"Verbindungsversuch {attempt} fehlgeschlagen: {e}")
                
                # Warten vor nächstem Versuch
                if attempt < self.max_reconnect_attempts:
                    logger.info(f"⏳ Warte {self.reconnect_delay}s vor nächstem Versuch...")
                    time.sleep(self.reconnect_delay)
            
            logger.error("❌ Alle Verbindungsversuche fehlgeschlagen!")
            return False
    
    def _release_rfcomm(self):
        """Gibt rfcomm-Verbindung frei"""
        try:
            result = subprocess.run(
                ['sudo', 'rfcomm', 'release', str(self.rfcomm_channel)], 
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                logger.debug(f"rfcomm{self.rfcomm_channel} freigegeben")
            else:
                logger.debug(f"rfcomm release: {result.stderr}")
        except Exception as e:
            logger.debug(f"rfcomm release Fehler: {e}")
    
    def _create_rfcomm_connection(self):
        """Erstellt neue rfcomm-Verbindung"""
        try:
            result = subprocess.run([
                'sudo', 'rfcomm', 'bind', str(self.rfcomm_channel), self.mac_address
            ], capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                # Kurz warten bis Device verfügbar
                time.sleep(2)
                
                # Prüfen ob Device existiert
                if os.path.exists(self.rfcomm_device):
                    return True
                else:
                    logger.error(f"Device {self.rfcomm_device} nicht verfügbar")
                    return False
            else:
                logger.error(f"rfcomm bind Fehler: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("rfcomm bind Timeout")
            return False
        except Exception as e:
            logger.error(f"rfcomm bind Fehler: {e}")
            return False
    
    def auto_reconnect(self):
        """NEUE METHODE: Automatisches Reconnect wenn Verbindung verloren"""
        if not self.auto_reconnect_enabled:
            return False
        
        if not self.is_connected():
            logger.warning("🔄 Verbindung verloren - versuche Reconnect...")
            return self.connect_bluetooth()
        
        return True
    
    def send_command(self, command_bytes):
        """Sendet Befehl an Drucker - ERWEITERT mit Auto-Reconnect"""
        max_retries = 2
        
        for retry in range(max_retries + 1):
            try:
                # Auto-Reconnect prüfen
                if not self.auto_reconnect():
                    logger.error("Reconnect fehlgeschlagen")
                    return False
                
                # Befehl senden
                with open(self.rfcomm_device, 'wb') as printer:
                    printer.write(command_bytes)
                    printer.flush()
                
                return True
                
            except (FileNotFoundError, PermissionError, IOError) as e:
                logger.warning(f"Sendefehler (Versuch {retry + 1}): {e}")
                
                if retry < max_retries:
                    logger.info("🔄 Versuche Reconnect...")
                    if not self.connect_bluetooth():
                        continue
                else:
                    logger.error("❌ Alle Sendeversuche fehlgeschlagen")
                    return False
            
            except Exception as e:
                logger.error(f"Unerwarteter Sendefehler: {e}")
                return False
        
        return False
    
    def get_connection_status(self):
        """NEUE METHODE: Detaillierte Verbindungsinfo"""
        status = {
            'connected': self.is_connected(),
            'mac_address': self.mac_address,
            'rfcomm_device': self.rfcomm_device,
            'auto_reconnect': self.auto_reconnect_enabled,
            'reconnect_attempts': self.reconnect_attempts,
            'last_check': datetime.fromtimestamp(self.last_connection_check).strftime('%H:%M:%S'),
            'device_exists': os.path.exists(self.rfcomm_device)
        }
        
        # Bluetooth-Service Status
        try:
            result = subprocess.run(['systemctl', 'is-active', 'bluetooth'], 
                                  capture_output=True, text=True, timeout=5)
            status['bluetooth_service'] = result.stdout.strip()
        except:
            status['bluetooth_service'] = 'unknown'
        
        return status
    
    def force_reconnect(self):
        """NEUE METHODE: Erzwingt Neuverbindung"""
        logger.info("🔄 Erzwinge Neuverbindung...")
        self.reconnect_attempts = 0
        return self.connect_bluetooth()
    
    def initialize_printer(self):
        """Drucker initialisieren"""
        try:
            # ESC @: Drucker zurücksetzen
            self.send_command(b'\x1b\x40')
            time.sleep(0.5)
            
            # Druckerdichte und -geschwindigkeit
            self.send_command(b'\x1b\x37\x07\x64\x64')
            time.sleep(0.1)
            
            return True
            
        except Exception as e:
            logger.error(f"Drucker-Initialisierung fehlgeschlagen: {e}")
            return False
    
    def print_text(self, text, font_size=24):
        """Text drucken mit Auto-Reconnect"""
        logger.info(f"Drucke Text: '{text}' (Größe: {font_size}px)")
        
        if not self.auto_reconnect():
            return False
        
        try:
            self.initialize_printer()
            
            # Text-Bild erstellen
            img = self.create_text_image(text, font_size)
            image_bytes, height = self.image_to_bytes(img)
            
            # Drucken
            return self._send_image_block(image_bytes, height)
            
        except Exception as e:
            logger.error(f"Text-Druckfehler: {e}")
            return False
    
    def create_text_image(self, text, font_size=24):
        """Text-Bild für Labels erstellen"""
        try:
            # Font laden
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            # Text-Dimensionen berechnen
            lines = text.replace('\\n', '\n').split('\n')
            
            # Temporäres Bild für Größenberechnung
            temp_img = Image.new('RGB', (1, 1), 'white')
            temp_draw = ImageDraw.Draw(temp_img)
            
            max_width = 0
            total_height = 0
            line_heights = []
            
            for line in lines:
                bbox = temp_draw.textbbox((0, 0), line, font=font)
                line_width = bbox[2] - bbox[0]
                line_height = bbox[3] - bbox[1]
                
                max_width = max(max_width, line_width)
                total_height += line_height + 5  # 5px Zeilenabstand
                line_heights.append(line_height)
            
            # Automatische Schriftgrößen-Anpassung
            if max_width > self.label_width_pixels:
                scale_factor = self.label_width_pixels / max_width
                font_size = int(font_size * scale_factor * 0.9)  # 10% Puffer
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
                logger.info(f"Schrift angepasst auf {font_size}px")
            
            # Bild-Höhe basierend auf Inhalt
            img_height = min(max(total_height + 20, 60), 120)  # 60-120px Höhe
            
            # Finales Bild erstellen
            img = Image.new('RGB', (self.width_pixels, img_height), 'white')
            draw = ImageDraw.Draw(img)
            
            # Text zentriert positionieren - KORRIGIERT (6mm tiefer)
            label_center_x = self.label_offset_x + (self.label_width_pixels // 2)
            y_start = 35 + self.calibration_offset_y  # 35px Basis + Y-Offset
            
            y_offset = y_start
            for i, line in enumerate(lines):
                bbox = draw.textbbox((0, 0), line, font=font)
                line_width = bbox[2] - bbox[0]
                x_offset = label_center_x - (line_width // 2)
                
                if y_offset + line_heights[i] <= img_height and y_offset >= 0:
                    draw.text((x_offset, y_offset), line, fill='black', font=font)
                
                y_offset += line_heights[i] + 5
            
            # Label-Rahmen (Debug)
            # draw.rectangle([
            #     (self.label_offset_x, 0), 
            #     (self.label_offset_x + self.label_width_pixels - 1, img_height - 1)
            # ], outline='gray', width=1)
            
            img = img.convert('1')
            logger.info(f"Text-Bild erstellt: {img.size}")
            return img
            
        except Exception as e:
            logger.error(f"Text-Bild-Fehler: {e}")
            return Image.new('1', (self.width_pixels, 80), 'white')
    
    def print_image(self, image_data):
        """Bild drucken mit Auto-Reconnect"""
        logger.info("Drucke Bild...")
        
        if not self.auto_reconnect():
            return False
        
        try:
            self.initialize_printer()
            
            # Bild laden und anpassen
            img = Image.open(image_data)
            img = self.resize_image_to_label(img)
            
            image_bytes, height = self.image_to_bytes(img)
            
            # Drucken
            return self._send_image_block(image_bytes, height)
            
        except Exception as e:
            logger.error(f"Bild-Druckfehler: {e}")
            return False
    
    def resize_image_to_label(self, img):
        """Bild auf Label-Größe anpassen"""
        try:
            # Zu RGB konvertieren
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Seitenverhältnis berechnen
            img_ratio = img.width / img.height
            label_ratio = self.label_width_pixels / self.label_height_pixels
            
            if img_ratio > label_ratio:
                # Bild ist breiter -> an Label-Breite anpassen
                new_width = self.label_width_pixels
                new_height = int(self.label_width_pixels / img_ratio)
            else:
                # Bild ist höher -> an Label-Höhe anpassen
                new_height = self.label_height_pixels
                new_width = int(self.label_height_pixels * img_ratio)
            
            # Größe ändern mit guter Qualität
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Auf Label-Canvas zentrieren
            canvas = Image.new('RGB', (self.width_pixels, self.label_height_pixels), 'white')
            
            # Position berechnen (mit Offset)
            x_pos = self.label_offset_x + (self.label_width_pixels - new_width) // 2
            y_pos = (self.label_height_pixels - new_height) // 2
            
            canvas.paste(img, (x_pos, y_pos))
            
            # Zu Schwarz/Weiß konvertieren
            canvas = canvas.convert('1')
            
            logger.info(f"Bild angepasst: {img.size} -> {canvas.size}")
            return canvas
            
        except Exception as e:
            logger.error(f"Bildanpassung fehlgeschlagen: {e}")
            return Image.new('1', (self.width_pixels, self.label_height_pixels), 'white')
    
    def image_to_bytes(self, img):
        """Konvertiert PIL-Bild zu Drucker-Bytes"""
        width, height = img.size
        
        # Bilddaten extrahieren
        pixels = list(img.getdata())
        
        # In Drucker-Format konvertieren (8 Pixel = 1 Byte)
        image_bytes = bytearray()
        
        for y in range(height):
            for x in range(0, width, 8):
                byte_value = 0
                for bit in range(8):
                    if x + bit < width:
                        pixel_idx = y * width + x + bit
                        if pixel_idx < len(pixels):
                            # Schwarzer Pixel = 1, Weißer Pixel = 0
                            if pixels[pixel_idx] == 0:  # Schwarz
                                byte_value |= (1 << (7 - bit))
                
                image_bytes.append(byte_value)
        
        return bytes(image_bytes), height
    
    def _send_image_block(self, image_bytes, height):
        """Sendet Bilddaten als Block"""
        try:
            # ESC * m nL nH [Daten]
            # m = Modus (0 = normal), nL/nH = Bytes pro Zeile
            bytes_per_line = self.width_pixels // 8  # 48 Bytes pro Zeile
            
            # Header für Bilddruck
            header = bytes([
                0x1b, 0x2a, 0x00,  # ESC * 0
                bytes_per_line & 0xFF,  # nL (Low Byte)
                (bytes_per_line >> 8) & 0xFF  # nH (High Byte)
            ])
            
            # Daten in Blöcken senden
            block_size = bytes_per_line * min(height, 100)  # Max 100 Zeilen pro Block
            
            for start_line in range(0, height, 100):
                end_line = min(start_line + 100, height)
                lines_in_block = end_line - start_line
                
                # Block-Header
                block_header = bytes([
                    0x1b, 0x2a, 0x00,
                    bytes_per_line & 0xFF,
                    (bytes_per_line >> 8) & 0xFF
                ])
                
                # Block-Daten
                start_byte = start_line * bytes_per_line
                end_byte = end_line * bytes_per_line
                block_data = image_bytes[start_byte:end_byte]
                
                # Senden
                if not self.send_command(block_header + block_data):
                    return False
                
                # Kurze Pause zwischen Blöcken
                time.sleep(0.1)
            
            # Feed nach Bild
            self.send_command(b'\x1b\x64\x02')  # 2 Zeilen Feed
            
            logger.info(f"Bild gesendet: {height} Zeilen in Blöcken")
            return True
            
        except Exception as e:
            logger.error(f"Bildsende-Fehler: {e}")
            return False

# Konfiguration
PRINTER_MAC = "12:7E:5A:E9:E5:22"  # Ihre Drucker-MAC

# Drucker-Instanz mit erweiterten Features
printer = PhomemoM110(PRINTER_MAC, label_width_mm=40, label_height_mm=30)
        .status {
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
            font-weight: bold;
        }
        
        .status.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .status.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .status.info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        
        .status.warning {
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
        }
        
        /* NEUE: Connection indicator */
        .connection-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }
        
        .connected { background: #27ae60; }
        .disconnected { background: #e74c3c; }
        .connecting { background: #f39c12; }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }
        
        .auto-refresh {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 15px;
            padding: 10px;
            background: rgba(52, 152, 219, 0.1);
            border-radius: 8px;
        }
        
        @media (max-width: 768px) {
            .container {
                grid-template-columns: 1fr;
                padding: 10px;
            }
            
            .status-grid {
                grid-template-columns: 1fr;
            }
            
            .connection-actions {
                justify-content: center;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="card header">
            <h1>🖨️ Phomemo M110 Drucker</h1>
            <p class="subtitle">Web-Interface mit automatischem Reconnect</p>
            <div style="display: flex; justify-content: center; gap: 10px; flex-wrap: wrap;">
                <span class="btn btn-info" style="cursor: default;">📏 40×30mm Labels</span>
                <span class="btn btn-info" style="cursor: default;">🔵 Bluetooth</span>
                <span class="btn btn-info" style="cursor: default;">🔄 Auto-Reconnect</span>
            </div>
        </div>

        <!-- CONNECTION STATUS PANEL - NEUE HAUPTFUNKTION -->
        <div class="card connection-panel">
            <h2 style="color: white; margin-bottom: 20px;">
                🔗 Verbindungsstatus
                <span id="connectionIndicator" class="connection-indicator disconnected"></span>
                <span id="connectionText">Prüfe...</span>
            </h2>
            
            <div class="status-grid">
                <div class="status-item">
                    <div class="status-label">Drucker-MAC</div>
                    <div class="status-value" id="printerMac">12:7E:5A:E9:E5:22</div>
                </div>
                <div class="status-item">
                    <div class="status-label">rfcomm Device</div>
                    <div class="status-value" id="rfcommDevice">/dev/rfcomm0</div>
                </div>
                <div class="status-item">
                    <div class="status-label">Letzte Prüfung</div>
                    <div class="status-value" id="lastCheck">--:--:--</div>
                </div>
                <div class="status-item">
                    <div class="status-label">Auto-Reconnect</div>
                    <div class="status-value" id="autoReconnect">Aktiv</div>
                </div>
            </div>
            
            <div class="connection-actions">
                <button class="btn btn-success" onclick="checkConnection()">🔍 Status prüfen</button>
                <button class="btn btn-warning" onclick="reconnectPrinter()">🔄 Reconnect</button>
                <button class="btn btn-danger" onclick="forceReconnect()">⚡ Force Reconnect</button>
                <button class="btn btn-info" onclick="toggleAutoReconnect()">🤖 Auto-Reconnect</button>
            </div>
            
            <div class="auto-refresh">
                <input type="checkbox" id="autoRefresh" checked>
                <label for="autoRefresh">🔄 Auto-Status-Update (alle 10s)</label>
            </div>
        </div>

        <!-- Text-Druck Sektion -->
        <div class="card section">
            <h2>📝 Text drucken</h2>
            <textarea id="textInput" rows="4" placeholder="Text eingeben...
Beispiel:
Hallo Welt
40×30mm
✓ Test OK"></textarea>
            
            <div class="slider-container">
                <label for="fontSize">Schriftgröße: <span id="fontSizeValue">20px</span></label>
                <input type="range" id="fontSize" class="slider" min="12" max="32" value="20">
            </div>
            
            <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                <button class="btn btn-primary" onclick="printText()">🖨️ Text drucken</button>
                <button class="btn btn-info" onclick="testText()">🧪 Test drucken</button>
            </div>
        </div>

        <!-- Bild-Druck Sektion -->
        <div class="card section">
            <h2>🖼️ Bild drucken</h2>
            <input type="file" id="imageFile" accept="image/*">
            <button class="btn btn-primary" onclick="printImage()">🖨️ Bild drucken</button>
            
            <div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                <strong>💡 Tipps:</strong>
                <ul style="margin-left: 20px; margin-top: 10px;">
                    <li>Optimale Größe: 320×240px</li>
                    <li>Unterstützt: JPG, PNG, GIF</li>
                    <li>Wird automatisch angepasst</li>
                </ul>
            </div>
        </div>

        <!-- Kalibrierung -->
        <div class="card section">
            <h2>🎯 Kalibrierung</h2>
            <div class="slider-container">
                <label for="offsetX">X-Offset (Links/Rechts): <span id="offsetXValue">72px (9mm)</span></label>
                <input type="range" id="offsetX" class="slider" min="0" max="144" value="72">
            </div>
            
            <div class="slider-container">
                <label for="offsetY">Y-Offset (Oben/Unten): <span id="offsetYValue">0px (0mm)</span></label>
                <input type="range" id="offsetY" class="slider" min="-30" max="50" value="0">
            </div>
            
            <div style="margin: 15px 0;">
                <label>
                    <input type="checkbox" id="showFrame" checked> 
                    Debug-Rahmen anzeigen
                </label>
            </div>
            
            <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                <button class="btn btn-warning" onclick="testCalibration()">🎯 Kalibrierung testen</button>
                <button class="btn btn-success" onclick="saveCalibration()">💾 Speichern</button>
            </div>
        </div>

        <!-- Erweiterte Tests -->
        <div class="card section">
            <h2>🔬 Erweiterte Tests</h2>
            <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                <button class="btn btn-info" onclick="testMinimal()">📏 Minimal-Test</button>
                <button class="btn btn-primary" onclick="testFullHeight()">📐 Volltest</button>
                <button class="btn btn-warning" onclick="testReconnect()">🔄 Reconnect-Test</button>
            </div>
            
            <div style="margin-top: 15px; padding: 15px; background: #e8f4f8; border-radius: 8px;">
                <strong>🧪 Test-Beschreibungen:</strong>
                <ul style="margin-left: 20px; margin-top: 10px;">
                    <li><strong>Minimal:</strong> 80px Test für Grundfunktion</li>
                    <li><strong>Volltest:</strong> Komplette 30mm Label-Höhe</li>
                    <li><strong>Reconnect:</strong> Verbindung trennen & wiederherstellen</li>
                </ul>
            </div>
        </div>
    </div>

    <!-- Status Display -->
    <div id="status" style="position: fixed; bottom: 20px; right: 20px; max-width: 400px; z-index: 1000;"></div>

    <script>
        // NEUE JAVASCRIPT-FUNKTIONEN FÜR RECONNECT
        let autoRefreshInterval;
        let connectionStatus = { connected: false };
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            updateSliderValues();
            checkConnection();
            startAutoRefresh();
        });
        
        // Slider value updates
        function updateSliderValues() {
            document.getElementById('fontSize').addEventListener('input', function() {
                document.getElementById('fontSizeValue').textContent = this.value + 'px';
            });
            
            document.getElementById('offsetX').addEventListener('input', function() {
                const mm = Math.round(this.value / 8);
                document.getElementById('offsetXValue').textContent = this.value + 'px (' + mm + 'mm)';
            });
            
            document.getElementById('offsetY').addEventListener('input', function() {
                const mm = Math.round(this.value / 8);
                document.getElementById('offsetYValue').textContent = this.value + 'px (' + mm + 'mm)';
            });
            
            document.getElementById('autoRefresh').addEventListener('change', function() {
                if (this.checked) {
                    startAutoRefresh();
                } else {
                    stopAutoRefresh();
                }
            });
        }
        
        // NEUE: Connection management
        function checkConnection() {
            showStatus('🔍 Prüfe Verbindung...', 'info');
            
            fetch('/api/connection-status')
                .then(response => response.json())
                .then(data => {
                    updateConnectionDisplay(data);
                    connectionStatus = data;
                })
                .catch(error => {
                    showStatus('❌ Verbindungsprüfung fehlgeschlagen: ' + error, 'error');
                    updateConnectionDisplay({ connected: false, error: error.message });
                });
        }
        
        function updateConnectionDisplay(status) {
            const indicator = document.getElementById('connectionIndicator');
            const text = document.getElementById('connectionText');
            
            if (status.connected) {
                indicator.className = 'connection-indicator connected';
                text.textContent = 'Verbunden ✓';
                showStatus('✅ Drucker verbunden und bereit!', 'success');
            } else {
                indicator.className = 'connection-indicator disconnected';
                text.textContent = 'Getrennt ✗';
                showStatus('❌ Drucker nicht verbunden', 'error');
            }
            
            // Update detailed status
            if (status.mac_address) document.getElementById('printerMac').textContent = status.mac_address;
            if (status.rfcomm_device) document.getElementById('rfcommDevice').textContent = status.rfcomm_device;
            if (status.last_check) document.getElementById('lastCheck').textContent = status.last_check;
            if (status.auto_reconnect !== undefined) {
                document.getElementById('autoReconnect').textContent = status.auto_reconnect ? 'Aktiv' : 'Inaktiv';
            }
        }
        
        function reconnectPrinter() {
            const indicator = document.getElementById('connectionIndicator');
            const text = document.getElementById('connectionText');
            
            indicator.className = 'connection-indicator connecting';
            text.textContent = 'Verbinde...';
            showStatus('🔄 Stelle Verbindung wieder her...', 'info');
            
            fetch('/api/reconnect', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showStatus('✅ Reconnect erfolgreich!', 'success');
                        checkConnection();
                    } else {
                        showStatus('❌ Reconnect fehlgeschlagen: ' + data.error, 'error');
                        updateConnectionDisplay({ connected: false });
                    }
                })
                .catch(error => {
                    showStatus('❌ Reconnect-Fehler: ' + error, 'error');
                    updateConnectionDisplay({ connected: false });
                });
        }
        
        function forceReconnect() {
            showStatus('⚡ Erzwinge Neuverbindung...', 'warning');
            
            fetch('/api/force-reconnect', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showStatus('✅ Force Reconnect erfolgreich!', 'success');
                        checkConnection();
                    } else {
                        showStatus('❌ Force Reconnect fehlgeschlagen: ' + data.error, 'error');
                    }
                })
                .catch(error => {
                    showStatus('❌ Force Reconnect-Fehler: ' + error, 'error');
                });
        }
        
        function toggleAutoReconnect() {
            fetch('/api/toggle-auto-reconnect', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const status = data.auto_reconnect ? 'aktiviert' : 'deaktiviert';
                        showStatus('🤖 Auto-Reconnect ' + status, 'info');
                        checkConnection();
                    } else {
                        showStatus('❌ Auto-Reconnect Toggle fehlgeschlagen', 'error');
                    }
                })
                .catch(error => {
                    showStatus('❌ Toggle-Fehler: ' + error, 'error');
                });
        }
        
        function startAutoRefresh() {
            stopAutoRefresh();
            autoRefreshInterval = setInterval(checkConnection, 10000); // 10 Sekunden
        }
        
        function stopAutoRefresh() {
            if (autoRefreshInterval) {
                clearInterval(autoRefreshInterval);
                autoRefreshInterval = null;
            }
        }
        
        // NEUE: Test Reconnect function
        function testReconnect() {
            showStatus('🔄 Teste Reconnect-Funktionalität...', 'info');
            
            // 1. Verbindung trennen
            fetch('/api/disconnect', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    showStatus('🔌 Verbindung getrennt - Reconnect in 3s...', 'warning');
                    updateConnectionDisplay({ connected: false });
                    
                    // 2. Nach 3s reconnect
                    setTimeout(() => {
                        reconnectPrinter();
                    }, 3000);
                })
                .catch(error => {
                    showStatus('❌ Disconnect-Test fehlgeschlagen: ' + error, 'error');
                });
        }
            return jsonify({
                'success': True, 
                'message': f'Kalibrierung gedruckt: X={offset_x}px ({offset_x//8}mm), Y={offset_y}px ({offset_y//8}mm)'
            })
        else:
            return jsonify({'success': False, 'error': 'Kalibrierungs-Druckfehler'})
            
    except Exception as e:
        logger.error(f"Kalibrierungs-Fehler: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/save-calibration', methods=['POST'])
def save_calibration():
    """Kalibrierung speichern"""
    try:
        offset_x = int(request.form.get('offset_x', 72))
        offset_y = int(request.form.get('offset_y', 0))
        
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

@app.route('/api/print-minimal', methods=['POST'])
def print_minimal():
    """Minimal-Test drucken"""
    try:
        text = request.form.get('text', 'MINIMAL\\nTEST')
        height = int(request.form.get('height', 80))
        font_size = int(request.form.get('font_size', 14))
        
        # Vereinfachter Minimal-Test
        success = printer.print_text(text.replace('\\n', '\n'), font_size)
        
        if success:
            return jsonify({
                'success': True, 
                'message': f'{height}px Minimal-Test gedruckt'
            })
        else:
            return jsonify({'success': False, 'error': 'Minimal-Test fehlgeschlagen'})
            
    except Exception as e:
        logger.error(f"Minimal-Test-Fehler: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/print-full-height', methods=['POST'])
def print_full_height():
    """Volltest drucken"""
    try:
        offset_x = int(request.form.get('offset_x', 72))
        offset_y = int(request.form.get('offset_y', 0))
        
        # Volltest-Text
        test_text = f"VOLLTEST\\nX: {offset_x//8}mm\\nY: {offset_y//8}mm\\n🔄 Auto-Reconnect"
        
        success = printer.print_text(test_text.replace('\\n', '\n'), 16)
        
        if success:
            return jsonify({
                'success': True, 
                'message': f'Volltest gedruckt mit X={offset_x//8}mm, Y={offset_y//8}mm'
            })
        else:
            return jsonify({'success': False, 'error': 'Volltest fehlgeschlagen'})
            
    except Exception as e:
        logger.error(f"Volltest-Fehler: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/status')
def printer_status():
    """Drucker-Status (Legacy-Kompatibilität)"""
    try:
        status = printer.get_connection_status()
        return jsonify({
            'connected': status.get('connected', False),
            'mac': status.get('mac_address', PRINTER_MAC),
            'device': status.get('rfcomm_device', '/dev/rfcomm0'),
            'auto_reconnect': status.get('auto_reconnect', True),
            'details': status
        })
    except Exception as e:
        return jsonify({
            'connected': False,
            'error': str(e)
        })

if __name__ == '__main__':
    print("🚀 Phomemo M110 ERWEITERTE Version mit Reconnect startet...")
    print(f"📱 Web Interface: http://localhost:8080")
    print(f"🔵 Drucker MAC: {PRINTER_MAC}")
    print(f"📡 Gerät: {printer.rfcomm_device}")
    print("🔄 NEUE FEATURES:")
    print("   ✅ Automatisches Reconnect")
    print("   ✅ Verbindungsmanagement")
    print("   ✅ Force Reconnect")
    print("   ✅ Live Connection Status")
    print("   ✅ Auto-Status-Updates")
    print("   ✅ Retry-Logik für alle Druckvorgänge")
    print("💡 Stelle sicher, dass Bluetooth aktiviert ist!")
    
    # Initiale Verbindung versuchen
    logger.info("🔄 Versuche initiale Bluetooth-Verbindung...")
    if printer.connect_bluetooth():
        logger.info("✅ Initiale Verbindung erfolgreich!")
    else:
        logger.warning("⚠️ Initiale Verbindung fehlgeschlagen - Auto-Reconnect aktiviert")
    
    app.run(host='0.0.0.0', port=8080, debug=True)
