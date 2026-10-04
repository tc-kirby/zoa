"""Tests for the rot mechanic.

Run from the repository root (media.py loads ./images at import time):
    SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m unittest discover -v
"""
import os
import random
import sys
import unittest
from types import SimpleNamespace
from unittest import mock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pygame
pygame.init()
pygame.display.set_mode((1, 1))

import engine, grid, media, player, interface

SIZE = (20, 20)


def make_game(n_players=2, ai=False):
    cls = player.AIPlayer if ai else player.Player
    players = [cls(i) for i in range(n_players)]
    game = engine.Game(SIZE, players)
    game.current_player = players[0]
    return game


def fill(game, p, positions):
    for pos in positions:
        game.grid.get_square(pos).player = p


def fill_board(game, p0, p1, fraction_rows=20):
    """Left half p0, right half p1 (full board occupied) -- heads untouched."""
    for (x, y), tile in game.grid.squares.items():
        if tile.player is None:
            tile.player = p0 if x < 10 else p1


class StubRng:
    def __init__(self, value=0.0, choice_index=0):
        self.value = value
        self.choice_index = choice_index

    def random(self):
        return self.value

    def choice(self, seq):
        return seq[self.choice_index]

    def choices(self, population, weights=None, k=1):
        return [population[0]]


class OccupancyTests(unittest.TestCase):
    def test_occupancy_counts_owned_tiles_only(self):
        game = make_game()
        self.assertAlmostEqual(game.get_occupancy(), 2 / 400)
        game.grid.get_square((1, 1)).tooth = True  # tooth on empty tile counts as empty
        self.assertAlmostEqual(game.get_occupancy(), 2 / 400)
        fill(game, game.players[0], [(2, 2), (3, 3)])
        self.assertAlmostEqual(game.get_occupancy(), 4 / 400)

    def test_no_rot_at_or_below_threshold(self):
        game = make_game()
        a, b = game.players
        # Exactly 80% occupied = 320 tiles
        count = 2
        for pos, tile in game.grid.squares.items():
            if count >= 320:
                break
            if tile.player is None:
                tile.player = a
                count += 1
        self.assertEqual(game.get_occupancy(), 0.8)
        with mock.patch.object(engine, "ROT_CHANCE", 1.0):
            self.assertEqual(game.rot_player_extremities(random.Random(1)), [])

    def test_rot_above_threshold(self):
        game = make_game()
        a, b = game.players
        fill_board(game, a, b)
        with mock.patch.object(engine, "ROT_CHANCE", 1.0):
            # Only the target rots; keep rolling rounds until it's a's turn
            queue = game.rot_player_extremities(StubRng(0.0, choice_index=0))
        self.assertTrue(queue)
        self.assertTrue(all(isinstance(t, media.Rot) for t in queue))


class SelectionTests(unittest.TestCase):
    def test_heads_never_rot_and_count_clamped(self):
        game = make_game()
        a, b = game.players
        fill_board(game, a, b)
        for seed in range(50):
            positions = game.select_rot_positions(a, random.Random(seed))
            self.assertNotIn(a.head_location, positions)
            self.assertEqual(len(set(positions)), len(positions))
            self.assertTrue(all(game.grid.get_square(p).player is a for p in positions))
            self.assertEqual(len(positions), engine.ROT_MAX_TILES)  # 200 tiles -> clamp to max

    def test_minimum_one_and_eligible_cap(self):
        game = make_game()
        a, b = game.players
        fill(game, a, [(5, 4)])  # head + 1 tile; 0.05*2 rounds to 0 -> min 1
        self.assertEqual(len(game.select_rot_positions(a, random.Random(0))), 1)
        game2 = make_game()  # head only -> nothing eligible
        self.assertEqual(game2.select_rot_positions(game2.players[0], random.Random(0)), [])

    def test_exposure_weighting_bias(self):
        game = make_game()
        a, b = game.players
        # a: 3x3 block in the interior... plus an edge tile and a contact tile
        interior = [(8, 8), (8, 9), (9, 8), (9, 9), (8, 10), (9, 10)]
        edge = (0, 10)       # one off-board side
        contact = (9, 11)    # next to b's tile
        fill(game, a, interior + [edge, contact])
        fill(game, b, [(10, 11)])
        weights_rng = random.Random(42)
        counts = {}
        trials = 3000
        with mock.patch.object(engine, "ROT_MAX_TILES", 1), mock.patch.object(engine, "ROT_FRACTION", 0.0):
            for _ in range(trials):
                pos = game.select_rot_positions(a, weights_rng)[0]
                counts[pos] = counts.get(pos, 0) + 1
        avg_interior = sum(counts.get(p, 0) for p in interior) / len(interior)
        self.assertGreater(counts[edge], 2 * avg_interior)
        self.assertGreater(counts[contact], 2 * avg_interior)
        self.assertGreater(avg_interior, 0)  # interior tiles can still rot


