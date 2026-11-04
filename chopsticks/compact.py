"""Minimize the optimal policy's decision entries, covering either seat.

Run: python3 chopsticks/compact.py
Only optimization needs SciPy. Reading or following the exported policy does not.
"""

from collections import deque
import csv
from pathlib import Path

if __package__:
    from .chopsticks import INITIAL_STATE, normalize_state
    from .solve import action_label, reachable_graph, solve, verify
else:
    from chopsticks import INITIAL_STATE, normalize_state
    from solve import action_label, reachable_graph, solve, verify


def policy_coverage(policy, strategy, start=INITIAL_STATE):
    """Explore every opponent reply from each seat; reject unsafe/missing moves."""
    start = normalize_state(start)
    graph = reachable_graph(start)
    coverage = {}
    for seat in ("first", "second"):
        root = (start, seat == "first")
        queue = deque([root])
        seen = {root}
        needed = set()
        while queue:
            state, our_turn = queue.popleft()
            moves = graph[state]
            if not moves:
                continue
            if our_turn:
                needed.add(state)
                if state not in policy or policy[state] not in strategy[state]["actions"]:
                    raise ValueError(f"Missing or nonoptimal action at {state}")
                moves = [(a, child) for a, child in moves if a == policy[state]]
            for action, child in moves:
                node = (child, not our_turn)
                if node not in seen:
                    seen.add(node)
                    queue.append(node)
        coverage[seat] = needed
    return coverage


def minimize_policy(strategy=None, start=INITIAL_STATE, time_limit=60):
    """Find a globally smallest deterministic policy among equally optimal moves.

    x[state, action] selects at most one action at each of our decision states.
    z[state] marks a position covered when it is the opponent's turn.
    A selected action requires its opponent successor. A covered opponent state
    requires decisions for EVERY legal reply. Both opening seats are required.
    Minimize sum(x): exactly the number of stored decision entries.
    """
    import numpy as np
    from scipy.optimize import Bounds, LinearConstraint, milp

    start = normalize_state(start)
    if strategy is None:
        strategy = solve(start)
    verify(strategy, start)
    graph = reachable_graph(start)
    active = [s for s in strategy if strategy[s]["actions"]]
    if not graph[start]:
        return {}, {"entries": 0, "lower_bound": 0, "gap": 0.0}
    keys = [(s, a) for s in active for a in strategy[s]["actions"]]
    x = {key: i for i, key in enumerate(keys)}
    z = {s: len(keys) + i for i, s in enumerate(active)}
    count = len(keys) + len(active)
    rows, lower, upper = [], [], []

    def constrain(terms, lo=-np.inf, hi=np.inf):
        row = np.zeros(count)
        for index, value in terms:
            row[index] += value
        rows.append(row)
        lower.append(lo)
        upper.append(hi)

    for state in active:
        selected = [(x[state, a], 1) for a in strategy[state]["actions"]]
        constrain(selected, 1 if state == start else 0, 1)
        for action, child in graph[state]:
            if child not in z:
                continue  # Terminal states need no policy entry.
            # Opponent may make any legal move, including mistakes.
            constrain([(x[child, a], 1) for a in strategy[child]["actions"]]
                      + [(z[state], -1)], lo=0)
            if action in strategy[state]["actions"]:
                constrain([(z[child], 1), (x[state, action], -1)], lo=0)
    constrain([(z[start], 1)], 1, 1)

    objective = np.zeros(count)
    objective[:len(keys)] = 1
    result = milp(
        objective, integrality=np.ones(count), bounds=Bounds(0, 1),
        constraints=LinearConstraint(np.array(rows), lower, upper),
        options={"mip_rel_gap": 0, "time_limit": time_limit},
    )
    if result.status != 0 or result.mip_gap > 1e-8:
        raise RuntimeError(f"Minimum not proved: {result.message}")
    policy = {s: a for (s, a), index in x.items() if result.x[index] > 0.5}
    coverage = policy_coverage(policy, strategy, start)
    required = coverage["first"] | coverage["second"]
    bound = int(round(result.mip_dual_bound))
    if set(policy) != required or len(policy) != bound or abs(result.fun - bound) > 1e-6:
        raise RuntimeError("Optimizer certificate does not match verified coverage")
    return policy, {"entries": len(policy), "lower_bound": bound,
                    "gap": float(result.mip_gap)}


