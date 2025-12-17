from typing import Annotated

from fastapi import APIRouter, Depends

from approvalfetcher.model.approval import EvmAddress, ApprovalEvents
from approvalfetcher.dto.approval.approval_response import ApprovalsResponse, to_response
from approvalfetcher.services.approval_service import ApprovalService
from approvalfetcher.services.dependencies import get_approval_service, get_coingecko_client
from approvalfetcher.clients.coingecko_client import CoinGeckoClient
from approvalfetcher.utils.config import get_settings
from approvalfetcher.utils.throttling import Throttling
from datetime import datetime, timezone

router = APIRouter(prefix="", tags=["approvals"])
settings = get_settings()
throttler = Throttling(max_tasks=settings.max_concurrent_tasks)


@router.post("/get_approvals")
async def get_approvals(
        addresses: list[EvmAddress],
        approval_service: Annotated[ApprovalService, Depends(get_approval_service)],
        coingecko_client: Annotated[CoinGeckoClient, Depends(get_coingecko_client)],
        get_token_price: bool
) -> ApprovalsResponse:

    approval_events_list = await throttler.submit(addresses, approval_service.fetch_all_approvals)

    prices = None
    if get_token_price and approval_events_list:
        all_events = [event for ae in approval_events_list for event in ae.events]
        if all_events:
            token_addresses = list(set(event.token_address for event in all_events))
            prices = await coingecko_client.get_multiple_prices(token_addresses)

    return to_response(approval_events_list, prices)
