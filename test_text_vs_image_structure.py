#!/usr/bin/env python3
"""
Text vs Image Structure Test
Vergleicht die funktionierende Text-Struktur mit der Bild-Struktur
"""

import requests
import time
from PIL import Image, ImageDraw, ImageFont
import io

BASE_URL = "http://localhost:8080"

def test_text_vs_image_structure():
    """Vergleicht Text-Druck (funktioniert) mit Bild-Druck (gleiche Struktur)"""
    print("📊 TEXT vs IMAGE STRUCTURE TEST")
    print("=" * 60)
    print("🎯 Vergleicht funktionierende Text-Struktur mit Bild-Struktur")
    print("📋 Beide sollten jetzt identisch funktionieren")
    print("=" * 60)
    
    # Test 1: Text-Druck (Referenz - funktioniert)
    print("\n1️⃣ REFERENZ-TEST: Text-Druck (funktioniert)")
    test_text_print()
    
    # Test 2: Bild-Druck mit gleicher Struktur
    print("\n2️⃣ STRUKTUR-TEST: Bild-Druck (gleiche Struktur)")
    test_image_print()
    
    # Test 3: Vergleich
    print("\n3️⃣ VERGLEICH: Text vs Bild")
    compare_results()

def test_text_print():
    """Testet Text-Druck als funktionierende Referenz"""
    try:
        print("   📝 Drucke Test-Text...")
        
        test_text = """TEXT STRUCTURE TEST

Zeile 1: ABCDEFGHIJKLM
Zeile 2: NOPQRSTUVWXYZ
Zeile 3: 1234567890

Position Test:
<- Links    Mitte    Rechts ->
|          |          |

FUNKTIONIERT PERFEKT!"""
        
        response = requests.post(f"{BASE_URL}/api/print-text", data={
            'text': test_text,
            'font_size': '16',
            'alignment': 'left',
            'immediate': 'true'
        })
        
        result = response.json()
        
        if result['success']:
            print("   ✅ Text-Druck erfolgreich")
            print("   📋 Prüfe: Position, Ausrichtung, Qualität")
            
            quality = input("   📊 Text-Qualität (1-10): ").strip()
            if quality.isdigit() and int(quality) >= 8:
                print("   🎉 TEXT-STRUKTUR FUNKTIONIERT PERFEKT!")
                return True
            else:
                print("   ⚠️ Text-Struktur hat Qualitätsprobleme")
                return False
        else:
            print(f"   ❌ Text-Druck fehlgeschlagen: {result.get('error', '?')}")
            return False
            
    except Exception as e:
        print(f"   ❌ Text-Test Fehler: {e}")
        return False

def test_image_print():
    """Testet Bild-Druck mit gleicher Struktur wie Text"""
    try:
        print("   🖼️ Erstelle Test-Bild (gleiche Struktur wie Text)...")
        
        # Erstelle Bild mit GENAU dem gleichen Inhalt wie Text
        width, height = 300, 200
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)
        
        # Gleicher Inhalt wie Text-Test
        draw.text((10, 10), "IMAGE STRUCTURE TEST", fill='black')
        draw.text((10, 30), "Zeile 1: ABCDEFGHIJKLM", fill='black')
        draw.text((10, 50), "Zeile 2: NOPQRSTUVWXYZ", fill='black')
        draw.text((10, 70), "Zeile 3: 1234567890", fill='black')
        
        draw.text((10, 100), "Position Test:", fill='black')
        draw.text((10, 120), "<- Links    Mitte    Rechts ->", fill='black')
        draw.text((10, 140), "|          |          |", fill='black')
        
        draw.text((10, 170), "GLEICHE STRUKTUR WIE TEXT!", fill='black')
        
        # Rahmen für Position-Vergleich
        draw.rectangle([5, 5, width-5, height-5], outline='black', width=1)
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        test_image = buffer.getvalue()
        
        print("   📤 Drucke Test-Bild mit Text-Struktur...")
        
        files = {'data': ('structure_test.png', test_image, 'image/png')}
        data = {
            'use_queue': 'false',
            'fit_to_label': 'true',
            'maintain_aspect': 'true',
            'enable_dither': 'true',
            'scaling_mode': 'fit_aspect'
        }
        
        response = requests.post(f"{BASE_URL}/api/print-image", files=files, data=data)
        result = response.json()
        
        if result['success']:
            print("   ✅ Bild-Druck erfolgreich")
            print("   📋 Prüfe: Position, Ausrichtung, Qualität")
            
            quality = input("   📊 Bild-Qualität (1-10): ").strip()
            if quality.isdigit() and int(quality) >= 8:
                print("   🎉 BILD-STRUKTUR FUNKTIONIERT JETZT AUCH!")
                return True
            else:
                print("   ⚠️ Bild-Struktur hat noch Qualitätsprobleme")
                return False
        else:
            print(f"   ❌ Bild-Druck fehlgeschlagen: {result.get('error', '?')}")
            return False
            
    except Exception as e:
        print(f"   ❌ Bild-Test Fehler: {e}")
        return False

