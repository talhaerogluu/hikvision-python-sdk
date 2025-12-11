from pydantic import BaseModel, Field

class AudioChannel(BaseModel):
    """
    Ses Kanalı Ayarları (Mikrofon/Hoparlör)
    Ref: ISAPI PDF Section 15.10.5
    """
    id: int = Field(..., alias="id")
    enabled: bool = Field(..., alias="enabled")
    audio_type: str = Field(..., alias="audioInputType") # micIn, lineIn
    volume: int = Field(..., alias="inputVolume") # 0-100 arası seviye