#!/usr/bin/env python3
"""
Quality Optimization Test
Testet verschiedene Einstellungen für bessere Druckqualität
"""

import requests
import time
from PIL import Image, ImageDraw, ImageFont
import io

BASE_URL = "http://localhost:8080"

def create_quality_test_pattern() -> bytes:
    """Erstellt Test-Pattern für Qualitäts-Bewertung"""
    width, height = 320, 240
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Verschiedene Test-Pattern für Qualitäts-Bewertung
    
    # 1. Feine horizontale Linien (Drift-Test)
    for y in range(20, 80, 2):
        draw.line([10, y, width-10, y], fill='black', width=1)
    draw.text((15, 85), "HORIZONTAL LINES - CHECK ALIGNMENT", fill='black')
    
    # 2. Vertikale Linien (Konsistenz-Test)
    for x in range(20, 120, 4):
        draw.line([x, 100, x, 140], fill='black', width=1)
    draw.text((15, 145), "VERTICAL LINES - CHECK CONSISTENCY", fill='black')
    
    # 3. Diagonal-Pattern (Qualitäts-Test)
    for i in range(0, 80, 4):
        draw.line([140+i, 100, 140+i+20, 120], fill='black', width=1)
        draw.line([140+i+20, 120, 140+i+40, 100], fill='black', width=1)
    draw.text((145, 125), "DIAGONAL - CHECK QUALITY", fill='black')
    
    # 4. Text-Schärfe-Test
    draw.text((10, 160), "TEXT SHARPNESS TEST:", fill='black')
    draw.text((10, 175), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", fill='black')
    draw.text((10, 190), "1234567890 !@#$%^&*()", fill='black')
    
    # 5. Rahmen für Position-Referenz
    draw.rectangle([0, 0, width-1, height-1], outline='black', width=2)
    draw.rectangle([5, 5, width-6, height-6], outline='black', width=1)
    
    # Position-Markierungen
    draw.text((10, 10), "TOP-LEFT", fill='black')
    draw.text((width-70, 10), "TOP-RIGHT", fill='black')
    draw.text((10, height-25), "BOTTOM-LEFT", fill='black')
    draw.text((width-90, height-25), "BOTTOM-RIGHT", fill='black')
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()

def test_quality_settings():
    """Testet verschiedene Qualitäts-Einstellungen"""
    print("🎯 QUALITY OPTIMIZATION TEST")
    print("=" * 60)
    print("📋 Testet optimierte Einstellungen für bessere Druckqualität")
    print("🔧 Ohne extra Zeilen, mit verbesserter Übertragung")
    print("=" * 60)
    
    # Test 1: Standard-Qualitäts-Test
    print("\n1️⃣ QUALITÄTS-TEST: Standard-Pattern")
    test_standard_quality()
    
    # Test 2: Verschiedene Dithering-Einstellungen
    print("\n2️⃣ DITHERING-TEST: Verschiedene Einstellungen")
    test_dithering_settings()
    
    # Test 3: Verschiedene Skalierungs-Modi
    print("\n3️⃣ SKALIERUNGS-TEST: Verschiedene Modi")
    test_scaling_modes()

def test_standard_quality():
    """Standard-Qualitäts-Test mit dem optimierten Pattern"""
    try:
        print("   🎨 Erstelle Qualitäts-Test-Pattern...")
        test_image = create_quality_test_pattern()
        
        print("   📤 Sende mit optimierten Einstellungen...")
        files = {'data': ('quality_test.png', test_image, 'image/png')}
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
            print(f"   ✅ Qualitäts-Test erfolgreich ({end_time-start_time:.2f}s)")
            print("   📋 QUALITÄTS-BEWERTUNG:")
            print("       • Horizontale Linien gerade und ausgerichtet?")
            print("       • Vertikale Linien gleichmäßig?")
            print("       • Diagonale sauber und scharf?")
            print("       • Text scharf und lesbar?")
            print("       • Rahmen korrekt positioniert?")
            print("       • KEINE extra Zeilen am Ende?")
            
            quality_rating = input("   📊 Qualitäts-Bewertung (1-10, 10=perfekt): ")
            if quality_rating.isdigit():
                rating = int(quality_rating)
                if rating >= 8:
                    print("   🎉 EXCELLENT! Qualität ist sehr gut")
                elif rating >= 6:
                    print("   👍 GOOD! Qualität ist akzeptabel")
                    suggest_quality_improvements()
                else:
                    print("   😞 NEEDS IMPROVEMENT! Weitere Optimierung nötig")
                    suggest_quality_improvements()
        else:
            print(f"   ❌ Qualitäts-Test fehlgeschlagen: {result['error']}")
            
    except Exception as e:
        print(f"   ❌ Qualitäts-Test Fehler: {e}")

def test_dithering_settings():
    """Testet verschiedene Dithering-Einstellungen"""
    dithering_tests = [
        ('Dithering AN, Standard', {'dither': 'true'}),
        ('Dithering AUS, Threshold', {'dither': 'false', 'dither_threshold': '128'}),
        ('Hoher Kontrast', {'dither': 'true', 'contrast_boost': '1.5'}),
        ('Schwacher Kontrast', {'dither': 'true', 'contrast_boost': '0.8'})
    ]
    
    test_image = create_quality_test_pattern()
    
    for i, (name, settings) in enumerate(dithering_tests, 1):
        try:
            print(f"   {i}. {name}...")
            
            files = {'data': ('dither_test.png', test_image, 'image/png')}
            data = {
                'use_queue': 'false',
                'fit_to_label': 'true',
                **settings
            }
            
            response = requests.post(f"{BASE_URL}/api/print-image", files=files, data=data)
            result = response.json()
            
            if result['success']:
                print(f"      ✅ {name} erfolgreich")
                quality = input(f"      📊 Qualität von {name} (1-10): ")
                print(f"      📝 Bewertung: {quality}/10")
            else:
                print(f"      ❌ {name} fehlgeschlagen")
            
            time.sleep(2)  # Pause zwischen Tests
            
        except Exception as e:
            print(f"      ❌ {name} Fehler: {e}")

def test_scaling_modes():
    """Testet verschiedene Skalierungs-Modi"""
    scaling_tests = [
        ('Fit Aspect (Standard)', {'scaling_mode': 'fit_aspect'}),
        ('Crop Center', {'scaling_mode': 'crop_center'}),
        ('Pad Center', {'scaling_mode': 'pad_center'}),
        ('Stretch Full', {'scaling_mode': 'stretch_full'})
    ]
    
    test_image = create_quality_test_pattern()
    
    for i, (name, settings) in enumerate(scaling_tests, 1):
        try:
            print(f"   {i}. {name}...")
            
            files = {'data': ('scaling_test.png', test_image, 'image/png')}
            data = {
                'use_queue': 'false',
                'fit_to_label': 'true',
                'dither': 'true',
                **settings
            }
            
            response = requests.post(f"{BASE_URL}/api/print-image", files=files, data=data)
            result = response.json()
            
            if result['success']:
                print(f"      ✅ {name} erfolgreich")
                positioning = input(f"      📐 Positionierung von {name} OK? (y/N): ")
                if positioning.lower() == 'y':
                    print(f"      🎯 {name} - Positionierung OK")
                else:
                    print(f"      ⚠️ {name} - Positionierung problematisch")
            else:
                print(f"      ❌ {name} fehlgeschlagen")
            
            time.sleep(2)  # Pause zwischen Tests
            
        except Exception as e:
            print(f"      ❌ {name} Fehler: {e}")

def suggest_quality_improvements():
    """Vorschläge für weitere Qualitäts-Verbesserungen"""
    print("\n🔧 QUALITÄTS-VERBESSERUNGS-VORSCHLÄGE:")
    print("1. Chunk-Größe anpassen:")
    print("   • Kleinere Chunks (64-96) für bessere Präzision")
    print("   • Größere Chunks (192-256) für bessere Geschwindigkeit")
    
    print("\n2. Timing-Optimierung:")
    print("   • Längere Pausen: 0.02-0.05s zwischen Chunks")
    print("   • Kürzere Pausen: 0.005-0.01s für schnellere Übertragung")
    
    print("\n3. Bildverarbeitung:")
    print("   • Andere Dithering-Einstellungen")
    print("   • Kontrast-Anpassung")
    print("   • Auflösungs-Optimierung")
    
    print("\n4. Hardware-Checks:")
    print("   • Bluetooth-Signalstärke prüfen")
    print("   • Drucker-Position stabilisieren")
    print("   • Label-Qualität überprüfen")

def quick_drift_check():
    """Schneller Drift-Check mit einfachem Muster"""
    try:
        print("   🔍 Quick Drift Check...")
        
        # Einfaches Drift-Test-Muster
        width, height = 200, 100
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)
        
        # Nur horizontale Linien für Drift-Erkennung
        for y in range(10, height-10, 10):
            draw.line([5, y, width-5, y], fill='black', width=2)
            draw.text((10, y-8), f"LINE {y}", fill='black')
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        test_image = buffer.getvalue()
        
        files = {'data': ('drift_check.png', test_image, 'image/png')}
        data = {'use_queue': 'false', 'fit_to_label': 'true', 'dither': 'true'}
        
        response = requests.post(f"{BASE_URL}/api/print-image", files=files, data=data)
        result = response.json()
        
        if result['success']:
            print("   ✅ Drift-Check gedruckt")
            drift_status = input("   ❓ Drift sichtbar? (y/N): ")
            if drift_status.lower() == 'y':
                print("   ❌ DRIFT WEITERHIN VORHANDEN")
                return False
            else:
                print("   ✅ KEIN DRIFT ERKENNBAR")
                return True
        else:
            print(f"   ❌ Drift-Check fehlgeschlagen: {result['error']}")
            return False
            
    except Exception as e:
        print(f"   ❌ Drift-Check Fehler: {e}")
        return False

if __name__ == "__main__":
    print("🎯 QUALITY OPTIMIZATION TESTER")
    print("🔧 Optimiert für: Keine extra Zeilen + Bessere Qualität")
    print()
    
    # Erst schneller Drift-Check
    print("🔍 QUICK DRIFT CHECK:")
    drift_ok = quick_drift_check()
    
    if drift_ok:
        print("\n🎯 DRIFT OK - Starte Qualitäts-Tests...")
        test_quality_settings()
    else:
        print("\n⚠️ DRIFT PROBLEM - Qualitäts-Tests übersprungen")
        print("💡 Löse erst das Drift-Problem, dann Qualitäts-Optimierung")
    
    print("\n🎉 Quality Optimization Test abgeschlossen!")
