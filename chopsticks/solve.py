"""Build, verify, and minimize a perfect-play strategy.

Run: uv run python chopsticks/solve.py
Writes full and compact tables in strategy.md; minimization requires SciPy.
Use --full-only to generate just the full table with the standard library.
All outcomes are relative to the player to move; one ply is one player's move.
Infinite play counts as a draw. No game rules or repetition limits are changed.
"""

import argparse
from collections import Counter, defaultdict, deque
from pathlib import Path

if __package__:
    from .chopsticks import INITIAL_STATE, legal_moves, normalize_state
else:
    from chopsticks import INITIAL_STATE, legal_moves, normalize_state


def reachable_graph(start=INITIAL_STATE):
    """Map each reachable state to its explicit (action, next_state) moves."""
    start = normalize_state(start)
    if start == ((0, 0), (0, 0)):
        raise ValueError("Both players cannot be dead")
    graph = {}
    queue = deque([start])
    seen = {start}
    while queue:
        state = queue.popleft()
        graph[state] = legal_moves(state)
        for action, child in graph[state]:
            if child not in seen:
                seen.add(child)
                queue.append(child)
    return graph


def solve(start=INITIAL_STATE):
    """Return state -> {outcome, plies, actions}, keeping all optimal actions.

    Prefer the fastest forced win, then a draw, then the longest forced loss.
    The first optimal action is a deterministic choice when several tie.
    """
    graph = reachable_graph(start)
    parents = defaultdict(set)
    remaining = {}
    values = {}
    longest = defaultdict(int)
    for state, moves in graph.items():
        children = {child for action, child in moves}
        remaining[state] = len(children)
        for child in children:
            parents[child].add(state)
        if not moves:
            values[state] = ("loss" if state[0] == (0, 0) else "win", 0)

    # FIFO processes solved positions in increasing distance from the end.
    queue = deque(sorted(values))
    while queue:
        child = queue.popleft()
        outcome, plies = values[child]
        for parent in sorted(parents[child]):
            if parent in values:
                continue
            if outcome == "loss":
                # The first losing child found gives the shortest forced win.
                values[parent] = ("win", plies + 1)
            else:
                remaining[parent] -= 1
                longest[parent] = max(longest[parent], plies)
                if remaining[parent]:
                    continue
                # Every distinct child wins for the opponent.
                values[parent] = ("loss", longest[parent] + 1)
            queue.append(parent)

    for state in graph:
        values.setdefault(state, ("draw", None))

    strategy = {}
    for state, moves in sorted(graph.items()):
        outcome, plies = values[state]
        actions = []
        for action, child in moves:
            child_outcome, child_plies = values[child]
            if outcome == "draw":
                optimal = child_outcome == "draw"
            else:
                optimal = child_outcome != outcome and child_plies is not None
                optimal = optimal and child_plies + 1 == plies
            if optimal:
                actions.append(action)
        strategy[state] = {"outcome": outcome, "plies": plies, "actions": actions}
    return strategy


def verify(strategy, start=INITIAL_STATE):
    """Check graph coverage, optimal distances, draw closure, and every action.

    Finite distances certify progress to a terminal state. For every draw,
    there must be a drawing continuation and no move to an opponent's loss.
    """
    graph = reachable_graph(start)
    if set(strategy) != set(graph):
        raise ValueError("Strategy does not cover exactly the reachable states")
    for state, moves in graph.items():
        row = strategy[state]
        outcome, plies = row["outcome"], row["plies"]
        children = [strategy[child] for action, child in moves]
        expected = []
        if not moves:
            terminal = "loss" if state[0] == (0, 0) else "win"
            valid = outcome == terminal and plies == 0
        elif outcome == "win":
            losses = [c["plies"] for c in children if c["outcome"] == "loss"]
            valid = (type(plies) is int and plies > 0 and bool(losses)
                     and plies == 1 + min(losses))
            expected = [a for a, c in moves if strategy[c]["outcome"] == "loss"
                        and strategy[c]["plies"] + 1 == plies]
        elif outcome == "loss":
            valid = (type(plies) is int and plies > 0
                     and all(c["outcome"] == "win" for c in children)
                     and plies == 1 + max(c["plies"] for c in children))
            expected = [a for a, c in moves if strategy[c]["outcome"] == "win"
                        and strategy[c]["plies"] + 1 == plies]
        elif outcome == "draw":
            valid = (plies is None and any(c["outcome"] == "draw" for c in children)
                     and all(c["outcome"] != "loss" for c in children))
            expected = [a for a, c in moves if strategy[c]["outcome"] == "draw"]
        else:
            valid = False
        if not valid or row["actions"] != expected:
            raise ValueError(f"Invalid strategy entry at {state}: {row}")


