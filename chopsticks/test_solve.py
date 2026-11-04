"""Checks for the complete perfect-play strategy and exported tables."""

from copy import deepcopy
import csv
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from chopsticks import INITIAL_STATE, legal_moves
from solve import reachable_graph, solve, verify, write_tables


class StrategyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = reachable_graph()
        cls.strategy = solve()

    def test_reachable_coverage_and_opening(self):
        self.assertEqual(len(self.graph), 192)
        self.assertEqual(set(self.strategy), set(self.graph))
        self.assertEqual(sum(not moves for moves in self.graph.values()), 14)
        self.assertEqual(self.strategy[INITIAL_STATE], {
            "outcome": "draw", "plies": None,
            "actions": [("attack", 0, 0), ("self_attack", 0, 1)],
        })
        verify(self.strategy)

    def test_independent_round_by_round_classification(self):
        # A synchronous fixed-point calculation independently checks the queue
        # solver, including cycles and multiple actions with the same child.
        wins = {s for s in self.graph if s[1] == (0, 0)}
        losses = {s for s in self.graph if s[0] == (0, 0)}
        undecided = set(self.graph) - wins - losses
        while True:
            new_wins = set()
            new_losses = set()
            for state in undecided:
                children = {child for action, child in self.graph[state]}
                if children & losses:
                    new_wins.add(state)
                elif children and children <= wins:
                    new_losses.add(state)
            if not new_wins and not new_losses:
                break
            wins |= new_wins
            losses |= new_losses
            undecided -= new_wins | new_losses
        self.assertEqual((len(wins), len(losses), len(undecided)), (79, 29, 84))
        for state, row in self.strategy.items():
            expected = "win" if state in wins else "loss" if state in losses else "draw"
            self.assertEqual(row["outcome"], expected, state)

    def test_fastest_win_and_all_equal_best_actions(self):
        row = self.strategy[((2, 4), (1, 3))]
        self.assertEqual(row, {"outcome": "win", "plies": 9,
                               "actions": [("attack", 0, 1), ("attack", 1, 1)]})
        # Attacking with 4 against 1 also wins, but takes 11 plies.
        child = dict(legal_moves(((2, 4), (1, 3))))[("attack", 1, 0)]
        self.assertEqual(self.strategy[child]["plies"], 10)

    def test_finite_policies_terminate_at_the_predicted_distance(self):
        for start, row in self.strategy.items():
            if row["plies"] is None:
                continue
            state = start
            for remaining in range(row["plies"], 0, -1):
                self.assertEqual(self.strategy[state]["plies"], remaining)
                action = self.strategy[state]["actions"][0]
                state = dict(self.graph[state])[action]
            self.assertFalse(self.graph[state])
            self.assertEqual(self.strategy[state]["plies"], 0)

    def test_verifier_rejects_missing_entries_and_bad_policy(self):
        missing = dict(self.strategy)
        del missing[INITIAL_STATE]
        with self.assertRaises(ValueError):
            verify(missing)
        bad = deepcopy(self.strategy)
        bad[INITIAL_STATE]["actions"] = []
        with self.assertRaises(ValueError):
            verify(bad)
        bad = deepcopy(self.strategy)
        bad[((2, 4), (1, 3))]["plies"] = 11
        with self.assertRaises(ValueError):
            verify(bad)

    def test_terminal_and_custom_start(self):
        for start, outcome in [(((0, 0), (1, 1)), "loss"),
                               (((1, 1), (0, 0)), "win")]:
            strategy = solve(start)
            self.assertEqual(strategy, {start: {"outcome": outcome, "plies": 0, "actions": []}})
            verify(strategy, start)
        with self.assertRaises(ValueError):
            solve(((0, 0), (0, 0)))

    def test_exports_preserve_all_records(self):
        with TemporaryDirectory() as directory:
            write_tables(self.strategy, directory)
            with (Path(directory) / "strategy.csv").open(newline="", encoding="utf-8") as source:
                records = list(csv.DictReader(source))
            self.assertEqual(len(records), 192)
            states = set()
            for row in records:
                state = ((int(row["your_h1"]), int(row["your_h2"])),
                         (int(row["opponent_h1"]), int(row["opponent_h2"])))
                states.add(state)
                expected = self.strategy[state]
                self.assertEqual(row["outcome"], expected["outcome"])
                plies = int(row["plies"]) if row["plies"] else None
                self.assertEqual(plies, expected["plies"])
                labels = row["all_optimal_actions"].split("; ") if row["all_optimal_actions"] else []
                self.assertEqual(len(labels), len(expected["actions"]))
                self.assertEqual(row["best_action"], labels[0] if labels else "")
                if state == INITIAL_STATE:
                    self.assertEqual(labels, ["attack H1 -> opponent H1", "self-attack H1 -> H2"])
                if state == ((0, 4), (3, 4)):
                    self.assertIn("split -> (1, 3)", labels)
                    self.assertIn("split -> (2, 2)", labels)
            self.assertEqual(states, set(self.strategy))
            self.assertFalse((Path(directory) / "strategy.json").exists())
            markdown = (Path(directory) / "strategy.md").read_text()
            self.assertEqual(sum(line.startswith("| `") for line in markdown.splitlines()), 192)


if __name__ == "__main__":
    unittest.main()
