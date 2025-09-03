"""
board.py — Game state and move generation

Responsibilities:
  • Hold the 8×8 board array and king locations
  • Apply/undo moves (incl. basic castling + promotion)
  • Generate pseudo-legal moves per piece, then filter to legal moves
  • Detect check for the side to move

"""

from typing import List, Set, Tuple

from Move import Move


class Board:
    """Mutable chess position: pieces, side to move, history, and helpers."""

    def __init__(self) -> None:
        # 8x8 board; strings like "wP", "bK", or "--" for empty.
        self.board: List[List[str]] = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bP", "bP", "bP", "bP", "bP", "bP", "bP", "bP"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wP", "wP", "wP", "wP", "wP", "wP", "wP", "wP"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"],
        ]
        self.wK_position: Tuple[int, int] = (7, 4)
        self.bK_position: Tuple[int, int] = (0, 4)
        self.whiteMove: bool = True
        self.moveRecord: List[Move] = []
        self.promotion_choices = ["Q", "R", "N", "B"]

    # --- core state mutation -------------------------------------------------

    def doMove(self, move: Move, simulate: bool) -> None:
        """
        Apply a move to the board.

        Args:
            move: Move to apply.
            simulate: If True, skip user UI and assume automatic promotion to queen.

        Side effects:
            • Updates board array
            • Handles rook movement for castling
            • Triggers promotion (lazy-imports main for UI if not simulate)
            • Flips side to move and updates king locations
            • Appends move to history
        """
        # Move piece
        self.board[move.start_row][move.start_col] = "--"
        self.board[move.end_row][move.end_col] = move.moving_piece

        # Castling: slide rook after king moves two files
        if move.moving_piece[1] == "K" and abs(move.start_col - move.end_col) == 2:
            if move.end_col == 6:  # king-side
                self.board[move.end_row][5] = self.board[move.end_row][7]
                self.board[move.end_row][7] = "--"
            elif move.end_col == 2:  # queen-side
                self.board[move.end_row][3] = self.board[move.end_row][0]
                self.board[move.end_row][0] = "--"

        # Promotion
        if (move.moving_piece == "wP" and move.end_row == 0) or (
            move.moving_piece == "bP" and move.end_row == 7
        ):
            if simulate:
                self.promote(move.end_row, move.end_col, move.moving_piece[0] + "Q")
            else:
                # Lazy import avoids circular dependency with main.py
                try:
                    from main import main as _main  # type: ignore
                    choice = _main.pawn_promotion_menu()
                except Exception:
                    choice = "Q"
                self.promote(move.end_row, move.end_col, move.moving_piece[0] + (choice or "Q"))

        # Switch side to move + track king positions
        self.whiteMove = not self.whiteMove
        if move.moving_piece == "wK":
            self.wK_position = (move.end_row, move.end_col)
        elif move.moving_piece == "bK":
            self.bK_position = (move.end_row, move.end_col)

        self.moveRecord.append(move)

    def promote(self, row: int, col: int, piece: str) -> None:
        """Replace a pawn on the last rank with the chosen piece (e.g. 'wQ')."""
        if self.board[row][col] == "wP" and row == 0:
            self.board[row][col] = piece
        elif self.board[row][col] == "bP" and row == 7:
            self.board[row][col] = piece

    def undo(self) -> None:
        """
        Revert the last move (including rook movement for castling)
        and restore side to move + king positions.
        """
        if not self.moveRecord:
            return
        move = self.moveRecord.pop()
        self.board[move.start_row][move.start_col] = move.moving_piece
        self.board[move.end_row][move.end_col] = move.captured_piece

        # Undo castling rook slide
        if move.moving_piece[1] == "K" and abs(move.start_col - move.end_col) == 2:
            if move.end_col == 6:  # king-side
                self.board[move.end_row][7] = self.board[move.end_row][5]
                self.board[move.end_row][5] = "--"
            else:  # queen-side
                self.board[move.end_row][0] = self.board[move.end_row][3]
                self.board[move.end_row][3] = "--"

        self.whiteMove = not self.whiteMove
        if move.moving_piece == "wK":
            self.wK_position = (move.start_row, move.start_col)
        elif move.moving_piece == "bK":
            self.bK_position = (move.start_row, move.start_col)

    # --- legality ------------------------------------------------------------

    def is_check(self) -> bool:
        """
        Return True if the current side to move is in check.

        Implementation detail:
            Temporarily flip side-to-move to generate opponent moves and
            see if any land on our king square.
        """
        king_loc = self.wK_position if self.whiteMove else self.bK_position
        self.whiteMove = not self.whiteMove
        opponent_moves = self.getPossibleMoves()
        self.whiteMove = not self.whiteMove
        return any(m.end_row == king_loc[0] and m.end_col == king_loc[1] for m in opponent_moves)

    def getValidMoves(self) -> Set[Move]:
        """
        Generate fully legal moves by:
          1) generating pseudo-legal moves,
          2) simulating each and discarding those that leave our king in check.
        """
        valid: Set[Move] = set()
        for move in self.getPossibleMoves():
            self.doMove(move, True)
            self.whiteMove = not self.whiteMove
            if not self.is_check():
                valid.add(move)
            self.whiteMove = not self.whiteMove
            self.undo()
        return valid

    # --- move generation -----------------------------------------------------

    def getPossibleMoves(self) -> Set[Move]:
        """
        Generate pseudo-legal moves for the side to move.
        Legality w.r.t. own-king-in-check is enforced later in getValidMoves().
        """
        moves: Set[Move] = set()
        for r in range(8):
            for c in range(8):
                colour = self.board[r][c][0]
                # Skip empties / opponent pieces
                if colour == "-" or (
                    (colour == "w" and not self.whiteMove) or (colour == "b" and self.whiteMove)
                ):
                    continue
                piece = self.board[r][c][1]
                if piece == "P":
                    self.getPawnMoves(r, c, moves)
                elif piece == "R":
                    self.getRookMoves(r, c, moves)
                elif piece == "N":
                    self.getKnightMoves(r, c, moves)
                elif piece == "B":
                    self.getBishopMoves(r, c, moves)
                elif piece == "Q":
                    self.getQueenMoves(r, c, moves)
                elif piece == "K":
                    self.getKingMoves(r, c, moves)
        return moves

    def getPawnMoves(self, row: int, col: int, moves: Set[Move]) -> None:
        """Add pawn pushes and captures (no en passant)."""
        colour = self.board[row][col][0]
        d = -1 if colour == "w" else 1
        nr = row + d

        # Single push
        if 0 <= nr < 8 and self.board[nr][col] == "--":
            moves.add(Move((row, col), (nr, col), self.board))

            # Double push from start rank
            nr2 = row + 2 * d
            if (colour == "w" and row == 6) or (colour == "b" and row == 1):
                if 0 <= nr2 < 8 and self.board[nr2][col] == "--":
                    moves.add(Move((row, col), (nr2, col), self.board))

        # Diagonal captures
        for dc in (-1, 1):
            nc = col + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                dest = self.board[nr][nc]
                if dest != "--" and dest[0] != colour:
                    moves.add(Move((row, col), (nr, nc), self.board))

    def getRookMoves(self, row: int, col: int, moves: Set[Move]) -> None:
        """Add rook sliding moves along ranks/files until blocked."""
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            r, c = row + dr, col + dc
            while 0 <= r < 8 and 0 <= c < 8:
                dest = self.board[r][c]
                if dest == "--":
                    moves.add(Move((row, col), (r, c), self.board))
                else:
                    if dest[0] != self.board[row][col][0]:
                        moves.add(Move((row, col), (r, c), self.board))
                    break
                r += dr
                c += dc

    def getKnightMoves(self, row: int, col: int, moves: Set[Move]) -> None:
        """Add knight L-moves, skipping own pieces."""
        for dr, dc in ((2, 1), (1, 2), (-1, 2), (-2, -1), (-2, 1), (-1, -2), (1, -2), (2, -1)):
            r, c = row + dr, col + dc
            if 0 <= r < 8 and 0 <= c < 8:
                dest = self.board[r][c]
                if dest[0] != self.board[row][col][0]:
                    moves.add(Move((row, col), (r, c), self.board))

    def getBishopMoves(self, row: int, col: int, moves: Set[Move]) -> None:
        """Add bishop diagonal moves until blocked."""
        for dr, dc in ((-1, 1), (-1, -1), (1, -1), (1, 1)):
            r, c = row + dr, col + dc
            while 0 <= r < 8 and 0 <= c < 8:
                dest = self.board[r][c]
                if dest == "--":
                    moves.add(Move((row, col), (r, c), self.board))
                else:
                    if dest[0] != self.board[row][col][0]:
                        moves.add(Move((row, col), (r, c), self.board))
                    break
                r += dr
                c += dc

    def getQueenMoves(self, row: int, col: int, moves: Set[Move]) -> None:
        """Queen = bishop moves + rook moves."""
        self.getBishopMoves(row, col, moves)
        self.getRookMoves(row, col, moves)

    def getKingMoves(self, row: int, col: int, moves: Set[Move]) -> None:
        """Add king one-step moves + basic castling targets (see notes above)."""
        for dr, dc in ((1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)):
            r, c = row + dr, col + dc
            if 0 <= r < 8 and 0 <= c < 8:
                dest = self.board[r][c]
                if dest == "--" or dest[0] != self.board[row][col][0]:
                    moves.add(Move((row, col), (r, c), self.board))

        # Castling squares are added here; attack checks are validated
        # later when filtering legal moves.
        if self.canCastleKingside(row, col):
            moves.add(Move((row, col), (row, col + 2), self.board))
        if self.canCastleQueenside(row, col):
            moves.add(Move((row, col), (row, col - 2), self.board))

    # --- castling helpers (basic) -------------------------------------------

    def canCastleKingside(self, row: int, col: int) -> bool:
        """Basic king-side castling precheck: squares empty and rook present."""
        if self.whiteMove:
            return (
                row == 7 and col == 4 and
                self.board[7][5] == "--" and self.board[7][6] == "--" and
                self.board[7][7] == "wR"
            )
        else:
            return (
                row == 0 and col == 4 and
                self.board[0][5] == "--" and self.board[0][6] == "--" and
                self.board[0][7] == "bR"
            )

    def canCastleQueenside(self, row: int, col: int) -> bool:
        """Basic queen-side castling precheck: squares empty and rook present."""
        if self.whiteMove:
            return (
                row == 7 and col == 4 and
                self.board[7][1] == "--" and self.board[7][2] == "--" and self.board[7][3] == "--" and
                self.board[7][0] == "wR"
            )
        else:
            return (
                row == 0 and col == 4 and
                self.board[0][1] == "--" and self.board[0][2] == "--" and self.board[0][3] == "--" and
                self.board[0][0] == "bR"
            )
