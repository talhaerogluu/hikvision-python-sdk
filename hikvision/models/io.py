from pydantic import BaseModel, Field

# Ref: ISAPI PDF Section 8.3.1 IOPortStatus XML Block [cite: 943]

class IOPortStatus(BaseModel):
    port_id: int = Field(..., validation_alias="ioPortID")
    port_type: str = Field(..., validation_alias="ioPortType") # input, output
    state: str = Field(..., validation_alias="ioState") # active, inactive