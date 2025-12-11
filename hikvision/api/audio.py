import xmltodict
from ..core import HikvisionSession
from ..models.audio import AudioChannel
from ..utils import parse_xml, is_success_response

# Çalışmıyor
class AudioAPI:
    def __init__(self, session: HikvisionSession):
        self._session = session
        self.working_endpoint = None # Çalışan adresi hafızada tut

    def get_audio_input(self, channel: int = 1) -> AudioChannel:
        """
        Mikrofon ayarlarını çeker.
        """
        # Eğer daha önce çalışan bir adres bulduysak direkt onu kullan
        if self.working_endpoint:
            endpoints = [self.working_endpoint]
        else:
            # Sırayla dene: Standart -> TwoWay -> Genel
            endpoints = [
                f"/System/Audio/AudioIn/channels/{channel}",  #
                f"/System/TwoWayAudio/channels/{channel}",    #
                f"/System/Audio/channels/{channel}"            #
            ]
        
        for url in endpoints:
            try:
                response = self._session.request("GET", url)
                data = parse_xml(response)
                
                # Farklı XML köklerine bak
                root_key = None
                if "AudioInputChannel" in data: root_key = "AudioInputChannel"
                elif "TwoWayAudioChannel" in data: root_key = "TwoWayAudioChannel"
                elif "AudioChannel" in data: root_key = "AudioChannel"
                
                if root_key:
                    # Çalışan adresi kaydet!
                    self.working_endpoint = url
                    
                    root = data[root_key]
                    return AudioChannel(
                        id=int(root.get("id", channel)),
                        enabled=(str(root.get("enabled")).lower() == "true"),
                        audioInputType=root.get("audioInputType", "unknown"),
                        inputVolume=int(root.get("inputVolume", 0))
                    )
            except Exception:
                continue
        
        # Hiçbiri çalışmadıysa
        return AudioChannel(id=channel, enabled=False, audioInputType="none", inputVolume=0)

    def set_volume(self, volume: int, channel: int = 1) -> bool:
        """
        Ses seviyesini (0-100) ayarlar.
        """
        if not self.working_endpoint:
            # Eğer get_audio_input hiç çalıştırılmadıysa önce onu çalıştırıp adresi bulalım
            self.get_audio_input(channel)
            
        if not self.working_endpoint:
            print("Hata: Çalışan bir ses endpoint'i bulunamadı.")
            return False

        endpoint = self.working_endpoint
        
        try:
            # 1. OKU (Read)
            response = self._session.request("GET", endpoint)
            data = xmltodict.parse(response.text, process_namespaces=False)
            
            # Kök elemanı dinamik bul (AudioInputChannel veya TwoWayAudioChannel)
            root_key = next(iter(data))
            
            # 2. DEĞİŞTİR (Modify)
            if "inputVolume" in data[root_key]:
                data[root_key]["inputVolume"] = str(volume)
                
                # İsteğe bağlı: enabled true değilse sesi açarken onu da açalım mı?
                # Şimdilik sadece volume değiştiriyoruz.
                
                # 3. YAZ (Write)
                new_xml = xmltodict.unparse(data, pretty=True)
                put_response = self._session.request("PUT", endpoint, data=new_xml)
                return is_success_response(put_response)
            
            print(f"Hata: XML içinde 'inputVolume' alanı bulunamadı. Kök: {root_key}")
            return False
            
        except Exception as e:
            print(f"Ses Ayarı Hatası: {e}")
            return False