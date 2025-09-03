"""
Move.py — encapsulates a single chess move.

Responsibilities:
  • Store start/end squares, moving piece, and captured piece
  • Provide hashing/equality so Moves can be used in sets and dicts
  • Generate simple algebraic notation (captures, castling, etc.)
"""

from __future__ import annotations
from typing import Tuple, List


class Move:
    # Lookup tables for algebraic conversion
    rowsToRanks = {0: "8", 1: "7", 2: "6", 3: "5", 4: "4", 5: "3", 6: "2", 7: "1"}
    colsToFiles = {0: "a", 1: "b", 2: "c", 3: "d", 4: "e", 5: "f", 6: "g", 7: "h"}

    def __init__(self, start_Sq: Tuple[int, int], end_Sq: Tuple[int, int], board: List[List[str]]) -> None:
        """
        Args:
            start_Sq: (row, col) of the moving piece
            end_Sq: (row, col) of the destination
            board: current board state for looking up piece identities
        """
        self.start_row = start_Sq[0]
        self.start_col = start_Sq[1]
        self.end_row = end_Sq[0]
        self.end_col = end_Sq[1]
        self.moving_piece = board[self.start_row][self.start_col]
        self.captured_piece = board[self.end_row][self.end_col]

        # Compact unique id (12 bits: 6 for start, 6 for end)
        # Used for hashing and equality
        self.move_identifier = ((self.start_row * 8 + self.start_col) << 6) + (
            self.end_row * 8 + self.end_col
        )

    # --- equality + hashing -------------------------------------------------

    def __eq__(self, other: object) -> bool:
        """Moves are equal if their encoded identifiers match."""
        return isinstance(other, Move) and self.move_identifier == other.move_identifier

    def __hash__(self) -> int:
        return hash(self.move_identifier)

    # --- notation helpers ---------------------------------------------------

    def getAlgebraicNotation(self) -> str:
        """
        Return simple algebraic notation for the move.

        Features:
          • Pawn moves omit the "P"
          • Captures include "x" (file+rank for pawn captures)
          • Castling shown as O-O / O-O-O
          • Does not yet encode check/mate or disambiguation
        """
        moving_piece = self.moving_piece[1].upper() if self.moving_piece != "--" else ""
        piece_captured = self.captured_piece != "--"

        start_position = self.getFileRank(self.start_row, self.start_col)
        end_position = self.getFileRank(self.end_row, self.end_col)

        # Special case: castling
        if self.moving_piece[1] == "K" and abs(self.start_col - self.end_col) == 2:
            return "O-O" if self.end_col == 6 else "O-O-O"

        if piece_captured:
            return f"{moving_piece}x{end_position}" if moving_piece != "P" else f"{start_position[0]}x{end_position}"
        else:
            return f"{moving_piece}{end_position}" if moving_piece != "P" else end_position

    def getFileRank(self, r: int, c: int) -> str:
        """Return algebraic file+rank (e.g. 'e4') for given board coordinates."""
        return f"{self.colsToFiles[c]}{self.rowsToRanks[r]}"
