#!/usr/bin/env python3
"""
Phomemo M110 Robust Server - Hauptdatei
Modulare Version für bessere Wartbarkeit
"""

import sys
import signal
import logging
from flask import Flask, render_template_string

# Module importieren
from printer_controller import RobustPhomemoM110
from api_routes import setup_api_routes
from calibration_api import setup_calibration_routes
from web_template import WEB_INTERFACE

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('phomemo_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Flask App
app = Flask(__name__)

# Configuration
PRINTER_MAC = "12:7E:5A:E9:E5:22"  # ÄNDERN SIE DIESE MAC-ADRESSE!

# Printer Controller initialisieren
printer = RobustPhomemoM110(PRINTER_MAC)

# API Routes registrieren
setup_api_routes(app, printer)
setup_calibration_routes(app, printer)

# Web Interface Route
@app.route('/')
def index():
    return render_template_string(WEB_INTERFACE)

# Static Files (für JavaScript)
@app.route('/static/<path:filename>')
def static_files(filename):
    from flask import send_from_directory
    return send_from_directory('static', filename)

# Graceful Shutdown
def signal_handler(signum, frame):
    logger.info("Received shutdown signal, stopping services...")
    printer.stop_services()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == '__main__':
    print("🍓 Phomemo M110 ROBUST Server (Modulare Version)")
    print(f"🔵 Drucker MAC: {PRINTER_MAC}")
    print(f"📡 Device: {printer.rfcomm_device}")
    print("🌐 Web-Interface: http://RASPBERRY_IP:8080")
    print("💡 WICHTIG: MAC-Adresse in PRINTER_MAC anpassen!")
    print("🔧 Features: Auto-Reconnect, Print Queue, Connection Monitoring")
    print("📊 Background Services: Queue Processor, Connection Monitor")
    print()
    print("📁 Modulare Struktur:")
    print("  ├── main.py              (Hauptserver)")
    print("  ├── printer_controller.py (Bluetooth & Print Logic)")
    print("  ├── api_routes.py        (REST API)")
    print("  ├── web_template.py      (HTML Template)")
    print("  └── static/app.js        (JavaScript)")
    
    try:
        app.run(host='0.0.0.0', port=8080, debug=False)
    finally:
        printer.stop_services()
