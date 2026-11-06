"""Play against a perfect opponent: uv run python chopsticks/play_ai.py [--player 2]."""

import argparse
import random

if __package__:
    from . import chopsticks as game
    from .solve import solve
else:
    import chopsticks as game
    from solve import solve


def choose_action(state, strategy, suboptimal_percent=0):
    """Usually play optimally; optionally choose a random nonoptimal legal move.

    Suboptimal includes slower wins or faster losses, even if the outcome stays
    the same. If every legal move is optimal, keep the usual optimal choice.
    """
    if not 0 <= suboptimal_percent <= 100:
        raise ValueError("Suboptimal percentage must be between 0 and 100")
    state = game.normalize_state(state)
    actions = strategy[state]["actions"]
    if not actions:
        raise ValueError("A finished game has no action")
    if suboptimal_percent > 0:
        alternatives = [action for action, _ in game.legal_moves(state)
                        if action not in actions]
        if alternatives and random.random() < suboptimal_percent / 100:
            return random.choice(alternatives)
    return actions[0]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Play Chopsticks against a perfect opponent.")
    parser.add_argument("--player", type=int, choices=(1, 2), default=1,
                        help="your player number: 1 moves first, 2 moves second (default: 1)")
    parser.add_argument("--suboptimal-percent", type=float, default=0,
                        help="chance per AI turn of a random suboptimal move, 0–100 (default: 0)")
    args = parser.parse_args(argv)
    if not 0 <= args.suboptimal_percent <= 100:
        parser.error("--suboptimal-percent must be between 0 and 100")
    strategy = solve()
    if args.suboptimal_percent:
        print(f"The computer has a {args.suboptimal_percent:g}% chance per turn of choosing a "
              "random suboptimal move when available.")
    else:
        print("The computer forces the fastest win it can, preserves draws, and delays forced losses.")
    print("Perfect play from the opening is a draw; games can repeat. Enter q to quit.")
    game.main(computer=lambda state: choose_action(state, strategy, args.suboptimal_percent),
              human_player=args.player)


if __name__ == "__main__":
    main()
