#!/usr/bin/env python3
"""
Test für Bild-API-Endpunkte
Testet preview-image und print-image mit verschiedenen Formaten
"""

import requests
import os
import base64
from PIL import Image
import io

BASE_URL = "http://localhost:8080"

def create_test_images():
    """Erstellt Test-Bilder in verschiedenen Formaten"""
    test_images = {}
    
    # Einfaches Test-Bild erstellen (100x100px mit Text)
    img = Image.new('RGB', (100, 100), 'white')
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(img)
    
    # Einfaches Muster zeichnen
    draw.rectangle([10, 10, 90, 90], outline='black', width=2)
    draw.text((25, 40), "TEST", fill='black')
    
    # In verschiedenen Formaten speichern
    formats = ['PNG', 'JPEG', 'BMP', 'GIF']
    
    for fmt in formats:
        buffer = io.BytesIO()
        save_format = 'JPEG' if fmt == 'JPG' else fmt
        img.save(buffer, format=save_format)
        test_images[fmt] = buffer.getvalue()
    
    return test_images

def test_image_apis():
    print("🖼️ Teste Bild-API-Endpunkte...")
    print("=" * 50)
    
    # Test-Bilder erstellen
    test_images = create_test_images()
    
    for format_name, image_data in test_images.items():
        print(f"\n📸 Teste {format_name}-Bild ({len(image_data)} bytes)...")
        
        # Test 1: Preview-Image API
        print("   🔍 Teste /api/preview-image...")
        try:
            files = {'data': (f'test.{format_name.lower()}', image_data, f'image/{format_name.lower()}')}
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
            else:
                print(f"   ❌ Preview fehlgeschlagen: {result['error']}")
                
        except requests.exceptions.ConnectionError:
            print("   ❌ Server nicht erreichbar")
            return
        except Exception as e:
            print(f"   ❌ Fehler: {e}")
        
        # Test 2: Print-Image API (ohne tatsächlich zu drucken)
        print("   🖨️ Teste /api/print-image...")
        try:
            files = {'data': (f'test.{format_name.lower()}', image_data, f'image/{format_name.lower()}')}
            data = {
                'use_queue': 'false',  # Direkt verarbeiten
                'fit_to_label': 'true',
                'maintain_aspect': 'true',
                'dither': 'true'
            }
            
            response = requests.post(f"{BASE_URL}/api/print-image", files=files, data=data)
            result = response.json()
            
            if result['success']:
                print(f"   ✅ Print-API erfolgreich verarbeitet")
                if 'message' in result:
                    print(f"   📄 {result['message']}")
            else:
                print(f"   ❌ Print-API fehlgeschlagen: {result['error']}")
                
        except Exception as e:
            print(f"   ❌ Print-API Fehler: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Test verschiedener Datei-Feld-Namen...")
    
    # Test mit 'image' statt 'data' Feld
    png_data = test_images['PNG']
    
    for field_name in ['data', 'image']:
        print(f"\n📎 Teste Feld-Name: '{field_name}'...")
        try:
            files = {field_name: ('test.png', png_data, 'image/png')}
            response = requests.post(f"{BASE_URL}/api/preview-image", files=files)
            result = response.json()
            
            if result['success']:
                print(f"   ✅ Feld '{field_name}' funktioniert")
            else:
                print(f"   ❌ Feld '{field_name}' fehlgeschlagen: {result['error']}")
                
        except Exception as e:
            print(f"   ❌ Fehler mit Feld '{field_name}': {e}")
    
    print("\n🎉 Bild-API-Tests abgeschlossen!")
    
    # Zusätzlicher Test: Fehlerhaftes Format
    print("\n⚠️ Teste fehlerhaftes Format...")
    try:
        fake_data = b"Das ist kein Bild"
        files = {'data': ('test.txt', fake_data, 'text/plain')}
        response = requests.post(f"{BASE_URL}/api/preview-image", files=files)
        result = response.json()
        
        if not result['success']:
            print(f"   ✅ Fehlerhafte Formate werden korrekt abgelehnt: {result['error']}")
        else:
            print("   ❌ Fehlerhafte Formate sollten abgelehnt werden!")
            
    except Exception as e:
        print(f"   ❌ Unerwarteter Fehler: {e}")

if __name__ == "__main__":
    test_image_apis()