def compare_results():
    """Vergleicht die Ergebnisse"""
    print("   📊 ERGEBNIS-VERGLEICH:")
    print("       • Haben Text und Bild die gleiche Position?")
    print("       • Ist die Qualität vergleichbar?")
    print("       • Sind beide scharf und klar?")
    print("       • Keine Drift bei beiden?")
    
    match = input("   ❓ Sind Text und Bild-Qualität vergleichbar? (y/N): ").lower().strip()
    
    if match == 'y':
        print("   🎉 STRUKTUR-ANGLEICHUNG ERFOLGREICH!")
        print("   ✅ Text- und Bild-Druck verwenden jetzt gleiche Struktur")
        
        # Test Frontend-Parameter
        frontend_test = input("   ❓ Frontend-Parameter auch testen? (y/N): ").lower().strip()
        if frontend_test == 'y':
            test_frontend_parameters()
    else:
        print("   ❌ STRUKTUR-UNTERSCHIEDE WEITERHIN VORHANDEN")
        diagnose_structure_differences()

def test_frontend_parameters():
    """Testet Frontend-Parameter mit gleicher Struktur"""
    print("\n🔧 FRONTEND-PARAMETER-TEST:")
    
    # Erstelle einfaches Bild
    width, height = 200, 100
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    draw.text((10, 20), "PARAMETER TEST", fill='black')
    draw.text((10, 40), "Scaling & Dithering", fill='black')
    draw.rectangle([5, 5, width-5, height-5], outline='black', width=2)
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    test_image = buffer.getvalue()
    
    # Teste verschiedene Parameter
    parameter_tests = [
        {
            'name': 'Crop Center',
            'params': {'scaling_mode': 'crop_center', 'fit_to_label': 'true'}
        },
        {
            'name': 'No Dithering',
            'params': {'enable_dither': 'false', 'dither_threshold': '100'}
        }
    ]
    
    for test in parameter_tests:
        print(f"   🧪 Test: {test['name']}")
        
        # Vorschau
        files = {'data': ('param_test.png', test_image, 'image/png')}
        preview_response = requests.post(f"{BASE_URL}/api/preview-image", files=files, data=test['params'])
        
        if preview_response.json()['success']:
            print("      ✅ Vorschau erstellt")
            
            # Druck mit gleichen Parametern
            test['params']['use_queue'] = 'false'
            files = {'data': ('param_test.png', test_image, 'image/png')}
            print_response = requests.post(f"{BASE_URL}/api/print-image", files=files, data=test['params'])
            
            if print_response.json()['success']:
                print("      ✅ Druck erfolgreich")
                match = input(f"      ❓ {test['name']}: Vorschau = Druck? (y/N): ").lower().strip()
                if match == 'y':
                    print(f"      🎉 {test['name']} Parameter funktionieren!")
                else:
                    print(f"      ❌ {test['name']} Parameter-Problem")
            else:
                print("      ❌ Druck fehlgeschlagen")
        else:
            print("      ❌ Vorschau fehlgeschlagen")
        
        time.sleep(2)

def diagnose_structure_differences():
    """Diagnostiziert Struktur-Unterschiede"""
    print("   🔧 STRUKTUR-DIAGNOSE:")
    print("      1. send_bitmap Funktion: Gleich für Text und Bild?")
    print("      2. image_to_printer_format: Gleich für Text und Bild?")
    print("      3. Offset-Anwendung: Gleich für Text und Bild?")
    print("      4. Parameter-Verarbeitung: Gleich für Text und Bild?")
    
    print("\n   💡 LÖSUNGSANSÄTZE:")
    print("      • Schaue Server-Logs für Unterschiede")
    print("      • Vergleiche 'RESTORED WORKING' vs 'TEXT STRUCTURE' Ausgaben")
    print("      • Prüfe ob beide Methoden gleiche image_to_printer_format verwenden")

if __name__ == "__main__":
    print("📊 TEXT vs IMAGE STRUCTURE TESTER")
    print("🎯 Vergleicht funktionierende Text- mit Bild-Struktur")
    print()
    
    test_text_vs_image_structure()
    
    print("\n🎉 Struktur-Vergleich abgeschlossen!")
    print("📋 Erwartung: Beide sollten jetzt gleich gut funktionieren")
