"""
ChessAI.py — evaluation and alpha–beta search (engine-only; no UI)

Responsibilities:
  • Evaluate a position with material + piece–square tables
  • Alpha–beta minimax with mate/stalemate terminal handling
  • Root move selection helper
  .
"""

from __future__ import annotations
import random
from typing import Set

from board import Board, Move
from constants import POSITION_VALUE_TABLE


def findRandomMove(validMoves: Set[Move]) -> Move:
    """Return a random legal move (useful for smoke tests/baselines)."""
    return random.sample(validMoves, 1)[0]


def evaluate_board(board: Board) -> int:
    """
    Static evaluation: material + piece–square bonuses.
    Returns centipawns relative to White (positive favors White).
    """
    total = 0
    for row in range(8):
        for col in range(8):
            piece = board.board[row][col]
            if piece == "--":
                continue
            pv = _piece_value(piece)
            pst = _piece_sq_value(piece, row, col)
            total += (pv + pst) if piece[0] == "w" else -(pv + pst)
    return total


def _piece_value(piece: str) -> int:
    """Base material values (centipawns)."""
    values = {"P": 100, "N": 320, "B": 330, "R": 600, "Q": 900, "K": 20000}
    return values.get(piece[1], 0)


def _piece_sq_value(piece: str, row: int, col: int) -> int:
    """Look up piece–square bonus and mirror vertically for Black pieces."""
    table = POSITION_VALUE_TABLE[piece[1]]
    return table[row][col] if piece[0] == "w" else table[7 - row][col]


def minimax(board: Board, depth: int, alpha: float, beta: float, maximising_player: bool) -> float:
    """
    Alpha–beta minimax. Returns a score from White’s perspective.

    Args:
        board: current position (mutated during search; undone after)
        depth: remaining ply to search
        alpha: best score guaranteed for the maximizing player so far
        beta: best score guaranteed for the minimizing player so far
        maximising_player: True if the side to move tries to maximize score

    Implementation:
        • Depth-0 returns static eval (no move generation at leaves).
        • If no legal moves: return ±∞ for mate, 0 for stalemate.
    """
    # Leaf: static eval only (fast path; avoids unnecessary move-gen).
    if depth == 0:
        return float(evaluate_board(board))

    # Generate legal moves for terminal detection and child expansion.
    valid_moves = board.getValidMoves()

    # Terminal node: checkmate or stalemate for side-to-move.
    if not valid_moves:
        if board.is_check():
            # Side-to-move is mated: bad for the mover.
            return float("-inf") if maximising_player else float("inf")
        return 0.0  # stalemate

    if maximising_player:
        best = float("-inf")
        for move in valid_moves:
            board.doMove(move, True)
            score = minimax(board, depth - 1, alpha, beta, False)
            board.undo()
            if score > best:
                best = score
            if best >= beta:  # beta cut-off
                return best
            if best > alpha:
                alpha = best
        return best
    else:
        best = float("inf")
        for move in valid_moves:
            board.doMove(move, True)
            score = minimax(board, depth - 1, alpha, beta, True)
            board.undo()
            if score < best:
                best = score
            if best <= alpha:  # alpha cut-off
                return best
            if best < beta:
                beta = best
        return best


def find_best_move(board: Board, depth: int, valid_moves: Set[Move], team: str) -> Move | None:
    """
    Root selection for the given side.

    Args:
        board: current position (mutated and undone per candidate)
        depth: search depth in plies
        valid_moves: set of legal root moves to consider
        team: "white" or "black" — which side the AI controls

    Returns:
        The best Move found, or None if there are no legal moves.
    """
    # Keep your original repetition guard (cheap heuristic). Optional to remove.
    unique_moves = [m for m in valid_moves if board.moveRecord.count(m) < 3]
    moves = unique_moves or list(valid_moves)
    if not moves:
        return None

    best_move: Move | None = None

    if team == "white":
        best_score = float("-inf")
        for move in moves:
            board.doMove(move, True)
            # After White moves, it's Black's turn → minimizing node
            score = minimax(board, depth - 1, float("-inf"), float("inf"), False)
            board.undo()
            if score >= best_score:
                best_score = score
                best_move = move
    else:
        best_score = float("inf")
        for move in moves:
            board.doMove(move, True)
            # After Black moves, it's White's turn → maximizing node
            score = minimax(board, depth - 1, float("-inf"), float("inf"), True)
            board.undo()
            if score <= best_score:
                best_score = score
                best_move = move

    return best_move
