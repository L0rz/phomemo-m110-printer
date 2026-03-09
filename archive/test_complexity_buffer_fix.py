#!/usr/bin/env python3
"""
KOMPLEXITÄTS-BASIERTE BUFFER-LÖSUNG
Problem identifiziert: Komplexe Bildbereiche verursachen Buffer-Overflow
Lösung: Dynamische Segmentierung basierend auf lokaler Komplexität
"""

import sys
import time
import logging
from PIL import Image
import os

from printer_controller import EnhancedPhomemoM110
from config import *

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def load_real_test_image():
    """Lädt das echte Test-PNG"""
    try:
        test_png_path = "2025-08-15 16_49_38-Kamera (Benutzerdefiniert).png"
        
        if os.path.exists(test_png_path):
            img = Image.open(test_png_path)
            if img.mode != '1':
                img = img.convert('L').convert('1')
            logger.info(f"✅ Loaded real test PNG: {img.size}")
            return img
        else:
            logger.error(f"❌ PNG not found: {test_png_path}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error loading PNG: {e}")
        return None

def analyze_image_complexity_regions(img):
    """Analysiert die Komplexität verschiedener Bildbereiche"""
    
    if img.width != 384:
        # Auf 384px anpassen
        img = img.resize((384, img.height), Image.NEAREST)
    
    pixels = list(img.getdata())
    width, height = img.size
    
    # Analysiere in 1cm-Segmenten (etwa 38 Pixel bei 384px Gesamtbreite)
    segment_width = 38
    segments = []
    
    for segment_start in range(0, width, segment_width):
        segment_end = min(segment_start + segment_width, width)
        
        # Zähle non-zero Pixels in diesem Segment
        segment_non_zero = 0
        segment_total = 0
        
        for y in range(height):
            for x in range(segment_start, segment_end):
                pixel_idx = y * width + x
                if pixel_idx < len(pixels):
                    if pixels[pixel_idx] == 0:  # Schwarz
                        segment_non_zero += 1
                    segment_total += 1
        
        if segment_total > 0:
            complexity = segment_non_zero / segment_total
        else:
            complexity = 0.0
        
        segments.append({
            'start_x': segment_start,
            'end_x': segment_end,
            'width': segment_end - segment_start,
            'complexity': complexity,
            'non_zero_pixels': segment_non_zero,
            'total_pixels': segment_total
        })
    
    return segments

def create_segmented_transmission_approach(img):
    """Erstellt einen segmentierten Übertragungsansatz basierend auf Komplexität"""
    
    try:
        # Analysiere Komplexität
        segments = analyze_image_complexity_regions(img)
        
        logger.info("🔍 IMAGE COMPLEXITY ANALYSIS:")
        for i, segment in enumerate(segments):
            logger.info(f"   Segment {i:2d}: x={segment['start_x']:3d}-{segment['end_x']:3d}, "
                       f"complexity={segment['complexity']:.1%}, "
                       f"non-zero={segment['non_zero_pixels']:4d}")
        
        # Identifiziere kritische Segmente (> 8% Komplexität)
        critical_segments = [s for s in segments if s['complexity'] > 0.08]
        
        if critical_segments:
            logger.warning(f"⚠️ Found {len(critical_segments)} critical segments (>8% complexity)")
            for segment in critical_segments:
                logger.warning(f"   Critical: x={segment['start_x']}-{segment['end_x']}, "
                              f"complexity={segment['complexity']:.1%}")
        else:
            logger.info("✅ No critical segments found")
        
        return segments
        
    except Exception as e:
        logger.error(f"❌ Segmentation analysis error: {e}")
        return None

