import xmltodict
from ..core import HikvisionSession
from ..models.image import TextOverlay, ColorSetup, DayNightMode
from ..utils import parse_xml, is_success_response

class ImageAPI:
    def __init__(self, session: HikvisionSession):
        self._session = session
        # Image servisi genelde ver10 kullanır, hata alırsak ver20 deneriz
        self.NAMESPACE = "http://www.hikvision.com/ver10/XMLSchema"

    # --- OSD İŞLEMLERİ (Video Service) ---
    
    # ---- ----- ----- ----- ------ ------ÇALIŞMIYOR----- ----- ----- ----- ---- ----- ------
    def set_text_overlay(self, message: str, id: int = 1, x: int = None, y: int = None, enabled: bool = True, channel: int = 1) -> bool:
        """
        OSD Metnini günceller.
        Liste boşsa 1-8 arası tüm slotları oluşturur (Browser Mimic).
        """
        endpoint = f"/System/Video/inputs/channels/{channel}/overlays"
        
        try:
            # 1. OKU (READ)
            response = self._session.request("GET", endpoint)
            
            # Namespace'leri korumadan parse et (daha kolay yönetim için)
            data = xmltodict.parse(response.text, process_namespaces=False)
            
            # --- GÜVENLİ VERİ ÇEKME ---
            video_overlay = data.get('VideoOverlay')
            if not video_overlay:
                print("Hata: 'VideoOverlay' bulunamadı.")
                return False
            
            # TextOverlayList'i al veya oluştur
            text_list_container = video_overlay.get('TextOverlayList')
            if text_list_container is None:
                text_list_container = {}
                video_overlay['TextOverlayList'] = text_list_container

            overlays_list = text_list_container.get('TextOverlay')
            
            # --- STRATEJİ: LİSTE BOŞSA 8 SLOTU DA DOLDUR ---
            if not overlays_list:
                print(f"ℹ️ Bilgi: OSD listesi boş. Tarayıcı standardına uygun 8 slot oluşturuluyor...")
                overlays_list = []
                
                for i in range(1, 9): # ID 1'den 8'e kadar
                    # Varsayılan boş kayıt
                    item = {
                        'id': str(i),
                        'enabled': 'false',
                        'alignment': '0',       # Hizalama (Sıralama önemli)
                        'positionX': '0',
                        'positionY': '576',     # Genelde alt köşe
                        'displayText': ''
                    }
                    overlays_list.append(item)
                
                # Listeyi ana yapıya bağla
                text_list_container['TextOverlay'] = overlays_list

            # Tek eleman varsa listeye çevir (xmltodict özelliği)
            if isinstance(overlays_list, dict):
                overlays_list = [overlays_list]
                text_list_container['TextOverlay'] = overlays_list # Referansı güncelle

            # --- HEDEFİ BUL VE GÜNCELLE ---
            target_overlay = next((item for item in overlays_list if int(item.get('id', 0)) == id), None)
            
            if not target_overlay:
                print(f"Hata: ID {id} oluşturulan listede bile bulunamadı!")
                return False
            
            # Değerleri yaz (Sıralama dict içinde zaten oluştu)
            target_overlay['displayText'] = message
            target_overlay['enabled'] = 'true' if enabled else 'false'
            
            # Koordinat varsa güncelle
            if x is not None: target_overlay['positionX'] = str(x)
            if y is not None: target_overlay['positionY'] = str(y)
            
            # Hizalama (Alignment) manuel girilmediyse ve XML'de yoksa varsayılan 0
            if 'alignment' not in target_overlay:
                target_overlay['alignment'] = '0'

            # 3. YAZ (WRITE)
            new_xml = xmltodict.unparse(data, pretty=True)
            
            # Debug için gerekirse: 
            # print(f"GİDEN XML:\n{new_xml}")
            
            response_put = self._session.request("PUT", endpoint, data=new_xml)
            return is_success_response(response_put)
            
        except Exception as e:
            print(f"OSD İşlem Hatası: {e}")
            if 'response_put' in locals():
                print(f"Detay: {response_put.text}")
            return False
                
    def get_color_settings(self, channel: int = 1) -> ColorSetup:
        """
        Mevcut parlaklık/kontrast değerlerini çeker.
        Endpoint: /Image/channels/ID/Color
        """
        endpoint = f"/Image/channels/{channel}/Color"
        response = self._session.request("GET", endpoint)
        
        # parse_xml artık response objesi alabiliyor (utils güncellemesinden sonra)
        data = parse_xml(response) 
        payload = data.get("Color", {})
        return ColorSetup(**payload)

    def set_color_settings(self, brightness: int = None, contrast: int = None, saturation: int = None, hue: int = None, channel: int = 1) -> bool:
        """
        Görüntü ayarlarını günceller.
        Kullanıcı sadece değiştirmek istediği değeri girer.
        """
        endpoint = f"/Image/channels/{channel}/Color"
        
        # 1. Modeli içeride oluştur (Validation için)
        # Sadece girilen değerleri alıyoruz, Pydantic (Optional) buna izin veriyor.
        settings = ColorSetup(
            brightnessLevel=brightness,
            contrastLevel=contrast,
            saturationLevel=saturation,
            hueLevel=hue
        )
        
        # 2. XML Oluşturucu
        fields = []
        if settings.brightness is not None: fields.append(f"<brightnessLevel>{settings.brightness}</brightnessLevel>")
        if settings.contrast is not None: fields.append(f"<contrastLevel>{settings.contrast}</contrastLevel>")
        if settings.saturation is not None: fields.append(f"<saturationLevel>{settings.saturation}</saturationLevel>")
        if settings.hue is not None: fields.append(f"<hueLevel>{settings.hue}</hueLevel>")
        
        if not fields:
            print("Uyarı: Hiçbir renk ayarı girilmedi.")
            return False

        xml_content = "".join(fields)

        xml_body = f"""<?xml version="1.0" encoding="UTF-8"?>
        <Color version="1.0" xmlns="{self.NAMESPACE}">
            {xml_content}
        </Color>"""
        
        response = self._session.request("PUT", endpoint, data=xml_body)
        return is_success_response(response)

    def switch_day_night(self, mode: str, channel: int = 1) -> bool:
        """
        Gece görüşünü değiştirir (auto, day, night).
        Endpoint: /Image/channels/ID/IrcutFilterExt
        """
        validated = DayNightMode(IrcutFilterType=mode)
        endpoint = f"/Image/channels/{channel}/IrcutFilterExt"
        
        xml_body = f"""<?xml version="1.0" encoding="UTF-8"?>
<IrcutFilterExt version="1.0" xmlns="{self.NAMESPACE}">
    <IrcutFilterType>{validated.mode}</IrcutFilterType>
</IrcutFilterExt>"""
        
        response = self._session.request("PUT", endpoint, data=xml_body)
        return is_success_response(response)