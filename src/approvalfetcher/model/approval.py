from pydantic import BaseModel, Field, AfterValidator
from datetime import datetime, timezone
from typing import Optional

from typing import Annotated
from approvalfetcher.utils.valdation.eth_validtor import eth_address
EthAddress = Annotated[str, AfterValidator(eth_address)]

class ApprovalEvent(BaseModel):
    token_address: EthAddress
    token_symbol: Optional[str] = Field(None, description="Token symbol (optional)")
    spender: EthAddress
    value: str = Field(..., description="Approved amount in wei (as string to preserve precision)")

class ApprovalEvents(BaseModel):
    address: EthAddress
    total_events: int = Field(..., description="Total number of approval events found")
    scanned_blocks: int = Field(..., description="Total number of blocks scanned")
    events: list[ApprovalEvent] = Field(default_factory=list, description="List of approval events")
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of when data was fetched")
