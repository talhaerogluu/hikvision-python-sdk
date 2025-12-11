from pydantic import BaseModel, Field, field_validator
from typing import Optional

# --- OSD (Ekrana Yazı Yazma) Modelleri ---
# Ref: ISAPI PDF Section 8.4.5 [cite: 1040, 1045]

class TextOverlay(BaseModel):
    """Ekranda görünen metin kutusu ayarları"""
    id: int = Field(default=1, ge=1, le=4, description="Overlay ID (Genelde 1-4 arası)")
    enabled: bool = Field(default=True)
    pos_x: int = Field(alias="posX", default=0, ge=0, description="X koordinatı")
    pos_y: int = Field(alias="posY", default=0, ge=0, description="Y koordinatı (16'nın katları önerilir)")
    message: str = Field(max_length=44, description="Ekranda görünecek yazı")

    @field_validator('message')
    def validate_message(cls, v):
        # Hikvision genelde ASCII karakterleri sever, Türkçe karakterler bazen sorun çıkarabilir
        # Şimdilik uzunluk kontrolü yeterli.
        return v

# --- Görüntü Ayarları Modelleri ---
# Ref: ISAPI PDF Section 8.14.24 (Color) [cite: 2244]

class ColorSetup(BaseModel):
    """Parlaklık, Kontrast ve Renk Ayarları"""
    brightness: Optional[int] = Field(default=None, alias="brightnessLevel", ge=0, le=100)
    contrast: Optional[int] = Field(default=None, alias="contrastLevel", ge=0, le=100)
    saturation: Optional[int] = Field(default=None, alias="saturationLevel", ge=0, le=100)
    hue: Optional[int] = Field(default=None, alias="hueLevel", ge=0, le=100)

# Ref: ISAPI PDF Section 8.14.13 (Day/Night) [cite: 2206]
class DayNightMode(BaseModel):
    """Gece Görüş Modu Ayarları"""
    # day, night, auto, schedule
    mode: str = Field(alias="IrcutFilterType", pattern="^(day|night|auto|schedule)$")