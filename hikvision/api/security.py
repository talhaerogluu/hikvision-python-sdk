from typing import List
from ..core import HikvisionSession
from ..models.security import User
from ..utils import parse_xml
from ..utils import is_success_response
import xmltodict

class SecurityAPI:
    def __init__(self, session: HikvisionSession):
        self._session = session

    def get_users(self) -> List[User]:
        """
        Kayıtlı kullanıcıları listeler.
        Endpoint: /Security/users
        Ref: [cite: 5286]
        """
        endpoint = "/Security/users"
        response = self._session.request("GET", endpoint)
        
        data = parse_xml(response)
        # XML Listesi bazen tek elemanlı olabilir, utils.parse_xml bunu yönetmeli
        # Basitçe UserList -> User hiyerarşisini çözüyoruz
        user_list = data.get("UserList", {}).get("User", [])
        
        if isinstance(user_list, dict): # Tek kullanıcı varsa dict gelir
            user_list = [user_list]
            
        return [User(**u) for u in user_list]
    
    def create_user(self, username: str, password: str, level: str = "Operator") -> bool:
        """
        Yeni kullanıcı oluşturur.
        Level: Administrator, Operator, Viewer
        Ref: ISAPI PDF Section 8.8.1 (POST)
        """
        endpoint = "/Security/users"
        
        # Kullanıcı ID'sini otomatik bulmak zor, genelde kamera sıradaki ID'yi atar 
        # ama XML'de ID alanı zorunlu olabilir. 
        # Güvenli yöntem: Mevcut kullanıcıları sayıp +1 eklemek veya manuel ID vermek.
        # Biz burada ID=10'dan başlayarak boş bir ID bulma mantığı kurabiliriz 
        # ama basitlik için POST metodunun ID'siz çalışıp çalışmadığını deneyeceğiz.
        # Doküman ID zorunlu diyor[cite: 1319].
        
        # 1. Mevcut kullanıcıları çek ve boş ID bul
        users = self.get_users()
        existing_ids = [u.id for u in users]
        new_id = next(i for i in range(2, 32) if i not in existing_ids) # 1 Admin'dir, 2'den başla
        
        xml_body = f"""<User version="1.0" xmlns="http://www.hikvision.com/ver10/XMLSchema">
            <id>{new_id}</id>
            <userName>{username}</userName>
            <password>{password}</password>
            <userLevel>{level}</userLevel>
        </User>"""
        
        # Kullanıcı ekleme işlemi POST ile yapılır
        response = self._session.request("POST", endpoint, data=xml_body)
        return is_success_response(response)

    def delete_user(self, user_id: int) -> bool:
        """
        Kullanıcıyı siler. (Admin ID=1 silinemez!)
        Ref: ISAPI PDF Section 8.8.2 (DELETE)
        """
        if user_id == 1:
            print("Hata: Admin kullanıcısı silinemez.")
            return False
            
        endpoint = f"/Security/users/{user_id}"
        response = self._session.request("DELETE", endpoint)
        return is_success_response(response)
    
    def change_password(self, user_id: int, new_password: str) -> bool:
        """
        Mevcut kullanıcının şifresini değiştirir.
        Ref: ISAPI PDF Section 8.8.2 (PUT) [cite: 1312]
        """
        endpoint = f"/Security/users/{user_id}"
        
        # Önce mevcut bilgileri çek (UserName ve Level değişmemeli)
        response = self._session.request("GET", endpoint)
        data = xmltodict.parse(response.text, process_namespaces=False)
        
        if "User" in data:
            data["User"]["password"] = new_password
            
            new_xml = xmltodict.unparse(data, pretty=True)
            put_response = self._session.request("PUT", endpoint, data=new_xml)
            return is_success_response(put_response)
            
        return False