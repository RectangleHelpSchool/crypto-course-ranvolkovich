from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional


class ApprovalEvent(BaseModel):
    """Represents a single ERC-20 Approval event."""

    block_number: int = Field(..., description="Block number where the event occurred")
    timestamp: datetime = Field(..., description="Block timestamp")
    transaction_hash: str = Field(..., description="Transaction hash")
    token_address: str = Field(..., description="Token contract address")
    token_name: Optional[str] = Field(None, description="Token name (optional)")
    token_symbol: Optional[str] = Field(None, description="Token symbol (optional)")
    owner: str = Field(..., description="Address granting the approval")
    spender: str = Field(..., description="Address receiving the approval")
    value: str = Field(..., description="Approved amount in wei (as string to preserve precision)")

    @field_validator('timestamp', mode='before')
    @classmethod
    def parse_timestamp(cls, v):
        """Parse timestamp from various formats."""
        if isinstance(v, str):
            return datetime.fromtimestamp(int(v))
        if isinstance(v, int):
            return datetime.fromtimestamp(v)
        return v

    @field_validator('transaction_hash', 'token_address', 'owner', 'spender')
    @classmethod
    def validate_hex_string(cls, v):
        """Ensure hex strings are lowercase."""
        if isinstance(v, str):
            return v.lower()
        return v


class ApprovalEventCollection(BaseModel):
    """Collection of approval events with metadata."""

    address: str = Field(..., description="Ethereum address that was scanned")
    total_events: int = Field(..., description="Total number of approval events found")
    scanned_blocks: int = Field(..., description="Total number of blocks scanned")
    events: list[ApprovalEvent] = Field(default_factory=list, description="List of approval events")
    fetched_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of when data was fetched")

    @field_validator('address')
    @classmethod
    def validate_address(cls, v):
        """Ensure address is lowercase."""
        if isinstance(v, str):
            return v.lower()
        return v
