from typing import Dict

TR_TENTS = {
    -1: 0,  # EMPTY
    1: 1,  # TREE
    -3: 2,  # TENT
    -4: 3,  # GREEN
}

TR_KAKURASU = {
    -1: 0,  # EMPTY
    0: 0,  # CROSS
    1: 1,  # BLACK
}
# EMPTY, 1-9
TR_SUDOKU = {
    -1: 0,
    1: 1,
    2: 2,
    3: 3,
    4: 4,
    5: 5,
    6: 6,
    7: 7,
    8: 8,
    9: 9,
}

# EMPTY, WALL (no-constraint), WALL (with constraints, 1-4), Light, -4 (lit cell, ignored as empty)
TR_LIGHTUP = {
    0: 0,  # WALL (constraint of 0)
    1: 1,  # WALL (constraint of 1)
    2: 2,  # WALL (constraint of 2)
    3: 3,  # WALL (constraint of 3)
    4: 4,  # WALL (constraint of 4)
    -2: 5,  # WALL (no-constraint)
    -1: 6,  # EMPTY
    -3: 7,  # LIGHT
    -4: 0,  # NO LIGHT BULB (ignored as empty)
}

# EMPTY, 0-8, FLAG, SAFE
TR_MINESWEEPER = {
    0: 0,  # UNMARKED
    1: 1,
    2: 2,
    3: 3,
    4: 4,
    5: 5,
    6: 6,
    7: 7,
    8: 8,
    -1: 9,  # UNMARKED
    -3: 10,  # FLAG
    -4: 11,  # SAFE
}

TRANSLATION_DICTS = {
    "kakurasu": TR_KAKURASU,
    "tents": TR_TENTS,
    "sudoku": TR_SUDOKU,
    "lightup": TR_LIGHTUP,
    "minesweeper": TR_MINESWEEPER,
}

def get_translation_dict(puzzle_type):
    """Get the appropriate translation dictionary for a puzzle type"""
    tr_dict = TRANSLATION_DICTS.get(puzzle_type)
    if not tr_dict:
        raise ValueError(f"No translation dictionary found for puzzle type: {puzzle_type}")
    return tr_dict

def game_state_to_string(game_state, translation_dict):
    """Convert a 2D game_state to a string representation using translation_dict"""
    return [translation_dict[cell] for row in game_state for cell in row]
