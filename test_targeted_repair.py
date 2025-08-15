#!/usr/bin/env python3
"""
Targeted Repair Test
Repariert die verbleibenden spezifischen Probleme
"""

import requests
import time
from PIL import Image, ImageDraw
import io
import os

BASE_URL = "http://localhost:8080"

def test_text_specific_repair():
    """Testet Text-spezifische Reparatur"""
    print("📝 TEXT-SPEZIFISCHE REPARATUR")
    print("=" * 50)
    
    # Test verschiedene Text-Formate
    test_texts = [
        # Einfacher Text (sollte funktionieren)
        "Einfacher Test ohne Markdown",
        
        # Text mit Alphabet (das hatte Probleme)
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ\n1234567890",
        
        # Text mit Markdown (könnte problematisch sein)
        "**Fetter Text** mit *kursiv* und `code`",
        
        # Text mit Sonderzeichen
        "Sonderzeichen: äöüß @#$%&"
    ]
    
    for i, test_text in enumerate(test_texts, 1):
        print(f"\n   {i}. Text-Variante: '{test_text[:30]}...'")
        
        try:
            response = requests.post(f"{BASE_URL}/api/print-text", data={
                'text': test_text,
                'font_size': '16',
                'alignment': 'left',
                'immediate': 'true'
            })
            result = response.json()
            
            status = "✅" if result['success'] else "❌"
            print(f"      {status} Text-Variante {i}")
            
            if result['success']:
                print("      📋 Prüfe: Ist der Text korrekt positioniert?")
            else:
                print(f"      💬 Fehler: {result['error']}")
            
            # Pause zwischen Tests
            time.sleep(2.0)
            
        except Exception as e:
            print(f"      ❌ Text-Variante {i} Fehler: {e}")

def test_image_format_repair():
    """Testet verschiedene Bild-Formate vs. Debug-Bild"""
    print("\n🖼️ BILD-FORMAT-SPEZIFISCHE REPARATUR")
    print("=" * 50)
    
    # 1. Debug-Bild (funktioniert) - Referenz
    print("\n   1. Debug-Bild (Referenz - sollte funktionieren):")
    debug_image = create_debug_reference()
    test_single_image("debug_reference.png", debug_image, "Debug-Referenz")
    
    # 2. Echtes Bild (Problem)
    print("\n   2. Echtes Bild-Upload (Problem):")
    test_real_uploaded_image()
    
    # 3. Identisches Bild, aber als Upload simuliert
    print("\n   3. Debug-Bild als Upload simuliert:")
    test_debug_as_upload()