class RoundTests(unittest.TestCase):
    def run_round(self, game, rng, turns=None):
        rotted = []
        for _ in range(turns or len(game.players)):
            queue = game.rot_player_extremities(rng)
            if queue:
                rotted.append(game.current_player)
            game.next_turn()
        return rotted

    def test_single_roll_per_round_and_only_starting_player(self):
        game = make_game(3)
        a, b, c = game.players
        fill_board(game, a, b)
        for pos, t in game.grid.squares.items():
            if pos[1] > 14 and t.player is not None and not t.head:
                t.player = c
        counting = mock.Mock(wraps=StubRng(0.0, choice_index=1))
        before = {p: len(game.grid.get_player_positions(p)) for p in game.players}
        with mock.patch.object(engine, "ROT_CHANCE", 1.0):
            rotted = self.run_round(game, counting)
        self.assertEqual(counting.random.call_count, 1)
        self.assertEqual(rotted, [b])
        after = {p: len(game.grid.get_player_positions(p)) for p in game.players}
        self.assertLess(after[b], before[b])
        self.assertEqual(after[a], before[a])
        self.assertEqual(after[c], before[c])

    def test_failed_roll_means_no_rot_all_round(self):
        game = make_game(3)
        fill_board(game, game.players[0], game.players[1])
        with mock.patch.object(engine, "ROT_CHANCE", 0.3):
            self.assertEqual(self.run_round(game, StubRng(0.99)), [])

    def test_chosen_player_dies_midround(self):
        game = make_game(3)
        a, b, c = game.players
        fill_board(game, a, b)
        with mock.patch.object(engine, "ROT_CHANCE", 1.0):
            self.assertEqual(game.rot_player_extremities(StubRng(0.0, choice_index=1)), [])  # a's turn
            self.assertIs(game.rot_target_player, b)
            b.alive = False
            game.remove_dead_players()
            game.next_turn()
            self.assertIs(game.current_player, c)
            self.assertEqual(game.rot_player_extremities(StubRng(0.0)), [])

    def test_next_turn_when_current_player_removed(self):
        game = make_game(3)
        a, b, c = game.players
        game.current_player = b
        b.alive = False
        game.remove_dead_players()
        game.next_turn()
        self.assertIs(game.current_player, c)


class CascadeTests(unittest.TestCase):
    def test_cut_off_chunk_dies(self):
        game = make_game()
        a, b = game.players
        # A thin line from a's head (4,4) to (4,6) then a detached chunk beyond (4,7)
        fill(game, a, [(4, 5), (4, 6), (4, 7), (4, 8)])
        game.grid.get_square((4, 8)).player = a
        queue = game.get_rot_anim_stages([(4, 5)])
        self.assertIsNone(game.grid.get_square((4, 5)).player)
        game.check_alive()
        deaths = game.get_death_anim_stages()
        self.assertEqual(sorted(t.pos for t in deaths), [(4, 6), (4, 7), (4, 8)])
        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0].mid_tile.animation_state, media.TileAnimation.ROT)


class EnvTests(unittest.TestCase):
    def test_parse_rot_chance(self):
        self.assertEqual(engine.parse_rot_chance("1", 0.3), 1.0)
        self.assertEqual(engine.parse_rot_chance("0.5", 0.3), 0.5)
        self.assertEqual(engine.parse_rot_chance("0", 0.3), 0.0)
        for bad in (None, "", "abc", "nan", "-1", "2", "inf"):
            self.assertEqual(engine.parse_rot_chance(bad, 0.3), 0.3)

    def test_rot_sound_and_visual_map_to_cut(self):
        self.assertEqual(media.ROT_SOUND, "cut")
        self.assertEqual(media.ROT_VISUAL, media.TileAnimation.CUT)
        self.assertEqual(media.Rot(None, None, None, None).get_sounds(), ["rot"])


class AITurnHookTests(unittest.TestCase):
    def test_ai_turns_trigger_start_turn(self):
        game = make_game(3, ai=True)
        game.players[0].__class__ = player.Player  # human first
        starts = []
        ui = SimpleNamespace(game=game, piece_pal_element=SimpleNamespace(has_piece=False))
        ui.start_turn = lambda: starts.append(game.current_player)
        ui.end_turn_actions = lambda: None
        ui.draw_elements = lambda: None
        ui.draw_screen = lambda: None
        for p in game.players:
            p.take_turn = lambda g, p=p: False
        game.players[1].take_turn = lambda g: False

        # Stop the loop once it is the human's turn again
        with mock.patch.object(interface.time, "sleep"):
            interface.UI.next_turn(ui)
        # human (a) -> AI b and AI c each start a turn, then human again
        self.assertEqual(starts[0], game.players[1])
        self.assertIn(game.players[2], starts)
        self.assertIs(game.current_player, game.players[0])

    def test_loop_stops_when_winner_set(self):
        game = make_game(3, ai=True)
        game.current_player = game.players[0]
        starts = []
        ui = SimpleNamespace(game=game, piece_pal_element=SimpleNamespace(has_piece=False))
        ui.start_turn = lambda: starts.append(game.current_player)
        ui.end_turn_actions = lambda: setattr(game, "winner", game.players[1])
        ui.draw_elements = lambda: None
        ui.draw_screen = lambda: None
        for p in game.players:
            p.take_turn = lambda g: True
        with mock.patch.object(interface.time, "sleep"):
            interface.UI.next_turn(ui)
        self.assertEqual(len(starts), 1)


if __name__ == "__main__":
    unittest.main()
