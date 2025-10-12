#!/usr/bin/env python3
"""
Bitstream Analyse Tool für Phomemo M110 Drucker

Analysiert die Raw-Bilddaten und erstellt detaillierte Reports über:
- Bit-Komplexität
- Byte-Verteilung
- Zeilen-für-Zeilen Analyse
- Muster-Erkennung
"""

import os
import sys
import logging
from datetime import datetime
from PIL import Image
import io

# Füge Parent-Directory zum Path hinzu
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from printer_controller import EnhancedPhomemoM110
from config import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BitstreamAnalyzer:
    """Analysiert Bitstreams für den Drucker"""
    
    def __init__(self, printer_width_pixels=384, bytes_per_line=48):
        self.width_pixels = printer_width_pixels
        self.bytes_per_line = bytes_per_line
    
    def analyze_image_to_bitstream(self, image_path: str, output_dir: str = "bitstream_analysis"):
        """
        Analysiert ein Bild und erstellt detaillierte Bitstream-Reports
        
        Args:
            image_path: Pfad zum Bild
            output_dir: Verzeichnis für Ausgabedateien
        """
        try:
            # Output-Verzeichnis erstellen
            os.makedirs(output_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            
            logger.info(f"📊 Analysiere Bild: {image_path}")
            
            # Bild laden
            img = Image.open(image_path)
            logger.info(f"✅ Bild geladen: {img.size}, Mode: {img.mode}")
            
            # Zu S/W konvertieren
            if img.mode != '1':
                img = img.convert('1')
            
            # Auf Drucker-Breite anpassen
            if img.width != self.width_pixels:
                logger.info(f"🔧 Resize: {img.width}px -> {self.width_pixels}px")
                img = img.resize((self.width_pixels, img.height), Image.Resampling.LANCZOS)
            
            # Zu Drucker-Format konvertieren
            width, height = img.size
            pixels = list(img.getdata())
            
            # Bitstream generieren
            image_bytes = []
            line_stats = []
            
            for y in range(height):
                line_bytes = [0] * self.bytes_per_line
                line_set_bits = 0
                
                for pixel_x in range(self.width_pixels):
                    pixel_idx = y * width + pixel_x
                    
                    if pixel_idx < len(pixels):
                        pixel_value = pixels[pixel_idx]
                    else:
                        pixel_value = 1  # Weiß
                    
                    byte_index = pixel_x // 8
                    bit_index = pixel_x % 8
                    
                    if pixel_value == 0:  # Schwarz
                        line_bytes[byte_index] |= (1 << (7 - bit_index))
                        line_set_bits += 1
                
                image_bytes.extend(line_bytes)
                
                # Zeilen-Statistik
                line_stats.append({
                    'line': y,
                    'set_bits': line_set_bits,
                    'complexity': line_set_bits / self.width_pixels,
                    'bytes': bytes(line_bytes)
                })
            
            final_bytes = bytes(image_bytes)
            
            # === ANALYSE 1: Gesamtstatistik ===
            total_bits = len(final_bytes) * 8
            total_set_bits = sum(bin(b).count('1') for b in final_bytes)
            overall_complexity = total_set_bits / total_bits
            
            stats_file = os.path.join(output_dir, f"{base_name}_{timestamp}_stats.txt")
            with open(stats_file, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write(f"BITSTREAM ANALYSE: {base_name}\n")
                f.write("=" * 80 + "\n\n")
                
                f.write("📊 GESAMTSTATISTIK\n")
                f.write("-" * 80 + "\n")
                f.write(f"Bildgröße:           {width}x{height} Pixel\n")
                f.write(f"Datengröße:          {len(final_bytes)} Bytes\n")
                f.write(f"Zeilen:              {height}\n")
                f.write(f"Bytes pro Zeile:     {self.bytes_per_line}\n")
                f.write(f"Gesamte Bits:        {total_bits}\n")
                f.write(f"Gesetzte Bits:       {total_set_bits}\n")
                f.write(f"Komplexität:         {overall_complexity*100:.2f}%\n")
                f.write(f"NULL-Bytes (0x00):   {final_bytes.count(0)}\n")
                f.write(f"VOLL-Bytes (0xFF):   {final_bytes.count(255)}\n")
                f.write("\n")
                
                # Byte-Verteilung
                f.write("📊 BYTE-VERTEILUNG\n")
                f.write("-" * 80 + "\n")
                byte_counts = {}
                for b in final_bytes:
                    byte_counts[b] = byte_counts.get(b, 0) + 1
                
                # Top 10 häufigste Bytes
                top_bytes = sorted(byte_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                for byte_val, count in top_bytes:
                    percentage = (count / len(final_bytes)) * 100
                    f.write(f"  0x{byte_val:02X}: {count:6d} mal ({percentage:5.2f}%)  {bin(byte_val)}\n")
                f.write("\n")
                
                # Zeilen-für-Zeilen Analyse
                f.write("📊 ZEILEN-FÜR-ZEILEN KOMPLEXITÄT\n")
                f.write("-" * 80 + "\n")
                f.write(f"{'Zeile':>6} | {'Set Bits':>8} | {'Komplexität':>11} | Bemerkung\n")
                f.write("-" * 80 + "\n")
                
                for stats in line_stats:
                    line = stats['line']
                    set_bits = stats['set_bits']
                    complexity = stats['complexity']
                    
                    # Bemerkung
                    if complexity < 0.01:
                        remark = "fast leer"
                    elif complexity < 0.05:
                        remark = "sehr einfach"
                    elif complexity < 0.15:
                        remark = "einfach"
                    elif complexity < 0.30:
                        remark = "mittel"
                    elif complexity < 0.50:
                        remark = "komplex"
                    else:
                        remark = "SEHR KOMPLEX!"
                    
                    f.write(f"{line:6d} | {set_bits:8d} | {complexity*100:9.2f}% | {remark}\n")
                
                f.write("\n")
                
                # Komplexitäts-Statistik
                complexities = [s['complexity'] for s in line_stats]
                avg_complexity = sum(complexities) / len(complexities)
                min_complexity = min(complexities)
                max_complexity = max(complexities)
                
                f.write("📊 KOMPLEXITÄTS-ÜBERSICHT\n")
                f.write("-" * 80 + "\n")
                f.write(f"Durchschnitt:        {avg_complexity*100:.2f}%\n")
                f.write(f"Minimum:             {min_complexity*100:.2f}%\n")
                f.write(f"Maximum:             {max_complexity*100:.2f}%\n")
                f.write(f"Standardabweichung:  {self._std_dev(complexities)*100:.2f}%\n")
                f.write("\n")
                
                # Empfehlung
                f.write("💡 EMPFEHLUNG FÜR ÜBERTRAGUNGSGESCHWINDIGKEIT\n")
                f.write("-" * 80 + "\n")
                if overall_complexity < 0.02:
                    f.write("ULTRA_FAST: Sehr einfaches Bild, schnellste Übertragung möglich\n")
                elif overall_complexity < 0.05:
                    f.write("FAST: Einfaches Bild, schnelle Übertragung\n")
                elif overall_complexity < 0.08:
                    f.write("NORMAL: Mittlere Komplexität, normale Geschwindigkeit\n")
                elif overall_complexity < 0.12:
                    f.write("SLOW: Komplexes Bild, langsamere Übertragung empfohlen\n")
                else:
                    f.write("ULTRA_SLOW: Sehr komplexes Bild, langsamste Übertragung erforderlich\n")
                f.write("\n")
            
            logger.info(f"✅ Statistik geschrieben: {stats_file}")
            
            # === ANALYSE 2: Raw Bitstream ===
            raw_file = os.path.join(output_dir, f"{base_name}_{timestamp}_raw.bin")
            with open(raw_file, 'wb') as f:
                f.write(final_bytes)
            logger.info(f"✅ Raw Bitstream: {raw_file}")
            
            # === ANALYSE 3: Hex Dump ===
            hex_file = os.path.join(output_dir, f"{base_name}_{timestamp}_hex.txt")
            with open(hex_file, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write(f"HEX DUMP: {base_name}\n")
                f.write("=" * 80 + "\n\n")
                
                # Zeile für Zeile im Hex-Format
                for line_num, stats in enumerate(line_stats):
                    f.write(f"Zeile {line_num:4d} (Komplexität: {stats['complexity']*100:5.2f}%):\n")
                    
                    # Hex-Dump dieser Zeile
                    line_bytes = stats['bytes']
                    for i in range(0, len(line_bytes), 16):
                        chunk = line_bytes[i:i+16]
                        
                        # Hex-Darstellung
                        hex_str = ' '.join(f'{b:02X}' for b in chunk)
                        
                        # ASCII-Darstellung (. für nicht druckbare Zeichen)
                        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
                        
                        f.write(f"  {i:04X}:  {hex_str:<48}  |{ascii_str}|\n")
                    
                    f.write("\n")
            
            logger.info(f"✅ Hex Dump: {hex_file}")
            
            # === ANALYSE 4: Bit-Visualisierung ===
            bit_viz_file = os.path.join(output_dir, f"{base_name}_{timestamp}_bitviz.txt")
            with open(bit_viz_file, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write(f"BIT-VISUALISIERUNG: {base_name}\n")
                f.write("=" * 80 + "\n\n")
                f.write("Legende: █ = gesetztes Bit (schwarz), · = Null-Bit (weiß)\n\n")
                
                # Erste 50 Zeilen visualisieren
                for line_num in range(min(50, height)):
                    stats = line_stats[line_num]
                    f.write(f"Zeile {line_num:4d}: ")
                    
                    line_bytes = stats['bytes']
                    for byte in line_bytes:
                        # Jedes Bit visualisieren
                        for bit in range(8):
                            if byte & (1 << (7 - bit)):
                                f.write('█')
                            else:
                                f.write('·')
                    
                    f.write(f"  ({stats['complexity']*100:5.2f}%)\n")
                
                if height > 50:
                    f.write(f"\n... ({height - 50} weitere Zeilen)\n")
            
            logger.info(f"✅ Bit-Visualisierung: {bit_viz_file}")
            
            # === ZUSAMMENFASSUNG ===
            print("\n" + "=" * 80)
            print("✅ ANALYSE ABGESCHLOSSEN")
            print("=" * 80)
            print(f"📁 Ausgabeverzeichnis: {output_dir}")
            print(f"📊 Statistik:          {stats_file}")
            print(f"💾 Raw Bitstream:      {raw_file}")
            print(f"🔢 Hex Dump:           {hex_file}")
            print(f"👁️  Bit-Visualisierung: {bit_viz_file}")
            print("\n📊 KURZSTATISTIK:")
            print(f"   Bildgröße:     {width}x{height}")
            print(f"   Datengröße:    {len(final_bytes)} Bytes")
            print(f"   Komplexität:   {overall_complexity*100:.2f}%")
            print(f"   Gesetzte Bits: {total_set_bits}/{total_bits}")
            print("=" * 80 + "\n")
            
            return {
                'success': True,
                'stats_file': stats_file,
                'raw_file': raw_file,
                'hex_file': hex_file,
                'complexity': overall_complexity
            }
            
        except Exception as e:
            logger.error(f"❌ Analyse-Fehler: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {'success': False, 'error': str(e)}
    
    def _std_dev(self, values):
        """Berechnet Standardabweichung"""
        if not values:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def compare_bitstreams(self, file1: str, file2: str, output_file: str = "bitstream_comparison.txt"):
        """Vergleicht zwei Bitstream-Dateien"""
        try:
            with open(file1, 'rb') as f:
                data1 = f.read()
            with open(file2, 'rb') as f:
                data2 = f.read()
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("BITSTREAM VERGLEICH\n")
                f.write("=" * 80 + "\n\n")
                
                f.write(f"Datei 1: {file1}\n")
                f.write(f"Größe 1: {len(data1)} Bytes\n\n")
                f.write(f"Datei 2: {file2}\n")
                f.write(f"Größe 2: {len(data2)} Bytes\n\n")
                
                if len(data1) != len(data2):
                    f.write("⚠️ WARNUNG: Unterschiedliche Dateigrößen!\n\n")
                
                # Byte-für-Byte Vergleich
                differences = 0
                min_len = min(len(data1), len(data2))
                
                f.write("UNTERSCHIEDE:\n")
                f.write("-" * 80 + "\n")
                
                for i in range(min_len):
                    if data1[i] != data2[i]:
                        differences += 1
                        f.write(f"Position {i:6d}: 0x{data1[i]:02X} != 0x{data2[i]:02X}  "
                               f"(Diff: {abs(data1[i] - data2[i])} Bits unterschiedlich)\n")
                        
                        if differences > 100:  # Nur erste 100 anzeigen
                            f.write(f"\n... ({differences} weitere Unterschiede gefunden)\n")
                            break
                
                f.write(f"\nGESAMT: {differences} von {min_len} Bytes unterschiedlich ({differences/min_len*100:.2f}%)\n")
            
            logger.info(f"✅ Vergleich geschrieben: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Vergleichs-Fehler: {e}")
            return False


def main():
    """Hauptprogramm"""
    print("=" * 80)
    print("BITSTREAM ANALYSE TOOL")
    print("=" * 80)
    print()
    
    if len(sys.argv) < 2:
        print("VERWENDUNG:")
        print("  python analyze_bitstream.py <bild.png>")
        print("  python analyze_bitstream.py <bild1.png> --compare <bild2.png>")
        print()
        print("BEISPIELE:")
        print("  python analyze_bitstream.py test.png")
        print("  python analyze_bitstream.py normal.png --compare scharf.png")
        sys.exit(1)
    
    analyzer = BitstreamAnalyzer()
    
    # Vergleichsmodus?
    if '--compare' in sys.argv:
        idx = sys.argv.index('--compare')
        if idx + 1 < len(sys.argv):
            image1 = sys.argv[1]
            image2 = sys.argv[idx + 1]
            
            print(f"📊 Analysiere und vergleiche:")
            print(f"   Bild 1: {image1}")
            print(f"   Bild 2: {image2}")
            print()
            
            # Beide Bilder analysieren
            result1 = analyzer.analyze_image_to_bitstream(image1, "bitstream_analysis/image1")
            result2 = analyzer.analyze_image_to_bitstream(image2, "bitstream_analysis/image2")
            
            # Bitstreams vergleichen
            if result1['success'] and result2['success']:
                analyzer.compare_bitstreams(
                    result1['raw_file'],
                    result2['raw_file'],
                    "bitstream_analysis/comparison.txt"
                )
        else:
            print("❌ Fehler: Kein zweites Bild für Vergleich angegeben")
            sys.exit(1)
    else:
        # Einzelnes Bild analysieren
        image_path = sys.argv[1]
        
        if not os.path.exists(image_path):
            print(f"❌ Fehler: Datei nicht gefunden: {image_path}")
            sys.exit(1)
        
        analyzer.analyze_image_to_bitstream(image_path)


if __name__ == "__main__":
    main()
