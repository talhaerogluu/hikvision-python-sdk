from pydantic import BaseModel, Field, AliasChoices
from typing import List, Optional

class DeviceInfo(BaseModel):
    """
    /System/deviceInfo endpoint'inden dönen veriyi doğrular.
    Field alias'ları XML'deki etiket isimleridir.
    """
    device_name: str = Field(validation_alias=AliasChoices("deviceName", "devicename"))
    model: str = Field(validation_alias="model")
    serial_number: str = Field(validation_alias="serialNumber")
    firmware_version: str = Field(validation_alias="firmwareVersion")
    
    # PDF'te olan ama bizim belki kullanmayacağımız alanlar opsiyonel olsun
    mac_address: str | None = Field(default=None, validation_alias="macAddress")

class MemoryStatus(BaseModel):
    usage: float = Field(alias="memoryUsage", description="MB cinsinden kullanım")
    available: float = Field(alias="memoryAvailable", description="MB cinsinden boş alan")
    description: Optional[str] = Field(default=None, alias="memoryDescription")

class CPUStatus(BaseModel):
    utilization: int = Field(alias="cpuUtilization", description="Yüzde olarak kullanım (0-100)")
    description: Optional[str] = Field(default=None, alias="cpuDescription")

class DeviceStatus(BaseModel):
    """
    Cihazın anlık sağlık durumu.
    Ref: ISAPI PDF Section 8.1.6 [cite: 430]
    """
    current_time: str = Field(alias="currentDeviceTime")
    uptime: int = Field(alias="deviceUpTime", description="Saniye cinsinden çalışma süresi")
    
    # Liste veya tekil gelebilir, validator ile yönetmek en doğrusu ama basit tutuyoruz
    cpu_list: Optional[List[CPUStatus]] = Field(default=None, alias="CPUList")
    memory_list: Optional[List[MemoryStatus]] = Field(default=None, alias="MemoryList")

class TimeConfig(BaseModel):
    """
    Kamera zaman ayarları.
    Ref: ISAPI PDF Section 8.1.7 Time XML Block
    """
    time_mode: str = Field(..., alias="timeMode") # NTP, manual
    local_time: str = Field(..., alias="localTime") # 2025-12-04T15:30:00
    time_zone: str = Field(..., alias="timeZone") # CST-8:00:00 (Format karışıktır)