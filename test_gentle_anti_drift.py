#!/usr/bin/env python3
"""
Sanfter Anti-Drift-Test
Testet schonende Anti-Drift-Einstellungen ohne aggressive Position-Resets
"""

import requests
import time
from PIL import Image, ImageDraw
import io

BASE_URL = "http://localhost:8080"

def create_simple_test_image(test_number: int) -> bytes:
    """Erstellt ein einfaches Test-Bild ohne komplexe Patterns"""
    width, height = 150, 100
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Einfacher Rahmen
    draw.rectangle([0, 0, width-1, height-1], outline='black', width=2)
    
    # Test-Nummer
    draw.text((10, 10), f"Test #{test_number}", fill='black')
    
    # Links-Markierung (zur Drift-Erkennung)
    draw.rectangle([5, 30, 15, 40], fill='black')
    draw.text((20, 32), "L", fill='black')
    
    # Rechts-Markierung
    draw.rectangle([width-15, 30, width-5, 40], fill='black') 
    draw.text((width-25, 32), "R", fill='black')
    
    # Zentral-Linie
    center_x = width // 2
    draw.line([center_x, 20, center_x, 80], fill='gray', width=1)
    draw.text((center_x-5, 85), "C", fill='gray')
    
    # Status-Text
    draw.text((10, 50), "Gentle Anti-Drift", fill='black')
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()

def test_gentle_anti_drift():
    """Testet schonende Anti-Drift-Einstellungen"""
    print("🕊️ SCHONENDER ANTI-DRIFT-TEST")
    print("=" * 50)
    print("📋 Testet die reparierte Version ohne aggressive Resets")
    print("=" * 50)
    
    test_count = 3
    
    print(f"🧪 Test-Parameter:")
    print(f"   • Anzahl Tests: {test_count}")
    print(f"   • Schonende Einstellungen aktiviert")
    print(f"   • Keine aggressiven Position-Resets")
    print()
    
    try:
        for i in range(1, test_count + 1):
            print(f"📸 Schonender Test #{i}/{test_count}...")
            
            test_image = create_simple_test_image(i)
            
            files = {'data': (f'gentle_test_{i}.png', test_image, 'image/png')}
            data = {
                'use_queue': 'false',
                'fit_to_label': 'true',
                'maintain_aspect': 'true',
                'dither': 'true'
            }
            
            start_time = time.time()
            response = requests.post(f"{BASE_URL}/api/print-image", files=files, data=data)
            end_time = time.time()
            
            result = response.json()
            
            if result['success']:
                print(f"   ✅ Test #{i} erfolgreich ({end_time-start_time:.2f}s)")
                print(f"      📏 {result.get('format', '?')} - {result.get('size_bytes', '?')} bytes")
            else:
                print(f"   ❌ Test #{i} fehlgeschlagen: {result['error']}")
                break
            
            # Moderate Pause
            if i < test_count:
                print("   ⏱️ Warte 1 Sekunde...")
                time.sleep(1.0)
        
        print("\n" + "="*50)
        print("🔍 VISUELLER CHECK:")
        print("✅ ERFOLGREICH: Keine Zeilen-Sprünge nach links")
        print("✅ ERFOLGREICH: Alle Labels gleich positioniert")
        print("❌ PROBLEM: Labels springen nach links/rechts")
        print()
        print("📋 Prüfe die L-C-R Markierungen:")
        print("   • L (Links) sollte bei allen Labels an derselben Stelle sein")
        print("   • C (Center) sollte mittig sein")
        print("   • R (Rechts) sollte bei allen Labels gleich sein")
        
    except requests.exceptions.ConnectionError:
        print("❌ Server nicht erreichbar")
        print("   Starte Server mit: python3 main.py")
    except Exception as e:
        print(f"❌ Test-Fehler: {e}")

def test_original_behavior():
    """Testet ohne jegliche Anti-Drift-Maßnahmen"""
    print("\n🔄 ORIGINAL-VERHALTEN-TEST")
    print("   Schnelle Aufeinanderfolge ohne Anti-Drift-Pausen...")
    
    for i in range(1, 4):
        print(f"   ⚡ Schnell-Test #{i}/3...")
        
        test_image = create_simple_test_image(100 + i)
        files = {'data': (f'fast_{i}.png', test_image, 'image/png')}
        
        try:
            response = requests.post(f"{BASE_URL}/api/print-image", 
                                   files=files, 
                                   data={'use_queue': 'false'})
            result = response.json()
            
            status = "✅" if result['success'] else "❌"
            print(f"      {status} Schnell-Test #{i}")
            
            # Sehr kurze Pause (kritisch für Drift)
            if i < 3:
                time.sleep(0.1)
                
        except Exception as e:
            print(f"      ❌ Fehler: {e}")

if __name__ == "__main__":
    print("🕊️ SCHONENDER ANTI-DRIFT-TESTER")
    print()
    
    test_gentle_anti_drift()
    
    # Optional: Test ohne Anti-Drift für Vergleich
    answer = input("\n❓ Original-Verhalten testen (zum Vergleich)? (y/N): ")
    if answer.lower() == 'y':
        test_original_behavior()
    
    print("\n🎉 Schonende Anti-Drift-Tests abgeschlossen!")
    print("📋 Die Labels sollten jetzt ohne Links-Sprünge gedruckt werden.")
