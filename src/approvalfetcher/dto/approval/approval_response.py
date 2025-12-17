from hexbytes import HexBytes
from pydantic import BaseModel, Field
from approvalfetcher.model.approval import ApprovalEvents
from approvalfetcher.utils.formatters import parse_amount


class ApprovalEventResponse(BaseModel):
    token_symbol: str | None = Field(None, description="Token symbol")
    spender: str = Field(..., description="Spender address")
    value: str = Field(..., description="Approved amount")
    token_price: float | None = Field(None, description="Token price in USD")


class ApprovalsResponse(BaseModel):
    events: list[ApprovalEventResponse] = Field(..., description="List of approval events")


def to_response(approval_events_list: list[ApprovalEvents], prices: dict[str, float | None] | None = None) -> ApprovalsResponse:
    prices = prices or {}

    all_events = [event for ae in approval_events_list for event in ae.events]

    return ApprovalsResponse(
        events=[
            ApprovalEventResponse(
                token_symbol=event.token_symbol,
                spender=event.spender,
                value=parse_amount(HexBytes(event.value)),
                token_price=prices.get(event.token_address.lower())
            )
            for event in all_events
        ]
    )
