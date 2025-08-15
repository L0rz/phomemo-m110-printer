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
        
        # QR-Code Standardeinstellungen - KOMPAKTER für bessere Text-Balance
        self.qr_default_size = 80  # Reduziert von 100 auf 80 Pixel
        self.qr_border = 2
        
        # Barcode Standardeinstellungen - KOMPAKTER für bessere Text-Balance  
        self.barcode_height = 40  # Reduziert von 50 auf 40 Pixel
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
    
    def parse_markdown_text(self, text, base_font_size):
        """
        Parst Markdown-Text und gibt eine Liste von formatierten Text-Segmenten zurück
        
        Unterstützte Markdown-Syntax:
        - **fett** oder __fett__
        - # Überschrift (große Schrift)
        - ## Unterüberschrift (mittlere Schrift)
        
        Returns: List of tuples (text, font_size, bold)
        """
        import re
        
        # Text-Bereinigung VOR dem Parsen
        clean_text = text.replace('\r\n', '\n').replace('\r', '\n').replace('\\n', '\n').replace('\\r\\n', '\n')
        clean_text = clean_text.replace('\x00', '').replace('\t', '    ')
        clean_text = ''.join(char for char in clean_text if ord(char) >= 32 or char in ['\n', ' '])
        
        lines = clean_text.split('\n')
        parsed_lines = []
        
        for line in lines:
            line_segments = []
            
            # Überschriften prüfen (müssen am Zeilenanfang stehen)
            if line.strip().startswith('# '):
                # H1 - Große Überschrift
                clean_text = line.strip()[2:].strip()
                line_segments.append((clean_text, base_font_size + 8, True))
            elif line.strip().startswith('## '):
                # H2 - Mittlere Überschrift  
                clean_text = line.strip()[3:].strip()
                line_segments.append((clean_text, base_font_size + 4, True))
            else:
                # Normale Zeile - inline Formatierung parsen
                segments = self._parse_inline_markdown(line, base_font_size)
                line_segments.extend(segments)
            
            parsed_lines.append(line_segments)
        
        return parsed_lines
    
    def _parse_inline_markdown(self, text, base_font_size):
        """Parst inline Markdown-Formatierung in einem Text - NUR FETT"""
        import re
        
        segments = []
        current_pos = 0
        
        # Regex-Patterns für Markdown - NUR FETT, KEIN KURSIV
        patterns = [
            (r'\*\*(.*?)\*\*', True),    # **fett**
            (r'__(.*?)__', True),        # __fett__
        ]
        
        # Alle Matches finden und sortieren
        all_matches = []
        for pattern, is_bold in patterns:
            for match in re.finditer(pattern, text):
                # Prüfen ob es sich überschneidet mit bereits gefundenen Matches
                overlaps = False
                for existing_start, existing_end, _, _ in all_matches:
                    if (match.start() < existing_end and match.end() > existing_start):
                        overlaps = True
                        break
                
                if not overlaps:
                    all_matches.append((match.start(), match.end(), match.group(1), is_bold))
        
        # Nach Position sortieren
        all_matches.sort(key=lambda x: x[0])
        
        # Text in Segmente aufteilen
        for match_start, match_end, match_text, is_bold in all_matches:
            # Text vor dem Match hinzufügen
            if current_pos < match_start:
                plain_text = text[current_pos:match_start]
                if plain_text:
                    segments.append((plain_text, base_font_size, False))
            
            # Formatierten Text hinzufügen
            segments.append((match_text, base_font_size, is_bold))
            current_pos = match_end
        
        # Restlichen Text hinzufügen
        if current_pos < len(text):
            remaining_text = text[current_pos:]
            if remaining_text:
                segments.append((remaining_text, base_font_size, False))
        
        # Wenn keine Formatierung gefunden wurde, ganzen Text als plain zurückgeben
        if not segments:
            segments.append((text, base_font_size, False))
        
        return segments

    def create_combined_image(self, text: str, font_size: int = 22, alignment: str = 'center') -> Optional[Image.Image]:
        """
        Erstellt kombiniertes Bild mit Text, Markdown UND Codes
        """
        try:
            # SCHRITT 1: Text parsen und QR/Barcode-Codes extrahieren
            processed_text, codes = self.parse_and_process_text(text)
            
            # SCHRITT 2: Den verarbeiteten Text durch Markdown-Parser schicken
            parsed_lines = self.parse_markdown_text(processed_text, font_size)
            
            # Basis-Bild erstellen
            img = Image.new('1', (self.label_width_px, self.label_height_px), 'white')
            draw = ImageDraw.Draw(img)
            
            # Font-Cache für verschiedene Größen und Stile
            font_cache = {}
            
            def get_font(size, bold=False):
                key = (size, bold)
                if key not in font_cache:
                    font_paths = [
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/TTF/DejaVuSans.ttf",
                        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                        "/System/Library/Fonts/Arial.ttf",  # macOS
                        "C:/Windows/Fonts/arial.ttf"  # Windows
                    ]
                    
                    font_obj = None
                    for font_path in font_paths:
                        try:
                            if os.path.exists(font_path):
                                font_obj = ImageFont.truetype(font_path, size)
                                break
                        except Exception:
                            continue
                    
                    if font_obj is None:
                        font_obj = ImageFont.load_default()
                    
                    font_cache[key] = font_obj
                
                return font_cache[key]
            
            # VERBESSERTES Platz-Management: Intelligente Code-Größenanpassung
            current_y = 5  # Start-Y-Position
            
            # Codes generieren mit intelligenter Größenanpassung
            code_images = {}
            total_code_height = 0
            
            for code in codes:
                if code['type'] == 'qr':
                    # QR-Code Größe basierend auf verfügbarem Platz anpassen
                    requested_size = code['size']
                    max_qr_size = min(requested_size, 120)  # Maximal 120px
                    min_qr_size = 60  # Minimal 60px für Lesbarkeit
                    
                    # Versuche mit der gewünschten Größe, aber nicht größer als sinnvoll
                    if len(codes) == 1:  # Nur ein Code -> mehr Platz
                        qr_size = min(requested_size, max_qr_size)
                    else:  # Mehrere Codes -> kompakter
                        qr_size = min(requested_size, 80)
                    
                    code_img = self.generate_qr_code(code['content'], qr_size)
                    
                elif code['type'] == 'barcode':
                    # Barcode Höhe basierend auf verfügbarem Platz anpassen
                    requested_height = code['height']
                    max_bar_height = min(requested_height, 60)  # Maximal 60px
                    min_bar_height = 30  # Minimal 30px für Lesbarkeit
                    
                    if len(codes) == 1:  # Nur ein Code -> mehr Platz
                        bar_height = min(requested_height, max_bar_height)
                    else:  # Mehrere Codes -> kompakter
                        bar_height = min(requested_height, 45)
                    
                    code_img = self.generate_barcode(code['content'], bar_height)
                else:
                    continue
                
                if code_img:
                    code_images[code['placeholder']] = code_img
                    total_code_height += code_img.height + 15  # Code + Abstand
            
            # Prüfen ob alle Codes + Text auf das Label passen
            estimated_text_height = len(parsed_lines) * (font_size + 5)  # Grobe Schätzung
            total_needed_height = total_code_height + estimated_text_height + 20  # + Ränder
            
            if total_needed_height > self.label_height_px:
                logger.info(f"Content too large ({total_needed_height}px > {self.label_height_px}px), optimizing...")
                
                # Codes verkleinern wenn nötig
                for code in codes:
                    placeholder = code['placeholder']
                    if placeholder in code_images:
                        old_img = code_images[placeholder]
                        
                        if code['type'] == 'qr':
                            # QR auf minimum verkleinern
                            new_size = 60
                            code_images[placeholder] = self.generate_qr_code(code['content'], new_size)
                            logger.info(f"Resized QR from {old_img.width}px to {new_size}px")
                            
                        elif code['type'] == 'barcode':
                            # Barcode auf minimum verkleinern
                            new_height = 30
                            code_images[placeholder] = self.generate_barcode(code['content'], new_height)
                            logger.info(f"Resized Barcode from {old_img.height}px to {new_height}px")
            
            # SCHRITT 3: Markdown-formatierte Zeilen mit QR/Barcode-Platzhaltern verarbeiten
            for line_segments in parsed_lines:
                if not line_segments:
                    current_y += font_size // 2  # Leerzeile
                    continue
                
                # Prüfen ob diese Zeile Code-Platzhalter enthält
                line_text = ''.join([seg[0] for seg in line_segments])
                
                code_found = False
                for placeholder, code_img in code_images.items():
                    if placeholder in line_text:
                        # CODE EINBINDEN
                        code_x = (self.label_width_px - code_img.width) // 2  # Zentriert
                        
                        # Prüfen ob genug Platz vorhanden (weniger strikt)
                        space_needed = code_img.height + 5  # Weniger Abstand
                        space_available = self.label_height_px - current_y - 20  # Reserve für Text
                        
                        if space_needed <= space_available:
                            # Code einfügen
                            img.paste(code_img, (code_x, current_y))
                            current_y += code_img.height + 8  # Weniger Abstand nach Code
                            logger.info(f"Placed {placeholder} at y={current_y-code_img.height-8}")
                        else:
                            logger.warning(f"Skipping {placeholder} - not enough space ({space_needed}px needed, {space_available}px available)")
                        
                        # MARKDOWN-FORMATIERTE Text-Segmente um den Code herum verarbeiten
                        remaining_segments = []
                        for segment_text, seg_font_size, is_bold in line_segments:
                            if placeholder in segment_text:
                                # Platzhalter entfernen, aber Text davor/danach behalten
                                parts = segment_text.split(placeholder)
                                if parts[0]:
                                    remaining_segments.append((parts[0], seg_font_size, is_bold))
                                if len(parts) > 1 and parts[1]:
                                    remaining_segments.append((parts[1], seg_font_size, is_bold))
                            else:
                                remaining_segments.append((segment_text, seg_font_size, is_bold))
                        
                        # Remaining text mit Markdown-Formatierung zeichnen
                        if remaining_segments:
                            current_y = self._draw_markdown_line(draw, remaining_segments, current_y, alignment, get_font)
                        
                        code_found = True
                        break
                
                if not code_found:
                    # NORMALE MARKDOWN-FORMATIERTE ZEILE ohne Codes
                    current_y = self._draw_markdown_line(draw, line_segments, current_y, alignment, get_font)
            
            logger.info(f"Combined image created with Markdown + {len(codes)} codes")
            return img
            
        except Exception as e:
            logger.error(f"Combined image creation failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    def _draw_markdown_line(self, draw, line_segments, current_y, alignment, get_font):
        """Zeichnet eine Zeile mit Markdown-Formatierung"""
        try:
            # Gesamtbreite der Zeile berechnen für Ausrichtung
            line_width = 0
            line_height = 0
            
            for segment_text, seg_font_size, is_bold in line_segments:
                if segment_text.strip():
                    seg_font = get_font(seg_font_size, is_bold)
                    try:
                        bbox = draw.textbbox((0, 0), segment_text, font=seg_font)
                        seg_width = bbox[2] - bbox[0]
                        seg_height = bbox[3] - bbox[1]
                        line_width += seg_width
                        line_height = max(line_height, seg_height)
                    except Exception:
                        line_width += len(segment_text) * (seg_font_size // 2)
                        line_height = max(line_height, seg_font_size)
            
            # X-Startposition basierend auf Ausrichtung
            if alignment == 'left':
                start_x = 10
            elif alignment == 'right':
                start_x = max(10, self.label_width_px - line_width - 10)
            else:  # center
                start_x = max(10, (self.label_width_px - line_width) // 2)
            
            # Segmente zeichnen
            current_x = start_x
            for segment_text, seg_font_size, is_bold in line_segments:
                if segment_text:
                    # Text bereinigen
                    clean_text = segment_text.replace('\x00', '').replace('\t', '    ')
                    clean_text = ''.join(char for char in clean_text if ord(char) >= 32 or char in '\n\r')
                    
                    if clean_text.strip():
                        seg_font = get_font(seg_font_size, is_bold)
                        try:
                            draw.text((current_x, current_y), clean_text, fill='black', font=seg_font)
                            bbox = draw.textbbox((0, 0), clean_text, font=seg_font)
                            current_x += bbox[2] - bbox[0]
                            
                            logger.debug(f"Drew Markdown segment '{clean_text[:20]}...' (size:{seg_font_size}, bold:{is_bold})")
                        except Exception as e:
                            logger.warning(f"Could not draw segment '{clean_text[:20]}...': {e}")
                            current_x += len(clean_text) * (seg_font_size // 2)
            
            return current_y + max(line_height, 20) + 5
            
        except Exception as e:
            logger.error(f"Error drawing markdown line: {e}")
            return current_y + 25
    
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
