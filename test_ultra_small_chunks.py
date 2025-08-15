#!/usr/bin/env python3
"""
Ultra Small Chunk Test
Testet die ultra-kleinen 64-Byte Chunks für kontinuierliche Zeichen-Sequenzen
"""

import requests
import time

BASE_URL = "http://localhost:8080"

def test_problematic_sequences():
    """Testet die spezifisch problematischen Sequenzen"""
    print("🎯 ULTRA SMALL CHUNK TEST")
    print("=" * 60)
    print("📦 Testet 64-Byte Chunks für kontinuierliche Zeichen-Sequenzen")
    print("🎯 Fokus auf: A-Z, Dashes, lange Zeichen-Ketten")
    print("=" * 60)
    
    # Die spezifisch problematischen Sequenzen
    problematic_tests = [
        {
            'name': 'Alphabet Full A-Z',
            'text': '''ALPHABET FULL TEST

ABCDEFGHIJKLMNOPQRSTUVWXYZ

Position: Korrekt?''',
            'description': 'War problematisch - Test 3 aus vorherigem Test'
        },
        {
            'name': 'Extended Alphabet',
            'text': '''EXTENDED ALPHABET TEST

ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789

Position: Korrekt?''',
            'description': 'War problematisch - Test 4 aus vorherigem Test'
        },
        {
            'name': 'Dashes Pattern',
            'text': '''DASHES PATTERN TEST

- - - - - - - - - - - - - - - -

Position: Korrekt?''',
            'description': 'War problematisch - Erste Zeile mit Fehlern'
        },
        {
            'name': 'Multiple Dense Lines',
            'text': '''MULTIPLE DENSE LINES

ABCDEFGHIJKLMNOPQRSTUVWXYZ
1234567890123456789012345
- - - - - - - - - - - - - - -
AAAAAAAAAAAAAAAAAAAAAAAAA

Alle korrekt positioniert?''',
            'description': 'Kombiniert alle problematischen Elemente'
        }
    ]
    
    for i, test in enumerate(problematic_tests, 1):
        print(f"\n{i}️⃣ {test['name'].upper()}")
        print(f"   📋 {test['description']}")
        
        try:
            response = requests.post(f"{BASE_URL}/api/print-text", data={
                'text': test['text'],
                'font_size': '16',
                'alignment': 'left',
                'immediate': 'true'
            })
            result = response.json()
            
            if result['success']:
                print(f"   ✅ {test['name']} erfolgreich gedruckt")
                print("   📋 KRITISCH: Prüfe Position - war vorher problematisch!")
                
                if 'A-Z' in test['name'] or 'Alphabet' in test['name']:
                    print("   🔤 Spezial-Check: Ist A-Z vollständig und korrekt positioniert?")
                elif 'Dashes' in test['name']:
                    print("   ➖ Spezial-Check: Sind die Striche in der ersten Zeile korrekt?")
                elif 'Multiple' in test['name']:
                    print("   📏 Spezial-Check: Sind ALLE 4 dichten Zeilen gleich positioniert?")
                    
            else:
                print(f"   ❌ {test['name']} fehlgeschlagen: {result['error']}")
                
            # Längere Pause zwischen kritischen Tests
            if i < len(problematic_tests):
                print(f"   ⏱️ Stabilisierungs-Pause vor nächstem Test...")
                time.sleep(4.0)  # Noch längere Pause
                
        except Exception as e:
            print(f"   ❌ {test['name']} Fehler: {e}")

def test_chunk_size_effectiveness():
    """Testet die Effektivität der 64-Byte Chunks"""
    print("\n📦 CHUNK-GRÖSSEN-EFFEKTIVITÄTS-TEST")
    print("=" * 50)
    print("   Vergleicht die Verbesserung durch ultra-kleine Chunks")
    
    # Baseline-Test (sollte funktionieren)
    print("\n   🔹 Baseline (kurze Zeile, sollte immer funktionieren):")
    test_baseline()
    
    # Stress-Test (die kritischste Sequenz)
    print("\n   🔸 Stress-Test (längste kritische Sequenz):")
    test_stress_sequence()

def test_baseline():
    """Baseline-Test mit kurzer, unkritischer Sequenz"""
    try:
        response = requests.post(f"{BASE_URL}/api/print-text", data={
            'text': 'BASELINE: ABC DEF GHI\nShort and safe',
            'font_size': '16',
            'alignment': 'left',
            'immediate': 'true'
        })
        result = response.json()
        
        status = "✅" if result['success'] else "❌"
        print(f"      {status} Baseline-Test (sollte immer funktionieren)")
        
    except Exception as e:
        print(f"      ❌ Baseline-Fehler: {e}")

