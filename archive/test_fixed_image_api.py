#!/usr/bin/env python3
"""
Reparierter Test für Bild-API-Endpunkte
Testet preview-image und print-image mit korrekten Methoden
"""

import requests
import os
import base64
from PIL import Image
import io

BASE_URL = "http://localhost:8080"

def create_test_image():
    """Erstellt ein einfaches Test-Bild"""
    # Einfaches Test-Bild erstellen (200x100px mit Text)
    img = Image.new('RGB', (200, 100), 'white')
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    
    # Einfaches Muster zeichnen
    draw.rectangle([10, 10, 190, 90], outline='black', width=3)
    draw.text((50, 35), "API TEST", fill='black')
    draw.line([10, 50, 190, 50], fill='gray', width=1)
    
    # Als PNG speichern
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()

def test_fixed_apis():
    print("🔧 Teste reparierte Bild-APIs...")
    print("=" * 50)
    
    # Test-Bild erstellen
    test_image = create_test_image()
    print(f"📸 Test-Bild erstellt: {len(test_image)} bytes PNG")
    
    try:
        # Test 1: Preview-Image API (sollte funktionieren)
        print("\n🔍 Teste /api/preview-image...")
        files = {'data': ('test.png', test_image, 'image/png')}
        data = {
            'fit_to_label': 'true',
            'maintain_aspect': 'true',
            'enable_dither': 'true',
            'dither_threshold': '128'
        }
        
        response = requests.post(f"{BASE_URL}/api/preview-image", files=files, data=data)
        result = response.json()
        
        if result['success']:
            print(f"   ✅ Preview erfolgreich: {len(result['preview_base64'])} Zeichen Base64")
            if 'info' in result:
                info = result['info']
                print(f"   📐 Verarbeitet: {info.get('processed_width', '?')}×{info.get('processed_height', '?')}px")
                print(f"   🎛️ Offsets: X={info.get('x_offset', 0)}, Y={info.get('y_offset', 0)}")
        else:
            print(f"   ❌ Preview fehlgeschlagen: {result['error']}")
            return
            
        # Test 2: Print-Image API mit Sofort-Druck (use_queue=false)
        print("\n🖨️ Teste /api/print-image (sofortiger Druck)...")
        files = {'data': ('test.png', test_image, 'image/png')}
        data = {
            'use_queue': 'false',  # Sofortiger Druck
            'fit_to_label': 'true',
            'maintain_aspect': 'true', 
            'dither': 'true'
        }
        
        response = requests.post(f"{BASE_URL}/api/print-image", files=files, data=data)
        result = response.json()
        
        if result['success']:
            print(f"   ✅ Sofort-Druck erfolgreich verarbeitet")
            print(f"   📄 {result.get('message', 'Kein Message-Text')}")
            print(f"   📏 Format: {result.get('format', '?')}")
            print(f"   📦 Größe: {result.get('size_bytes', '?')} bytes")
        else:
            print(f"   ❌ Sofort-Druck fehlgeschlagen: {result['error']}")
        
        # Test 3: Print-Image API mit Queue (use_queue=true)
        print("\n⏰ Teste /api/print-image (mit Queue)...")
        files = {'data': ('test.png', test_image, 'image/png')}
        data = {
            'use_queue': 'true',   # Queue verwenden
            'fit_to_label': 'true',
            'maintain_aspect': 'true',
            'dither': 'true'
        }
        
        response = requests.post(f"{BASE_URL}/api/print-image", files=files, data=data)
        result = response.json()
        
        if result['success']:
            print(f"   ✅ Queue-Druck erfolgreich")
            print(f"   🆔 Job-ID: {result.get('job_id', '?')}")
            print(f"   📄 {result.get('message', 'Kein Message-Text')}")
        else:
            print(f"   ❌ Queue-Druck fehlgeschlagen: {result['error']}")
            
        # Test 4: Verschiedene Datei-Feldnamen
        print("\n📎 Teste verschiedene Datei-Feldnamen...")
        for field_name in ['data', 'image']:
            files = {field_name: ('test.png', test_image, 'image/png')}
            response = requests.post(f"{BASE_URL}/api/preview-image", files=files)
            result = response.json()
            
            status = "✅" if result['success'] else "❌"
            print(f"   {status} Feld '{field_name}': {'OK' if result['success'] else result['error']}")
            
        print("\n" + "=" * 50)
        print("🎉 Reparierte Bild-API-Tests abgeschlossen!")
        
        # Zusammenfassung der verfügbaren Methoden
        print("\n📋 Verfügbare API-Methoden:")
        print("   • /api/preview-image  → Vorschau ohne Drucken")
        print("   • /api/print-image    → Drucken (sofort oder Queue)")
        print("   • Parameter:")
        print("     - use_queue=false   → Sofortiger Druck")
        print("     - use_queue=true    → In Warteschlange einreihen")
        print("     - Datei-Feld: 'data' oder 'image'")
        
    except requests.exceptions.ConnectionError:
        print("❌ Server nicht erreichbar - Starte Server mit: python3 main.py")
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}")

if __name__ == "__main__":
    test_fixed_apis()
