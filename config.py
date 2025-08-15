"""
Erweiterte Konfigurationsdatei für Phomemo M110 Robust Server
Mit X-Offset und Bildvorschau-Features
"""

# Drucker-Konfiguration
PRINTER_MAC = "12:7E:5A:E9:E5:22"  # DEINE MAC-ADRESSE HIER!
RFCOMM_DEVICE = "/dev/rfcomm0"
RFCOMM_CHANNEL = "1"

# Server-Konfiguration
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8080
DEBUG_MODE = False

# Drucker-Spezifikationen
PRINTER_WIDTH_PIXELS = 384
PRINTER_BYTES_PER_LINE = 48  # 384 / 8

# Neue Features: Offset-Konfiguration
DEFAULT_X_OFFSET = 0   # Standard X-Offset (kein Offset)
DEFAULT_Y_OFFSET = 0   # Standard Y-Offset
MIN_X_OFFSET = 0       # Minimum X-Offset
MAX_X_OFFSET = 100     # Maximum X-Offset
MIN_Y_OFFSET = -50     # Minimum Y-Offset
MAX_Y_OFFSET = 50      # Maximum Y-Offset

# Label-Spezifikationen für Vorschau
LABEL_WIDTH_MM = 40    # 40mm Label-Breite
LABEL_HEIGHT_MM = 30   # 30mm Label-Höhe
LABEL_DPI = 203        # Dots per inch
LABEL_WIDTH_PX = int((LABEL_WIDTH_MM / 25.4) * LABEL_DPI)   # ~320px
LABEL_HEIGHT_PX = int((LABEL_HEIGHT_MM / 25.4) * LABEL_DPI) # ~240px

# Bildverarbeitung-Einstellungen
DEFAULT_DITHER_THRESHOLD = 128  # Schwellenwert für SW-Konvertierung
DEFAULT_DITHER_ENABLED = True   # Floyd-Steinberg Dithering aktiviert
DEFAULT_DITHER_STRENGTH = 1.0   # Dithering-Stärke (0.1 - 2.0)
DEFAULT_CONTRAST_BOOST = 1.0    # Kontrast-Verstärkung (0.5 - 2.0)
SUPPORTED_IMAGE_FORMATS = ['PNG', 'JPEG', 'JPG', 'BMP', 'GIF', 'WEBP']
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB max Upload

# Bildanpassungs-Modi
IMAGE_SCALING_MODES = {
    'fit_aspect': 'An Label anpassen (Seitenverhältnis beibehalten)',
    'stretch_full': 'Volle Label-Größe (stretchen)',
    'crop_center': 'Zentriert zuschneiden (volle Größe)',
    'pad_center': 'Zentriert mit Rand (volle Größe)'
}

# Preview-Einstellungen
PREVIEW_MAX_WIDTH = 400   # Max Breite für Web-Vorschau
PREVIEW_MAX_HEIGHT = 300  # Max Höhe für Web-Vorschau
PREVIEW_FORMAT = 'PNG'    # Format für Vorschau-Bilder

# Connection Management
MAX_CONNECTION_ATTEMPTS = 5
BASE_RETRY_DELAY = 2  # Sekunden
MAX_RETRY_DELAY = 30  # Sekunden
HEARTBEAT_INTERVAL = 30  # Sekunden

# Print Job Settings
MAX_RETRIES_PER_JOB = 3

# Font-Pfade (in Prioritätsreihenfolge)
FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"
]

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "phomemo_server.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Kalibrierungs-Einstellungen
CALIBRATION_TEST_PATTERNS = {
    'x_offset_test': {
        'description': 'X-Offset Kalibrierung',
        'width': 100,
        'height': 50,
        'pattern': 'grid'
    },
    'y_offset_test': {
        'description': 'Y-Offset Kalibrierung', 
        'width': 200,
        'height': 100,
        'pattern': 'lines'
    },
    'full_test': {
        'description': 'Vollständiger Test',
        'width': LABEL_WIDTH_PX,
        'height': LABEL_HEIGHT_PX,
        'pattern': 'full'
    }
}

# Konfigurationsdatei für persistente Einstellungen
CONFIG_FILE = "printer_settings.json"

# Standard-Konfiguration für neue Installationen
DEFAULT_SETTINGS = {
    'x_offset': DEFAULT_X_OFFSET,
    'y_offset': DEFAULT_Y_OFFSET,
    'dither_threshold': DEFAULT_DITHER_THRESHOLD,
    'dither_enabled': DEFAULT_DITHER_ENABLED,
    'dither_strength': DEFAULT_DITHER_STRENGTH,
    'contrast_boost': DEFAULT_CONTRAST_BOOST,
    'fit_to_label_default': True,
    'maintain_aspect_default': True,
    'auto_connect': True,
    'debug_mode': False
}