def test_stress_sequence():
    """Stress-Test mit der längsten kritischen Sequenz"""
    try:
        stress_text = '''ULTRA-STRESS-TEST

ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ
----------------------------------------------------------------
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

Ultra-kleine 64-Byte Chunks aktiv'''

        response = requests.post(f"{BASE_URL}/api/print-text", data={
            'text': stress_text,
            'font_size': '14',
            'alignment': 'left',
            'immediate': 'true'
        })
        result = response.json()
        
        status = "✅" if result['success'] else "❌"
        print(f"      {status} Ultra-Stress-Test")
        
        if result['success']:
            print("      🎉 ULTRA-KRITISCH: Längste Sequenz erfolgreich!")
            print("      📋 Wenn das funktioniert, sind alle Probleme gelöst!")
        else:
            print(f"      💬 Stress-Fehler: {result['error']}")
            print("      ⚠️ Braucht eventuell noch kleinere Chunks")
            
    except Exception as e:
        print(f"      ❌ Stress-Test Fehler: {e}")

def analyze_ultra_small_results():
    """Analysiert die Ultra-Small-Chunk-Ergebnisse"""
    print("\n" + "="*60)
    print("📊 ULTRA-SMALL-CHUNK ERGEBNIS-ANALYSE")
    print()
    print("🔍 Vergleiche mit vorherigen Ergebnissen:")
    print("   VORHER (128-Byte Chunks):")
    print("   ❌ Alphabet-Test 3 & 4: Fehler")
    print("   ❌ Pattern Dashes: Fehler in erster Zeile")
    print()
    print("   NACHHER (64-Byte Chunks):")
    print("   ❓ Alphabet Full A-Z: ?")
    print("   ❓ Extended Alphabet: ?")
    print("   ❓ Dashes Pattern: ?")
    print("   ❓ Multiple Dense Lines: ?")
    print()
    
    answer = input("❓ Sind ALLE problematischen Tests jetzt erfolgreich? (y/n): ").lower().strip()
    
    if answer == 'y':
        print("\n🎉 ULTRA-SMALL-CHUNKS ERFOLGREICH!")
        print("✅ 64-Byte Chunks lösen das kontinuierliche Sequenz-Problem!")
        print("🔧 Ultra-kleine Chunks + 10 Retries + längere Pausen = Perfekt!")
        print()
        print("📋 Gelöste Probleme:")
        print("   ✅ A-Z Alphabet-Zeilen")
        print("   ✅ Dash-Pattern in erster Zeile")
        print("   ✅ Lange Zeichen-Sequenzen")
        print("   ✅ Dense horizontale Bereiche")
        
    elif answer == 'n':
        print("\n⚠️ WEITERE OPTIMIERUNG NÖTIG")
        print("🔧 Noch kleinere Chunks erforderlich")
        suggest_even_smaller_chunks()
        
    else:
        print("\n⚠️ Unklare Bewertung - visueller Check empfohlen")

def suggest_even_smaller_chunks():
    """Vorschläge für noch kleinere Chunks"""
    print("\n🛠️ NOCH-KLEINERE-CHUNKS-VORSCHLÄGE:")
    print("1. Chunk-Größe auf 32 Bytes reduzieren")
    print("2. Chunk-Größe auf 16 Bytes (extrem konservativ)")
    print("3. Adaptive Chunk-Größe: 32 Bytes für dichte, 64 für normale Bereiche")
    print("4. Noch längere Pausen: 0.1s zwischen Chunks")
    print("5. Hardware-Reset zwischen kritischen Drucken")

def quick_verification():
    """Schnelle Verifikation der kritischsten Sequenz"""
    print("\n⚡ SCHNELLE VERIFIKATION")
    print("   Teste nur die kritischste A-Z Sequenz...")
    
    try:
        response = requests.post(f"{BASE_URL}/api/print-text", data={
            'text': 'VERIFIKATION\n\nABCDEFGHIJKLMNOPQRSTUVWXYZ\n\n64-Byte Chunks',
            'font_size': '16',
            'alignment': 'left',
            'immediate': 'true'
        })
        result = response.json()
        
        if result['success']:
            print("   ✅ A-Z Verifikation erfolgreich")
            print("   📋 Das war die kritischste Sequenz!")
        else:
            print(f"   ❌ A-Z Verifikation fehlgeschlagen: {result['error']}")
            
    except Exception as e:
        print(f"   ❌ Verifikations-Fehler: {e}")

if __name__ == "__main__":
    print("📦 ULTRA SMALL CHUNK TESTER")
    print("🎯 Testet 64-Byte Chunks für kontinuierliche Zeichen-Sequenzen")
    print()
    
    test_problematic_sequences()
    test_chunk_size_effectiveness()
    analyze_ultra_small_results()
    
    # Optional: Schnelle Verifikation
    answer = input("\n❓ Schnelle A-Z Verifikation? (y/N): ")
    if answer.lower() == 'y':
        quick_verification()
    
    print("\n🎉 Ultra Small Chunk Test abgeschlossen!")
    print("📦 64-Byte Chunks sollten alle kontinuierlichen Sequenz-Probleme lösen.")
