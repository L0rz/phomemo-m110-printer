#!/usr/bin/env python3
"""
MINIMALER TEST: Direkter Bluetooth-Test ohne komplexe Bildverarbeitung
Testet ob das Problem in der Bluetooth-Übertragung liegt
"""

import sys
import os
import time
import logging

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Module importieren
from printer_controller import EnhancedPhomemoM110
from config import *

def create_minimal_test_data():
    """Erstellt minimale, kontrollierte Testdaten"""
    logger.info("📦 Creating minimal test data")
    
    # Nur 10 Zeilen, jede Zeile = exakt 48 Bytes
    # Erste 5 Zeilen: Alle Bytes = 0xFF (komplett schwarz)
    # Zweite 5 Zeilen: Alle Bytes = 0x00 (komplett weiß)
    
    height = 10
    line_bytes = []
    
    for y in range(height):
        if y < 5:
            # Schwarze Zeilen
            line = [0xFF] * PRINTER_BYTES_PER_LINE
        else:
            # Weiße Zeilen  
            line = [0x00] * PRINTER_BYTES_PER_LINE
        
        line_bytes.extend(line)
    
    test_data = bytes(line_bytes)
    expected_size = height * PRINTER_BYTES_PER_LINE
    
    logger.info(f"✅ Created minimal test data:")
    logger.info(f"   Height: {height} lines")
    logger.info(f"   Data size: {len(test_data)} bytes")
    logger.info(f"   Expected: {expected_size} bytes")
    logger.info(f"   Pattern: 5 black lines + 5 white lines")
    
    return test_data, height

def test_direct_bluetooth_transmission():
    """Testet direkte Bluetooth-Übertragung ohne Bildverarbeitung"""
    logger.info("📡 TESTING: Direct Bluetooth transmission")
    
    try:
        printer = EnhancedPhomemoM110(PRINTER_MAC)
        
        # Verbindung prüfen
        if not printer.is_connected():
            logger.info("🔌 Connecting to printer...")
            if not printer.connect_bluetooth():
                logger.error("❌ Cannot connect to printer!")
                return False
        
        # Minimale Testdaten erstellen
        test_data, height = create_minimal_test_data()
        
        # DIREKTER Bluetooth-Test mit send_bitmap
        logger.info("📤 Sending minimal test data via Bluetooth...")
        logger.info("🎯 This test eliminates image processing as error source")
        
        success = printer.send_bitmap(test_data, height)
        
        if success:
            logger.info("✅ DIRECT BLUETOOTH TEST: Success!")
            logger.info("👀 Check printed result:")
            logger.info("   ✅ Should show 5 completely black lines")
            logger.info("   ✅ Followed by 5 completely white lines")
            logger.info("   ❌ ANY horizontal shift indicates bluetooth/timing problem")
            logger.info("")
            logger.info("🔍 If there's STILL a shift at 7mm:")
            logger.info("   → Problem is in Bluetooth transmission")
            logger.info("   → NOT in image processing!")
            return True
        else:
            logger.error("❌ DIRECT BLUETOOTH TEST: Failed!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Direct bluetooth test error: {e}")
        return False

def test_very_slow_transmission():
    """Testet sehr langsame Übertragung mit längeren Pausen"""
    logger.info("🐌 TESTING: Very slow transmission with long delays")
    
    try:
        printer = EnhancedPhomemoM110(PRINTER_MAC)
        
        if not printer.is_connected():
            if not printer.connect_bluetooth():
                logger.error("❌ Cannot connect to printer!")
                return False
        
        # Noch einfacheres Testmuster: Nur 3 Zeilen
        height = 3
        line_data = []
        
        # Zeile 1: Komplett schwarz
        line_data.extend([0xFF] * PRINTER_BYTES_PER_LINE)
        # Zeile 2: Komplett weiß  
        line_data.extend([0x00] * PRINTER_BYTES_PER_LINE)
        # Zeile 3: Komplett schwarz
        line_data.extend([0xFF] * PRINTER_BYTES_PER_LINE)
        
        test_data = bytes(line_data)
        
        logger.info("🐌 Sending with ULTRA-SLOW transmission...")
        
        # MANUELLER SEND-PROZESS mit extremen Verzögerungen
        width_bytes = PRINTER_BYTES_PER_LINE
        
        # 1. Init mit langer Pause
        if not printer.send_command(b'\x1b\x40'):  # ESC @
            return False
        time.sleep(0.5)  # 500ms!
        
        # 2. Header mit langer Pause
        header = bytes([
            0x1D, 0x76, 0x30, 0,                    # GS v 0
            width_bytes & 0xFF, (width_bytes >> 8) & 0xFF,  # Width
            height & 0xFF, (height >> 8) & 0xFF             # Height
        ])
        
        if not printer.send_command(header):
            return False
        time.sleep(0.3)  # 300ms!
        
        # 3. Daten in SEHR kleinen Blöcken (nur 48 Bytes = 1 Zeile)
        logger.info("📤 Sending line by line with delays...")
        for line_num in range(height):
            line_start = line_num * PRINTER_BYTES_PER_LINE
            line_end = line_start + PRINTER_BYTES_PER_LINE
            line_bytes = test_data[line_start:line_end]
            
            logger.info(f"   Sending line {line_num + 1}/{height}...")
            if not printer.send_command(line_bytes):
                logger.error(f"❌ Failed to send line {line_num + 1}")
                return False
            
            time.sleep(0.1)  # 100ms zwischen Zeilen!
        
        time.sleep(0.5)  # 500ms final
        
        logger.info("✅ ULTRA-SLOW TRANSMISSION: Completed!")
        logger.info("👀 Check if this eliminates the 7mm shift:")
        logger.info("   ✅ Perfect alignment = Bluetooth timing problem")
        logger.info("   ❌ Still shifted = Hardware/firmware problem")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ultra-slow transmission error: {e}")
        return False

