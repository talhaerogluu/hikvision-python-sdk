from .core import HikvisionSession, SimpleConfig # SimpleConfig'i geçici olarak kullandık
from .api.system import SystemAPI
from .api.ptz import PTZAPI 
from .api.image import ImageAPI
from .api.event import EventAPI
from .api.streaming import StreamingAPI
from .api.security import SecurityAPI
from .api.storage import StorageAPI
from .api.network import NetworkAPI
from .api.io import IOAPI
from .api.thermal import ThermalAPI
from .api.content import ContentAPI 
from .api.audio import AudioAPI

class HikvisionClient:
    def __init__(self, ip, username, password, port=80, channel=1, mock_mode=False):
        
        # Pydantic Config yerine şimdilik SimpleConfig kullanıyoruz
        config = SimpleConfig(ip, username, password, port, channel)
        
        # 1. Oturumu başlat
        self.session = HikvisionSession(config, mock_mode)
        
        # 2. Alt modülleri yükle
        self.system = SystemAPI(self.session)
        self.ptz = PTZAPI(self.session)
        self.image = ImageAPI(self.session)
        self.event = EventAPI(self.session)
        self.streaming = StreamingAPI(self.session)
        self.security = SecurityAPI(self.session)
        self.storage = StorageAPI(self.session)
        self.network = NetworkAPI(self.session)
        self.io = IOAPI(self.session)
        self.thermal = ThermalAPI(self.session)
        self.content = ContentAPI(self.session)
        self.audio = AudioAPI(self.session)