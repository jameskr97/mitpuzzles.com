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

    this function exists for the minority number of games that used an older data storage format.
    when exported, all the games are given the same format, but in order to ensure this, we need to check
    which games ARE vs AR NOT in the desired format.
    TODO(james): retroactively convert all old-format stored games to the new format
    """
    if board_state:
        for row in board_state:
            if isinstance(row, list) and -1 in row:
                return True

    if action_history:
        for action in action_history:
            if action.get("old_value") == -1 or action.get("new_value") == -1:
                return True

    return False
