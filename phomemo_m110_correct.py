#!/usr/bin/env python3
"""
PHOMEMO M110 - KORREKTE BEFEHLE
Basierend auf vivier/phomemo-tools GitHub Repository
"""

import time
import os
from PIL import Image, ImageDraw, ImageFont

class PhomemoM110Correct:
    def __init__(self, device="/dev/rfcomm0"):
        self.device = device
        self.width_pixels = 384
        self.width_bytes = 48  # 384 / 8
        
    def send_command(self, data):
        """Sendet Befehle an Drucker"""
        try:
            with open(self.device, 'wb') as printer:
                printer.write(data)
                printer.flush()
            return True
        except Exception as e:
            print(f"❌ Fehler: {e}")
            return False
    
    def initialize_printer(self):
        """KORREKTE M110 Initialisierung"""
        print("🔧 Initialisiere M110 mit korrekten Befehlen...")
        
        # 1. Reset
        self.send_command(b'\x1b\x40')
        time.sleep(0.1)
        
        # 2. PHOMEMO-SPEZIFISCH!
        self.send_command(b'\x1f\x11\x02\x04')
        time.sleep(0.1)
        
        print("✅ M110 initialisiert")
    
    def print_test_pattern(self):
        """Druckt Test-Pattern mit korrekter M110 Sequenz"""
        print("🎨 Drucke Test-Pattern...")
        
        self.initialize_printer()
        
        # Einfaches Test-Pattern: 3 Zeilen
        lines = 24
        
        # GS v 0 Befehl - KORREKTE M110 SYNTAX
        cmd = bytearray([
            0x1d, 0x76, 0x30,          # GS v 0
            0x00,                      # Mode: normal
            0x30, 0x00,                # Width: 48 bytes (Little-Endian!)
            lines & 0xFF, (lines >> 8) & 0xFF  # Height: 24 lines (Little-Endian!)
        ])
        
        # Test-Pattern Daten
        pattern_data = bytearray()
        for line in range(lines):
            if line < 8:
                # Erste 8 Zeilen: solid black
                pattern_data.extend([0xFF] * 48)
            elif line < 16:
                # Mittlere 8 Zeilen: Streifen
                pattern_data.extend([0xAA] * 48)
            else:
                # Letzte 8 Zeilen: Punkte
                pattern_data.extend([0x88] * 48)
        
        # Komplett senden
        full_cmd = cmd + pattern_data
        print(f"📤 Sende {len(full_cmd)} bytes...")
        self.send_command(full_cmd)
        
        # Paper Feed
        time.sleep(0.5)
        self.send_command(b'\x1b\x64\x02')  # Feed 2 lines
        
        print("✅ Test-Pattern gesendet!")
    
    def print_text_as_image(self, text):
        """Druckt Text als Bild mit KORREKTER M110 Methode"""
        print(f"📝 Drucke Text: '{text}'")
        
        self.initialize_printer()
        
        # Text-Bild erstellen
        img = self.create_text_image(text)
        
        # In M110-Format konvertieren
        image_data, height = self.image_to_m110_format(img)
        
        # M110 Bild-Befehl
        cmd = bytearray([
            0x1d, 0x76, 0x30,          # GS v 0
            0x00,                      # Mode: normal
            0x30, 0x00,                # Width: 48 bytes (Little-Endian!)
            height & 0xFF, (height >> 8) & 0xFF  # Height (Little-Endian!)
        ])
        
        # Vollständigen Befehl senden
        full_cmd = cmd + image_data
        print(f"📤 Sende Text-Bild: {len(full_cmd)} bytes, {height} Zeilen")
        self.send_command(full_cmd)
        
        # Paper Feed
        time.sleep(0.5)
        self.send_command(b'\x1b\x64\x03')  # Feed 3 lines
        
        print("✅ Text-Bild gesendet!")
    
    def create_text_image(self, text):
        """Erstellt Text-Bild"""
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        # Bild-Höhe berechnen
        lines = text.split('\n')
        img_height = len(lines) * 30 + 20
        
        # Bild erstellen
        img = Image.new('RGB', (self.width_pixels, img_height), 'white')
        draw = ImageDraw.Draw(img)
        
        # Text zentriert zeichnen
        y_pos = 10
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            x_pos = (self.width_pixels - line_width) // 2
            
            draw.text((x_pos, y_pos), line, fill='black', font=font)
            y_pos += 30
        
        return img.convert('1')  # Schwarz/Weiß
    
    def image_to_m110_format(self, img):
        """Konvertiert Bild zu M110-Format"""
        width, height = img.size
        pixels = list(img.getdata())
        
        image_data = bytearray()
        
        # Zeilenweise verarbeiten
        for y in range(height):
            line_bytes = bytearray()
            
            # 8 Pixel zu 1 Byte
            for x in range(0, width, 8):
                byte_val = 0
                for bit in range(8):
                    if x + bit < width:
                        pixel_idx = y * width + x + bit
                        if pixel_idx < len(pixels) and pixels[pixel_idx] == 0:  # Schwarz
                            byte_val |= (1 << (7 - bit))
                
                line_bytes.append(byte_val)
            
            # Auf 48 Bytes auffüllen
            while len(line_bytes) < 48:
                line_bytes.append(0)
            
            image_data.extend(line_bytes[:48])  # Exakt 48 Bytes
        
        return image_data, height

def main():
    print("🖨️ PHOMEMO M110 - KORREKTE BEFEHLE")
    print("Basierend auf vivier/phomemo-tools")
    print("=" * 50)
    
    printer = PhomemoM110Correct()
    
    if not os.path.exists(printer.device):
        print(f"❌ Device {printer.device} nicht gefunden")
        print("Bluetooth-Verbindung herstellen:")
        print("sudo rfcomm bind 0 12:7E:5A:E9:E5:22")
        return
    
    while True:
        print("\n🎯 M110 TESTS:")
        print("1. 🎨 Test-Pattern drucken")
        print("2. 📝 Text drucken")
        print("3. 🔧 Nur initialisieren")
        print("4. ❌ Exit")
        
        choice = input("\nWähle (1-4): ").strip()
        
        if choice == "1":
            printer.print_test_pattern()
        elif choice == "2":
            text = input("Text eingeben: ")
            printer.print_text_as_image(text)
        elif choice == "3":
            printer.initialize_printer()
        elif choice == "4":
            break
        else:
            print("❌ Ungültige Auswahl")

if __name__ == "__main__":
    main()
