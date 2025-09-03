"""
main.py — Game loop, UI, and rendering for ChessAI

Responsibilities:
  • Rendering of the board, pieces, and overlays (PyGame)
  • Pre-game configuration menu (choose human/AI sides, depth)
  • Event handling (mouse, resize, undo)
  • Main game loop: alternates human/AI turns, plays sounds, checks game state
"""

from typing import List, Optional
import pygame as p

import ChessAI
from constants import *
from board import Board, Move


# ============================================================================
# Rendering helpers
# ============================================================================

def highlight_square(screen: p.Surface, row: int, col: int,
                     sq_width: float, sq_height: float, color: Tuple[int, int, int]) -> None:
    """Draw a border highlight around a given square."""
    x = int(col * sq_width)
    y = int(row * sq_height)
    p.draw.rect(screen, color, p.Rect(x, y, sq_width, sq_height), 5)


def draw_game_over_message(screen: p.Surface, message: str) -> None:
    """Render and display a centered game-over message (e.g. checkmate)."""
    width, height = screen.get_width(), screen.get_height()
    font = p.font.Font(None, 50)
    text = font.render(message, True, (255, 0, 0))
    rect = text.get_rect(center=(width // 2, height // 2))
    screen.blit(text, rect)


def draw_board(screen: p.Surface, sq_width: float, sq_height: float,
               colour1: str, colour2: str) -> None:
    """Draw the 8×8 board background."""
    for row in range(8):
        for col in range(8):
            colour = colour1 if (row + col) % 2 == 0 else colour2
            rect = (col * sq_width, row * sq_height, sq_width, sq_height)
            p.draw.rect(screen, colour, rect)


def load_images(sq_width: float, sq_height: float) -> None:
    """Load and cache scaled piece images into IMAGES."""
    pieces = ["bR", "bB", "bN", "bQ", "bK", "bP",
              "wR", "wB", "wN", "wQ", "wK", "wP"]
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(
            p.transform.smoothscale(
                p.image.load("images/" + piece + ".png"),
                (sq_width, sq_height)),
            (sq_width, sq_height),
        )


def draw_pieces(screen: p.Surface, board: List[List[str]],
                sq_width: float, sq_height: float) -> None:
    """Draw all pieces on the board based on current state array."""
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece != "--":
                screen.blit(IMAGES[piece],
                            p.Rect((col * sq_width, row * sq_height),
                                   (sq_width, sq_height)))


def draw_labels(screen: p.Surface, sq_width: float, sq_height: float) -> None:
    """Draw rank/file labels (1–8, a–h) along the board edges."""
    font = p.font.Font(None, 30)
    width, height = screen.get_size()
    for row in range(8):
        label = font.render(str(8 - row), True, (0, 0, 0))
        screen.blit(label, (0, row * sq_height + sq_height / 10))
    for col in range(8):
        label = font.render(chr(ord("a") + col), True, (0, 0, 0))
        label_x = col * sq_width + (width - 8 * sq_width) / 2 + sq_width / 1.2
        screen.blit(label, (label_x, height - (sq_height / 1.5) + 50))


def design(screen: p.Surface, sq_width: float, sq_height: float) -> None:
    """Draw a semi-transparent design overlay on the board."""
    image = p.transform.scale(p.image.load("images/design.png"),
                              (int(sq_width * 8), int(sq_height * 8)))
    image.set_alpha(20)
    screen.blit(image, (0, 0))


def methods(screen: p.Surface, board: Board,
            sq_width: float, sq_height: float,
            colour1: str, colour2: str) -> None:
    """Redraw full board state (board, pieces, labels, design)."""
    draw_board(screen, sq_width, sq_height, colour1, colour2)
    load_images(sq_width, sq_height)
    draw_pieces(screen, board.board, sq_width, sq_height)
    draw_labels(screen, sq_width, sq_height)
    design(screen, sq_width, sq_height)


# ============================================================================
# Simple UI widgets (menu buttons + number pickers)
# ============================================================================

class Button:
    """Clickable rectangular button with hover feedback."""

    def __init__(self, rect: p.Rect, label: str):
        self.rect = rect
        self.label = label
        self.hover = False

    def draw(self, screen: p.Surface, font: p.font.Font) -> None:
        base = (90, 90, 90) if not self.hover else (130, 130, 130)
        p.draw.rect(screen, base, self.rect, border_radius=8)
        p.draw.rect(screen, (230, 230, 230), self.rect, 2, border_radius=8)
        text = font.render(self.label, True, (255, 255, 255))
        screen.blit(text, text.get_rect(center=self.rect.center))

    def update_hover(self, mouse: Tuple[int, int]) -> None:
        self.hover = self.rect.collidepoint(mouse)

    def clicked(self, event: p.event.Event) -> bool:
        return event.type == p.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos)


class NumberPicker:
    """UI widget for selecting an integer value via +/- controls."""

    def __init__(self, rect: p.Rect, label: str,
                 value: int, min_v: int = 1, max_v: int = 4):
        self.rect = rect
        self.label = label
        self.value = value
        self.min_v = min_v
        self.max_v = max_v
        # sub-rects for decrement and increment controls
        w = rect.width
        h = rect.height
        self.dec_rect = p.Rect(rect.x, rect.y, h, h)
        self.inc_rect = p.Rect(rect.x + w - h, rect.y, h, h)

    def draw(self, screen: p.Surface, font: p.font.Font) -> None:
        lbl = font.render(f"{self.label}", True, (0, 0, 0))
        screen.blit(lbl, (self.rect.x, self.rect.y - 28))

        p.draw.rect(screen, (240, 240, 240), self.rect, border_radius=8)
        p.draw.rect(screen, (80, 80, 80), self.rect, 2, border_radius=8)

        vfont = p.font.Font(None, 40)
        vtxt = vfont.render(str(self.value), True, (20, 20, 20))
        screen.blit(vtxt, vtxt.get_rect(center=self.rect.center))

        # draw +/- controls
        p.draw.rect(screen, (200, 200, 200), self.dec_rect, border_radius=6)
        p.draw.rect(screen, (200, 200, 200), self.inc_rect, border_radius=6)
        screen.blit(vfont.render("-", True, (40, 40, 40)),
                    vfont.render("-", True, (40, 40, 40)).get_rect(center=self.dec_rect.center))
        screen.blit(vfont.render("+", True, (40, 40, 40)),
                    vfont.render("+", True, (40, 40, 40)).get_rect(center=self.inc_rect.center))

    def handle(self, event: p.event.Event) -> None:
        """Adjust value if +/- clicked."""
        if event.type == p.MOUSEBUTTONDOWN:
            if self.dec_rect.collidepoint(event.pos) and self.value > self.min_v:
                self.value -= 1
            if self.inc_rect.collidepoint(event.pos) and self.value < self.max_v:
                self.value += 1

# ===== main application =====================================================

class Main:
    """Top-level application: window/init, config, sounds, and the main loop."""

    def __init__(self) -> None:
        """Initialize window, sounds, and default (pre-menu) config."""
        p.init()
        p.display.set_caption("Chess")
        self.screen = p.display.set_mode((WIDTH, HEIGHT), p.RESIZABLE)
        p.display.set_icon(p.image.load("images/Icon-chess.png"))

        # Runtime flags / counters
        self.game_over = False
        self.count = 0  # simple AI-move counter (debug/telemetry)

        # Audio cues
        self.move_sound = p.mixer.Sound("sound/move.wav")
        self.capture = p.mixer.Sound("sound/capture.wav")
        self.check = p.mixer.Sound("sound/check.wav")

        # Config defaults (overridden by pregame_menu)
        self.human_white: bool = HUMAN_WHITE
        self.human_black: bool = HUMAN_BLACK
        self.depth_white: int = DEPTH
        self.depth_black: int = DEPTH

    def pregame_menu(self) -> None:
        """
        Modal setup screen.
        Lets the user pick:
          • Mode: Human vs Human / Human (White) vs AI / Human (Black) vs AI / AI vs AI
          • Search depth for each AI side (independent, capped at 4)
        """
        screen = self.screen
        clock = p.time.Clock()
        font_title = p.font.Font(None, 64)
        font = p.font.Font(None, 36)

        width, height = screen.get_width(), screen.get_height()

        # Layout metrics
        btn_w, btn_h = 320, 60
        gap = 16
        cx = width // 2
        y0 = height // 5

        # Mode buttons + start
        buttons = {
            "hvh": Button(p.Rect(cx - btn_w // 2, y0, btn_w, btn_h), "Human vs Human"),
            "hvai_w": Button(p.Rect(cx - btn_w // 2, y0 + (btn_h + gap), btn_w, btn_h), "Human (White) vs AI"),
            "hvai_b": Button(p.Rect(cx - btn_w // 2, y0 + 2 * (btn_h + gap), btn_w, btn_h), "Human (Black) vs AI"),
            "aivai": Button(p.Rect(cx - btn_w // 2, y0 + 3 * (btn_h + gap), btn_w, btn_h), "AI vs AI"),
            "start": Button(p.Rect(cx - btn_w // 2, y0 + 5 * (btn_h + gap), btn_w, btn_h), "Start Game"),
        }

        # Depth selectors (shown only for AI-controlled sides), capped at 4
        picker_w = NumberPicker(
            p.Rect(cx - 320, y0 + 5 * (btn_h + gap), 140, 50),
            "White AI Depth", max(1, DEPTH), min_v=1, max_v=4
        )
        picker_b = NumberPicker(
            p.Rect(cx + 180, y0 + 5 * (btn_h + gap), 140, 50),
            "Black AI Depth", max(1, DEPTH), min_v=1, max_v=4
        )

        # Default selection: Human (White) vs AI
        mode = "hvai_w"
        self.human_white, self.human_black = True, False
        self.depth_white, self.depth_black = max(1, DEPTH), max(1, DEPTH)

        running = True
        while running:
            # --- draw ---
            screen.fill((250, 248, 240))
            title = font_title.render("Chess — Game Setup", True, (30, 30, 30))
            screen.blit(title, title.get_rect(center=(cx, y0 - 70)))

            # Hover feedback
            mouse = p.mouse.get_pos()
            for b in buttons.values():
                b.update_hover(mouse)

            # Buttons (highlight current mode)
            for key, b in buttons.items():
                if key == mode:
                    p.draw.rect(screen, (70, 140, 70), b.rect.inflate(8, 8), border_radius=10)
                b.draw(screen, font)

            # Only show depth pickers for AI sides
            show_white_depth = (mode in ("aivai", "hvai_b"))
            show_black_depth = (mode in ("aivai", "hvai_w"))

            if show_white_depth:
                picker_w.draw(screen, font)
            if show_black_depth:
                picker_b.draw(screen, font)

            # Warning if any side is set to depth 4
            if (show_white_depth and picker_w.value == 4) or (show_black_depth and picker_b.value == 4):
                warn_font = p.font.Font(None, 28)
                warn = warn_font.render("Depth 4 may run slowly on your machine", True, (200, 50, 50))
                # place warning a bit below the pickers
                warn_y = y0 + 6 * (btn_h + gap) + 40
                screen.blit(warn, warn.get_rect(center=(cx, warn_y)))

            p.display.update()
            clock.tick(60)

            # --- events ---
            for event in p.event.get():
                if event.type == p.QUIT:
                    p.quit()
                    raise SystemExit

                if event.type == p.MOUSEBUTTONDOWN:
                    if buttons["hvh"].clicked(event):
                        mode = "hvh"
                        self.human_white, self.human_black = True, True
                    elif buttons["hvai_w"].clicked(event):
                        mode = "hvai_w"
                        self.human_white, self.human_black = True, False
                    elif buttons["hvai_b"].clicked(event):
                        mode = "hvai_b"
                        self.human_white, self.human_black = False, True
                    elif buttons["aivai"].clicked(event):
                        mode = "aivai"
                        self.human_white, self.human_black = False, False
                    elif buttons["start"].clicked(event):
                        running = False  # exit menu

                # Let pickers adjust values when visible
                if show_white_depth:
                    picker_w.handle(event)
                if show_black_depth:
                    picker_b.handle(event)

            # Persist latest picker values
            self.depth_white = picker_w.value
            self.depth_black = picker_b.value

    # ---------- mouse handling ----------------------------------------------

    def handle_mouse_click(
        self,
        screen: p.Surface,
        coordinates: Tuple[int, int],
        sq_width: float,
        sq_height: float,
        sq_selected: Tuple[int, int] | tuple,
        selected_positions: List[Tuple[int, int]],
        board: Board,
        valid_moves: set,
        move_done: bool,
        colour1: str,
        colour2: str,
    ) -> Tuple[Tuple[int, int] | tuple, List[Tuple[int, int]], bool]:
        """
        Handle the two-click move selection pattern for a human:
          1) first click selects a piece (highlight)
          2) second click attempts a move to the target square
        Plays SFX, refreshes display, and returns updated selection state.
        """
        col = int(coordinates[0] // sq_width)
        row = int(coordinates[1] // sq_height)

        # Toggle selection
        if sq_selected == (row, col):
            sq_selected = ()
            selected_positions = []
        else:
            sq_selected = (row, col)
            selected_positions.append(sq_selected)

        # First click: only highlight own piece for the side-to-move
        if len(selected_positions) == 1 and (
            (board.board[row][col][0] == "w" and board.whiteMove)
            or (board.board[row][col][0] == "b" and not board.whiteMove)
        ):
            highlight_square(screen, row, col, sq_width, sq_height, (0, 255, 0))

        # Second click: attempt to make the move
        if len(selected_positions) == 2:
            start = selected_positions[0]
            end = selected_positions[1]

            if board.board[start[0]][start[1]] == "--":
                # clicked an empty square first — reset selection
                sq_selected = ()
                selected_positions = []
            else:
                move = Move(start, end, board.board)
                print(move.getAlgebraicNotation())

                if move in valid_moves:
                    # Decide SFX before mutating board
                    if board.board[move.end_row][move.end_col] == "--":
                        self.move_sound.play()
                    else:
                        self.capture.play()

                    board.doMove(move, False)
                    move_done = True

                # Always redraw after an attempted move
                methods(screen, board, sq_width, sq_height, colour1, colour2)

                if move_done:
                    # Visualize last move (from/to) + check warning
                    highlight_square(screen, start[0], start[1], sq_width, sq_height, (0, 255, 0))
                    highlight_square(screen, end[0], end[1], sq_width, sq_height, (0, 125, 0))

                    if board.is_check():
                        self.check.play()
                        king_pos = board.wK_position if board.whiteMove else board.bK_position
                        highlight_square(screen, king_pos[0], king_pos[1], sq_width, sq_height, (255, 0, 0))

                # Clear selection for next action
                sq_selected = ()
                selected_positions = []

        return sq_selected, selected_positions, move_done

    # ---------- main game loop ----------------------------------------------

    def main(self) -> None:
        """
        Initialize board + rendering, run pregame menu, then loop:
          • Human turn → process clicks and try a move
          • AI turn → compute best move (depth per side), apply + animate
          • After each move → recompute legal moves, detect end states
        """
        sq_width = WIDTH / 8
        sq_height = HEIGHT / 8
        colour1 = "#E7DDD2"
        colour2 = "#D88D2B"

        # Let the user pick sides/depths before we start
        self.pregame_menu()

        board = Board()
        screen = self.screen
        clock = p.time.Clock()

        # Per-turn UI selection state
        sq_selected: Tuple[int, int] | tuple = ()
        selected_positions: List[Tuple[int, int]] = []

        # Start position legal moves
        valid_moves = board.getValidMoves()
        move_done = False
        running = True

        # Initial render
        methods(screen, board, sq_width, sq_height, colour1, colour2)

        while running:
            # Whose turn is controlled by a human?
            human_turn = (board.whiteMove and self.human_white) or (not board.whiteMove and self.human_black)

            # --- events ---
            for event in p.event.get():
                if event.type == p.QUIT:
                    running = False

                elif event.type == p.KEYDOWN and event.key == p.K_u:
                    # Undo last move and re-render
                    board.undo()
                    move_done = True
                    methods(screen, board, sq_width, sq_height, colour1, colour2)

                elif event.type == p.MOUSEBUTTONDOWN and not self.game_over and human_turn:
                    # Human attempts a move via click-click selection
                    sq_selected, selected_positions, move_done = self.handle_mouse_click(
                        screen,
                        p.mouse.get_pos(),
                        sq_width,
                        sq_height,
                        sq_selected,
                        selected_positions,
                        board,
                        valid_moves,
                        move_done,
                        colour1,
                        colour2,
                    )

                elif event.type == p.VIDEORESIZE:
                    # Resize-aware rendering
                    screen = p.display.set_mode((event.w, event.h), p.RESIZABLE)
                    sq_width, sq_height = event.w / 8, event.h / 8
                    methods(screen, board, sq_width, sq_height, colour1, colour2)

            # --- AI turn ---
            if not self.game_over and not human_turn:
                self.count += 1
                team = "white" if board.whiteMove else "black"
                depth = self.depth_white if board.whiteMove else self.depth_black

                ai_move = ChessAI.find_best_move(board, depth, valid_moves, team)

                if ai_move is None:
                    # Defensive guard: if search returns nothing
                    print("AI crashed")
                else:
                    # Play SFX based on captured piece BEFORE applying move
                    captured_piece = board.board[ai_move.end_row][ai_move.end_col]
                    board.doMove(ai_move, True)
                    move_done = True

                    methods(screen, board, sq_width, sq_height, colour1, colour2)

                    if captured_piece == "--":
                        self.move_sound.play()
                    else:
                        self.capture.play()

                    # Visualize AI move and potential checks
                    highlight_square(screen, ai_move.start_row, ai_move.start_col, sq_width, sq_height, (0, 255, 0))
                    highlight_square(screen, ai_move.end_row, ai_move.end_col, sq_width, sq_height, (0, 125, 0))

                    if board.is_check():
                        self.check.play()
                        king_pos = board.wK_position if board.whiteMove else board.bK_position
                        highlight_square(screen, king_pos[0], king_pos[1], sq_width, sq_height, (255, 0, 0))

            # --- post-move bookkeeping ---
            if move_done:
                valid_moves = board.getValidMoves()
                move_done = False

                # No legal moves → checkmate or stalemate
                if len(valid_moves) == 0:
                    winner = "white" if not board.whiteMove else "black"
                    draw_game_over_message(
                        screen,
                        f"Checkmate, {winner} wins" if board.is_check() else "Stalemate"
                    )
                    self.game_over = True

                # Trivial draw heuristic: K vs K (62 empty squares)
                if sum(1 for row in board.board for col in row if col == "--") == 62:
                    draw_game_over_message(screen, "Draw")
                    self.game_over = True

            # Present frame and keep frame time reasonable
            p.display.update()
            clock.tick(120)  # cap both menu + game FPS


# Entrypoint
main = Main()

if __name__ == "__main__":
    main.main()
