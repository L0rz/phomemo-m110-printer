"""
Bildverarbeitung, Dithering, Skalierung und Format-Konvertierung
fuer den Phomemo M110 Drucker.
"""

import io
import base64
import logging
from typing import Optional, Dict, Any

from PIL import Image, ImageEnhance
from config import (
    DEFAULT_DITHER_THRESHOLD, DEFAULT_DITHER_STRENGTH, DEFAULT_CONTRAST_BOOST,
    DEFAULT_X_OFFSET, DEFAULT_Y_OFFSET, PREVIEW_MAX_WIDTH, PREVIEW_MAX_HEIGHT,
    PREVIEW_FORMAT, PRINTER_WIDTH_PIXELS,
)
from .models import ImageProcessingResult

# Optional numpy import fuer erweiterte Bildverarbeitung
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

logger = logging.getLogger(__name__)


class ImageProcessingMixin:
    """Mixin fuer Bildverarbeitung und Format-Konvertierung."""

    def process_image_for_preview(self, image_data, fit_to_label=None, maintain_aspect=None,
                                  enable_dither=None, dither_threshold=None, dither_strength=None,
                                  scaling_mode='fit_aspect') -> Optional[ImageProcessingResult]:
        """Verarbeitet ein Bild fuer die Schwarz-Weiss-Vorschau"""
        try:
            # Parameter aus Einstellungen falls nicht uebergeben
            if fit_to_label is None:
                fit_to_label = self.settings.get('fit_to_label_default', True)
            if maintain_aspect is None:
                maintain_aspect = self.settings.get('maintain_aspect_default', True)
            if enable_dither is None:
                enable_dither = self.settings.get('dither_enabled', True)
            if dither_threshold is None:
                dither_threshold = self.settings.get('dither_threshold', DEFAULT_DITHER_THRESHOLD)
            if dither_strength is None:
                dither_strength = self.settings.get('dither_strength', DEFAULT_DITHER_STRENGTH)

            # Bild oeffnen
            if isinstance(image_data, bytes):
                img = Image.open(io.BytesIO(image_data))
            else:
                img = image_data

            # In RGB konvertieren falls notwendig
            if img.mode != 'RGB':
                img = img.convert('RGB')

            original_size = img.size

            # Groesse anpassen basierend auf Skalierungsmodus
            if fit_to_label:
                # Verwende DRUCKER-Breite statt Label-Breite fuer Dithering-Erhaltung
                target_width = self.width_pixels  # 384px statt self.label_width_px (320px)
                target_height = self.label_height_px

                logger.info(f"DITHERING PRESERVATION: Scaling to printer width {target_width}px instead of label width {self.label_width_px}px")

                if scaling_mode == 'fit_aspect':
                    if maintain_aspect:
                        img.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)
                        new_img = Image.new('RGB', (target_width, target_height), 'white')
                        paste_x = (target_width - img.width) // 2
                        paste_y = (target_height - img.height) // 2
                        new_img.paste(img, (paste_x, paste_y))
                        img = new_img
                    else:
                        img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

                elif scaling_mode == 'stretch_full':
                    img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

                elif scaling_mode == 'crop_center':
                    scale_w = target_width / img.width
                    scale_h = target_height / img.height
                    scale = max(scale_w, scale_h)
                    new_width = int(img.width * scale)
                    new_height = int(img.height * scale)
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    left = (new_width - target_width) // 2
                    top = (new_height - target_height) // 2
                    img = img.crop((left, top, left + target_width, top + target_height))

                elif scaling_mode == 'pad_center':
                    scale_w = target_width / img.width
                    scale_h = target_height / img.height
                    scale = min(scale_w, scale_h)
                    new_width = int(img.width * scale)
                    new_height = int(img.height * scale)
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    new_img = Image.new('RGB', (target_width, target_height), 'white')
                    paste_x = (target_width - new_width) // 2
                    paste_y = (target_height - new_height) // 2
                    new_img.paste(img, (paste_x, paste_y))
                    img = new_img

            # Automatische Komplexitaets-Reduktion (VOR dem Dithering)
            if self.settings.get('auto_reduce_complexity', True):
                gray_preview = img.convert('L')
                pixels = list(gray_preview.getdata())
                threshold_preview = self.settings.get('dither_threshold', DEFAULT_DITHER_THRESHOLD)
                estimated_black = sum(1 for p in pixels if p < threshold_preview)
                estimated_complexity = estimated_black / len(pixels)

                if enable_dither:
                    estimated_complexity *= 2.5
                    logger.info(f"Estimated complexity with dithering: {estimated_complexity*100:.1f}%")

                if estimated_complexity > self.settings.get('auto_reduce_threshold', 0.10):
                    logger.warning(f"High complexity detected (estimated): {estimated_complexity*100:.1f}%")
                    logger.info(f"AUTO-REDUCING complexity BEFORE dithering...")

                    if enable_dither:
                        if estimated_complexity > 0.50:
                            factor = 1.8
                        elif estimated_complexity > 0.30:
                            factor = 1.6
                        elif estimated_complexity > 0.20:
                            factor = 1.4
                        else:
                            factor = 1.2
                    else:
                        factor = 1.4 if estimated_complexity > 0.15 else 1.2

                    logger.info(f"   -> Using: Brightness +{(factor-1)*100:.0f}% (Dithering: {enable_dither})")
                    enhancer = ImageEnhance.Brightness(img)
                    img = enhancer.enhance(factor)

                    gray_preview = img.convert('L')
                    pixels = list(gray_preview.getdata())
                    new_estimated_black = sum(1 for p in pixels if p < threshold_preview)
                    new_estimated_complexity = new_estimated_black / len(pixels)
                    if enable_dither:
                        new_estimated_complexity *= 2.5

                    reduction = (estimated_complexity - new_estimated_complexity) * 100
                    logger.info(f"Estimated complexity reduced: {estimated_complexity*100:.1f}% -> {new_estimated_complexity*100:.1f}% (-{reduction:.1f}%)")

            # Schwarz-Weiss konvertieren mit erweiterten Dithering-Optionen
            if enable_dither:
                contrast_boost = self.settings.get('contrast_boost', DEFAULT_CONTRAST_BOOST)
                if contrast_boost != 1.0:
                    try:
                        enhancer = ImageEnhance.Contrast(img)
                        img = enhancer.enhance(contrast_boost)
                    except Exception:
                        logger.warning("Contrast enhancement failed, using original image")

                if dither_strength != 1.0 and HAS_NUMPY:
                    try:
                        gamma = 1.0 / dither_strength
                        img_array = np.array(img)
                        img_array = np.power(img_array / 255.0, gamma) * 255.0
                        img = Image.fromarray(np.uint8(img_array))
                    except Exception:
                        logger.warning("Advanced dithering failed, using standard dithering")

                bw_img = img.convert('1', dither=Image.Dither.FLOYDSTEINBERG)
            else:
                gray_img = img.convert('L')
                bw_img = gray_img.point(lambda x: 0 if x < dither_threshold else 255, '1')

            # Base64 fuer Web-Vorschau erstellen
            preview_buffer = io.BytesIO()
            preview_img = bw_img.convert('RGB')
            preview_img.thumbnail((PREVIEW_MAX_WIDTH, PREVIEW_MAX_HEIGHT), Image.Resampling.NEAREST)
            preview_img.save(preview_buffer, format=PREVIEW_FORMAT)
            preview_base64 = base64.b64encode(preview_buffer.getvalue()).decode('utf-8')

            # Statistik aktualisieren
            self.stats['images_processed'] += 1

            return ImageProcessingResult(
                processed_image=bw_img,
                preview_base64=preview_base64,
                original_size=original_size,
                processed_size=bw_img.size,
                info={
                    'original_width': original_size[0],
                    'original_height': original_size[1],
                    'processed_width': bw_img.size[0],
                    'processed_height': bw_img.size[1],
                    'fit_to_label': fit_to_label,
                    'maintain_aspect': maintain_aspect,
                    'scaling_mode': scaling_mode,
                    'dither_enabled': enable_dither,
                    'dither_threshold': dither_threshold,
                    'dither_strength': dither_strength,
                    'contrast_boost': self.settings.get('contrast_boost', DEFAULT_CONTRAST_BOOST),
                    'x_offset': self.settings.get('x_offset', DEFAULT_X_OFFSET),
                    'y_offset': self.settings.get('y_offset', DEFAULT_Y_OFFSET),
                    'dithering_preservation_active': True,
                    'scaled_to_printer_width': True
                }
            )

        except Exception as e:
            logger.error(f"Image processing error: {e}")
            return None

    def apply_offsets_to_image(self, img: Image.Image) -> Image.Image:
        """
        TESTVERSION: KOMPLETT DEAKTIVIERT - Gibt Bild 1:1 zurueck
        """
        try:
            logger.info(f"BYPASS: apply_offsets_to_image DEACTIVATED")
            logger.info(f"Input image size: {img.width}x{img.height}")
            logger.info(f"Output: UNCHANGED (no offset processing)")
            return img
        except Exception as e:
            logger.error(f"Error in bypass mode: {e}")
            return img

    def image_to_printer_format(self, img):
        """
        Pixel-zu-Byte-Konvertierung mit strikter Byte-Alignment-Garantie.
        """
        try:
            if img.mode != '1':
                img = img.convert('1')

            width, height = img.size

            logger.info(f"Converting {width}x{height} -> printer format")

            if width != self.width_pixels:
                logger.info(f"DITHER-SAFE RESIZE: {width}px -> {self.width_pixels}px (preserving dithering)")
                if abs(width - self.width_pixels) <= 10:
                    img = img.resize((self.width_pixels, height), Image.Resampling.LANCZOS)
                else:
                    logger.warning(f"Large resize {width} -> {self.width_pixels} may affect dithering quality")
                    img = img.resize((self.width_pixels, height), Image.Resampling.LANCZOS)
                width = self.width_pixels
            else:
                logger.info(f"Image already correct width: {width}px - preserving dithering")

            pixels = list(img.getdata())

            logger.info(f"Processing {width}x{height} (exactly {self.width_pixels} pixels per line)")

            image_bytes = []

            for y in range(height):
                line_bytes = [0] * self.bytes_per_line

                for pixel_x in range(self.width_pixels):
                    pixel_idx = y * width + pixel_x

                    if pixel_idx < len(pixels):
                        pixel_value = pixels[pixel_idx]
                    else:
                        pixel_value = 1  # Weiss als Fallback

                    byte_index = pixel_x // 8
                    bit_index = pixel_x % 8

                    if pixel_value == 0:  # PIL: 0 = schwarz
                        line_bytes[byte_index] |= (1 << (7 - bit_index))

                if len(line_bytes) != self.bytes_per_line:
                    logger.error(f"CRITICAL: Line {y} has {len(line_bytes)} bytes, expected {self.bytes_per_line}")
                    return None

                image_bytes.extend(line_bytes)

            final_bytes = bytes(image_bytes)
            expected_size = height * self.bytes_per_line

            logger.info(f"Converted to {len(final_bytes)} bytes (expected: {expected_size})")

            if len(final_bytes) != expected_size:
                logger.error(f"Size mismatch {len(final_bytes)} != {expected_size}")
                return None

            if len(final_bytes) % self.bytes_per_line != 0:
                logger.error(f"Not aligned to {self.bytes_per_line}-byte boundaries")
                return None

            logger.info(f"Perfect byte alignment guaranteed")
            return final_bytes

        except Exception as e:
            logger.error(f"Image format conversion error: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return None
