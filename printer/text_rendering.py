"""
Text-Rendering und Markdown-Verarbeitung fuer den Phomemo M110 Drucker.
"""

import os
import re
import logging
from typing import Optional, List, Tuple

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


class TextRenderingMixin:
    """Mixin fuer Text-Bild-Erzeugung und Markdown-Parsing."""

    def create_text_image_with_offsets(self, text, font_size, alignment='center'):
        """Erstellt Text-Bild mit Offsets und Ausrichtung - MIT MARKDOWN SUPPORT"""
        try:
            # Erst das Markdown-formatierte Bild ohne Offsets erstellen
            markdown_img = self.create_text_image_preview(text, font_size, alignment)

            if markdown_img is None:
                logger.error("Failed to create markdown image")
                return None

            # Dann Offsets anwenden
            x_offset = self.settings.get('x_offset', 0)
            y_offset = self.settings.get('y_offset', 0)

            if x_offset != 0 or y_offset != 0:
                logger.info(f"Applying offsets to markdown text: X={x_offset}, Y={y_offset}")
                final_img = self.apply_offsets_to_image(markdown_img)
                logger.info(f"Final markdown text image size: {final_img.width}x{final_img.height}")
                return final_img
            else:
                logger.info(f"No offsets applied to markdown text, image size: {markdown_img.width}x{markdown_img.height}")
                return markdown_img

        except Exception as e:
            logger.error(f"Markdown text image creation error: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return None

    def parse_markdown_text(self, text, base_font_size):
        """
        Parst Markdown-Text und gibt eine Liste von formatierten Text-Segmenten zurueck

        Unterstuetzte Markdown-Syntax:
        - **fett** oder __fett__
        - # Ueberschrift (grosse Schrift)
        - ## Unterueberschrift (mittlere Schrift)

        Returns: List of tuples (text, font_size, bold)
        """
        # SCHRITT 1: Komplette Text-Bereinigung VOR dem Parsen
        clean_text = text.replace('\r\n', '\n')
        clean_text = clean_text.replace('\r', '\n')
        clean_text = clean_text.replace('\\n', '\n')
        clean_text = clean_text.replace('\\r\\n', '\n')

        # Problematische Zeichen entfernen
        clean_text = clean_text.replace('\x00', '')
        clean_text = clean_text.replace('\t', '    ')

        # Alle anderen Steuerzeichen entfernen (ausser \n und Space)
        clean_text = ''.join(char for char in clean_text if ord(char) >= 32 or char in ['\n', ' '])

        lines = clean_text.split('\n')
        parsed_lines = []

        for line in lines:
            line_segments = []

            if line.strip().startswith('# '):
                heading_text = line.strip()[2:].strip()
                line_segments.append((heading_text, base_font_size + 8, True))
            elif line.strip().startswith('## '):
                heading_text = line.strip()[3:].strip()
                line_segments.append((heading_text, base_font_size + 4, True))
            else:
                segments = self._parse_inline_markdown(line, base_font_size)
                line_segments.extend(segments)

            parsed_lines.append(line_segments)

        return parsed_lines

    def _parse_inline_markdown(self, text, base_font_size):
        """Parst inline Markdown-Formatierung in einem Text - NUR FETT"""
        segments = []
        current_pos = 0

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

            segments.append((match_text, base_font_size, is_bold))
            current_pos = match_end

        if current_pos < len(text):
            remaining_text = text[current_pos:]
            if remaining_text:
                segments.append((remaining_text, base_font_size, False))

        if not segments:
            segments.append((text, base_font_size, False))

        return segments

    def create_text_image_preview(self, text, font_size, alignment='center'):
        """Erstellt Text-Bild fuer Vorschau OHNE Offsets - mit Markdown-Support"""
        try:
            logger.info(f"Creating MARKDOWN text preview with font size {font_size}, alignment: {alignment}")

            # Markdown-Text parsen
            parsed_lines = self.parse_markdown_text(text, font_size)

            # Font-Cache fuer verschiedene Groessen und Stile
            font_cache = {}

            def get_font(size, bold=False):
                key = (size, bold)
                if key not in font_cache:
                    font_paths = [
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/TTF/DejaVuSans.ttf",
                        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                        "/System/Library/Fonts/Arial.ttf",
                        "C:/Windows/Fonts/arial.ttf"
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

            # Bildgroesse berechnen
            temp_img = Image.new('RGB', (1, 1), 'white')
            temp_draw = ImageDraw.Draw(temp_img)

            line_heights = []
            max_width = 0

            for line_segments in parsed_lines:
                line_width = 0
                line_height = 0

                for segment_text, seg_font_size, is_bold in line_segments:
                    if segment_text.strip():
                        seg_font = get_font(seg_font_size, is_bold)
                        try:
                            bbox = temp_draw.textbbox((0, 0), segment_text, font=seg_font)
                            seg_width = bbox[2] - bbox[0]
                            seg_height = bbox[3] - bbox[1]
                            line_width += seg_width
                            line_height = max(line_height, seg_height)
                        except Exception:
                            line_width += len(segment_text) * (seg_font_size // 2)
                            line_height = max(line_height, seg_font_size)

                max_width = max(max_width, line_width)
                line_heights.append(max(line_height, 20))

            # Bild erstellen
            total_height = sum(line_heights) + (len(parsed_lines) - 1) * 5 + 40
            total_height = max(total_height, 50)

            logger.info(f"Markdown preview image size: {self.label_width_px}x{total_height}")
            img = Image.new('RGB', (self.label_width_px, total_height), 'white')
            draw = ImageDraw.Draw(img)

            # Markdown-Text mit Formatierung zeichnen
            y_pos = 20
            for i, line_segments in enumerate(parsed_lines):
                line_width = 0

                for segment_text, seg_font_size, is_bold in line_segments:
                    if segment_text.strip():
                        seg_font = get_font(seg_font_size, is_bold)
                        try:
                            bbox = draw.textbbox((0, 0), segment_text, font=seg_font)
                            seg_width = bbox[2] - bbox[0]
                            line_width += seg_width
                        except Exception:
                            line_width += len(segment_text) * (seg_font_size // 2)

                if alignment == 'left':
                    start_x = 10
                elif alignment == 'right':
                    start_x = max(10, self.label_width_px - line_width - 10)
                else:  # center
                    start_x = max(10, (self.label_width_px - line_width) // 2)

                current_x = start_x
                for segment_text, seg_font_size, is_bold in line_segments:
                    if segment_text:
                        clean_text = segment_text.replace('\x00', '').replace('\t', '    ')
                        clean_text = ''.join(char for char in clean_text if ord(char) >= 32 or char in '\n\r')

                        if clean_text.strip():
                            seg_font = get_font(seg_font_size, is_bold)
                            try:
                                draw.text((current_x, y_pos), clean_text, fill='black', font=seg_font)
                                bbox = draw.textbbox((0, 0), clean_text, font=seg_font)
                                current_x += bbox[2] - bbox[0]

                                logger.debug(f"Drew segment '{clean_text[:20]}...' (size:{seg_font_size}, bold:{is_bold}) at ({current_x}, {y_pos})")
                            except Exception as e:
                                logger.warning(f"Could not draw segment '{clean_text[:20]}...': {e}")
                                current_x += len(clean_text) * (seg_font_size // 2)

                y_pos += line_heights[i] + 5

            # Bild zu S/W konvertieren OHNE Offsets
            bw_img = img.convert('1')

            logger.info(f"Markdown preview image created (NO offsets): {bw_img.width}x{bw_img.height}")
            return bw_img

        except Exception as e:
            logger.error(f"Markdown text preview image creation error: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return None
