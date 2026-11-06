# Chopsticks

The numbered rules are at the top of `chopsticks.py`. States put the player to
move first, with each player's two hands sorted. Every move swaps the players.

For a human-oriented summary, see [the compact strategy guide](strategy-guide.md).

For a smaller exact lookup table, use the [45-entry policy](strategy.md#minimum-size-optimal-policy)
and its [minimum-size explanation](strategy.md#minimum-size-optimal-policy). It selects one optimal
action per decision state, covers either starting seat, and handles every legal
opponent response. Follow the selected actions consistently; your own deviations
can lead outside the compact table.

Play locally:

```sh
uv run python chopsticks/chopsticks.py
```

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
