from pydantic import BaseModel, Field, AliasChoices
from typing import List, Optional, Any

class TimeSpan(BaseModel):
    start_time: str = Field(..., alias="startTime")
    end_time: str = Field(..., alias="endTime")

class SearchMatchItem(BaseModel):
    """Bulunan her bir kayıt parçasını temsil eder"""
    # sourceID bazen gelmeyebilir veya farklı isimde olabilir, Optional yapıyoruz
    source_id: Optional[str] = Field(default=None, validation_alias=AliasChoices("sourceID", "sourceId"))
    track_id: Optional[int] = Field(default=None, alias="trackID")
    time_span: TimeSpan = Field(alias="timeSpan")
    
    # Detaylar her zaman gelmez, Any veya Dict olarak alıp geçelim
    media_segment_descriptor: Optional[Any] = Field(default=None, alias="mediaSegmentDescriptor")
    metadata_descriptor: Optional[Any] = Field(default=None, alias="metadataDescriptor")

class SearchResult(BaseModel):
    """Arama sonucunda dönen ana yapı"""
    search_id: Optional[str] = Field(default=None, alias="searchID")
    response_status: str = Field(alias="responseStatus") 
    num_of_matches: int = Field(alias="numOfMatches")
    match_list: List[SearchMatchItem] = Field(default=[], alias="matchList")

class Track(BaseModel):
    track_id: int = Field(..., alias="trackID") # Kanal ID (101, 201 vb.)