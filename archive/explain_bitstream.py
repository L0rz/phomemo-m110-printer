#!/usr/bin/env python3
"""
Bitstream Ergebnis-Erklärer

Liest die Analyse-Ergebnisse und erklärt sie verständlich
"""

import os
import sys
import glob
from datetime import datetime


class BitstreamExplainer:
    """Erklärt Bitstream-Analyse-Ergebnisse verständlich"""
    
    def __init__(self):
        self.analysis_dir = "bitstream_analysis"
    
    def find_latest_analysis(self):
        """Findet die neueste Analyse"""
        stats_files = glob.glob(os.path.join(self.analysis_dir, "*_stats.txt"))
        if not stats_files:
            return None
        
        # Neueste Datei
        latest = max(stats_files, key=os.path.getmtime)
        return latest
    
    def parse_stats_file(self, stats_file):
        """Parst eine Stats-Datei und extrahiert wichtige Werte"""
        try:
            with open(stats_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            data = {
                'width': 0,
                'height': 0,
                'size_bytes': 0,
                'complexity': 0.0,
                'set_bits': 0,
                'total_bits': 0,
                'null_bytes': 0,
                'full_bytes': 0,
                'recommendation': 'UNKNOWN'
            }
            
            # Extrahiere wichtige Werte
            for line in content.split('\n'):
                line = line.strip()
                
                try:
                    if 'Bildgröße:' in line and 'Pixel' in line:
                        # "Bildgröße:           384x240 Pixel"
                        parts = line.split(':')[1].strip().split('x')
                        if len(parts) >= 2:
                            data['width'] = int(parts[0])
                            data['height'] = int(parts[1].split()[0])
                    
                    elif 'Datengröße:' in line and 'Bytes' in line:
                        # "Datengröße:          11520 Bytes"
                        value_str = line.split(':')[1].strip().split()[0]
                        data['size_bytes'] = int(value_str)
                    
                    elif 'Komplexität:' in line and '%' in line and 'ÜBERSICHT' not in line and 'Durchschnitt' not in line:
                        # "Komplexität:         8.45%"
                        value_str = line.split(':')[1].strip().replace('%', '')
                        data['complexity'] = float(value_str)
                    
                    elif 'Gesetzte Bits:' in line and '/' in line:
                        # "Gesetzte Bits:       7812/92160"
                        parts = line.split(':')[1].strip().split('/')
                        if len(parts) >= 2:
                            data['set_bits'] = int(parts[0])
                            data['total_bits'] = int(parts[1])
                    
                    elif 'NULL-Bytes (0x00):' in line:
                        value_str = line.split(':')[1].strip()
                        data['null_bytes'] = int(value_str)
                    
                    elif 'VOLL-Bytes (0xFF):' in line:
                        value_str = line.split(':')[1].strip()
                        data['full_bytes'] = int(value_str)
                        
                except (ValueError, IndexError) as e:
                    # Einzelne Zeile konnte nicht geparst werden - ignorieren
                    pass
            
            # Extrahiere Empfehlung
            if 'ULTRA_FAST' in content:
                data['recommendation'] = 'ULTRA_FAST'
            elif 'FAST:' in content:
                data['recommendation'] = 'FAST'
            elif 'NORMAL:' in content:
                data['recommendation'] = 'NORMAL'
            elif 'SLOW:' in content:
                data['recommendation'] = 'SLOW'
            elif 'ULTRA_SLOW' in content:
                data['recommendation'] = 'ULTRA_SLOW'
            
            # Validierung: Mindestens Bildgröße sollte gefunden werden
            if data['width'] == 0 or data['height'] == 0:
                print(f"⚠️  Warnung: Bildgröße konnte nicht extrahiert werden")
                print(f"   Erste Zeilen der Datei:")
                lines = content.split('\n')[:10]
                for i, line in enumerate(lines, 1):
                    print(f"   {i}: {line}")
            
            return data
            
        except Exception as e:
            print(f"❌ Fehler beim Parsen: {e}")
            print(f"   Datei: {stats_file}")
            import traceback
            print(f"   Details: {traceback.format_exc()}")
            return None
    
    def explain_single_analysis(self, stats_file):
        """Erklärt eine einzelne Analyse verständlich"""
        
        print("\n" + "=" * 80)
        print("📊 BITSTREAM-ANALYSE ERKLÄRT")
        print("=" * 80)
        
        data = self.parse_stats_file(stats_file)
        if not data:
            print("❌ Konnte Analyse nicht lesen")
            return
        
        filename = os.path.basename(stats_file)
        print(f"\n📁 Datei: {filename}")
        print(f"📏 Bildgröße: {data.get('width', '?')}x{data.get('height', '?')} Pixel")
        
        # === KOMPLEXITÄT ERKLÄREN ===
        print("\n" + "=" * 80)
        print("🎯 KOMPLEXITÄT")
        print("=" * 80)
        
        complexity = data.get('complexity', 0)
        print(f"\n📊 Gemessene Komplexität: {complexity:.2f}%")
        
        print("\n💡 Was bedeutet das?")
        print("   Komplexität = Anteil der gesetzten Bits (schwarze Pixel)")
        print(f"   Von {data.get('total_bits', 0)} Bits sind {data.get('set_bits', 0)} gesetzt")
        
        # Visuelle Darstellung
        bar_length = 50
        filled = int((complexity / 100) * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"\n   [{bar}] {complexity:.2f}%")
        
        # Einordnung
        print("\n📈 Einordnung:")
        if complexity < 2:
            print("   ✅ SEHR NIEDRIG - Fast nur weiße Fläche")
            print("   → Bild hat sehr wenig Inhalt")
            print("   → Druckt sehr schnell")
        elif complexity < 5:
            print("   ✅ NIEDRIG - Einfaches Bild")
            print("   → Wenig schwarze Bereiche")
            print("   → Druckt schnell")
        elif complexity < 8:
            print("   ⚠️  MITTEL - Normales Bild")
            print("   → Ausgewogener Schwarz-Weiß-Anteil")
            print("   → Normale Druckgeschwindigkeit")
        elif complexity < 12:
            print("   ⚠️  HOCH - Komplexes Bild")
            print("   → Viele schwarze Bereiche")
            print("   → Langsamerer Druck empfohlen")
        else:
            print("   🔴 SEHR HOCH - Sehr komplexes Bild")
            print("   → Sehr viele schwarze Bereiche")
            print("   → Langsamer Druck erforderlich!")
        
        # === ÜBERTRAGUNGSGESCHWINDIGKEIT ===
        print("\n" + "=" * 80)
        print("🚀 ÜBERTRAGUNGSGESCHWINDIGKEIT")
        print("=" * 80)
        
        recommendation = data.get('recommendation', 'UNKNOWN')
        print(f"\n💡 Empfohlene Geschwindigkeit: {recommendation}")
        
        speed_info = {
            'ULTRA_FAST': {
                'emoji': '⚡',
                'description': 'Blitzschnell',
                'delay': '5ms zwischen Blöcken',
                'suitable': 'Fast leere Bilder, einzelne Linien',
                'risk': 'Minimal'
            },
            'FAST': {
                'emoji': '🚀',
                'description': 'Schnell',
                'delay': '10ms zwischen Blöcken',
                'suitable': 'Einfache Grafiken, wenig Text',
                'risk': 'Sehr gering'
            },
            'NORMAL': {
                'emoji': '✅',
                'description': 'Normal',
                'delay': '20ms zwischen Blöcken',
                'suitable': 'Die meisten Bilder',
                'risk': 'Gering'
            },
            'SLOW': {
                'emoji': '🐌',
                'description': 'Langsam',
                'delay': '50ms zwischen Blöcken',
                'suitable': 'Komplexe Bilder, viel Dithering',
                'risk': 'Mittel bei falscher Geschwindigkeit'
            },
            'ULTRA_SLOW': {
                'emoji': '🐢',
                'description': 'Sehr langsam',
                'delay': '100ms zwischen Blöcken',
                'suitable': 'Sehr dichte Bilder, fast komplett schwarz',
                'risk': 'Hoch bei falscher Geschwindigkeit'
            }
        }
        
        if recommendation in speed_info:
            info = speed_info[recommendation]
            print(f"\n{info['emoji']} {info['description']}")
            print(f"   Verzögerung: {info['delay']}")
            print(f"   Geeignet für: {info['suitable']}")
            print(f"   Fehlerrisiko: {info['risk']}")
        
        # === BYTE-ANALYSE ===
        print("\n" + "=" * 80)
        print("💾 BYTE-ANALYSE")
        print("=" * 80)
        
        total_bytes = data.get('size_bytes', 0)
        null_bytes = data.get('null_bytes', 0)
        full_bytes = data.get('full_bytes', 0)
        
        print(f"\n📦 Gesamte Bytes: {total_bytes}")
        print(f"   • NULL-Bytes (0x00): {null_bytes} ({null_bytes/total_bytes*100:.1f}%)")
        print(f"     → Komplett weiße Zeilen")
        print(f"   • VOLL-Bytes (0xFF): {full_bytes} ({full_bytes/total_bytes*100:.1f}%)")
        print(f"     → Komplett schwarze Bereiche")
        print(f"   • Gemischte Bytes: {total_bytes - null_bytes - full_bytes} ({(total_bytes - null_bytes - full_bytes)/total_bytes*100:.1f}%)")
        print(f"     → Dithering und Details")
        
        # === POTENZIELLE PROBLEME ===
        print("\n" + "=" * 80)
        print("⚠️  POTENZIELLE PROBLEME")
        print("=" * 80)
        
        problems = []
        
        if complexity > 12:
            problems.append({
                'severity': '🔴',
                'title': 'Sehr hohe Komplexität',
                'description': 'Bild könnte zu viele Daten enthalten',
                'solution': 'Verwende ULTRA_SLOW oder reduziere Dithering'
            })
        
        if complexity > 8 and recommendation == 'FAST':
            problems.append({
                'severity': '⚠️',
                'title': 'Geschwindigkeit zu schnell',
                'description': 'Empfohlene Geschwindigkeit könnte zu schnell sein',
                'solution': 'Besser NORMAL oder SLOW verwenden'
            })
        
        if null_bytes / total_bytes > 0.9:
            problems.append({
                'severity': '💡',
                'title': 'Fast leeres Bild',
                'description': 'Sehr wenig Inhalt im Bild',
                'solution': 'OK - wird sehr schnell drucken'
            })
        
        if full_bytes / total_bytes > 0.3:
            problems.append({
                'severity': '⚠️',
                'title': 'Viele vollständig schwarze Bereiche',
                'description': 'Könnte zu Timing-Problemen führen',
                'solution': 'Verwende langsame Geschwindigkeit'
            })
        
        if not problems:
            print("\n✅ Keine Probleme erkannt - sollte problemlos drucken!")
        else:
            for i, problem in enumerate(problems, 1):
                print(f"\n{problem['severity']} Problem {i}: {problem['title']}")
                print(f"   Beschreibung: {problem['description']}")
                print(f"   Lösung: {problem['solution']}")
        
        # === ZUSAMMENFASSUNG ===
        print("\n" + "=" * 80)
        print("📋 ZUSAMMENFASSUNG")
        print("=" * 80)
        
        print(f"\n✅ Analyse abgeschlossen für: {filename}")
        print(f"📊 Komplexität: {complexity:.2f}% → {self._complexity_rating(complexity)}")
        print(f"🚀 Empfohlene Geschwindigkeit: {recommendation}")
        print(f"⚠️  Potenzielle Probleme: {len(problems)}")
        
        if complexity < 8:
            print("\n💡 FAZIT: Dieses Bild sollte problemlos drucken ✅")
        elif complexity < 12:
            print("\n💡 FAZIT: Achte auf die richtige Geschwindigkeit ⚠️")
        else:
            print("\n💡 FAZIT: Vorsicht - komplexes Bild! Langsam drucken! 🔴")
        
        print("\n" + "=" * 80 + "\n")
    
    def _complexity_rating(self, complexity):
        """Gibt Rating für Komplexität zurück"""
        if complexity < 2:
            return "Sehr einfach ⚡"
        elif complexity < 5:
            return "Einfach ✅"
        elif complexity < 8:
            return "Mittel ⚠️"
        elif complexity < 12:
            return "Komplex 🐌"
        else:
            return "Sehr komplex 🔴"
    
    def compare_analyses(self, file1, file2):
        """Vergleicht zwei Analysen"""
        
        print("\n" + "=" * 80)
        print("🔍 BITSTREAM VERGLEICH")
        print("=" * 80)
        
        data1 = self.parse_stats_file(file1)
        data2 = self.parse_stats_file(file2)
        
        if not data1 or not data2:
            print("❌ Konnte Analysen nicht lesen")
            return
        
        name1 = os.path.basename(file1).replace('_stats.txt', '')
        name2 = os.path.basename(file2).replace('_stats.txt', '')
        
        print(f"\n📁 Bild 1: {name1}")
        print(f"📁 Bild 2: {name2}")
        
        # === KOMPLEXITÄTS-VERGLEICH ===
        print("\n" + "=" * 80)
        print("📊 KOMPLEXITÄTS-VERGLEICH")
        print("=" * 80)
        
        comp1 = data1.get('complexity', 0)
        comp2 = data2.get('complexity', 0)
        diff = abs(comp2 - comp1)
        
        print(f"\nBild 1: {comp1:.2f}%")
        print(f"Bild 2: {comp2:.2f}%")
        print(f"Differenz: {diff:.2f}%")
        
        if diff < 1:
            print("✅ Sehr ähnliche Komplexität")
        elif diff < 3:
            print("⚠️  Leicht unterschiedliche Komplexität")
        elif diff < 5:
            print("⚠️  Deutlich unterschiedliche Komplexität")
        else:
            print("🔴 SEHR unterschiedliche Komplexität!")
        
        # === GESCHWINDIGKEITS-VERGLEICH ===
        print("\n" + "=" * 80)
        print("🚀 GESCHWINDIGKEITS-VERGLEICH")
        print("=" * 80)
        
        speed1 = data1.get('recommendation', 'UNKNOWN')
        speed2 = data2.get('recommendation', 'UNKNOWN')
        
        print(f"\nBild 1: {speed1}")
        print(f"Bild 2: {speed2}")
        
        if speed1 == speed2:
            print("✅ Gleiche Geschwindigkeit empfohlen")
        else:
            print("⚠️  Unterschiedliche Geschwindigkeiten empfohlen!")
            print(f"   → Bild 2 benötigt {'schnellere' if self._speed_to_num(speed2) < self._speed_to_num(speed1) else 'langsamere'} Übertragung")
        
        # === WARUM UNTERSCHIED? ===
        if diff > 3 or speed1 != speed2:
            print("\n" + "=" * 80)
            print("🔍 WARUM UNTERSCHIEDLICH?")
            print("=" * 80)
            
            set_bits_diff = data2.get('set_bits', 0) - data1.get('set_bits', 0)
            
            print(f"\n• Unterschied in gesetzten Bits: {set_bits_diff:+d}")
            
            if set_bits_diff > 0:
                print("  → Bild 2 hat MEHR schwarze Pixel")
                print("  → Wahrscheinlich:")
                print("    - Höhere Dither-Stärke verwendet")
                print("    - Höherer Kontrast")
                print("    - Dunkleres Ausgangsbild")
            else:
                print("  → Bild 2 hat WENIGER schwarze Pixel")
                print("  → Wahrscheinlich:")
                print("    - Niedrigere Dither-Stärke")
                print("    - Niedrigerer Kontrast")
                print("    - Helleres Ausgangsbild")
            
            # Null/Full Bytes vergleichen
            null_diff = data2.get('null_bytes', 0) - data1.get('null_bytes', 0)
            full_diff = data2.get('full_bytes', 0) - data1.get('full_bytes', 0)
            
            print(f"\n• NULL-Bytes: {null_diff:+d}")
            print(f"• VOLL-Bytes: {full_diff:+d}")
        
        print("\n" + "=" * 80 + "\n")
    
    def _speed_to_num(self, speed):
        """Konvertiert Speed-String zu Nummer für Vergleich"""
        speed_map = {
            'ULTRA_FAST': 1,
            'FAST': 2,
            'NORMAL': 3,
            'SLOW': 4,
            'ULTRA_SLOW': 5
        }
        return speed_map.get(speed, 3)
    
    def auto_explain(self):
        """Findet und erklärt automatisch die neueste Analyse"""
        
        print("\n🔍 Suche nach Analyse-Ergebnissen...")
        
        if not os.path.exists(self.analysis_dir):
            print(f"❌ Verzeichnis nicht gefunden: {self.analysis_dir}")
            print("💡 Führe zuerst eine Analyse aus mit:")
            print("   python analyze_bitstream.py <dein_bild.png>")
            return
        
        stats_files = glob.glob(os.path.join(self.analysis_dir, "*_stats.txt"))
        
        if not stats_files:
            print(f"❌ Keine Analyse-Ergebnisse gefunden in: {self.analysis_dir}")
            print("💡 Führe zuerst eine Analyse aus mit:")
            print("   python analyze_bitstream.py <dein_bild.png>")
            return
        
        print(f"✅ Gefunden: {len(stats_files)} Analyse(n)")
        
        if len(stats_files) == 1:
            self.explain_single_analysis(stats_files[0])
        elif len(stats_files) == 2:
            print("\n💡 Zwei Analysen gefunden - vergleiche sie...")
            self.explain_single_analysis(stats_files[0])
            self.explain_single_analysis(stats_files[1])
            self.compare_analyses(stats_files[0], stats_files[1])
        else:
            # Neueste anzeigen
            latest = max(stats_files, key=os.path.getmtime)
            print(f"\n💡 Zeige neueste Analyse: {os.path.basename(latest)}")
            self.explain_single_analysis(latest)
            
            print("\n📋 Weitere verfügbare Analysen:")
            for f in sorted(stats_files, key=os.path.getmtime, reverse=True)[1:]:
                print(f"   • {os.path.basename(f)}")


def main():
    explainer = BitstreamExplainer()
    
    if len(sys.argv) < 2:
        # Auto-Modus
        explainer.auto_explain()
    elif sys.argv[1] == '--compare' and len(sys.argv) >= 4:
        # Vergleichs-Modus
        explainer.explain_single_analysis(sys.argv[2])
        explainer.explain_single_analysis(sys.argv[3])
        explainer.compare_analyses(sys.argv[2], sys.argv[3])
    else:
        # Spezifische Datei
        explainer.explain_single_analysis(sys.argv[1])


if __name__ == "__main__":
    main()
