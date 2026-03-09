#!/usr/bin/env python3
"""
Komplexitäts-Reduzierer für Phomemo M110 Drucker

Verschiedene Methoden um die Bild-Komplexität zu reduzieren und
damit Druck-Fehler zu vermeiden
"""

import os
import sys
from PIL import Image, ImageEnhance, ImageFilter
import argparse


class ComplexityReducer:
    """Reduziert Bild-Komplexität für zuverlässigeren Druck"""
    
    def __init__(self):
        self.methods = {
            'threshold': 'Einfacher Schwellwert (kein Dithering)',
            'reduce_dither': 'Reduziertes Dithering',
            'increase_brightness': 'Helligkeit erhöhen',
            'reduce_contrast': 'Kontrast reduzieren',
            'blur': 'Leichtes Weichzeichnen',
            'erosion': 'Morphologische Erosion (dünnt Schwarz aus)',
            'combined': 'Kombinierte Methode (empfohlen)'
        }
    
    def list_methods(self):
        """Listet alle verfügbaren Methoden auf"""
        print("\n" + "=" * 80)
        print("📊 VERFÜGBARE KOMPLEXITÄTS-REDUKTIONS-METHODEN")
        print("=" * 80)
        
        for key, description in self.methods.items():
            print(f"\n{key:20s} - {description}")
        
        print("\n" + "=" * 80 + "\n")
    
    def method_threshold(self, img, threshold=140):
        """
        Methode 1: Einfacher Schwellwert - KEIN Dithering
        
        Am effektivsten für Komplexitäts-Reduktion!
        Wandelt alles über dem Schwellwert in Weiß um.
        """
        print(f"⚙️  Anwende: Threshold (Schwellwert={threshold})")
        
        # In Graustufen
        if img.mode != 'L':
            img = img.convert('L')
        
        # Threshold anwenden
        img = img.point(lambda x: 0 if x < threshold else 255, '1')
        
        return img
    
    def method_reduce_dither(self, img, strength=0.5):
        """
        Methode 2: Reduziertes Dithering
        
        Behält Dithering bei, aber mit reduzierter Stärke
        """
        print(f"⚙️  Anwende: Reduziertes Dithering (Stärke={strength})")
        
        # Helligkeit erhöhen vor Dithering
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.0 + (1.0 - strength))
        
        # Dithering mit Floyd-Steinberg
        img = img.convert('1', dither=Image.Dither.FLOYDSTEINBERG)
        
        return img
    
    def method_increase_brightness(self, img, factor=1.3):
        """
        Methode 3: Helligkeit erhöhen
        
        Macht dunkle Bereiche heller → weniger schwarze Pixel
        """
        print(f"⚙️  Anwende: Helligkeit erhöhen (Faktor={factor})")
        
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(factor)
        
        # Mit Dithering zu S/W
        img = img.convert('1', dither=Image.Dither.FLOYDSTEINBERG)
        
        return img
    
    def method_reduce_contrast(self, img, factor=0.7):
        """
        Methode 4: Kontrast reduzieren
        
        Reduziert extreme Schwarz/Weiß-Unterschiede
        """
        print(f"⚙️  Anwende: Kontrast reduzieren (Faktor={factor})")
        
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(factor)
        
        # Mit Dithering zu S/W
        img = img.convert('1', dither=Image.Dither.FLOYDSTEINBERG)
        
        return img
    
    def method_blur(self, img, radius=1):
        """
        Methode 5: Leichtes Weichzeichnen
        
        Reduziert feine Details und damit Komplexität
        """
        print(f"⚙️  Anwende: Weichzeichnen (Radius={radius})")
        
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Gaussian Blur
        img = img.filter(ImageFilter.GaussianBlur(radius=radius))
        
        # Mit Dithering zu S/W
        img = img.convert('1', dither=Image.Dither.FLOYDSTEINBERG)
        
        return img
    
    def method_erosion(self, img, iterations=1):
        """
        Methode 6: Morphologische Erosion
        
        "Erodiert" schwarze Bereiche, macht sie dünner
        ACHTUNG: Kann Details verlieren!
        """
        print(f"⚙️  Anwende: Erosion (Iterationen={iterations})")
        
        # Zu S/W konvertieren
        if img.mode != '1':
            img = img.convert('1', dither=Image.Dither.FLOYDSTEINBERG)
        
        # Erosion (mehrfach wenn gewünscht)
        for i in range(iterations):
            img = img.filter(ImageFilter.MinFilter(3))
        
        return img
    
    def method_combined(self, img, aggressive=False):
        """
        Methode 7: Kombinierte Methode (EMPFOHLEN)
        
        Kombiniert mehrere Techniken für optimales Ergebnis
        """
        print(f"⚙️  Anwende: Kombinierte Methode (Aggressiv={aggressive})")
        
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        if aggressive:
            # AGGRESSIVE Reduktion
            print("   → Schritt 1: Starke Helligkeitserhöhung")
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.4)
            
            print("   → Schritt 2: Kontrast reduzieren")
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(0.6)
            
            print("   → Schritt 3: Weichzeichnen")
            img = img.filter(ImageFilter.GaussianBlur(radius=1.5))
            
            print("   → Schritt 4: Threshold (kein Dithering)")
            img = img.convert('L')
            img = img.point(lambda x: 0 if x < 150 else 255, '1')
        else:
            # MODERATE Reduktion
            print("   → Schritt 1: Leichte Helligkeitserhöhung")
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.2)
            
            print("   → Schritt 2: Leichtes Weichzeichnen")
            img = img.filter(ImageFilter.GaussianBlur(radius=0.8))
            
            print("   → Schritt 3: Reduziertes Dithering")
            img = img.convert('1', dither=Image.Dither.FLOYDSTEINBERG)
        
        return img
    
    def reduce_complexity(self, input_path, output_path, method='combined', **kwargs):
        """
        Reduziert die Komplexität eines Bildes
        
        Args:
            input_path: Eingabebild
            output_path: Ausgabebild
            method: Methode (siehe list_methods)
            **kwargs: Methoden-spezifische Parameter
        """
        try:
            print("\n" + "=" * 80)
            print("🔧 KOMPLEXITÄTS-REDUKTION")
            print("=" * 80)
            
            print(f"\n📂 Eingabe: {input_path}")
            print(f"📂 Ausgabe: {output_path}")
            print(f"⚙️  Methode: {method}")
            
            # Bild laden
            img = Image.open(input_path)
            print(f"\n✅ Bild geladen: {img.size}, Mode: {img.mode}")
            
            # Original-Komplexität berechnen (Schätzung)
            orig_bw = img.convert('1', dither=Image.Dither.FLOYDSTEINBERG)
            orig_pixels = list(orig_bw.getdata())
            orig_black = orig_pixels.count(0)
            orig_complexity = (orig_black / len(orig_pixels)) * 100
            
            print(f"📊 Original-Komplexität (geschätzt): {orig_complexity:.2f}%")
            
            # Methode anwenden
            if method == 'threshold':
                result = self.method_threshold(img, kwargs.get('threshold', 140))
            elif method == 'reduce_dither':
                result = self.method_reduce_dither(img, kwargs.get('strength', 0.5))
            elif method == 'increase_brightness':
                result = self.method_increase_brightness(img, kwargs.get('factor', 1.3))
            elif method == 'reduce_contrast':
                result = self.method_reduce_contrast(img, kwargs.get('factor', 0.7))
            elif method == 'blur':
                result = self.method_blur(img, kwargs.get('radius', 1))
            elif method == 'erosion':
                result = self.method_erosion(img, kwargs.get('iterations', 1))
            elif method == 'combined':
                result = self.method_combined(img, kwargs.get('aggressive', False))
            else:
                print(f"❌ Unbekannte Methode: {method}")
                return False
            
            # Neue Komplexität berechnen
            result_pixels = list(result.getdata())
            result_black = result_pixels.count(0)
            result_complexity = (result_black / len(result_pixels)) * 100
            
            print(f"📊 Neue Komplexität: {result_complexity:.2f}%")
            
            reduction = orig_complexity - result_complexity
            print(f"✅ Reduktion: {reduction:.2f}% (von {orig_complexity:.2f}% auf {result_complexity:.2f}%)")
            
            # Empfehlung
            if result_complexity < 5:
                print("💡 SEHR GUT: Sollte sehr schnell und zuverlässig drucken! ⚡")
            elif result_complexity < 8:
                print("💡 GUT: Sollte problemlos drucken ✅")
            elif result_complexity < 12:
                print("💡 OK: Normale Druckgeschwindigkeit empfohlen ⚠️")
            else:
                print("💡 NOCH HOCH: Eventuell aggressivere Reduktion nötig 🔴")
            
            # Speichern
            result.save(output_path)
            print(f"\n✅ Gespeichert: {output_path}")
            
            print("\n" + "=" * 80 + "\n")
            return True
            
        except Exception as e:
            print(f"\n❌ Fehler: {e}")
            import traceback
            print(traceback.format_exc())
            return False
    
    def batch_reduce(self, input_path, output_dir="reduced_complexity"):
        """
        Erstellt mehrere Versionen mit verschiedenen Reduktions-Methoden
        zum Vergleichen
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            
            print("\n" + "=" * 80)
            print("🔄 BATCH KOMPLEXITÄTS-REDUKTION")
            print("=" * 80)
            print(f"\nErstelle mehrere Versionen von: {input_path}")
            print(f"Ausgabeverzeichnis: {output_dir}\n")
            
            results = []
            
            # 1. Threshold verschiedene Werte
            for threshold in [120, 140, 160]:
                output = os.path.join(output_dir, f"{base_name}_threshold_{threshold}.png")
                self.reduce_complexity(input_path, output, 'threshold', threshold=threshold)
                results.append(('threshold', threshold, output))
            
            # 2. Kombiniert moderat
            output = os.path.join(output_dir, f"{base_name}_combined_moderate.png")
            self.reduce_complexity(input_path, output, 'combined', aggressive=False)
            results.append(('combined', 'moderate', output))
            
            # 3. Kombiniert aggressiv
            output = os.path.join(output_dir, f"{base_name}_combined_aggressive.png")
            self.reduce_complexity(input_path, output, 'combined', aggressive=True)
            results.append(('combined', 'aggressive', output))
            
            # 4. Helligkeit erhöhen
            output = os.path.join(output_dir, f"{base_name}_bright.png")
            self.reduce_complexity(input_path, output, 'increase_brightness', factor=1.3)
            results.append(('brightness', 1.3, output))
            
            print("\n" + "=" * 80)
            print("✅ BATCH ABGESCHLOSSEN")
            print("=" * 80)
            print(f"\n{len(results)} Versionen erstellt in: {output_dir}")
            print("\n💡 NÄCHSTE SCHRITTE:")
            print("   1. Analysiere die Versionen:")
            print(f"      python analyze_bitstream.py {output_dir}/*.png")
            print("   2. Vergleiche die Komplexität")
            print("   3. Wähle die beste Version zum Drucken")
            print("\n" + "=" * 80 + "\n")
            
            return results
            
        except Exception as e:
            print(f"\n❌ Batch-Fehler: {e}")
            return []


def main():
    parser = argparse.ArgumentParser(
        description='Reduziert Bild-Komplexität für zuverlässigeren Druck'
    )
    
    parser.add_argument('input', nargs='?', help='Eingabebild')
    parser.add_argument('-o', '--output', help='Ausgabebild')
    parser.add_argument('-m', '--method', default='combined',
                       choices=['threshold', 'reduce_dither', 'increase_brightness',
                               'reduce_contrast', 'blur', 'erosion', 'combined'],
                       help='Reduktions-Methode')
    parser.add_argument('--list', action='store_true', help='Liste alle Methoden')
    parser.add_argument('--batch', action='store_true', 
                       help='Erstelle mehrere Versionen zum Vergleichen')
    parser.add_argument('--aggressive', action='store_true',
                       help='Aggressive Reduktion (nur bei combined)')
    parser.add_argument('--threshold', type=int, default=140,
                       help='Threshold-Wert (80-200)')
    
    args = parser.parse_args()
    
    reducer = ComplexityReducer()
    
    if args.list:
        reducer.list_methods()
        return
    
    if not args.input:
        print("❌ Fehler: Kein Eingabebild angegeben")
        print("\nVERWENDUNG:")
        print("  python reduce_complexity.py <input.png>")
        print("  python reduce_complexity.py <input.png> -o <output.png>")
        print("  python reduce_complexity.py <input.png> --batch")
        print("  python reduce_complexity.py --list")
        return
    
    if args.batch:
        reducer.batch_reduce(args.input)
    else:
        if not args.output:
            base = os.path.splitext(args.input)[0]
            args.output = f"{base}_reduced.png"
        
        reducer.reduce_complexity(
            args.input,
            args.output,
            args.method,
            aggressive=args.aggressive,
            threshold=args.threshold
        )


if __name__ == "__main__":
    main()
