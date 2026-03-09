#!/usr/bin/env python3
"""
Integration Script: Wendet die FIXED Bitmap-Konvertierung auf deinen bestehenden Code an

VERWENDUNG:
1. Backup erstellen: python apply_bitmap_fix.py --backup
2. Fix anwenden: python apply_bitmap_fix.py --apply
3. Testen: python apply_bitmap_fix.py --test
4. Rollback (falls nötig): python apply_bitmap_fix.py --rollback
"""

import os
import shutil
import logging
import argparse
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Pfade
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ORIGINAL_FILE = os.path.join(SCRIPT_DIR, 'printer_controller.py')
FIXED_FILE = os.path.join(SCRIPT_DIR, 'printer_controller_fixed.py')
BACKUP_DIR = os.path.join(SCRIPT_DIR, 'Backup')


def create_backup():
    """Erstellt Backup des Original-Files"""
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(BACKUP_DIR, f'printer_controller_backup_{timestamp}.py')
        
        shutil.copy2(ORIGINAL_FILE, backup_file)
        logger.info(f"✅ Backup erstellt: {backup_file}")
        return backup_file
    except Exception as e:
        logger.error(f"❌ Backup-Fehler: {e}")
        return None


def apply_fix():
    """Wendet die Fixed-Methoden auf die Original-Datei an"""
    try:
        logger.info("📝 Lese Original-Datei...")
        with open(ORIGINAL_FILE, 'r', encoding='utf-8') as f:
            original_code = f.read()
        
        logger.info("📝 Lese Fixed-Methoden...")
        with open(FIXED_FILE, 'r', encoding='utf-8') as f:
            fixed_code = f.read()
        
        # Extrahiere die Fixed-Methoden
        logger.info("🔧 Extrahiere Fixed-Methoden...")
        
        # image_to_printer_format
        fixed_image_to_printer = extract_method(fixed_code, 'def image_to_printer_format(self, img):')
        # send_bitmap
        fixed_send_bitmap = extract_method(fixed_code, 'def send_bitmap(self, image_data: bytes, height: int) -> bool:')
        
        if not fixed_image_to_printer or not fixed_send_bitmap:
            logger.error("❌ Konnte Fixed-Methoden nicht extrahieren")
            return False
        
        # Erstelle Backup vor Änderung
        backup_file = create_backup()
        if not backup_file:
            logger.error("❌ Kann ohne Backup nicht fortfahren")
            return False
        
        # Ersetze die Methoden im Original
        logger.info("🔧 Ersetze image_to_printer_format...")
        original_code = replace_method(original_code, 'def image_to_printer_format(self, img):', fixed_image_to_printer)
        
        logger.info("🔧 Ersetze send_bitmap...")
        original_code = replace_method(original_code, 'def send_bitmap(self, image_data: bytes, height: int) -> bool:', fixed_send_bitmap)
        
        # Schreibe zurück
        logger.info("💾 Schreibe modifizierte Datei...")
        with open(ORIGINAL_FILE, 'w', encoding='utf-8') as f:
            f.write(original_code)
        
        logger.info("✅ Fix erfolgreich angewendet!")
        logger.info(f"   Backup: {backup_file}")
        logger.info("   Modified: printer_controller.py")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Anwenden: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def extract_method(code, method_signature):
    """Extrahiert eine Methode aus dem Code"""
    try:
        # Finde Methodenbeginn
        start_idx = code.find(method_signature)
        if start_idx == -1:
            return None
        
        # Finde Methodenende (nächste Methode auf gleicher Einrückungsebene oder Klassenende)
        lines = code[start_idx:].split('\n')
        method_lines = [lines[0]]
        
        base_indent = len(lines[0]) - len(lines[0].lstrip())
        
        for i in range(1, len(lines)):
            line = lines[i]
            
            # Leere Zeile oder Kommentar → weiter
            if not line.strip() or line.strip().startswith('#'):
                method_lines.append(line)
                continue
            
            # Einrückung prüfen
            current_indent = len(line) - len(line.lstrip())
            
            # Wenn Einrückung kleiner/gleich Basis → Methodenende
            if current_indent <= base_indent and line.strip():
                break
            
            method_lines.append(line)
        
        return '\n'.join(method_lines)
        
    except Exception as e:
        logger.error(f"Fehler beim Extrahieren: {e}")
        return None


