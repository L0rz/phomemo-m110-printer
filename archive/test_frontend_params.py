#!/usr/bin/env python3
"""
Frontend Parameter Test
Testet ob Vorschau-Parameter beim Druck angewendet werden
"""

import requests
import time
from PIL import Image, ImageDraw
import io

BASE_URL = "http://localhost:8080"

def create_simple_test_image() -> bytes:
    """Erstellt einfaches Test-Bild zum Parameter-Test"""
    width, height = 200, 150
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Einfaches Test-Pattern
    draw.rectangle([10, 10, width-10, height-10], outline='black', width=2)
    draw.text((20, 30), "PARAMETER TEST", fill='black')
    draw.text((20, 50), "Scaling & Dithering", fill='black')
    draw.text((20, 70), "Should match preview", fill='black')
    
    # Pattern für Skalierungs-Test
    for i in range(5):
        y = 90 + i * 10
        draw.line([20, y, width-20, y], fill='black', width=1)
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()

def test_preview_vs_print():
    """Testet ob Vorschau und Druck identisch sind"""
    print("🔍 FRONTEND PARAMETER TEST")
    print("=" * 60)
    print("📋 Testet ob Vorschau-Parameter beim Druck angewendet werden")
    print("=" * 60)
    
    test_image = create_simple_test_image()
    
    # Test verschiedene Parameter-Kombinationen
    test_cases = [
        {
            'name': 'Standard Fit Aspect',
            'params': {
                'fit_to_label': 'true',
                'maintain_aspect': 'true',
                'enable_dither': 'true',
                'scaling_mode': 'fit_aspect'
            }
        },
        {
            'name': 'Crop Center Mode',
            'params': {
                'fit_to_label': 'true',
                'maintain_aspect': 'false',
                'enable_dither': 'true',
                'scaling_mode': 'crop_center'
            }
        },
        {
            'name': 'No Dithering',
            'params': {
                'fit_to_label': 'true',
                'maintain_aspect': 'true',
                'enable_dither': 'false',
                'dither_threshold': '100'
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}️⃣ TEST CASE: {test_case['name']}")
        print(f"   Parameters: {test_case['params']}")
        
        # 1. Vorschau erstellen
        print("   📸 Erstelle Vorschau...")
        preview_success = test_preview(test_image, test_case['params'])
        
        if preview_success:
            print("   ✅ Vorschau erfolgreich erstellt")
            
            # 2. Druck mit GLEICHEN Parametern
            print("   🖨️ Drucke mit gleichen Parametern...")
            print_success = test_print(test_image, test_case['params'])
            
            if print_success:
                print("   ✅ Druck erfolgreich")
                
                # 3. Visueller Vergleich
                match = input("   ❓ Stimmen Vorschau und Druck überein? (y/N): ").lower().strip()
                if match == 'y':
                    print("   🎉 PARAMETER KORREKT ANGEWENDET")
                else:
                    print("   ❌ PARAMETER-PROBLEM ERKANNT")
                    diagnose_parameter_issue(test_case)
            else:
                print("   ❌ Druck fehlgeschlagen")
        else:
            print("   ❌ Vorschau fehlgeschlagen")
        
        # Pause zwischen Tests
        time.sleep(3)

def test_preview(image_data: bytes, params: dict) -> bool:
    """Testet Vorschau mit spezifischen Parametern"""
    try:
        files = {'data': ('test.png', image_data, 'image/png')}
        
        response = requests.post(f"{BASE_URL}/api/preview-image", files=files, data=params)
        result = response.json()
        
        if result['success']:
            info = result.get('info', {})
            print(f"      📊 Vorschau Info: {info.get('processed_width', '?')}x{info.get('processed_height', '?')}px")
            print(f"      ⚙️ Scaling: {info.get('scaling_mode', '?')}, Dither: {info.get('dither_enabled', '?')}")
            return True
        else:
            print(f"      ❌ Vorschau Fehler: {result.get('error', 'Unknown')}")
            return False
            
    except Exception as e:
        print(f"      ❌ Vorschau Exception: {e}")
        return False

def test_print(image_data: bytes, params: dict) -> bool:
    """Testet Druck mit spezifischen Parametern"""
    try:
        files = {'data': ('test.png', image_data, 'image/png')}
        # WICHTIG: use_queue=false für sofortigen Druck
        params['use_queue'] = 'false'
        
        response = requests.post(f"{BASE_URL}/api/print-image", files=files, data=params)
        result = response.json()
        
        if result['success']:
            settings = result.get('settings_applied', {})
            print(f"      📊 Angewendete Einstellungen: {settings}")
            return True
        else:
            print(f"      ❌ Druck Fehler: {result.get('error', 'Unknown')}")
            return False
            
    except Exception as e:
        print(f"      ❌ Druck Exception: {e}")
        return False

def diagnose_parameter_issue(test_case: dict):
    """Diagnostiziert Parameter-Probleme"""
    print("   🔧 PARAMETER-DIAGNOSE:")
    print("      • Check 1: API überträgt Parameter korrekt?")
    print("      • Check 2: print_image_immediate verwendet Parameter?")
    print("      • Check 3: Bildverarbeitung wendet Parameter an?")
    
    suggestion = input("   💡 Welcher Check soll durchgeführt werden? (1/2/3): ").strip()
    
    if suggestion == '1':
        print("   📋 API-Check: Schaue Server-Logs für 'settings_applied' Ausgabe")
    elif suggestion == '2':
        print("   📋 Immediate-Check: Schaue ob print_image_immediate alle Parameter erhält")
    elif suggestion == '3':
        print("   📋 Processing-Check: Schaue ob process_image_for_preview Parameter verwendet")

def test_simple_drift_check():
    """Einfacher Drift-Check"""
    print("\n🔍 QUICK DRIFT CHECK")
    
    # Einfaches Linien-Pattern
    width, height = 150, 100
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    for y in range(10, height-10, 15):
        draw.line([10, y, width-10, y], fill='black', width=2)
        draw.text((15, y-8), f"L{y}", fill='black')
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    test_image = buffer.getvalue()
    
    try:
        files = {'data': ('drift_test.png', test_image, 'image/png')}
        data = {'use_queue': 'false', 'fit_to_label': 'true'}
        
        response = requests.post(f"{BASE_URL}/api/print-image", files=files, data=data)
        result = response.json()
        
        if result['success']:
            print("✅ Drift-Test gedruckt")
            drift = input("❓ Drift sichtbar? (y/N): ").lower().strip()
            return drift != 'y'
        else:
            print(f"❌ Drift-Test fehlgeschlagen: {result.get('error', '?')}")
            return False
            
    except Exception as e:
        print(f"❌ Drift-Test Fehler: {e}")
        return False

def quick_server_status():
    """Schneller Server-Status Check"""
    try:
        response = requests.get(f"{BASE_URL}/api/status")
        status = response.json()
        
        print(f"📡 Server Status: {'✅ Connected' if status.get('connected') else '❌ Disconnected'}")
        print(f"📊 Queue Size: {status.get('queue_size', '?')}")
        
        settings_response = requests.get(f"{BASE_URL}/api/settings")
        settings = settings_response.json()
        
        if settings['success']:
            s = settings['settings']
            print(f"⚙️ Current Settings:")
            print(f"   X-Offset: {s.get('x_offset', '?')}")
            print(f"   Y-Offset: {s.get('y_offset', '?')}")
            print(f"   Anti-Drift Interval: {s.get('anti_drift_interval', '?')}s")
        
        return True
    except Exception as e:
        print(f"❌ Server Status Fehler: {e}")
        return False

if __name__ == "__main__":
    print("🔍 FRONTEND PARAMETER TESTER")
    print("🎯 Überprüft ob Vorschau-Parameter beim Druck angewendet werden")
    print()
    
    # Server Status prüfen
    print("📡 SERVER STATUS CHECK:")
    server_ok = quick_server_status()
    
    if not server_ok:
        print("❌ Server nicht erreichbar - beende Test")
        exit(1)
    
    # Drift Check
    print("\n🔍 DRIFT CHECK:")
    drift_ok = test_simple_drift_check()
    
    if drift_ok:
        print("✅ Kein Drift erkannt")
    else:
        print("❌ Drift Problem - behebe erst den Drift")
    
    # Parameter Tests
    answer = input("\n❓ Frontend Parameter Tests durchführen? (y/N): ")
    if answer.lower() == 'y':
        test_preview_vs_print()
    
    print("\n🎉 Frontend Parameter Test abgeschlossen!")
    print("📋 Nächste Schritte:")
    print("1. Wenn Parameter-Problem: API-Route korrigieren")
    print("2. Wenn Drift-Problem: send_bitmap Funktion reparieren")
    print("3. Wenn beides OK: Frontend-Integration prüfen")
