#!/usr/bin/env python3
"""
Hardware-Level Drift Debug
Analysiert die rohen Drucker-Kommandos und Bitmap-Daten
"""

import requests
import time
import logging

BASE_URL = "http://localhost:8080"

def enable_debug_logging():
    """Aktiviert detailliertes Debug-Logging"""
    print("🔧 HARDWARE-LEVEL DEBUG")
    print("=" * 50)
    print("📋 Analysiert rohe Drucker-Kommandos und Bitmap-Übertragung")
    print("📋 Sucht nach Hardware-spezifischen Drift-Ursachen")
    print("=" * 50)
    
    try:
        # Debug-Mode aktivieren
        response = requests.post(f"{BASE_URL}/api/settings", data={
            'debug_mode': 'true'
        })
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print("✅ Debug-Logging aktiviert")
            else:
                print(f"⚠️ Debug-Logging-Problem: {result['error']}")
        else:
            print("⚠️ Debug-Logging konnte nicht aktiviert werden")
            
    except Exception as e:
        print(f"⚠️ Debug-Logging-Fehler: {e}")

def test_minimal_image():
    """Testet mit minimalem Bild für Hardware-Analyse"""
    print("\n🖼️ MINIMAL-BILD HARDWARE-TEST")
    
    # Erstelle winziges Test-Bild (minimal für Hardware-Analyse)
    from PIL import Image, ImageDraw
    import io
    
    # Sehr kleines Bild (50x30) - minimal für Drift-Test
    img = Image.new('RGB', (50, 30), 'white')
    draw = ImageDraw.Draw(img)
    
    # Nur essenzielle Markierungen
    draw.rectangle([0, 0, 49, 29], outline='black', width=1)  # Rahmen
    draw.text((5, 10), "MIN", fill='black')  # Text
    draw.line([0, 15, 49, 15], fill='black', width=1)  # Horizontal-Linie
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    minimal_image = buffer.getvalue()
    
    print(f"   📊 Minimal-Bild: {len(minimal_image)} bytes")
    
    try:
        files = {'data': ('minimal.png', minimal_image, 'image/png')}
        data = {
            'use_queue': 'false',
            'fit_to_label': 'true',
            'maintain_aspect': 'true',
            'dither': 'false'  # Kein Dithering für Hardware-Test
        }
        
        print("   📤 Sende Minimal-Bild...")
        response = requests.post(f"{BASE_URL}/api/print-image", files=files, data=data)
        result = response.json()
        
        if result['success']:
            print("   ✅ Minimal-Bild erfolgreich")
            print("   📋 Prüfe: Hat sogar dieses winzige Bild Drift?")
        else:
            print(f"   ❌ Minimal-Bild fehlgeschlagen: {result['error']}")
            
    except Exception as e:
        print(f"   ❌ Minimal-Bild Fehler: {e}")

def test_chunk_sizes():
    """Testet verschiedene Chunk-Größen"""
    print("\n📦 CHUNK-GRÖSSEN-TEST")
    print("   Testet, ob Chunk-Größe den Drift beeinflusst...")
    
    # Aktueller Status
    try:
        response = requests.get(f"{BASE_URL}/api/status")
        if response.status_code == 200:
            status = response.json()
            print(f"   📊 Aktueller Status: {status.get('connection_status', 'Unknown')}")
        
    except Exception as e:
        print(f"   ⚠️ Status-Abfrage fehlgeschlagen: {e}")

