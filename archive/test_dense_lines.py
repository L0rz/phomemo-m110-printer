#!/usr/bin/env python3
"""
Dense Horizontal Line Test
Testet speziell das Problem mit vollen horizontalen Zeilen
"""

import requests
import time
from PIL import Image, ImageDraw, ImageFont
import io

BASE_URL = "http://localhost:8080"

def create_density_test_images():
    """Erstellt Bilder mit verschiedenen horizontalen Dichte-Leveln"""
    tests = {}
    
    # Test 1: Spärlich (sollte funktionieren)
    width, height = 200, 100
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    draw.text((20, 20), "SPARSE", fill='black')
    draw.text((20, 40), "I I I I", fill='black')  # Wenig pro Zeile
    draw.text((20, 60), "O O O O", fill='black')
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    tests['sparse'] = buffer.getvalue()
    
    # Test 2: Mittel-dicht
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    draw.text((20, 20), "MEDIUM DENSITY", fill='black')
    draw.text((20, 40), "ABCDEFGHIJKLM", fill='black')  # Mittlere Dichte
    draw.text((20, 60), "1234567890123", fill='black')
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    tests['medium'] = buffer.getvalue()
    
    # Test 3: SEHR DICHT (das problematische A-Z)
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    draw.text((10, 20), "DENSE TEST", fill='black')
    draw.text((10, 40), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", fill='black')  # VOLLE Zeile!
    draw.text((10, 60), "0123456789012345678901234567890", fill='black')  # VOLLE Zeile!
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    tests['dense'] = buffer.getvalue()
    
    # Test 4: ULTRA-DICHT (schwarze Blöcke)
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    # Viele schwarze Pixel in horizontalen Linien
    for y in range(20, 80, 4):
        draw.rectangle([10, y, width-10, y+2], fill='black')
    draw.text((20, 10), "ULTRA-DENSE", fill='black')
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    tests['ultra_dense'] = buffer.getvalue()
    
    return tests

def test_density_levels():
    """Testet verschiedene Dichte-Level"""
    print("📊 DENSE HORIZONTAL LINE TEST")
    print("=" * 60)
    print("🎯 Testet das Problem mit vollen horizontalen Zeilen")
    print("📋 Hypothese: Dichte Zeilen verursachen Drift, spärliche nicht")
    print("=" * 60)
    
    density_images = create_density_test_images()
    
    for density_name, image_data in density_images.items():
        print(f"\n📸 Teste {density_name.upper()} Dichte ({len(image_data)} bytes)...")
        
        try:
            files = {'data': (f'{density_name}_test.png', image_data, 'image/png')}
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
                print(f"   ✅ {density_name.upper()} erfolgreich ({end_time-start_time:.2f}s)")
                print(f"   📊 Format: {result.get('format', '?')}, Größe: {result.get('size_bytes', '?')} bytes")
                
                # Spezifische Erwartungen
                if density_name == 'sparse':
                    print("   📋 Erwartung: Perfekte Position (wenig Daten)")
                elif density_name == 'medium':
                    print("   📋 Erwartung: Gute Position (mittlere Daten)")
                elif density_name == 'dense':
                    print("   📋 Erwartung: KRITISCH - war vorher problematisch!")
                elif density_name == 'ultra_dense':
                    print("   📋 Erwartung: SEHR KRITISCH - viele schwarze Pixel!")
                    
            else:
                print(f"   ❌ {density_name.upper()} fehlgeschlagen: {result['error']}")
                
            # Pause zwischen Dichte-Tests
            if density_name != 'ultra_dense':  # Nicht nach dem letzten
                print(f"   ⏱️ Pause vor nächstem Dichte-Test...")
                time.sleep(3.0)  # Längere Pause für Drucker-Stabilität
                
        except Exception as e:
            print(f"   ❌ {density_name.upper()} Fehler: {e}")

def test_alphabet_line_specific():
    """Testet speziell die problematische A-Z Zeile"""
    print("\n🔤 ALPHABET-ZEILEN-SPEZIFISCHER TEST")
    print("=" * 50)
    
    alphabet_tests = [
        # Test 1: Kurze Buchstaben-Sequenzen
        "ABC DEF GHI",
        
        # Test 2: Mittlere Sequenz
        "ABCDEFGHIJKLM",
        
        # Test 3: Die problematische volle A-Z Zeile
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        
        # Test 4: Noch länger
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    ]
    
    for i, alphabet_text in enumerate(alphabet_tests, 1):
        print(f"\n   {i}. Alphabet-Test: '{alphabet_text}'")
        
        try:
            response = requests.post(f"{BASE_URL}/api/print-text", data={
                'text': f'ALPHABET-TEST {i}\n\n{alphabet_text}\n\nPosition OK?',
                'font_size': '16',
                'alignment': 'left',
                'immediate': 'true'
            })
            result = response.json()
            
            status = "✅" if result['success'] else "❌"
            print(f"      {status} Alphabet-Test {i}")
            
            if result['success']:
                if i == 3:  # Die problematische A-Z Zeile
                    print("      🎯 KRITISCH: War vorher problematisch!")
                    print("      📋 Prüfe: Ist die A-Z Zeile jetzt korrekt positioniert?")
                else:
                    print("      📋 Prüfe: Position im Vergleich zur A-Z Zeile")
            else:
                print(f"      💬 Fehler: {result['error']}")
            
            # Pause zwischen Alphabet-Tests
            time.sleep(2.0)
            
        except Exception as e:
            print(f"      ❌ Alphabet-Test {i} Fehler: {e}")

def test_horizontal_density_patterns():
    """Testet verschiedene horizontale Dichte-Muster"""
    print("\n📏 HORIZONTALE DICHTE-MUSTER-TEST")
    print("=" * 50)
    
    # Erstelle Bilder mit verschiedenen horizontalen Mustern
    patterns = {
        'dots': '• • • • • • • • • • • • • • • •',
        'dashes': '- - - - - - - - - - - - - - - -',
        'full_line': '████████████████████████████',
        'mixed': 'ABC123XYZ789DEF456GHI012JKL345'
    }
    
    for pattern_name, pattern_text in patterns.items():
        print(f"\n   📊 Pattern: {pattern_name.upper()}")
        
        try:
            response = requests.post(f"{BASE_URL}/api/print-text", data={
                'text': f'PATTERN: {pattern_name.upper()}\n\n{pattern_text}\n\nDensity test complete',
                'font_size': '14',
                'alignment': 'left',
                'immediate': 'true'
            })
            result = response.json()
            
            status = "✅" if result['success'] else "❌"
            print(f"      {status} Pattern {pattern_name}")
            
            if result['success']:
                if pattern_name == 'full_line':
                    print("      🎯 KRITISCH: Vollste horizontale Linie!")
                print("      📋 Prüfe: Dichte-Abhängigkeit der Position")
            else:
                print(f"      💬 Fehler: {result['error']}")
            
            time.sleep(2.0)
            
        except Exception as e:
            print(f"      ❌ Pattern {pattern_name} Fehler: {e}")

def analyze_density_results():
    """Analysiert die Dichte-Test-Ergebnisse"""
    print("\n" + "="*60)
    print("📊 DICHTE-ANALYSE-ERGEBNISSE")
    print()
    print("🔍 Vergleiche die verschiedenen Dichte-Tests:")
    print("   • SPARSE → Wenig Daten pro Zeile")
    print("   • MEDIUM → Mittlere Daten pro Zeile")
    print("   • DENSE → Volle A-Z Zeile (war problematisch)")
    print("   • ULTRA-DENSE → Maximale schwarze Pixel")
    print()
    print("❓ Welche Dichte-Level zeigen noch Probleme?")
    print("   A) Alle Dichte-Level perfekt → Problem gelöst!")
    print("   B) Nur DENSE und ULTRA-DENSE problematisch")
    print("   C) Alle ab MEDIUM problematisch")
    print("   D) Immer noch alle problematisch")
    print()
    
    answer = input("Eingabe (A/B/C/D): ").upper().strip()
    
    if answer == 'A':
        print("\n🎉 DICHTE-PROBLEM GELÖST!")
        print("✅ Dense-Data-Safe Chunks funktionieren perfekt!")
        print("🔧 Ultra-kleine Chunks + Extra-Pausen lösen das Problem")
        
    elif answer == 'B':
        print("\n🔧 TEILWEISE GELÖST!")
        print("💡 Sehr dichte Bereiche brauchen noch kleinere Chunks")
        suggest_ultra_dense_fix()
        
    elif answer == 'C':
        print("\n⚠️ CHUNK-GRÖSSE NOCH ZU GROSS")
        print("💡 Chunk-Größe weiter reduzieren nötig")
        suggest_smaller_chunks()
        
    elif answer == 'D':
        print("\n❌ GRUNDPROBLEM WEITERHIN VORHANDEN")
        print("💡 Hardware-Level-Problem möglich")
        suggest_hardware_level_fix()
        
    else:
        print("\n⚠️ Weitere Analyse empfohlen")

def suggest_ultra_dense_fix():
    print("🛠️ ULTRA-DICHTE-REPARATUR-VORSCHLÄGE:")
    print("1. Chunk-Größe auf 64 Bytes reduzieren")
    print("2. Noch längere Pausen zwischen Chunks")
    print("3. Adaptive Chunk-Größe basierend auf Dichte")

def suggest_smaller_chunks():
    print("🛠️ KLEINERE-CHUNKS-VORSCHLÄGE:")
    print("1. Chunk-Größe auf 32-64 Bytes")
    print("2. Doppelte Pausen zwischen Chunks")
    print("3. Mehr Retry-Versuche pro Chunk")

def suggest_hardware_level_fix():
    print("🛠️ HARDWARE-LEVEL-VORSCHLÄGE:")
    print("1. Übertragungsgeschwindigkeit reduzieren")
    print("2. Bluetooth-Parameter anpassen")
    print("3. Hardware-Reset des Druckers")

if __name__ == "__main__":
    print("📊 DENSE HORIZONTAL LINE TESTER")
    print("🎯 Speziell für das Problem mit vollen horizontalen Zeilen")
    print()
    
    test_density_levels()
    test_alphabet_line_specific()
    test_horizontal_density_patterns()
    analyze_density_results()
    
    print("\n🎉 Dense Line Test abgeschlossen!")
    print("📋 Die Dichte-optimierten Chunks sollten das Problem lösen.")
