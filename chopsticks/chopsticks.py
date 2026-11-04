"""Chopsticks rules:

1. Two players start with one finger on each of their two hands.
2. Players alternate turns, making one attack or split per turn.
3. Attack with a live hand by adding its count to an opponent's live hand
   or your own other live hand. The attacking hand stays unchanged.
4. A hand reaching 5 or more fingers becomes dead (0); there is no rollover.
   Dead hands cannot attack or be attacked.
5. Split only when you have one dead hand and one live hand with 2–4 fingers.
   Redistribute the total so both hands are alive: 2 becomes (1, 1),
   3 becomes (1, 2), and 4 becomes (1, 3) or (2, 2).
6. Left and right hands are interchangeable; swapped pairs are the same.
7. A player loses when both hands are dead. No further moves are allowed.
8. There is no automatic draw or repetition limit; play may continue forever.

A state is (current player's hands, opponent's hands), with each pair sorted.
legal_moves(state) returns (action, next_state) pairs. Attack actions contain
the attacking and target hand indices (0 or 1); split actions contain the
smaller resulting count. Indices refer to the sorted hands before the move.
next_states(state) returns distinct legal results with the next player first.
"""

INITIAL_STATE = ((1, 1), (1, 1))


def normalize_state(state):
    """Validate finger counts and sort each player's hands."""
    if len(state) != 2:
        raise ValueError("A state must contain exactly two players")
    for hand in state:
        if len(hand) != 2 or any(
            type(count) is not int or not 0 <= count <= 4 for count in hand
        ):
            raise ValueError("Each player needs two finger counts from 0 to 4")
    return tuple(tuple(sorted(hand)) for hand in state)


def legal_moves(state):
    """Return (action, next_state) pairs, with the next player first."""
    own, other = normalize_state(state)
    if (0, 0) in (own, other):
        return []
    moves = []

    for attacker, count in enumerate(own):
        if count == 0 or (attacker == 1 and count == own[0]):
            continue
        # Attack an opponent's live hand.
        for target, value in enumerate(other):
            if value and not (target == 1 and value == other[0]):
                updated = list(other)
                updated[target] = count + value if count + value < 5 else 0
                moves.append((("attack", attacker, target), (tuple(sorted(updated)), own)))
        # Attack your other live hand.
        target = 1 - attacker
        if own[target]:
            updated = list(own)
            total = count + own[target]
            updated[target] = total if total < 5 else 0
            moves.append((("self_attack", attacker, target), (other, tuple(sorted(updated)))))

    if own[0] == 0 and own[1] > 1:
        for left in range(1, own[1] // 2 + 1):
            moves.append((("split", left), (other, (left, own[1] - left))))
    return sorted(moves, key=lambda move: move[0])


def next_states(state):
    """Return distinct legal results, each with the next player first."""
    return sorted({result for action, result in legal_moves(state)})


def main():
    """Play a two-player game in the terminal."""
    state = INITIAL_STATE
    player = 1
    print("Chopsticks")
    print("Choose a move number, or q to quit.")
    print("Hands are (H1, H2), sorted by finger count each turn.")

    while (0, 0) not in state:
        print(f"\nPlayer {player}'s turn")
        print(f"You (P{player}): {state[0]}    Opponent (P{3 - player}): {state[1]}")
        print(f"\n  {'#':>2}  {'Action':<41}  {'You after':<10}  {'Opponent after'}")
        print("  " + "-" * 73)
        choices = legal_moves(state)
        for index, (action, (other, own)) in enumerate(choices, start=1):
            if action[0] == "split":
                source = f"Split {state[0]}"
                destination = str(own)
            else:
                kind, attacker, target = action
                label = "Attack" if kind == "attack" else "Self-attack"
                destination = f"opponent H{target + 1}" if kind == "attack" else f"H{target + 1}"
                target_count = state[1][target] if kind == "attack" else state[0][target]
                source = f"{label} H{attacker + 1} ({state[0][attacker]})"
                destination = f"{destination} ({target_count})"
            description = f"{source:<21} -> {destination:<16}"
            print(f"  {index:>2}  {description}  {str(own):<10}  {other}")

        choice = input("\nYour move: ").strip().lower()
        if choice in {"q", "quit", "exit"}:
            print("Game ended.")
            return
        try:
            selected = int(choice)
            if not 1 <= selected <= len(choices):
                raise ValueError
        except ValueError:
            print("Enter one of the listed action numbers, or q to quit.")
            continue

        action, state = choices[selected - 1]
        player = 3 - player

    winning_player = 3 - player if state[0] == (0, 0) else player
    print(f"\nPlayer {winning_player} wins!")


if __name__ == "__main__":
    main()