def test_complexity_based_fixes():
    """Testet Komplexitäts-basierte Lösungsansätze"""
    logger.info("🔧 COMPLEXITY-BASED BUFFER FIX")
    
    try:
        printer = EnhancedPhomemoM110(PRINTER_MAC)
        
        if not printer.is_connected():
            if not printer.connect_bluetooth():
                logger.error("❌ Cannot connect to printer")
                return False
        
        # Lade echtes Bild
        real_img = load_real_test_image()
        if not real_img:
            logger.error("❌ Could not load real image")
            return False
        
        # Analysiere Komplexität
        segments = create_segmented_transmission_approach(real_img)
        if not segments:
            return False
        
        print(f"\n🧪 COMPLEXITY-BASED FIXES")
        print(f"Testing different approaches to handle complex regions")
        print(f"")
        
        # Test-Ansätze
        approaches = [
            ("1. Ultra Conservative (10x slower)", 10.0),
            ("2. Adaptive Extreme (5x slower)", 5.0),
            ("3. Smart Segmentation", "smart"),
            ("4. Complexity Threshold", "threshold"),
        ]
        
        for approach_name, approach_config in approaches:
            logger.info(f"\n📤 {approach_name}")
            
            print(f"Test {approach_name}? (y/n/s): ", end="")
            response = input()
            
            if response.lower().startswith('s'):
                break
            elif not response.lower().startswith('y'):
                continue
            
            try:
                # Backup original settings
                original_multiplier = printer.settings.get('timing_multiplier', 1.0)
                original_adaptive = printer.settings.get('adaptive_speed_enabled', True)
                
                if isinstance(approach_config, float):
                    # Einfache Verlangsamung
                    printer.update_settings({
                        'timing_multiplier': approach_config,
                        'adaptive_speed_enabled': True
                    })
                
                elif approach_config == "smart":
                    # Smart Segmentation: Verschiedene Delays für verschiedene Komplexitäten
                    printer.update_settings({
                        'timing_multiplier': 1.0,
                        'adaptive_speed_enabled': True,
                        'min_complexity_for_slow': 0.05,  # Schon bei 5% langsam
                        'max_complexity_for_fast': 0.02,  # Nur unter 2% schnell
                    })
                
                elif approach_config == "threshold":
                    # Threshold: Alles über 8% wird ultra-langsam
                    printer.update_settings({
                        'timing_multiplier': 2.0,  # Generell 2x langsamer
                        'adaptive_speed_enabled': True,
                        'min_complexity_for_slow': 0.06,  # Slow ab 6%
                        'force_slow_for_complex': True,
                    })
                
                # Drucke mit angepassten Einstellungen
                success = printer.print_image_immediate(real_img)
                
                if success:
                    logger.info(f"✅ {approach_name} completed")
                    print(f"📝 Check result:")
                    print(f"   - Any shifting/alignment issues?")
                    print(f"   - Image quality preserved?")
                    
                    quality_check = input(f"   Is this result PERFECT? (y/n): ")
                    if quality_check.lower().startswith('y'):
                        logger.info(f"🎉 PERFECT SOLUTION FOUND: {approach_name}")
                        print(f"🎯 Success! Configuration:")
                        if isinstance(approach_config, float):
                            print(f"   timing_multiplier: {approach_config}")
                        else:
                            print(f"   approach: {approach_config}")
                            print(f"   current settings: {printer.settings}")
                        return True
                    
                    input(f"   Press Enter to continue...")
                else:
                    logger.error(f"❌ {approach_name} failed")
                
                # Restore original settings
                printer.update_settings({
                    'timing_multiplier': original_multiplier,
                    'adaptive_speed_enabled': original_adaptive
                })
                
            except Exception as e:
                logger.error(f"❌ {approach_name} error: {e}")
        
        print(f"\n📊 COMPLEXITY ANALYSIS SUMMARY:")
        
        # Zeige Komplexitäts-Verteilung
        high_complexity_segments = [s for s in segments if s['complexity'] > 0.08]
        medium_complexity_segments = [s for s in segments if 0.05 < s['complexity'] <= 0.08]
        low_complexity_segments = [s for s in segments if s['complexity'] <= 0.05]
        
        print(f"High complexity segments (>8%): {len(high_complexity_segments)}")
        print(f"Medium complexity segments (5-8%): {len(medium_complexity_segments)}")
        print(f"Low complexity segments (≤5%): {len(low_complexity_segments)}")
        
        if high_complexity_segments:
            print(f"\n⚠️ Problem areas (high complexity):")
            for segment in high_complexity_segments:
                cm_position = segment['start_x'] / 384 * 10  # Approximation in cm
                print(f"   Position ~{cm_position:.1f}cm: {segment['complexity']:.1%} complexity")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Complexity-based fix error: {e}")
        return False

def main():
    logger.info("🔧 COMPLEXITY-BASED BUFFER FIX")
    logger.info("=" * 60)
    logger.info("Problem: Complex image regions cause buffer overflow")
    logger.info("Solution: Dynamic timing based on local complexity")
    logger.info("=" * 60)
    
    success = test_complexity_based_fixes()
    
    if success:
        logger.info("✅ Complexity-based fix test completed")
    else:
        logger.info("❌ No perfect solution found yet")
        print(f"\n💡 Alternative approach:")
        print(f"   Consider reducing image complexity before printing")
        print(f"   Or implement line-by-line complexity analysis")

if __name__ == "__main__":
    main()
