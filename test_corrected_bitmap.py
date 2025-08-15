#!/usr/bin/env python3
"""
Test für korrigierte Bitmap-Übertragung
Basierend auf erfolgreichen Implementierungen aus vivier/phomemo-tools
"""

import requests
import time
from PIL import Image, ImageDraw, ImageFont
import io
import os

BASE_URL = "http://localhost:8080"

def create_horizontal_line_test_image() -> bytes:
    """Erstellt Test-Bild mit vielen horizontalen Linien (Drift-Test)"""
    width, height = 320, 200
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Horizontale Linien in verschiedenen Abständen
    for y in range(10, height-10, 15):
        # Abwechselnd verschiedene Linienstile
        if y % 30 == 10:
            # Durchgezogene Linie
            draw.line([5, y, width-5, y], fill='black', width=2)
            draw.text((10, y-8), f"LINE {y}", fill='black')
        elif y % 30 == 25:
            # Gestrichelte Linie
            for x in range(5, width-5, 20):
                draw.line([x, y, min(x+10, width-5), y], fill='black', width=2)
            draw.text((10, y-8), f"DASH {y}", fill='black')
        else:
            # Gepunktete Linie
            for x in range(5, width-5, 8):
                draw.point((x, y), fill='black')
            draw.text((10, y-8), f"DOT {y}", fill='black')
    
    # Rahmen für Positions-Referenz
    draw.rectangle([0, 0, width-1, height-1], outline='black', width=3)
    
    # Position-Markierungen
    draw.text((10, 10), "TOP LEFT", fill='black')
    draw.text((width-80, 10), "TOP RIGHT", fill='black')
    draw.text((10, height-25), "BOTTOM LEFT", fill='black')
    draw.text((width-100, height-25), "BOTTOM RIGHT", fill='black')
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()

def test_corrected_bitmap_transmission():
    """Testet die korrigierte Bitmap-Übertragung"""
    print("🔧 CORRECTED BITMAP TRANSMISSION TEST")
    print("=" * 60)
    print("📋 Testet die korrigierte ESC/POS-basierte Bitmap-Übertragung")
    print("🎯 Speziell für das Problem: Horizontale Zeilen-Drift")
    print("=" * 60)
    
    # Test 1: Basis-Test mit Text
    print("\n1️⃣ BASIS-TEST: Text-Referenz")
    test_text_reference()
    
    # Test 2: Horizontale Linien (Haupt-Test)
    print("\n2️⃣ HAUPT-TEST: Horizontale Linien")
    test_horizontal_lines()
    
    # Test 3: Vollständiges Bild
    print("\n3️⃣ VOLLTEST: Komplexes Bild")
    test_complex_image()

def test_text_reference():
    """Text-Referenz für Positions-Vergleich"""
    try:
        print("   📝 Drucke Text-Referenz...")
        response = requests.post(f"{BASE_URL}/api/print-text", data={
            'text': '''CORRECTED BITMAP TEST

TEXT REFERENCE
←LEFT      CENTER      RIGHT→
|           |           |
Position check: OK

ZEILE 1: ABCDEFGHIJKLM
ZEILE 2: NOPQRSTUVWXYZ  
ZEILE 3: 1234567890123

Expected: Perfect alignment''',
            'font_size': '14',
            'alignment': 'left',
            'immediate': 'true'
        })
        result = response.json()
        
        if result['success']:
            print("   ✅ Text-Referenz gedruckt")
            print("   📋 Prüfe: Sind alle Zeilen korrekt ausgerichtet?")
        else:
            print(f"   ❌ Text-Referenz fehlgeschlagen: {result['error']}")
            
    except Exception as e:
        print(f"   ❌ Text-Referenz Fehler: {e}")

