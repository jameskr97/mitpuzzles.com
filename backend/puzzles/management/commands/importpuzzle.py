import json
import os.path

from django.core.management.base import BaseCommand
from django.db import IntegrityError

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
            self.stdout.write(self.style.ERROR(
                f"{filename}: Invalid filename format: {filename_ext}. Expected format: <puzzle_type>_<puzzle_size>_<puzzle_difficulty>.json. Skipping file..."))
            return False

        # load file
        data = json.loads(open(file, "r").read())
        if not isinstance(data, list):
            self.stdout.write(
                self.style.ERROR(f"{filename}: The file {file} does not contain a list at the top level."))
            return False

        # check if any of those hashes are in the database
        all_current_hashes = models.Puzzle.objects.values_list('puzzle_hash', flat=True)

        # import the puzzles - use each puzzle's "id" as the hash
        imported_count = 0
        for puzzle in data:
            if "id" not in puzzle:
                self.stdout.write(self.style.WARNING(f"Skipping puzzle without id"))
                continue

            puzzle_hash = puzzle["id"]

            # skip puzzles that already exist in the database
            if puzzle_hash in all_current_hashes:
                continue

            try:
                models.Puzzle.objects.create(
                    puzzle_hash=puzzle_hash,
                    puzzle_type=puzzle_type,
                    puzzle_size=puzzle_size,
                    puzzle_difficulty=puzzle_difficulty,
                    puzzle_data=puzzle,
                )
            except IntegrityError:
                self.stdout.write(self.style.ERROR(f"Failed to import puzzle with id {puzzle_hash}. It may already exist."))
                continue
            imported_count += 1

        self.stdout.write(self.style.SUCCESS(f"Imported {imported_count} puzzles from {filename_ext}"))
        return True
