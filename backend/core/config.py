import hashlib
import json

def get_game_settings():
    return {
        'minesweeper': MINESWEEPER,
        # 'sudoku': SUDOKU,
    }

def generate_settings_etag(request, *args, **kwargs):
    """
    Generates an ETag for the game settings.
    """
    data = json.dumps(get_game_settings(), sort_keys=True)
    return hashlib.md5(data.encode()).hexdigest()

MINESWEEPER = {
    "key": "minesweeper",
    "displayname": "Minesweeper",
    "modes": [
        {'options': {'rows': 9,  'columns': 9,  'mines': 10}, "displayname": "Easy" },
        {'options': {'rows': 16, 'columns': 16, 'mines': 40}, "displayname": "Medium" },
        {'options': {'rows': 16, 'columns': 30, 'mines': 99}, "displayname": "Difficult" },
    ],
}

SUDOKU = {
    "key": "sudoku",
    "displayname": "Sudoku",
    "modes": [
        {'options': {'pre_filled': 40},   "displayname": "Easy" },
        {'options': {'pre_filled': 30},   "displayname": "Medium" },
        {'options': {'pre_filled': 25},   "displayname": "Hard" },
    ]
}

