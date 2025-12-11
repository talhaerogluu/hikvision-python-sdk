import requests
from requests.auth import HTTPDigestAuth
import logging
from hikvision.utils import parse_response_status, is_success_response
import json

# --- MOCK DATA (Kamera yokken dönecek sahte cevaplar) ---
MOCK_DATA = {
    # Cihaz Bilgisi (GET)
    "/System/deviceInfo": """<?xml version="1.0" encoding="UTF-8"?>
<DeviceInfo version="1.0" xmlns="http://www.hikvision.com/ver10/XMLSchema">
<deviceName>HIKVISION_MOCK</deviceName>
<deviceID>1</deviceID>
<deviceDescription>IPCamera</deviceDescription>
<deviceLocation>hangar</deviceLocation>
<systemContact>Admin</systemContact>
<model>DS-2CD2020F-I</model>
<serialNumber>DS-2CD2020F-I20160101CCCH567890123</serialNumber>
<macAddress>c0:56:e3:xx:xx:xx</macAddress>
<firmwareVersion>V5.4.5</firmwareVersion>
</DeviceInfo>""",

    # PTZ 3D Zoom (PUT) - Genelde boş döner veya XML Status döner
    "/PTZCtrl/channels/1/position3D": """<?xml version="1.0" encoding="UTF-8"?>
<ResponseStatus version="1.0" xmlns="http://www.hikvision.com/ver10/XMLSchema">
<requestURL>/PTZCtrl/channels/1/position3D</requestURL>
<statusCode>1</statusCode>
<statusString>OK</statusString>
</ResponseStatus>""",

"/Image/channels/1/Color": """<?xml version="1.0" encoding="UTF-8"?>
<Color version="1.0" xmlns="http://www.hikvision.com/ver10/XMLSchema">
<brightnessLevel>50</brightnessLevel>
<contrastLevel>50</contrastLevel>
<saturationLevel>50</saturationLevel>
<hueLevel>50</hueLevel>
</Color>""",

"/Video/inputs/channels/1/overlays/text/1": """<ResponseStatus version="1.0">
<statusCode>1</statusCode>
<statusString>OK</statusString>
</ResponseStatus>""",

"/Image/channels/1/IrcutFilterExt": """<ResponseStatus version="1.0">
<statusCode>1</statusCode>
<statusString>OK</statusString>
</ResponseStatus>""",

"/Event/notification/alertStream": """<EventNotificationAlert version="1.0" xmlns="http://www.hikvision.com/ver10/XMLSchema">
<ipAddress>192.168.1.65</ipAddress>
<portNo>80</portNo>
<protocol>HTTP</protocol>
<macAddress>01:17:24:45:D9:F4</macAddress>
<channelID>1</channelID>
<dateTime>2025-11-28T15:27:00Z</dateTime>
<activePostCount>1</activePostCount>
<eventType>VMD</eventType>
<eventState>active</eventState>
<eventDescription>Motion alarm</eventDescription>
</EventNotificationAlert>""",

"/Network/interfaces/1/ipAddress": """<IPAddress version="1.0" xmlns="http://www.hikvision.com/ver10/XMLSchema">
<ipVersion>v4</ipVersion>
<addressingType>static</addressingType>
<ipAddress>192.168.1.65</ipAddress>
<subnetMask>255.255.255.0</subnetMask>
<DefaultGateway><ipAddress>192.168.1.1</ipAddress></DefaultGateway>
</IPAddress>""",

    # --- IO MOCKS ---
    "/IO/status": """<IOPortStatusList version="1.0" xmlns="http://www.hikvision.com/ver10/XMLSchema">
<IOPortStatus>
<ioPortID>1</ioPortID>
<ioPortType>input</ioPortType>
<ioState>inactive</ioState>
</IOPortStatus>
<IOPortStatus>
<ioPortID>1</ioPortID>
<ioPortType>output</ioPortType>
<ioState>inactive</ioState>
</IOPortStatus>
</IOPortStatusList>""",

# Output Trigger (PUT)
    "/IO/outputs/1/trigger": """<ResponseStatus version="1.0">
<statusCode>1</statusCode>
<statusString>OK</statusString>
</ResponseStatus>""",

"/PTZCtrl/channels/1/auxcontrol": "<ResponseStatus><statusCode>1</statusCode><statusString>OK</statusString></ResponseStatus>",
    
# Lens
"/PTZCtrl/channels/1/onepushfocus/start": "<ResponseStatus><statusCode>1</statusCode><statusString>OK</statusString></ResponseStatus>",
    
# System
"/System/reboot": "<ResponseStatus><statusCode>1</statusCode><statusString>OK</statusString></ResponseStatus>",
    
# Storage Format
"/System/Storage/volumes/1/format": "<ResponseStatus><statusCode>1</statusCode><statusString>OK</statusString></ResponseStatus>",

}

