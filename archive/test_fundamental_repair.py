#!/usr/bin/env python3
"""
Fundamental Repair Test
Testet die fundamentale Drift-Reparatur für alle Drucktypen
"""

import requests
import time
from PIL import Image, ImageDraw
import io

BASE_URL = "http://localhost:8080"

def create_precision_test_image() -> bytes:
    """Erstellt hochpräzises Test-Bild für Drift-Erkennung"""
    width, height = 200, 120
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # ULTRA-PRÄZISE Position-Markierungen
    # Linker Rand - Pixel-genaue Markierung
    for i in range(5):
        draw.line([i, 0, i, height], fill='black', width=1)
    draw.text((8, 5), "LEFT-EDGE", fill='black')
    
    # Rechter Rand - Pixel-genaue Markierung  
    for i in range(width-5, width):
        draw.line([i, 0, i, height], fill='black', width=1)
    draw.text((width-55, 5), "RIGHT-EDGE", fill='black')
    
    # Zentral-Referenz-Linie
    center_x = width // 2
    draw.line([center_x, 0, center_x, height], fill='red', width=2)
    draw.text((center_x-20, height//2), "CENTER", fill='red')
    
    # Horizontale Referenz-Linien (für vertikale Drift-Erkennung)
    for y in [20, 40, 60, 80, 100]:
        draw.line([10, y, width-10, y], fill='gray', width=1)
        draw.text((5, y-5), str(y), fill='gray')
    
    # Test-Pattern für systematische Drift-Erkennung
    draw.text((20, 25), "FUNDAMENTAL REPAIR TEST", fill='black')
    draw.text((20, 45), "Pattern: No Drift Expected", fill='black')
    draw.text((20, 65), "All elements aligned?", fill='black')
    draw.text((20, 85), "Check: L-CENTER-R same?", fill='black')
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()

def test_fundamental_repair():
    """Testet die fundamentale Drift-Reparatur"""
    print("🔧 FUNDAMENTAL DRIFT REPAIR TEST")
    print("=" * 60)
    print("🎯 Testet die komplette Drucker-Reset-Reparatur")
    print("📋 Erwartet: ALLE Tests ohne Drift/Verschiebung")
    print("=" * 60)
    
    # Test 1: Text-Test (war vorher: Buchstaben-Reihenfolge verschoben)
    print("\n1️⃣ TEXT-REPAIR-TEST")
    test_text_repair()
    
    # Test 2: Debug-Bild-Test (war vorher: Unterer Teil doppelt)
    print("\n2️⃣ DEBUG-BILD-REPAIR-TEST")  
    test_debug_image_repair()
    
    # Test 3: Echtes Bild-Test (war vorher: Völlig verschoben)
    print("\n3️⃣ ECHTES-BILD-REPAIR-TEST")
    test_real_image_repair()
    
    # Test 4: Sequenz-Test (mehrere hintereinander)
    print("\n4️⃣ SEQUENZ-REPAIR-TEST")
    test_sequence_repair()

def test_text_repair():
    """Test 1: Text-Repair (Buchstaben-Reihenfolge Problem)"""
    try:
        print("   📝 Text-Repair: Buchstaben-Reihenfolge sollte korrekt sein...")
        
        response = requests.post(f"{BASE_URL}/api/print-text", data={
            'text': '''TEXT-REPAIR-TEST

Links: ← EDGE
ABCDEFGHIJKLMNOPQRSTUVWXYZ
1234567890
Rechts: EDGE →

Fundamental Repair: SUCCESS?''',
            'font_size': '16',
            'alignment': 'left',
            'immediate': 'true'
        })
        result = response.json()
        
        if result['success']:
            print("   ✅ Text-Repair erfolgreich gedruckt")
            print("   📋 Prüfe: Ist ABCDEFG...XYZ in korrekter Reihenfolge?")
            print("   📋 Prüfe: Sind Links/Rechts korrekt positioniert?")
        else:
            print(f"   ❌ Text-Repair fehlgeschlagen: {result['error']}")
            
    except Exception as e:
        print(f"   ❌ Text-Repair Fehler: {e}")

def test_debug_image_repair():
    """Test 2: Debug-Bild-Repair (Unterer Teil doppelt Problem)"""
    try:
        print("   🖼️ Debug-Bild-Repair: Kein doppelter unterer Teil...")
        
        precision_image = create_precision_test_image()
        
        files = {'data': ('repair_test.png', precision_image, 'image/png')}
        data = {
            'use_queue': 'false',
            'fit_to_label': 'true',
            'maintain_aspect': 'true',
            'dither': 'true'
        }
        
        response = requests.post(f"{BASE_URL}/api/print-image", files=files, data=data)
        result = response.json()
        
        if result['success']:
            print("   ✅ Debug-Bild-Repair erfolgreich gedruckt")
            print("   📋 Prüfe: Ist der untere Teil NICHT doppelt?")
            print("   📋 Prüfe: Sind alle Linien korrekt positioniert?")
            print("   📋 Prüfe: LEFT-CENTER-RIGHT in einer Linie?")
        else:
            print(f"   ❌ Debug-Bild-Repair fehlgeschlagen: {result['error']}")
            
    except Exception as e:
        print(f"   ❌ Debug-Bild-Repair Fehler: {e}")

def test_real_image_repair():
    """Test 3: Echtes Bild-Repair (Völlige Verschiebung Problem)"""
    print("   📷 Echtes-Bild-Repair: Normale Position erwartet...")
    
    # Suche nach verfügbaren Bildern
    import os
    image_files = []
    for file in os.listdir('.'):
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            image_files.append(file)
    
    if not image_files:
        print("   ⚠️ Keine Bild-Dateien gefunden - verwende Precision-Test-Bild")
        # Verwende Precision-Test-Bild als Fallback
        test_image = create_precision_test_image()
        files = {'data': ('fallback.png', test_image, 'image/png')}
    else:
        print(f"   📁 Verwende echtes Bild: {image_files[0]}")
        try:
            with open(image_files[0], 'rb') as f:
                test_image = f.read()
            files = {'data': (image_files[0], test_image)}
        except Exception as e:
            print(f"   ⚠️ Bild-Lade-Fehler: {e} - verwende Fallback")
            test_image = create_precision_test_image()
            files = {'data': ('fallback.png', test_image, 'image/png')}
    
    try:
        data = {
            'use_queue': 'false',
            'fit_to_label': 'true',
            'maintain_aspect': 'true',
            'dither': 'true'
        }
        
        response = requests.post(f"{BASE_URL}/api/print-image", files=files, data=data)
        result = response.json()
        
        if result['success']:
            print("   ✅ Echtes-Bild-Repair erfolgreich gedruckt")
            print("   📋 Prüfe: Ist das Bild NICHT völlig verschoben?")
            print("   📋 Prüfe: Hat das Bild normale Position wie Text?")
        else:
            print(f"   ❌ Echtes-Bild-Repair fehlgeschlagen: {result['error']}")
            
    except Exception as e:
        print(f"   ❌ Echtes-Bild-Repair Fehler: {e}")

def test_sequence_repair():
    """Test 4: Sequenz-Repair (mehrere Drucke hintereinander)"""
    print("   🔄 Sequenz-Repair: 3 aufeinanderfolgende Drucke...")
    
    sequence_tests = [
        ("Text", "print-text", {'text': 'SEQ-1: Text normal?', 'font_size': '16', 'immediate': 'true'}),
        ("Bild", "print-image", None),  # Wird unten definiert
        ("Text", "print-text", {'text': 'SEQ-3: Noch normal?', 'font_size': '16', 'immediate': 'true'})
    ]
    
    for i, (test_type, endpoint, data) in enumerate(sequence_tests, 1):
        print(f"      {i}. Sequenz-{test_type}...")
        
        try:
            if test_type == "Bild":
                # Kleines Test-Bild für Sequenz
                small_img = Image.new('RGB', (100, 60), 'white')
                draw = ImageDraw.Draw(small_img)
                draw.rectangle([0, 0, 99, 59], outline='black', width=2)
                draw.text((20, 25), f"SEQ-{i}", fill='black')
                
                buffer = io.BytesIO()
                small_img.save(buffer, format='PNG')
                
                files = {'data': (f'seq_{i}.png', buffer.getvalue(), 'image/png')}
                data = {'use_queue': 'false', 'fit_to_label': 'true'}
                response = requests.post(f"{BASE_URL}/api/{endpoint}", files=files, data=data)
            else:
                response = requests.post(f"{BASE_URL}/api/{endpoint}", data=data)
            
            result = response.json()
            status = "✅" if result['success'] else "❌"
            print(f"         {status} Sequenz-{test_type} #{i}")
            
            # Kurze Pause zwischen Sequenz-Tests
            if i < len(sequence_tests):
                time.sleep(1.0)
                
        except Exception as e:
            print(f"         ❌ Sequenz-{test_type} #{i} Fehler: {e}")

def analyze_repair_results():
    """Analysiert die Repair-Ergebnisse"""
    print("\n" + "="*60)
    print("📊 FUNDAMENTAL REPAIR ERGEBNIS-ANALYSE")
    print("📋 Vergleiche die 4 Test-Drucke mit den ursprünglichen Problemen:")
    print()
    
    print("🔍 VORHER vs. NACHHER:")
    print("   1. Text-Test:")
    print("      VORHER: ❌ Buchstaben-Reihenfolge A-Z verschoben")
    print("      NACHHER: ❓ ABCDEFG...XYZ in korrekter Reihenfolge?")
    print()
    print("   2. Debug-Bild-Test:")
    print("      VORHER: ❌ Unterer Teil zweimal gedruckt")
    print("      NACHHER: ❓ Kein doppelter unterer Teil?")
    print()
    print("   3. Echtes-Bild-Test:")
    print("      VORHER: ❌ Völlig verschoben")
    print("      NACHHER: ❓ Normale Position?")
    print()
    print("   4. Sequenz-Test:")
    print("      VORHER: ❌ Drift akkumuliert sich")
    print("      NACHHER: ❓ Alle 3 Tests gleiche Position?")
    print()
    
    answer = input("❓ Sind ALLE 4 Tests jetzt korrekt? (y/n): ").lower().strip()
    
    if answer == 'y':
        print("\n🎉 FUNDAMENTAL REPAIR ERFOLGREICH!")
        print("✅ Drift-Problem vollständig behoben")
        print("🔧 Die komplette Drucker-Reset-Reparatur funktioniert")
    else:
        print("\n⚠️ FUNDAMENTAL REPAIR UNVOLLSTÄNDIG")
        print("🔧 Weitere Hardware-Level-Diagnose nötig")
        print("💡 Mögliche nächste Schritte:")
        print("   • Hardware-Reset des Druckers (Aus/Ein)")
        print("   • Bluetooth-Verbindung neu aufbauen")
        print("   • Drucker-Firmware-Problem")

if __name__ == "__main__":
    print("🔧 FUNDAMENTAL DRIFT REPAIR TESTER")
    print("🎯 Testet die komplette Drucker-Reset-Reparatur")
    print()
    
    test_fundamental_repair()
    analyze_repair_results()
    
    print("\n🎉 Fundamental Repair Test abgeschlossen!")
    print("📋 Die fundamentale Reparatur sollte ALLE Drift-Probleme beheben.")
