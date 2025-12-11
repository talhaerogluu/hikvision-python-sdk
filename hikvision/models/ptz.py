from pydantic import BaseModel, Field
from enum import Enum

class PTZCoordinate(BaseModel):
    """
    Tek bir eksen için 0-255 aralığındaki koordinat.
    """
    x: int = Field(..., ge=0, le=255, description="X ekseni kordinatı (0-255)")
    y: int = Field(..., ge=0, le=255, description="Y ekseni kordinatı (0-255)")

class PTZRegion(BaseModel):
    """
    Position3D (3D Zoom) için başlangıç ve bitiş noktalarını tanımlar.
    """
    start_x: int = Field(..., ge=0, le=255, description="Başlangıç X kordinatı")
    start_y: int = Field(..., ge=0, le=255, description="Başlangıç Y kordinatı")
    end_x: int = Field(..., ge=0, le=255, description="Bitiş X kordinatı")
    end_y: int = Field(..., ge=0, le=255, description="Bitiş Y kordinatı")

class PresetData(BaseModel):
    """
    Preset noktalarına gitmek için gerekli ID.
    Ref: ISAPI PDF Section 8.13.2
    """
    preset_id: int = Field(..., ge=1, le=255, description="Ön tanımlı nokta ID'si (Genelde 1-255)")

class PTZAuxCommand(str, Enum):
    """
    PTZ Yardımcı Komutları için Sabitler.
    Kullanıcı 'WIPER' yazmakla uğraşmaz, PTZAuxCommand.WIPER seçer.
    """
    LIGHT = "LIGHT"   # IR Işık
    WIPER = "WIPER"   # Silecek
    FAN = "FAN"       # Fan
    HEATER = "HEATER" # Isıtıcı
    # Eğer kamerada başka özellik varsa buraya eklenir

# İleride eklenecek:
# class PTZStatus(BaseModel): ... # Kameranın anlık Pan/Tilt/Zoom değerleri