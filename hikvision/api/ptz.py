from ..core import HikvisionSession
from ..models.ptz import PTZRegion, PresetData, PTZAuxCommand
from ..utils import is_success_response
from typing import Union

class PTZAPI:
    def __init__(self, session: HikvisionSession):
        self._session = session
        self.INVERT_Y_AXIS = True
        # PTZ Servisi genelde ver20 (ISAPI) ister
        self.NAMESPACE = "http://www.isapi.org/ver20/XMLSchema"

    def _get_url(self, endpoint_suffix: str) -> str:
        return f"/PTZCtrl/channels/{self._session.config.channel}/{endpoint_suffix}"

    def zoom_3d(self, start_x: int, start_y: int, end_x: int, end_y: int, width: int = 1920, height: int = 1080, invert_y: bool = True) -> bool:
        """
        Pixel koordinatlarını alır, 0-255 formatına çevirir ve 3D Zoom yapar.
        
        Args:
            start_x, start_y: Başlangıç pikseli (Mouse Down)
            end_x, end_y: Bitiş pikseli (Mouse Up)
            width, height: Görüntünün o anki çözünürlüğü (Oranlamak için)
            invert_y: Hikvision için Y eksenini ters çevir (255 - Y)
        """
        # 1. Görüntü boyutuna göre 0-255 oranlama (Senin kodundaki mantık)
        sx_255 = int((start_x / width) * 255)
        sy_255 = int((start_y / height) * 255)
        ex_255 = int((end_x / width) * 255)
        ey_255 = int((end_y / height) * 255)

        # 2. Y Eksenini Ters Çevirme (Kritik Düzeltme)
        if invert_y:
            sy_255 = 255 - sy_255
            ey_255 = 255 - ey_255

        # 3. Değerlerin 0-255 dışına taşmamasını garanti et
        sx = max(0, min(sx_255, 255))
        sy = max(0, min(sy_255, 255))
        ex = max(0, min(ex_255, 255))
        ey = max(0, min(ey_255, 255))

        # XML Oluşturma
        # Senin kodunda namespace yoktu, burada da sadelik için namespace'siz denenebilir
        # ama ISAPI standardı genelde namespace ister. Şimdilik senin koduna sadık kalarak
        # namespace'i XML body içine gömüyoruz.
        
        xml_body = f"""<position3D version="2.0" xmlns="{self.NAMESPACE}">
    <StartPoint>
        <positionX>{sx}</positionX>
        <positionY>{sy}</positionY>
    </StartPoint>
    <EndPoint>
        <positionX>{ex}</positionX>
        <positionY>{ey}</positionY>
    </EndPoint>
</position3D>"""

        endpoint = f"/PTZCtrl/channels/{self._session.config.channel}/position3D"
        
        # Senin kodunda 'X-Requested-With' header'ı vardı. 
        # Bunu session seviyesinde değil, sadece bu istek için ekleyebiliriz.
        headers = {
            "Content-Type": "application/xml", # ISAPI genelde XML ister
            "X-Requested-With": "XMLHttpRequest" # Tarayıcı taklidi
        }

        try:
            response = self._session.request("PUT", endpoint, data=xml_body, headers=headers)
            return is_success_response(response)
        except Exception as e:
            print(f"3D Zoom Hatası: {e}")
            return False

    def goto_preset(self, preset_id: int) -> bool:
        """
        Ön tanımlı noktaya (Preset) gitme.
        """
        validated_data = PresetData(preset_id=preset_id)
        endpoint = f"/PTZCtrl/channels/{self._session.config.channel}/presets/{validated_data.preset_id}/goto"
        
        response = self._session.request("PUT", endpoint, data=None)
        return is_success_response(response)
    
    def aux_control(self, command: Union[PTZAuxCommand, str], enable: bool = True) -> bool:
        """
        PTZ Yardımcı donanımlarını kontrol eder.
        
        Kullanım:
            cam.ptz.aux_control(PTZAuxCommand.WIPER, True)
        """
        
        # Eğer kullanıcı Enum gönderdiyse içindeki string değerini al (.value)
        # Eğer direkt string gönderdiyse olduğu gibi kullan
        if isinstance(command, PTZAuxCommand):
            cmd_value = command.value
        else:
            cmd_value = str(command)

        # Komutun sonuna _PWRON ekle
        cmd_str = f"{cmd_value.upper()}_PWRON"
        endpoint = f"/PTZCtrl/channels/{self._session.config.channel}/auxcontrol?command={cmd_str}"
        
        # AuxStatus genelde ver10 kullanır ama hata verirse ver20 deneriz
        # Şimdilik PTZ genelinde ver20 kabul ettik, deneyelim.
        xml_body = f"""<?xml version="1.0" encoding="UTF-8"?>
<PTZAuxStatus version="2.0" xmlns="{self.NAMESPACE}">
    <enabled>{str(enable).lower()}</enabled>
</PTZAuxStatus>"""
        
        response = self._session.request("PUT", endpoint, data=xml_body)
        return is_success_response(response)
    
    def one_push_focus(self) -> bool:
        """
        Tek tuşla otomatik odaklama.
        """
        # Dokümanda onepushfocus yazıyor, hata verirse focus->focus
        endpoint = f"/PTZCtrl/channels/{self._session.config.channel}/onepushfocus/start"
        response = self._session.request("PUT", endpoint)
        return is_success_response(response)

    def reset_lens(self) -> bool:
        """
        Lens motorunu sıfırla.
        """
        endpoint = f"/PTZCtrl/channels/{self._session.config.channel}/onepushfocus/reset"
        response = self._session.request("PUT", endpoint)
        return is_success_response(response)