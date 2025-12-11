from pydantic import BaseModel, Field
from typing import Optional

class NetworkInterface(BaseModel):
    """
    Ağ Arayüzü Bilgileri
    Ref: ISAPI PDF Section 15.10.91
    """
    id: int = Field(..., alias="id")
    ip_address: str = Field(..., alias="ipAddress")
    subnet_mask: str = Field(..., alias="subnetMask")
    gateway: Optional[str] = Field(default=None) # XML'de iç içe olduğu için alias'ı manuel eşleyeceğiz
    mac_address: Optional[str] = Field(default=None, alias="PhysicalAddress")
    dhcp: bool = False