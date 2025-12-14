from datetime import datetime
from approvalfetcher.model.approval import ApprovalEvent
from approvalfetcher.services.approval_service import ApprovalService


def test_filter_latest_approvals_keeps_latest():
    """Test that only the latest approval for each (token, spender) pair is kept."""
    events = [
        ApprovalEvent(
            block_number=1000,
            timestamp=datetime(2025, 1, 1, 10, 0, 0),
            transaction_hash="0xaaa",
            token_address="0xTOKEN1",
            owner="0xOWNER",
            spender="0xSPENDER1",
            value="0x64"  # 100
        ),
        ApprovalEvent(
            block_number=2000,
            timestamp=datetime(2025, 1, 2, 10, 0, 0),
            transaction_hash="0xbbb",
            token_address="0xTOKEN1",
            owner="0xOWNER",
            spender="0xSPENDER1",
            value="0x0"  # 0 (revocation)
        ),
        ApprovalEvent(
            block_number=3000,
            timestamp=datetime(2025, 1, 3, 10, 0, 0),
            transaction_hash="0xccc",
            token_address="0xTOKEN1",
            owner="0xOWNER",
            spender="0xSPENDER1",
            value="0x3e8"  # 1000
        ),
    ]

    filtered = ApprovalService._filter_latest_approvals(events)

    # Should only keep the latest (block 3000)
    assert len(filtered) == 1
    assert filtered[0].block_number == 3000
    assert filtered[0].value == "0x3e8"


def test_filter_latest_approvals_different_tokens():
    """Test that different tokens are kept separate."""
    events = [
        ApprovalEvent(
            block_number=1000,
            timestamp=datetime(2025, 1, 1, 10, 0, 0),
            transaction_hash="0xaaa",
            token_address="0xTOKEN1",
            owner="0xOWNER",
            spender="0xSPENDER1",
            value="0x64"
        ),
        ApprovalEvent(
            block_number=2000,
            timestamp=datetime(2025, 1, 2, 10, 0, 0),
            transaction_hash="0xbbb",
            token_address="0xTOKEN2",
            owner="0xOWNER",
            spender="0xSPENDER1",
            value="0xc8"
        ),
    ]

    filtered = ApprovalService._filter_latest_approvals(events)

    # Should keep both (different tokens)
    assert len(filtered) == 2


def test_filter_latest_approvals_different_spenders():
    """Test that different spenders are kept separate."""
    events = [
        ApprovalEvent(
            block_number=1000,
            timestamp=datetime(2025, 1, 1, 10, 0, 0),
            transaction_hash="0xaaa",
            token_address="0xTOKEN1",
            owner="0xOWNER",
            spender="0xSPENDER1",
            value="0x64"
        ),
        ApprovalEvent(
            block_number=2000,
            timestamp=datetime(2025, 1, 2, 10, 0, 0),
            transaction_hash="0xbbb",
            token_address="0xTOKEN1",
            owner="0xOWNER",
            spender="0xSPENDER2",
            value="0xc8"
        ),
    ]

    filtered = ApprovalService._filter_latest_approvals(events)

    # Should keep both (different spenders)
    assert len(filtered) == 2


def test_filter_latest_approvals_case_insensitive():
    """Test that filtering is case-insensitive for addresses."""
    events = [
        ApprovalEvent(
            block_number=1000,
            timestamp=datetime(2025, 1, 1, 10, 0, 0),
            transaction_hash="0xaaa",
            token_address="0xTOKEN1",
            owner="0xOWNER",
            spender="0xSPENDER1",
            value="0x64"
        ),
        ApprovalEvent(
            block_number=2000,
            timestamp=datetime(2025, 1, 2, 10, 0, 0),
            transaction_hash="0xbbb",
            token_address="0xtoken1",  # Different case
            owner="0xOWNER",
            spender="0xspender1",  # Different case
            value="0xc8"
        ),
    ]

    filtered = ApprovalService._filter_latest_approvals(events)

    # Should only keep the latest (case-insensitive matching)
    assert len(filtered) == 1
    assert filtered[0].block_number == 2000


def test_filter_latest_approvals_empty_list():
    """Test that empty list returns empty list."""
    filtered = ApprovalService._filter_latest_approvals([])
    assert len(filtered) == 0