class SimpleConfig:
    """
    Pydantic kullanmadan hızlı test yapmak için basit yapılandırma sınıfı.
    Normalde bu veriler models.py içindeki Pydantic modelinden gelmeli.
    """
    def __init__(self, ip, user, password, port=80, channel=1):
        self.ip = ip
        self.username = user
        self.password = password
        self.port = port
        self.channel = channel

class HikvisionSession:
    """
    HTTP Bağlantılarını, Oturum Yönetimini (Session) ve 
    Mocking (Taklit) işlemini yöneten çekirdek sınıf.
    """
    
    def __init__(self, config, mock_mode=False):
        """
        :param config: SimpleConfig veya Pydantic config objesi.
        :param mock_mode: True ise kamera olmadan çalışır.
        """
        self.config = config
        self.mock_mode = mock_mode
        protocol = "http" 
        self.base_url = f"{protocol}://{config.ip}:{config.port}/ISAPI"        
        # Loglama ayarı
        self.logger = logging.getLogger("HikvisionCore")
        
        # Session başlat (TCP Keep-Alive sağlar, her istekte tekrar bağlanmaz)
        self.session = requests.Session()
        self.session.auth = HTTPDigestAuth(config.username, config.password)
        self.session.headers.update({
            "Content-Type": "application/xml",
            "X-Requested-With": "XMLHttpRequest"
        })

    def request(self, method: str, endpoint: str, data: str = None, json_data: dict = None, stream: bool = False, **kwargs) -> requests.Response:
        """
        Merkezi istek metodu.
        **kwargs: headers, timeout gibi ekstra parametreleri yakalar.
        """
        # --- MOCK MODE ---
        if self.mock_mode:
            self.logger.warning(f"[MOCK] {method} {endpoint}")
            if endpoint in MOCK_DATA:
                return MOCK_DATA[endpoint]
            return """<ResponseStatus><statusCode>1</statusCode><statusString>Mock OK</statusString></ResponseStatus>"""

        # --- GERÇEK MODE ---
        url = f"{self.base_url}{endpoint}"
        
        # 1. Session'daki mevcut headerları kopyala
        headers = self.session.headers.copy()
        
        # 2. Dışarıdan (örn: ptz.py'den) özel header geldiyse onları ekle
        # kwargs içinden 'headers'ı alıp siliyoruz ki aşağıda çakışmasın
        if 'headers' in kwargs:
            custom_headers = kwargs.pop('headers')
            headers.update(custom_headers)
        
        # 3. JSON veya XML durumuna göre Content-Type ayarla
        if json_data or "format=json" in endpoint:
            headers["Content-Type"] = "application/json"
            headers["Accept"] = "application/json"
            body = json.dumps(json_data) if json_data else None
        else:
            # Varsayılan XML
            body = data

        try:
            # print(f"--- [REQ] {method} {url} ---") # İstersen açabilirsin
            
            resp = self.session.request(
                method, 
                url, 
                data=body, 
                headers=headers, # Hem session hem de dışarıdan gelen headerlar birleşti
                timeout=10, 
                stream=stream,
                **kwargs # Geriye kalan diğer parametreler (varsa) buraya
            )
            
            # print(f"--- [RES] {resp.status_code} ---")
            resp.raise_for_status()
            return resp
            
        except requests.RequestException as e:
            # self.logger henüz tanımlı değilse print kullan
            print(f"Hata: {e}")
            raise

    def request_binary(self, method: str, endpoint: str, data: str = None) -> bytes:
        """
        Resim, dosya gibi binary verileri çekmek için kullanılır.
        """
        # --- MOCK MODE ---
        if self.mock_mode:
            self.logger.warning(f"[MOCK BINARY] {method} {endpoint}")
            # Sahte bir 1x1 piksel siyah JPEG header'ı dönelim
            return b'\xff\xd8\xff\xe0\x00\x10JFIF...' 

        # --- GERÇEK MODE ---
        url = f"{self.base_url}{endpoint}"
        try:
            # stream=True ile büyük dosyaları da destekleriz
            resp = self.session.request(method, url, data=data, timeout=10, stream=True)
            resp.raise_for_status()
            return resp.content
        except requests.RequestException as e:
            self.logger.error(f"Binary İstek Hatası ({method} {url}): {e}")
            raise