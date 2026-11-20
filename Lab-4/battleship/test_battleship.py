"""Tests for the README's "Required testing" list. Run with: python -m unittest -v"""
import random
import unittest

from ai import AI
from board import Board, HIT, MISS, REPEAT, SUNK, ShotResult
from game import Battleship, parse_coord, describe


def fixed_board():
    b = Board()
    b.place_ship("Cruiser", [(0, 0), (0, 1), (0, 2)])
    b.place_ship("Destroyer", [(2, 5), (3, 5)])
    return b


class CoordinateTests(unittest.TestCase):
    def test_parse_converts_to_zero_based_tuple(self):
        self.assertEqual(parse_coord("1,1"), (0, 0))
        self.assertEqual(parse_coord(" 6 , 6 "), (5, 5))

    def test_invalid_coordinates_rejected(self):
        for raw in ["", "abc", "1", "1,2,3", "0,1", "7,1", "1,7", "-1,2", "a,b"]:
            with self.assertRaises(ValueError, msg=raw):
                parse_coord(raw)

    def test_every_ship_cell_hits_and_every_empty_cell_misses(self):
        b = fixed_board()
        ships = b.occupied()
        for r in range(b.size):
            for c in range(b.size):
                outcome = b.fire((r, c)).outcome
                self.assertEqual(outcome in (HIT, SUNK), (r, c) in ships, (r, c))

    def test_ai_choice_uses_board_coordinates(self):
        # An AI shot at a real ship cell must register as a hit on the board.
        b = fixed_board()
        ai = AI(rng=random.Random(0))
        hits = 0
        while (pos := ai.choose()) is not None:
            self.assertIsInstance(pos, tuple)
            result = b.fire(pos)
            ai.record(pos, result)
            hits += result.outcome in (HIT, SUNK)
        self.assertEqual(hits, len(b.occupied()))
        self.assertTrue(b.all_sunk())


class FleetTests(unittest.TestCase):
    def test_hit_and_miss(self):
        b = fixed_board()
        self.assertEqual(b.fire((0, 0)).outcome, HIT)
        self.assertEqual(b.fire((5, 0)).outcome, MISS)

    def test_repeated_shot_changes_nothing(self):
        b = fixed_board()
        b.fire((0, 0))
        b.fire((4, 4))
        self.assertEqual(b.fire((0, 0)).outcome, REPEAT)
        self.assertEqual(b.fire((4, 4)).outcome, REPEAT)
        self.assertEqual(len(b.shots), 2)
        self.assertEqual(b.ship_at((0, 0)).hits, {(0, 0)})

    def test_sinking_one_ship(self):
        b = fixed_board()
        self.assertEqual(b.fire((2, 5)).outcome, HIT)
        result = b.fire((3, 5))
        self.assertEqual(result.outcome, SUNK)
        self.assertEqual(result.ship.name, "Destroyer")
        self.assertFalse(b.all_sunk())
        self.assertEqual([s.name for s in b.ships_afloat()], ["Cruiser"])

    def test_sinking_all_ships_ends_game(self):
        b = fixed_board()
        for cell in sorted(b.occupied()):
            b.fire(cell)
        self.assertTrue(b.all_sunk())

    def test_individual_damage_tracked(self):
        b = fixed_board()
        b.fire((0, 1))
        b.fire((2, 5))
        self.assertEqual(b.ship_at((0, 0)).hits, {(0, 1)})
        self.assertEqual(b.ship_at((3, 5)).hits, {(2, 5)})

    def test_invalid_placement_rejected(self):
        b = fixed_board()
        with self.assertRaises(ValueError):
            b.place_ship("Overlap", [(0, 2), (1, 2)])
        with self.assertRaises(ValueError):
            b.place_ship("Diagonal", [(4, 0), (5, 1)])
        with self.assertRaises(ValueError):
            b.place_ship("Gap", [(5, 0), (5, 2)])
        with self.assertRaises(ValueError):
            b.place_ship("Outside", [(5, 5), (5, 6)])

    def test_random_fleet_is_valid(self):
        for seed in range(50):
            b = Board()
            b.place_fleet_randomly(rng=random.Random(seed))
            self.assertEqual(len(b.ships), 3)
            self.assertEqual(len(b.occupied()), 7)


