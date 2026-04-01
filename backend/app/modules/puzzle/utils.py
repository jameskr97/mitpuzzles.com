def format_duration(time_seconds: float) -> str:
    """format a duration in seconds to a human-readable string like '1h:23m:45.67s'."""
    parts = []
    remaining = int(time_seconds)

    days = remaining // 86400
    remaining %= 86400
    hours = remaining // 3600
    remaining %= 3600
    minutes = remaining // 60
    seconds = time_seconds % 60

    if days > 0:
        parts.append(f"{days}d")
    if hours > 0 or days > 0:
        parts.append(f"{hours}h")
    if minutes > 0 or hours > 0 or days > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds:.2f}s")

    return ":".join(parts)


def is_research_format(board_state, action_history):
    """
    check if data is already in research format by looking for -1 (empty cell marker).

    prioritizes action_history over board_state: the first move on any cell will have
    old_value=-1 in research format, which is a more reliable signal than board_state
    (which may have no empty cells if the puzzle was completed).
    """
    if action_history:
        for action in action_history:
            if action.get("old_value") == -1 or action.get("new_value") == -1:
                return True

    if board_state:
        for row in board_state:
            if isinstance(row, list) and -1 in row:
                return True

    return False
