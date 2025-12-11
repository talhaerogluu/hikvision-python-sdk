from pydantic import BaseModel, Field
from typing import Optional

# Ref: ISAPI PDF Section 8.8.2 User XML Block [cite: 5300]

class User(BaseModel):
    id: int = Field(..., ge=1, le=32)
    user_name: str = Field(..., validation_alias="userName")
    user_level: str = Field(..., validation_alias="userLevel") # Administrator, Operator, Viewer
    
    # Şifre sadece gönderirken gereklidir, okurken gelmez (Write-only)
    password: Optional[str] = None