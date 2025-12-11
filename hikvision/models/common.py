from pydantic import BaseModel, Field, AliasChoices
from typing import Optional, Union

class ResponseStatus(BaseModel):
    request_url: Optional[str] = Field(None, validation_alias=AliasChoices("requestURL", "requestUri"))
    status_code: int = Field(..., validation_alias="statusCode")
    status_string: Optional[str] = Field(None, validation_alias="statusString")
    id: Optional[str] = Field(None) # Bazen ID döner (yeni kullanıcı eklerken vb.)

    def is_ok(self) -> bool:
        """
        İşlemin başarılı olup olmadığını kontrol eder.
        1: OK
        7: Reboot Required (İşlem başarılı ama yeniden başlatma lazım)
        """
        # Dokümana göre 1 ve 7 başarı statüsüdür.
        return self.status_code in [1, 7]