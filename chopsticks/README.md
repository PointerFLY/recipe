# Chopsticks

The numbered rules are at the top of `chopsticks.py`. States put the player to
move first, with each player's two hands sorted. Every move swaps the players.

For a human-oriented summary, see [the compact strategy guide](strategy-guide.md).

For a smaller exact lookup table, use the [45-entry policy](compact-strategy.csv)
and its [minimum-size explanation](compact-strategy.md). It selects one optimal
action per decision state, covers either starting seat, and handles every legal
opponent response. Follow the selected actions consistently; your own deviations
can lead outside the compact table.

Play locally:

```sh
python3 chopsticks/chopsticks.py
```

Play against an optimal computer (you move first by default):

```sh
python3 chopsticks/play_ai.py
python3 chopsticks/play_ai.py --player 2
```

The computer solves the full reachable graph once at startup and chooses one
equally optimal action on each turn. It forces the fastest win when possible,
preserves draws, and delays unavoidable losses. The same aligned move display
shows what the computer chose. This mode needs only Python's standard library,
with no CSV files or SciPy dependency. Perfect play can repeat indefinitely;
enter `q` on your turn to quit. The original two-human mode is unchanged.

Generate and verify the complete strategy, then write `strategy.csv` and
`strategy.md` alongside the solver:

```sh
python3 chopsticks/solve.py
```

Minimize the policy by choosing between equally optimal actions:

```sh
python3 -m pip install -r chopsticks/requirements.txt
python3 chopsticks/compact.py
```

Only the minimizer needs SciPy; playing the game, generating the complete
strategy, and using the saved tables do not. The minimizer writes
`compact-strategy.csv` and `compact-strategy.md`.

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

The CSV has separate numeric columns for your H1/H2 and the opponent's H1/H2,
followed by outcome, plies, one deterministic best action, and all optimal
actions separated by semicolons. Actions use readable, one-based H1/H2 labels
matching the CLI, such as `attack H1 -> opponent H2` or `split -> (1, 3)`.
Draws have a blank plies cell; terminal losses have zero plies and blank actions.
The Python and Markdown action tuples above use zero-based indices.
Distinct actions that reach the same position remain separate actions; the
solver counts distinct child positions when propagating losses.

The current rules give 192 reachable positions: 79 wins, 15 ongoing losses,
84 draws, and 14 terminal losses. The opening is a draw; either opening action
preserves it. Regenerate the tables after changing the rules. Only positions
reachable from the chosen starting state are included; `solve(start)` can
analyze a different start.

Run all checks:

```sh
python3 -m unittest discover -s chopsticks -v
```
