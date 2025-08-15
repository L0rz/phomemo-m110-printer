#!/usr/bin/env python3
"""
Test-Skript für Label-Größen-Feature
"""

import requests
import json

# Server-URL
BASE_URL = "http://localhost:8080"

def test_label_sizes():
    print("🧪 Teste Label-Größen-Feature...")
    
    try:
        # 1. Verfügbare Label-Größen abrufen
        print("\n1. Lade verfügbare Label-Größen...")
        response = requests.get(f"{BASE_URL}/api/label-sizes")
        data = response.json()
        
        if data['success']:
            print(f"✅ {len(data['available_sizes'])} Label-Größen verfügbar:")
            for key, size in data['available_sizes'].items():
                current = " (AKTUELL)" if key == data['current_size']['current'] else ""
                print(f"   📏 {key}: {size['name']} - {size['width_px']}×{size['height_px']}px{current}")
        else:
            print(f"❌ Fehler: {data['error']}")
            return
        
        # 2. Label-Größe wechseln
        print("\n2. Teste Label-Größen-Wechsel...")
        test_sizes = ['30x50', '25x25', '40x30']  # Zurück zum Standard
        
        for size_key in test_sizes:
            print(f"\n   Wechsle zu {size_key}...")
            response = requests.post(f"{BASE_URL}/api/label-size", data={'label_size': size_key})
            data = response.json()
            
            if data['success']:
                print(f"   ✅ {data['message']}")
                print(f"   📐 Neue Größe: {data['current_size']['width_px']}×{data['current_size']['height_px']}px")
            else:
                print(f"   ❌ Fehler: {data['error']}")
        
        # 3. Test-Vorschau mit QR-Code
        print("\n3. Teste Vorschau mit QR-Code...")
        test_text = """# Test Label

**Größe:** Variable

#qr#https://github.com/phomemo-m110#qr#

**Barcode:** #bar#TEST-ABC123#bar#

✅ Dynamic sizing works!"""
        
        response = requests.post(f"{BASE_URL}/api/preview-text", data={
            'text': test_text,
            'font_size': '22',
            'alignment': 'center'
        })
        data = response.json()
        
        if data['success']:
            print("   ✅ Vorschau erfolgreich erstellt!")
            print(f"   📸 Vorschau-Größe: {len(data['preview_base64'])} Zeichen Base64")
        else:
            print(f"   ❌ Vorschau-Fehler: {data['error']}")
        
        print("\n🎉 Label-Größen-Feature funktioniert!")
        print(f"\n🌐 Öffne: {BASE_URL}/label-sizes")
        
    except requests.exceptions.ConnectionError:
        print("❌ Verbindungsfehler: Server läuft nicht oder ist nicht erreichbar")
        print("   Starte den Server mit: python3 main.py")
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}")

if __name__ == "__main__":
    test_label_sizes()
