"""Computer targeting.

The AI works only with 0-based ``(row, col)`` tuples. ``choose()`` picks a
cell and never prints or fires; the game fires the shot and then reports the
result back through ``record()``.
"""
import random

from board import HIT, SUNK


class AI:
    def __init__(self, size=6, rng=None):
        self.size = size
        self.rng = rng or random.Random()
        self.tried = set()
        self.open_hits = set()  # hits on ships that are not sunk yet

    def _untried_neighbours(self, pos):
        r, c = pos
        for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if 0 <= nr < self.size and 0 <= nc < self.size and (nr, nc) not in self.tried:
                yield (nr, nc)

    def _target_candidates(self):
        """Untried cells next to open hits; cells that extend a line of hits come first."""
        line_cells, near_cells = set(), set()
        for hit in self.open_hits:
            for cell in self._untried_neighbours(hit):
                near_cells.add(cell)
                # A neighbour is "in line" if the hit also has a hit on its far side.
                dr, dc = cell[0] - hit[0], cell[1] - hit[1]
                if (hit[0] - dr, hit[1] - dc) in self.open_hits:
                    line_cells.add(cell)
        return sorted(line_cells) or sorted(near_cells)

    def choose(self):
        """Return the next cell to shoot, or None if every cell has been tried."""
        candidates = self._target_candidates()
        if not candidates:
            candidates = [(r, c) for r in range(self.size) for c in range(self.size)
                          if (r, c) not in self.tried]
        if not candidates:
            return None
        pos = self.rng.choice(candidates)
        self.tried.add(pos)
        return pos

    def record(self, pos, result):
        """Learn from the result of a shot that was actually fired."""
        if result.outcome == HIT:
            self.open_hits.add(pos)
        elif result.outcome == SUNK:
            self.open_hits.add(pos)
            self.open_hits -= result.ship.cells
