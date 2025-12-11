import xmltodict
from ..core import HikvisionSession
from ..models.streaming import StreamingChannel
from ..utils import parse_xml, is_success_response

class StreamingAPI:
    def __init__(self, session: HikvisionSession):
        self._session = session
        # Namespace artık GET'ten geleni kullanacağımız için dinamik olacak

    def get_channel_info(self, channel: int = 101) -> StreamingChannel:
        """Kanalın tüm yayın ayarlarını çeker."""
        endpoint = f"/Streaming/channels/{channel}"
        response = self._session.request("GET", endpoint)
        data = parse_xml(response)
        return StreamingChannel(**data.get("StreamingChannel", {}))

    def get_snapshot(self, channel: int = 101) -> bytes:
        endpoint = f"/Streaming/channels/{channel}/picture"
        return self._session.request_binary("GET", endpoint)

    def set_video_config(self, channel: int = 101, fps: int = None, bitrate: int = None, width: int = None, height: int = None) -> bool:
        """
        Video ayarlarını 'Read-Modify-Write' yöntemiyle günceller.
        Mevcut ayarları çeker, sadece isteneni değiştirir, geri yükler.
        """
        endpoint = f"/Streaming/channels/{channel}"
        
        response = self._session.request("GET", endpoint)
        
        # xmltodict ile dictionary'e çeviriyoruz (Namespace'leri koruyarak)
        # process_namespaces=False diyoruz ki '@xmlns' attribute'ları kaybolmasın
        data = xmltodict.parse(response.text, process_namespaces=False)
        
        if 'StreamingChannel' not in data or 'Video' not in data['StreamingChannel']:
            print("Hata: Gelen XML yapısı beklenmedik formatta.")
            return False
            
        video = data['StreamingChannel']['Video']
        
        
        if bitrate:
            video['constantBitRate'] = str(bitrate)
            video['videoQualityControlType'] = 'CBR' # Bitrate varsa CBR zorunludur
            
        if fps:
            # Hikvision FPS'i 100 ile çarpılmış ister (25 fps -> 2500)
            video['maxFrameRate'] = str(fps * 100)
            
        if width and height:
            video['videoResolutionWidth'] = str(width)
            video['videoResolutionHeight'] = str(height)

        new_xml_body = xmltodict.unparse(data, pretty=True)
        
        response_put = self._session.request("PUT", endpoint, data=new_xml_body)
        return is_success_response(response_put)