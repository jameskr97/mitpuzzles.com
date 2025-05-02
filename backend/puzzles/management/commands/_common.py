import os

from django.core.management.base import CommandError
from django.core.management.color import color_style

_style = color_style()

def _ensure_path_exists(file_path: str) -> None:
    if not os.path.exists(file_path):
        raise CommandError(_style.ERROR(f"File {file_path} does not exist."))


def _confirm_action(message: str) -> bool:
    """
    Confirm an action with the user.

    Args:
        message (str): The message to display to the user for confirmation.

    Returns:
        bool: True if the user confirms, False otherwise.
    """
    response = input(f"{message} (y/N): ").strip().lower()
    if response != 'y':
        raise CommandError(_style.ERROR("Action cancelled by user."))


def _get_puzzle_files(path: str) -> list:
    """
    Get all files in a directory with a specific extension.

    Args:
        path (str): The directory path.
        extension (str): The file extension to filter by.

    Returns:
        list: A sorted list of files with the specified extension.
    """
    KNOWN_PUZZLES = ["kakurasu", "lightup", "minesweeper", "sudoku", "tents"]

    valid_files = []
    for filename in os.listdir(path):
        if not filename.endswith(".json"): continue

        for prefix in KNOWN_PUZZLES:
            if not filename.startswith(prefix): continue
            valid_files.append(filename)

    if not valid_files:
        raise CommandError(_style.ERROR(f"No valid puzzle files found in {path}. Expected files to start with {', '.join(KNOWN_PUZZLES)}."))

    return sorted(valid_files)
