import json
import uuid
from typing import Dict, Any, List, Tuple, Optional


class PuzzleNormalizer:
    """
    Complete puzzle normalization and deduplication system.
    """

    def __init__(self):
        # Generate stab˚˚le namespace UUIDs for each puzzle type
        # Define what constitutes the "definition" for each puzzle type
        self.puzzle_definitions = {
            "sudoku": ["initial_state"],
            "kakurasu": ["row_sums", "col_sums"],
            "nonograms": ["row_hints", "col_hints"],
            "tents": ["initial_state", "row_tent_counts", "col_tent_counts"],
            "norinori": ["regions"],
            "battleships": ["row_sums", "col_sums", "ships_dict", "initial_state"],
            "hashi": ["initial_state"],
            "minesweeper": ["initial_state"],
            "lightup": ["initial_state"],
            "mosaic": ["initial_state"],
        }

        self.PUZZLE_NAMESPACE = uuid.UUID("ebf9c570-3a85-4898-b471-e0d4224952fc")
        self.namespaces = {gametype: uuid.uuid5(self.PUZZLE_NAMESPACE, gametype) for gametype in self.puzzle_definitions.keys()}
        self.stats = {"total_processed": 0, "duplicates_found": 0, "errors": 0, "by_type": {}}

    def create_stable_string(self, data: Any) -> str:
        """Create a stable string representation of any data structure."""
        if isinstance(data, dict):
            sorted_dict = {k: self.create_stable_string(v) for k, v in sorted(data.items())}
            return json.dumps(sorted_dict, sort_keys=True, separators=(",", ":"))
        elif isinstance(data, list):
            return json.dumps([self.create_stable_string(item) for item in data], separators=(",", ":"))
        else:
            return json.dumps(data, separators=(",", ":"))

    def extract_puzzle_metadata(self, filename_stem: str) -> Tuple[str, str, Optional[str]]:
        """
        Extract puzzle type, size, and difficulty from filename.
        filename_stem format:
        -   <puzzle_type>_<size>_<difficulty>
        -   <puzzle_type>_<size>
        """
        # get puzzletype based on filename format
        parts = filename_stem.split("_")
        puzzle_type = parts[0].lower()

        # ensure this is a known puzzletype
        if puzzle_type not in self.puzzle_definitions:
            raise ValueError(f"Unknown puzzle type in filename: {filename_stem}")

        size = parts[1].lower()
        difficulty = parts[2].lower() if len(parts) > 2 else None

        return puzzle_type, size, difficulty

    def normalize_puzzle(self, puzzle: Dict[str, Any], filename: str) -> Dict[str, Any]:
        puzzle_type, size, difficulty = self.extract_puzzle_metadata(filename)

        # prepare universal normalized structure
        normalized = {
            "puzzle_type": puzzle_type,
            "initial_state": puzzle["game_state"],
            "difficulty_label": difficulty,
        }

        ##################################################################
        # hashi is special and has a different solution key
        solution_key = "solution_bridges" if puzzle_type == "hashi" else "game_board"
        normalized["solution"] = puzzle[solution_key]

        ##################################################################
        # Handle size/rows/cols normalization
        has_rows_cols = "rows" in puzzle and "cols" in puzzle
        has_size = "size" in puzzle

        if has_rows_cols and has_size:
            if puzzle["rows"] != puzzle["size"] or puzzle["cols"] != puzzle["size"]:
                raise ValueError(f"Inconsistent dimensions in {puzzle_type}: size={puzzle['size']} but rows={puzzle['rows']}, cols={puzzle['cols']}")
            # invariant - they are consistent rows == cols == size
            normalized["rows"] = puzzle["rows"]
            normalized["cols"] = puzzle["cols"]
        elif has_size:
            normalized["rows"] = puzzle["size"]
            normalized["cols"] = puzzle["size"]
        elif has_rows_cols:
            normalized["rows"] = puzzle["rows"]
            normalized["cols"] = puzzle["cols"]

        ##################################################################
        # add puzzle specific fields
        if puzzle_type == "nonograms":
            normalized["row_hints"] = puzzle.get("row_hints")
            normalized["col_hints"] = puzzle.get("col_hints")
            normalized["count_black_cells"] = puzzle.get("n_black_cells")
        elif puzzle_type == "kakurasu":
            normalized["row_sums"] = puzzle.get("row_sums")
            normalized["col_sums"] = puzzle.get("col_sums")
        elif puzzle_type == "tents":
            normalized["row_tent_counts"] = puzzle.get("row_tent_counts")
            normalized["col_tent_counts"] = puzzle.get("col_tent_counts")
            normalized["count_tents"] = puzzle.get("n_tents")
        elif puzzle_type == "battleships":
            normalized["row_sums"] = puzzle.get("row_sums")
            normalized["col_sums"] = puzzle.get("col_sums")
            normalized["ships_dict"] = puzzle.get("ships_dict")
            normalized["num_hints"] = puzzle.get("num_hints")
        elif puzzle_type == "hashi":
            normalized["num_islands"] = puzzle.get("num_islands")
        elif puzzle_type == "lightup":
            normalized["n_lights"] = puzzle.get("n_lights")
        elif puzzle_type == "minesweeper":
            normalized["n_mines"] = puzzle.get("n_mines")
        elif puzzle_type == "norinori":
            normalized["regions"] = puzzle.get("regions")
        return normalized

    def generate_ids(self, normalized_puzzle: Dict[str, Any]) -> Dict[str, str]:
        """Generate three semantic IDs for the puzzle."""
        puzzle_type = normalized_puzzle["puzzle_type"]

        if puzzle_type not in self.puzzle_definitions:
            raise ValueError(f"Unknown puzzle type: {puzzle_type}")

        namespace = self.namespaces[puzzle_type]
        definition_fields = self.puzzle_definitions[puzzle_type]

        # Build definition data
        definition_data = {}
        for field in definition_fields:
            if field in normalized_puzzle:
                definition_data[field] = normalized_puzzle[field]

        # Generate IDs
        definition_id = str(uuid.uuid5(namespace, self.create_stable_string(definition_data)))
        solution_id = str(uuid.uuid5(namespace, self.create_stable_string(normalized_puzzle["solution"])))

        # Complete ID combines definition + solution
        complete_data = {**definition_data, "solution": normalized_puzzle["solution"]}
        complete_id = str(uuid.uuid5(namespace, self.create_stable_string(complete_data)))

        return {"definition_id": definition_id, "solution_id": solution_id, "complete_id": complete_id}

    def process_puzzle(self, puzzle: Dict[str, Any], filename: str, index: int) -> Optional[Dict[str, Any]]:
        """Process a single puzzle: normalize and generate IDs."""
        puzzle_type, size, difficulty = self.extract_puzzle_metadata(filename)
        try:
            if puzzle_type not in self.stats["by_type"]:
                self.stats["by_type"][puzzle_type] = {"processed": 0, "duplicates": 0, "errors": 0}

            normalized = self.normalize_puzzle(puzzle, filename)
            ids = self.generate_ids(normalized)

            # Add IDs to normalized puzzle
            normalized["definition_id"] = ids["definition_id"]
            normalized["solution_id"] = ids["solution_id"]
            normalized["complete_id"] = ids["complete_id"]

            # Add metadata
            # normalized['source_file'] = filename
            # normalized['source_index'] = index

            # Extract size and difficulty for database
            normalized["puzzle_size"] = size
            normalized["puzzle_difficulty"] = difficulty

            self.stats["total_processed"] += 1
            self.stats["by_type"][puzzle_type]["processed"] += 1

            return normalized

        except Exception as e:
            print(f"Error processing {filename}[{index}]: {e}")
            self.stats["errors"] += 1
            if puzzle_type in self.stats["by_type"]:
                self.stats["by_type"][puzzle_type]["errors"] += 1
            return None

    def process_all_puzzles(self, puzzles_dict: Dict[str, List[Dict]]) -> Tuple[List[Dict], List[Dict]]:
        """
        Process all puzzles and return unique puzzles and duplicates.
        """
        unique_puzzles = []
        duplicates = []
        seen_complete_ids = {}

        # print(f"Processing {sum(len(v) for v in puzzles_dict.values())} total puzzles...")

        for filename, puzzle_list in puzzles_dict.items():
            for idx, puzzle in enumerate(puzzle_list):
                normalized = self.process_puzzle(puzzle, filename, idx)

                if normalized:
                    complete_id = normalized["complete_id"]

                    # Check for duplicates
                    if complete_id in seen_complete_ids:
                        duplicates.append({"duplicate": normalized, "original": seen_complete_ids[complete_id]})
                        self.stats["duplicates_found"] += 1
                        puzzle_type = normalized["puzzle_type"]
                        if puzzle_type in self.stats["by_type"]:
                            self.stats["by_type"][puzzle_type]["duplicates"] += 1
                    else:
                        seen_complete_ids[complete_id] = f"{filename}[{idx}]"
                        unique_puzzles.append(normalized)

        # print(f"Processed {self.stats['total_processed']} puzzles")
        # print(f"Found {len(unique_puzzles)} unique puzzles")
        # print(f"Found {len(duplicates)} duplicates")
        # print(f"Encountered {self.stats['errors']} errors")

        return unique_puzzles, duplicates


# normalizer = PuzzleNormalizer()
#
# print("\n" + "="*60)
# print("NORMALIZATION COMPLETE")
# print("="*60)
# print(f"Total processed: {normalizer.stats['total_processed']}")
# print(f"Unique puzzles: {len(unique_puzzles)}")
# print(f"Duplicates found: {len(duplicates)}")
# print(f"Errors: {normalizer.stats['errors']}")
