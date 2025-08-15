#!/usr/bin/env python3
"""
Debug-Tool für API-Requests
Zeigt genau an, was bei preview-image und print-image APIs ankommt
"""

import logging
from flask import Flask, request, jsonify
import sys
import threading
import time

# Debug-Logger konfigurieren
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/debug/api/preview-image', methods=['POST'])
def debug_preview_image():
    """Debug-Version der preview-image API"""
    logger.info("=" * 60)
    logger.info("🔍 DEBUG: /api/preview-image Request empfangen")
    
    # Request-Details loggen
    logger.info(f"📊 Content-Type: {request.content_type}")
    logger.info(f"📊 Content-Length: {request.content_length}")
    logger.info(f"📊 Method: {request.method}")
    
    # Headers durchgehen
    logger.info("📋 Headers:")
    for key, value in request.headers:
        if key.lower().startswith(('content-', 'accept')):
            logger.info(f"   {key}: {value}")
    
    # Form-Daten
    logger.info("📝 Form-Data:")
    for key, value in request.form.items():
        logger.info(f"   {key}: {value}")
    
    # Dateien analysieren
    logger.info("📁 Files:")
    for field_name, file_obj in request.files.items():
        logger.info(f"   Feld: '{field_name}'")
        logger.info(f"   Dateiname: '{file_obj.filename}'")
        logger.info(f"   Content-Type: '{file_obj.content_type}'")
        
        # Datei-Größe ermitteln
        file_obj.seek(0, 2)  # Zum Ende
        file_size = file_obj.tell()
        file_obj.seek(0)  # Zurück zum Anfang
        logger.info(f"   Größe: {file_size} bytes")
        
        # Erste paar Bytes lesen (um Format zu erkennen)
        first_bytes = file_obj.read(20)
        file_obj.seek(0)  # Zurück zum Anfang
        logger.info(f"   Erste Bytes: {first_bytes[:10].hex()} ({''.join(chr(b) if 32 <= b <= 126 else '.' for b in first_bytes[:10])})")
        
        # Format versuchen zu erkennen
        if first_bytes.startswith(b'\x89PNG'):
            detected_format = "PNG"
        elif first_bytes.startswith(b'\xff\xd8\xff'):
            detected_format = "JPEG"
        elif first_bytes.startswith(b'GIF8'):
            detected_format = "GIF"
        elif first_bytes.startswith(b'BM'):
            detected_format = "BMP"
        elif first_bytes.startswith(b'RIFF') and b'WEBP' in first_bytes[:20]:
            detected_format = "WEBP"
        else:
            detected_format = "UNBEKANNT"
        
        logger.info(f"   🎯 Erkanntes Format: {detected_format}")
    
    # Raw-Daten (falls verfügbar)
    if hasattr(request, 'data') and request.data:
        logger.info(f"📦 Raw Data: {len(request.data)} bytes")
        logger.info(f"   Erste Bytes: {request.data[:20].hex()}")
    
    logger.info("=" * 60)
    
    return jsonify({
        'success': True,
        'debug_info': {
            'content_type': request.content_type,
            'content_length': request.content_length,
            'files_count': len(request.files),
            'form_fields': list(request.form.keys()),
            'file_fields': list(request.files.keys())
        }
    })

@app.route('/debug/api/print-image', methods=['POST'])
def debug_print_image():
    """Debug-Version der print-image API"""
    logger.info("🖨️ DEBUG: /api/print-image Request empfangen")
    
    # Gleiche Debug-Info wie bei preview-image
    return debug_preview_image()

def start_debug_server():
    """Startet Debug-Server auf Port 8081"""
    print("🐛 Debug-Server startet auf Port 8081...")
    print("🌐 URLs:")
    print("   http://localhost:8081/debug/api/preview-image")
    print("   http://localhost:8081/debug/api/print-image")
    print("\n💡 Verwendung:")
    print("   Ändere deine API-Calls von :8080 auf :8081/debug")
    print("   Beispiel: POST http://localhost:8081/debug/api/preview-image")
    print("\n🔍 Der Debug-Server loggt alle Request-Details!")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=8081, debug=False)

if __name__ == "__main__":
    start_debug_server()