def replace_method(code, method_signature, new_method):
    """Ersetzt eine Methode im Code"""
    try:
        # Finde alte Methode
        start_idx = code.find(method_signature)
        if start_idx == -1:
            logger.warning(f"Methode nicht gefunden: {method_signature}")
            return code
        
        # Finde Methodenende
        lines = code[start_idx:].split('\n')
        base_indent = len(lines[0]) - len(lines[0].lstrip())
        
        end_line_idx = 1
        for i in range(1, len(lines)):
            line = lines[i]
            if not line.strip() or line.strip().startswith('#'):
                end_line_idx = i + 1
                continue
            
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= base_indent and line.strip():
                break
            end_line_idx = i + 1
        
        # Berechne absolute Indizes
        end_idx = start_idx + sum(len(l) + 1 for l in lines[:end_line_idx])
        
        # Ersetze
        new_code = code[:start_idx] + new_method + '\n\n' + code[end_idx:]
        
        return new_code
        
    except Exception as e:
        logger.error(f"Fehler beim Ersetzen: {e}")
        return code


def rollback():
    """Stellt die letzte Backup-Version wieder her"""
    try:
        # Finde neuestes Backup
        backups = [f for f in os.listdir(BACKUP_DIR) if f.startswith('printer_controller_backup_')]
        if not backups:
            logger.error("❌ Keine Backups gefunden")
            return False
        
        backups.sort(reverse=True)
        latest_backup = os.path.join(BACKUP_DIR, backups[0])
        
        logger.info(f"📦 Stelle wieder her: {latest_backup}")
        shutil.copy2(latest_backup, ORIGINAL_FILE)
        
        logger.info("✅ Rollback erfolgreich!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Rollback-Fehler: {e}")
        return False


def test_fix():
    """Testet die Fixed-Version"""
    try:
        logger.info("🧪 Teste Fixed-Version...")
        
        # Importiere Fixed-Klasse
        from printer_controller_fixed import FixedPhomemoM110, test_fixed_conversion
        
        # Führe Test aus
        test_fixed_conversion()
        
        logger.info("✅ Test abgeschlossen - Siehe Ausgabe oben")
        
    except Exception as e:
        logger.error(f"❌ Test-Fehler: {e}")
        import traceback
        logger.error(traceback.format_exc())


def main():
    parser = argparse.ArgumentParser(description='Wendet Bitmap-Fix auf printer_controller.py an')
    parser.add_argument('--backup', action='store_true', help='Erstellt nur ein Backup')
    parser.add_argument('--apply', action='store_true', help='Wendet den Fix an')
    parser.add_argument('--test', action='store_true', help='Testet die Fixed-Version')
    parser.add_argument('--rollback', action='store_true', help='Stellt Backup wieder her')
    
    args = parser.parse_args()
    
    if args.backup:
        create_backup()
    elif args.apply:
        logger.info("=" * 80)
        logger.info("BITMAP FIX ANWENDEN")
        logger.info("=" * 80)
        apply_fix()
    elif args.test:
        test_fix()
    elif args.rollback:
        rollback()
    else:
        parser.print_help()
        print("\n" + "=" * 80)
        print("EMPFOHLENE SCHRITTE:")
        print("=" * 80)
        print("1. Backup erstellen:  python apply_bitmap_fix.py --backup")
        print("2. Fix testen:        python apply_bitmap_fix.py --test")
        print("3. Fix anwenden:      python apply_bitmap_fix.py --apply")
        print("4. Bei Problemen:     python apply_bitmap_fix.py --rollback")


if __name__ == "__main__":
    main()
