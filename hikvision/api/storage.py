from typing import List, Union
import xmltodict
from ..core import HikvisionSession
from ..models.storage import HDDInfo
from ..utils import parse_xml, is_success_response

class StorageAPI:
    def __init__(self, session: HikvisionSession):
        self._session = session

    def get_hdd_status(self) -> List[HDDInfo]:
        """
        Disk durumunu çeker.
        """
        # PLAN A: Modern Yöntem (Fiziksel HDD)
        endpoint_a = "/ContentMgmt/Storage/hdd"
        
        # Hem büyük harfli (HDDList) hem küçük harfli (hddList) versiyonları deniyoruz
        disks = self._fetch_from_endpoint(endpoint_a, ["HDDList", "hddList"], ["HDD", "hdd"])
        
        if disks:
            return disks
            
        # PLAN B: Eski Yöntem (Mantıksal Bölümler)
        endpoint_b = "/System/Storage/volumes"
        return self._fetch_from_endpoint(endpoint_b, ["StorageVolumeList", "storageVolumeList"], ["StorageVolume", "storageVolume"])

    def _fetch_from_endpoint(self, endpoint: str, list_nodes: List[str], item_nodes: List[str]) -> List[HDDInfo]:
        try:
            response = self._session.request("GET", endpoint)
            data = xmltodict.parse(response.text, process_namespaces=False)

            # Helper: İlk bulunan node'u döndür
            def find_first(data_dict, candidates):
                for name in candidates:
                    if name in data_dict:
                        return data_dict[name]
                return None

            # Root liste node'unu bul
            root = find_first(data, list_nodes)
            if not root:
                return []

            # Elemanları bul
            items = find_first(root, item_nodes)
            if not items:
                return []

            # Tek item -> listeye sar
            if isinstance(items, dict):
                items = [items]

            results = []
            for item in items:
                try:
                    info = HDDInfo(
                        id=int(item.get("id") or item.get("volumeID") or 0),
                        hddName=item.get("hddName") or item.get("volumeName") or "Unknown",
                        hddPath=item.get("hddPath"),
                        hddType=item.get("hddType") or item.get("volumeType"),
                        status=item.get("status") or "unknown",
                        capacity=int(item.get("capacity") or 0),
                        freeSpace=int(item.get("freeSpace") or 0),
                        property=item.get("property")
                    )
                    results.append(info)
                except Exception as e:
                    print(f"   ⚠️ Disk verisi işlenirken hata: {e}")

            return results

        except Exception:
            return []

    def format_hdd(self, hdd_id: int) -> bool:
        endpoint = f"/ContentMgmt/Storage/hdd/{hdd_id}/format"
        response = self._session.request("PUT", endpoint)
        return is_success_response(response)