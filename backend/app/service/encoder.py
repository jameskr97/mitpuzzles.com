from typing import List, Dict, Any, Optional


class ResearchFormatTranslator:
    """
    Translates puzzle data between developer format (enums) and research format (numbers).

    Developer format uses sequential enums (0, 1, 2, 3...)
    Research format uses semantic numbers (-1 for empty, -3 for positive action, -4 for negative action, etc.)
    """

    # Mapping from developer enum values to research format numbers
    # Format: { developer_enum_value: research_number }
    ENUM_TO_RESEARCH = {
        "tents": {
            0: -1,   # EMPTY
            1: 1,    # TREE
            2: -3,   # TENT
            3: -4,   # GREEN
        },
        "kakurasu": {
            0: -1,   # EMPTY
            1: 1,    # BLACK
            2: 0,    # CROSS
        },
        "nonograms": {
            0: -1,   # EMPTY
            1: 1,    # BLACK
            2: 0,    # CROSS
        },
        "battleships": {
            0: -1,   # EMPTY
            1: -4,   # WATER
            2: -3,   # SHIP
        },
        "sudoku": {
            0: -1,   # EMPTY
            1: 1,    # ONE
            2: 2,    # TWO
            3: 3,    # THREE
            4: 4,    # FOUR
            5: 5,    # FIVE
            6: 6,    # SIX
            7: 7,    # SEVEN
            8: 8,    # EIGHT
            9: 9,    # NINE
        },
        "lightup": {
            0: 0,    # WALL_0
            1: 1,    # WALL_1
            2: 2,    # WALL_2
            3: 3,    # WALL_3
            4: 4,    # WALL_4
            5: -2,   # WALL_NO_CONSTRAINT
            6: -1,   # EMPTY
            7: -3,   # BULB
            8: -4,   # CROSS
        },
        "minesweeper": {
            0: -1,   # UNMARKED
            1: 1,    # ONE
            2: 2,    # TWO
            3: 3,    # THREE
            4: 4,    # FOUR
            5: 5,    # FIVE
            6: 6,    # SIX
            7: 7,    # SEVEN
            8: 8,    # EIGHT
            9: -3,   # FLAG
            10: -4,  # SAFE
            11: 0,   # EMPTY (revealed empty)
            12: -5,  # QUESTION_MARK
            13: -1,  # UNMARKED_HIGHLIGHTED (treat as unmarked)
        },
        "mosaic": {
            0: 0,    # ZERO
            1: 1,    # ONE
            2: 2,    # TWO
            3: 3,    # THREE
            4: 4,    # FOUR
            5: 5,    # FIVE
            6: 6,    # SIX
            7: 7,    # SEVEN
            8: 8,    # EIGHT
            9: 9,    # NINE
            10: -1,  # UNMARKED
            11: -3,  # SHADED
            12: -4,  # CROSS
        },
        "norinori": {
            0: -1,   # EMPTY
            1: -3,   # SHADED
            2: -4,   # CROSS
        },
        "aquarium": {
            0: -1,   # EMPTY
            1: -3,   # WATER
            2: -4,   # CROSS
        },
    }

    def __init__(self, puzzle_type: str):
        self.puzzle_type = puzzle_type
        if puzzle_type not in self.ENUM_TO_RESEARCH:
            raise ValueError(f"Unknown puzzle type: {puzzle_type}")
        self.mapping = self.ENUM_TO_RESEARCH[puzzle_type]

    def translate_cell(self, cell_value: int) -> int:
        """Translate a single cell value from developer format to research format."""
        if cell_value in self.mapping:
            return self.mapping[cell_value]
        # If not in mapping, return as-is (might be a clue number or special value)
        return cell_value

    def translate_grid(self, grid: List[List[int]]) -> List[List[int]]:
        """Translate a 2D grid from developer format to research format."""
        if not grid:
            return grid
        return [
            [self.translate_cell(cell) for cell in row]
            for row in grid
        ]

    def translate_action_history(self, action_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Translate action history, converting any board states and values within actions.

        Actions may contain 'state', 'board_state', 'old_value', 'new_value' fields that need translation.
        """
        if not action_history:
            return action_history

        translated = []
        for action in action_history:
            action_copy = action.copy()

            # Translate 'state' field if present and is a grid
            if 'state' in action_copy and isinstance(action_copy['state'], list):
                if action_copy['state'] and isinstance(action_copy['state'][0], list):
                    action_copy['state'] = self.translate_grid(action_copy['state'])

            # Translate 'board_state' field if present and is a grid
            if 'board_state' in action_copy and isinstance(action_copy['board_state'], list):
                if action_copy['board_state'] and isinstance(action_copy['board_state'][0], list):
                    action_copy['board_state'] = self.translate_grid(action_copy['board_state'])

            # Translate 'old_value' and 'new_value' fields if present
            if 'old_value' in action_copy and isinstance(action_copy['old_value'], int):
                action_copy['old_value'] = self.translate_cell(action_copy['old_value'])
            if 'new_value' in action_copy and isinstance(action_copy['new_value'], int):
                action_copy['new_value'] = self.translate_cell(action_copy['new_value'])

            # Translate 'board_before' and 'board_after' in custom_data if present
            if 'custom_data' in action_copy and isinstance(action_copy['custom_data'], dict):
                custom_data = action_copy['custom_data'].copy()
                if 'board_before' in custom_data and isinstance(custom_data['board_before'], list):
                    if custom_data['board_before'] and isinstance(custom_data['board_before'][0], list):
                        custom_data['board_before'] = self.translate_grid(custom_data['board_before'])
                if 'board_after' in custom_data and isinstance(custom_data['board_after'], list):
                    if custom_data['board_after'] and isinstance(custom_data['board_after'][0], list):
                        custom_data['board_after'] = self.translate_grid(custom_data['board_after'])
                action_copy['custom_data'] = custom_data

            translated.append(action_copy)

        return translated

    @classmethod
    def translate_attempt(cls, attempt_data: Dict[str, Any], puzzle_type: str) -> Dict[str, Any]:
        """
        Translate an entire attempt record to research format.

        Args:
            attempt_data: Dictionary containing board_state and action_history
            puzzle_type: The puzzle type for translation

        Returns:
            New dictionary with translated board_state and action_history
        """
        try:
            translator = cls(puzzle_type)
        except ValueError:
            # Unknown puzzle type, return as-is
            return attempt_data

        result = attempt_data.copy()

        # Translate board_state
        if 'board_state' in result and isinstance(result['board_state'], list):
            if result['board_state'] and isinstance(result['board_state'][0], list):
                result['board_state'] = translator.translate_grid(result['board_state'])

        # Translate action_history
        if 'action_history' in result and isinstance(result['action_history'], list):
            result['action_history'] = translator.translate_action_history(result['action_history'])

        return result


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
        "hashi": {
            # Hashi uses bridge-based encoding, not cell-based
            # This config is a placeholder - actual encoding is handled specially
            "positive_values": [],
            "negative_values": [],
            "immutable_values": [],
            "empty_values": [],
            "bridge_based": True,  # Flag for special handling
        },
        "norinori": {
            "positive_values": [-3],  # SHADED (filled cells forming dominoes)
            "negative_values": [-4],  # CROSS (pertinent negative for strict mode)
            "immutable_values": [],  # None
            "empty_values": [-1],  # EMPTY
        },
        "aquarium": {
            "positive_values": [-3],  # WATER (filled cells)
            "negative_values": [-4],  # CROSS (pertinent negative for strict mode)
            "immutable_values": [],  # None
            "empty_values": [-1],  # EMPTY
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
        # Special handling for Hashi (bridge-based puzzles)
        if self.config.get("bridge_based"):
            return self._create_hashi_encoding(board)

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

    def _create_hashi_encoding(self, bridges_or_board) -> str:
        """
        Create encoding for Hashi puzzles.

        Hashi solutions are bridge-based, not cell-based.
        The solution is a list of bridges, each with:
        - island1: [row, col]
        - island2: [row, col]
        - count: 1 or 2

        We encode bridges in a deterministic order:
        sorted by (min_row, min_col, max_row, max_col)
        Then each bridge as: r1c1r2c2n where n is the count
        """
        # Handle case where bridges_or_board might be a list of bridge dicts
        if isinstance(bridges_or_board, list) and len(bridges_or_board) > 0:
            # Check if it's a list of bridges (dicts with island1, island2, count)
            if isinstance(bridges_or_board[0], dict) and "island1" in bridges_or_board[0]:
                bridges = bridges_or_board
            else:
                # It's a 2D grid - Hashi might store solution differently
                # Return empty encoding as we can't process this format
                return "0"
        else:
            return "0"

        if not bridges:
            return "0"

        # Normalize each bridge so island1 < island2 (lexicographic on [row, col])
        normalized = []
        for b in bridges:
            i1, i2, count = b["island1"], b["island2"], b["count"]
            if (i1[0], i1[1]) > (i2[0], i2[1]):
                i1, i2 = i2, i1
            normalized.append((i1[0], i1[1], i2[0], i2[1], count))

        # Sort for deterministic order
        normalized.sort()

        # Encode as string: each bridge is "r1,c1-r2,c2:n"
        parts = [f"{r1},{c1}-{r2},{c2}:{n}" for r1, c1, r2, c2, n in normalized]
        return ";".join(parts)
