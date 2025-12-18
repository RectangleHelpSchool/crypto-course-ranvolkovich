from typing import Annotated

from fastapi import APIRouter, Depends

from approvalfetcher.dto.approval.approval_response import ApprovalsResponse, to_response
from approvalfetcher.model.approval import EvmAddress
from approvalfetcher.services.approval_service import ApprovalService
from approvalfetcher.services.price_service import PriceService
from approvalfetcher.services.dependencies import get_approval_service, get_price_service
from approvalfetcher.utils.config import get_settings
from approvalfetcher.utils.throttling import Throttling

router = APIRouter(prefix="", tags=["approvals"])
settings = get_settings()
throttler = Throttling(max_tasks=settings.max_concurrent_tasks)


@router.post("/get_approvals")
async def get_approvals(
        addresses: list[EvmAddress],
        approval_service: Annotated[ApprovalService, Depends(get_approval_service)],
        price_service: Annotated[PriceService, Depends(get_price_service)],
        get_token_price: bool = True
) -> ApprovalsResponse:
    approval_events_list = await throttler.submit(addresses, approval_service.fetch_all_approvals)

    prices = None
    if get_token_price and approval_events_list:
        all_events = [event for ae in approval_events_list for event in ae.events]
        if all_events:
            token_addresses = [event.token_address for event in all_events]
            prices = await price_service.fetch_prices(token_addresses)

    return to_response(approval_events_list, prices)
