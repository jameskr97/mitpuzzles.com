import os

from django.core.management.base import CommandError
from django.core.management.color import color_style

_style = color_style()

def _ensure_dir_exists(file_path: str) -> None:
    if not os.path.isdir(file_path):
        raise CommandError(_style.ERROR(f"File {file_path} does not exist."))

def _confirm_action(message: str) -> bool:
    """
    Confirm an action with the user.

    Args:
        message (str): The message to display to the user for confirmation.

    Returns:
        bool: True if the user confirms, False otherwise.
    """
    response = input(f"{message} (y/n): ").strip().lower()
    return response in ['y', 'yes']
