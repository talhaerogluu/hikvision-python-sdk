from typing import Generator

import xmltodict

from ..core import HikvisionSession
from ..models.event import EventAlert
from ..utils import parse_xml, is_success_response


class EventAPI:
    def __init__(self, session: HikvisionSession):
        self._session = session
        # Hareket algılama için olası adresler (Modern -> Eski)
        self.VMD_ENDPOINTS = [
            "/System/Video/inputs/channels/{channel}/motionDetection",
            "/MotionDetectionExt/{channel}",
            "/MotionDetection/{channel}",
        ]
        # Çalışan adresi hafızada tut
        self.working_endpoint: str | None = None

    def listen_alert_stream(self) -> Generator[EventAlert, None, None]:
        """
        Canlı olay akışını (Server Push) dinler.
        Sürekli açık kalan bir bağlantıdır.
        Ref: ISAPI PDF Section 8.11.12
        """
        endpoint = "/Event/notification/alertStream"
        url = f"{self._session.base_url}{endpoint}"

        # Mock modundaysa sonsuz döngüye girmesin, tek bir fake alert versin
        if self._session.mock_mode:
            mock_xml = self._session.request("GET", endpoint)
            data = parse_xml(mock_xml)
            yield EventAlert(**data.get("EventNotificationAlert", {}))
            return

        try:
            # stream=True ile bağlantıyı açıyoruz
            with self._session.session.get(url, stream=True, timeout=60) as response:
                response.raise_for_status()

                buffer = ""
                for chunk in response.iter_content(chunk_size=1024):
                    if not chunk:
                        continue

                    buffer += chunk.decode("utf-8", errors="ignore")

                    # XML bloğunun sonunu yakala
                    while "</EventNotificationAlert>" in buffer:
                        start_tag = "<EventNotificationAlert"
                        end_tag = "</EventNotificationAlert>"

                        start_idx = buffer.find(start_tag)
                        end_idx = buffer.find(end_tag)

                        if start_idx != -1 and end_idx != -1:
                            # XML'i söküp al
                            xml_str = buffer[start_idx : end_idx + len(end_tag)]

                            # Geri kalanını buffer'da tut
                            buffer = buffer[end_idx + len(end_tag) :]

                            # Parse et ve yield ile fırlat
                            data = parse_xml(xml_str)
                            payload = data.get("EventNotificationAlert", {})
                            if payload:
                                yield EventAlert(**payload)
                        else:
                            break

        except Exception as e:
            print(f"Stream Hatası: {e}")

    def _find_working_endpoint(self, channel: int) -> str:
        """Çalışan endpoint'i bulur ve önbelleğe alır."""
        if self.working_endpoint:
            return self.working_endpoint.format(channel=channel)

        for pattern in self.VMD_ENDPOINTS:
            endpoint = pattern.format(channel=channel)
            try:
                # Sadece varlığını kontrol etmek için GET atıyoruz
                self._session.request("GET", endpoint)
                print(f"   ✓ Çalışan VMD adresi bulundu: {endpoint}")
                self.working_endpoint = pattern
                return endpoint
            except Exception:
                continue

        raise Exception(
            "Hiçbir hareket algılama adresi çalışmadı (Yetki veya Destek Yok)."
        )

    def get_motion_detection_status(self, channel: int = 1) -> bool:
        """
        Hareket algılamanın açık olup olmadığını kontrol eder.
        """
        try:
            endpoint = self._find_working_endpoint(channel)
            response = self._session.request("GET", endpoint)

            data = parse_xml(response)

            # Farklı endpointler farklı Root tag dönebilir
            # Genelde: <MotionDetection><enabled>...</enabled></MotionDetection>
            root = (
                data.get("MotionDetection")
                or data.get("MotionDetectionExt")
                or {}
            )

            return str(root.get("enabled")).lower() == "true"

        except Exception as e:
            print(f"   ⚠️ VMD Durum Okuma Hatası: {e}")
            return False

    def set_motion_detection(self, enabled: bool, channel: int = 1) -> bool:
        """
        Hareket algılamayı açar veya kapatır.
        """
        try:
            endpoint = self._find_working_endpoint(channel)

            # 1. OKU (READ)
            response = self._session.request("GET", endpoint)

            # --- DÜZELTME BURADA ---
            # response bir requests.Response objesidir. xmltodict string ister.
            # response.text ile string'i alıyoruz.
            xml_content = response.text 
            
            # 2. DEĞİŞTİR (MODIFY)
            data = xmltodict.parse(xml_content, process_namespaces=False)

            # Root elemanını bul (MotionDetection veya MotionDetectionExt)
            root_key = next(iter(data))  # İlk anahtar root'tur

            if "enabled" in data[root_key]:
                data[root_key]["enabled"] = "true" if enabled else "false"

                # 3. YAZ (WRITE)
                new_xml = xmltodict.unparse(data, pretty=True)
                response_put = self._session.request("PUT", endpoint, data=new_xml)
                return is_success_response(response_put)

            return False
        except Exception as e:
            print(f"   ❌ VMD Ayarlama Hatası: {e}")
            # Hata detayını görmek için gerekirse:
            # import traceback
            # traceback.print_exc()
            return False