Font.load_default()
            
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


# Klasse für Kompatibilität mit bestehendem Code
class CodeGenerator(FixedCodeGenerator):
    pass


if __name__ == "__main__":
    # Test
    generator = FixedCodeGenerator()
    
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
