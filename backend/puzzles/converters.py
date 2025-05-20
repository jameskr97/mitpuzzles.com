from typing import Dict

TR_TENTS = {
    -1: "0",  # EMPTY
    1: "1",  # TREE
    -3: "2",  # TENT
    -4: "3",  # GREEN
}

TR_KAKURASU = {
    -1: "0",  # EMPTY
    0: "0",  # CROSS
    1: "1",  # BLACK
}
# EMPTY, 1-9
TR_SUDOKU = {
    -1: "0",
    1: "1",
    2: "2",
    3: "3",
    4: "4",
    5: "5",
    6: "6",
    7: "7",
    8: "8",
    9: "9",
}

# EMPTY, WALL (no-constraint), WALL (with constraints, 1-4), Light, -4 (lit cell, ignored as empty)
TR_LIGHTUP = {
    0: "0",  # WALL (constraint of 0)
    1: "1",  # WALL (constraint of 1)
    2: "2",  # WALL (constraint of 2)
    3: "3",  # WALL (constraint of 3)
    4: "4",  # WALL (constraint of 4)
    -2: "5",  # WALL (no-constraint)
    -1: "6",  # EMPTY
    -3: "7",  # LIGHT
    -4: "0",  # NO LIGHT BULB (ignored as empty)
}

# EMPTY, 0-8, FLAG, SAFE
TR_MINESWEEPER = {
    -1: "_",  # EMPTY
    0: "0",
    1: "1",
    2: "2",
    3: "3",
    4: "4",
    5: "5",
    6: "6",
    7: "7",
    8: "8",
    -3: "F",  # FLAG
    -4: "S",  # SAFE
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
    return "".join(translation_dict[cell] for row in game_state for cell in row)

def convert_kakurasu(k_puzzle: Dict) -> Dict:
    converted_result = {
        "rows": k_puzzle["rows"],
        "cols": k_puzzle["cols"],
        "col_sum": k_puzzle["col_sums"],
        "row_sum": k_puzzle["row_sums"],
        "board_initial": "".join(TR_KAKURASU[cell] for row in k_puzzle["game_state"] for cell in row),
        "board_solution": "".join(TR_KAKURASU[cell] for row in k_puzzle["game_board"] for cell in row),
    }

    return converted_result


def convert_tents(puzzle: Dict) -> Dict:
    return {
        "rows": puzzle["length"],
        "cols": puzzle["width"],
        "row_counts": puzzle["row_tent_counts"],
        "col_counts": puzzle["col_tent_counts"],
        "board_initial": "".join(TR_TENTS[cell] for row in puzzle["game_state"] for cell in row),
        "board_solution": "".join(TR_TENTS[cell] for row in puzzle["game_board"] for cell in row),
    }


def convert_sudoku(puzzle: Dict) -> Dict:
    return {
        "rows": puzzle["rows"],
        "cols": puzzle["cols"],
        "board_initial": "".join(TR_SUDOKU[cell] for row in puzzle["game_state"] for cell in row),
        "board_solution": "".join(TR_SUDOKU[cell] for row in puzzle["game_board"] for cell in row),
    }


def convert_lightup(puzzle: Dict) -> Dict:
    return {
        "rows": puzzle["rows"],
        "cols": puzzle["cols"],
        "board_initial": "".join(TR_LIGHTUP[cell] for row in puzzle["game_state"] for cell in row),
        "board_solution": "".join(TR_LIGHTUP[cell] for row in puzzle["game_board"] for cell in row),
    }


def convert_minesweeper(puzzle: Dict) -> Dict:
    return {
        "rows": puzzle["n_rows"],
        "cols": puzzle["n_cols"],
        "board_initial": "".join(TR_MINESWEEPER[cell] for row in puzzle["game_state"] for cell in row),
        "board_solution": "".join(TR_MINESWEEPER[cell] for row in puzzle["game_board"] for cell in row),
    }
