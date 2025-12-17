from approvalfetcher.model.approval import ApprovalEvent
from approvalfetcher.services.approval_service import ApprovalService


def test_filter_latest_approvals_keeps_latest():
    events_with_block = [
        (ApprovalEvent(
            token_address="0xdAC17F958D2ee523a2206206994597C13D831ec7",
            spender="0x1111111254fb6c44bac0bed2854e76f90643097d",
            value="0x64"
        ), 1000),
        (ApprovalEvent(
            token_address="0xdAC17F958D2ee523a2206206994597C13D831ec7",
            spender="0x1111111254fb6c44bac0bed2854e76f90643097d",
            value="0x0"
        ), 2000),
        (ApprovalEvent(
            token_address="0xdAC17F958D2ee523a2206206994597C13D831ec7",
            spender="0x1111111254fb6c44bac0bed2854e76f90643097d",
            value="0x3e8"
        ), 3000),
    ]

    filtered = ApprovalService._filter_latest_approvals(events_with_block)

    assert len(filtered) == 1
    assert filtered[0].value == "0x3e8"


def test_filter_latest_approvals_different_tokens():
    events_with_block = [
        (ApprovalEvent(
            token_address="0xdAC17F958D2ee523a2206206994597C13D831ec7",
            spender="0x1111111254fb6c44bac0bed2854e76f90643097d",
            value="0x64"
        ), 1000),
        (ApprovalEvent(
            token_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            spender="0x1111111254fb6c44bac0bed2854e76f90643097d",
            value="0xc8"
        ), 2000),
    ]

    filtered = ApprovalService._filter_latest_approvals(events_with_block)

    assert len(filtered) == 2


def test_filter_latest_approvals_different_spenders():
    events_with_block = [
        (ApprovalEvent(
            token_address="0xdAC17F958D2ee523a2206206994597C13D831ec7",
            spender="0x1111111254fb6c44bac0bed2854e76f90643097d",
            value="0x64"
        ), 1000),
        (ApprovalEvent(
            token_address="0xdAC17F958D2ee523a2206206994597C13D831ec7",
            spender="0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",
            value="0xc8"
        ), 2000),
    ]

    filtered = ApprovalService._filter_latest_approvals(events_with_block)

    assert len(filtered) == 1
    assert filtered[0].spender == "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45"
    assert filtered[0].value == "0xc8"


def test_filter_latest_approvals_case_insensitive():
    events_with_block = [
        (ApprovalEvent(
            token_address="0xdAC17F958D2ee523a2206206994597C13D831ec7",
            spender="0x1111111254fb6c44bac0bed2854e76f90643097d",
            value="0x64"
        ), 1000),
        (ApprovalEvent(
            token_address="0xdac17f958d2ee523a2206206994597c13d831ec7",
            spender="0x1111111254fb6c44bac0bed2854e76f90643097d",
            value="0xc8"
        ), 2000),
    ]

    filtered = ApprovalService._filter_latest_approvals(events_with_block)

    assert len(filtered) == 1
    assert filtered[0].value == "0xc8"


def test_filter_latest_approvals_empty_list():
    filtered = ApprovalService._filter_latest_approvals([])
    assert len(filtered) == 0
