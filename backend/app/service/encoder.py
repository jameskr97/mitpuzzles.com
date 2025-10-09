from typing import List


class PrecisePuzzleEncoder:
    """
    Encoder for your specific 5 puzzle types based on the exact enum mappings
    """

    # Define positive/negative states based on your enums
    PUZZLE_CONFIGS = {
        "tents": {
            "positive_values": [-3],  # TENT only
            "negative_values": [-4],  # GREEN (pertinent negative for strict mode)
            "immutable_values": [1],  # TREE (immutable, ignore in encoding)
            "empty_values": [-1],  # EMPTY
        },
        "kakurasu": {
            "positive_values": [1],  # BLACK (marked cells)
            "negative_values": [0],  # CROSS (pertinent negative for strict mode)
            "immutable_values": [],  # None
            "empty_values": [-1],  # EMPTY
        },
        "sudoku": {
            "positive_values": [1, 2, 3, 4, 5, 6, 7, 8, 9],  # All numbers
            "negative_values": [],  # No pertinent negatives (strict = non-strict)
            "immutable_values": [],  # Given numbers handled same as solution numbers
            "empty_values": [-1],  # EMPTY
        },
        "lightup": {
            "positive_values": [-3],  # BULB only
            "negative_values": [-4],  # EMPTY_LIT (pertinent negative for strict mode)
            "immutable_values": [0, 1, 2, 3, 4, -2],  # All wall types (immutable)
            "empty_values": [-1],  # EMPTY
        },
        "minesweeper": {
            "positive_values": [-3],  # FLAG (mines)
            "negative_values": [-4],  # SAFE (pertinent negative for strict mode)
            "immutable_values": [1, 2, 3, 4, 5, 6, 7, 8],  # Number clues (immutable)
            "empty_values": [0, -1],  # UNMARKED
        },
        "nonograms": {
            "positive_values": [1],  # FILLED (marked cells)
            "negative_values": [0],  # EMPTY (pertinent negative for strict mode)
            "immutable_values": [],  # None
            "empty_values": [-1],  # UNMARKED
        },
        "battleships": {
            "positive_values": [-3],  # SHIP parts
            "negative_values": [-4],  # WATER (pertinent negative for strict mode)
            "immutable_values": [],  # None
            "empty_values": [-1],  # EMPTYs
        },
        "mosaic": {
            "positive_values": [-3],  # SHADED (filled cells)
            "negative_values": [-4],  # CROSS (pertinent negative for strict mode)
            "immutable_values": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],  # Number clues 0-9 (immutable)
            "empty_values": [-1],  # UNMARKED
        },
    }

    def __init__(self, puzzle_type: str):
        self.puzzle_type = puzzle_type
        self.config = self.PUZZLE_CONFIGS[puzzle_type]

    def _is_positive_state(self, cell_value: int) -> bool:
        """Check if cell represents a positive state for this puzzle type."""
        return cell_value in self.config["positive_values"]

    def _is_negative_state(self, cell_value: int) -> bool:
        """Check if cell represents a negative state (strict mode only)."""
        return cell_value in self.config["negative_values"]

    def _is_immutable_state(self, cell_value: int) -> bool:
        """Check if cell is immutable (given clues, walls, trees, etc.)."""
        return cell_value in self.config["immutable_values"]

    def _is_empty_state(self, cell_value: int) -> bool:
        """Check if cell is empty/unmarked."""
        return cell_value in self.config["empty_values"]

    def _get_positive_state_value(self, cell_value: int) -> str:
        """Convert positive state to encoding character."""
        positive_values = self.config["positive_values"]

        if len(positive_values) == 1:
            # Simple binary puzzles (Tents, Kakurasu, Lightup, Minesweeper)
            return "1"
        else:
            # Sudoku - use the actual number
            return str(cell_value)

    def _calculate_gap(self, row1: int, col1: int, row2: int, col2: int, board: List[List[int]]) -> int:
        """
        Calculate gap between positive positions.

        Always counts ALL cells between positions to maintain spatial integrity.
        The difference between modes is in validation, not gap counting.
        """
        cols = len(board[0]) if board else 0
        pos1 = row1 * cols + col1
        pos2 = row2 * cols + col2

        # Count ALL cells between positions (including immutable cells)
        gap_count = pos2 - pos1 - 1

        return gap_count

    def create_run_length_encoding(self, board: List[List[int]]) -> str:
        """
        Create run-length encoding for your specific puzzle types.

        Args:
            board: 2D array with your numeric values
            puzzle_id: Unique puzzle identifier
        """
        encoding_parts = []
        positive_positions = []

        # Find all positive state positions (skip immutable cells)
        for row_idx, row in enumerate(board):
            for col_idx, cell_value in enumerate(row):
                if self._is_positive_state(cell_value):
                    state_char = self._get_positive_state_value(cell_value)
                    positive_positions.append((row_idx, col_idx, state_char))

        if not positive_positions:
            encoding = "0"
        else:
            # Encode leading empty cells before first positive state
            first_row, first_col, _ = positive_positions[0]
            cols = len(board[0]) if board else 0
            leading_gap = first_row * cols + first_col

            if leading_gap > 0:
                if leading_gap <= 26:
                    encoding_parts.append(chr(ord("a") + leading_gap - 1))
                else:
                    encoding_parts.append(f"#{leading_gap}")

            # Build run-length encoding
            for i, (row, col, state_char) in enumerate(positive_positions):
                encoding_parts.append(state_char)

                if i < len(positive_positions) - 1:
                    next_row, next_col, _ = positive_positions[i + 1]
                    gap_count = self._calculate_gap(row, col, next_row, next_col, board)

                    if gap_count > 0:
                        if gap_count <= 26:
                            encoding_parts.append(chr(ord("a") + gap_count - 1))
                        else:
                            encoding_parts.append(f"#{gap_count}")

            encoding = "".join(encoding_parts)

        # Hash with puzzle type and ID
        # hash_input = f"{puzzle_id}:{self.puzzle_type.value}:{encoding}"
        # hash_input = encoding
        # hash = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
        return encoding
        # return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
