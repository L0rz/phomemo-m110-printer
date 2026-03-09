#!/usr/bin/env python3
"""
KRITISCHER FIX: Komplexitäts-Berechnung korrigieren

PROBLEM: .count(0) zählt NULL-BYTES (0x00 = weiß)
         Aber für Timing brauchen wir KOMPLEXITÄT = Anzahl gesetzter Bits!

LÖSUNG: Zähle tatsächlich komplexe Bytes (mit gesetzten Bits)
"""

import logging
import os
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fix_complexity_calculation():
    """Korrigiert die calculate_image_complexity Methode"""
    
    file_path = 'printer_controller.py'
    
    if not os.path.exists(file_path):
        logger.error(f"❌ {file_path} nicht gefunden!")
        return False
    
    try:
        # Datei lesen
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Backup erstellen
        backup_path = file_path.replace('.py', '_before_complexity_fix.py')
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"✅ Backup erstellt: {backup_path}")
        
        # Alte (falsche) Implementierung
        old_code = """    def calculate_image_complexity(self, image_data: bytes) -> float:
        \"\"\"
        Berechnet die Komplexität der Bilddaten als Prozentsatz non-zero bytes
        
        Args:
            image_data: Raw image bytes vom printer format
            
        Returns:
            float: Komplexität als Dezimalzahl (0.0 = 0%, 1.0 = 100%)
        \"\"\"
        try:
            if not image_data:
                return 0.0
            
            total_bytes = len(image_data)
            zero_bytes = image_data.count(0)
            non_zero_bytes = total_bytes - zero_bytes
            
            complexity = non_zero_bytes / total_bytes
            
            logger.info(f"📊 Image complexity: {complexity*100:.1f}% ({non_zero_bytes}/{total_bytes} non-zero bytes)")
            
            return complexity
            
        except Exception as e:
            logger.error(f"❌ Error calculating image complexity: {e}")
            return 0.1  # Fallback zu niedriger Komplexität"""
        
        # Neue (korrekte) Implementierung
        new_code = """    def calculate_image_complexity(self, image_data: bytes) -> float:
        \"\"\"
        Berechnet die Komplexität der Bilddaten basierend auf gesetzten Bits
        
        KRITISCHER FIX: Zählt tatsächliche BIT-Komplexität, nicht NULL-Bytes!
        
        Komplexität = Anzahl gesetzter Bits / Gesamtanzahl Bits
        
        Args:
            image_data: Raw image bytes vom printer format
            
        Returns:
            float: Komplexität als Dezimalzahl (0.0 = 0%, 1.0 = 100%)
        \"\"\"
        try:
            if not image_data:
                return 0.0
            
            total_bytes = len(image_data)
            
            # Zähle gesetzte Bits (Population Count)
            # Mehr gesetzte Bits = mehr schwarze Pixel = höhere Komplexität
            set_bits = 0
            for byte in image_data:
                # Zähle 1-Bits in diesem Byte
                set_bits += bin(byte).count('1')
            
            total_bits = total_bytes * 8
            complexity = set_bits / total_bits
            
            logger.info(f"📊 Image complexity: {complexity*100:.1f}% ({set_bits}/{total_bits} set bits, {complexity*total_bytes:.0f}/{total_bytes} weighted bytes)")
            
            return complexity
            
        except Exception as e:
            logger.error(f"❌ Error calculating image complexity: {e}")
            return 0.1  # Fallback zu niedriger Komplexität"""
        
        # Ersetzen
        if old_code in content:
            content = content.replace(old_code, new_code)
            logger.info("✅ calculate_image_complexity Methode ersetzt")
        else:
            logger.warning("⚠️ Alte Methode nicht gefunden - suche nach Varianten...")
            # Suche nach der Methodendefinition
            if 'def calculate_image_complexity(self, image_data: bytes)' in content:
                logger.error("❌ Methode gefunden, aber Content stimmt nicht überein")
                logger.error("   Bitte manuell ersetzen!")
                return False
            else:
                logger.error("❌ Methode nicht gefunden!")
                return False
        
        # Zurückschreiben
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info("✅ FIX ERFOLGREICH ANGEWENDET!")
        logger.info("")
        logger.info("=" * 80)
        logger.info("WAS WURDE GEFIXT:")
        logger.info("=" * 80)
        logger.info("ALT: zero_bytes = image_data.count(0)  # Zählt NULL-Bytes (weiß)")
        logger.info("     → Mehr Dithering = weniger 0x00 = höhere Komplexität")
        logger.info("     → FALSCH für Timing!")
        logger.info("")
        logger.info("NEU: set_bits = sum(bin(byte).count('1') for byte in image_data)")
        logger.info("     → Zählt tatsächlich gesetzte Bits (schwarz)")
        logger.info("     → KORREKT für Timing!")
        logger.info("=" * 80)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    print("=" * 80)
    print("KRITISCHER FIX: Komplexitäts-Berechnung")
    print("=" * 80)
    print()
    print("PROBLEM IDENTIFIZIERT:")
    print("  Dither Normal (128, 1.0):  ✅ Funktioniert")
    print("  Dither Scharf (150, 1.5):  ❌ Verschiebung")
    print()
    print("URSACHE:")
    print("  .count(0) zählt NULL-BYTES (weiß), nicht Komplexität!")
    print("  Mehr Dithering → weniger 0x00 → falsch höhere 'Komplexität'")
    print("  → Zu langsame Übertragung → Timing-Probleme!")
    print()
    print("LÖSUNG:")
    print("  Zähle gesetzte BITS statt NULL-BYTES")
    print("  → Korrekte Komplexitäts-Messung")
    print("=" * 80)
    print()
    
    response = input("Fix anwenden? (j/n): ")
    if response.lower() == 'j':
        if fix_complexity_calculation():
            print()
            print("✅ FIX ERFOLGREICH!")
            print()
            print("NÄCHSTE SCHRITTE:")
            print("1. Server neu starten: python main.py")
            print("2. Teste mit Dither Scharf (150, 1.5)")
            print("3. Sollte jetzt funktionieren!")
        else:
            print()
            print("❌ FIX FEHLGESCHLAGEN!")
            print("Siehe Fehler oben")
    else:
        print("Abgebrochen.")