def analyze_bitmap_data():
    """Analysiert Bitmap-Daten-Struktur"""
    print("\n🔬 BITMAP-DATEN-ANALYSE")
    
    # Test mit Preview-API um Bitmap-Struktur zu analysieren
    from PIL import Image, ImageDraw
    import io
    
    # Test-Bild für Analyse
    img = Image.new('RGB', (100, 50), 'white')
    draw = ImageDraw.Draw(img)
    
    # Präzise Linien für Drift-Erkennung
    for x in range(0, 100, 10):
        draw.line([x, 0, x, 50], fill='black', width=1)
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    test_image = buffer.getvalue()
    
    try:
        files = {'data': ('analysis.png', test_image, 'image/png')}
        data = {
            'fit_to_label': 'true',
            'maintain_aspect': 'true',
            'enable_dither': 'false'
        }
        
        print("   📊 Analysiere Bitmap-Konvertierung...")
        response = requests.post(f"{BASE_URL}/api/preview-image", files=files, data=data)
        result = response.json()
        
        if result['success']:
            print("   ✅ Bitmap-Analyse erfolgreich")
            if 'info' in result:
                info = result['info']
                print(f"   📐 Verarbeitete Größe: {info.get('processed_width', '?')}×{info.get('processed_height', '?')}px")
                print(f"   🎛️ Offsets: X={info.get('x_offset', 0)}, Y={info.get('y_offset', 0)}")
                
                # Prüfe auf ungewöhnliche Werte
                if info.get('x_offset', 0) != 0:
                    print(f"   ⚠️ X-Offset ist nicht 0: {info.get('x_offset')}")
                if info.get('y_offset', 0) != 0:
                    print(f"   ⚠️ Y-Offset ist nicht 0: {info.get('y_offset')}")
                    
        else:
            print(f"   ❌ Bitmap-Analyse fehlgeschlagen: {result['error']}")
            
    except Exception as e:
        print(f"   ❌ Bitmap-Analyse Fehler: {e}")

def check_printer_settings():
    """Überprüft kritische Drucker-Einstellungen"""
    print("\n⚙️ DRUCKER-EINSTELLUNGEN-CHECK")
    
    try:
        response = requests.get(f"{BASE_URL}/api/settings")
        if response.status_code == 200:
            settings = response.json()
            
            print("   📋 Kritische Einstellungen:")
            critical_settings = [
                'x_offset', 'y_offset', 'dither_threshold', 
                'anti_drift_interval', 'label_size'
            ]
            
            for setting in critical_settings:
                value = settings.get(setting, 'NICHT GESETZT')
                print(f"      {setting}: {value}")
                
                # Prüfe auf problematische Werte
                if setting == 'x_offset' and value != 40:
                    print(f"      ⚠️ X-Offset nicht Standard (40): {value}")
                if setting == 'anti_drift_interval' and value < 2.0:
                    print(f"      ⚠️ Anti-Drift-Interval zu kurz: {value}")
                    
        else:
            print("   ❌ Einstellungen-Abfrage fehlgeschlagen")
            
    except Exception as e:
        print(f"   ❌ Einstellungen-Check Fehler: {e}")

def hardware_reset_sequence():
    """Führt Hardware-Reset-Sequenz durch"""
    print("\n🔄 HARDWARE-RESET-SEQUENZ")
    print("   Führt aggressive Hardware-Resets durch...")
    
    reset_commands = [
        ("Drucker-Verbindung reset", "force-reconnect"),
        ("Offset-Kalibrierung", "test-offsets"), 
        ("Position-Reset", "test-offsets")
    ]
    
    for description, endpoint in reset_commands:
        print(f"   🔧 {description}...")
        try:
            if endpoint == "force-reconnect":
                response = requests.post(f"{BASE_URL}/api/force-reconnect")
            else:
                response = requests.post(f"{BASE_URL}/api/{endpoint}", data={'pattern': 'full_test'})
            
            if response.status_code == 200:
                result = response.json()
                status = "✅" if result.get('success', False) else "❌"
                print(f"      {status} {description}")
            else:
                print(f"      ❌ {description} fehlgeschlagen (HTTP {response.status_code})")
                
            time.sleep(2.0)  # Pause zwischen Resets
            
        except Exception as e:
            print(f"      ❌ {description} Fehler: {e}")

if __name__ == "__main__":
    print("🔬 HARDWARE-LEVEL DRIFT DEBUGGER")
    print("🎯 Analysiert Hardware-spezifische Drift-Ursachen")
    print()
    
    # Debug-Logging aktivieren
    enable_debug_logging()
    
    # Hardware-Tests
    check_printer_settings()
    analyze_bitmap_data()
    test_minimal_image()
    test_chunk_sizes()
    
    print("\n📊 HARDWARE-DIAGNOSE ABGESCHLOSSEN")
    print("📋 Prüfe die Drucker-Logs für weitere Details")
    
    # Optional: Hardware-Reset
    answer = input("\n❓ Hardware-Reset-Sequenz versuchen? (y/N): ")
    if answer.lower() == 'y':
        hardware_reset_sequence()
    
    print("\n🎉 Hardware-Level Debug abgeschlossen!")
    print("📋 Falls Problem weiterhin besteht: Hardware-Defekt möglich")
