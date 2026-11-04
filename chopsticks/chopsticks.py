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


def next_states(state):
    """Return distinct legal results, each with the next player first."""
    own, other = normalize_state(state)
    if (0, 0) in (own, other):
        return []
    results = set()

    for attacker, count in enumerate(own):
        if count == 0:
            continue
        # Attack an opponent's live hand.
        for target, value in enumerate(other):
            if value:
                updated = list(other)
                updated[target] = count + value if count + value < 5 else 0
                results.add((tuple(sorted(updated)), own))
        # Attack your other live hand.
        target = 1 - attacker
        if own[target]:
            updated = list(own)
            total = count + own[target]
            updated[target] = total if total < 5 else 0
            results.add((other, tuple(sorted(updated))))

    if own[0] == 0 and own[1] > 1:
        for left in range(1, own[1] // 2 + 1):
            results.add((other, (left, own[1] - left)))
    return sorted(results)


def main():
    """Play a two-player game in the terminal."""
    state = INITIAL_STATE
    player = 1
    print("Chopsticks! Choose a resulting position, or q to quit.")

    while (0, 0) not in state:
        print(f"\nPlayer {player}: {state[0]}    Player {3 - player}: {state[1]}")
        print(f"Player {player}'s turn:")
        choices = next_states(state)
        for index, (other, own) in enumerate(choices, start=1):
            print(f"  {index}. You: {own}    Opponent: {other}")

        choice = input("Choose position: ").strip().lower()
        if choice in {"q", "quit", "exit"}:
            print("Game ended.")
            return
        try:
            selected = int(choice)
            if not 1 <= selected <= len(choices):
                raise ValueError
        except ValueError:
            print("Enter one of the listed position numbers, or q to quit.")
            continue

        state = choices[selected - 1]
        player = 3 - player

    winning_player = 3 - player if state[0] == (0, 0) else player
    print(f"\nPlayer {winning_player} wins!")


if __name__ == "__main__":
    main()
