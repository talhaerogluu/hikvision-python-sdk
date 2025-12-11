from ..core import HikvisionSession
from ..utils import parse_xml
from ..models.system import DeviceInfo, DeviceStatus
from ..utils import is_success_response
from ..models.system import TimeConfig
import xmltodict


class SystemAPI:
    def __init__(self, session: HikvisionSession):
        self._session = session

    def get_device_info(self) -> DeviceInfo:
        """
        Cihaz bilgilerini çeker (Model, Seri No vb.)
        Ref: ISAPI PDF Section 8.1.1
        """
        # 1. İsteği at (Core halleder)
        xml_response = self._session.request("GET", "/System/deviceInfo")
        
        # 2. XML'i Dict'e çevir
        data_dict = parse_xml(xml_response)
        
        # 3. Pydantic modeline dök (Validation)
        # XML genelde root tag içinde gelir: {'DeviceInfo': {...}}
        payload = data_dict.get("DeviceInfo", data_dict)
        
        return DeviceInfo(**payload)
    
    def reboot_device(self) -> bool:
        """
        Cihazı yeniden başlatır.
        Ref: ISAPI PDF Section 8.1.5
        """
        endpoint = "/System/reboot"
        xml = self._session.request("PUT", endpoint)
        return is_success_response(xml)

    def factory_reset(self, mode: str = "full") -> bool:
        """
        Fabrika ayarlarına döndürür.
        mode: "full" (Her şey), "basic" (Ağ ayarları hariç)
        Ref: ISAPI PDF Section 8.1.3
        """
        endpoint = f"/System/factoryDefault?mode={mode}"
        xml = self._session.request("PUT", endpoint)
        return is_success_response(xml)
    
    def get_status(self) -> DeviceStatus:
        """
        Cihazın CPU, RAM ve Uptime durumunu çeker.
        Ref: ISAPI PDF Section 8.1.6 
        """
        endpoint = "/System/status"
        response = self._session.request("GET", endpoint)
        
        data = parse_xml(response)
        root = data.get("DeviceStatus", {})
        
        # CPU ve Memory listeleri için basit veri düzenleme
        # xmltodict tek elemanlı listeleri dict yapar, bunu listeye çevirelim
        if root.get("CPUList") and isinstance(root["CPUList"].get("CPU"), dict):
            root["CPUList"] = [root["CPUList"]["CPU"]]
        elif root.get("CPUList"):
             root["CPUList"] = root["CPUList"]["CPU"] # Zaten listeyse

        if root.get("MemoryList") and isinstance(root["MemoryList"].get("Memory"), dict):
            root["MemoryList"] = [root["MemoryList"]["Memory"]]
        elif root.get("MemoryList"):
            root["MemoryList"] = root["MemoryList"]["Memory"]

        return DeviceStatus(**root)
    
    def get_time_settings(self) -> TimeConfig:
        """Kamera saat ayarlarını çeker."""
        response = self._session.request("GET", "/System/time")
        data = parse_xml(response)
        return TimeConfig(**data.get("Time", {}))

    def set_time_manual(self, datetime_str: str) -> bool:
        """
        Saati manuel olarak ayarlar.
        Format: YYYY-MM-DDTHH:MM:SS (Örn: 2025-12-04T14:55:00)
        """
        # Read-Modify-Write
        endpoint = "/System/time"
        response = self._session.request("GET", endpoint)
        data = xmltodict.parse(response.text, process_namespaces=False)
        
        if "Time" in data:
            data["Time"]["timeMode"] = "manual"
            data["Time"]["localTime"] = datetime_str
            
            new_xml = xmltodict.unparse(data, pretty=True)
            put_response = self._session.request("PUT", endpoint, data=new_xml)
            return is_success_response(put_response)
        return False
    
    def set_ntp_mode(self) -> bool:
        """
        Kamerayı NTP (Otomatik Saat) moduna alır.
        """
        endpoint = "/System/time"
        response = self._session.request("GET", endpoint)
        data = xmltodict.parse(response.text, process_namespaces=False)
        
        if "Time" in data:
            data["Time"]["timeMode"] = "NTP"
            # NTP modunda localTime göndermeye gerek yok, kamera sunucudan çeker
            
            new_xml = xmltodict.unparse(data, pretty=True)
            put_response = self._session.request("PUT", endpoint, data=new_xml)
            return is_success_response(put_response)
        return False