def test_line_by_line_verification():
    """Testet Zeile-für-Zeile mit Verifikation"""
    logger.info("📋 TESTING: Line-by-line with verification")
    
    try:
        printer = EnhancedPhomemoM110(PRINTER_MAC)
        
        if not printer.is_connected():
            if not printer.connect_bluetooth():
                return False
        
        # Sehr einfaches Muster: Jede Zeile anders
        height = 5
        test_lines = []
        
        for line_num in range(height):
            line = [0x00] * PRINTER_BYTES_PER_LINE  # Start mit weiß
            
            # Jede Zeile hat schwarze Pixel an verschiedenen Positionen
            if line_num == 0:
                # Zeile 0: Erste 8 Pixel schwarz (Byte 0 = 0xFF)
                line[0] = 0xFF
            elif line_num == 1:
                # Zeile 1: Pixel 8-15 schwarz (Byte 1 = 0xFF)  
                line[1] = 0xFF
            elif line_num == 2:
                # Zeile 2: Pixel 16-23 schwarz (Byte 2 = 0xFF)
                line[2] = 0xFF
            elif line_num == 3:
                # Zeile 3: Pixel 24-31 schwarz (Byte 3 = 0xFF)
                line[3] = 0xFF
            elif line_num == 4:
                # Zeile 4: Letzten 8 Pixel schwarz (Byte 47 = 0xFF)
                line[47] = 0xFF
            
            test_lines.extend(line)
        
        test_data = bytes(test_lines)
        
        logger.info("📋 Sending line-verification pattern...")
        logger.info("   Line 0: Black pixels 0-7 (leftmost)")
        logger.info("   Line 1: Black pixels 8-15")  
        logger.info("   Line 2: Black pixels 16-23")
        logger.info("   Line 3: Black pixels 24-31")
        logger.info("   Line 4: Black pixels 376-383 (rightmost)")
        
        success = printer.send_bitmap(test_data, height)
        
        if success:
            logger.info("✅ LINE VERIFICATION: Sent successfully!")
            logger.info("👀 Check printed pattern:")
            logger.info("   ✅ Each line should have black pixels at different X-positions")
            logger.info("   🔍 If pattern is shifted/distorted:")
            logger.info("      → Measure EXACTLY where shift occurs")
            logger.info("      → Count pixels from left edge")
            return True
        else:
            logger.error("❌ LINE VERIFICATION: Failed!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Line verification error: {e}")
        return False

def main():
    """Hauptfunktion für Bluetooth-Debugging"""
    logger.info("=" * 60)
    logger.info("📡 PHOMEMO M110 - BLUETOOTH TRANSMISSION DEBUG")
    logger.info("=" * 60)
    logger.info("Testing if the 7mm shift is caused by Bluetooth transmission")
    logger.info("NOT by image processing (which we already fixed)")
    logger.info("=" * 60)
    
    tests_completed = 0
    
    # Test 1: Direkter Bluetooth-Test
    logger.info("\n📡 TEST 1: Direct Bluetooth transmission")
    print("Run direct bluetooth test? (y/n): ", end="")
    if input().lower().startswith('y'):
        if test_direct_bluetooth_transmission():
            logger.info("✅ TEST 1: COMPLETED")
        else:
            logger.error("❌ TEST 1: FAILED")
        tests_completed += 1
    
    # Test 2: Ultra-langsame Übertragung
    logger.info("\n🐌 TEST 2: Ultra-slow transmission")
    print("Run ultra-slow transmission test? (y/n): ", end="")
    if input().lower().startswith('y'):
        if test_very_slow_transmission():
            logger.info("✅ TEST 2: COMPLETED")
        else:
            logger.error("❌ TEST 2: FAILED")
        tests_completed += 1
    
    # Test 3: Zeile-für-Zeile-Verifikation
    logger.info("\n📋 TEST 3: Line-by-line verification")
    print("Run line verification test? (y/n): ", end="")
    if input().lower().startswith('y'):
        if test_line_by_line_verification():
            logger.info("✅ TEST 3: COMPLETED")
        else:
            logger.error("❌ TEST 3: FAILED")
        tests_completed += 1
    
    # Auswertung
    logger.info("\n" + "=" * 60)
    logger.info(f"🏁 BLUETOOTH DEBUG COMPLETED: {tests_completed} tests run")
    
    if tests_completed > 0:
        logger.info("🔍 ANALYSIS:")
        logger.info("   If ALL tests still show 7mm shift:")
        logger.info("   → Problem is in Bluetooth/Hardware level")
        logger.info("   → May need different transmission strategy")
        logger.info("")
        logger.info("   If SLOW transmission fixes it:")
        logger.info("   → Bluetooth timing/buffer problem")
        logger.info("   → Need to add delays in send_bitmap")
        logger.info("")
        logger.info("   If shifts occur at different positions:")
        logger.info("   → Data corruption during transmission")
        logger.info("   → Need smaller chunks or error checking")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
