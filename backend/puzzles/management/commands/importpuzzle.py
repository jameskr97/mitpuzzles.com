import hashlib
import json
import os.path
from typing import Dict

from django.core.management.base import BaseCommand

from puzzles import models
from puzzles.management.commands._common import _confirm_action, _ensure_path_exists

class Command(BaseCommand):
    help = "Validate and import a puzzle from a JSON file"

    def add_arguments(self, parser):
        parser.add_argument("path", type=str, help="The path to a directory containing the puzzle data")

    def handle(self, *args, **options):
        path = options["path"]
        _ensure_path_exists(path)

        # if not a directory, assume it's a json file that should be imported
        if not os.path.isdir(path):
            self.import_file(path)
            return

        # get all json files in the directory
        json_files = sorted([f for f in os.listdir(path) if f.endswith(".json")])
        self.stdout.write(self.style.SUCCESS("Found the following JSON files in %s:" % path))
        for json_file in json_files:
            self.stdout.write(" - {}".format(json_file))
        _confirm_action("Do you want to proceed with importing these files?")

        # import each file
        for file in json_files:
            file_path = str(os.path.join(path, file))
            self.import_file(file_path)

    def import_file(self, file: str) -> bool:
        filename_ext = os.path.basename(file)
        filename, ext = os.path.splitext(filename_ext)
        try:
            puzzle_type = filename.split("_")[0]  # e.g., "kakurasu", "tents", etc.
            puzzle_size = filename.split("_")[1]  # e.g., "4x4", "9x9", etc.
            puzzle_difficulty = filename.split("_")[2]  # e.g., "easy", "hard", etc.
        except IndexError:
            self.stdout.write(self.style.ERROR(f"{filename}: Invalid filename format: {filename_ext}. Expected format: <puzzle_type>_<puzzle_size>_<puzzle_difficulty>.json. Skipping file..."))
            return False

        # load file
        data = json.loads(open(file, "r").read())
        if not isinstance(data, list):
            self.stdout.write(self.style.ERROR(f"{filename}: The file {file} does not contain a list at the top level."))
            return False

        # hash all the puzzles
        puzzles = {}
        for puzzle in data:
            # remove unnecessary keys
            puzzle.pop("idx", None)
            puzzle.pop("difficulty", None)

            # hash puzzle
            serialized = json.dumps(puzzle, sort_keys=True, separators=(",", ":"))
            puzzle_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

            if puzzle_hash in puzzles:
                self.stdout.write(self.style.ERROR(f"{filename}: Duplicate puzzle found with hash {puzzle_hash}. Skipping..."))
                continue
            puzzles[puzzle_hash] = puzzle

        # check if any of those hashes are in the database
        existing_hashes = models.Puzzle.objects.filter(puzzle_hash__in=puzzles.keys()).values_list('puzzle_hash', flat=True)
        if existing_hashes:
            self.stdout.write(self.style.ERROR(f"{filename}: Skipping {len(existing_hashes)} puzzles that already exist in the database."))

        # import the puzzles
        for puzzle_hash in puzzles:
            # skip puzzles that already exist in the database
            if puzzle_hash in existing_hashes: continue

            models.Puzzle.objects.create(
                puzzle_hash=puzzle_hash,
                puzzle_type=puzzle_type,
                puzzle_size=puzzle_size,
                puzzle_difficulty=puzzle_difficulty,
                puzzle_data=puzzles[puzzle_hash],
            )

        return True
