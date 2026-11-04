"""Run with: python3 -m unittest discover -s chopsticks -v"""

from contextlib import redirect_stdout
from io import StringIO
from itertools import combinations_with_replacement, product
import unittest
from unittest.mock import patch

from chopsticks import INITIAL_STATE, legal_moves, main, next_states, normalize_state


class ChopsticksRulesTests(unittest.TestCase):
    def test_start_includes_opponent_and_self_attack(self):
        self.assertEqual(INITIAL_STATE, ((1, 1), (1, 1)))
        self.assertEqual(next_states(INITIAL_STATE), [
            ((1, 1), (1, 2)),  # Self-attack; opponent moves next.
            ((1, 2), (1, 1)),  # Opponent attack; opponent moves next.
        ])

    def test_split_options(self):
        expected = {1: [], 2: [(1, 1)], 3: [(1, 2)], 4: [(1, 3), (2, 2)]}
        for count, splits in expected.items():
            with self.subTest(count=count):
                # With one live hand, only splits leave the opponent unchanged.
                actual = [own for other, own in next_states(((count, 0), (1, 1)))
                          if other == (1, 1)]
                self.assertEqual(actual, splits)

    def test_explicit_actions_and_symmetric_hands(self):
        self.assertEqual(legal_moves(INITIAL_STATE), [
            (("attack", 0, 0), ((1, 2), (1, 1))),
            (("self_attack", 0, 1), ((1, 1), (1, 2))),
        ])
        # Different attacks can lead to the same result; keep both actions.
        moves = legal_moves(((2, 3), (0, 3)))
        result = ((0, 0), (2, 3))
        self.assertIn((("attack", 0, 1), result), moves)
        self.assertIn((("attack", 1, 1), result), moves)
        self.assertEqual(next_states(((2, 3), (0, 3))).count(result), 1)
        self.assertIn((("split", 1), ((1, 1), (1, 3))), legal_moves(((0, 4), (1, 1))))
        self.assertIn((("split", 2), ((1, 1), (2, 2))), legal_moves(((0, 4), (1, 1))))

    def test_two_live_hands_cannot_redistribute(self):
        self.assertNotIn(((1, 1), (2, 2)), next_states(((1, 3), (1, 1))))
        self.assertNotIn(((1, 1), (1, 3)), next_states(((2, 2), (1, 1))))

    def test_opponent_attack_uses_cutoff(self):
        for count, expected in [(1, (0, 4)), (2, (0, 0)), (4, (0, 0))]:
            with self.subTest(count=count):
                self.assertIn((expected, (1, 3)), next_states(((1, 3), (0, count))))

    def test_self_attacks_in_both_directions_use_cutoff(self):
        results = next_states(((2, 3), (1, 1)))
        self.assertIn(((1, 1), (0, 2)), results)
        self.assertIn(((1, 1), (0, 3)), results)
        self.assertNotIn(((1, 1), (2, 4)), results)  # Cannot attack the same hand.

    def test_dead_hands_cannot_attack_or_be_attacked(self):
        self.assertEqual(next_states(((0, 1), (0, 3))), [((0, 4), (0, 1))])

    def test_finished_games_have_no_moves(self):
        for state in [((0, 0), (1, 3)), ((1, 3), (0, 0)), ((0, 0), (0, 0))]:
            self.assertEqual(next_states(state), [])

    def test_normalization_and_validation(self):
        self.assertEqual(normalize_state(((4, 0), (3, 1))), ((0, 4), (1, 3)))
        for state in [((1, 1),), ((1,), (1, 1)), ((-1, 2), (1, 1)),
                      ((5, 1), (1, 1)), ((True, 1), (1, 1)), ((1.0, 1), (1, 1))]:
            with self.subTest(state=state), self.assertRaises(ValueError):
                next_states(state)

    def test_all_states_match_rules(self):
        hands = list(combinations_with_replacement(range(5), 2))
        for own, other in product(hands, repeat=2):
            expected = set()
            if own != (0, 0) and other != (0, 0):
                for attacker, target in product(range(2), repeat=2):
                    if own[attacker] and other[target]:
                        updated = list(other)
                        total = own[attacker] + other[target]
                        updated[target] = total if total < 5 else 0
                        expected.add((tuple(sorted(updated)), own))
                    if attacker != target and own[attacker] and own[target]:
                        updated = list(own)
                        total = own[attacker] + own[target]
                        updated[target] = total if total < 5 else 0
                        expected.add((other, tuple(sorted(updated))))
                if 0 in own:
                    for split in combinations_with_replacement(range(1, 5), 2):
                        if sum(split) == sum(own):
                            expected.add((other, split))
            with self.subTest(own=own, other=other):
                actual = next_states((own, other))
                self.assertEqual(actual, sorted(expected))
                self.assertEqual(next_states((own[::-1], other[::-1])), actual)

    def test_terminal_input_and_winner(self):
        # Exercise both winner labels while tracking the player swap.
        for state, own_after in [(((0, 4), (0, 1)), (0, 4)),
                                 (((0, 1), (0, 3)), (0, 1))]:
            choices = legal_moves(state)
            selected = next(i for i, (action, result) in enumerate(choices, 1)
                            if result[1] == own_after)
            if own_after == (0, 4):
                inputs = [str(selected)]
                expected_winner = 1
            else:
                # P1 raises the opponent's 3 to 4, then P2 kills P1's last hand.
                inputs = [str(selected), '1']
                expected_winner = 2
            output = StringIO()
            with patch('chopsticks.INITIAL_STATE', state):
                with patch('builtins.input', side_effect=['bad', '0', '999'] + inputs):
                    with redirect_stdout(output):
                        main()
            self.assertEqual(output.getvalue().count('Enter one of the listed'), 3)
            self.assertTrue(output.getvalue().endswith(f'Player {expected_winner} wins!\n'))
        with patch('builtins.input', return_value='q'), redirect_stdout(StringIO()) as output:
            main()
        self.assertIn('Game ended.', output.getvalue())

    def test_cli_shows_actions_and_results(self):
        for state, descriptions in [
            (INITIAL_STATE, ['Attack H1 (1) -> opponent H1 (1)',
                             'Self-attack H1 (1) -> H2 (1)']),
            (((0, 4), (1, 1)), ['Split (0, 4) -> (1, 3)',
                                'Split (0, 4) -> (2, 2)']),
            (((2, 3), (1, 4)), ['Self-attack H1 (2) -> H2 (3)',
                                'Self-attack H2 (3) -> H1 (2)']),
        ]:
            with self.subTest(state=state):
                output = StringIO()
                with patch('chopsticks.INITIAL_STATE', state):
                    with patch('builtins.input', return_value='q'), redirect_stdout(output):
                        main()
                for description in descriptions:
                    self.assertIn(description, ' '.join(output.getvalue().split()))
                self.assertIn('You after', output.getvalue())
                self.assertIn('Opponent after', output.getvalue())
                rows = [line for line in output.getvalue().splitlines() if ' -> ' in line]
                self.assertEqual(len({line.index('->') for line in rows}), 1)
                kinds = [action[0] for action, result in legal_moves(state)]
                self.assertEqual(kinds, sorted(kinds))


if __name__ == "__main__":
    unittest.main()