class AITests(unittest.TestCase):
    def test_never_repeats_and_handles_full_board(self):
        ai = AI(rng=random.Random(1))
        seen = set()
        for _ in range(36):
            pos = ai.choose()
            self.assertNotIn(pos, seen)
            seen.add(pos)
        self.assertEqual(len(seen), 36)
        self.assertIsNone(ai.choose())

    def test_targets_adjacent_cells_after_hit(self):
        for seed in range(20):
            b = fixed_board()
            ai = AI(rng=random.Random(seed))
            ai.tried.add((2, 5))
            ai.record((2, 5), b.fire((2, 5)))
            nxt = ai.choose()
            self.assertIn(nxt, {(1, 5), (3, 5), (2, 4)})

    def test_follows_line_of_hits(self):
        b = fixed_board()
        ai = AI(rng=random.Random(3))
        for cell in [(0, 0), (0, 1)]:
            ai.tried.add(cell)
            ai.record(cell, b.fire(cell))
        self.assertEqual(ai.choose(), (0, 2))

    def test_stops_targeting_after_sink(self):
        b = fixed_board()
        ai = AI(rng=random.Random(4))
        for cell in [(2, 5), (3, 5)]:
            ai.tried.add(cell)
            ai.record(cell, b.fire(cell))
        self.assertEqual(ai.open_hits, set())

    def test_choose_has_no_side_effects_on_board(self):
        b = fixed_board()
        ai = AI(rng=random.Random(5))
        ai.choose()
        self.assertEqual(b.shots, set())


class GameFlowTests(unittest.TestCase):
    def play(self, inputs, seed=7):
        lines = []
        feed = iter(inputs)

        def fake_input(prompt):
            try:
                return next(feed)
            except StopIteration:
                raise EOFError

        game = Battleship(seed=seed, input_fn=fake_input, output=lines.append)
        return game, game.run(), lines

    def test_quit(self):
        _, outcome, lines = self.play(["q"])
        self.assertEqual(outcome, "quit")
        self.assertIn("You quit the game.", lines)

    def test_invalid_input_does_not_use_a_turn(self):
        game, _, lines = self.play(["abc", "9,9", "q"])
        self.assertEqual(game.enemy.shots, set())
        self.assertEqual(game.player.shots, set())
        self.assertTrue(any("Outside board" in l for l in lines))

    def test_repeated_player_shot_rejected_without_ai_turn(self):
        game, _, lines = self.play(["1,1", "1,1", "q"])
        self.assertTrue(any("already fired" in l for l in lines))
        self.assertEqual(len(game.player.shots), 1)  # only one AI turn

    def test_feedback_exactly_once_per_actual_shot(self):
        game, _, lines = self.play(["1,1", "2,2", "3,3", "q"])
        you = [l for l in lines if l.startswith("You fired")]
        ai = [l for l in lines if l.startswith("AI fired")]
        self.assertEqual(len(you), 3)
        self.assertEqual(len(ai), 3)
        self.assertEqual(len(ai), len(game.player.shots))

    def test_player_wins_when_enemy_fleet_sunk(self):
        probe = Battleship(seed=11, input_fn=lambda p: "q", output=lambda *a: None)
        targets = [f"{r + 1},{c + 1}" for r, c in sorted(probe.enemy.occupied())]
        game, outcome, lines = self.play(targets, seed=11)
        if outcome == "player":
            self.assertTrue(game.enemy.all_sunk())
            self.assertIn("You sank the whole enemy fleet. You win!", lines)
            self.assertTrue(any("SUNK" in l for l in lines))
        else:  # the AI got lucky first; still a valid end of game
            self.assertEqual(outcome, "ai")

    def test_describe_messages(self):
        b = fixed_board()
        self.assertIn("MISS", describe("You", (5, 5), ShotResult(MISS)))
        self.assertIn("SUNK the Destroyer", describe("AI", (3, 5), ShotResult(SUNK, b.ships[1])))


if __name__ == "__main__":
    unittest.main()
