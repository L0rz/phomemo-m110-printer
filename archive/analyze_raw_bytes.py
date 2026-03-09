#!/usr/bin/env python3
"""
RAW-BYTE-ANALYSE-TOOL für Windows
Analysiert die problem_image_raw.bin auf Bit-Level
"""

import sys
import os

def analyze_raw_bytes(filename):
    """Analysiert RAW-Bytes auf Verschiebungsmuster"""
    print("ANALYZING RAW BYTES:")
    print(f"File: {filename}")
    
    try:
        with open(filename, 'rb') as f:
            data = f.read()
        
        print(f"Total size: {len(data)} bytes")
        
        # Berechne Zeilen
        BYTES_PER_LINE = 48
        total_lines = len(data) // BYTES_PER_LINE
        
        print(f"Total lines: {total_lines}")
        print(f"Bytes per line: {BYTES_PER_LINE}")
        
        # Analysiere Zeile 80 und Umgebung
        print("\nCRITICAL AREA ANALYSIS (Lines 75-85):")
        
        for line_num in range(75, min(86, total_lines)):
            line_start = line_num * BYTES_PER_LINE
            line_end = line_start + BYTES_PER_LINE
            
            if line_end <= len(data):
                line_data = data[line_start:line_end]
                
                # Hex-Darstellung der ersten 16 Bytes
                hex_data = ' '.join(f'{b:02x}' for b in line_data[:16])
                
                # Anzahl nicht-null Bytes
                non_zero = sum(1 for b in line_data if b != 0)
                
                # Spezielle Markierung für Zeile 80
                marker = " WARNING CRITICAL!" if line_num == 80 else ""
                
                print(f"Line {line_num:3d}: {hex_data}... ({non_zero:2d} non-zero){marker}")
        
        # Suche nach Mustern
        print("\nPATTERN ANALYSIS:")
        
        # Prüfe auf wiederholende Muster
        patterns_found = {}
        
        for line_num in range(min(100, total_lines)):
            line_start = line_num * BYTES_PER_LINE
            line_end = line_start + BYTES_PER_LINE
            
            if line_end <= len(data):
                line_data = data[line_start:line_end]
                
                # Ersten 4 Bytes als Muster
                pattern = line_data[:4]
                pattern_hex = ''.join(f'{b:02x}' for b in pattern)
                
                if pattern_hex in patterns_found:
                    patterns_found[pattern_hex].append(line_num)
                else:
                    patterns_found[pattern_hex] = [line_num]
        
        # Zeige häufige Muster
        print("Most common patterns (first 4 bytes):")
        sorted_patterns = sorted(patterns_found.items(), key=lambda x: len(x[1]), reverse=True)
        
        for pattern, lines in sorted_patterns[:10]:
            if len(lines) > 1:
                print(f"   {pattern}: appears in {len(lines)} lines {lines[:5]}{'...' if len(lines) > 5 else ''}")
        
        # Analysiere Byte-Shifts
        print("\nBYTE-SHIFT ANALYSIS:")
        
        # Vergleiche aufeinanderfolgende Zeilen
        shifts_detected = 0
        
        for line_num in range(1, min(total_lines, 100)):
            prev_line_start = (line_num - 1) * BYTES_PER_LINE
            curr_line_start = line_num * BYTES_PER_LINE
            
            prev_line = data[prev_line_start:prev_line_start + BYTES_PER_LINE]
            curr_line = data[curr_line_start:curr_line_start + BYTES_PER_LINE]
            
            # Suche nach ähnlichen Mustern mit Verschiebung
            for shift in range(1, 8):  # Teste 1-7 Byte Verschiebungen
                if len(prev_line) >= shift:
                    shifted_prev = prev_line[shift:] + b'\x00' * shift
                    
                    # Vergleiche mit aktueller Zeile
                    matches = sum(1 for i in range(len(curr_line)) if curr_line[i] == shifted_prev[i])
                    match_ratio = matches / len(curr_line)
                    
                    if match_ratio > 0.7:  # 70% Übereinstimmung
                        shifts_detected += 1
                        print(f"   Line {line_num}: {shift}-byte shift detected (match: {match_ratio:.1%})")
        
        if shifts_detected > 0:
            print(f"\nWARNING TOTAL SHIFTS DETECTED: {shifts_detected}")
        else:
            print("\nSUCCESS NO OBVIOUS BYTE-SHIFTS DETECTED")
        
        # Erstelle vereinfachte Visualisierung
        print("\nLINE VISUALIZATION (first 20 lines, first 8 bytes each):")
        for line_num in range(min(20, total_lines)):
            line_start = line_num * BYTES_PER_LINE
            line_end = line_start + BYTES_PER_LINE
            
            if line_end <= len(data):
                line_data = data[line_start:line_end]
                hex_short = ' '.join(f'{b:02x}' for b in line_data[:8])
                print(f"   {line_num:2d}: {hex_short}")
        
        return True
        
    except FileNotFoundError:
        print(f"ERROR File not found: {filename}")
        print("HINT Make sure you've transferred the file from Raspberry Pi!")
        return False
    except Exception as e:
        print(f"ERROR Analysis error: {e}")
        return False

def main():
    """Hauptfunktion für RAW-Byte-Analyse"""
    print("=" * 60)
    print("PHOMEMO M110 - RAW BYTE ANALYSIS TOOL")
    print("=" * 60)
    
    # Standard-Dateiname
    filename = "problem_image_raw.bin"
    
    # Prüfe ob Datei existiert
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    
    if not os.path.exists(filename):
        print(f"ERROR File '{filename}' not found!")
        print("\nTRANSFER INSTRUCTIONS:")
        print("1. SCP method:")
        print("   scp pi@[RASPBERRY_IP]:/path/to/problem_image_raw.bin .")
        print("\n2. HTTP method:")
        print("   On Raspberry: python3 -m http.server 8000")
        print("   Download: http://[RASPBERRY_IP]:8000/problem_image_raw.bin")
        print("\n3. Then run: python", sys.argv[0], "[filename]")
        return
    
    # Analysiere die Datei
    success = analyze_raw_bytes(filename)
    
    if success:
        print("\nSUCCESS RAW BYTE ANALYSIS COMPLETED!")
        print("Key insights:")
        print("   • Look for repeated patterns indicating shifts")
        print("   • Check if line 80 has unusual byte patterns")
        print("   • Byte-shift detection shows systematic errors")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
