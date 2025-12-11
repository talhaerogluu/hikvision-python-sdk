from pydantic import BaseModel, Field, AliasChoices
from typing import Optional
from datetime import datetime

class EventAlert(BaseModel):
    """
    Canlı alarm akışından gelen tekil olay bildirimi.
    Ref: ISAPI PDF Section 8.11.12 EventNotificationAlert XML Block
    """
    ip_address: Optional[str] = Field(default=None, validation_alias="ipAddress")
    port_no: Optional[int] = Field(default=None, validation_alias="portNo")
    channel_id: Optional[str] = Field(default="1", validation_alias="channelID")
    date_time: Optional[datetime] = Field(default=None, validation_alias="dateTime")
    active_post_count: int = Field(default=0, validation_alias="activePostCount")
    
    # Olay Tipi: VMD (Motion), IO, videoloss, shelteralarm vb.
    event_type: str = Field(..., validation_alias="eventType") 
    
    # Durum: active (başladı), inactive (bitti)
    event_state: str = Field(..., validation_alias="eventState") 
    
    description: Optional[str] = Field(default="", validation_alias="eventDescription")

class VMDConfig(BaseModel):
    """
    Hareket Algılama Ayarları
    Ref: ISAPI PDF Section 8.10.1
    """
    enabled: bool = Field(..., alias="enabled")
    # Hassasiyet genelde XML içinde iç içe liste halindedir,
    # basitleştirmek için sadece ana açma/kapama ve grid kontrolü yapacağız.
    # Ancak modern kameralarda sensitivityLevel direkt de gelebilir.