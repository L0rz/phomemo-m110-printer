#!/usr/bin/env python3
"""
Quick Test der neuen Adaptive Speed Control Implementierung
Überprüft, ob alle neuen Funktionen korrekt funktionieren
"""

import sys
import time
import logging
from PIL import Image, ImageDraw

# Logging für saubere Ausgabe
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

def test_imports():
    """Testet, ob alle neuen Imports funktionieren"""
    try:
        from printer_controller import EnhancedPhomemoM110, TransmissionSpeed
        from config import DEFAULT_SETTINGS
        
        logger.info("✅ Imports successful")
        
        # Teste neue Enum
        speeds = [speed.value for speed in TransmissionSpeed]
        logger.info(f"✅ TransmissionSpeed enum: {speeds}")
        
        # Teste neue Config-Einstellungen
        adaptive_settings = {k: v for k, v in DEFAULT_SETTINGS.items() if 'adaptive' in k}
        logger.info(f"✅ Adaptive settings: {list(adaptive_settings.keys())}")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False

def test_adaptive_methods():
    """Testet die neuen Adaptive Speed Methoden"""
    try:
        from printer_controller import EnhancedPhomemoM110
        from config import PRINTER_MAC
        
        printer = EnhancedPhomemoM110(PRINTER_MAC)
        
        # Test 1: Komplexitäts-Berechnung
        test_data = b'\x00' * 1000 + b'\xFF' * 100  # 10% complexity
        complexity = printer.calculate_image_complexity(test_data)
        expected = 0.1
        if abs(complexity - expected) < 0.01:
            logger.info(f"✅ Complexity calculation: {complexity:.3f} (expected ~{expected})")
        else:
            logger.error(f"❌ Complexity calculation wrong: {complexity:.3f} (expected ~{expected})")
            return False
        
        # Test 2: Speed Determination
        speed = printer.determine_transmission_speed(complexity)
        logger.info(f"✅ Speed determination: {complexity:.1%} → {speed.value}")
        
        # Test 3: Speed Config
        config = printer.get_speed_config(speed)
        required_keys = ['block_delay', 'init_delay', 'description']
        if all(key in config for key in required_keys):
            logger.info(f"✅ Speed config: {config['description']}")
        else:
            logger.error(f"❌ Speed config missing keys: {config.keys()}")
            return False
        
        # Test 4: Adaptive Speed Test (ohne echte Bilder)
        logger.info("✅ Testing adaptive speed analysis...")
        test_results = printer.test_adaptive_speed_with_images()
        if test_results['successful_tests'] >= 3:
            logger.info(f"✅ Adaptive speed test: {test_results['successful_tests']} tests passed")
        else:
            logger.error(f"❌ Adaptive speed test failed: only {test_results['successful_tests']} tests passed")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Adaptive methods test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_settings_integration():
    """Testet die Integration mit den Settings"""
    try:
        from printer_controller import EnhancedPhomemoM110
        from config import PRINTER_MAC
        
        printer = EnhancedPhomemoM110(PRINTER_MAC)
        
        # Test Settings Update
        original_multiplier = printer.settings.get('timing_multiplier', 1.0)
        
        # Teste Settings-Update
        printer.update_settings({'timing_multiplier': 1.5})
        
        if printer.settings.get('timing_multiplier') == 1.5:
            logger.info("✅ Settings update works")
        else:
            logger.error("❌ Settings update failed")
            return False
        
        # Teste angepasste Speed Config
        from printer_controller import TransmissionSpeed
        config = printer.get_speed_config(TransmissionSpeed.NORMAL)
        
        if '×1.5 slower' in config['description']:
            logger.info("✅ Timing multiplier applied to config")
        else:
            logger.error("❌ Timing multiplier not applied")
            return False
        
        # Settings zurücksetzen
        printer.update_settings({'timing_multiplier': original_multiplier})
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Settings integration test error: {e}")
        return False

def main():
    """Haupttest-Funktion"""
    logger.info("🧪 ADAPTIVE SPEED CONTROL - IMPLEMENTATION TEST")
    logger.info("=" * 60)
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: Imports
    logger.info("\n🔧 TEST 1: Imports and Basic Setup")
    if test_imports():
        tests_passed += 1
    
    # Test 2: Adaptive Methods
    logger.info("\n🚀 TEST 2: Adaptive Speed Methods")
    if test_adaptive_methods():
        tests_passed += 1
    
    # Test 3: Settings Integration
    logger.info("\n⚙️ TEST 3: Settings Integration")
    if test_settings_integration():
        tests_passed += 1
    
    # Ergebnis
    logger.info("\n" + "=" * 60)
    logger.info(f"🏁 TEST RESULTS: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        logger.info("🎉 ALL TESTS PASSED!")
        logger.info("✅ Adaptive Speed Control is ready to use!")
        logger.info("\n💡 Next steps:")
        logger.info("   1. Run: python test_adaptive_speed_control.py")
        logger.info("   2. Test with your problematic images")
        logger.info("   3. Check logs for automatic speed detection")
        return True
    else:
        logger.error("❌ SOME TESTS FAILED!")
        logger.error("Check the error messages above for details")
        return False

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\n⏹️ Test interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
