"""Python checks for hand positions, NiceGUI interactions, and launch options."""

import asyncio
from contextlib import asynccontextmanager, redirect_stderr
from importlib.util import find_spec
from io import StringIO
from itertools import product
import unittest
from unittest.mock import patch

from chopsticks.chopsticks import legal_moves, normalize_state


@asynccontextmanager
async def game_user(suboptimal_percent=0):
    from nicegui.testing import user_simulation
    from chopsticks import run_ui

    # Enable NiceGUI's test-specific cleanup when running under unittest.
    # Its default detection only recognizes pytest.
    with patch("nicegui.helpers.is_pytest", return_value=True):
        with patch.object(run_ui, "AI_SUBOPTIMAL_PERCENT", suboptimal_percent):
            async with user_simulation(run_ui.game_page) as user:
                yield user


async def start_game(user, player=1):
    toggle = next(iter(user.find(marker="buddy-first").elements))
    toggle.value = player == 2
    await asyncio.sleep(0)
    user.find("New game").click()
    await user.should_see("Buddy is thinking…" if player == 2 else "Your turn, bright spark!")


@unittest.skipUnless(find_spec("nicegui"), "NiceGUI is required for UI checks")
class HandPositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from chopsticks import run_ui
        cls.game = run_ui

    def test_every_physical_board_matches_core_successors(self):
        actions = [(kind, source, target) for kind in ("attack", "self_attack")
                   for source, target in product(range(2), repeat=2)]
        actions += [("split", left) for left in range(5)]
        for counts in product(range(5), repeat=4):
            hands = (counts[:2], counts[2:])
            for player in (0, 1):
                state = self.game.canonical_state(hands, player)
                expected = {child for action, child in legal_moves(state)}
                actual = set()
                for action in actions:
                    try:
                        updated, message = self.game.make_move(hands, player, action)
                    except ValueError:
                        continue
                    actual.add(normalize_state((updated[1 - player], updated[player])))
                    self.assertTrue(message)
                    if action[0] == "attack":
                        self.assertEqual(updated[player], hands[player])
                self.assertEqual(actual, expected, (hands, player))
                for action, child in legal_moves(state):
                    physical = self.game.physical_action(hands, player, action)
                    updated, _ = self.game.make_move(hands, player, physical)
                    self.assertEqual(normalize_state((updated[1 - player], updated[player])), child)

    def test_equal_hands_change_the_actual_clicked_target(self):
        hands = ((1, 1), (1, 1))
        updated, _ = self.game.make_move(hands, 0, ("self_attack", 1, 0))
        self.assertEqual(updated, ((2, 1), (1, 1)))
        updated, _ = self.game.make_move(hands, 0, ("attack", 1, 1))
        self.assertEqual(updated, ((1, 1), (1, 2)))

    def test_split_preserves_the_dead_hands_screen_position(self):
        for own, expected in [((4, 0), (3, 1)), ((0, 4), (1, 3))]:
            with self.subTest(own=own):
                updated, _ = self.game.make_move((own, (1, 1)), 0, ("split", 1))
                self.assertEqual(updated[0], expected)

    def test_invalid_taps_splits_and_finished_games(self):
        for hands, action in [
            (((1, 1), (1, 1)), ("self_attack", 0, 0)),
            (((0, 1), (0, 2)), ("attack", 0, 1)),
            (((0, 1), (0, 2)), ("attack", 1, 0)),
            (((1, 3), (1, 1)), ("split", 2)),
            (((0, 4), (1, 1)), ("split", 0)),
            (((0, 0), (1, 1)), ("attack", 0, 0)),
            (((1, 1), (0, 0)), ("split", 1)),
        ]:
            with self.subTest(hands=hands, action=action), self.assertRaises(ValueError):
                self.game.make_move(hands, 0, action)

    def test_winner_keeps_human_and_ai_identity(self):
        self.assertIsNone(self.game.winner(((1, 1), (1, 1))))
        self.assertEqual(self.game.winner(((4, 0), (0, 0))), 0)
        self.assertEqual(self.game.winner(((0, 0), (4, 0))), 1)


