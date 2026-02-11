"""
Order state machine — defines valid status transitions.
Prevents invalid state changes (e.g. delivered → pending).
"""

from typing import List, Optional


# Valid transitions: current_status → [allowed_next_statuses]
ORDER_TRANSITIONS = {
    "pending": ["confirmed", "cancelled"],
    "confirmed": ["processing", "cancelled", "refunded"],
    "processing": ["shipped", "cancelled"],
    "shipped": ["delivered"],
    "delivered": ["refunded"],
    "cancelled": [],      # Terminal state
    "refunded": [],       # Terminal state
}

ALL_ORDER_STATUSES = list(ORDER_TRANSITIONS.keys())


def validate_transition(current_status: str, target_status: str) -> bool:
    """
    Check if a status transition is valid.
    
    Returns:
        True if the transition is allowed.
    """
    allowed = ORDER_TRANSITIONS.get(current_status, [])
    return target_status in allowed


def get_allowed_transitions(current_status: str) -> List[str]:
    """Get list of valid next statuses from the current status."""
    return ORDER_TRANSITIONS.get(current_status, [])


def is_terminal_status(status: str) -> bool:
    """Check if a status is terminal (no further transitions possible)."""
    return len(ORDER_TRANSITIONS.get(status, [])) == 0


def is_cancellable(status: str) -> bool:
    """Check if an order in this status can be cancelled."""
    return "cancelled" in ORDER_TRANSITIONS.get(status, [])


def is_refundable(status: str) -> bool:
    """Check if an order in this status can be refunded."""
    return "refunded" in ORDER_TRANSITIONS.get(status, [])
