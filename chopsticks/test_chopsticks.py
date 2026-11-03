"""Regression checks for UC Berkeley GamesCrafters' base rules.

Run with: python3 -m unittest discover -s chopsticks -v
"""

from itertools import combinations_with_replacement, product
import unittest

from chopsticks import apply_action, initial_state, legal_actions, winner


class ChopsticksRulesTests(unittest.TestCase):
    def test_start(self):
        self.assertEqual(initial_state(), ((1, 1), (1, 1)))
        self.assertEqual(legal_actions(initial_state()), [("attack", 0, 0)])

    def test_split_from_one_and_revive_dead_hand(self):
        for own, action, expected in [
            ((1, 3), ("split", 2), (2, 2)),
            ((0, 2), ("split", 1), (1, 1)),
            ((0, 4), ("split", 1), (1, 3)),
            ((0, 4), ("split", 2), (2, 2)),
        ]:
            with self.subTest(own=own, action=action):
                self.assertEqual(
                    apply_action((own, (1, 1)), action), (expected, (1, 1))
                )

    def test_full_transfers_and_passes_are_illegal(self):
        for own, action in [
            ((2, 2), ("split", 0)),
            ((1, 3), ("split", 0)),
            ((1, 3), ("split", 1)),
            ((1, 3), ("split", 3)),
            ((0, 1), ("split", 0)),
        ]:
            with self.subTest(own=own, action=action):
                with self.assertRaises(ValueError):
                    apply_action((own, (1, 1)), action)

    def test_attacks_use_cutoff_and_preserve_attacker(self):
        for target, expected in [(1, (0, 4)), (2, (0, 0)), (4, (0, 0))]:
            with self.subTest(target=target):
                self.assertEqual(
                    apply_action(((1, 3), (0, target)), ("attack", 1, 1)),
                    ((1, 3), expected),
                )

    def test_dead_hands_and_self_attacks_are_illegal(self):
        state = ((0, 2), (0, 3))
        for action in [("attack", 0, 1), ("attack", 1, 0), ("self_attack", 1, 0)]:
            with self.subTest(action=action):
                with self.assertRaises(ValueError):
                    apply_action(state, action)

    def test_winning_attack_ends_game(self):
        state = apply_action(((1, 3), (0, 2)), ("attack", 1, 1))
        self.assertEqual(winner(state), 0)
        for player in (0, 1):
            self.assertEqual(legal_actions(state, player), [])
            with self.assertRaises(ValueError):
                apply_action(state, ("split", 2), player)

    def test_all_states_match_rule_defined_successors(self):
        hands = list(combinations_with_replacement(range(5), 2))
        for state in product(hands, repeat=2):
            for player in (0, 1):
                with self.subTest(state=state, player=player):
                    own, other = state[player], state[1 - player]
                    expected = set()
                    if own != (0, 0) and other != (0, 0):
                        for attacker, target in product(range(2), repeat=2):
                            if own[attacker] and other[target]:
                                updated = list(other)
                                count = own[attacker] + other[target]
                                updated[target] = count if count < 5 else 0
                                expected.add((own, tuple(sorted(updated))))
                        for redistributed in combinations_with_replacement(range(1, 5), 2):
                            if sum(redistributed) == sum(own) and redistributed != own:
                                expected.add((redistributed, other))
                    actual = set()
                    for action in legal_actions(state, player):
                        result = apply_action(state, action, player)
                        actual.add((result[player], result[1 - player]))
                    self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
