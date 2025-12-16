from hexbytes import HexBytes

from approvalfetcher.model.approval import ApprovalEvents

THRESHOLD = 2 ** 255


def normalize_approval_amount(data: str) -> str:
    hex_value = data[2:] if data.startswith('0x') else data
    int_value = int(hex_value, 16) if hex_value else 0

    return str(int_value)


def _parse_amount(log_data: HexBytes) -> str:
    amount = int(log_data.hex(), 16)
    if amount > THRESHOLD:
        return "INFINITY"
    return str(amount)


def format_approval_text(approval_events: ApprovalEvents) -> str:
    if approval_events.total_events == 0:
        return "No approval events found."
    lines = []
    for event in approval_events.events:
        token_display = event.token_symbol or event.token_name or "UnknownERC20"
        amount: str = _parse_amount(HexBytes(event.value))
        lines.append(f"approval on {token_display} to {event.spender} on amount of {amount}")
    return "\n".join(lines)
