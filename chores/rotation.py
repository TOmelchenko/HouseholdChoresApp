"""Pure round-robin rotation logic for chore assignments.

No Django imports here: this module must be importable and testable with
plain Python lists, independent of the database or the Django app registry.
"""


def next_assignee(roommate_ids: list[int], history: list[int]) -> int:
    """Return the roommate ID who should be assigned next in strict round-robin order.

    Args:
        roommate_ids: Current roommate IDs for the household, in the order
            rotation should follow. No duplicates. Must be non-empty.
        history: Roommate IDs of past assignments for one chore, in
            chronological order, oldest first (history[-1] is the most
            recent assignment). May be empty.

    Returns:
        The roommate ID who should be assigned next.

    Raises:
        ValueError: If roommate_ids is empty.
    """
    if not roommate_ids:
        raise ValueError("roommate_ids must not be empty")

    for past_roommate_id in reversed(history):
        if past_roommate_id in roommate_ids:
            index = roommate_ids.index(past_roommate_id)
            return roommate_ids[(index + 1) % len(roommate_ids)]

    return roommate_ids[0]
