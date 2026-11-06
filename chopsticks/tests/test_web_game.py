"""Exhaustive browser/Python parity plus static publication checks (no pip needed)."""

import itertools
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from chopsticks.chopsticks import legal_moves
from chopsticks.export_web import build, strategy_data

ROOT = Path(__file__).resolve().parents[2]


class WebGameTests(unittest.TestCase):
    def test_export_and_site_layout(self):
        data = strategy_data()
        self.assertEqual(data["version"], 1)
        self.assertEqual(data["states"]["1111"]["outcome"], "draw")
        with tempfile.TemporaryDirectory() as directory:
            output = build(Path(directory) / "recipe")
            files = {str(path.relative_to(output)) for path in output.rglob("*") if path.is_file()}
            self.assertEqual(files, {
                ".nojekyll", "index.html", "chopsticks/index.html", "chopsticks/game.mjs",
                "chopsticks/engine.mjs", "chopsticks/web.css", "chopsticks/strategy.json",
                "chopsticks/assets/game.css", "chopsticks/assets/hands.png",
            })
            self.assertEqual(json.loads((output / "chopsticks/strategy.json").read_text()),
                             json.loads(json.dumps(data)))
            html = (output / "chopsticks/index.html").read_text()
            for path in ("./assets/game.css", "./web.css", "./game.mjs"):
                self.assertIn(path, html)
                self.assertTrue((output / "chopsticks" / path).is_file())

    @unittest.skipUnless(shutil.which("node"), "Node.js is required for browser parity checks")
    def test_browser_engine_matches_python_for_every_reachable_physical_board(self):
        data = strategy_data()
        cases = []
        for key in data["states"]:
            state = (tuple(map(int, key[:2])), tuple(map(int, key[2:])))
            expected = [{"action": action, "next": child} for action, child in legal_moves(state)]
            for own in set(itertools.permutations(state[0])):
                for other in set(itertools.permutations(state[1])):
                    for player in (0, 1):
                        cases.append({"hands": (own, other) if player == 0 else (other, own),
                                      "player": player, "moves": expected})
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / "fixture.json"
            fixture.write_text(json.dumps({"strategy": data, "cases": cases}))
            result = subprocess.run(
                ["node", str(ROOT / "chopsticks/tests/web_game.test.mjs"), str(fixture)],
                capture_output=True, text=True, cwd=ROOT,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn(f"Verified {len(cases)} physical boards", result.stdout)


if __name__ == "__main__":
    unittest.main()
