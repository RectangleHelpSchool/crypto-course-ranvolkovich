from typing import Annotated

from fastapi import APIRouter, Depends

from approvalfetcher.model.approval import EthAddress, ApprovalEvents
from approvalfetcher.dto.approval.approval_response import ApprovalsResponse, to_response
from approvalfetcher.services.approval_service import ApprovalService
from approvalfetcher.services.dependencies import get_approval_service
from approvalfetcher.utils.config import get_settings
from approvalfetcher.utils.throttling import Throttling
from datetime import datetime, timezone

router = APIRouter(prefix="", tags=["approvals"])
settings = get_settings()
throttler = Throttling(max_tasks=settings.max_concurrent_tasks)


@router.post("/get_approvals")
async def get_approvals(
        addresses: list[EthAddress],
        approval_service: Annotated[ApprovalService, Depends(get_approval_service)]
) -> ApprovalsResponse:
    approval_events_list = await throttler.submit(addresses, approval_service.fetch_all_approvals)

    combined_events = ApprovalEvents(
        address="0x0000000000000000000000000000000000000000",  # Zero address for combined results
        total_events=sum(ae.total_events for ae in approval_events_list),
        scanned_blocks=max((ae.scanned_blocks for ae in approval_events_list), default=0),
        events=[event for ae in approval_events_list for event in ae.events],
        fetched_at=datetime.now(timezone.utc)
    )

    return to_response(combined_events)