def write_policy(policy, strategy, certificate, directory):
    """Write the compact CSV plus its scope and minimum-size certificate."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    coverage = policy_coverage(policy, strategy)
    required = coverage["first"] | coverage["second"]
    if set(policy) != required:
        raise ValueError("Policy contains unused entries")
    lines = [
        "# Minimum-size optimal policy", "",
        f"**{len(policy)} decision entries**, covering play from either starting seat.", "",
        "Follow the listed action on every turn. The opponent may choose any legal",
        "action, including mistakes. Every selected move is equally optimal under",
        "the complete solver: fastest forced win, draw preservation, or longest",
        "resistance. This is a deterministic policy based only on the current state.", "",
        "The table puts your hands first because it is always your turn at a lookup.",
        "H1/H2 refer to your sorted hands and use the same one-based labels as the CLI.",
        "Empty plies means a draw; one ply is one player's move.", "",
        "## Verification and minimum size", "",
        f"- Selected decision entries: **{certificate['entries']}**.",
        f"- Optimizer's global lower bound: **{certificate['lower_bound']}**.",
        f"- Relative optimization gap: **{certificate['gap']}**.",
        f"- Needed when playing first: **{len(coverage['first'])}**.",
        f"- Needed when playing second: **{len(coverage['second'])}**.", "",
        "An independent graph traversal checks every opponent continuation, confirms",
        "that no lookup is missing, and checks that each selected action is optimal.",
        "The entry count equals the optimization lower bound, so fewer entries are",
        "impossible under this model. The model permits only the complete solver's",
        "equally optimal actions; it does not trade slower wins for a smaller policy.", "",
        "The binary optimization selects at most one action per decision state.",
        "Selecting an action requires coverage of its successor on the opponent's",
        "turn. Covering an opponent position requires decisions after every legal",
        "reply. Both starting seats are required. The objective counts selected",
        "actions, which equals the number of stored decision states. Conversely,",
        "any policy satisfying these requirements gives a feasible assignment,",
        "so the model's lower bound applies to every such policy.", "",
        "The opening remains a draw. Minimum entry count does not necessarily mean",
        "the easiest policy to memorize. Positions caused by your own deviations",
        "are outside this compact policy; use the full table if a lookup is absent.", "",
        "Rebuild with `python3 chopsticks/compact.py` (requires SciPy).", "",
        "| Your hands | Opponent | Outcome | Plies | Action | Needed when playing |",
        "|---|---|---|---:|---|---|",
    ]
    with (directory / "compact-strategy.csv").open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output)
        writer.writerow(["your_h1", "your_h2", "opponent_h1", "opponent_h2",
                         "outcome", "plies", "action", "starting_seat"])
        for state, action in sorted(policy.items()):
            row = strategy[state]
            seats = "; ".join(seat for seat, states in coverage.items() if state in states)
            label = action_label(state, action)
            writer.writerow([*state[0], *state[1], row["outcome"], row["plies"], label, seats])
            distance = row["plies"] if row["plies"] is not None else "—"
            lines.append(f"| `{state[0]}` | `{state[1]}` | {row['outcome']} | {distance} | {label} | {seats} |")
    (directory / "compact-strategy.md").write_text("\n".join(lines) + "\n")


def main():
    strategy = solve()
    baseline = {s: row["actions"][0] for s, row in strategy.items() if row["actions"]}
    coverage = policy_coverage(baseline, strategy)
    print("First-action policy entries:", len(coverage["first"] | coverage["second"]))
    policy, certificate = minimize_policy(strategy)
    print("Minimum-size certificate:", certificate)
    directory = Path(__file__).resolve().parent
    write_policy(policy, strategy, certificate, directory)
    print(f"Wrote {directory / 'compact-strategy.csv'}")
    print(f"Wrote {directory / 'compact-strategy.md'}")


if __name__ == "__main__":
    main()
