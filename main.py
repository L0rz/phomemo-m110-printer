#!/usr/bin/env python3
"""
Phomemo M110 Enhanced Server - Hauptdatei
Mit Bildvorschau, X-Offset-Konfiguration und erweiterten Features
"""

import sys
import signal
import logging
import os
import time
from flask import Flask, render_template_string

# Module importieren
from printer_controller import EnhancedPhomemoM110
from api_routes import setup_api_routes
from web_template import WEB_INTERFACE
from config import *

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Flask App
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_UPLOAD_SIZE  # File upload limit

# Printer Controller initialisieren
printer = EnhancedPhomemoM110(PRINTER_MAC)

# API Routes registrieren
setup_api_routes(app, printer)

# Web Interface Route
@app.route('/')
def index():
    return render_template_string(WEB_INTERFACE)

# Static Files Error Handler
@app.errorhandler(413)
def too_large(e):
    return {"error": f"Datei zu groß. Maximum: {MAX_UPLOAD_SIZE // (1024*1024)}MB"}, 413

@app.errorhandler(500)
def internal_error(e):
    logger.error(f"Internal server error: {e}")
    return {"error": "Interner Serverfehler"}, 500

# Health Check Endpoint
@app.route('/health')
def health_check():
    """Einfacher Health Check für Monitoring"""
    try:
        return {
            "status": "healthy",
            "printer_connected": printer.is_connected(),
            "queue_size": printer.print_queue.qsize(),
            "uptime": int(time.time() - printer.stats['uptime_start'])
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}, 500

# Label-Größen-Verwaltung
@app.route('/label-sizes')
def label_sizes_page():
    """Label-Größen-Verwaltungsseite"""
    try:
        with open('static/label-sizes.html', 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"<h1>Fehler beim Laden der Label-Größen-Seite</h1><p>{e}</p>", 500

# Graceful Shutdown
def signal_handler(signum, frame):
    logger.info("Received shutdown signal, stopping services...")
    try:
        printer.stop_services()
        # Einstellungen vor dem Beenden speichern
        printer.save_settings()
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
    finally:
        sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def print_startup_info():
    """Zeigt Startup-Informationen an"""
    print("=" * 60)
    print("🖨️  PHOMEMO M110 ENHANCED SERVER")
    print("=" * 60)
    print(f"🔵 Drucker MAC: {PRINTER_MAC}")
    print(f"📡 Device: {printer.rfcomm_device}")
    print(f"🌐 Web-Interface: http://localhost:{SERVER_PORT}")
    print(f"🔧 Health Check: http://localhost:{SERVER_PORT}/health")
    print("=" * 60)
    print("✨ NEUE FEATURES:")
    print(f"   📷 Schwarz-Weiß-Bildvorschau")
    print(f"   📐 X-Offset Konfiguration (Standard: {DEFAULT_X_OFFSET}px)")
    print(f"   ⚙️  Persistente Einstellungen ({CONFIG_FILE})")
    print(f"   🎯 Erweiterte Kalibrierungs-Tools")
    print(f"   📊 Detaillierte Statistiken")
    print(f"   🔄 Robuste Queue mit Auto-Retry")
    print("=" * 60)
    print("🎛️  EINSTELLUNGEN:")
    print(f"   X-Offset Bereich: {MIN_X_OFFSET}-{MAX_X_OFFSET} Pixel")
    print(f"   Y-Offset Bereich: {MIN_Y_OFFSET}-{MAX_Y_OFFSET} Pixel")
    print(f"   Label-Größe: {LABEL_WIDTH_MM}×{LABEL_HEIGHT_MM}mm ({LABEL_WIDTH_PX}×{LABEL_HEIGHT_PX}px)")
    print(f"   Max Upload: {MAX_UPLOAD_SIZE // (1024*1024)}MB")
    print(f"   Unterstützte Formate: {', '.join(SUPPORTED_IMAGE_FORMATS)}")
    print("=" * 60)
    print("⌨️  KEYBOARD SHORTCUTS:")
    print("   Ctrl+Enter: Text sofort drucken")
    print("   Ctrl+Shift+Enter: Text in Queue")
    print("   F5: Verbindungsstatus aktualisieren")
    print("=" * 60)
    print("📁 MODULARE STRUKTUR:")
    print("   ├── main.py                    (Hauptserver)")
    print("   ├── printer_controller.py     (Printer-Logik)")
    print("   ├── api_routes.py              (REST API mit Bildverarbeitung)")
    print("   ├── web_template.py            (Web-Interface)")
    print("   ├── config.py                  (Konfiguration)")
    print("   └── printer_settings.json     (Persistente Einstellungen)")
    print("=" * 60)
    
    # Aktuelle Einstellungen anzeigen
    settings = printer.get_settings()
    print("🔧 AKTUELLE EINSTELLUNGEN:")
    print(f"   X-Offset: {settings.get('x_offset', DEFAULT_X_OFFSET)} px")
    print(f"   Y-Offset: {settings.get('y_offset', DEFAULT_Y_OFFSET)} px")
    print(f"   Dithering: {'✅' if settings.get('dither_enabled', True) else '❌'}")
    print(f"   Auto-Connect: {'✅' if settings.get('auto_connect', True) else '❌'}")
    print("=" * 60)
    print("💡 WICHTIG: MAC-Adresse in config.py anpassen!")
    print("🚀 Server startet...")
    print("=" * 60)

if __name__ == '__main__':
    print_startup_info()
    
    # Initiale Verbindung versuchen
    if printer.settings.get('auto_connect', True):
        logger.info("Attempting initial connection...")
        if printer.connect_bluetooth():
            logger.info("Initial connection successful")
        else:
            logger.warning("Initial connection failed, will retry automatically")
    
    try:
        app.run(
            host=SERVER_HOST, 
            port=SERVER_PORT, 
            debug=DEBUG_MODE,
            threaded=True
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        printer.stop_services()
        printer.save_settings()
        logger.info("Server shutdown complete")
