#!/usr/bin/env python3
"""
Direkter Phomemo M110 Hardware-Test
OHNE Web-Interface - nur Terminal
"""

import time
import os
import sys

class DirectPrinterTest:
    def __init__(self, device="/dev/rfcomm0"):
        self.device = device
        
    def check_device(self):
        """Prüft ob Device verfügbar ist"""
        if os.path.exists(self.device):
            print(f"✅ Device {self.device} gefunden")
            return True
        else:
            print(f"❌ Device {self.device} nicht gefunden")
            print("   Bluetooth-Verbindung prüfen:")
            print("   sudo rfcomm bind 0 12:7E:5A:E9:E5:22")
            return False
    
    def send_raw(self, data):
        """Sendet rohe Bytes an Drucker"""
        try:
            with open(self.device, 'wb') as printer:
                printer.write(data)
                printer.flush()
            print(f"✅ {len(data)} bytes gesendet")
            return True
        except Exception as e:
            print(f"❌ Sendefehler: {e}")
            return False
    
    def test_basic_feeds(self):
        """Testet grundlegende Paper Feeds"""
        print("\n🔧 TESTE PAPER FEEDS:")
        
        tests = [
            ("Line Feed", b'\n'),
            ("3x Line Feed", b'\n\n\n'),
            ("Carriage Return + LF", b'\r\n\r\n'),
            ("ESC d (Feed 3)", b'\x1b\x64\x03'),
            ("ESC d (Feed 5)", b'\x1b\x64\x05'),
            ("ESC J (Feed inch)", b'\x1b\x4a\x20'),
        ]
        
        for name, cmd in tests:
            print(f"\n📄 Test: {name}")
            input("   Drücke ENTER zum Senden...")
            if self.send_raw(cmd):
                response = input("   Hat sich das Papier bewegt? (j/n): ")
                if response.lower() == 'j':
                    print(f"   ✅ {name} funktioniert!")
                else:
                    print(f"   ❌ {name} keine Bewegung")
            time.sleep(1)
    
    def test_reset_commands(self):
        """Testet Reset-Befehle"""
        print("\n🔄 TESTE RESET-BEFEHLE:")
        
        resets = [
            ("ESC @ (Standard Reset)", b'\x1b\x40'),
            ("ESC ! (Format Reset)", b'\x1b\x21\x00'),
            ("GS ! (Character Size)", b'\x1d\x21\x00'),
            ("Multiple Reset", b'\x1b\x40\x1b\x21\x00\x1d\x21\x00'),
        ]
        
        for name, cmd in resets:
            print(f"\n🔄 Reset: {name}")
            input("   Drücke ENTER zum Senden...")
            self.send_raw(cmd)
            time.sleep(0.5)
            print("   Reset gesendet")
    
    def test_direct_text(self):
        """Testet direkten Text ohne Bildkonvertierung"""
        print("\n📝 TESTE DIREKTEN TEXT:")
        
        texts = [
            "HALLO",
            "DIRECT TEST",
            "123456789",
            "🖨️ PRINTER",
        ]
        
        for text in texts:
            print(f"\n📝 Text: '{text}'")
            input("   Drücke ENTER zum Senden...")
            
            # Text + mehrere Line Feeds
            data = (text + "\n\n\n").encode('utf-8')
            if self.send_raw(data):
                response = input("   Wurde Text gedruckt? (j/n): ")
                if response.lower() == 'j':
                    print(f"   ✅ Text-Druck funktioniert!")
                    return True
            time.sleep(1)
        
        return False
    
    def test_emergency_sequences(self):
        """Notfall-Sequenzen für hartnäckige Drucker"""
        print("\n🚨 NOTFALL-SEQUENZEN:")
        
        sequences = [
            ("Wake Up", b'\x00\x00\x00' + b'\x1b\x40'),
            ("Force Reset", b'\x1b\x40' * 3),
            ("Clear Buffer", b'\x18' + b'\x1b\x40'),  # CAN + Reset
            ("Full Wake", b'\x00' * 10 + b'\x1b\x40' + b'\n\n\n'),
        ]
        
        for name, cmd in sequences:
            print(f"\n🚨 Notfall: {name}")
            input("   Drücke ENTER zum Senden...")
            self.send_raw(cmd)
            time.sleep(1)
    
    def interactive_mode(self):
        """Interaktiver Modus für manuelle Tests"""
        print("\n🎮 INTERAKTIVER MODUS:")
        print("Befehle eingeben (hex mit \\x, text direkt)")
        print("Beispiele:")
        print("  reset          -> ESC @ Reset")
        print("  feed           -> Feed 3 lines") 
        print("  text:HALLO     -> Text senden")
        print("  hex:\\x1b\\x40   -> Hex-Bytes")
        print("  quit           -> Beenden")
        
        while True:
            try:
                cmd = input("\n📡 Befehl: ").strip()
                
                if cmd == "quit":
                    break
                elif cmd == "reset":
                    self.send_raw(b'\x1b\x40')
                elif cmd == "feed":
                    self.send_raw(b'\x1b\x64\x03')
                elif cmd.startswith("text:"):
                    text = cmd[5:] + "\n\n"
                    self.send_raw(text.encode('utf-8'))
                elif cmd.startswith("hex:"):
                    hex_str = cmd[4:]
                    try:
                        data = bytes(hex_str, 'utf-8').decode('unicode_escape').encode('latin1')
                        self.send_raw(data)
                    except:
                        print("❌ Ungültiger Hex-String")
                else:
                    print("❌ Unbekannter Befehl")
                    
            except KeyboardInterrupt:
                break
        
        print("\n👋 Interaktiver Modus beendet")

def main():
    print("🔧 DIREKTER PHOMEMO M110 HARDWARE-TEST")
    print("=" * 50)
    
    # Device prüfen
    printer = DirectPrinterTest()
    if not printer.check_device():
        print("\n💡 Bluetooth-Verbindung herstellen:")
        print("   sudo bluetoothctl")
        print("   > connect 12:7E:5A:E9:E5:22")
        print("   > exit")
        print("   sudo rfcomm bind 0 12:7E:5A:E9:E5:22")
        return
    
    # Hauptmenü
    while True:
        print("\n" + "="*50)
        print("🎯 HARDWARE-TESTS:")
        print("1. 📄 Paper Feed Tests")
        print("2. 🔄 Reset Commands") 
        print("3. 📝 Direct Text Tests")
        print("4. 🚨 Emergency Sequences")
        print("5. 🎮 Interactive Mode")
        print("6. ❌ Exit")
        
        try:
            choice = input("\nWähle Test (1-6): ").strip()
            
            if choice == "1":
                printer.test_basic_feeds()
            elif choice == "2":
                printer.test_reset_commands()
            elif choice == "3":
                if printer.test_direct_text():
                    print("\n🎉 ERFOLG! Direkter Text funktioniert!")
            elif choice == "4":
                printer.test_emergency_sequences()
            elif choice == "5":
                printer.interactive_mode()
            elif choice == "6":
                break
            else:
                print("❌ Ungültige Auswahl")
                
        except KeyboardInterrupt:
            print("\n👋 Programm beendet")
            break

if __name__ == "__main__":
    main()
