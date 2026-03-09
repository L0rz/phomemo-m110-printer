#!/usr/bin/env python3
"""
Temp Fix für send_bitmap
Stellt die ursprünglich funktionierende Version wieder her
"""

def send_bitmap_fixed(self, image_data: bytes, height: int) -> bool:
    """Sendet Bitmap an Drucker mit bewährter Enhanced Anti-Drift Methode (URSPRÜNGLICH FUNKTIONIEREND)"""
    try:
        width_bytes = self.bytes_per_line
        m = 0

        logger.info(f"📤 RESTORED WORKING: Starting bitmap transmission: {len(image_data)} bytes, {height}px high")
        
        # ENHANCED Anti-Drift: Immer eine Stabilisierungs-Pause, auch beim ersten Druck
        min_interval = self.settings.get('anti_drift_interval', 2.0)
        
        if hasattr(self, 'last_print_time'):
            time_since_last = time.time() - self.last_print_time
            if time_since_last < min_interval:
                sleep_time = min_interval - time_since_last
                logger.info(f"⏱️ Anti-drift pause ({min_interval}s setting): {sleep_time:.2f}s")
                time.sleep(sleep_time)
        else:
            # ERSTE BILD-DRUCK: Extra-Stabilisierung
            logger.info(f"🔄 First image print - initial stabilization pause: {min_interval}s")
            time.sleep(min_interval)
        
        # DRUCKER-VORBEREITUNG für Bilder (kritisch!)
        logger.info("🔧 Pre-image printer stabilization...")
        
        # Sanfte Drucker-Vorbereitung für Bilder
        if not self.send_command(b'\x1b\x40'):  # ESC @ - Initialize printer
            logger.warning("⚠️ Printer initialization failed")
        time.sleep(0.2)  # Längere Pause für Bilder
        
        # Position-Konsistenz für Bilder
        if not self.send_command(b'\x1b\x64\x00'):  # ESC d 0 - Horizontal position to 0
            logger.warning("⚠️ Position reset failed")
        time.sleep(0.1)

        # BITMAP-HEADER mit korrekten Dimensionen
        xL = width_bytes & 0xFF
        xH = (width_bytes >> 8) & 0xFF
        yL = height & 0xFF
        yH = (height >> 8) & 0xFF
        header = bytes([0x1D, 0x76, 0x30, m, xL, xH, yL, yH])

        logger.info(f"📋 Bitmap header: width_bytes={width_bytes}, height={height}")
        if not self.send_command(header):
            logger.error("❌ Failed to send bitmap header")
            return False
        time.sleep(0.1)  # Pause nach Header

        # BEWÄHRTE ULTRA-KLEINE Chunks 
        CHUNK = 64  # BEWÄHRTE Größe - funktionierte vorher
        chunks_sent = 0
        total_bytes_sent = 0
        
        logger.info(f"📦 PROVEN ULTRA-SMALL-CHUNKS: Sending {len(image_data)} bytes in {CHUNK}-byte chunks...")
        
        for i in range(0, len(image_data), CHUNK):
            chunk = image_data[i:i+CHUNK]
            
            # BEWÄHRTE RETRY für kontinuierliche Sequenzen
            chunk_success = False
            for attempt in range(7):  # Bewährte Anzahl
                if self.send_command(chunk):
                    chunk_success = True
                    break
                else:
                    logger.warning(f"⚠️ Ultra-small chunk {chunks_sent} attempt {attempt+1} failed, retrying...")
                    # Progressive Retry-Pause: 10ms, 20ms, 30ms, etc.
                    time.sleep(0.01 * (attempt + 1))
            
            if not chunk_success:
                logger.error(f"❌ Failed to send ultra-small chunk {chunks_sent} after 7 attempts")
                return False
            
            chunks_sent += 1
            total_bytes_sent += len(chunk)
            
            # Häufiger Progress für ultra-kleine Chunks
            if chunks_sent % 5 == 0:  
                progress = (total_bytes_sent / len(image_data)) * 100
                logger.info(f"📊 Ultra-small progress: {chunks_sent} chunks ({progress:.1f}%)")
            
            # BEWÄHRTE Pausen für kontinuierliche Sequenzen
            time.sleep(0.03)  # Bewährte Pause
            
            # BEWÄHRTE Extra-Pausen bei jedem 10. Chunk
            if chunks_sent % 10 == 0:
                logger.info(f"🔄 Stabilization pause after {chunks_sent} chunks...")
                time.sleep(0.1)  # Bewährte Extra-Pause

        # BEWÄHRTE POST-PRINT Stabilisierung
        time.sleep(0.2)  # Pause nach Bild-Druck
        
        # Position nach Bild-Druck explizit zurücksetzen
        logger.info("🔄 Post-image position stabilization...")
        self.send_command(b'\x1b\x64\x00')  # Position reset
        time.sleep(0.1)
        
        # Zeitstempel für Anti-Drift tracking
        self.last_print_time = time.time()
        
        logger.info(f"✅ RESTORED WORKING: Bitmap sent successfully: {chunks_sent} chunks, {total_bytes_sent}/{len(image_data)} bytes")
        
        # Validierung
        if total_bytes_sent != len(image_data):
            logger.warning(f"⚠️ Byte count mismatch: sent {total_bytes_sent}, expected {len(image_data)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ RESTORED WORKING: Bitmap send error: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False

# Anweisung zum Ersetzen:
# Ersetze die aktuelle send_bitmap Methode in printer_controller.py 
# mit dem Inhalt dieser Funktion (ohne die def-Zeile)
