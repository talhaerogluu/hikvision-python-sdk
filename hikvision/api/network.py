from typing import List
from ..core import HikvisionSession
from ..models.network import NetworkInterface
from ..utils import parse_xml, is_success_response

class NetworkAPI:
    def __init__(self, session: HikvisionSession):
        self._session = session

    def get_interfaces(self) -> List[NetworkInterface]:
        """
        Tüm ağ arayüzlerini çeker.
        Ref:
        """
        endpoint = "/System/Network/interfaces"
        
        try:
            response = self._session.request("GET", endpoint)
            data = parse_xml(response)
            
            if_list = data.get("NetworkInterfaceList", {}).get("NetworkInterface", [])
            
            if isinstance(if_list, dict):
                if_list = [if_list]
                
            results = []
            for item in if_list:
                ip_ver = item.get("IPAddress", {})
                is_dhcp = (ip_ver.get("addressingType") == "dynamic")
                gateway = ip_ver.get("DefaultGateway", {}).get("ipAddress")
                
                # --- DÜZELTME BURADA ---
                # MAC Adresi 'Link' objesinin içinde olabilir.
                link_info = item.get("Link", {})
                
                # Genelde 'MACAddress' olarak geçer ama şansımızı artıralım
                mac = link_info.get("MACAddress") or link_info.get("macAddress") or item.get("PhysicalAddress")

                net_if = NetworkInterface(
                    id=int(item.get("id", 1)),
                    ipAddress=ip_ver.get("ipAddress", "0.0.0.0"),
                    subnetMask=ip_ver.get("subnetMask", "255.255.255.0"),
                    gateway=gateway,
                    PhysicalAddress=mac, 
                    dhcp=is_dhcp
                )
                results.append(net_if)
                
            return results

        except Exception as e:
            print(f"Network Bilgisi Hatası: {e}")
            return []
        
    def set_static_ip(self, ip: str, mask: str, gateway: str, interface_id: int = 1) -> bool:
        """
        Statik IP ataması yapar.
        DİKKAT: IP değişirse bağlantı kopar!
        Ref: ISAPI PDF Section 15.10.100
        """
        # Senin yazdığın yapı doğru, sadece System yoluna çekiyoruz
        endpoint = f"/System/Network/interfaces/{interface_id}/ipAddress"
        
        xml_body = f"""<IPAddress version="2.0" xmlns="http://www.hikvision.com/ver10/XMLSchema">
            <ipVersion>v4</ipVersion>
            <addressingType>static</addressingType>
            <ipAddress>{ip}</ipAddress>
            <subnetMask>{mask}</subnetMask>
            <DefaultGateway>
                <ipAddress>{gateway}</ipAddress>
            </DefaultGateway>
        </IPAddress>"""
        
        try:
            response = self._session.request("PUT", endpoint, data=xml_body)
            return is_success_response(response)
        except Exception as e:
            print(f"IP Değiştirme Hatası: {e}")
            return False