#!/usr/bin/env python3
"""
Demo: Label-Größen mit QR/Barcode-Anpassung
Zeigt, wie sich Codes automatisch an verschiedene Label-Größen anpassen
"""

import requests
import json

BASE_URL = "http://localhost:8080"

def demo_label_sizes():
    print("🎭 DEMO: Label-Größen mit automatischer Code-Anpassung")
    print("=" * 60)
    
    # Demo-Text mit verschiedenen Codes
    demo_text = """# LABEL-DEMO

**Produkt:** #bar#DEMO-ABC123#bar#

**Website:** #qr#https://github.com/phomemo-m110#qr#

**Info:** Automatische Größenanpassung
"""
    
    label_sizes = [
        ('25x25', 'Kleines Quadrat'),
        ('40x30', 'Standard'),
        ('50x30', 'Breit/Standard'),
        ('30x50', 'Schmal/Hoch'),
        ('50x80', 'Groß/Hoch'),
        ('80x50', 'Extra Breit')
    ]
    
    for size_key, description in label_sizes:
        print(f"\n📏 Teste {size_key}mm ({description})...")
        
        try:
            # 1. Label-Größe setzen
            response = requests.post(f"{BASE_URL}/api/label-size", 
                                   data={'label_size': size_key})
            data = response.json()
            
            if not data['success']:
                print(f"   ❌ Größenwechsel fehlgeschlagen: {data['error']}")
                continue
                
            print(f"   ✅ Größe gewechselt: {data['current_size']['width_px']}×{data['current_size']['height_px']}px")
            
            # 2. Syntax-Hilfe abrufen (zeigt dynamische Limits)
            response = requests.get(f"{BASE_URL}/api/code-syntax-help")
            if response.status_code == 200:
                help_data = response.json()
                if help_data['success']:
                    help_text = help_data['syntax_help']
                    # QR und Barcode Limits extrahieren
                    qr_line = [line for line in help_text.split('\n') if 'Maximale QR-Größe' in line]
                    bar_line = [line for line in help_text.split('\n') if 'Maximale Barcode-Höhe' in line]
                    
                    if qr_line:
                        print(f"   📱 {qr_line[0].strip()}")
                    if bar_line:
                        print(f"   📊 {bar_line[0].strip()}")
            
            # 3. Vorschau erstellen
            response = requests.post(f"{BASE_URL}/api/preview-text", data={
                'text': demo_text,
                'font_size': '20',
                'alignment': 'center'
            })
            
            preview_data = response.json()
            if preview_data['success']:
                print(f"   📸 Vorschau erstellt ({len(preview_data['preview_base64'])} Zeichen)")
                print(f"   🎯 Optimiert für: {data['current_size']['width_mm']}×{data['current_size']['height_mm']}mm")
            else:
                print(f"   ❌ Vorschau fehlgeschlagen: {preview_data['error']}")
                
        except requests.exceptions.ConnectionError:
            print("   ❌ Server nicht erreichbar")
            break
        except Exception as e:
            print(f"   ❌ Fehler: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 DEMO abgeschlossen!")
    print("🌐 Öffne das Web-Interface für interaktive Tests:")
    print(f"   {BASE_URL}/label-sizes")
    print("\n💡 Features:")
    print("   • QR-Codes passen sich automatisch an Label-Breite an")
    print("   • Barcodes passen sich automatisch an Label-Höhe an") 
    print("   • Optimale Größen für jedes Label-Format")
    print("   • Live-Vorschau mit Dark/Light Mode")

if __name__ == "__main__":
    demo_label_sizes()
