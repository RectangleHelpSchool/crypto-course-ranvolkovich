from pydantic import BaseModel, Field

class ApprovalRequest(BaseModel):
    addresses: list[str] = Field(..., description="Ethereum addresses to scan")