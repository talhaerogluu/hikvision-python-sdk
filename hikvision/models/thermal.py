from pydantic import BaseModel, Field
from typing import Optional

class TemperatureInfo(BaseModel):
    """Termal kameradan alınan anlık sıcaklık verisi"""
    # JSON cevabı genelde şöyledir: {"Thermometry": {"maxTemperature": 36.5, ...}}
    # Bu yüzden iç içe modeller gerekebilir ama basitleştirilmiş hali:
    
    max_temp: Optional[float] = Field(..., alias="maxTemperature", description="Görüntüdeki en yüksek sıcaklık")
    min_temp: Optional[float] = Field(..., alias="minTemperature", description="Görüntüdeki en düşük sıcaklık")
    average_temp: Optional[float] = Field(..., alias="averageTemperature", description="Ortalama sıcaklık")
    unit: Optional[float] = Field(default="degree", alias="temperatureUnit") # celsius/fahrenheit/kelvin