def action_label(state, action):
    """Describe an action using the CLI's one-based hand labels."""
    if action[0] == "split":
        left = action[1]
        return f"split -> ({left}, {sum(state[0]) - left})"
    kind, source, target = action
    label = "attack" if kind == "attack" else "self-attack"
    destination = "opponent " if kind == "attack" else ""
    return f"{label} H{source + 1} -> {destination}H{target + 1}"


def write_tables(strategy, directory, policy=None, certificate=None):
    """Write the full strategy and optional compact policy in one Markdown file."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    summary = dict(sorted(Counter(row["outcome"] for row in strategy.values()).items()))
    lines = [
        "# Chopsticks perfect-play strategy", "",
        "Generated by `uv run python chopsticks/solve.py` using the current game rules.", "",
        "## Complete strategy", "",
        "The player to move is first; each hand pair is sorted. Outcomes are for",
        "that player. One ply is one player's move; infinite play is a draw.", "",
        "Action indices are **zero-based**, referring to the sorted hands before",
        "the move: `('attack', source, target)`, `('self_attack', source, target)`,",
        "or `('split', smaller_count)`. The opponent moves next.", "",
        "Winning actions minimize plies against optimal defense. Losing actions",
        "maximize plies. Drawing actions preserve the draw. All optimal actions",
        "are listed; choosing the first gives a deterministic policy. Terminal",
        "states have no action. Distinct actions may lead to the same result.", "",
        f"Reachable: **{len(strategy)}**. Outcomes (including terminal states): **{summary}**.", "",
        "| Your hands | Opponent | Outcome | Plies | Best action | All optimal actions |",
        "|---|---|---|---:|---|---|",
    ]
    for state, row in strategy.items():
        best = row["actions"][0] if row["actions"] else None
        actions = "; ".join(f"`{a}`" for a in row["actions"]) or "—"
        distance = row["plies"] if row["plies"] is not None else "—"
        first = f"`{best}`" if best else "—"
        lines.append(f"| `{state[0]}` | `{state[1]}` | {row['outcome']} | {distance} | {first} | {actions} |")
    if policy is not None:
        lines.extend(["", policy_markdown(policy, strategy, certificate)])
    (directory / "strategy.md").write_text("\n".join(lines) + "\n")


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


def policy_markdown(policy, strategy, certificate):
    """Render the compact policy section with its minimum-size certificate."""
    coverage = policy_coverage(policy, strategy)
    required = coverage["first"] | coverage["second"]
    if set(policy) != required:
        raise ValueError("Policy contains unused entries")
    lines = [
        "## Minimum-size optimal policy", "",
        f"**{len(policy)} decision entries**, covering play from either starting seat.", "",
        "Follow the listed action on every turn. The opponent may choose any legal",
        "action, including mistakes. Every selected move is equally optimal under",
        "the complete solver: fastest forced win, draw preservation, or longest",
        "resistance. This is a deterministic policy based only on the current state.", "",
        "The table puts your hands first because it is always your turn at a lookup.",
        "H1/H2 refer to your sorted hands and use the same one-based labels as the CLI.",
        "A dash in plies means a draw; one ply is one player's move.", "",
        "### Verification and minimum size", "",
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
        "Rebuild with `uv run python chopsticks/solve.py` (requires SciPy).", "",
        "| Your hands | Opponent | Outcome | Plies | Action | Needed when playing |",
        "|---|---|---|---:|---|---|",
    ]
    for state, action in sorted(policy.items()):
        row = strategy[state]
        seats = "; ".join(seat for seat, states in coverage.items() if state in states)
        label = action_label(state, action)
        distance = row["plies"] if row["plies"] is not None else "—"
        lines.append(f"| `{state[0]}` | `{state[1]}` | {row['outcome']} | {distance} | {label} | {seats} |")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build full and compact Chopsticks strategies.")
    parser.add_argument("--full-only", action="store_true",
                        help="skip policy minimization; needs only the standard library")
    args = parser.parse_args(argv)
    strategy = solve()
    verify(strategy)
    directory = Path(__file__).resolve().parent
    policy = certificate = None
    active = [row for row in strategy.values() if row["actions"]]
    print(f"Verified {len(strategy)} reachable states; {len(active)} need an action.")
    print("Nonterminal outcomes:", dict(sorted(Counter(r["outcome"] for r in active).items())))
    print("Opening:", strategy[INITIAL_STATE])
    print("Maximum finite plies:", max(r["plies"] for r in strategy.values() if r["plies"] is not None))
    if not args.full_only:
        baseline = {s: row["actions"][0] for s, row in strategy.items() if row["actions"]}
        coverage = policy_coverage(baseline, strategy)
        print("First-action policy entries:", len(coverage["first"] | coverage["second"]))
        policy, certificate = minimize_policy(strategy)
        print("Minimum-size certificate:", certificate)
    write_tables(strategy, directory, policy, certificate)
    print(f"Wrote {directory / 'strategy.md'}")


if __name__ == "__main__":
    main()
