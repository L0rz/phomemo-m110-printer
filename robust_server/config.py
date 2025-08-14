"""
Konfigurationsdatei für Phomemo M110 Robust Server
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
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"
]

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "phomemo_server.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
