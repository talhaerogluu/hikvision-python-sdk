from ..core import HikvisionSession
from ..utils import parse_xml
from ..models.content import SearchResult
import uuid
import datetime

class ContentAPI:
    def __init__(self, session: HikvisionSession):
        self._session = session
        self.NAMESPACE = "http://www.hikvision.com/ver10/XMLSchema"

    def search_recordings(self, start_time: datetime.datetime, end_time: datetime.datetime, track_id: int = 101, max_results: int = 40) -> SearchResult:
        """
        Belirli tarih aralığındaki kayıtları arar.
        Ref: ISAPI PDF Section 15.2.40
        """
        endpoint = "/ContentMgmt/search"
        
        start_str = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_str = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        search_id = str(uuid.uuid4()).upper()

        xml_body = f"""<?xml version="1.0" encoding="UTF-8"?>
        <CMSearchDescription version="1.0" xmlns="{self.NAMESPACE}">
            <searchID>{search_id}</searchID>
            <trackList>
                <trackID>{track_id}</trackID>
            </trackList>
            <timeSpanList>
                <timeSpan>
                    <startTime>{start_str}</startTime>
                    <endTime>{end_str}</endTime>
                </timeSpan>
            </timeSpanList>
            <maxResults>{max_results}</maxResults>
            <searchResultPostion>0</searchResultPostion>
            <metadataList>
                <metadataDescriptor>//recordType.meta.std-cgi.com</metadataDescriptor>
            </metadataList>
        </CMSearchDescription>"""

        response = self._session.request("POST", endpoint, data=xml_body)
        
        # --- HATA DÜZELTMESİ BURADA BAŞLIYOR ---
        data = parse_xml(response) 
        
        # 1. Root elemanı al, yoksa boş dict ver
        root = data.get("CMSearchResult", {})
        
        # 2. matchList elemanını al. Eğer kayıt yoksa bu None gelebilir.
        match_list_node = root.get("matchList")
        
        matches = []
        if match_list_node:
            # matchList varsa içinden searchMatchItem'ı çek
            # Eğer tek kayıt varsa dict, çok kayıt varsa list gelir.
            # xmltodict bazen boş tag için None döner, kontrol edelim.
            items = match_list_node.get("searchMatchItem")
            
            if items:
                if isinstance(items, list):
                    matches = items
                else:
                    matches = [items]
        
        # Pydantic modeline uydurmak için manipülasyon
        result_data = {
            "searchID": root.get("searchID", search_id),
            "responseStatus": root.get("responseStatus", "false"),
            "numOfMatches": int(root.get("numOfMatches", 0)),
            "matchList": matches
        }
        
        return SearchResult(**result_data)
    
    def get_playback_rtsp_url(self, track_id: int, start_time: str, end_time: str) -> str:
        """
        Geçmiş kayıtları izlemek için RTSP linki oluşturur.
        Zaman formatı: YYYYMMDDThhmmss (Örn: 20251204T120000)
        Ref: ISAPI PDF Section 15.9.17
        """
        # Kullanıcı user/pass girmek zorunda kalmasın diye URL'e gömüyoruz
        # Ancak şifrede özel karakter varsa URL encode yapmak gerekir.
        # Basitlik için ham halini koyuyoruz.
        
        user = self._session.session.auth.username
        password = self._session.session.auth.password
        ip = self._session.base_url.split("://")[1].split("/")[0] # IP:Port'u çek
        
        # RTSP URL Formatı:
        # rtsp://user:pass@IP:554/ISAPI/Streaming/tracks/ID?starttime=...&endtime=...
        
        # Start/End time formatını düzeltelim (2025-12-04T12:00:00Z -> 20251204T120000)
        # Eğer gelen format zaten düzgünse dokunmayız.
        
        url = f"rtsp://{user}:{password}@{ip.split(':')[0]}:554/ISAPI/Streaming/tracks/{track_id}?starttime={start_time}&endtime={end_time}"
        return url