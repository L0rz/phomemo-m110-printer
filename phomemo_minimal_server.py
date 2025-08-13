#!/usr/bin/env python3
"""
Phomemo M110 Minimal Server
Funktioniert nur mit Python-Standardbibliotheken und python3-pybluez
"""

import bluetooth
import socket
import threading
import time

class PhomemoM110Printer:
    """Minimaler Handler für Phomemo M110 Drucker"""
    
    # ESC/POS Befehle
    ESC = b'\x1b'
    GS = b'\x1d'
    US = b'\x1f'
    
    # Wichtige Befehle
    INIT_PRINTER = ESC + b'\x40'
    SELECT_JUSTIFICATION = ESC + b'\x61'
    PRINT_RASTER_IMAGE = GS + b'\x76\x30'
    FEED_LINES = ESC + b'\x64'
    SET_PRINT_SPEED = ESC + b'\x4e\x0d'
    SET_PRINT_DENSITY = ESC + b'\x4e\x04'
    SET_MEDIA_TYPE = US + b'\x11'
    
    # Druckerparameter
    DOTS_PER_LINE = 384
    BYTES_PER_LINE = 48
    MAX_LINES_PER_BLOCK = 255
    
    def __init__(self, mac_address, channel=1):
        self.mac_address = mac_address
        self.channel = channel
        self.socket = None
        
    def connect(self):
        """Verbindung zum Drucker herstellen"""
        try:
            self.socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.socket.connect((self.mac_address, self.channel))
            print(f"Verbunden mit {self.mac_address}:{self.channel}")
            self.init_printer()
            return True
        except Exception as e:
            print(f"Verbindungsfehler: {e}")
            return False
    
    def disconnect(self):
        """Verbindung trennen"""
        if self.socket:
            self.socket.close()
            self.socket = None
    
    def init_printer(self):
        """Drucker initialisieren"""
        if not self.socket:
            return
        
        self.socket.send(self.INIT_PRINTER)
        self.socket.send(self.SET_PRINT_SPEED + b'\x03')
        self.socket.send(self.SET_PRINT_DENSITY + b'\x0a')
        self.socket.send(self.SET_MEDIA_TYPE + b'\x0a')
        self.socket.send(self.SELECT_JUSTIFICATION + b'\x01')
        time.sleep(0.1)
    
    def text_to_simple_bitmap(self, text):
        """
        Konvertiert Text in einfaches Bitmap (ohne PIL)
        Verwendet eine simple 8x8 Pixel Schrift
        """
        # Einfache 8x8 ASCII Font (nur Großbuchstaben und Zahlen)
        font_8x8 = {
            ' ': [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
            'A': [0x18, 0x3C, 0x66, 0x7E, 0x66, 0x66, 0x66, 0x00],
            'B': [0x7E, 0x66, 0x66, 0x7E, 0x66, 0x66, 0x7E, 0x00],
            'C': [0x3C, 0x66, 0x60, 0x60, 0x60, 0x66, 0x3C, 0x00],
            'D': [0x78, 0x6C, 0x66, 0x66, 0x66, 0x6C, 0x78, 0x00],
            'E': [0x7E, 0x60, 0x60, 0x78, 0x60, 0x60, 0x7E, 0x00],
            'F': [0x7E, 0x60, 0x60, 0x78, 0x60, 0x60, 0x60, 0x00],
            'G': [0x3C, 0x66, 0x60, 0x6E, 0x66, 0x66, 0x3C, 0x00],
            'H': [0x66, 0x66, 0x66, 0x7E, 0x66, 0x66, 0x66, 0x00],
            'I': [0x3C, 0x18, 0x18, 0x18, 0x18, 0x18, 0x3C, 0x00],
            'J': [0x1E, 0x0C, 0x0C, 0x0C, 0x0C, 0x6C, 0x38, 0x00],
            'K': [0x66, 0x6C, 0x78, 0x70, 0x78, 0x6C, 0x66, 0x00],
            'L': [0x60, 0x60, 0x60, 0x60, 0x60, 0x60, 0x7E, 0x00],
            'M': [0x63, 0x77, 0x7F, 0x6B, 0x63, 0x63, 0x63, 0x00],
            'N': [0x66, 0x76, 0x7E, 0x7E, 0x6E, 0x66, 0x66, 0x00],
            'O': [0x3C, 0x66, 0x66, 0x66, 0x66, 0x66, 0x3C, 0x00],
            'P': [0x7C, 0x66, 0x66, 0x7C, 0x60, 0x60, 0x60, 0x00],
            'Q': [0x3C, 0x66, 0x66, 0x66, 0x66, 0x3C, 0x0E, 0x00],
            'R': [0x7C, 0x66, 0x66, 0x7C, 0x78, 0x6C, 0x66, 0x00],
            'S': [0x3C, 0x66, 0x60, 0x3C, 0x06, 0x66, 0x3C, 0x00],
            'T': [0x7E, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x00],
            'U': [0x66, 0x66, 0x66, 0x66, 0x66, 0x66, 0x3C, 0x00],
            'V': [0x66, 0x66, 0x66, 0x66, 0x66, 0x3C, 0x18, 0x00],
            'W': [0x63, 0x63, 0x63, 0x6B, 0x7F, 0x77, 0x63, 0x00],
            'X': [0x66, 0x66, 0x3C, 0x18, 0x3C, 0x66, 0x66, 0x00],
            'Y': [0x66, 0x66, 0x66, 0x3C, 0x18, 0x18, 0x18, 0x00],
            'Z': [0x7E, 0x06, 0x0C, 0x18, 0x30, 0x60, 0x7E, 0x00],
            '0': [0x3C, 0x66, 0x6E, 0x76, 0x66, 0x66, 0x3C, 0x00],
            '1': [0x18, 0x38, 0x18, 0x18, 0x18, 0x18, 0x7E, 0x00],
            '2': [0x3C, 0x66, 0x06, 0x0C, 0x30, 0x60, 0x7E, 0x00],
            '3': [0x3C, 0x66, 0x06, 0x1C, 0x06, 0x66, 0x3C, 0x00],
            '4': [0x06, 0x0E, 0x1E, 0x66, 0x7F, 0x06, 0x06, 0x00],
            '5': [0x7E, 0x60, 0x7C, 0x06, 0x06, 0x66, 0x3C, 0x00],
            '6': [0x3C, 0x66, 0x60, 0x7C, 0x66, 0x66, 0x3C, 0x00],
            '7': [0x7E, 0x66, 0x0C, 0x18, 0x18, 0x18, 0x18, 0x00],
            '8': [0x3C, 0x66, 0x66, 0x3C, 0x66, 0x66, 0x3C, 0x00],
            '9': [0x3C, 0x66, 0x66, 0x3E, 0x06, 0x66, 0x3C, 0x00],
            '.': [0x00, 0x00, 0x00, 0x00, 0x00, 0x18, 0x18, 0x00],
            ',': [0x00, 0x00, 0x00, 0x00, 0x00, 0x18, 0x18, 0x30],
            ':': [0x00, 0x18, 0x18, 0x00, 0x00, 0x18, 0x18, 0x00],
            '-': [0x00, 0x00, 0x00, 0x7E, 0x00, 0x00, 0x00, 0x00],
            '!': [0x18, 0x18, 0x18, 0x18, 0x00, 0x00, 0x18, 0x00],
        }
        
        # Text in Großbuchstaben konvertieren
        text = text.upper()
        lines = text.split('\n')
        
        # Berechne Bildhöhe (10 Pixel pro Zeile + Abstand)
        char_height = 10
        line_spacing = 4
        height = len(lines) * (char_height + line_spacing)
        
        # Bitmap erstellen
        bitmap_data = bytearray()
        
        for line in lines:
            # 10 Pixelzeilen pro Textzeile (8 für Zeichen + 2 Abstand)
            for pixel_row in range(char_height):
                line_data = bytearray(self.BYTES_PER_LINE)
                
                if pixel_row < 8:  # Zeichenbereich
                    x_pos = 0
                    for char in line:
                        if char in font_8x8 and x_pos < self.DOTS_PER_LINE - 8:
                            char_data = font_8x8[char][pixel_row]
                            # Zeichen in Bitmap einfügen
                            byte_index = x_pos // 8
                            bit_offset = x_pos % 8
                            
                            # Zeichen skalieren (2x Breite)
                            for bit in range(8):
                                if char_data & (0x80 >> bit):
                                    # Zwei Pixel setzen für breitere Zeichen
                                    if x_pos < self.DOTS_PER_LINE:
                                        line_data[x_pos // 8] |= (0x80 >> (x_pos % 8))
                                    x_pos += 1
                                    if x_pos < self.DOTS_PER_LINE:
                                        line_data[x_pos // 8] |= (0x80 >> (x_pos % 8))
                                    x_pos += 1
                                else:
                                    x_pos += 2
                            
                            x_pos += 4  # Abstand zwischen Zeichen
                
                bitmap_data.extend(line_data)
            
            # Leerzeilen zwischen Textzeilen
            for _ in range(line_spacing):
                bitmap_data.extend(bytearray(self.BYTES_PER_LINE))
        
        return bytes(bitmap_data), height
    
    def print_bitmap(self, bitmap_data, height):
        """Druckt Bitmap-Daten"""
        if not self.socket:
            return False
        
        try:
            lines_sent = 0
            
            while lines_sent < height:
                lines_in_block = min(self.MAX_LINES_PER_BLOCK, height - lines_sent)
                
                # Rasterbildbefehl
                cmd = self.PRINT_RASTER_IMAGE
                cmd += b'\x00'  # Modus: normal
                cmd += bytes([self.BYTES_PER_LINE, 0x00])
                cmd += bytes([lines_in_block, 0x00])
                
                self.socket.send(cmd)
                
                # Bilddaten
                start = lines_sent * self.BYTES_PER_LINE
                end = (lines_sent + lines_in_block) * self.BYTES_PER_LINE
                self.socket.send(bitmap_data[start:end])
                
                lines_sent += lines_in_block
                time.sleep(0.01)
            
            # Papiervorschub
            self.socket.send(self.FEED_LINES + b'\x03')
            
            return True
            
        except Exception as e:
            print(f"Druckfehler: {e}")
            return False
    
    def print_text(self, text):
        """Druckt Text"""
        bitmap_data, height = self.text_to_simple_bitmap(text)
        return self.print_bitmap(bitmap_data, height)


class PrintServer:
    """TCP Server für Druckaufträge"""
    
    def __init__(self, printer, host='0.0.0.0', port=9100):
        self.printer = printer
        self.host = host
        self.port = port
        self.running = False
        
    def start(self):
        """Server starten"""
        self.running = True
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        
        print(f"Server läuft auf {self.host}:{self.port}")
        print("Sende Text an Port 9100 zum Drucken")
        print("Beispiel: echo 'TEST' | nc localhost 9100")
        
        while self.running:
            try:
                client_socket, address = server_socket.accept()
                print(f"Verbindung von {address}")
                
                thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket,)
                )
                thread.start()
                
            except KeyboardInterrupt:
                break
        
        server_socket.close()
    
    def handle_client(self, client_socket):
        """Behandelt Druckaufträge"""
        try:
            data = b""
            while True:
                chunk = client_socket.recv(1024)
                if not chunk:
                    break
                data += chunk
            
            if data:
                text = data.decode('utf-8', errors='ignore').strip()
                print(f"Drucke: {text[:50]}...")
                
                if self.printer.connect():
                    if self.printer.print_text(text):
                        client_socket.send(b"OK\n")
                    else:
                        client_socket.send(b"ERROR\n")
                    self.printer.disconnect()
                else:
                    client_socket.send(b"NO CONNECTION\n")
            
        except Exception as e:
            print(f"Fehler: {e}")
            client_socket.send(f"ERROR: {e}\n".encode())
        
        finally:
            client_socket.close()


if __name__ == "__main__":
    import sys
    
    # Konfiguration - ANPASSEN!
    PRINTER_MAC = "DC:0D:30:90:23:C7"
    PRINTER_CHANNEL = 1
    SERVER_PORT = 9100
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            # Testmodus
            printer = PhomemoM110Printer(PRINTER_MAC, PRINTER_CHANNEL)
            if printer.connect():
                print("Sende Testdruck...")
                printer.print_text("PHOMEMO M110 TEST\n1234567890\nABCDEFGHIJ")
                printer.disconnect()
                print("Fertig!")
        else:
            PRINTER_MAC = sys.argv[1]
    
    # Server starten
    printer = PhomemoM110Printer(PRINTER_MAC, PRINTER_CHANNEL)
    server = PrintServer(printer, port=SERVER_PORT)
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nBeende...")
