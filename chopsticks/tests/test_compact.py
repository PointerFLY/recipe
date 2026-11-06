"""Verify minimum size and closure under every opponent continuation."""

from importlib.util import find_spec
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from chopsticks.chopsticks import INITIAL_STATE, legal_moves
from chopsticks.solve import minimize_policy, policy_coverage, write_tables
from chopsticks.solve import action_label, solve


@unittest.skipUnless(find_spec("scipy"), "Policy minimization requires SciPy")
class CompactPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.strategy = solve()
        cls.policy, cls.certificate = minimize_policy(cls.strategy)

    def test_minimum_certificate_and_baseline(self):
        self.assertEqual(self.certificate, {"entries": 45, "lower_bound": 45, "gap": 0.0})
        self.assertEqual(len(self.policy), 45)
        baseline = {s: r["actions"][0] for s, r in self.strategy.items() if r["actions"]}
        coverage = policy_coverage(baseline, self.strategy)
        self.assertEqual(len(coverage["first"] | coverage["second"]), 109)

    def test_independent_two_move_traversal_covers_every_reply(self):
        # Explore a whole round at a time instead of the implementation's
        # turn-labelled graph. Opponent moves are never restricted to optimal.
        required = set()
        for first in (True, False):
            pending = [INITIAL_STATE] if first else [c for a, c in legal_moves(INITIAL_STATE)]
            seen = set()
            while pending:
                state = pending.pop()
                if state in seen or not legal_moves(state):
                    continue
                seen.add(state)
                required.add(state)
                self.assertIn(state, self.policy)
                self.assertIn(self.policy[state], self.strategy[state]["actions"])
                self.assertNotEqual(self.strategy[state]["outcome"], "loss")
                opponent = dict(legal_moves(state))[self.policy[state]]
                if not legal_moves(opponent):
                    self.assertEqual(opponent[0], (0, 0))  # We won.
                    continue
                for action, child in legal_moves(opponent):
                    self.assertNotEqual(child[0], (0, 0))  # Opponent cannot win.
                    pending.append(child)
        self.assertEqual(required, set(self.policy))

    def test_missing_or_nonoptimal_move_is_rejected(self):
        missing = dict(self.policy)
        del missing[INITIAL_STATE]
        with self.assertRaises(ValueError):
            policy_coverage(missing, self.strategy)
        bad = dict(self.policy)
        bad[INITIAL_STATE] = ("split", 1)
        with self.assertRaises(ValueError):
            policy_coverage(bad, self.strategy)

    def test_exports_match_the_selected_policy(self):
        with TemporaryDirectory() as directory:
            write_tables(self.strategy, directory, self.policy, self.certificate)
            text = (Path(directory) / "strategy.md").read_text()
            self.assertIn("global lower bound: **45**", text)
            full, compact = text.split("## Minimum-size optimal policy", 1)
            self.assertEqual(sum(line.startswith("| `") for line in full.splitlines()), 192)
            rows = [line for line in compact.splitlines() if line.startswith("| `")]
            self.assertEqual(len(rows), 45)
            coverage = policy_coverage(self.policy, self.strategy)
            for line, (state, action) in zip(rows, sorted(self.policy.items())):
                row = self.strategy[state]
                cells = [cell.strip() for cell in line.split("|")[1:-1]]
                self.assertEqual(cells[:3], [f"`{state[0]}`", f"`{state[1]}`", row["outcome"]])
                self.assertEqual(cells[3], str(row["plies"]) if row["plies"] is not None else "—")
                self.assertEqual(cells[4], action_label(state, action))
                self.assertEqual(cells[5], "; ".join(seat for seat, states in coverage.items() if state in states))
            self.assertEqual({p.name for p in Path(directory).iterdir()}, {"strategy.md"})

    def test_terminal_start_needs_no_entries(self):
        start = ((0, 0), (1, 1))
        policy, certificate = minimize_policy(start=start)
        self.assertEqual(policy, {})
        self.assertEqual(certificate["entries"], 0)
        self.assertEqual(policy_coverage(policy, solve(start), start), {"first": set(), "second": set()})


if __name__ == "__main__":
    unittest.main()
