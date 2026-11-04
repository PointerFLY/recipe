"""Play against a perfect opponent: python3 chopsticks/play_ai.py [--player 2]."""

import argparse

if __package__:
    from . import chopsticks as game
    from .solve import solve
else:
    import chopsticks as game
    from solve import solve


def choose_action(state, strategy):
    """Choose the first equally optimal action from the full solved strategy."""
    state = game.normalize_state(state)
    actions = strategy[state]["actions"]
    if not actions:
        raise ValueError("A finished game has no action")
    return actions[0]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Play Chopsticks against a perfect opponent.")
    parser.add_argument("--player", type=int, choices=(1, 2), default=1,
                        help="your player number: 1 moves first, 2 moves second (default: 1)")
    args = parser.parse_args(argv)
    strategy = solve()
    print("The computer forces the fastest win it can, preserves draws, and delays forced losses.")
    print("Perfect play from the opening is a draw; games can repeat. Enter q to quit.")
    game.main(computer=lambda state: choose_action(state, strategy), human_player=args.player)


if __name__ == "__main__":
    main()
