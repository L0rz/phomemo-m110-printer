#!/usr/bin/env python3
"""
FIXED VERSION: QR-Code und Barcode Generator für Phomemo M110
GARANTIERT: Schriftgröße wird NIEMALS automatisch verkleinert
"""

import qrcode
import io
import logging
from PIL import Image, ImageDraw, ImageFont
from typing import Optional, Tuple, Dict, Any
import re
import os

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
        
        # KOMPAKTE Standard-Größen für mehr Text-Platz
        self.qr_default_size = min(70, label_width_px // 6)  # Dynamisch basierend auf Label-Breite
        self.qr_border = 2
        self.barcode_height = min(30, label_height_px // 8)  # Dynamisch basierend auf Label-Höhe
        self.barcode_width_factor = 2
        
        logger.info(f"📏 CodeGenerator initialized: {label_width_px}x{label_height_px}px, QR:{self.qr_default_size}px, Barcode:{self.barcode_height}px")

    def update_dimensions(self, width_px: int, height_px: int):
        """Aktualisiert die Label-Dimensionen"""
        self.label_width_px = width_px
        self.label_height_px = height_px
        
        # Standard-Größen anpassen
        self.qr_default_size = min(70, width_px // 6)
        self.barcode_height = min(30, height_px // 8)
        
        logger.info(f"📏 CodeGenerator dimensions updated: {width_px}x{height_px}px")

    def parse_and_process_text(self, text: str) -> Tuple[str, list]:
        """Parst Text nach QR-Codes und Barcodes"""
        codes = []
        processed_text = text
        
        # QR-Code Pattern
        qr_pattern = r'#qr(?::(\d+))?#(.*?)#qr#'
        qr_matches = re.finditer(qr_pattern, text, re.DOTALL)
        
        for i, match in enumerate(qr_matches):
            size = int(match.group(1)) if match.group(1) else self.qr_default_size
            # Größe basierend auf Label-Dimensionen begrenzen
            max_qr_size = min(self.label_width_px // 4, self.label_height_px // 4)
            size = min(size, max_qr_size)
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
        
        # Barcode Pattern
        bar_pattern = r'#bar(?::(\d+))?#(.*?)#bar#'
        bar_matches = re.finditer(bar_pattern, processed_text, re.DOTALL)
        
        for i, match in enumerate(bar_matches):
            height = int(match.group(1)) if match.group(1) else self.barcode_height
            # Höhe basierend auf Label-Dimensionen begrenzen
            max_bar_height = min(self.label_height_px // 6, 50)
            height = min(height, max_bar_height)
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
        """Generiert QR-Code angepasst an Label-Größe"""
        try:
            if size is None:
                size = self.qr_default_size
            
            # Dynamische Größenbegrenzung basierend auf Label
            max_size = min(self.label_width_px // 4, self.label_height_px // 4)
            size = min(size, max_size)
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=max(1, size // 25),
                border=self.qr_border,
            )
            
            qr.add_data(content)
            qr.make(fit=True)
            
            qr_img = qr.make_image(fill_color="black", back_color="white")
            qr_img = qr_img.resize((size, size), Image.Resampling.LANCZOS)
            
            logger.info(f"📱 Generated QR for {self.label_width_px}x{self.label_height_px} label: {size}x{size}px")
            return qr_img
            
        except Exception as e:
            logger.error(f"QR generation failed: {e}")
            return None

    def generate_barcode(self, content: str, height: int = None) -> Optional[Image.Image]:
        """Generiert Barcode angepasst an Label-Größe"""
        try:
            if height is None:
                height = self.barcode_height
            
            # Dynamische Höhenbegrenzung basierend auf Label
            max_height = min(self.label_height_px // 6, 50)
            height = min(height, max_height)
            
            if not content.strip():
                logger.warning("Empty barcode, creating placeholder")
                barcode_img = Image.new('1', (100, height), 'white')
                draw = ImageDraw.Draw(barcode_img)
                draw.rectangle([10, height//2-2, 90, height//2+2], fill='black')
                return barcode_img
            
            if HAS_CODE128:
                # Code128 mit Library erstellen
                try:
                    barcode_data = code128.encode(content)
                    width = len(barcode_data) * self.barcode_width_factor
                    width = min(width, self.label_width_px - 20)
                    
                    barcode_img = Image.new('1', (width, height), 'white')
                    draw = ImageDraw.Draw(barcode_img)
                    
                    x = 0
                    for bar in barcode_data:
                        if bar == '1':
                            draw.rectangle([x, 0, x + self.barcode_width_factor - 1, height], fill='black')
                        x += self.barcode_width_factor
                except:
                    # Fallback to simple
                    width = max(100, min(len(content) * 8, self.label_width_px - 20))
                    barcode_img = Image.new('1', (width, height), 'white')
                    draw = ImageDraw.Draw(barcode_img)
                    
                    x = 0
                    bar_width = max(2, width // max(1, len(content) * 6))
                    
                    for char in content:
                        pattern = bin(ord(char))[2:].zfill(8)
                        for bit in pattern[:6]:
                            if bit == '1':
                                draw.rectangle([x, 0, x + bar_width - 1, height], fill='black')
                            x += bar_width
            else:
                # Einfache Barcode-Implementierung
                width = max(100, min(len(content) * 8, self.label_width_px - 20))
                barcode_img = Image.new('1', (width, height), 'white')
                draw = ImageDraw.Draw(barcode_img)
                
                x = 0
                bar_width = max(2, width // max(1, len(content) * 6))
                
                for char in content:
                    pattern = bin(ord(char))[2:].zfill(8)
                    for bit in pattern[:6]:
                        if bit == '1':
                            draw.rectangle([x, 0, x + bar_width - 1, height], fill='black')
                        x += bar_width
            
            logger.info(f"📊 Generated COMPACT Barcode: {width}x{height}px")
            return barcode_img
            
        except Exception as e:
            logger.error(f"Barcode generation failed: {e}")
            return None

    def parse_markdown_text(self, text, base_font_size):
        """Parst Markdown OHNE Schriftgrößen-Änderung"""
        import re
        
        # Text bereinigen
        clean_text = text.replace('\r\n', '\n').replace('\r', '\n').replace('\\n', '\n').replace('\\r\\n', '\n')
        clean_text = clean_text.replace('\x00', '').replace('\t', '    ')
        clean_text = ''.join(char for char in clean_text if ord(char) >= 32 or char in ['\n', ' '])
        
        lines = clean_text.split('\n')
        parsed_lines = []
        
        for line in lines:
            line_segments = []
            
            # Überschriften - KLEINE Größen-Unterschiede
            if line.strip().startswith('# '):
                clean_text = line.strip()[2:].strip()
                line_segments.append((clean_text, base_font_size + 4, True))  # Nur +4px statt +8px
            elif line.strip().startswith('## '):
                clean_text = line.strip()[3:].strip()
                line_segments.append((clean_text, base_font_size + 2, True))  # Nur +2px statt +4px
            else:
                # Normale Zeile mit Fett-Formatierung
                segments = self._parse_inline_markdown(line, base_font_size)
                line_segments.extend(segments)
            
            parsed_lines.append(line_segments)
        
        return parsed_lines

    def _parse_inline_markdown(self, text, base_font_size):
        """Parst inline Markdown - NUR FETT, KEINE Größenänderung"""
        import re
        
        segments = []
        current_pos = 0
        
        # Nur Fett-Patterns
        patterns = [
            (r'\*\*(.*?)\*\*', True),    # **fett**
            (r'__(.*?)__', True),        # __fett__
        ]
        
        all_matches = []
        for pattern, is_bold in patterns:
            for match in re.finditer(pattern, text):
                overlaps = False
                for existing_start, existing_end, _, _ in all_matches:
                    if (match.start() < existing_end and match.end() > existing_start):
                        overlaps = True
                        break
                
                if not overlaps:
                    all_matches.append((match.start(), match.end(), match.group(1), is_bold))
        
        all_matches.sort(key=lambda x: x[0])
        
        for match_start, match_end, match_text, is_bold in all_matches:
            if current_pos < match_start:
                plain_text = text[current_pos:match_start]
                if plain_text:
                    segments.append((plain_text, base_font_size, False))
            
            segments.append((match_text, base_font_size, is_bold))  # GLEICHE Größe
            current_pos = match_end
        
        if current_pos < len(text):
            remaining_text = text[current_pos:]
            if remaining_text:
                segments.append((remaining_text, base_font_size, False))
        
        if not segments:
            segments.append((text, base_font_size, False))
        
        return segments

    def create_combined_image(self, text: str, font_size: int = 22, alignment: str = 'center') -> Optional[Image.Image]:
        """
        FIXED VERSION: Erstellt Bild mit garantiert fester Schriftgröße
        """
        try:
            logger.info(f"🎯 FIXED create_combined_image with GUARANTEED font_size={font_size}")
            
            # Text parsen
            processed_text, codes = self.parse_and_process_text(text)
            logger.info(f"📝 Found {len(codes)} codes")
            
            # Markdown parsen
            parsed_lines = self.parse_markdown_text(processed_text, font_size)
            logger.info(f"📄 Parsed into {len(parsed_lines)} lines")
            
            # Bild erstellen
            img = Image.new('1', (self.label_width_px, self.label_height_px), 'white')
            draw = ImageDraw.Draw(img)
            
            # Font-System
            def get_font(size, bold=False):
                font_paths = [
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/TTF/DejaVuSans.ttf",
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                    "/System/Library/Fonts/Arial.ttf",
                    "C:/Windows/Fonts/arial.ttf"
                ]
                
                for font_path in font_paths:
                    try:
                        if os.path.exists(font_path):
                            return ImageFont.truetype(font_path, size)
                    except:
                        continue
                
                return ImageFont.load_default()
            
            # Codes generieren - KOMPAKT
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
            
            # Content rendern
            current_y = 10
            
            for line_segments in parsed_lines:
                if not line_segments:
                    current_y += font_size // 2
                    continue
                
                # Prüfen auf Code-Platzhalter
                line_text = ''.join([seg[0] for seg in line_segments])
                
                code_placed = False
                for placeholder, code_img in code_images.items():
                    if placeholder in line_text:
                        # Code platzieren
                        code_x = (self.label_width_px - code_img.width) // 2
                        img.paste(code_img, (code_x, current_y))
                        current_y += code_img.height + 6
                        logger.info(f"🔧 Placed {placeholder} at y={current_y-code_img.height-6}")
                        
                        # Text um Code herum
                        remaining_segments = []
                        for segment_text, seg_font_size, is_bold in line_segments:
                            if placeholder in segment_text:
                                parts = segment_text.split(placeholder)
                                if parts[0].strip():
                                    remaining_segments.append((parts[0], seg_font_size, is_bold))
                                if len(parts) > 1 and parts[1].strip():
                                    remaining_segments.append((parts[1], seg_font_size, is_bold))
                            else:
                                remaining_segments.append((segment_text, seg_font_size, is_bold))
                        
                        # Remaining text zeichnen
                        if remaining_segments and any(seg[0].strip() for seg in remaining_segments):
                            current_y = self._draw_text_line(draw, remaining_segments, current_y, alignment, get_font)
                        
                        code_placed = True
                        break
                
                if not code_placed:
                    # Normale Text-Zeile
                    current_y = self._draw_text_line(draw, line_segments, current_y, alignment, get_font)
                
                # Überlauf-Schutz
                if current_y > self.label_height_px - 15:
                    logger.warning(f"⚠️ Y-overflow, stopping render")
                    break
            
            logger.info(f"✅ FIXED image created: {len(codes)} codes, final_y={current_y}")
            return img
            
        except Exception as e:
            logger.error(f"❌ FIXED image creation failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def _draw_text_line(self, draw, line_segments, current_y, alignment, get_font):
        """Zeichnet Text-Zeile OHNE Größen-Änderung"""
        try:
            if not line_segments:
                return current_y + 20
            
            # Gesamtbreite berechnen
            total_width = 0
            max_height = 0
            
            for segment_text, seg_font_size, is_bold in line_segments:
                clean_text = segment_text.strip()
                if clean_text:
                    seg_font = get_font(seg_font_size, is_bold)
                    try:
                        bbox = draw.textbbox((0, 0), clean_text, font=seg_font)
                        total_width += bbox[2] - bbox[0]
                        max_height = max(max_height, bbox[3] - bbox[1])
                    except:
                        total_width += len(clean_text) * (seg_font_size // 2)
                        max_height = max(max_height, seg_font_size)
            
            # X-Position
            if alignment == 'center':
                start_x = max(10, (self.label_width_px - total_width) // 2)
            elif alignment == 'right':
                start_x = max(10, self.label_width_px - total_width - 10)
            else:
                start_x = 10
            
            # Text zeichnen
            current_x = start_x
            for segment_text, seg_font_size, is_bold in line_segments:
                clean_text = segment_text.strip()
                if clean_text:
                    seg_font = get_font(seg_font_size, is_bold)
                    logger.info(f"🎨 Drawing '{clean_text}' with FIXED size={seg_font_size}, bold={is_bold}")
                    
                    try:
                        draw.text((current_x, current_y), clean_text, fill='black', font=seg_font)
                        bbox = draw.textbbox((0, 0), clean_text, font=seg_font)
                        current_x += bbox[2] - bbox[0] + 2
                    except Exception as e:
                        logger.warning(f"Could not draw '{clean_text}': {e}")
                        current_x += len(clean_text) * (seg_font_size // 2)
            
            return current_y + max(max_height, 20) + 4
            
        except Exception as e:
            logger.error(f"Error in _draw_text_line: {e}")
            return current_y + 25

    def get_syntax_help(self) -> str:
        """Gibt Hilfe zur Markdown-Syntax zurück (angepasst an aktuelle Label-Größe)"""
        max_qr = min(self.label_width_px // 4, self.label_height_px // 4)
        max_bar = min(self.label_height_px // 6, 50)
        
        return f"""
QR-Code und Barcode Syntax (Label: {self.label_width_px}×{self.label_height_px}px):

QR-Codes:
  #qr#Inhalt#qr#                    -> Standard QR-Code ({self.qr_default_size}px)
  #qr:{max_qr//2}#Größerer Inhalt#qr#        -> QR-Code mit angepasster Größe
  #qr#https://example.com#qr#       -> QR mit URL
  #qr#WIFI:S:MeinWLAN;T:WPA;P:passwort123;H:false;;#qr#  -> WLAN QR
  
  ⚠️ Maximale QR-Größe für aktuelles Label: {max_qr}px

Barcodes:
  #bar#1234567890#bar#              -> Standard Barcode ({self.barcode_height}px hoch)
  #bar:{max_bar//2}#Code mit Text#bar#        -> Barcode mit angepasster Höhe
  
  ⚠️ Maximale Barcode-Höhe für aktuelles Label: {max_bar}px

Markdown:
  **Fetter Text**                   -> Fett formatiert
  # Überschrift                     -> Große Überschrift
  ## Unterüberschrift               -> Mittlere Überschrift

Kombiniert:
  # Produkt-Label
  **Artikel:** #bar#ART-12345#bar#
  **Website:** #qr#https://shop.de#qr#
  
Hinweise:
- Codes werden automatisch zentriert
- Text kann vor/nach Codes stehen  
- Mehrere Codes pro Label möglich
- Größen werden automatisch an Label angepasst
- Aktuelles Label: {self.label_width_px}×{self.label_height_px} Pixel
        """.strip()


if __name__ == "__main__":
    # Test
    generator = CodeGenerator()
    
    test_text = """
# Test Label

**Artikel:** #bar#ART-12345#bar#

**Website:** #qr#https://test.com#qr#

Normal text here!
    """
    
    print("Testing FIXED version:")
    img = generator.create_combined_image(test_text, font_size=22, alignment='center')
    if img:
        print(f"✅ SUCCESS: Image created {img.width}x{img.height}")
    else:
        print("❌ FAILED: No image created")
