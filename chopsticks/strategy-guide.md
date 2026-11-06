# A compact Chopsticks strategy

The complete strategy table covers 192 reachable positions. For human play,
we can summarize it as a few rules and a small list of losing configurations.
These results apply to the current rules, including self-attacks and splitting
only to revive a dead hand. Infinite play counts as a draw in the analysis.

Always read a position as **your hands first, with you moving next**. Each
player's hands are sorted; left and right are interchangeable.

## Four rules

1. **Win immediately when possible:** eliminate the opponent's last live hand.
2. **Otherwise, try to leave the opponent a losing configuration** from the
   list below. Swap perspectives after your move: the opponent is now the
   player to move, so their hands go in the first column.
3. **If you cannot force a win, preserve the draw:** avoid moves that let the
   opponent win immediately or put you into a losing configuration.
4. **When defeat is unavoidable, delay it:** choose the move that postpones
   defeat longest against optimal opposition.

## The 15 nonterminal losing configurations

| Your hands | Opponent's hands that make your position losing |
|---|---|
| `(0,1)` | `(0,1)`, `(0,3)`, `(1,1)`, `(1,3)`, `(2,2)`, `(2,3)`, `(2,4)`, `(3,3)`, `(4,4)` |
| `(0,2)` | `(4,4)` |
| `(0,3)` | `(2,3)`, `(2,4)`, `(3,3)`, `(4,4)` |
| `(0,4)` | `(4,4)` |

These are all the nonterminal losing positions reachable from the opening.
A losing position means your opponent can force victory regardless of your
choices; it does not mean every opponent move wins.

## Two useful cautions

- **Don't always split.** With your `(0,2)` against `(2,4)`, you can preserve a
  draw, but splitting to `(1,1)` gives the opponent a forced win.
- **Don't always avoid self-attacks.** With your `(2,3)` against `(0,1)`, attack
  your own 2 with your 3. The 2 becomes dead, leaving your `(0,3)`. The opponent
  must attack with their 1, making your hand 4; you then eliminate their last
  hand. This forces a win in three moves, counting both players' moves.

## Make progress toward a win

Merely choosing moves that leave the opponent a losing position can still
produce a cycle. Among winning moves, choose the one with the shortest
forced-win distance. This ensures progress to victory against optimal defense.
When losing, prefer the longest distance; when drawing, preserve the draw.

The opening `((1,1),(1,1))` is a draw with perfect play. Both the opening
opponent attack and the opening self-attack preserve that draw.

Use the full [Markdown table](strategy.md) for
exact move choices, including all equally optimal actions and distances.
For fewer entries to remember, the [45-entry policy](strategy.md#minimum-size-optimal-policy)
chooses between equally optimal actions to minimize the number of decision
states. It covers both starting seats and every legal opponent response,
provided you consistently follow its selected actions. See the
[minimum-size verification](strategy.md#minimum-size-optimal-policy) for its scope and proof.
One ply is one player's move. Regenerate the tables after changing the rules:

```sh
uv run python chopsticks/solve.py
```
