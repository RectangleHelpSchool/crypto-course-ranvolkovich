from approvalfetcher.model.approval import ApprovalEventCollection
from .eth_utils import hex_to_int


def normalize_approval_amount(data: str) -> str:
    hex_value = data[2:] if data.startswith('0x') else data
    int_value = int(hex_value, 16) if hex_value else 0
    MAX_UINT256 = 2**256 - 1
    THRESHOLD = 2**255
    if int_value >= THRESHOLD or int_value == MAX_UINT256:
        return "INFINITY"

    return data


def format_approval_text(approval_events: ApprovalEventCollection) -> str:
    if approval_events.total_events == 0:
        return "No approval events found."
    lines = []
    for event in approval_events.events:
        token_display = event.token_symbol or event.token_name or "UnknownERC20"
        # Check if value is INFINITY before converting
        amount: str | int
        if event.value == "INFINITY":
            amount = "INFINITY"
        else:
            amount = hex_to_int(event.value)
        lines.append(f"approval on {token_display} to {event.spender} on amount of {amount}")
    return "\n".join(lines)
