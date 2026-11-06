import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {canonicalState, stateKey, makeMove, physicalAction, chooseAction, sameAction,
  validPercent, createGame, winner} from '../web/engine.mjs';

const {strategy, cases} = JSON.parse(readFileSync(process.argv[2], 'utf8'));
const candidates = [];
for (const kind of ['attack', 'self_attack'])
  for (const source of [0, 1]) for (const target of [0, 1]) candidates.push([kind, source, target]);
for (let left = 0; left < 5; left++) candidates.push(['split', left]);

for (const {hands, player, moves} of cases) {
  const original = JSON.stringify(hands);
  const successors = new Set();
  for (const action of candidates) {
    let result;
    try { result = makeMove(hands, player, action, strategy); }
    catch { continue; }
    assert.ok(result.message);
    const child = canonicalState(result.hands, 1 - player);
    successors.add(JSON.stringify(child));
    assert.ok(moves.some(move => JSON.stringify(move.next) === JSON.stringify(child)));
    if (action[0] === 'attack') assert.deepEqual(result.hands[player], hands[player]);
    if (action[0] === 'self_attack') {
      assert.deepEqual(result.hands[1 - player], hands[1 - player]);
      assert.equal(result.hands[player][action[1]], hands[player][action[1]]);
    }
  }
  assert.deepEqual(successors, new Set(moves.map(move => JSON.stringify(move.next))));
  for (const {action, next} of moves) {
    const result = makeMove(hands, player, physicalAction(hands, player, action), strategy);
    assert.deepEqual(canonicalState(result.hands, 1 - player), next);
  }
  if (moves.length) {
    const entry = strategy.states[stateKey(hands, player)];
    const chosen = chooseAction(hands, player, strategy);
    assert.deepEqual(chosen, physicalAction(hands, player, entry.actions[0]));
    const alternatives = moves.filter(move => !entry.actions.some(action => sameAction(action, move.action)));
    if (alternatives.length) {
      const suboptimal = chooseAction(hands, player, strategy, 100, () => 0);
      assert.deepEqual(suboptimal, physicalAction(hands, player, alternatives[0].action));
    }
  }
  assert.equal(JSON.stringify(hands), original, 'Adapters must not mutate the input');
}
assert.deepEqual(makeMove([[1, 1], [1, 1]], 0, ['attack', 1, 1], strategy).hands, [[1, 1], [1, 2]]);
assert.deepEqual(makeMove([[1, 1], [1, 1]], 0, ['self_attack', 1, 0], strategy).hands, [[2, 1], [1, 1]]);
assert.deepEqual(makeMove([[4, 0], [1, 1]], 0, ['split', 1], strategy).hands, [[3, 1], [1, 1]]);
assert.deepEqual(makeMove([[0, 4], [1, 1]], 0, ['split', 1], strategy).hands, [[1, 3], [1, 1]]);
for (const percent of [NaN, Infinity, -1, 101, '', null]) {
  assert.equal(validPercent(percent), false);
  assert.throws(() => chooseAction([[1, 1], [1, 1]], 1, strategy, percent));
}
let pending, cancelled = false, changes = 0;
const game = createGame(strategy, () => changes++, (callback, delay) => {
  assert.equal(delay, 850); pending = callback; return 123;
}, id => { assert.equal(id, 123); cancelled = true; pending = null; });
game.click(0, 0);
assert.equal(game.session.selected, 0);
game.click(0, 0);
assert.equal(game.session.selected, null);
game.click(0, 0);
game.click(1, 1);
assert.equal(game.session.busy, true);
assert.deepEqual(game.session.hands, [[1, 1], [1, 2]]);
game.click(0, 0);
assert.equal(game.session.selected, null);
pending();
assert.equal(game.session.busy, false);
assert.equal(game.session.log.length, 2);
game.restart();
game.session.percent = 20;
game.play(['attack', 0, 0]);
game.restart();
assert.equal(cancelled, true);
assert.equal(pending, null);
assert.equal(game.session.percent, 20);
assert.deepEqual(game.session.hands, [[1, 1], [1, 1]]);
assert.equal(game.session.log.length, 0);
assert.equal(game.session.busy, false);
game.session.percent = NaN;
assert.throws(() => game.play(['attack', 0, 0]));
assert.deepEqual(game.session.hands, [[1, 1], [1, 1]]);
game.session.percent = 0;
game.session.hands = [[1, 0], [4, 0]];
game.play(['attack', 0, 0]);
assert.equal(winner(game.session.hands), 0);
assert.equal(game.session.busy, false);
assert.equal(pending, null);
assert.ok(changes > 0);
// The starting preference affects the next round and never moves a live board.
const timers = new Map();
let timerId = 0;
const openingGame = createGame(strategy, () => {}, (callback, delay) => {
  assert.equal(delay, 850);
  timers.set(++timerId, callback);
  return timerId;
}, id => timers.delete(id));
assert.equal(openingGame.session.buddyFirst, false);
assert.equal(openingGame.session.humanPlayer, 1);
openingGame.session.buddyFirst = true;
assert.equal(openingGame.session.busy, false);
assert.equal(openingGame.session.humanPlayer, 1);
openingGame.restart();
assert.equal(openingGame.session.humanPlayer, 2);
assert.equal(openingGame.session.busy, true);
assert.deepEqual(openingGame.session.hands, [[1, 1], [1, 1]]);
openingGame.click(0, 0);
openingGame.play(['attack', 0, 0]);
assert.equal(openingGame.session.selected, null);
assert.equal(openingGame.session.log.length, 0);
const staleOpening = timers.get(timerId);
openingGame.restart();
assert.equal(timers.size, 1, 'Restart replaces the pending opening');
staleOpening();
assert.equal(openingGame.session.log.length, 0, 'A stale opening cannot affect the next round');
// Changes during thinking apply to the next turn/round, not the scheduled opening.
openingGame.session.percent = NaN;
openingGame.session.buddyFirst = false;
timers.get(timerId)();
assert.equal(openingGame.session.log.length, 1);
assert.match(openingGame.session.log[0], /^Buddy /);
assert.equal(openingGame.session.busy, false);
assert.equal(openingGame.session.humanPlayer, 2);
const openedHands = JSON.stringify(openingGame.session.hands);
assert.throws(() => openingGame.restart(), /percentage/);
assert.equal(JSON.stringify(openingGame.session.hands), openedHands);
openingGame.session.percent = 25;
openingGame.restart();
assert.equal(openingGame.session.humanPlayer, 1);
assert.equal(openingGame.session.busy, false);
assert.equal(openingGame.session.percent, 25);
assert.equal(openingGame.session.buddyFirst, false);
assert.equal(openingGame.session.log.length, 0);
assert.deepEqual(openingGame.session.hands, [[1, 1], [1, 1]]);
openingGame.session.buddyFirst = true;
openingGame.restart();
const cancelledOpening = timers.get(timerId);
openingGame.session.buddyFirst = false;
openingGame.restart();
cancelledOpening();
assert.equal(openingGame.session.log.length, 0);
assert.equal(openingGame.session.busy, false);
console.log(`Verified ${cases.length} physical boards, AI choices, difficulty, and game lifecycle.`);
