#!/usr/bin/env python3
"""
Real Image Drift Test
Testet Anti-Drift speziell mit echten Bildern (nicht generierten Test-Patterns)
"""

import requests
import time
import os

BASE_URL = "http://localhost:8080"

def test_real_image_drift():
    """Testet Anti-Drift mit echten Bild-Uploads"""
    print("📷 REAL IMAGE DRIFT TEST")
    print("=" * 60)
    print("🎯 Testet Anti-Drift-Mechanismus mit echten Bildern")
    print("📋 Reproduziert das Problem: 'extremer Drift bei einem Bild'")
    print("=" * 60)
    
    # Suche nach Beispiel-Bildern im aktuellen Verzeichnis
    image_files = []
    common_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
    
    for file in os.listdir('.'):
        if any(file.lower().endswith(ext) for ext in common_extensions):
            image_files.append(file)
    
    if not image_files:
        print("❌ Keine Bilder im aktuellen Verzeichnis gefunden!")
        print("💡 Kopiere ein PNG/JPG-Bild hierher und starte den Test erneut.")
        return
    
    print(f"📁 Gefundene Bilder: {len(image_files)}")
    for i, img in enumerate(image_files, 1):
        print(f"   {i}. {img}")
    
    # Erstes Bild für Test verwenden
    test_image_path = image_files[0]
    print(f"\n🎯 Test-Bild: {test_image_path}")
    
    try:
        # Bild-Datei lesen
        with open(test_image_path, 'rb') as f:
            image_data = f.read()
        
        print(f"📊 Bild-Größe: {len(image_data)} bytes")
        
        print("\n🔄 ERSTE BILD-DRUCK (kritisch für Drift)...")
        print("   Dies war das problematische Szenario!")
        
        # Test 1: Erster Bild-Druck (hier trat das Problem auf)
        files = {'data': (test_image_path, image_data)}
        data = {
            'use_queue': 'false',
            'fit_to_label': 'true',
            'maintain_aspect': 'true',
            'dither': 'true'
        }
        
        print("📤 Sende echtes Bild an Drucker...")
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/api/print-image", files=files, data=data)
        end_time = time.time()
        
        result = response.json()
        
        if result['success']:
            print(f"✅ Erstes Bild erfolgreich gedruckt ({end_time-start_time:.2f}s)")
            print(f"📏 Format: {result.get('format', '?')}")
            print(f"📦 Größe: {result.get('size_bytes', '?')} bytes")
            print(f"💬 {result.get('message', '')}")
            
            # Visueller Check
            print("\n🔍 VISUELLER CHECK:")
            print("❓ Hat das Bild extremen Drift (viele Zeilen-Verschiebungen)?")
            check = input("   Eingabe: 'y' für JA (Drift), 'n' für NEIN (OK): ").lower().strip()
            
            if check == 'y':
                print("❌ DRIFT BESTÄTIGT - Enhanced Anti-Drift hat noch nicht geholfen")
                print("🔧 Führe Zusatz-Stabilisierung durch...")
                
                # Zusätzliche Stabilisierung
                stabilize_printer()
                
            elif check == 'n':
                print("✅ KEIN DRIFT - Enhanced Anti-Drift funktioniert!")
                print("🎉 Problem wurde behoben!")
                
                # Zusätzlicher Test mit zweitem Bild
                print("\n📷 BESTÄTIGUNGS-TEST mit zweitem Bild...")
                test_second_image(image_files, image_data)
                
            else:
                print("⚠️ Unklare Eingabe - visueller Check empfohlen")
        else:
            print(f"❌ Erster Bild-Druck fehlgeschlagen: {result['error']}")
            
    except FileNotFoundError:
        print(f"❌ Bild-Datei nicht gefunden: {test_image_path}")
    except Exception as e:
        print(f"❌ Test-Fehler: {e}")

def test_second_image(image_files, first_image_data):
    """Testet mit zweitem Bild zur Bestätigung"""
    if len(image_files) > 1:
        second_image = image_files[1]
        try:
            with open(second_image, 'rb') as f:
                image_data = f.read()
        except:
            image_data = first_image_data  # Fallback: gleiches Bild
        
        print(f"   📸 Zweites Bild: {second_image if len(image_files) > 1 else 'Wiederholung'}")
        
        files = {'data': (second_image, image_data)}
        response = requests.post(f"{BASE_URL}/api/print-image", 
                               files=files, 
                               data={'use_queue': 'false'})
        result = response.json()
        
        status = "✅" if result['success'] else "❌"
        print(f"   {status} Zweites Bild gedruckt")
        
        if result['success']:
            print("   🔍 Vergleiche beide Bilder - haben sie dieselbe Position?")

def stabilize_printer():
    """Führt zusätzliche Drucker-Stabilisierung durch"""
    print("\n🔧 ZUSÄTZLICHE DRUCKER-STABILISIERUNG...")
    
    try:
        # Kalibrierungs-Druck
        response = requests.post(f"{BASE_URL}/api/test-offsets", data={
            'pattern': 'full_test'
        })
        result = response.json()
        
        if result['success']:
            print("✅ Kalibrierungs-Pattern gedruckt")
            print("📋 Dies sollte die Drucker-Position stabilisieren")
        else:
            print(f"❌ Kalibrierung fehlgeschlagen: {result['error']}")
            
        # Pause für Stabilisierung
        print("⏱️ 5-Sekunden-Stabilisierungs-Pause...")
        time.sleep(5.0)
        
    except Exception as e:
        print(f"❌ Stabilisierungs-Fehler: {e}")

def quick_drift_diagnosis():
    """Schnelle Diagnose der Drift-Ursache"""
    print("\n🔬 SCHNELLE DRIFT-DIAGNOSE")
    
    # Einfacher Text-Test
    try:
        response = requests.post(f"{BASE_URL}/api/print-text", data={
            'text': '''DRIFT-DIAGNOSE

Links: ← RAND
Mitte: ↔ CENTER ↔
Rechts: RAND →

12345678901234567890''',
            'font_size': '18',
            'alignment': 'left',
            'immediate': 'true'
        })
        result = response.json()
        
        if result['success']:
            print("✅ Text-Diagnose gedruckt")
            print("📋 Vergleiche mit dem problematischen Bild:")
            print("   • Hat der Text normale Position?")
            print("   • Nur das Bild hat Drift-Probleme?")
        else:
            print(f"❌ Text-Diagnose fehlgeschlagen: {result['error']}")
            
    except Exception as e:
        print(f"❌ Diagnose-Fehler: {e}")

if __name__ == "__main__":
    print("📷 REAL IMAGE DRIFT TESTER")
    print("🎯 Speziell für das Problem: 'extremer Drift bei einem Bild'")
    print()
    
    test_real_image_drift()
    
    # Optional: Diagnose
    answer = input("\n❓ Zusätzliche Drift-Diagnose durchführen? (y/N): ")
    if answer.lower() == 'y':
        quick_drift_diagnosis()
    
    print("\n🎉 Real Image Drift Test abgeschlossen!")
    print("📋 Enhanced Anti-Drift für Bilder wurde implementiert.")