def create_debug_reference():
    """Erstellt Debug-Bild identisch zum funktionierenden"""
    width, height = 200, 120
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Exakt wie das funktionierende Debug-Bild
    # Links-Rand-Markierung
    for i in range(5):
        draw.line([i, 0, i, height], fill='black', width=1)
    draw.text((8, 5), "LEFT-EDGE", fill='black')
    
    # Rechter Rand
    for i in range(width-5, width):
        draw.line([i, 0, i, height], fill='black', width=1)
    draw.text((width-55, 5), "RIGHT-EDGE", fill='black')
    
    # Zentral-Referenz
    center_x = width // 2
    draw.line([center_x, 0, center_x, height], fill='red', width=2)
    draw.text((center_x-20, height//2), "CENTER", fill='red')
    
    # Test-Text
    draw.text((20, 25), "DEBUG REFERENCE", fill='black')
    draw.text((20, 45), "Should work perfectly", fill='black')
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()

def test_single_image(filename, image_data, description):
    """Testet ein einzelnes Bild"""
    try:
        files = {'data': (filename, image_data, 'image/png')}
        data = {
            'use_queue': 'false',
            'fit_to_label': 'true',
            'maintain_aspect': 'true',
            'dither': 'true'
        }
        
        response = requests.post(f"{BASE_URL}/api/print-image", files=files, data=data)
        result = response.json()
        
        if result['success']:
            print(f"   ✅ {description} erfolgreich")
            print(f"   📊 Format: {result.get('format', '?')}, Größe: {result.get('size_bytes', '?')} bytes")
            print("   📋 Prüfe Position im Vergleich zur Debug-Referenz!")
        else:
            print(f"   ❌ {description} fehlgeschlagen: {result['error']}")
            
    except Exception as e:
        print(f"   ❌ {description} Fehler: {e}")

def test_real_uploaded_image():
    """Testet echtes Bild-Upload"""
    # Suche nach Bild-Dateien
    image_files = []
    for file in os.listdir('.'):
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            image_files.append(file)
    
    if not image_files:
        print("   ⚠️ Keine echten Bild-Dateien gefunden")
        return
    
    test_file = image_files[0]
    print(f"   📁 Teste echtes Bild: {test_file}")
    
    try:
        with open(test_file, 'rb') as f:
            image_data = f.read()
        
        test_single_image(test_file, image_data, f"Echtes Bild ({test_file})")
        
    except Exception as e:
        print(f"   ❌ Echtes Bild-Upload Fehler: {e}")

def test_debug_as_upload():
    """Testet Debug-Bild als Upload (um Code-Pfad zu testen)"""
    debug_image = create_debug_reference()
    test_single_image("debug_as_upload.png", debug_image, "Debug-Bild als Upload")

def test_offset_interference():
    """Testet, ob Offsets das Problem verursachen"""
    print("\n⚙️ OFFSET-INTERFERENZ-TEST")
    print("=" * 50)
    
    print("   📊 Aktuelle Offset-Einstellungen abrufen...")
    try:
        response = requests.get(f"{BASE_URL}/api/settings")
        if response.status_code == 200:
            settings = response.json()
            x_offset = settings.get('x_offset', 0)
            y_offset = settings.get('y_offset', 0)
            
            print(f"   📐 Aktuelle Offsets: X={x_offset}, Y={y_offset}")
            
            if x_offset != 0 or y_offset != 0:
                print("   ⚠️ Offsets sind nicht 0 - könnten Drift verursachen!")
                
                # Test mit Offsets auf 0 setzen
                print("   🔧 Teste mit Offsets = 0...")
                test_with_zero_offsets()
            else:
                print("   ✅ Offsets sind bereits 0")
                
        else:
            print("   ❌ Offset-Abfrage fehlgeschlagen")
            
    except Exception as e:
        print(f"   ❌ Offset-Test Fehler: {e}")

def test_with_zero_offsets():
    """Testet mit Offsets auf 0 gesetzt"""
    try:
        # Offsets temporär auf 0 setzen
        response = requests.post(f"{BASE_URL}/api/settings", data={
            'x_offset': '0',
            'y_offset': '0'
        })
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print("      ✅ Offsets auf 0 gesetzt")
                
                # Test-Druck mit 0-Offsets
                print("      📝 Test-Text mit 0-Offsets...")
                response = requests.post(f"{BASE_URL}/api/print-text", data={
                    'text': 'ZERO-OFFSET-TEST\nABCDEFGHIJKLMNOPQRSTUVWXYZ',
                    'font_size': '16',
                    'alignment': 'left',
                    'immediate': 'true'
                })
                result = response.json()
                
                status = "✅" if result['success'] else "❌"
                print(f"      {status} Zero-Offset-Test")
                print("      📋 Prüfe: Ist der Text jetzt korrekt?")
                
            else:
                print(f"      ❌ Offset-Setzen fehlgeschlagen: {result['error']}")
        else:
            print("      ❌ Offset-Request fehlgeschlagen")
            
    except Exception as e:
        print(f"      ❌ Zero-Offset-Test Fehler: {e}")

def analyze_targeted_results():
    """Analysiert die gezielten Test-Ergebnisse"""
    print("\n" + "="*50)
    print("📊 GEZIELTE REPARATUR-ANALYSE")
    print()
    print("🔍 Welche Tests waren erfolgreich?")
    print("   A) Alle Text-Varianten korrekt")
    print("   B) Debug-Bild vs. Echtes Bild unterschiedlich")  
    print("   C) Zero-Offset-Test war erfolgreich")
    print("   D) Immer noch Probleme bei bestimmten Typen")
    print()
    
    answer = input("Eingabe (A/B/C/D): ").upper().strip()
    
    if answer == 'A':
        print("\n✅ TEXT-PROBLEM GELÖST!")
        print("🎯 Fokus jetzt auf Bild-Upload-Problem")
        
    elif answer == 'B':
        print("\n🔧 BILD-FORMAT-PROBLEM IDENTIFIZIERT!")
        print("💡 Unterschiedliche Verarbeitung von Debug vs. Upload")
        suggest_image_format_fix()
        
    elif answer == 'C':
        print("\n🎯 OFFSET-PROBLEM IDENTIFIZIERT!")
        print("💡 Offsets verursachen den Drift")
        suggest_offset_fix()
        
    elif answer == 'D':
        print("\n⚠️ KOMPLEXES PROBLEM")
        print("💡 Tiefere Hardware-Analyse nötig")
        suggest_hardware_analysis()
        
    else:
        print("\n⚠️ Weitere Analyse empfohlen")

def suggest_image_format_fix():
    print("🛠️ BILD-FORMAT-REPARATUR-VORSCHLÄGE:")
    print("1. Bild-Upload-Pipeline überprüfen")
    print("2. Format-Konvertierung vor Verarbeitung")
    print("3. Einheitliche Bild-Verarbeitung implementieren")

def suggest_offset_fix():
    print("🛠️ OFFSET-REPARATUR-VORSCHLÄGE:")  
    print("1. Offset-Anwendung nur bei Preview, nicht bei Druck")
    print("2. Offset-Reset vor jedem Druck")
    print("3. Separate Offset-Pipeline für verschiedene Drucktypen")

def suggest_hardware_analysis():
    print("🛠️ HARDWARE-ANALYSE-VORSCHLÄGE:")
    print("1. Bluetooth-Verbindung neu aufbauen")
    print("2. Drucker-Firmware-Reset")
    print("3. Verschiedene Übertragungsgeschwindigkeiten testen")

if __name__ == "__main__":
    print("🎯 TARGETED REPAIR TESTER")
    print("🔧 Repariert spezifische verbleibende Probleme")
    print()
    
    test_text_specific_repair()
    test_image_format_repair() 
    test_offset_interference()
    analyze_targeted_results()
    
    print("\n🎉 Targeted Repair Test abgeschlossen!")
    print("📋 Die gezielten Tests zeigen die spezifischen Problemquellen.")
