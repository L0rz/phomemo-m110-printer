#!/usr/bin/env python3
"""
Optimierter Anti-Drift-Test
Basierend auf den erfolgreichen Kontroll-Tests mit 2-Sekunden-Pausen
"""

import requests
import time
from PIL import Image, ImageDraw
import io

BASE_URL = "http://localhost:8080"

def create_validation_image(test_number: int) -> bytes:
    """Erstellt Validierungs-Bild ähnlich den erfolgreichen Kontroll-Tests"""
    width, height = 180, 120
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Rahmen für Position-Check
    draw.rectangle([0, 0, width-1, height-1], outline='black', width=2)
    
    # Test-Nummer prominent
    draw.text((10, 10), f"OPTIMIERT #{test_number}", fill='black')
    
    # Position-Markierungen (wie bei erfolgreichen Tests)
    # Links-Markierung
    draw.rectangle([5, 35, 20, 50], fill='black')
    draw.text((25, 40), "LINKS", fill='black')
    
    # Rechts-Markierung  
    draw.rectangle([width-20, 35, width-5, 50], fill='black')
    draw.text((width-50, 40), "RECHTS", fill='black')
    
    # Zentral-Referenz
    center_x = width // 2
    draw.line([center_x, 20, center_x, 100], fill='red', width=2)
    draw.text((center_x-15, 105), "MITTE", fill='red')
    
    # Alignment-Grid (fein)
    for x in range(20, width-20, 20):
        draw.line([x, 60, x, 70], fill='lightgray', width=1)
    
    # Status
    draw.text((10, 80), "2s Timing-Test", fill='black')
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()

def test_optimized_anti_drift():
    """Testet mit den erfolgreichen 2-Sekunden-Einstellungen"""
    print("🎯 OPTIMIERTER ANTI-DRIFT-TEST")
    print("=" * 60)
    print("📊 Basierend auf erfolgreichen Kontroll-Tests #2 und #3")
    print("⏱️ Verwendet 2-Sekunden-Pause zwischen Drucken")
    print("=" * 60)
    
    test_count = 5
    
    print(f"🧪 Optimierte Test-Parameter:")
    print(f"   • Anzahl Tests: {test_count}")
    print(f"   • Pause zwischen Drucken: 2.0s (wie bei erfolgreichen Tests)")
    print(f"   • Schonende Anti-Drift-Mechanismen")
    print()
    
    successful_tests = 0
    
    try:
        for i in range(1, test_count + 1):
            print(f"📸 Optimierter Test #{i}/{test_count}...")
            
            test_image = create_validation_image(i)
            
            files = {'data': (f'optimized_{i}.png', test_image, 'image/png')}
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
                successful_tests += 1
                print(f"   ✅ Test #{i} erfolgreich ({end_time-start_time:.2f}s)")
                print(f"      📏 {result.get('format', '?')} - {result.get('size_bytes', '?')} bytes")
                
                # Info über Anti-Drift-Timing
                if i == 1:
                    print("      ℹ️ Erstes Bild - Anti-Drift-Timer startet")
                else:
                    print("      ⏱️ Anti-Drift-Pause automatisch angewendet")
                    
            else:
                print(f"   ❌ Test #{i} fehlgeschlagen: {result['error']}")
                break
            
            # Pause zwischen Tests (wird zusätzlich zur automatischen Anti-Drift-Pause angewendet)
            if i < test_count:
                print(f"   ⌛ Warte für Test #{i+1}...")
                time.sleep(0.5)  # Kurze zusätzliche Pause
        
        print("\n" + "="*60)
        print("📊 ERGEBNIS-ZUSAMMENFASSUNG:")
        print(f"✅ Erfolgreiche Tests: {successful_tests}/{test_count}")
        
        if successful_tests == test_count:
            print("🎉 PERFEKT: Alle Tests erfolgreich!")
            print("✅ Anti-Drift-Mechanismus funktioniert optimal")
        elif successful_tests >= test_count - 1:
            print("👍 GUT: Fast alle Tests erfolgreich")
            print("✅ Anti-Drift-Mechanismus weitgehend funktional")
        else:
            print("⚠️ PROBLEM: Weniger als 80% erfolgreiche Tests")
            print("🔧 Anti-Drift-Mechanismus benötigt weitere Anpassung")
        
        print("\n🔍 VISUELLER CHECK:")
        print("📋 Vergleiche alle gedruckten Labels:")
        print("   • LINKS-Markierungen sollten alle an derselben Stelle sein")
        print("   • RECHTS-Markierungen sollten alle an derselben Stelle sein")  
        print("   • MITTE-Linien (rot) sollten alle zentriert sein")
        print("   • Schwarzer Rahmen sollte überall gleich dick sein")
        print("   • Grid-Markierungen sollten gleichmäßig verteilt sein")
        
        print("\n💡 ERWARTUNG:")
        print("   Basierend auf erfolgreichen Kontroll-Tests #2 und #3")
        print("   sollten ALLE 5 Tests die gleiche perfekte Position haben!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Server nicht erreichbar")
        print("   Starte Server mit: python3 main.py")
    except Exception as e:
        print(f"❌ Test-Fehler: {e}")

def quick_position_validation():
    """Schnelle Validierung der aktuellen Position-Einstellungen"""
    print("\n⚡ SCHNELLE POSITION-VALIDIERUNG")
    print("   Druckt 2 identische Labels mit 2s Pause (wie erfolgreiche Tests)")
    
    for i in range(1, 3):
        print(f"   📋 Validierung #{i}/2...")
        
        test_image = create_validation_image(200 + i)
        files = {'data': (f'validation_{i}.png', test_image, 'image/png')}
        
        try:
            response = requests.post(f"{BASE_URL}/api/print-image", 
                                   files=files, 
                                   data={'use_queue': 'false'})
            result = response.json()
            
            status = "✅" if result['success'] else "❌"
            print(f"      {status} Validierung #{i}")
            
            # 2-Sekunden-Pause wie bei erfolgreichen Tests
            if i < 2:
                print("      ⏱️ 2-Sekunden-Pause...")
                time.sleep(2.0)
                
        except Exception as e:
            print(f"      ❌ Validierungs-Fehler {i}: {e}")

if __name__ == "__main__":
    print("🎯 OPTIMIERTER ANTI-DRIFT-TESTER")
    print("🔬 Nutzt Erkenntnisse aus erfolgreichen Kontroll-Tests")
    print()
    
    test_optimized_anti_drift()
    
    # Optional: Schnelle Validierung
    answer = input("\n❓ Zusätzliche Position-Validierung? (y/N): ")
    if answer.lower() == 'y':
        quick_position_validation()
    
    print("\n🎉 Optimierte Anti-Drift-Tests abgeschlossen!")
    print("📈 Die 2-Sekunden-Timing-Strategie sollte konsistente Ergebnisse liefern.")