@unittest.skipUnless(find_spec("nicegui"), "NiceGUI is required for UI checks")
class BrowserInteractionTests(unittest.IsolatedAsyncioTestCase):
    async def test_opens_ready_to_play_with_buddy_first_off(self):
        async with game_user() as user:
            await user.open("/")
            await user.should_see("Your turn, bright spark!")
            await user.should_see(marker="hand-0-0")
            await user.should_not_see("Who goes first?")
            self.assertFalse(next(iter(user.find(marker="buddy-first").elements)).value)
            await user.should_see("PLAYER 1 · YOU")
            await user.should_see("Your story starts with a tap.")

    async def test_toggle_applies_to_next_game_and_persists(self):
        async with game_user() as user:
            await user.open("/")
            toggle = next(iter(user.find(marker="buddy-first").elements))
            toggle.value = True
            await asyncio.sleep(0)
            await user.should_see("PLAYER 1 · YOU")
            await user.should_see("Your turn, bright spark!")
            user.find("New game").click()
            await user.should_see("Buddy is thinking…")
            await user.should_see("PLAYER 2 · YOU")
            await asyncio.sleep(1)
            user.find("New game").click()
            await user.should_see("Buddy is thinking…")
            self.assertTrue(toggle.value)
            await asyncio.sleep(1)

    async def test_player_two_gets_exactly_one_buddy_opening(self):
        from chopsticks import run_ui

        async with game_user() as user:
            await user.open("/")
            with patch.object(run_ui, "choose_action", wraps=run_ui.choose_action) as choose:
                await start_game(user, player=2)
                await user.should_see("PLAYER 2 · YOU")
                self.assertFalse(next(iter(user.find(marker="hand-0-0").elements)).enabled)
                await asyncio.sleep(1)
                await user.should_see("Your turn, bright spark!")
                self.assertEqual(choose.call_count, 1)
                self.assertTrue(next(iter(user.find(marker="hand-0-0").elements)).enabled)

    async def test_restart_cancels_opening_even_when_next_game_has_started(self):
        from chopsticks import run_ui

        async with game_user() as user:
            await user.open("/")
            with patch.object(run_ui, "choose_action", wraps=run_ui.choose_action) as choose:
                await start_game(user, player=2)
                await start_game(user, player=1)
                await asyncio.sleep(1)
                choose.assert_not_called()
                await user.should_see("Your story starts with a tap.")
                await user.should_see("Your turn, bright spark!")

    async def test_invalid_percentage_prevents_buddy_opening(self):
        from nicegui import ui

        async with game_user() as user:
            await user.open("/")
            next(iter(user.find(ui.number).elements)).value = None
            next(iter(user.find(marker="buddy-first").elements)).value = True
            await asyncio.sleep(0)
            user.find("New game").click()
            await user.should_see("Choose a suboptimal percentage from 0 to 100 first.")
            await user.should_see("Your turn, bright spark!")
            await user.should_see("PLAYER 1 · YOU")

    async def test_select_tap_ai_reply_and_restart(self):
        async with game_user() as user:
            await user.open("/")
            await start_game(user)
            await user.should_see("Chopsticks Club")
            user.find(marker="hand-0-0").click()
            await user.should_see("Now choose a target")
            user.find(marker="hand-1-1").click()
            await user.should_see("Buddy is thinking…")
            await asyncio.sleep(1)
            await user.should_see("Your turn, bright spark!")
            await user.should_see("You tapped Buddy: 1 + 1 = 2.")
            user.find("New game").click()
            await user.should_see("Your turn, bright spark!")
            await user.should_see("Your story starts with a tap.")

    async def test_self_tap_targets_the_selected_physical_hand(self):
        async with game_user() as user:
            await user.open("/")
            await start_game(user)
            user.find(marker="hand-0-1").click()
            await user.should_see("Now choose a target")
            user.find(marker="hand-0-0").click()
            await user.should_see("Buddy is thinking…")
            await user.should_see("You tapped the other hand: 1 + 1 = 2.")
            await asyncio.sleep(1)

    async def test_restart_cancels_the_pending_ai_turn(self):
        async with game_user() as user:
            await user.open("/")
            await start_game(user)
            user.find(marker="hand-0-0").click()
            await user.should_see("Now choose a target")
            user.find(marker="hand-1-0").click()
            await user.should_see("Buddy is thinking…")
            user.find("New game").click()
            await asyncio.sleep(1)
            await user.should_see("Your turn, bright spark!")
            await user.should_see("Your story starts with a tap.")
            await user.should_see("Your turn, bright spark!")

    async def test_percentage_defaults_to_zero_and_can_be_changed_in_the_page(self):
        from nicegui import ui
        from chopsticks import run_ui

        async with game_user() as user:
            await user.open("/")
            await start_game(user)
            control = next(iter(user.find(ui.number).elements))
            self.assertEqual(control.value, 0)
            await user.should_see("Suboptimal percentage")
            control.value = 37.5
            with patch.object(run_ui, "choose_action", wraps=run_ui.choose_action) as choose:
                user.find(marker="hand-0-0").click()
                await user.should_see("Now choose a target")
                user.find(marker="hand-1-0").click()
                await asyncio.sleep(1)
                self.assertEqual(choose.call_args.args[2], 37.5)
            user.find("New game").click()
            self.assertEqual(control.value, 37.5)

    async def test_invalid_percentage_does_not_advance_the_game(self):
        from nicegui import ui

        async with game_user() as user:
            await user.open("/")
            await start_game(user)
            next(iter(user.find(ui.number).elements)).value = None
            user.find(marker="hand-0-0").click()
            await user.should_see("Now choose a target")
            user.find(marker="hand-1-0").click()
            await user.should_see("Choose a suboptimal percentage from 0 to 100 first.")
            await user.should_see("Your story starts with a tap.")


@unittest.skipUnless(find_spec("nicegui"), "NiceGUI is required for UI checks")
class BrowserCommandLineTests(unittest.TestCase):
    def test_cli_percentage_and_default(self):
        from chopsticks import run_ui

        for arguments, expected in [([], 0), (["--suboptimal-percent", "12.5"], 12.5)]:
            with patch.object(run_ui, "AI_SUBOPTIMAL_PERCENT", 0):
                with patch.object(run_ui.ui, "run") as run:
                    run_ui.main(arguments + ["--no-show"])
                    self.assertEqual(run_ui.AI_SUBOPTIMAL_PERCENT, expected)
                    self.assertFalse(run.call_args.kwargs["show"])

    def test_cli_rejects_invalid_percentages_before_starting_server(self):
        from chopsticks import run_ui

        for value in ("-1", "101", "nan", "inf"):
            with self.subTest(value=value), patch.object(run_ui.ui, "run") as run:
                with redirect_stderr(StringIO()), self.assertRaises(SystemExit) as error:
                    run_ui.main(["--suboptimal-percent", value])
                self.assertEqual(error.exception.code, 2)
                run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
