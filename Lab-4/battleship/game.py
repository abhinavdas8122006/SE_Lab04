"""Turn flow and setup.

Players type 1-based "row,col" text. It is converted to a 0-based
``(row, col)`` tuple once, in ``parse_coord``, and every other module uses
that tuple format.
"""
import random

from ai import AI
from board import Board, HIT, MISS, REPEAT, SUNK

QUIT_WORDS = {"q", "quit", "exit"}


def parse_coord(raw, size=Board.SIZE):
    """Turn "2,3" into (1, 2). Raises ValueError with a message for the player."""
    parts = raw.replace(" ", "").split(",")
    if len(parts) != 2:
        raise ValueError("Use row,col (for example 2,3).")
    try:
        r, c = int(parts[0]), int(parts[1])
    except ValueError:
        raise ValueError("Row and column must be whole numbers, like 2,3.") from None
    if not (1 <= r <= size and 1 <= c <= size):
        raise ValueError(f"Outside board. Rows and columns go from 1 to {size}.")
    return (r - 1, c - 1)


def format_coord(pos):
    return f"{pos[0] + 1},{pos[1] + 1}"


def describe(shooter, pos, result):
    """One feedback line for one shot that was actually fired."""
    where = format_coord(pos)
    if result.outcome == MISS:
        return f"{shooter} fired at {where}: MISS."
    if result.outcome == HIT:
        return f"{shooter} fired at {where}: HIT!"
    if result.outcome == SUNK:
        return f"{shooter} fired at {where}: HIT and SUNK the {result.ship.name}!"
    raise ValueError(f"No feedback for outcome {result.outcome!r}")


class Battleship:
    def __init__(self, seed=None, input_fn=input, output=print):
        self.rng = random.Random(seed)
        self.input = input_fn
        self.out = output
        self.player = Board()
        self.enemy = Board()
        self.ai = AI(Board.SIZE, rng=self.rng)
        self._setup()

    def _setup(self):
        self.player.place_fleet_randomly(rng=self.rng)
        self.enemy.place_fleet_randomly(rng=self.rng)

    def show(self):
        enemy = self.enemy.render(reveal_ships=False)
        mine = self.player.render(reveal_ships=True)
        self.out("")
        self.out(f"{'Enemy waters':<18}   {'Your fleet'}")
        for left, right in zip(enemy, mine):
            self.out(f"{left:<18}   {right}")
        self.out(f"Enemy ships afloat: {len(self.enemy.ships_afloat())}/{len(self.enemy.ships)}"
                 f"   Your ships afloat: {len(self.player.ships_afloat())}/{len(self.player.ships)}")

    def player_turn(self, raw):
        """Handle one line of input. Returns True if a shot was fired."""
        try:
            pos = parse_coord(raw)
        except ValueError as err:
            self.out(str(err))
            return False
        result = self.enemy.fire(pos)
        if result.outcome == REPEAT:
            self.out(f"You already fired at {format_coord(pos)}. Pick another cell.")
            return False
        self.out(describe("You", pos, result))
        return True

    def ai_turn(self):
        pos = self.ai.choose()
        if pos is None:
            self.out("The AI has no cells left to shoot at.")
            return
        result = self.player.fire(pos)
        self.ai.record(pos, result)
        self.out(describe("AI", pos, result))

    def run(self):
        self.out("Battleship vs AI")
        self.out(f"Fleet: {', '.join(f'{s.name} ({len(s.cells)})' for s in self.enemy.ships)}."
                 " Shoot with row,col (e.g. 2,3). Type q to quit.")
        while True:
            self.show()
            try:
                raw = self.input("> ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                self.out("\nGoodbye.")
                return "quit"
            if raw in QUIT_WORDS:
                self.out("You quit the game.")
                return "quit"
            if not self.player_turn(raw):
                continue
            if self.enemy.all_sunk():
                self.show()
                self.out("You sank the whole enemy fleet. You win!")
                return "player"
            self.ai_turn()
            if self.player.all_sunk():
                self.show()
                self.out("The AI sank your whole fleet. You lose.")
                return "ai"
