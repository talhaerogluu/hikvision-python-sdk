from typing import List
from ..core import HikvisionSession
from ..models.io import IOPortStatus
from ..utils import parse_xml, is_success_response

class IOAPI:
    def __init__(self, session: HikvisionSession):
        self._session = session
        # IO için olası kök dizinler (Modern -> Eski)
        self.IO_BASES = [
            "/System/IO",  # Yeni nesil
            "/IO"          # Eski nesil
        ]
        self.working_base = None # Çalışan yolu hafızada tut

    def _get_base_url(self) -> str:
        """Çalışan IO kök dizinini bulur (Örn: /System/IO)"""
        if self.working_base:
            return self.working_base

        # Deneme Yanılma
        for base in self.IO_BASES:
            url = f"{base}/status"
            try:
                # Sadece varlığını kontrol etmek için status'e GET atıyoruz
                self._session.request("GET", url)
                print(f"   ✓ Çalışan IO adresi bulundu: {base}")
                self.working_base = base
                return base
            except Exception:
                continue
        
        # Hiçbiri çalışmazsa varsayılan olarak eskisini döndür (Hata mesajı main'de çıkar)
        return "/IO"

    def get_port_status(self) -> List[IOPortStatus]:
        """
        Tüm giriş/çıkış portlarının durumunu çeker.
        Ref: ISAPI PDF Section 8.3.1  & 15.10.50
        """
        base = self._get_base_url()
        endpoint = f"{base}/status"
        
        response = self._session.request("GET", endpoint)
        
        data = parse_xml(response)
        
        # <IOPortStatusList><IOPortStatus>...</IOPortStatus></IOPortStatusList>
        ports_data = data.get("IOPortStatusList", {}).get("IOPortStatus", [])
        
        if isinstance(ports_data, dict):
            ports_data = [ports_data]
            
        return [IOPortStatus(**p) for p in ports_data]

    def trigger_output(self, port_id: int, state: str = "high") -> bool:
        """
        Bir röleyi (Output) tetikler.
        State: 'high' (açık/tetiklenmiş) veya 'low' (kapalı).
        """
        base = self._get_base_url()
        endpoint = f"{base}/outputs/{port_id}/trigger"
        
        # Ref: ISAPI PDF Section 8.3.8 [cite: 1001]
        xml_body = f"""<?xml version="1.0" encoding="UTF-8"?>
<IOPortData xmlns="http://www.hikvision.com/ver10/XMLSchema">
    <outputState>{state}</outputState>
</IOPortData>"""
        
        response = self._session.request("PUT", endpoint, data=xml_body)
        return is_success_response(response)