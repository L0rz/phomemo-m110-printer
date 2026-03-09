#!/usr/bin/env python3
"""
Drift Debug Tool
Analysiert genau, wo und wie der Drift beim Bild-Druck entsteht
"""

import requests
import time
from PIL import Image, ImageDraw
import io
import os

BASE_URL = "http://localhost:8080"

def create_drift_debug_image(test_id: str) -> bytes:
    """Erstellt spezielles Debug-Bild mit Drift-Erkennungs-Pattern"""
    width, height = 200, 150
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Sehr präzise Position-Markierungen
    # Links-Rand-Markierung (Pixel-genau)
    for i in range(0, 10):
        draw.line([i, 0, i, height], fill='black', width=1)
    draw.text((12, 10), "LEFT EDGE", fill='black')
    
    # Rechts-Rand-Markierung
    for i in range(width-10, width):
        draw.line([i, 0, i, height], fill='black', width=1)
    draw.text((width-70, 10), "RIGHT EDGE", fill='black')
    
    # Zentral-Markierungen in Abständen
    for x in [25, 50, 75, 100, 125, 150, 175]:
        draw.line([x, 30, x, 120], fill='gray', width=1)
        draw.text((x-3, 125), str(x), fill='gray')
    
    # Test-ID
    draw.text((10, 50), f"DEBUG: {test_id}", fill='black')
    
    # Drift-Mess-Linien (horizontal)
    for y in [40, 60, 80, 100]:
        draw.line([0, y, width, y], fill='lightgray', width=1)
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()

def step_by_step_debug():
    """Schritt-für-Schritt Debug-Analyse"""
    print("🔍 STEP-BY-STEP DRIFT DEBUG")
    print("=" * 60)
    print("📋 Analysiert jeden Schritt des Bild-Druck-Prozesses")
    print("=" * 60)
    
    # Schritt 1: Basis-Test ohne Bild
    print("\n1️⃣ BASIS-TEST: Text ohne Bilder")
    test_text_baseline()
    
    # Schritt 2: Sehr einfaches Bild
    print("\n2️⃣ EINFACH-TEST: Minimales Debug-Bild")
    test_simple_debug_image()
    
    # Schritt 3: Echtes Bild
    print("\n3️⃣ REAL-TEST: Echtes Bild-Upload")
    test_real_image_upload()
    
    # Schritt 4: Vergleich der Ergebnisse
    print("\n4️⃣ ERGEBNIS-ANALYSE")
    analyze_results()

def test_text_baseline():
    """Test 1: Reiner Text als Baseline"""
    try:
        print("   📝 Drucke Text-Baseline...")
        response = requests.post(f"{BASE_URL}/api/print-text", data={
            'text': '''BASELINE-TEST

← LINKS    MITTE    RECHTS →
|          |          |
10        20        30

ABCDEFGHIJKLMNOPQRSTUVWXYZ
1234567890123456789012345''',
            'font_size': '16',
            'alignment': 'left',
            'immediate': 'true'
        })
        result = response.json()
        
        if result['success']:
            print("   ✅ Text-Baseline erfolgreich")
            print("   📋 Prüfe: Ist die Position korrekt?")
        else:
            print(f"   ❌ Text-Baseline fehlgeschlagen: {result['error']}")
            
    except Exception as e:
        print(f"   ❌ Text-Baseline Fehler: {e}")

def test_simple_debug_image():
    """Test 2: Sehr einfaches Debug-Bild"""
    try:
        print("   🖼️ Drucke einfaches Debug-Bild...")
        debug_image = create_drift_debug_image("SIMPLE")
        
        files = {'data': ('debug_simple.png', debug_image, 'image/png')}
        data = {
            'use_queue': 'false',
            'fit_to_label': 'true',
            'maintain_aspect': 'true',
            'dither': 'true'
        }
        
        response = requests.post(f"{BASE_URL}/api/print-image", files=files, data=data)
        result = response.json()
        
        if result['success']:
            print("   ✅ Debug-Bild erfolgreich")
            print("   📋 Prüfe: Stimmen die Positions-Markierungen?")
            print("   📋 Vergleiche mit Text-Baseline!")
        else:
            print(f"   ❌ Debug-Bild fehlgeschlagen: {result['error']}")
            
    except Exception as e:
        print(f"   ❌ Debug-Bild Fehler: {e}")

def test_real_image_upload():
    """Test 3: Echtes Bild-Upload"""
    try:
        # Suche nach Bild-Dateien
        image_files = []
        for file in os.listdir('.'):
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                image_files.append(file)
        
        if not image_files:
            print("   ⚠️ Keine Bild-Dateien gefunden - überspringe Real-Test")
            return
        
        test_image = image_files[0]
        print(f"   📷 Drucke echtes Bild: {test_image}")
        
        with open(test_image, 'rb') as f:
            image_data = f.read()
        
        files = {'data': (test_image, image_data)}
        data = {
            'use_queue': 'false',
            'fit_to_label': 'true',
            'maintain_aspect': 'true',
            'dither': 'true'
        }
        
        response = requests.post(f"{BASE_URL}/api/print-image", files=files, data=data)
        result = response.json()
        
        if result['success']:
            print("   ✅ Echtes Bild erfolgreich")
            print(f"   📊 Größe: {result.get('size_bytes', '?')} bytes")
            print("   📋 Prüfe: Hat dieses Bild den extremen Drift?")
        else:
            print(f"   ❌ Echtes Bild fehlgeschlagen: {result['error']}")
            
    except Exception as e:
        print(f"   ❌ Real-Bild Fehler: {e}")

