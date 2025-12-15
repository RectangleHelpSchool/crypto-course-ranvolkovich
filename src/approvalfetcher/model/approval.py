from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone
from typing import Optional


class ApprovalEvent(BaseModel):
    token_address: str = Field(..., description="Token contract address")
    token_name: Optional[str] = Field(None, description="Token name (optional)")
    token_symbol: Optional[str] = Field(None, description="Token symbol (optional)")
    owner: str = Field(..., description="Address granting the approval")
    spender: str = Field(..., description="Address receiving the approval")
    value: str = Field(..., description="Approved amount in wei (as string to preserve precision)")

    @field_validator('token_address', 'owner', 'spender')
    @classmethod
    def validate_hex_string(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v


class ApprovalEventCollection(BaseModel):
    address: str = Field(..., description="Ethereum address that was scanned")
    total_events: int = Field(..., description="Total number of approval events found")
    scanned_blocks: int = Field(..., description="Total number of blocks scanned")
    events: list[ApprovalEvent] = Field(default_factory=list, description="List of approval events")
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of when data was fetched")

    @field_validator('address')
    @classmethod
    def validate_address(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v
