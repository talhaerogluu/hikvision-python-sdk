import xmltodict
from typing import Optional, Dict, Any, Union
import logging
import requests
from .models.common import ResponseStatus

logger = logging.getLogger("HikvisionUtils")

def parse_xml(content: Union[str, bytes, requests.Response]) -> Dict[str, Any]:
    """
    Hikvision'dan gelen veriyi (String, Bytes veya Response objesi) 
    Python Dictionary'e çevirir.
    """
    xml_string = ""
    
    # 1. Gelen verinin tipini kontrol et ve string'e çevir
    try:
        if isinstance(content, requests.Response):
            # Eğer Response objesi geldiyse içindeki text'i al
            xml_string = content.text
        elif isinstance(content, bytes):
            # Eğer byte geldiyse decode et
            xml_string = content.decode('utf-8', errors='ignore')
        else:
            # Zaten string ise olduğu gibi kullan
            xml_string = str(content)

        if not xml_string.strip():
            return {}

        # 2. Parse İşlemi
        return xmltodict.parse(
            xml_string, 
            dict_constructor=dict,
            process_namespaces=False # Namespace karmaşasını önle
        )
    except Exception as e:
        logger.error(f"XML Parse Hatası: {e}")
        return {}

def parse_response_status(xml_input: Union[str, requests.Response]) -> Optional[ResponseStatus]:
    """
    ISAPI ResponseStatus XML'ini Pydantic modele çevirir.
    """
    data = parse_xml(xml_input)

    # XML root elementini bulmaya çalışıyoruz
    payload = data.get("ResponseStatus") or data.get("Response")

    if not payload:
        return None

    try:
        return ResponseStatus(**payload)
    except Exception as e:
        logger.warning(f"ResponseStatus modeli oluşturulamadı: {e}")
        return None

def is_success_response(xml_input: Union[str, requests.Response]) -> bool:
    """
    Gelen cevabın 'Başarılı' olup olmadığını kontrol eder.
    PUT/POST/DELETE işlemleri için kullanılır.
    """
    status = parse_response_status(xml_input)
    
    if status is None:
        # ResponseStatus dönmediyse, işlem başarısız varsayılır (Güvenli yaklaşım)
        # Ancak 200 OK dönüp body boşsa, bunu çağıran yer status_code kontrolü yapmalı.
        return False

    if not status.is_ok():
        logger.error(f"API Hatası: {status.status_string} (Kod: {status.status_code})")
        return False

    if status.status_code == 7:
        logger.info("İşlem Başarılı (Cihazın yeniden başlatılması gerekiyor).")

    return True