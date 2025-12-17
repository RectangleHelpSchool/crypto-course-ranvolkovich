from hexbytes import HexBytes
from pydantic import BaseModel, Field
from approvalfetcher.model.approval import ApprovalEvents
from approvalfetcher.utils.formatters import parse_amount


class ApprovalEventResponse(BaseModel):
    token_symbol: str | None = Field(None, description="Token symbol")
    spender: str = Field(..., description="Spender address")
    value: str = Field(..., description="Approved amount")


class ApprovalsResponse(BaseModel):
    events: list[ApprovalEventResponse] = Field(..., description="List of approval events")


def to_response(approval_events: ApprovalEvents) -> ApprovalsResponse:
    return ApprovalsResponse(
        events=[
            ApprovalEventResponse(
                token_symbol=event.token_symbol,
                spender=event.spender,
                value=parse_amount(HexBytes(event.value))
            )
            for event in approval_events.events
        ]
    )
