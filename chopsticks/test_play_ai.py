"""Checks for optimal computer choices and human/computer turn handling."""

from contextlib import redirect_stdout
from io import StringIO
import unittest
from unittest.mock import patch

import chopsticks as game
import play_ai
from solve import solve


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
