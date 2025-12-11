from pydantic import BaseModel, Field, AliasChoices
from typing import Optional

# Ref: ISAPI PDF Section 8.9.3 StreamingChannel XML Block [cite: 5387]

class VideoSettings(BaseModel):
    enabled: bool = Field(default=True)
    codec_type: Optional[str] = Field(default=None, validation_alias="videoCodecType") # H.264, H.265
    resolution_width: int = Field(..., validation_alias="videoResolutionWidth")
    resolution_height: int = Field(..., validation_alias="videoResolutionHeight")
    
    # FPS: API'den 2500 gelir, biz bunu 25.00 olarak kullanıcıya sunmak isteyebiliriz.
    # Şimdilik ham haliyle (x100) tutalım, API katmanında çevirelim.
    max_frame_rate: int = Field(..., validation_alias="maxFrameRate", description="FPS * 100 (Örn: 2500)")
    
    bitrate_type: str = Field(..., validation_alias="videoQualityControlType") # CBR (Sabit), VBR (Değişken)
    constant_bit_rate: Optional[int] = Field(default=None, validation_alias="constantBitRate", description="kbps cinsinden")
    fixed_quality: Optional[int] = Field(default=None, validation_alias="fixedQuality", description="VBR için kalite yüzdesi (0-100)")
    
    iframe_interval: Optional[int] = Field(default=None, validation_alias="keyFrameInterval", description="I-Frame sıklığı")
    
class StreamingTransport(BaseModel):
    rtsp_port: int = Field(554, validation_alias="rtspPortNo")
    max_packet_size: int = Field(1000, validation_alias="maxPacketSize")

class StreamingChannel(BaseModel):
    id: int
    name: str = Field(..., validation_alias="channelName")
    enabled: bool
    
    # XML içinde iç içe (nested) yapılar vardır: <Video>...</Video>
    video: VideoSettings = Field(..., validation_alias="Video")
    transport: Optional[StreamingTransport] = Field(..., validation_alias="Transport")