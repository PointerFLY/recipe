"""Rules and state helpers for the Chopsticks hand game.

Player hands and player order are interchangeable, so states are normalized
before they are returned. This keeps the state space small for later search.
"""

from typing import Literal

Hand = tuple[int, int]
Player = tuple[Hand, Hand]
State = tuple[Player, Player]
Action = tuple[str, int, int] | tuple[str, int]


def normalize_hand(hand: Hand) -> Hand:
    """Sort a player's hands so (1, 2) and (2, 1) are identical."""
    if len(hand) != 2 or any(
        not isinstance(count, int) or isinstance(count, bool) or not 0 <= count <= 4
        for count in hand
    ):
        raise ValueError("A hand must contain exactly two finger counts from 0 to 4")
    return tuple(sorted(hand))  # type: ignore[return-value]


def normalize_state(state: State) -> State:
    """Normalize both hands within each player; player order stays meaningful."""
    if len(state) != 2:
        raise ValueError("A state must contain exactly two players")
    return (normalize_hand(state[0]), normalize_hand(state[1]))


def initial_state() -> State:
    return ((1, 1), (1, 1))


def _player_after_action(player: Hand, opponent: Hand, action: Action):
    kind = action[0]
    if kind == "attack":
        _, attacker, target = action
        if player[attacker] == 0 or opponent[target] == 0:
            raise ValueError("Attacks require a live attacking hand and target")
        updated = list(opponent)
        value = player[attacker] + updated[target]
        updated[target] = 0 if value >= 5 else value
        return player, normalize_hand(tuple(updated))

    if kind == "self_attack":
        _, attacker, target = action
        if attacker == target or player[attacker] == 0 or player[target] == 0:
            raise ValueError("Self-attacks require two distinct live hands")
        updated = list(player)
        value = updated[attacker] + updated[target]
        updated[target] = 0 if value >= 5 else value
        return normalize_hand(tuple(updated)), opponent

    if kind == "split":
        _, left = action
        total = sum(player)
        if 1 in player:
            raise ValueError("Cannot split when a hand contains exactly 1 finger")
        if not 0 <= left <= min(4, total):
            raise ValueError("Split must keep each hand between 0 and 4")
        right = total - left
        if right > 4:
            raise ValueError("Split must keep each hand between 0 and 4")
        return normalize_hand((left, right)), opponent

    raise ValueError(f"Unknown action: {kind}")


def legal_actions(state: State, player: int = 0) -> list[Action]:
    """List distinct legal actions for player 0 or 1.

    Split redistributes a player's whole finger total, reviving dead hands as
    needed. A split is allowed only when neither hand has exactly one finger.
    """
    state = normalize_state(state)
    if player not in (0, 1):
        raise ValueError("player must be 0 or 1")
    own, other = state[player], state[1 - player]
    actions: list[Action] = []

    for attacker, count in enumerate(own):
        if count == 0:
            continue
        for target, target_count in enumerate(other):
            if target_count:
                actions.append(("attack", attacker, target))
        for target, target_count in enumerate(own):
            if attacker != target and target_count:
                actions.append(("self_attack", attacker, target))

    if 1 not in own:
        total = sum(own)
        for left in range(max(0, total - 4), min(4, total) + 1):
            candidate = normalize_hand((left, total - left))
            if candidate != own:
                action = ("split", candidate[0])
                if action not in actions:
                    actions.append(action)
    return actions


def apply_action(state: State, action: Action, player: int = 0) -> State:
    """Apply a legal action and return the normalized next state."""
    state = normalize_state(state)
    if player not in (0, 1):
        raise ValueError("player must be 0 or 1")
    if action not in legal_actions(state, player):
        raise ValueError(f"Illegal action: {action}")

    result = list(state)
    result[player], result[1 - player] = _player_after_action(
        state[player], state[1 - player], action
    )
    return (result[0], result[1])


def winner(state: State) -> Literal[0, 1] | None:
    """Return the winning player index, or None while both players are alive."""
    state = normalize_state(state)
    if state[0] == (0, 0):
        return 1
    if state[1] == (0, 0):
        return 0
    return None


def main() -> None:
    """Play a two-player local game in the terminal."""
    state = initial_state()
    player = 0
    print("Chopsticks! Enter the number of a legal action, or q to quit.")

    while winner(state) is None:
        print(f"\nPlayer 1: {state[0]}    Player 2: {state[1]}")
        actions = legal_actions(state, player)
        print(f"Player {player + 1}'s turn:")
        for index, action in enumerate(actions, start=1):
            if action[0] == "attack":
                _, attacker, target = action
                description = (
                    f"attack with hand {attacker + 1} "
                    f"on opponent hand {target + 1}"
                )
            elif action[0] == "self_attack":
                _, attacker, target = action
                description = (
                    f"attack with hand {attacker + 1} "
                    f"on your hand {target + 1}"
                )
            else:
                _, first_hand = action
                total = sum(state[player])
                description = f"split to ({first_hand}, {total - first_hand})"
            print(f"  {index}. {description}")

        choice = input("Choose action: ").strip().lower()
        if choice in {"q", "quit", "exit"}:
            print("Game ended.")
            return
        try:
            selected = int(choice)
            if not 1 <= selected <= len(actions):
                raise ValueError
        except ValueError:
            print("Enter one of the listed action numbers, or q to quit.")
            continue

        state = apply_action(state, actions[selected - 1], player)
        player = 1 - player

    print(f"\nPlayer {player + 1} wins!")


if __name__ == "__main__":
    main()
