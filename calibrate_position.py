#!/usr/bin/env python3
"""
Drucker-Kalibrierung für Position-Reset
Führt verschiedene Kalibrierungs-Kommandos aus, um Drift zu korrigieren
"""

import requests
import time

BASE_URL = "http://localhost:8080"

def printer_reset_calibration():
    """Führt eine vollständige Drucker-Kalibrierung durch"""
    print("🔧 DRUCKER-KALIBRIERUNG für Position-Reset")
    print("=" * 50)
    
    # Test 1: Einzelner Kalibrierungs-Druck
    print("📐 Teste Kalibrierungs-Pattern...")
    try:
        response = requests.post(f"{BASE_URL}/api/test-offsets", data={
            'pattern': 'full_test'
        })
        result = response.json()
        
        if result['success']:
            print("✅ Kalibrierungs-Pattern erfolgreich gedruckt")
            print("📋 Prüfe das Pattern auf korrekte Positionierung")
        else:
            print(f"❌ Kalibrierung fehlgeschlagen: {result['error']}")
            
    except Exception as e:
        print(f"❌ Kalibrierungs-Fehler: {e}")
    
    print("\n🔄 DRUCKER-RESET-SEQUENZ")
    print("   Führt mehrere Reset-Kommandos aus...")
    
    # Test 2: Mehrfache Reset-Zyklen
    reset_commands = [
        ("Drucker initialisieren", {}),
        ("Position zurücksetzen", {}),
        ("Erweiterte Kalibrierung", {'pattern': 'x_offset_test'}),
    ]
    
    for i, (description, params) in enumerate(reset_commands, 1):
        print(f"\n{i}. {description}...")
        try:
            response = requests.post(f"{BASE_URL}/api/test-offsets", data=params)
            result = response.json()
            
            status = "✅" if result['success'] else "❌"
            print(f"   {status} {description}")
            
            # Pause zwischen Reset-Kommandos
            time.sleep(1.0)
            
        except Exception as e:
            print(f"   ❌ Fehler bei {description}: {e}")
    
    print("\n📊 VERIFIKATIONS-TEST")
    print("   Druckt 3 identische Test-Patterns...")
    
    # Test 3: Verifikation mit identischen Patterns
    for i in range(1, 4):
        print(f"   📋 Verifikations-Pattern {i}/3...")
        try:
            # Einfacher Text-Test für Position-Verifikation
            response = requests.post(f"{BASE_URL}/api/print-text", data={
                'text': f'''# POSITION-TEST {i}

**Links:** ←←← RAND
**Mitte:** ←→ ZENTER ←→  
**Rechts:** RAND →→→

Zeile {i}: Konstante Position?
123456789012345678901234567890''',
                'font_size': '18',
                'alignment': 'left',
                'immediate': 'true'
            })
            result = response.json()
            
            status = "✅" if result['success'] else "❌"
            print(f"      {status} Pattern {i}")
            
            # Kurze Pause zwischen Verifikations-Tests
            time.sleep(0.5)
            
        except Exception as e:
            print(f"      ❌ Verifikations-Fehler {i}: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 KALIBRIERUNGS-ERGEBNIS:")
    print("📋 Vergleiche die 3 Verifikations-Patterns:")
    print("   ✅ ERFOLGREICH: Alle Patterns haben dieselbe Position")
    print("   ❌ PROBLEM: Patterns wandern nach rechts")
    print()
    print("💡 NÄCHSTE SCHRITTE:")
    print("   • Bei erfolgreichem Reset: Normales Drucken fortsetzen")
    print("   • Bei weiterem Drift: Server neustarten")
    print("   • Bei Hardware-Problem: Drucker aus/ein schalten")

def quick_position_test():
    """Schneller Test für aktuelle Position"""
    print("\n⚡ SCHNELLER POSITIONS-TEST")
    
    try:
        response = requests.post(f"{BASE_URL}/api/print-text", data={
            'text': '''← LINKS    MITTE    RECHTS →
    |         |         |
   10        20        30
ABCDEFGHIJKLMNOPQRSTUVWXYZ''',
            'font_size': '16',
            'alignment': 'left',
            'immediate': 'true'
        })
        result = response.json()
        
        if result['success']:
            print("✅ Positions-Test gedruckt")
            print("📏 Prüfe, ob die Markierungen korrekt ausgerichtet sind")
        else:
            print(f"❌ Positions-Test fehlgeschlagen: {result['error']}")
            
    except Exception as e:
        print(f"❌ Test-Fehler: {e}")

if __name__ == "__main__":
    print("🔧 DRUCKER-KALIBRIERUNGS-TOOL")
    print()
    print("Optionen:")
    print("1. Vollständige Kalibrierung (empfohlen)")
    print("2. Schneller Positions-Test")
    print("3. Beide")
    print()
    
    choice = input("Wähle Option (1-3): ").strip()
    
    if choice == "1":
        printer_reset_calibration()
    elif choice == "2":
        quick_position_test()
    elif choice == "3":
        quick_position_test()
        print("\n" + "="*30)
        printer_reset_calibration()
    else:
        print("❌ Ungültige Option")
    
    print("\n🎉 Kalibrierung abgeschlossen!")
