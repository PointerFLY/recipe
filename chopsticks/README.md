# Chopsticks

The numbered rules are at the top of `chopsticks.py`. States put the player to
move first, with each player's two hands sorted. Every move swaps the players.

For a human-oriented summary, see [the compact strategy guide](win.md).

For a smaller exact lookup table, use the [45-entry policy](strategy.md#minimum-size-optimal-policy)
and its [minimum-size explanation](strategy.md#minimum-size-optimal-policy). It selects one optimal
action per decision state, covers either starting seat, and handles every legal
opponent response. Follow the selected actions consistently; your own deviations
can lead outside the compact table.

Play locally:

```sh
uv run python chopsticks/chopsticks.py
```

Play the static browser game (the GitHub Pages version):

```sh
python3 -m chopsticks.export_web
python3 -m http.server 8000 --directory build/pages
```

Open <http://localhost:8000/chopsticks/>. This version needs only Python's
standard library to build and a browser with JavaScript to play. The build
exports the Python solver's complete strategy and legal transitions to JSON;
the browser keeps hand positions stable and plays without a Python server.
The hand images, delayed AI turn, split actions, rules, restart, and suboptimal
percentage control are shared in behavior with the local NiceGUI version.
The **Buddy first** toggle beside **New game** chooses who opens the next round:
on for Buddy, off for you (the default). Changing it takes effect when you press
**New game**; it stays selected between rounds.

### GitHub Pages

The intended public URL is <https://pointerfly.github.io/recipe/chopsticks/>.
The `.github/workflows/pages.yml` workflow tests and builds the static site,
then publishes `build/pages` on pushes affecting Chopsticks on `main`.
Pull requests to `main` run the same checks without publishing. Generated
files stay in the ignored `build/` directory; do not commit them.

After committing and pushing these changes to `main` (or merging them from
a development branch), select **Settings → Pages → Build and deployment →
Source → GitHub Actions** in the repository. If the initial run happened before
Pages was enabled, use **Actions → Deploy Chopsticks to GitHub Pages → Run
workflow**, choosing `main`. The workflow's deployment link points to the
game's `/chopsticks/` path. All asset URLs are relative to support `/recipe/`.

To verify the browser adapter against every reachable physical board, plus
AI difficulty and restart behavior (requires Node.js):

```sh
python3 -m unittest chopsticks.tests.test_web_game -v
```

Play the NiceGUI browser game locally:

```sh
uv sync
uv run python chopsticks/run_ui.py
uv run python chopsticks/run_ui.py --suboptimal-percent 20
```

The app opens at `http://127.0.0.1:8080` ready for your first move.
Use the **Buddy first** toggle beside **New game** to choose who opens the next
round: on means Buddy starts, off means you start. Press **New game** to apply
the setting and reset the board. Your hands always stay at the bottom, and
Buddy pauses to think before its opening move.

Pick one of your hand pictures, then
tap a highlighted target: Buddy's hand or your other hand. Split buttons appear
when one hand rests and the other has 2–4 fingers. Hands keep their physical
screen positions while the adapter translates to the solver's sorted indices.

The on-screen **Suboptimal percentage** defaults to **0%** (optimal play).
Set 0–100 to choose the chance of a random nonoptimal AI move, using the same
behavior as `play_ai.py`. If every legal move is optimal, Buddy plays optimally.
The card contains only the percentage input. Use `--suboptimal-percent 20`
to change its initial value. Each browser page has its own setting. A turn
uses the percentage selected when the human makes that move.

New game immediately starts a fresh round, keeping the toggle and AI percentage.
Restarting also cancels a pending AI reply, including Buddy's opening move.
Each browser page has its own game; refreshing the page starts over. Perfect play can repeat indefinitely.

Use `--port 8081` for another port or `--no-show` to skip automatically opening
the browser. The default binds only to your computer. To play from another
device on your network, start with `--host 0.0.0.0` and use your computer's LAN
address. This small version includes playing, splitting, restart, and rules;
there are no accounts or saved games.

Photographic-style hand images were generated for this project; their brief
and finger-count ordering are documented in [assets/README.md](assets/README.md).
The automated checks include exhaustive rules-adapter tests and NiceGUI's Python
user simulation for selection, taps, AI replies, CLI settings, and restart.

Play against an optimal computer (you move first by default):

```sh
uv run python chopsticks/play_ai.py
uv run python chopsticks/play_ai.py --player 2
uv run python chopsticks/play_ai.py --suboptimal-percent 20
```

`--suboptimal-percent` accepts 0–100 (including decimals) and defaults to 0.
On each AI turn, this is the chance of choosing a random legal move outside
the solver's optimal choices. If every legal move is optimal, the AI keeps its
usual optimal choice. A suboptimal move can also mean a slower win or a faster
loss, rather than a different outcome.

The computer solves the full reachable graph once at startup and chooses one
equally optimal action on each turn. It forces the fastest win when possible,
preserves draws, and delays unavoidable losses. The same aligned move display
shows what the computer chose. This mode needs only Python's standard library,
with no saved tables or SciPy dependency. Perfect play can repeat indefinitely;
enter `q` on your turn to quit. The original two-human mode is unchanged.

Generate and verify the complete strategy and minimum-size policy together in
`strategy.md` alongside the solver:

```sh
uv sync
uv run python chopsticks/solve.py
```

Only policy minimization needs SciPy. To write `strategy.md` with only the
complete strategy using Python's standard library:

```sh
uv run python chopsticks/solve.py --full-only
```

Dependencies are managed for the whole repository in the root `pyproject.toml`
and `uv.lock`. Playing the game and using the saved tables do not need SciPy.

The arbitrary first-action policy requires 109 decision entries across the two
starting seats. Binary optimization reduces this to **45**, with a matching
global lower bound and zero optimality gap. It counts unique decision states,
not actions, opponent turns, or terminal positions. Choices remain optimal for
outcome and distance: it does not accept slower wins to reduce table size.
The minimum is for a deterministic policy depending only on the current state
and covering both seats, not a claim about every possible memory aid or strategy
representation. A separate traversal verifies every opponent continuation.

The solver explores every reachable position and works backward from terminal
losses. A position wins if it can give the opponent a loss; it loses if every
move gives the opponent a win. Positions remaining after those deductions stop
are draws, treating infinite play as a draw. The game itself has no automatic
repetition limit.

The table contains all equally optimal actions. Winning actions force the
fastest victory against optimal defense; losing actions delay defeat as long
as possible. Drawing actions preserve the draw. `plies` counts individual
player moves, is zero at a terminal state, and is `None` for a draw.

The verifier checks coverage, terminal outcomes, optimal distances, and all
recommended actions. Every drawing position must have a drawing continuation
and no move to an opponent's loss. Finite distances certify progress to a
terminal state. Tests also check outcomes using a separate round-by-round
calculation.

Use the table from Python (run from the repository root):

```python
from chopsticks.chopsticks import INITIAL_STATE, normalize_state
from chopsticks.solve import solve

strategy = solve()
row = strategy[normalize_state(INITIAL_STATE)]
print(row)  # outcome, plies, and all optimal actions

best_action = {
    state: row["actions"][0] if row["actions"] else None
    for state, row in strategy.items()
}
```

Action indices are zero-based and refer to the sorted hands before the move:

- `("attack", source, target)`: attack the opponent.
- `("self_attack", source, target)`: attack your other live hand.
- `("split", smaller_count)`: revive your dead hand by splitting.

The Markdown table lists your hands, the opponent's hands, outcome, plies,
one deterministic best action, and all equally optimal actions. Action tuples
use zero-based indices. Draws show a dash for plies; terminal states have zero
plies and no actions. The compact table uses readable, one-based H1/H2 labels
matching the CLI.
Distinct actions that reach the same position remain separate actions; the
solver counts distinct child positions when propagating losses.

The current rules give 192 reachable positions: 79 wins, 15 ongoing losses,
84 draws, and 14 terminal losses. The opening is a draw; either opening action
preserves it. Regenerate the tables after changing the rules. Only positions
reachable from the chosen starting state are included; `solve(start)` can
analyze a different start.

Run all checks:

```sh
uv run python -m unittest discover -s chopsticks/tests -v
```
