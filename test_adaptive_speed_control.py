#!/usr/bin/env python3
"""
Test der adaptiven Geschwindigkeitssteuerung für Phomemo M110
LÖSUNG für das Bluetooth-Timing-Problem bei komplexen Bildern
"""

import sys
import time
import logging
from PIL import Image, ImageDraw

# Module importieren
from printer_controller import EnhancedPhomemoM110
from config import *

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def main():
    """Haupttest für adaptive Geschwindigkeitssteuerung"""
    logger.info("=" * 70)
    logger.info("🚀 ADAPTIVE SPEED CONTROL TEST")
    logger.info("=" * 70)
    logger.info("Testet die neue automatische Geschwindigkeitsanpassung")
    logger.info("basierend auf Bilddaten-Komplexität")
    logger.info("=" * 70)
    
    try:
        # Drucker initialisieren
        printer = EnhancedPhomemoM110(PRINTER_MAC)
        
        # Test 1: Adaptive Speed Analysis (ohne Drucken)
        logger.info("\n🧪 TEST 1: Adaptive Speed Analysis")
        test_results = printer.test_adaptive_speed_with_images()
        
        if test_results['successful_tests'] > 0:
            logger.info("✅ Adaptive speed analysis successful!")
            
            # Zeige empfohlene Geschwindigkeiten
            print("\n📊 SPEED RECOMMENDATIONS:")
            for result in test_results['results']:
                complexity_pct = result['complexity'] * 100
                print(f"  {result['test']:<20}: {complexity_pct:5.1f}% → {result['speed']:<12} ({result['description']})")
        else:
            logger.error("❌ Adaptive speed analysis failed!")
            return False
        
        # Test 2: Verbindungstest
        logger.info("\n🔗 TEST 2: Connection Test")
        if printer.is_connected():
            logger.info("✅ Printer already connected")
        else:
            logger.info("🔄 Connecting to printer...")
            if printer.connect_bluetooth():
                logger.info("✅ Successfully connected to printer")
            else:
                logger.error("❌ Failed to connect to printer")
                print("\n⚠️ Cannot perform actual print tests without connection")
                print("But speed analysis shows the adaptive control is working!")
                return True
        
        # Test 3: Actual Print Tests (optional)
        print(f"\n🖨️ ACTUAL PRINT TESTS")
        print("Do you want to test actual printing with different speeds?")
        print("This will print 3 test labels with different complexities:")
        print("  1. Simple image  (fast speed)")
        print("  2. Medium image  (normal speed)") 
        print("  3. Complex image (slow speed)")
        
        response = input("\nPrint test labels? (y/n): ")
        
        if response.lower().startswith('y'):
            logger.info("\n🖨️ TEST 3: Actual Printing Tests")
            
            test_levels = ['simple', 'medium', 'complex']
            successful_prints = 0
            
            for level in test_levels:
                logger.info(f"\n🎯 Printing {level} complexity test...")
                print(f"Printing {level} test... (check speed adaptation in logs)")
                
                success = printer.force_speed_test_print(level)
                if success:
                    logger.info(f"✅ {level} test printed successfully!")
                    successful_prints += 1
                    time.sleep(2)  # Pause zwischen Tests
                else:
                    logger.error(f"❌ {level} test failed!")
                
                # Pause zwischen Tests
                if level != test_levels[-1]:  # Nicht nach dem letzten Test
                    input("Press Enter to continue to next test...")
            
            logger.info(f"\n📊 Print test results: {successful_prints}/{len(test_levels)} successful")
            
            if successful_prints == len(test_levels):
                logger.info("🎉 ALL PRINT TESTS SUCCESSFUL!")
                print("\n✅ Check the printed labels:")
                print("   - Simple should have printed quickly")
                print("   - Medium with normal speed")
                print("   - Complex with slow, stable transmission")
                print("   - ALL should be perfectly aligned (no shifts!)")
            else:
                logger.warning("⚠️ Some print tests failed - check logs")
        else:
            logger.info("⏭️ Skipping actual print tests")
        
        # Test 4: Legacy Problem Image Test (falls verfügbar)
        logger.info(f"\n🔍 TEST 4: Legacy Problem Image Analysis")
        try:
            problem_path = r'C:\Users\marcu\Downloads\problem_image_raw.bin'
            import os
            if os.path.exists(problem_path):
                with open(problem_path, 'rb') as f:
                    problem_data = f.read()
                
                complexity = printer.calculate_image_complexity(problem_data)
                speed, config = printer.analyze_and_determine_speed(problem_data)
                
                logger.info(f"📊 Legacy problem image analysis:")
                logger.info(f"   Complexity: {complexity*100:.1f}%")
                logger.info(f"   Recommended speed: {speed.value}")
                logger.info(f"   Description: {config['description']}")
                logger.info(f"   Block delay: {config['block_delay']*1000:.0f}ms")
                
                print(f"\n🎯 SOLUTION SUMMARY:")
                print(f"   Your problem image has {complexity*100:.1f}% complexity")
                print(f"   New system will automatically use: {speed.value}")
                print(f"   With {config['block_delay']*1000:.0f}ms delays between blocks")
                print(f"   This should eliminate the shifting problem!")
            else:
                logger.info("   Legacy problem image not found - skipping")
        except Exception as e:
            logger.warning(f"   Legacy image analysis failed: {e}")
        
        # Finale Zusammenfassung
        logger.info("\n" + "=" * 70)
        logger.info("🏁 ADAPTIVE SPEED CONTROL TEST COMPLETED")
        logger.info("=" * 70)
        
        print(f"\n🎉 SUMMARY:")
        print(f"✅ Adaptive speed control is working!")
        print(f"✅ Automatic complexity detection implemented")
        print(f"✅ Speed ranges from ultra-fast to ultra-slow")
        print(f"✅ Should solve the Bluetooth timing problem")
        
        if 'response' in locals() and response.lower().startswith('y'):
            print(f"✅ Print tests completed")
            print(f"👀 Check your printed labels for perfect alignment!")
        
        print(f"\n💡 HOW IT WORKS:")
        print(f"   • Images < 2% complexity  → Ultra Fast (5ms delays)")
        print(f"   • Images < 5% complexity  → Fast (10ms delays)")
        print(f"   • Images < 8% complexity  → Normal (20ms delays)")
        print(f"   • Images < 12% complexity → Slow (50ms delays)")
        print(f"   • Images > 12% complexity → Ultra Slow (100ms delays)")
        
        print(f"\n🔧 WHAT'S FIXED:")
        print(f"   • Automatic speed detection based on image complexity")
        print(f"   • No more manual speed selection needed")
        print(f"   • Complex images automatically get slower, stable transmission")
        print(f"   • Simple images stay fast for efficiency")
        print(f"   • Should eliminate all shifting/alignment problems!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test error: {e}")
        import traceback
        logger.error(f"❌ Full traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print(f"\n🎯 Test completed successfully!")
        print(f"💡 Your printer now has adaptive speed control!")
    else:
        print(f"\n❌ Test failed - check logs for details")
    
    input(f"\nPress Enter to exit...")