def test_horizontal_lines():
    """Test mit vielen horizontalen Linien"""
    try:
        print("   📏 Erstelle Horizontal-Linien-Test-Bild...")
        test_image = create_horizontal_line_test_image()
        
        print("   📤 Sende Horizontal-Linien-Bild mit korrigierter Übertragung...")
        files = {'data': ('horizontal_lines_test.png', test_image, 'image/png')}
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
            print(f"   ✅ Horizontal-Linien-Test erfolgreich ({end_time-start_time:.2f}s)")
            print(f"   📊 Größe: {result.get('size_bytes', '?')} bytes")
            print("   📋 KRITISCHER CHECK:")
            print("       • Sind ALLE horizontalen Linien gerade?")
            print("       • Keine Zeilen-Verschiebungen nach rechts?")
            print("       • Position-Markierungen korrekt?")
            
            drift_check = input("   ❓ Drift erkennbar? (y/N): ").lower().strip()
            if drift_check == 'y':
                print("   ❌ DRIFT WEITERHIN VORHANDEN")
                print("   💡 Möglicherweise Hardware-Problem oder andere Ursache")
                suggest_additional_fixes()
            else:
                print("   ✅ KEIN DRIFT - Korrektur erfolgreich!")
        else:
            print(f"   ❌ Horizontal-Linien-Test fehlgeschlagen: {result['error']}")
            
    except Exception as e:
        print(f"   ❌ Horizontal-Linien-Test Fehler: {e}")

def test_complex_image():
    """Test mit echtem Bild (falls vorhanden)"""
    try:
        # Suche nach Bild-Dateien
        image_files = []
        for file in os.listdir('.'):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_files.append(file)
        
        if not image_files:
            print("   ⚠️ Keine Bild-Dateien für Volltest gefunden")
            return
        
        test_image = image_files[0]
        print(f"   📷 Volltest mit echtem Bild: {test_image}")
        
        with open(test_image, 'rb') as f:
            image_data = f.read()
        
        files = {'data': (test_image, image_data)}
        data = {'use_queue': 'false', 'fit_to_label': 'true'}
        
        response = requests.post(f"{BASE_URL}/api/print-image", files=files, data=data)
        result = response.json()
        
        if result['success']:
            print("   ✅ Volltest erfolgreich")
            print("   📋 Vergleiche mit Text-Referenz und Horizontal-Linien")
        else:
            print(f"   ❌ Volltest fehlgeschlagen: {result['error']}")
            
    except Exception as e:
        print(f"   ❌ Volltest Fehler: {e}")

def suggest_additional_fixes():
    """Weitere Lösungsvorschläge wenn Drift weiterhin vorhanden"""
    print("\n🔧 ZUSÄTZLICHE LÖSUNGSANSÄTZE:")
    print("1. Hardware-Überprüfung:")
    print("   • Drucker-Firmware aktualisieren")
    print("   • Bluetooth-Verbindung prüfen (Signalstärke)")
    print("   • Drucker physisch überprüfen (Mechanik)")
    
    print("\n2. Software-Konfiguration:")
    print("   • Andere Chunk-Größen testen (120, 480)")
    print("   • Längere Pausen zwischen Chunks")
    print("   • Unterschiedliche Dithering-Einstellungen")
    
    print("\n3. Alternative Ansätze:")
    print("   • ESC/POS-Kommandos einzeln testen")
    print("   • Drucker-spezifische Sequenzen aus Handbuch")
    print("   • USB-Verbindung testen (falls verfügbar)")

def monitor_server_logs():
    """Überwacht Server-Logs während der Tests"""
    print("\n📊 SERVER-LOG MONITORING:")
    print("💡 Während der Tests sollten Sie die Server-Logs überwachen:")
    print("   - Konsole wo der Server läuft")
    print("   - Achten Sie auf 'CORRECTED BITMAP' Meldungen")
    print("   - Chunk-Progress und Fehler-Meldungen")

if __name__ == "__main__":
    print("🔧 CORRECTED BITMAP TRANSMISSION TESTER")
    print("📋 Basiert auf erfolgreichen vivier/phomemo-tools Implementierungen")
    print()
    
    monitor_server_logs()
    
    input("📋 Server-Logs bereit? Drücken Sie Enter um zu starten...")
    
    test_corrected_bitmap_transmission()
    
    print("\n🎉 Corrected Bitmap Test abgeschlossen!")
    print("📋 Die korrigierte ESC/POS-Implementierung sollte den Drift beheben.")
