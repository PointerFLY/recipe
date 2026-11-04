"""Build and verify a perfect-play strategy using retrograde analysis.

Run: python3 chopsticks/solve.py
All outcomes are relative to the player to move; one ply is one player's move.
Infinite play counts as a draw. No game rules or repetition limits are changed.
"""

from collections import Counter, defaultdict, deque
import csv
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


def write_tables(strategy, directory):
    """Export readable CSV and Markdown strategy tables."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    summary = dict(sorted(Counter(row["outcome"] for row in strategy.values()).items()))
    records = []
    lines = [
        "# Chopsticks perfect-play strategy", "",
        "Generated by `python3 chopsticks/solve.py` using the current game rules.", "",
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
        labels = [action_label(state, action) for action in row["actions"]]
        records.append({
            "your_h1": state[0][0], "your_h2": state[0][1],
            "opponent_h1": state[1][0], "opponent_h2": state[1][1],
            "outcome": row["outcome"], "plies": row["plies"],
            "best_action": labels[0] if labels else "",
            "all_optimal_actions": "; ".join(labels),
        })
        actions = "; ".join(f"`{a}`" for a in row["actions"]) or "—"
        distance = row["plies"] if row["plies"] is not None else "—"
        first = f"`{best}`" if best else "—"
        lines.append(f"| `{state[0]}` | `{state[1]}` | {row['outcome']} | {distance} | {first} | {actions} |")
    with (directory / "strategy.csv").open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=[
            "your_h1", "your_h2", "opponent_h1", "opponent_h2",
            "outcome", "plies", "best_action", "all_optimal_actions",
        ])
        writer.writeheader()
        writer.writerows(records)
    (directory / "strategy.md").write_text("\n".join(lines) + "\n")


def main():
    strategy = solve()
    verify(strategy)
    directory = Path(__file__).resolve().parent
    write_tables(strategy, directory)
    active = [row for row in strategy.values() if row["actions"]]
    print(f"Verified {len(strategy)} reachable states; {len(active)} need an action.")
    print("Nonterminal outcomes:", dict(sorted(Counter(r["outcome"] for r in active).items())))
    print("Opening:", strategy[INITIAL_STATE])
    print("Maximum finite plies:", max(r["plies"] for r in strategy.values() if r["plies"] is not None))
    print(f"Wrote {directory / 'strategy.csv'}")
    print(f"Wrote {directory / 'strategy.md'}")


if __name__ == "__main__":
    main()
