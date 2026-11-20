"""Ship and shot state for one player's board.

Coordinates everywhere in this module are 0-based ``(row, col)`` tuples.
Conversion to and from the 1-based "row,col" text that players type happens
only in ``game.py``.
"""
import random

MISS = "miss"
HIT = "hit"
SUNK = "sunk"
REPEAT = "repeat"

# (name, length). 7 ship cells on a 6x6 board.
FLEET = [("Cruiser", 3), ("Destroyer", 2), ("Submarine", 2)]


class Ship:
    def __init__(self, name, cells):
        self.name = name
        self.cells = frozenset(cells)
        self.hits = set()

    def is_sunk(self):
        return self.hits >= self.cells


class ShotResult:
    """Outcome of one shot: MISS, HIT, SUNK or REPEAT, plus the ship involved."""

    def __init__(self, outcome, ship=None):
        self.outcome = outcome
        self.ship = ship

    def __repr__(self):
        return f"ShotResult({self.outcome!r}, {self.ship.name if self.ship else None!r})"


class Board:
    SIZE = 6

    def __init__(self, size=SIZE):
        self.size = size
        self.ships = []
        self.shots = set()

    def in_bounds(self, pos):
        r, c = pos
        return 0 <= r < self.size and 0 <= c < self.size

    def ship_at(self, pos):
        for ship in self.ships:
            if pos in ship.cells:
                return ship
        return None

    def occupied(self):
        return {cell for ship in self.ships for cell in ship.cells}

    def place_ship(self, name, cells):
        """Place a straight, contiguous ship. Raises ValueError if it does not fit."""
        cells = sorted(set(cells))
        if not cells:
            raise ValueError("A ship needs at least one cell.")
        if not all(self.in_bounds(c) for c in cells):
            raise ValueError(f"{name} is outside the board.")
        rows = {r for r, _ in cells}
        cols = {c for _, c in cells}
        if len(rows) == 1:
            line = sorted(cols)
        elif len(cols) == 1:
            line = sorted(rows)
        else:
            raise ValueError(f"{name} must be in one row or one column.")
        if line != list(range(line[0], line[0] + len(cells))):
            raise ValueError(f"{name} cells must be next to each other.")
        if self.occupied() & set(cells):
            raise ValueError(f"{name} overlaps another ship.")
        ship = Ship(name, cells)
        self.ships.append(ship)
        return ship

    def place_fleet_randomly(self, fleet=FLEET, rng=random):
        for name, length in fleet:
            while True:
                horizontal = rng.random() < 0.5
                r = rng.randrange(self.size if horizontal else self.size - length + 1)
                c = rng.randrange(self.size - length + 1 if horizontal else self.size)
                cells = [(r, c + i) if horizontal else (r + i, c) for i in range(length)]
                try:
                    self.place_ship(name, cells)
                    break
                except ValueError:
                    continue

    def fire(self, pos):
        """Resolve one shot. A repeated shot changes nothing and returns REPEAT."""
        if not self.in_bounds(pos):
            raise ValueError("Shot is outside the board.")
        if pos in self.shots:
            return ShotResult(REPEAT, self.ship_at(pos))
        self.shots.add(pos)
        ship = self.ship_at(pos)
        if ship is None:
            return ShotResult(MISS)
        ship.hits.add(pos)
        return ShotResult(SUNK if ship.is_sunk() else HIT, ship)

    def all_sunk(self):
        return bool(self.ships) and all(s.is_sunk() for s in self.ships)

    def ships_afloat(self):
        return [s for s in self.ships if not s.is_sunk()]

    def render(self, reveal_ships):
        """Grid lines: X hit, o miss, S ship (only if reveal_ships), . unknown."""
        occupied = self.occupied()
        lines = ["   " + " ".join(str(c + 1) for c in range(self.size))]
        for r in range(self.size):
            row = []
            for c in range(self.size):
                pos = (r, c)
                if pos in self.shots:
                    row.append("X" if pos in occupied else "o")
                elif reveal_ships and pos in occupied:
                    row.append("S")
                else:
                    row.append(".")
            lines.append(f"{r + 1:>2} " + " ".join(row))
        return lines
