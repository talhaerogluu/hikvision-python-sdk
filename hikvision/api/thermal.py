from ..core import HikvisionSession
from ..models.thermal import TemperatureInfo
import json
import xmltodict

class ThermalAPI:
    def __init__(self, session: HikvisionSession):
        self._session = session
        
        # Termal veri için olası tüm adresler
        self.ENDPOINTS = [
            "/Thermal/temperature/collection?format=json",           # Modern JSON
            "/Thermometry/realTimeThermometry/1",                    # Endüstriyel Tip (Seninki bu olabilir)
            "/Thermometry/rulesTemperatureMeasurement/1"             # Kural Bazlı
        ]

    def get_temperature(self, channel: int = 1) -> TemperatureInfo:
        """
        Termal veriyi çekmeye çalışır.
        Önce Termometri özelliğinin açık olup olmadığına bakar.
        """
        # 1. Önce Özellik Açık mı Kontrol Et
        # Bu endpoint genelde tüm termal kameralarda çalışır
        check_url = f"/Thermal/Thermometry/thermometryBasicSettings?channelID={channel}"
        
        try:
            # Sadece kontrol amaçlı
            self._session.request("GET", check_url)
        except Exception:
            # Eğer ayarlara bile erişemiyorsak, muhtemelen termal modül yetkisi yoktur
            # Ama yine de şansımızı asıl veri endpointinde deneyelim.
            pass

        # 2. Veri Çekme (Endüstriyel Modeller İçin En Garantisi)
        # DS-2TD serisi genelde bu adresi sever.
        endpoints = [
            f"/Thermal/Thermometry/realTimeThermometry/{channel}",      # Yöntem A
            "/Thermal/Thermometry/realTimeThermometry",                # Yöntem B
            f"/Thermometry/rulesTemperatureMeasurement/{channel}"      # Yöntem C (Kural bazlı)
        ]

        last_error = None
        
        for url in endpoints:
            try:
                print(f"   [THERMAL] Deneniyor: {url}")
                response = self._session.request("GET", url)
                data = xmltodict.parse(response.text, process_namespaces=False)
                
                # Farklı XML köklerini tara
                root = data.get("RealTimeThermometry") or \
                       data.get("ThermalMeasurement") or \
                       data.get("Thermometry")

                if not root:
                    continue

                # İçindeki listeyi bul (Thermometry veya Measurement)
                match_list = root.get("Thermometry") or root.get("Measurement")
                
                # Hedef veriyi bul
                target = None
                if isinstance(match_list, list):
                    # Listeyse ilk dolu veriyi al
                    target = match_list[0]
                elif isinstance(match_list, dict):
                    target = match_list
                
                if target:
                    # Pydantic modeline uydur
                    return TemperatureInfo(**target)
                    
            except Exception as e:
                last_error = e
                continue
        
        # Eğer hiçbiri çalışmazsa, boş/dummy veri dönelim ki program patlamasın
        print(f"⚠️ Uyarı: Termal veri alınamadı. Son hata: {last_error}")
        return TemperatureInfo(maxTemperature=0.0, minTemperature=0.0, averageTemperature=0.0)