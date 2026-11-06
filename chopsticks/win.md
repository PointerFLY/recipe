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

## Memory table for the compact policy

**Finish first:** if you can eliminate the opponent's last live hand, do it.
This covers 10 of the compact policy's 45 entries. For example, with your `24`
against their `01`, your 4 attacks their 1 and wins immediately.

**Only when you cannot win immediately**, use this table from top to bottom.
It covers the remaining 35 entries. Here `14` means `(1,4)`, and "Any" means
any of your hand pairs encountered in that part of the compact policy.

| Opponent's hands | Your hands | Action | Entries |
|---|---|---|---:|
| `01` | Any | Dead hand: **split**. Otherwise: **self-attack larger onto smaller**. | 7 |
| `11` | Any | Dead hand: **split**. Otherwise, total ≤4: **self-attack larger onto smaller**. Total >4: **largest attacks their 1**. | 10 |
| `14` | `04` | **Split to `22`**. | 1 |
| `14` | Other | **Kill their 4** with any live hand. | 9 |
| `13` | `14` | **Your 1 attacks their 3**. | 1 |
| Other remaining cases | Any | **Largest attacks largest**. | 7 |
| | | **Total** | **35** |

**Mnemonic:** Ones build · Fourteen loses four · Otherwise big hits big.

With equal hands, either equivalent hand works. These rules apply to positions
reached while consistently following the compact policy. If you deviate and
reach a position outside it, consult the full strategy table.

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
