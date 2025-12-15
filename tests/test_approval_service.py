from approvalfetcher.model.approval import ApprovalEvent
from approvalfetcher.services.approval_service import ApprovalService


def test_filter_latest_approvals_keeps_latest():
    events_with_block = [
        (ApprovalEvent(
            token_address="0xTOKEN1",
            owner="0xOWNER",
            spender="0xSPENDER1",
            value="0x64"
        ), 1000),
        (ApprovalEvent(
            token_address="0xTOKEN1",
            owner="0xOWNER",
            spender="0xSPENDER1",
            value="0x0"
        ), 2000),
        (ApprovalEvent(
            token_address="0xTOKEN1",
            owner="0xOWNER",
            spender="0xSPENDER1",
            value="0x3e8"
        ), 3000),
    ]

    filtered = ApprovalService._filter_latest_approvals(events_with_block)

    assert len(filtered) == 1
    assert filtered[0].value == "0x3e8"


def test_filter_latest_approvals_different_tokens():
    events_with_block = [
        (ApprovalEvent(
            token_address="0xTOKEN1",
            owner="0xOWNER",
            spender="0xSPENDER1",
            value="0x64"
        ), 1000),
        (ApprovalEvent(
            token_address="0xTOKEN2",
            owner="0xOWNER",
            spender="0xSPENDER1",
            value="0xc8"
        ), 2000),
    ]

    filtered = ApprovalService._filter_latest_approvals(events_with_block)

    assert len(filtered) == 2


def test_filter_latest_approvals_different_spenders():
    events_with_block = [
        (ApprovalEvent(
            token_address="0xTOKEN1",
            owner="0xOWNER",
            spender="0xSPENDER1",
            value="0x64"
        ), 1000),
        (ApprovalEvent(
            token_address="0xTOKEN1",
            owner="0xOWNER",
            spender="0xSPENDER2",
            value="0xc8"
        ), 2000),
    ]

    filtered = ApprovalService._filter_latest_approvals(events_with_block)

    assert len(filtered) == 2


def test_filter_latest_approvals_case_insensitive():
    events_with_block = [
        (ApprovalEvent(
            token_address="0xTOKEN1",
            owner="0xOWNER",
            spender="0xSPENDER1",
            value="0x64"
        ), 1000),
        (ApprovalEvent(
            token_address="0xtoken1",
            owner="0xOWNER",
            spender="0xspender1",
            value="0xc8"
        ), 2000),
    ]

    filtered = ApprovalService._filter_latest_approvals(events_with_block)

    assert len(filtered) == 1
    assert filtered[0].value == "0xc8"


def test_filter_latest_approvals_empty_list():
    filtered = ApprovalService._filter_latest_approvals([])
    assert len(filtered) == 0
