#!/usr/bin/env python3
"""
Einfacher Struktur-Test ohne Unicode-Probleme
"""

import requests
import time
from PIL import Image, ImageDraw
import io

BASE_URL = "http://localhost:8080"

def simple_structure_test():
    """Einfacher Test der Struktur-Angleichung"""
    print("🔧 SIMPLE STRUCTURE TEST")
    print("=" * 50)
    print("📋 Testet Text vs Bild ohne Unicode-Probleme")
    print("=" * 50)
    
    # Test 1: Einfacher Text
    print("\n1️⃣ TEXT-TEST (Referenz):")
    text_success = simple_text_test()
    
    # Test 2: Einfaches Bild
    print("\n2️⃣ BILD-TEST (gleiche Struktur):")
    image_success = simple_image_test()
    
    # Test 3: Vergleich
    print("\n3️⃣ ERGEBNIS:")
    if text_success and image_success:
        print("🎉 BEIDE FUNKTIONIEREN - Struktur-Angleichung erfolgreich!")
        
        # Frontend-Parameter-Test
        param_test = input("Frontend-Parameter testen? (y/N): ").lower().strip()
        if param_test == 'y':
            test_frontend_params()
    elif text_success:
        print("⚠️ Text funktioniert, Bild noch nicht - weitere Anpassung nötig")
    else:
        print("❌ Beide haben Probleme - Grundlegende Reparatur nötig")

def simple_text_test():
    """Einfacher Text-Test"""
    try:
        test_text = """STRUCTURE TEST

Text Zeile 1
Text Zeile 2  
Text Zeile 3

Links  Mitte  Rechts
|      |      |

POSITION CHECK"""
        
        response = requests.post(f"{BASE_URL}/api/print-text", data={
            'text': test_text,
            'font_size': '16',
            'alignment': 'left',
            'immediate': 'true'
        })
        
        result = response.json()
        
        if result['success']:
            print("   ✅ Text gedruckt")
            quality = input("   Text-Qualität OK? (y/N): ").lower().strip()
            return quality == 'y'
        else:
            print(f"   ❌ Text-Fehler: {result.get('error', '?')}")
            return False
            
    except Exception as e:
        print(f"   ❌ Text-Exception: {e}")
        return False

def simple_image_test():
    """Einfacher Bild-Test mit gleicher Struktur"""
    try:
        # Einfaches Bild ohne Unicode
        width, height = 250, 150
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)
        
        # Gleicher Inhalt wie Text
        draw.text((10, 10), "STRUCTURE TEST", fill='black')
        draw.text((10, 30), "Bild Zeile 1", fill='black')
        draw.text((10, 50), "Bild Zeile 2", fill='black')
        draw.text((10, 70), "Bild Zeile 3", fill='black')
        
        draw.text((10, 100), "Links  Mitte  Rechts", fill='black')
        draw.text((10, 120), "|      |      |", fill='black')
        
        # Rahmen
        draw.rectangle([5, 5, width-5, height-5], outline='black', width=1)
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        image_data = buffer.getvalue()
        
        files = {'data': ('test.png', image_data, 'image/png')}
        data = {
            'use_queue': 'false',
            'fit_to_label': 'true',
            'maintain_aspect': 'true',
            'enable_dither': 'true'
        }
        
        response = requests.post(f"{BASE_URL}/api/print-image", files=files, data=data)
        result = response.json()
        
        if result['success']:
            print("   ✅ Bild gedruckt")
            quality = input("   Bild-Qualität OK? (y/N): ").lower().strip()
            return quality == 'y'
        else:
            print(f"   ❌ Bild-Fehler: {result.get('error', '?')}")
            return False
            
    except Exception as e:
        print(f"   ❌ Bild-Exception: {e}")
        return False

def test_frontend_params():
    """Testet Frontend-Parameter"""
    print("\n🔧 FRONTEND-PARAMETER-TEST:")
    
    # Einfaches Test-Bild
    width, height = 150, 100
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    draw.text((10, 20), "PARAM TEST", fill='black')
    draw.text((10, 40), "Scale & Dither", fill='black')
    draw.rectangle([5, 5, width-5, height-5], outline='black', width=2)
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    image_data = buffer.getvalue()
    
    # Test: Crop Center Mode
    print("   🧪 Test: Crop Center Mode")
    
    # 1. Vorschau
    files = {'data': ('param.png', image_data, 'image/png')}
    preview_data = {'scaling_mode': 'crop_center', 'fit_to_label': 'true'}
    
    preview_response = requests.post(f"{BASE_URL}/api/preview-image", files=files, data=preview_data)
    
    if preview_response.json()['success']:
        print("      ✅ Vorschau erstellt")
        
        # 2. Druck mit gleichen Parametern
        print_data = preview_data.copy()
        print_data['use_queue'] = 'false'
        
        files = {'data': ('param.png', image_data, 'image/png')}
        print_response = requests.post(f"{BASE_URL}/api/print-image", files=files, data=print_data)
        
        if print_response.json()['success']:
            print("      ✅ Druck erfolgreich")
            match = input("      Vorschau = Druck? (y/N): ").lower().strip()
            if match == 'y':
                print("      🎉 FRONTEND-PARAMETER FUNKTIONIEREN!")
            else:
                print("      ❌ Parameter-Problem weiterhin vorhanden")
        else:
            print("      ❌ Druck fehlgeschlagen")
    else:
        print("      ❌ Vorschau fehlgeschlagen")

if __name__ == "__main__":
    print("🔧 SIMPLE STRUCTURE TESTER")
    print("📋 Ohne Unicode-Probleme")
    print()
    
    simple_structure_test()
    
    print("\n🎉 Simple Structure Test abgeschlossen!")