def analyze_results():
    """Analysiert die Debug-Ergebnisse"""
    print("📊 ERGEBNIS-ANALYSE:")
    print()
    print("🔍 Visueller Vergleich der 3 Drucke:")
    print("   1. Text-Baseline    → Position OK?")
    print("   2. Debug-Bild       → Position OK?") 
    print("   3. Echtes Bild      → Position OK?")
    print()
    print("❓ Welcher Test zeigt Drift?")
    print("   A) Alle zeigen Drift → Problem im Basis-System")
    print("   B) Nur Bilder zeigen Drift → Bild-spezifisches Problem")
    print("   C) Nur echtes Bild zeigt Drift → Format-spezifisches Problem")
    print("   D) Keiner zeigt Drift → Problem gelöst!")
    print()
    
    answer = input("Eingabe (A/B/C/D): ").upper().strip()
    
    if answer == 'A':
        print("\n🔧 DIAGNOSE: BASIS-SYSTEM-PROBLEM")
        print("💡 Lösungsansatz: Grundlegende Drucker-Kommunikation überprüfen")
        suggest_basic_fixes()
        
    elif answer == 'B':
        print("\n🔧 DIAGNOSE: BILD-VERARBEITUNGS-PROBLEM")
        print("💡 Lösungsansatz: Bild-Pipeline analysieren")
        suggest_image_fixes()
        
    elif answer == 'C':
        print("\n🔧 DIAGNOSE: FORMAT-SPEZIFISCHES PROBLEM")
        print("💡 Lösungsansatz: Bild-Format-Verarbeitung optimieren")
        suggest_format_fixes()
        
    elif answer == 'D':
        print("\n🎉 DIAGNOSE: PROBLEM GELÖST!")
        print("✅ Enhanced Anti-Drift funktioniert erfolgreich")
        
    else:
        print("\n⚠️ Unklare Diagnose - manuelle Analyse empfohlen")

def suggest_basic_fixes():
    """Vorschläge für Basis-System-Probleme"""
    print("\n🛠️ BASIS-SYSTEM-REPARATUR-VORSCHLÄGE:")
    print("1. Drucker-Verbindung zurücksetzen")
    print("2. Niedrigere Übertragungsgeschwindigkeit")
    print("3. Längere Pausen zwischen allen Drucken")
    print("4. Hardware-Reset des Druckers")

def suggest_image_fixes():
    """Vorschläge für Bild-Verarbeitungs-Probleme"""
    print("\n🛠️ BILD-VERARBEITUNGS-REPARATUR-VORSCHLÄGE:")
    print("1. Bild-Größe vor Verarbeitung reduzieren")
    print("2. Andere Dithering-Einstellungen")
    print("3. Chunk-Größe bei Bitmap-Übertragung reduzieren")
    print("4. Mehr Pausen in der Bild-Pipeline")

def suggest_format_fixes():
    """Vorschläge für Format-spezifische Probleme"""
    print("\n🛠️ FORMAT-SPEZIFISCHE-REPARATUR-VORSCHLÄGE:")
    print("1. Bilder vor Upload in PNG konvertieren")
    print("2. Maximale Bild-Auflösung begrenzen")
    print("3. Verschiedene Komprimierungs-Einstellungen")
    print("4. Format-spezifische Verarbeitungs-Pipeline")

def emergency_stabilization():
    """Notfall-Stabilisierung des Druckers"""
    print("\n🚨 NOTFALL-STABILISIERUNG")
    print("   Führt aggressive Drucker-Reset-Sequenz durch...")
    
    try:
        # Mehrfache Stabilisierung
        for i in range(3):
            print(f"   🔄 Reset-Zyklus {i+1}/3...")
            
            response = requests.post(f"{BASE_URL}/api/test-offsets", data={
                'pattern': 'full_test'
            })
            
            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    print(f"      ✅ Reset {i+1} erfolgreich")
                else:
                    print(f"      ❌ Reset {i+1} fehlgeschlagen")
            
            time.sleep(3.0)  # Lange Pause zwischen Resets
            
        print("   ✅ Notfall-Stabilisierung abgeschlossen")
        print("   📋 Teste jetzt erneut mit einem Bild")
        
    except Exception as e:
        print(f"   ❌ Notfall-Stabilisierung fehlgeschlagen: {e}")

if __name__ == "__main__":
    print("🔍 DRIFT DEBUG TOOL")
    print("🎯 Findet die genaue Ursache des Bild-Drift-Problems")
    print()
    
    step_by_step_debug()
    
    # Optional: Notfall-Stabilisierung
    answer = input("\n❓ Notfall-Stabilisierung versuchen? (y/N): ")
    if answer.lower() == 'y':
        emergency_stabilization()
    
    print("\n🎉 Drift-Debug abgeschlossen!")
    print("📋 Die Analyse sollte die genaue Drift-Ursache aufzeigen.")
