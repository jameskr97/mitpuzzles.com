from typing import Dict
import os.path
import json

from django.core.management.base import BaseCommand
from core import models
from puzzles.management.commands._common import _ensure_dir_exists, _confirm_action

# EMPTY, TREE, TENT, GREEN
TR_TENTS    = { -1: "0",  1: "1", -3: "2", -4: "3" }
# EMPTY, CROSS, BLACK
TR_KAKURASU = { -1: "0", 0: "0", 1: "1" }
# EMPTY, 1-9
TR_SUDOKU   = { -1: "0", 1: "1", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9" }
# EMPTY, WALL (no-constraint), WALL (with constraints, 1-4), Light, -4 (lit cell, ignored as empty)
TR_LIGHTUP  = { -1: ".", 0: "5", 1: "1", 2: "2", 3: "3", 4: "4", -3: "L", -4: "0" }
# # EMPTY, 0-8, FLAG, SAFE
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
    -4: "S"   # SAFE
}

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
        "board_solution":  "".join(TR_TENTS[cell] for row in puzzle["game_board"] for cell in row)
    }

def convert_sudoku(puzzle: Dict) -> Dict:
    return {
        "rows": puzzle["rows"],
        "cols": puzzle["cols"],
        "board_initial": "".join(TR_SUDOKU[cell] for row in puzzle["game_state"] for cell in row),
        "board_solution": "".join(TR_SUDOKU[cell] for row in puzzle["game_board"] for cell in row)
    }

def convert_lightup(puzzle: Dict) -> Dict:
    return {
        "rows": puzzle["rows"],
        "cols": puzzle["cols"],
        "board_initial": "".join(TR_LIGHTUP[cell] for row in puzzle["game_state"] for cell in row),
        "board_solution": "".join(TR_LIGHTUP[cell] for row in puzzle["game_board"] for cell in row)
    }

def convert_minesweeper(puzzle: Dict) -> Dict:
    return {
        "rows": puzzle["n_rows"],
        "cols": puzzle["n_cols"],
        "board_initial": "".join(TR_MINESWEEPER[cell] for row in puzzle["game_state"] for cell in row),
        "board_solution": "".join(TR_MINESWEEPER[cell] for row in puzzle["game_board"] for cell in row),
    }

class Command(BaseCommand):
    help = "Validate and import a puzzle from a JSON file"

    def add_arguments(self, parser):
        parser.add_argument("path", type=str, help="The path to a directory containing the puzzle data")

    def handle(self, *args, **options):
        path = options["path"]
        _ensure_dir_exists(path)


        KNOWN_PUZZLES = ["kakurasu", "lightup", "minesweeper", "sudoku", "tents"]
        # KNOWN_PUZZLES = ["tents", "kakurasu", "sudoku", "lightup"]

        # get all json files, ensuring the start with "x_" where X is a known puzzle type
        json_files = sorted([
            f for f in os.listdir(path)
                if f.endswith(".json") and
                   any([f.startswith(x) for x in KNOWN_PUZZLES])]
        )
        if not json_files:
            self.stdout.write(self.style.ERROR("No JSON files found in the specified directory: %s" % path))
            return

        # tell user what files we will process for puzzle data
        self.stdout.write(self.style.SUCCESS("Found the following JSON files in %s:" % path))
        for json_file in json_files:
            self.stdout.write(" - {}".format(json_file))

        # ask user to confirm
        _confirm_action("Do you want to proceed with importing these files?")

        # import each file
        for file in json_files:
            puzzle_type = file.split("_")[0]
            puzzle_class = ".".join(file.split("_")[1:]).replace(".json", "")
            self.stdout.write(f"importing {puzzle_type} -> {puzzle_class}")
            data = json.loads(open(os.path.join(path, file), 'r').read())

            # ensure outermost element is a list
            if not isinstance(data, list):
                self.stdout.write(self.style.ERROR("The file %s does not contain a list at the top level." % file))
                continue

            conversion_function = {
                "kakurasu": convert_kakurasu,
                "tents": convert_tents,
                "sudoku": convert_sudoku,
                "lightup": convert_lightup,
                "minesweeper": convert_minesweeper
            }

            for puzzle in data:
                converted_puzzle = conversion_function[puzzle_type](puzzle)
                models.Puzzles.objects.create(
                    puzzle_type=puzzle_type,
                    puzzle_class=puzzle_class,
                    puzzle_data=converted_puzzle
                )
            self.stdout.write(self.style.SUCCESS("Successfully imported puzzle: %s" % file))
