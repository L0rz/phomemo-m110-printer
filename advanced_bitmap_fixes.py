#!/usr/bin/env python3
"""
Advanced Bitmap Transmission Fix
Falls die erste Korrektur nicht ausreicht - weitere Optimierungen
"""

def send_bitmap_advanced_fix(self, image_data: bytes, height: int) -> bool:
    """
    Erweiterte Bitmap-Übertragung mit zusätzlichen Fixes
    Für hartnäckige Drift-Probleme
    """
    try:
        width_bytes = self.bytes_per_line
        
        logger.info(f"📤 ADVANCED FIX: Starting enhanced bitmap transmission")
        
        # ERWEITERTE DRUCKER-VORBEREITUNG
        logger.info("🔧 ADVANCED: Extended printer preparation...")
        
        # 1. Mehrfache Initialisierung für hartnäckige Fälle
        for i in range(2):  # 2x Initialize
            if not self.send_command(b'\x1b\x40'):  # ESC @
                logger.error(f"❌ Init attempt {i+1} failed")
                return False
            time.sleep(0.3)
        
        # 2. Print Speed (langsamste Einstellung für Stabilität)
        speed_cmd = b'\x1b\x4e\x0d\x01'  # ESC N 13 1 (slowest)
        if not self.send_command(speed_cmd):
            logger.warning("⚠️ Speed setting failed")
        time.sleep(0.1)
        
        # 3. Print Density (mittlere Einstellung)
        density_cmd = b'\x1b\x4e\x04\x08'  # ESC N 4 8 (medium)
        if not self.send_command(density_cmd):
            logger.warning("⚠️ Density setting failed")
        time.sleep(0.1)
        
        # 4. Media Type (Label with gaps)
        media_cmd = b'\x1f\x11\x0a'  # Label with gaps
        if not self.send_command(media_cmd):
            logger.warning("⚠️ Media type setting failed")
        time.sleep(0.2)
        
        # 5. Position und Justification
        if not self.send_command(b'\x1b\x61\x00'):  # Left align
            logger.warning("⚠️ Alignment failed")
        time.sleep(0.1)
        
        # ZEILEN-WEISE ÜBERTRAGUNG (Alternative zu Chunks)
        # Bei hartnäckigem Drift: Zeile für Zeile senden
        logger.info("📏 ADVANCED: Line-by-line transmission...")
        
        lines_per_chunk = 10  # Wenige Zeilen pro Chunk
        total_lines = height
        bytes_per_line = width_bytes
        
        for line_start in range(0, total_lines, lines_per_chunk):
            line_end = min(line_start + lines_per_chunk, total_lines)
            chunk_lines = line_end - line_start
            
            # Chunk-Header für diese Zeilen
            xL = bytes_per_line & 0xFF
            xH = (bytes_per_line >> 8) & 0xFF
            yL = chunk_lines & 0xFF
            yH = (chunk_lines >> 8) & 0xFF
            
            chunk_header = bytes([0x1D, 0x76, 0x30, 0x00, xL, xH, yL, yH])
            
            if not self.send_command(chunk_header):
                logger.error(f"❌ Line chunk header failed: lines {line_start}-{line_end}")
                return False
            time.sleep(0.1)
            
            # Daten für diese Zeilen
            start_byte = line_start * bytes_per_line
            end_byte = line_end * bytes_per_line
            chunk_data = image_data[start_byte:end_byte]
            
            # Chunk-Daten senden
            if not self.send_command(chunk_data):
                logger.error(f"❌ Line chunk data failed: lines {line_start}-{line_end}")
                return False
            
            # Progress
            progress = (line_end / total_lines) * 100
            logger.info(f"📊 Line progress: {line_end}/{total_lines} lines ({progress:.1f}%)")
            
            # Pause zwischen Zeilen-Chunks
            time.sleep(0.05)
        
        # POST-PROCESSING
        logger.info("🔄 ADVANCED: Enhanced post-processing...")
        
        # Feed und Stabilisierung
        time.sleep(0.3)
        self.send_command(b'\x1b\x64\x02')  # Feed 2 lines
        time.sleep(0.2)
        
        # Position stabilisieren
        self.send_command(b'\x1b\x40')  # Final reset
        time.sleep(0.2)
        
        logger.info("✅ ADVANCED FIX: Enhanced bitmap transmission completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ ADVANCED FIX failed: {e}")
        return False

