#!/usr/bin/env python3
"""
Phomemo M110 Kalibrierungs-Tool
Druckt Kalibrierungsmuster für Offset- und Ausrichtungseinstellungen
"""

import sys
import os
import time
import logging
from PIL import Image, ImageDraw, ImageFont
from typing import Optional, Tuple
import argparse

# Versuche das Drucker-Modul zu importieren
try:
    from printer_controller import RobustPhomemoM110
except ImportError:
    # Fallback für direkten Aufruf
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    try:
        from printer_controller import RobustPhomemoM110
    except ImportError:
        print("❌ Fehler: printer_controller.py nicht gefunden!")
        print("💡 Stellen Sie sicher, dass das Script im robust_server/ Verzeichnis liegt.")
        sys.exit(1)

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PhomemoCalibration:
    def __init__(self, printer: RobustPhomemoM110):
        self.printer = printer
        self.width_pixels = 384  # Phomemo M110 Standard
        self.width_mm = 48       # 48mm physische Breite
        self.pixels_per_mm = self.width_pixels / self.width_mm  # ~8 Pixel/mm
        
        # Label-Größen (40x30mm)
        self.label_width_mm = 40
        self.label_height_mm = 30
        self.label_width_px = int(self.label_width_mm * self.pixels_per_mm)
        self.label_height_px = int(self.label_height_mm * self.pixels_per_mm)
        
        logger.info(f"Kalibrierung initialisiert: {self.width_pixels}x{self.label_height_px}px ({self.label_width_mm}x{self.label_height_mm}mm)")
    
    def create_border_test(self, border_thickness: int = 2, offset_x: int = 0, offset_y: int = 0) -> Image.Image:
        """
        Erstellt ein Rechteck am Druckrand für Kalibrierung
        
        Args:
            border_thickness: Dicke des Rahmens in Pixeln
            offset_x: Horizontaler Offset in Pixeln (negativ = links, positiv = rechts)
            offset_y: Vertikaler Offset in Pixeln (negativ = oben, positiv = unten)
        """
        # Bild mit Label-Größe erstellen
        img = Image.new('RGB', (self.width_pixels, self.label_height_px), 'white')
        draw = ImageDraw.Draw(img)
        
        # Berechne Rahmen-Position mit Offset
        margin_x = (self.width_pixels - self.label_width_px) // 2 + offset_x
        margin_y = offset_y if offset_y >= 0 else 0
        
        # Rahmen-Koordinaten
        left = margin_x
        top = margin_y
        right = margin_x + self.label_width_px - 1
        bottom = margin_y + self.label_height_px - 1
        
        # Äußerer Rahmen (schwarz)
        for i in range(border_thickness):
            draw.rectangle([left + i, top + i, right - i, bottom - i], outline='black', width=1)
        
        # Ecken-Markierungen (extra dick für bessere Sichtbarkeit)
        corner_size = 10
        corner_thickness = 3
        
        # Ecken zeichnen
        corners = [
            (left, top),                    # Oben links
            (right - corner_size, top),     # Oben rechts
            (left, bottom - corner_size),   # Unten links
            (right - corner_size, bottom - corner_size)  # Unten rechts
        ]
        
        for corner_x, corner_y in corners:
            # L-förmige Ecken-Markierung
            for t in range(corner_thickness):
                # Horizontale Linie
                draw.line([corner_x, corner_y + t, corner_x + corner_size, corner_y + t], fill='black', width=1)
                # Vertikale Linie
                draw.line([corner_x + t, corner_y, corner_x + t, corner_y + corner_size], fill='black', width=1)
        
        return img.convert('1')  # Zu schwarz-weiß konvertieren
    
    def create_grid_test(self, grid_spacing_mm: int = 5, offset_x: int = 0, offset_y: int = 0) -> Image.Image:
        """
        Erstellt ein Gitter-Muster für präzise Kalibrierung
        """
        img = Image.new('RGB', (self.width_pixels, self.label_height_px), 'white')
        draw = ImageDraw.Draw(img)
        
        grid_spacing_px = int(grid_spacing_mm * self.pixels_per_mm)
        
        # Berechne Start-Position mit Offset
        start_x = (self.width_pixels - self.label_width_px) // 2 + offset_x
        start_y = offset_y if offset_y >= 0 else 0
        
        # Vertikale Linien
        for x in range(start_x, start_x + self.label_width_px, grid_spacing_px):
            if 0 <= x < self.width_pixels:
                draw.line([x, start_y, x, start_y + self.label_height_px], fill='black', width=1)
        
        # Horizontale Linien
        for y in range(start_y, start_y + self.label_height_px, grid_spacing_px):
            if 0 <= y < self.label_height_px:
                draw.line([start_x, y, start_x + self.label_width_px, y], fill='black', width=1)
        
        # Rahmen um das Gitter
        draw.rectangle([start_x, start_y, start_x + self.label_width_px - 1, start_y + self.label_height_px - 1], 
                      outline='black', width=2)
        
        return img.convert('1')
    
    def create_measurement_rulers(self, offset_x: int = 0, offset_y: int = 0) -> Image.Image:
        """
        Erstellt Lineale zur Vermessung
        """
        img = Image.new('RGB', (self.width_pixels, self.label_height_px), 'white')
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except:
            font = ImageFont.load_default()
        
        # Start-Position berechnen
        start_x = (self.width_pixels - self.label_width_px) // 2 + offset_x
        start_y = offset_y if offset_y >= 0 else 0
        
        # Horizontales Lineal (oben)
        ruler_height = 20
        for mm in range(0, self.label_width_mm + 1, 5):
            x = start_x + int(mm * self.pixels_per_mm)
            if 0 <= x < self.width_pixels:
                # Markierung
                draw.line([x, start_y, x, start_y + ruler_height], fill='black', width=1)
                # Nummer
                if mm % 10 == 0:
                    draw.text((x - 5, start_y + 2), str(mm), fill='black', font=font)
        
        # Vertikales Lineal (links)
        ruler_width = 15
        for mm in range(0, self.label_height_mm + 1, 5):
            y = start_y + ruler_height + int(mm * self.pixels_per_mm)
            if start_y <= y < self.label_height_px:
                # Markierung
                draw.line([start_x, y, start_x + ruler_width, y], fill='black', width=1)
                # Nummer
                if mm % 10 == 0:
                    draw.text((start_x + 2, y - 8), str(mm), fill='black', font=font)
        
        # Label-Bereich markieren
        draw.rectangle([start_x + ruler_width, start_y + ruler_height, 
                       start_x + self.label_width_px - 1, start_y + ruler_height + self.label_height_px - 1], 
                      outline='black', width=1)
        
        return img.convert('1')
    
    def create_corner_test(self, corner_size: int = 15, offset_x: int = 0, offset_y: int = 0) -> Image.Image:
        """
        Erstellt L-förmige Ecken-Markierungen für präzise Ausrichtung
        """
        img = Image.new('RGB', (self.width_pixels, self.label_height_px), 'white')
        draw = ImageDraw.Draw(img)
        
        # Start-Position berechnen
        start_x = (self.width_pixels - self.label_width_px) // 2 + offset_x
        start_y = offset_y if offset_y >= 0 else 0
        
        # Ecken-Positionen
        corners = [
            (start_x, start_y, "TL"),  # Top Left
            (start_x + self.label_width_px - corner_size, start_y, "TR"),  # Top Right
            (start_x, start_y + self.label_height_px - corner_size, "BL"),  # Bottom Left
            (start_x + self.label_width_px - corner_size, start_y + self.label_height_px - corner_size, "BR")  # Bottom Right
        ]
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 10)
        except:
            font = ImageFont.load_default()
        
        for corner_x, corner_y, label in corners:
            # L-förmige Markierung (3px dick)
            for thickness in range(3):
                # Horizontale Linie
                draw.line([corner_x, corner_y + thickness, corner_x + corner_size, corner_y + thickness], 
                         fill='black', width=1)
                # Vertikale Linie
                draw.line([corner_x + thickness, corner_y, corner_x + thickness, corner_y + corner_size], 
                         fill='black', width=1)
            
            # Label hinzufügen
            text_x = corner_x + corner_size + 2
            text_y = corner_y + corner_size // 2
            draw.text((text_x, text_y), label, fill='black', font=font)
        
        # Zentrale Kreuz-Markierung
        center_x = start_x + self.label_width_px // 2
        center_y = start_y + self.label_height_px // 2
        cross_size = 8
        
        draw.line([center_x - cross_size, center_y, center_x + cross_size, center_y], fill='black', width=2)
        draw.line([center_x, center_y - cross_size, center_x, center_y + cross_size], fill='black', width=2)
        
        return img.convert('1')
    
    def create_offset_test_series(self, base_offset_x: int = 0, base_offset_y: int = 0) -> list:
        """
        Erstellt eine Serie von Offset-Tests
        """
        tests = []
        offsets = [-6, -3, 0, 3, 6]  # Verschiedene Offset-Werte
        
        for i, offset in enumerate(offsets):
            img = self.create_border_test(
                border_thickness=2,
                offset_x=base_offset_x + offset,
                offset_y=base_offset_y
            )
            tests.append((img, f"X-Offset: {base_offset_x + offset}px"))
        
        return tests
    
    def print_calibration_image(self, img: Image.Image, description: str = "") -> bool:
        """
        Druckt ein Kalibrierungsbild
        """
        try:
            logger.info(f"Drucke Kalibrierung: {description}")
            
            if not self.printer.is_connected():
                logger.warning("Drucker nicht verbunden, versuche Verbindung...")
                if not self.printer.connect_bluetooth():
                    logger.error("Bluetooth-Verbindung fehlgeschlagen!")
                    return False
            
            # Bild zu Drucker-Format konvertieren
            image_data = self.printer.image_to_printer_format(img)
            if not image_data:
                logger.error("Bildkonvertierung fehlgeschlagen!")
                return False
            
            # Drucker initialisieren
            if not self.printer.send_command(b'\x1b\x40'):  # ESC @
                logger.error("Drucker-Initialisierung fehlgeschlagen!")
                return False
            
            time.sleep(0.2)
            
            # Bild drucken
            success = self.printer.send_bitmap(image_data, img.height)
            
            if success:
                logger.info(f"✅ Kalibrierung gedruckt: {description}")
                time.sleep(0.5)
            else:
                logger.error(f"❌ Druck fehlgeschlagen: {description}")
            
            return success
            
        except Exception as e:
            logger.error(f"Fehler beim Drucken: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Phomemo M110 Kalibrierungs-Tool')
    parser.add_argument('--mac', default='12:7E:5A:E9:E5:22', help='Drucker MAC-Adresse')
    parser.add_argument('--mode', choices=['border', 'grid', 'rulers', 'corners', 'series'], 
                       default='border', help='Kalibrierungsmodus')
    parser.add_argument('--offset-x', type=int, default=0, help='X-Offset in Pixeln')
    parser.add_argument('--offset-y', type=int, default=0, help='Y-Offset in Pixeln')
    parser.add_argument('--thickness', type=int, default=2, help='Rahmendicke in Pixeln')
    parser.add_argument('--preview', action='store_true', help='Nur Vorschau anzeigen, nicht drucken')
    
    args = parser.parse_args()
    
    print("🖨️ Phomemo M110 Kalibrierungs-Tool")
    print(f"📡 Drucker MAC: {args.mac}")
    print(f"🎯 Modus: {args.mode}")
    print(f"📐 Offset: X={args.offset_x}px, Y={args.offset_y}px")
    print()
    
    # Drucker initialisieren
    printer = RobustPhomemoM110(args.mac)
    calibration = PhomemoCalibration(printer)
    
    try:
        if args.mode == 'border':
            print("🔲 Erstelle Rahmen-Test...")
            img = calibration.create_border_test(args.thickness, args.offset_x, args.offset_y)
            description = f"Rahmen-Test (Offset: {args.offset_x},{args.offset_y})"
            
        elif args.mode == 'grid':
            print("📐 Erstelle Gitter-Test...")
            img = calibration.create_grid_test(5, args.offset_x, args.offset_y)
            description = f"Gitter-Test (5mm, Offset: {args.offset_x},{args.offset_y})"
            
        elif args.mode == 'rulers':
            print("📏 Erstelle Lineal-Test...")
            img = calibration.create_measurement_rulers(args.offset_x, args.offset_y)
            description = f"Lineal-Test (Offset: {args.offset_x},{args.offset_y})"
            
        elif args.mode == 'corners':
            print("📍 Erstelle Ecken-Test...")
            img = calibration.create_corner_test(15, args.offset_x, args.offset_y)
            description = f"Ecken-Test (Offset: {args.offset_x},{args.offset_y})"
            
        elif args.mode == 'series':
            print("📊 Erstelle Offset-Serie...")
            tests = calibration.create_offset_test_series(args.offset_x, args.offset_y)
            
            for i, (img, desc) in enumerate(tests):
                print(f"  {i+1}/{len(tests)}: {desc}")
                if not args.preview:
                    success = calibration.print_calibration_image(img, desc)
                    if not success:
                        print(f"❌ Fehler bei Test {i+1}")
                        break
                    if i < len(tests) - 1:
                        time.sleep(2)  # Pause zwischen Drucken
                else:
                    print(f"  📋 Vorschau: {desc}")
            
            print("✅ Offset-Serie abgeschlossen!")
            return
        
        if args.preview:
            print(f"📋 Vorschau erstellt: {description}")
            print(f"🖼️ Bildgröße: {img.width}x{img.height}px")
        else:
            success = calibration.print_calibration_image(img, description)
            if success:
                print("✅ Kalibrierung erfolgreich gedruckt!")
            else:
                print("❌ Druck fehlgeschlagen!")
        
    except KeyboardInterrupt:
        print("\n⏹️ Abgebrochen durch Benutzer")
    except Exception as e:
        print(f"❌ Fehler: {e}")
    finally:
        printer.stop_services()

if __name__ == '__main__':
    main()
