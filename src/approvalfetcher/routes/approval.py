from typing import Annotated
from fastapi import APIRouter, Depends

from approvalfetcher.model.approval import ApprovalEvents
from approvalfetcher.model.dto.approval.approval_request import ApprovalRequest
from approvalfetcher.services.approval_service import ApprovalService
from approvalfetcher.services.dependencies import get_approval_service
from approvalfetcher.utils.throttling import Throttling
from approvalfetcher.utils.config import get_settings

router = APIRouter(prefix="", tags=["approvals"])
settings = get_settings()
throttler = Throttling(max_tasks=settings.max_concurrent_tasks)

@router.post("/get_approvals")
async def get_approvals(
    request: ApprovalRequest,
    approval_service: Annotated[ApprovalService, Depends(get_approval_service)]
) -> list[ApprovalEvents]:
    return await throttler.submit(request.addresses, approval_service.fetch_all_approvals)
