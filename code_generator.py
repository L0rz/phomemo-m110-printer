#!/usr/bin/env python3
"""
QR-Code und Barcode Generator für Phomemo M110
Erweitert das bestehende System um Code-Generation mit Markdown-Syntax
"""

import qrcode
import io
import logging
from PIL import Image, ImageDraw, ImageFont
from typing import Optional, Tuple, Dict, Any
import re

# Try to import code128, fallback to simple implementation
try:
    import code128
    HAS_CODE128 = True
except ImportError:
    HAS_CODE128 = False
    print("WARNING: code128 not available, using simple barcode implementation")

logger = logging.getLogger(__name__)

class CodeGenerator:
    def __init__(self, label_width_px=384, label_height_px=240):
        self.label_width_px = label_width_px
        self.label_height_px = label_height_px
        
        # QR-Code Standardeinstellungen
        self.qr_default_size = 100  # Pixel
        self.qr_border = 2
        
        # Barcode Standardeinstellungen
        self.barcode_height = 50
        self.barcode_width_factor = 2
        
    def parse_and_process_text(self, text: str) -> Tuple[str, list]:
        """
        Parst Text nach QR-Codes und Barcodes und ersetzt sie durch Platzhalter
        
        Syntax:
        #qr#content#qr# -> QR-Code
        #qr:size#content#qr# -> QR-Code mit spezifischer Größe
        #bar#content#bar# -> Barcode (Code128)
        #bar:height#content#bar# -> Barcode mit spezifischer Höhe
        
        Returns: (processed_text, list_of_codes)
        """
        codes = []
        processed_text = text
        
        # QR-Code Pattern mit optionaler Größe
        qr_pattern = r'#qr(?::(\d+))?#(.*?)#qr#'
        qr_matches = re.finditer(qr_pattern, text, re.DOTALL)
        
        for i, match in enumerate(qr_matches):
            size = int(match.group(1)) if match.group(1) else self.qr_default_size
            content = match.group(2).strip()
            
            placeholder = f"[QR_CODE_{i}]"
            processed_text = processed_text.replace(match.group(0), placeholder)
            
            codes.append({
                'type': 'qr',
                'content': content,
                'size': size,
                'placeholder': placeholder,
                'position': i
            })
        
        # Barcode Pattern mit optionaler Höhe
        bar_pattern = r'#bar(?::(\d+))?#(.*?)#bar#'
        bar_matches = re.finditer(bar_pattern, processed_text, re.DOTALL)
        
        for i, match in enumerate(bar_matches):
            height = int(match.group(1)) if match.group(1) else self.barcode_height
            content = match.group(2).strip()
            
            placeholder = f"[BARCODE_{i}]"
            processed_text = processed_text.replace(match.group(0), placeholder)
            
            codes.append({
                'type': 'barcode',
                'content': content,
                'height': height,
                'placeholder': placeholder,
                'position': len([c for c in codes if c['type'] == 'qr']) + i
            })
        
        return processed_text, codes
    
    def generate_qr_code(self, content: str, size: int = None) -> Optional[Image.Image]:
        """Generiert QR-Code als PIL Image"""
        try:
            if size is None:
                size = self.qr_default_size
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=max(1, size // 25),  # Dynamische Box-Größe
                border=self.qr_border,
            )
            
            qr.add_data(content)
            qr.make(fit=True)
            
            # Als PIL Image erstellen
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Auf gewünschte Größe skalieren
            qr_img = qr_img.resize((size, size), Image.Resampling.LANCZOS)
            
            logger.info(f"QR-Code generated: {len(content)} chars, {size}x{size}px")
            return qr_img
            
        except Exception as e:
            logger.error(f"QR-Code generation failed: {e}")
            return None
    
    def generate_barcode(self, content: str, height: int = None) -> Optional[Image.Image]:
        """Generiert Barcode (Code128) als PIL Image"""
        try:
            if height is None:
                height = self.barcode_height
            
            # Leeren Content abfangen
            if not content.strip():
                logger.warning("Empty barcode content, creating placeholder")
                barcode_img = Image.new('1', (100, height), 'white')
                draw = ImageDraw.Draw(barcode_img)
                draw.rectangle([10, height//2-2, 90, height//2+2], fill='black')
                return barcode_img
            
            if HAS_CODE128:
                # Code128 mit Library erstellen
                barcode_data = code128.encode(content)
                
                # Barcode als Bild rendern
                width = len(barcode_data) * self.barcode_width_factor
                width = min(width, self.label_width_px - 20)  # Max. Labelbreite minus Rand
                
                barcode_img = Image.new('1', (width, height), 'white')
                draw = ImageDraw.Draw(barcode_img)
                
                # Barcode-Striche zeichnen
                x = 0
                for bar in barcode_data:
                    if bar == '1':  # Schwarzer Strich
                        draw.rectangle([x, 0, x + self.barcode_width_factor - 1, height], fill='black')
                    x += self.barcode_width_factor
            else:
                # Einfache Barcode-Implementierung ohne code128 Library
                width = max(100, min(len(content) * 12, self.label_width_px - 20))
                barcode_img = Image.new('1', (width, height), 'white')
                draw = ImageDraw.Draw(barcode_img)
                
                # Einfaches Muster für jeden Charakter
                x = 0
                bar_width = max(2, width // max(1, len(content) * 6))
                
                for char in content:
                    # Einfaches Strich-Muster basierend auf ASCII-Wert
                    pattern = bin(ord(char))[2:].zfill(8)
                    for bit in pattern[:6]:  # Nur erste 6 Bits verwenden
                        if bit == '1':
                            draw.rectangle([x, 0, x + bar_width - 1, height], fill='black')
                        x += bar_width
            
            logger.info(f"Barcode generated: '{content}', {width}x{height}px")
            return barcode_img
            
        except Exception as e:
            logger.error(f"Barcode generation failed: {e}")
            return None
    
    def create_combined_image(self, text: str, font_size: int = 22, alignment: str = 'center') -> Optional[Image.Image]:
        """
        Erstellt kombiniertes Bild mit Text und Codes
        """
        try:
            # Text parsen und Codes extrahieren
            processed_text, codes = self.parse_and_process_text(text)
            
            # Basis-Bild erstellen
            img = Image.new('1', (self.label_width_px, self.label_height_px), 'white')
            draw = ImageDraw.Draw(img)
            
            # Font laden
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("arial.ttf", font_size)
                except:
                    font = ImageFont.load_default()
            
            current_y = 10
            
            # Codes generieren und platzieren
            code_images = {}
            for code in codes:
                if code['type'] == 'qr':
                    code_img = self.generate_qr_code(code['content'], code['size'])
                elif code['type'] == 'barcode':
                    code_img = self.generate_barcode(code['content'], code['height'])
                else:
                    continue
                
                if code_img:
                    code_images[code['placeholder']] = code_img
            
            # Text-Zeilen verarbeiten
            text_lines = processed_text.split('\n')
            
            for line in text_lines:
                line = line.strip()
                if not line:
                    current_y += font_size // 2  # Leerzeile
                    continue
                
                # Prüfen ob Zeile einen Code-Platzhalter enthält
                code_found = False
                for placeholder, code_img in code_images.items():
                    if placeholder in line:
                        # Code platzieren
                        code_x = (self.label_width_px - code_img.width) // 2  # Zentriert
                        
                        # Prüfen ob genug Platz vorhanden
                        if current_y + code_img.height > self.label_height_px:
                            logger.warning(f"Not enough space for {placeholder}, shrinking...")
                            # Versuche kleineren Code zu erstellen
                            if code['type'] == 'qr':
                                smaller_size = min(80, code.get('size', 100))
                                code_img = self.generate_qr_code(code['content'], smaller_size)
                            elif code['type'] == 'barcode':
                                smaller_height = min(30, code.get('height', 50))
                                code_img = self.generate_barcode(code['content'], smaller_height)
                            
                            if code_img and current_y + code_img.height <= self.label_height_px:
                                logger.info(f"Successfully shrunk {placeholder}")
                            else:
                                logger.warning(f"Skipping {placeholder} - no space even after shrinking")
                                continue
                        
                        # Code einfügen
                        img.paste(code_img, (code_x, current_y))
                        current_y += code_img.height + 10
                        
                        # Text vor/nach dem Code
                        text_before_after = line.replace(placeholder, '').strip()
                        if text_before_after:
                            # Text unter dem Code
                            bbox = draw.textbbox((0, 0), text_before_after, font=font)
                            text_width = bbox[2] - bbox[0]
                            text_height = bbox[3] - bbox[1]
                            
                            if alignment == 'center':
                                text_x = (self.label_width_px - text_width) // 2
                            elif alignment == 'right':
                                text_x = self.label_width_px - text_width - 10
                            else:  # left
                                text_x = 10
                            
                            draw.text((text_x, current_y), text_before_after, font=font, fill='black')
                            current_y += text_height + 5
                        
                        code_found = True
                        break
                
                if not code_found:
                    # Normaler Text
                    bbox = draw.textbbox((0, 0), line, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    
                    if alignment == 'center':
                        text_x = (self.label_width_px - text_width) // 2
                    elif alignment == 'right':
                        text_x = self.label_width_px - text_width - 10
                    else:  # left
                        text_x = 10
                    
                    draw.text((text_x, current_y), line, font=font, fill='black')
                    current_y += text_height + 5
            
            logger.info(f"Combined image created with {len(codes)} codes")
            return img
            
        except Exception as e:
            logger.error(f"Combined image creation failed: {e}")
            return None
    
    def get_syntax_help(self) -> str:
        """Gibt Hilfe zur Markdown-Syntax zurück"""
        return """
QR-Code und Barcode Syntax:

QR-Codes:
  #qr#Inhalt#qr#                    -> Standard QR-Code (100px)
  #qr:150#Größerer Inhalt#qr#       -> QR-Code mit 150px Größe
  #qr#https://example.com#qr#       -> QR mit URL
  #qr#WIFI:S:MeinWLAN;T:WPA;P:passwort123;H:false;;#qr#  -> WLAN QR

Barcodes:
  #bar#1234567890#bar#              -> Standard Barcode (50px hoch)
  #bar:80#Code mit Text#bar#        -> Barcode mit 80px Höhe

Kombiniert:
  Produkt: #bar#ART-12345#bar#
  Website: #qr#https://shop.de#qr#
  
Hinweise:
- Codes werden automatisch zentriert
- Text kann vor/nach Codes stehen
- Mehrere Codes pro Label möglich
- Achte auf Labelgröße (384x240px)
        """.strip()

# Integration in den bestehenden printer_controller
def enhance_printer_controller():
    """
    Fügt Code-Generation zum bestehenden EnhancedPhomemoM110 hinzu
    """
    enhancement_code = '''
    def __init__(self, mac_address):
        # ... existing init code ...
        
        # Code Generator hinzufügen
        self.code_generator = CodeGenerator(self.label_width_px, self.label_height_px)
    
    def create_text_image_with_codes(self, text: str, font_size: int = 22, alignment: str = 'center') -> Optional[Image.Image]:
        """Erstellt Text-Bild mit QR/Barcode-Unterstützung"""
        return self.code_generator.create_combined_image(text, font_size, alignment)
    
    def print_text_with_codes_immediate(self, text: str, font_size: int = 22, alignment: str = 'center') -> Dict[str, Any]:
        """Druckt Text mit Codes sofort"""
        try:
            img = self.create_text_image_with_codes(text, font_size, alignment)
            if img:
                success = self._print_image_direct(img)
                self.stats['successful_jobs'] += 1 if success else 0
                self.stats['failed_jobs'] += 0 if success else 1
                return {'success': success, 'message': 'Text mit Codes gedruckt' if success else 'Druckfehler'}
            else:
                return {'success': False, 'message': 'Bild-Erstellung fehlgeschlagen'}
        except Exception as e:
            logger.error(f"Print text with codes error: {e}")
            return {'success': False, 'message': str(e)}
    '''
    
    return enhancement_code

if __name__ == "__main__":
    # Test
    generator = CodeGenerator()
    
    test_text = """
Testlabel mit Codes:

#qr#https://github.com/phomemo-m110#qr#

Artikel: #bar#ART-12345#bar#

Datum: 15.08.2025
    """
    
    print("Parsing test:")
    processed, codes = generator.parse_and_process_text(test_text)
    print(f"Processed: {processed}")
    print(f"Codes found: {len(codes)}")
    for code in codes:
        print(f"  {code['type']}: {code['content']}")
