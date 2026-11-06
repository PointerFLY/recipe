"""Build the dependency-free Pages site: python -m chopsticks.export_web."""

import argparse
import json
from pathlib import Path
import shutil

from .chopsticks import legal_moves
from .solve import solve


def strategy_data():
    """Export the full graph, including every legal and equally optimal action."""
    return {
        "version": 1,
        "states": {
            "".join(str(n) for hand in state for n in hand): {
                **entry,
                "moves": [{"action": action, "next": child}
                          for action, child in legal_moves(state)],
            }
            for state, entry in solve().items()
        },
    }


def build(output):
    source = Path(__file__).resolve().parent
    output = Path(output)
    # Copy only public game files, never repository files or generated research.
    game = output / "chopsticks"
    game.mkdir(parents=True, exist_ok=True)
    for name in ("index.html", "game.mjs", "engine.mjs", "web.css"):
        shutil.copyfile(source / "web" / name, game / name)
    assets = game / "assets"
    assets.mkdir(exist_ok=True)
    for name in ("game.css", "hands.png"):
        shutil.copyfile(source / "assets" / name, assets / name)
    (game / "strategy.json").write_text(
        json.dumps(strategy_data(), separators=(",", ":")) + "\n", encoding="utf-8"
    )
    (output / ".nojekyll").touch()
    (output / "index.html").write_text(
        '<!doctype html><html lang="en"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Recipe games</title><h1>Recipe games</h1>'
        '<a href="./chopsticks/">Play Chopsticks Club</a></html>\n', encoding="utf-8"
    )
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("build/pages"))
    args = parser.parse_args()
    print(f"Built {build(args.output)}/chopsticks/")


if __name__ == "__main__":
    main()
