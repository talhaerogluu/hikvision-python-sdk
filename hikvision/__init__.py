"""
Hikvision ISAPI Python Wrapper
------------------------------
Hikvision kameraları (PTZ, Termal, NVR) yönetmek için geliştirilmiş
modern ve kapsamlı bir kütüphane.
"""

# 1. Ana İstemci (Kullanıcının etkileşime girdiği tek sınıf)
from .client import HikvisionClient

# 2. Yardımcı Sınıflar ve Enum'lar (Kullanıcının import etmek isteyebileceği tipler)

# PTZ Modelleri
try:
    from .models.ptz import PTZAuxCommand, PTZRegion
except ImportError:
    pass # Eğer henüz Enum dosyasını oluşturmadıysan hata vermesin

# Görüntü (Image) Modelleri
from .models.image import TextOverlay, ColorSetup, DayNightMode

# Akış (Streaming) Modelleri
from .models.streaming import VideoSettings, StreamingChannel

# Kayıt (Content) Modelleri
from .models.content import SearchResult, SearchMatchItem

# Termal Modeller
try:
    from .models.thermal import TemperatureInfo
except ImportError:
    pass

# IO Modelleri
from .models.io import IOPortStatus

# 3. Kütüphane Versiyonu
__version__ = "1.0.0"

# 4. Dışarıya Açılan İsimler (Public API)
# Kullanıcı 'from hikvision import *' dediğinde sadece bunlar gelir.
__all__ = [
    "HikvisionClient",
    "PTZAuxCommand",
    "PTZRegion",
    "TextOverlay",
    "ColorSetup",
    "DayNightMode",
    "VideoSettings",
    "StreamingChannel",
    "SearchResult",
    "SearchMatchItem",
    "TemperatureInfo",
    "IOPortStatus"
]