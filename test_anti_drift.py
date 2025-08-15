#!/usr/bin/env python3
"""
Anti-Drift Test für Phomemo M110
Testet die Rechts-Verschiebung bei vielen Druckaufträgen
"""

import requests
import time
from PIL import Image, ImageDraw, ImageFont
import io
import threading

BASE_URL = "http://localhost:8080"

def create_position_test_image(test_number: int, pattern_type: str = "grid") -> bytes:
    """Erstellt ein Test-Bild mit Positionsmarkierungen"""
    width, height = 200, 150
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    if pattern_type == "grid":
        # Gitter-Pattern für Positions-Erkennung
        for x in range(0, width, 20):
            draw.line([x, 0, x, height], fill='lightgray', width=1)
        for y in range(0, height, 20):
            draw.line([0, y, width, y], fill='lightgray', width=1)
        
        # Rand-Markierungen
        draw.rectangle([0, 0, width-1, height-1], outline='black', width=3)
        
        # Test-Nummer prominent anzeigen
        draw.text((10, 10), f"TEST #{test_number}", fill='black')
        draw.text((10, 30), f"Pattern: {pattern_type}", fill='black')
        
        # Links-Markierung (zum Erkennen von Rechts-Drift)
        draw.rectangle([5, 50, 25, 70], fill='black')
        draw.text((30, 55), "LEFT", fill='black')
        
        # Rechts-Markierung
        draw.rectangle([width-25, 50, width-5, 70], fill='black')
        draw.text((width-55, 55), "RIGHT", fill='black')
        
        # Zentral-Markierung
        center_x = width // 2
        draw.line([center_x, 0, center_x, height], fill='red', width=2)
        draw.text((center_x-20, height//2), "CENTER", fill='red')
        
    elif pattern_type == "alignment":
        # Spezielle Alignment-Tests
        draw.rectangle([0, 0, width-1, height-1], outline='black', width=2)
        
        # Vertikale Linien für Alignment-Check
        for x in [10, 50, 100, 150, 190]:
            draw.line([x, 10, x, height-10], fill='black', width=2)
            draw.text((x-5, height-25), str(x), fill='black')
        
        # Test-Info
        draw.text((width//2-30, 20), f"ALIGN #{test_number}", fill='black')
    
    # Als PNG-Bytes speichern
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()

def test_anti_drift():
    """Testet Anti-Drift-Mechanismus mit mehreren schnellen Drucken"""
    print("🎯 Anti-Drift-Test für Phomemo M110")
    print("=" * 60)
    print("📋 Dieser Test druckt mehrere Bilder schnell hintereinander")
    print("📋 um zu prüfen, ob sich der Druck nach rechts verschiebt.")
    print("=" * 60)
    
    test_count = 5
    delay_between = 0.1  # Sehr kurze Pause = Stress-Test
    
    print(f"🧪 Test-Parameter:")
    print(f"   • Anzahl Tests: {test_count}")
    print(f"   • Pause zwischen Drucken: {delay_between}s")
    print(f"   • Server: {BASE_URL}")
    print()
    
    try:
        # Test 1: Schnelle Aufeinanderfolge (kritisch für Drift)
        print("🔥 STRESS-TEST: Schnelle Aufeinanderfolge...")
        for i in range(1, test_count + 1):
            print(f"   📸 Drucke Test-Bild #{i}/{test_count}...")
            
            # Grid-Pattern für Positions-Erkennung
            test_image = create_position_test_image(i, "grid")
            
            files = {'data': (f'drift_test_{i}.png', test_image, 'image/png')}
            data = {
                'use_queue': 'false',  # Sofortiger Druck für Timing-Test
                'fit_to_label': 'true',
                'maintain_aspect': 'true',
                'dither': 'true'
            }
            
            start_time = time.time()
            response = requests.post(f"{BASE_URL}/api/print-image", files=files, data=data)
            end_time = time.time()
            
            result = response.json()
            
            if result['success']:
                print(f"   ✅ #{i} erfolgreich ({end_time-start_time:.2f}s)")
                if 'message' in result:
                    print(f"      💬 {result['message']}")
            else:
                print(f"   ❌ #{i} fehlgeschlagen: {result['error']}")
                break
            
            # Kurze Pause (kritisch für Drift-Test)
            if i < test_count:
                time.sleep(delay_between)
        
        print("\n" + "="*60)
        print("🔍 ERGEBNIS-ANALYSE:")
        print("📋 Schaue die gedruckten Labels an:")
        print("   ✅ ERFOLGREICH: Alle Labels sind links-bündig ausgerichtet")
        print("   ❌ DRIFT-PROBLEM: Labels wandern nach rechts")
        print()
        print("🎯 Achte auf:")
        print("   • LEFT/RIGHT-Markierungen sind an derselben Position")
        print("   • CENTER-Linie (rot) ist bei allen Labels mittig")
        print("   • Schwarzer Rand ist überall gleich dick")
        print("   • Grid-Linien sind gleichmäßig verteilt")
        
        # Test 2: Mit längeren Pausen (sollte immer funktionieren)
        print(f"\n🐌 KONTROLL-TEST: Mit längeren Pausen (2s)...")
        for i in range(1, 4):  # Nur 3 Tests
            print(f"   📸 Kontroll-Druck #{i}/3...")
            
            test_image = create_position_test_image(100 + i, "alignment")
            
            files = {'data': (f'control_test_{i}.png', test_image, 'image/png')}
            data = {'use_queue': 'false', 'fit_to_label': 'true'}
            
            response = requests.post(f"{BASE_URL}/api/print-image", files=files, data=data)
            result = response.json()
            
            status = "✅" if result['success'] else "❌"
            print(f"   {status} Kontroll-Test #{i}")
            
            # Lange Pause
            if i < 3:
                time.sleep(2.0)
        
        print("\n" + "="*60)
        print("📊 VERGLEICH:")
        print("   Stress-Test vs. Kontroll-Test")
        print("   → Beide sollten dieselbe Positionierung haben")
        print("   → Falls Unterschied = Anti-Drift-Mechanismus nötig")
        
    except requests.exceptions.ConnectionError:
        print("❌ Server nicht erreichbar")
        print("   Starte Server mit: python3 main.py")
    except Exception as e:
        print(f"❌ Test-Fehler: {e}")

def continuous_drift_test():
    """Langer Test über Zeit"""
    print("\n🕒 KONTINUIERLICHER DRIFT-TEST")
    print("   Druckt alle 3 Sekunden ein Test-Label (10x)")
    print("   Überwache die Position über Zeit...")
    
    for i in range(1, 11):
        print(f"   ⏰ Langzeit-Test {i}/10...")
        
        test_image = create_position_test_image(200 + i, "grid")
        files = {'data': (f'longterm_{i}.png', test_image, 'image/png')}
        
        try:
            response = requests.post(f"{BASE_URL}/api/print-image", 
                                   files=files, 
                                   data={'use_queue': 'false'})
            result = response.json()
            
            status = "✅" if result['success'] else "❌"
            print(f"      {status} Langzeit #{i}")
            
        except Exception as e:
            print(f"      ❌ Fehler: {e}")
        
        # Normale Pause zwischen Druckaufträgen
        if i < 10:
            time.sleep(3.0)

if __name__ == "__main__":
    test_anti_drift()
    
    # Optional: Kontinuierlicher Test
    answer = input("\n❓ Kontinuierlichen Langzeit-Test starten? (y/N): ")
    if answer.lower() == 'y':
        continuous_drift_test()
    
    print("\n🎉 Anti-Drift-Tests abgeschlossen!")
    print("📋 Prüfe die gedruckten Labels visuell auf Position-Konstanz.")
