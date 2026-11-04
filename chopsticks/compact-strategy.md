# Minimum-size optimal policy

**45 decision entries**, covering play from either starting seat.

Follow the listed action on every turn. The opponent may choose any legal
action, including mistakes. Every selected move is equally optimal under
the complete solver: fastest forced win, draw preservation, or longest
resistance. This is a deterministic policy based only on the current state.

The table puts your hands first because it is always your turn at a lookup.
H1/H2 refer to your sorted hands and use the same one-based labels as the CLI.
Empty plies means a draw; one ply is one player's move.

## Verification and minimum size

- Selected decision entries: **45**.
- Optimizer's global lower bound: **45**.
- Relative optimization gap: **0.0**.
- Needed when playing first: **45**.
- Needed when playing second: **31**.

An independent graph traversal checks every opponent continuation, confirms
that no lookup is missing, and checks that each selected action is optimal.
The entry count equals the optimization lower bound, so fewer entries are
impossible under this model. The model permits only the complete solver's
equally optimal actions; it does not trade slower wins for a smaller policy.

The binary optimization selects at most one action per decision state.
Selecting an action requires coverage of its successor on the opponent's
turn. Covering an opponent position requires decisions after every legal
reply. Both starting seats are required. The objective counts selected
actions, which equals the number of stored decision states. Conversely,
any policy satisfying these requirements gives a feasible assignment,
so the model's lower bound applies to every such policy.

The opening remains a draw. Minimum entry count does not necessarily mean
the easiest policy to memorize. Positions caused by your own deviations
are outside this compact policy; use the full table if a lookup is absent.

Rebuild with `python3 chopsticks/compact.py` (requires SciPy).

| Your hands | Opponent | Outcome | Plies | Action | Needed when playing |
|---|---|---|---:|---|---|
| `(0, 1)` | `(1, 4)` | win | 9 | attack H2 -> opponent H2 | first; second |
| `(0, 2)` | `(0, 1)` | win | 7 | split -> (1, 1) | first; second |
| `(0, 2)` | `(1, 1)` | draw | — | split -> (1, 1) | first |
| `(0, 2)` | `(1, 4)` | draw | — | attack H2 -> opponent H2 | first; second |
| `(0, 3)` | `(0, 1)` | draw | — | split -> (1, 2) | first; second |
| `(0, 3)` | `(1, 1)` | draw | — | split -> (1, 2) | first |
| `(0, 3)` | `(1, 4)` | win | 3 | attack H2 -> opponent H2 | first; second |
| `(0, 4)` | `(0, 1)` | win | 1 | attack H2 -> opponent H2 | first; second |
| `(0, 4)` | `(1, 4)` | draw | — | split -> (2, 2) | first; second |
| `(1, 1)` | `(1, 1)` | draw | — | self-attack H1 -> H2 | first |
| `(1, 1)` | `(1, 2)` | draw | — | attack H1 -> opponent H2 | first; second |
| `(1, 1)` | `(1, 4)` | win | 7 | attack H1 -> opponent H2 | first; second |
| `(1, 1)` | `(3, 4)` | draw | — | attack H1 -> opponent H2 | first; second |
| `(1, 2)` | `(0, 1)` | win | 5 | self-attack H2 -> H1 | first; second |
| `(1, 2)` | `(0, 4)` | win | 1 | attack H1 -> opponent H2 | first |
| `(1, 2)` | `(1, 1)` | draw | — | self-attack H2 -> H1 | first; second |
| `(1, 2)` | `(1, 2)` | draw | — | attack H2 -> opponent H2 | first |
| `(1, 2)` | `(1, 3)` | draw | — | attack H2 -> opponent H2 | first; second |
| `(1, 3)` | `(0, 1)` | draw | — | self-attack H2 -> H1 | first; second |
| `(1, 3)` | `(1, 1)` | draw | — | self-attack H2 -> H1 | first |
| `(1, 3)` | `(1, 4)` | win | 5 | attack H2 -> opponent H2 | first |
| `(1, 4)` | `(0, 1)` | win | 1 | attack H2 -> opponent H2 | first; second |
| `(1, 4)` | `(0, 3)` | win | 1 | attack H2 -> opponent H2 | first; second |
| `(1, 4)` | `(0, 4)` | win | 1 | attack H1 -> opponent H2 | first; second |
| `(1, 4)` | `(1, 3)` | draw | — | attack H1 -> opponent H2 | first; second |
| `(2, 2)` | `(0, 1)` | win | 9 | self-attack H1 -> H2 | first; second |
| `(2, 2)` | `(0, 4)` | win | 1 | attack H1 -> opponent H2 | first; second |
| `(2, 2)` | `(1, 1)` | draw | — | self-attack H1 -> H2 | first |
| `(2, 2)` | `(1, 4)` | win | 5 | attack H1 -> opponent H2 | first |
| `(2, 3)` | `(0, 1)` | win | 3 | self-attack H2 -> H1 | first |
| `(2, 3)` | `(1, 2)` | win | 5 | attack H2 -> opponent H2 | first; second |
| `(2, 3)` | `(1, 4)` | win | 5 | attack H1 -> opponent H2 | first; second |
| `(2, 4)` | `(0, 1)` | win | 1 | attack H2 -> opponent H2 | first; second |
| `(2, 4)` | `(1, 1)` | win | 9 | attack H2 -> opponent H1 | first; second |
| `(2, 4)` | `(1, 2)` | win | 9 | attack H2 -> opponent H2 | first |
| `(2, 4)` | `(1, 4)` | win | 9 | attack H1 -> opponent H2 | first; second |
| `(3, 3)` | `(0, 1)` | win | 3 | self-attack H1 -> H2 | first; second |
| `(3, 3)` | `(0, 4)` | win | 1 | attack H1 -> opponent H2 | first; second |
| `(3, 3)` | `(1, 1)` | draw | — | attack H1 -> opponent H1 | first; second |
| `(3, 4)` | `(0, 1)` | win | 1 | attack H2 -> opponent H2 | first; second |
| `(3, 4)` | `(1, 1)` | draw | — | attack H2 -> opponent H1 | first |
| `(3, 4)` | `(1, 2)` | draw | — | attack H2 -> opponent H2 | first |
| `(3, 4)` | `(1, 4)` | draw | — | attack H2 -> opponent H2 | first; second |
| `(4, 4)` | `(0, 1)` | win | 1 | attack H1 -> opponent H2 | first; second |
| `(4, 4)` | `(1, 1)` | win | 3 | attack H1 -> opponent H1 | first |
