from pydantic import BaseModel, Field
from typing import Optional

class HDDInfo(BaseModel):
    """
    Sabit Disk veya SD Kart Bilgisi
    Ref: ISAPI PDF Section 15.2.47
    """
    id: int = Field(..., alias="id")
    name: str = Field(..., alias="hddName")
    path: Optional[str] = Field(default=None, alias="hddPath")
    type: Optional[str] = Field(default=None, alias="hddType") # Local, NAS
    status: str = Field(..., alias="status") # normal, unformatted, error, repairing
    capacity: int = Field(..., alias="capacity") # MB cinsinden toplam alan
    free_space: int = Field(..., alias="freeSpace") # MB cinsinden boş alan
    hdd_property: Optional[str] = Field(default=None, alias="property") # RW, RO

    @property
    def usage_percent(self) -> float:
        """Doluluk oranını hesaplar"""
        if self.capacity == 0: return 0.0
        used = self.capacity - self.free_space
        return round((used / self.capacity) * 100, 1)