"""
Datenmodelle, Enums und Konstanten fuer den Phomemo M110 Printer Controller.
"""

from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from PIL import Image


class ConnectionStatus(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


class TransmissionSpeed(Enum):
    """Uebertragungsgeschwindigkeiten basierend auf Datenkomplexitaet"""
    ULTRA_FAST = "ultra_fast"    # Fuer sehr einfache Bilder (<2% non-zero)
    FAST = "fast"                # Fuer einfache Bilder (<5% non-zero)
    NORMAL = "normal"            # Fuer mittlere Komplexitaet (<8% non-zero)
    SLOW = "slow"                # Fuer komplexe Bilder (<12% non-zero)
    ULTRA_SLOW = "ultra_slow"    # Fuer sehr komplexe Bilder (>12% non-zero)


@dataclass
class PrintJob:
    """Repraesentiert einen Druckauftrag in der Queue"""
    job_id: str
    job_type: str  # 'text', 'image', 'calibration', etc.
    data: Dict[Any, Any]
    timestamp: float
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class ImageProcessingResult:
    """Ergebnis der Bildverarbeitung"""
    processed_image: Image.Image
    preview_base64: str
    original_size: Tuple[int, int]
    processed_size: Tuple[int, int]
    info: Dict[str, Any]
