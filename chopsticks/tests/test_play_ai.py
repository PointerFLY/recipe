"""Checks for optimal computer choices and human/computer turn handling."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import unittest
from unittest.mock import patch

from chopsticks import chopsticks as game
from chopsticks import play_ai
from chopsticks.solve import solve


class ComputerPlayerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.strategy = solve()

    def test_computer_selects_an_optimal_legal_action_at_every_position(self):
        for state, row in self.strategy.items():
            with self.subTest(state=state):
                if row["actions"]:
                    action = play_ai.choose_action(state, self.strategy)
                    self.assertIn(action, row["actions"])
                    self.assertIn(action, dict(game.legal_moves(state)))
                    self.assertEqual(play_ai.choose_action((state[0][::-1], state[1][::-1]), self.strategy), action)
                else:
                    with self.assertRaises(ValueError):
                        play_ai.choose_action(state, self.strategy)

    def test_human_moves_first_by_default(self):
        output = StringIO()
        with patch('builtins.input', return_value='q') as prompt, redirect_stdout(output):
            play_ai.main([])
        self.assertEqual(prompt.call_count, 1)
        self.assertIn('You are Player 1', output.getvalue())
        self.assertNotIn('Computer chooses', output.getvalue())

    def test_full_suboptimal_chance_chooses_only_nonoptimal_moves_when_available(self):
        for state, row in self.strategy.items():
            if not row["actions"]:
                continue
            alternatives = {a for a, _ in game.legal_moves(state)} - set(row["actions"])
            with self.subTest(state=state):
                action = play_ai.choose_action(state, self.strategy, 100)
                if alternatives:
                    self.assertIn(action, alternatives)
                else:
                    self.assertEqual(action, row["actions"][0])

    def test_percentage_threshold_and_zero_default(self):
        state = ((2, 4), (1, 3))
        with patch.object(play_ai.random, 'random', return_value=0.249):
            self.assertNotIn(play_ai.choose_action(state, self.strategy, 25),
                             self.strategy[state]["actions"])
        with patch.object(play_ai.random, 'random', return_value=0.25):
            self.assertEqual(play_ai.choose_action(state, self.strategy, 25),
                             self.strategy[state]["actions"][0])
        with patch.object(play_ai.random, 'random') as draw:
            play_ai.choose_action(state, self.strategy)
            draw.assert_not_called()

    def test_invalid_percentages_are_rejected(self):
        for value in (-1, 101, float('nan'), float('inf')):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    play_ai.choose_action(game.INITIAL_STATE, self.strategy, value)
                with redirect_stderr(StringIO()), self.assertRaises(SystemExit) as error:
                    play_ai.main(['--suboptimal-percent', str(value)])
                self.assertEqual(error.exception.code, 2)

    def test_cli_passes_percentage_to_computer(self):
        with patch.object(game, 'main') as run_game, redirect_stdout(StringIO()) as output:
            play_ai.main(['--suboptimal-percent', '12.5'])
        self.assertIn('12.5%', output.getvalue())
        with patch.object(play_ai, 'choose_action') as choose:
            run_game.call_args.kwargs['computer'](game.INITIAL_STATE)
        self.assertEqual(choose.call_args.args[2], 12.5)

    def test_computer_moves_first_when_human_is_player_two(self):
        output = StringIO()
        with patch('builtins.input', return_value='q') as prompt, redirect_stdout(output):
            play_ai.main(['--player', '2'])
        self.assertEqual(prompt.call_count, 1)
        self.assertEqual(output.getvalue().count('Computer chooses move'), 1)
        self.assertIn('AI (P1)', output.getvalue())
        self.assertIn('You (P2)', output.getvalue())
        self.assertIn('AI after', output.getvalue())

    def test_computer_takes_a_forced_win_after_a_human_move(self):
        output = StringIO()
        with patch.object(game, 'INITIAL_STATE', ((0, 1), (0, 3))):
            with patch('builtins.input', return_value='1') as prompt, redirect_stdout(output):
                play_ai.main([])
        self.assertEqual(prompt.call_count, 1)
        self.assertTrue(output.getvalue().endswith('Computer wins!\n'))

    def test_human_win_and_invalid_input_do_not_trigger_extra_computer_turns(self):
        output = StringIO()
        with patch.object(game, 'INITIAL_STATE', ((0, 4), (0, 1))):
            with patch('builtins.input', side_effect=['bad', '0', '1']), redirect_stdout(output):
                play_ai.main([])
        self.assertTrue(output.getvalue().endswith('You win!\n'))
        self.assertNotIn('Computer chooses', output.getvalue())


if __name__ == "__main__":
    unittest.main()