# ALTERNATIVE: Stream-basierte Übertragung
def send_bitmap_stream_mode(self, image_data: bytes, height: int) -> bool:
    """
    Stream-basierte Übertragung - kontinuierlicher Datenstrom
    Für Fälle wo Chunk-basierte Übertragung Probleme verursacht
    """
    try:
        logger.info("🌊 STREAM MODE: Continuous data transmission")
        
        # Standard-Initialisierung
        self.send_command(b'\x1b\x40')  # ESC @
        time.sleep(0.3)
        self.send_command(b'\x1b\x61\x00')  # Left align
        time.sleep(0.1)
        
        # Einmalige Bitmap-Header für gesamtes Bild
        width_bytes = self.bytes_per_line
        xL = width_bytes & 0xFF
        xH = (width_bytes >> 8) & 0xFF
        yL = height & 0xFF
        yH = (height >> 8) & 0xFF
        
        header = bytes([0x1D, 0x76, 0x30, 0x00, xL, xH, yL, yH])
        
        if not self.send_command(header):
            logger.error("❌ Stream header failed")
            return False
        time.sleep(0.2)
        
        # KONTINUIERLICHE ÜBERTRAGUNG
        # Gesamte Daten in einem Stück - kein Chunking
        logger.info(f"🌊 Sending entire bitmap as continuous stream: {len(image_data)} bytes")
        
        if not self.send_command(image_data):
            logger.error("❌ Stream data transmission failed")
            return False
        
        # Längere Pause für große Datenmengen
        time.sleep(1.0)
        
        # Post-processing
        self.send_command(b'\x1b\x64\x02')  # Feed
        time.sleep(0.2)
        
        logger.info("✅ STREAM MODE: Continuous transmission completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ STREAM MODE failed: {e}")
        return False

# DEBUGGING: Packet-Level-Analyse
def debug_bitmap_transmission(self, image_data: bytes, height: int):
    """
    Debugging-Funktion für detaillierte Packet-Analyse
    """
    logger.info("🔍 DEBUG: Analyzing bitmap transmission packets")
    
    width_bytes = self.bytes_per_line
    
    # Berechne erwartete Packet-Struktur
    total_pixels = len(image_data) * 8
    total_lines = height
    pixels_per_line = width_bytes * 8
    
    logger.info(f"🔍 Bitmap analysis:")
    logger.info(f"   Total pixels: {total_pixels}")
    logger.info(f"   Total lines: {total_lines}")
    logger.info(f"   Pixels per line: {pixels_per_line}")
    logger.info(f"   Bytes per line: {width_bytes}")
    logger.info(f"   Expected data size: {total_lines * width_bytes} bytes")
    logger.info(f"   Actual data size: {len(image_data)} bytes")
    
    # Validiere Daten-Integrität
    if len(image_data) != total_lines * width_bytes:
        logger.error(f"❌ Data size mismatch!")
        logger.error(f"   Expected: {total_lines * width_bytes}")
        logger.error(f"   Actual: {len(image_data)}")
        return False
    
    # Analysiere erste und letzte Zeilen
    first_line = image_data[:width_bytes]
    last_line = image_data[-width_bytes:]
    
    logger.info(f"🔍 First line data: {first_line[:8].hex()} ... {first_line[-8:].hex()}")
    logger.info(f"🔍 Last line data: {last_line[:8].hex()} ... {last_line[-8:].hex()}")
    
    # Suche nach Pattern die Drift verursachen könnten
    consecutive_zeros = 0
    consecutive_ones = 0
    max_consecutive_zeros = 0
    max_consecutive_ones = 0
    
    for byte in image_data:
        if byte == 0x00:
            consecutive_zeros += 1
            consecutive_ones = 0
            max_consecutive_zeros = max(max_consecutive_zeros, consecutive_zeros)
        elif byte == 0xFF:
            consecutive_ones += 1
            consecutive_zeros = 0
            max_consecutive_ones = max(max_consecutive_ones, consecutive_ones)
        else:
            consecutive_zeros = 0
            consecutive_ones = 0
    
    logger.info(f"🔍 Pattern analysis:")
    logger.info(f"   Max consecutive 0x00 bytes: {max_consecutive_zeros}")
    logger.info(f"   Max consecutive 0xFF bytes: {max_consecutive_ones}")
    
    if max_consecutive_zeros > 50 or max_consecutive_ones > 50:
        logger.warning("⚠️ Long sequences detected - potential drift cause!")
    
    return True
