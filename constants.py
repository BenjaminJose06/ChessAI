# constants.py — global configuration and evaluation tables
#
# Contains:
#   • Defaults for gameplay and UI (overridden by the pre-game menu at runtime)
#   • Global image cache (populated on load)
#   • Piece–square tables for heuristic evaluation
#
# This module should stay free of runtime logic; it only defines constants.

from __future__ import annotations
from typing import Final, Dict, Tuple

# ---------------------------------------------------------------------------
# Game configuration
# ---------------------------------------------------------------------------

DEPTH: Final[int] = 2                 # Default AI search depth (UI can override)
HUMAN_WHITE: Final[bool] = False      # Default: White controlled by AI
HUMAN_BLACK: Final[bool] = False      # Default: Black controlled by AI

# Display defaults
HEIGHT: Final[int] = 800
WIDTH: Final[int] = 800

# Image cache — populated at runtime by main.load_images()
IMAGES: Dict[str, object] = {}

# ---------------------------------------------------------------------------
# Piece–Square Tables
# ---------------------------------------------------------------------------
# Positional bonuses in centipawns.
#
# Each table is indexed [row][col] from White’s perspective.
# For Black, the table is mirrored vertically (handled in ChessAI._piece_sq_value).
#
# Values are approximate midgame heuristics. Material values
# (e.g. pawn = 100, queen = 900) are defined separately in ChessAI.
# ---------------------------------------------------------------------------

POSITION_VALUE_TABLE: Final[Dict[str, Tuple[Tuple[int, ...], ...]]] = {
    "P": (  # Pawn
        (0,   0,  0,  0,  0,  0,  0,  0),
        (50, 50, 50, 50, 50, 50, 50, 50),
        (10, 10, 20, 30, 30, 20, 10, 10),
        (5,   5, 10, 25, 25, 10,  5,  5),
        (0,   0,  0, 30, 30,  0,  0,  0),
        (5,  -5,-10,  0,  0,-10, -5,  5),
        (5,  10, 10,-20,-20, 10, 10,  5),
        (0,   0,  0,  0,  0,  0,  0,  0),
    ),
    "N": (  # Knight
        (-50,-40,-30,-30,-30,-30,-40,-50),
        (-40,-20,  0,  0,  0,  0,-20,-40),
        (-30,  0, 10, 15, 15, 10,  0,-30),
        (-30,  5, 15, 20, 20, 15,  5,-30),
        (-30,  0, 15, 20, 20, 15,  0,-30),
        (-30,  5, 10, 15, 15, 10,  5,-30),
        (-40,-20,  0,  5,  5,  0,-20,-40),
        (-50,-40,-30,-30,-30,-30,-40,-50),
    ),
    "B": (  # Bishop
        (-20,-10,-10,-10,-10,-10,-10,-20),
        (-10,  0,  0,  0,  0,  0,  0,-10),
        (-10,  0,  5, 10, 10,  5,  0,-10),
        (-10,  5,  5, 10, 10,  5,  5,-10),
        (-10,  0, 10, 10, 10, 10,  0,-10),
        (-10, 10, 10, 10, 10, 10, 10,-10),
        (-10,  5,  0,  0,  0,  0,  5,-10),
        (-20,-10,-10,-10,-10,-10,-10,-20),
    ),
    "R": (  # Rook
        (0,  0,  0,  0,  0,  0,  0,  0),
        (5, 10, 10, 10, 10, 10, 10,  5),
        (-5,  0,  0,  0,  0,  0,  0, -5),
        (-5,  0,  0,  0,  0,  0,  0, -5),
        (-5,  0,  0,  0,  0,  0,  0, -5),
        (-5,  0,  0,  0,  0,  0,  0, -5),
        (-5,  0,  0,  0,  0,  0,  0, -5),
        (0,  0,  0,  5,  5,  0,  0,  0),
    ),
    "Q": (  # Queen
        (-20,-10,-10, -5, -5,-10,-10,-20),
        (-10,  0,  0,  0,  0,  0,  0,-10),
        (-10,  0,  5,  5,  5,  5,  0,-10),
        ( -5,  0,  5,  5,  5,  5,  0, -5),
        (  0,  0,  5,  5,  5,  5,  0, -5),
        (-10,  5,  5,  5,  5,  5,  0,-10),
        (-10,  0,  5,  0,  0,  0,  0,-10),
        (-20,-10,-10, -5, -5,-10,-10,-20),
    ),
    "K": (  # King (midgame)
        (-30,-40,-40,-50,-50,-40,-40,-30),
        (-30,-40,-40,-50,-50,-40,-40,-30),
        (-30,-40,-40,-50,-50,-40,-40,-30),
        (-30,-40,-40,-50,-50,-40,-40,-30),
        (-20,-30,-30,-40,-40,-30,-30,-20),
        (-10,-20,-20,-20,-20,-20,-20,-10),
        ( 20, 20,  0,  0,  0,  0, 20, 20),
        ( 20, 30, 10,  0,  0, 10, 30, 20),
    ),
}
