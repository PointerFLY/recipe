// Python exports legality and optimal actions; this adapter preserves screen positions.
export const sameAction = (a, b) => JSON.stringify(a) === JSON.stringify(b);
export const validPercent = value => typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 100;

export function canonicalState(hands, player) {
  if (![0, 1].includes(player) || !Array.isArray(hands) || hands.length !== 2 ||
      hands.some(hand => !Array.isArray(hand) || hand.length !== 2 ||
        hand.some(n => !Number.isInteger(n) || n < 0 || n > 4))) throw new Error('Invalid board');
  return [hands[player], hands[1 - player]].map(hand => [...hand].sort((a, b) => a - b));
}

export const stateKey = (hands, player) => canonicalState(hands, player).flat().join('');
export const winner = hands => hands[0].every(n => n === 0) ? 1 : hands[1].every(n => n === 0) ? 0 : null;

export function makeMove(hands, player, action, strategy) {
  const state = canonicalState(hands, player);
  const entry = strategy.states[state.flat().join('')];
  const own = hands[player];
  const updated = hands.map(hand => [...hand]);
  const actor = player === 0 ? 'You' : 'Buddy';
  let canonical, message;
  if (action.length === 2 && action[0] === 'split') {
    canonical = action;
    if (!entry?.moves.some(move => sameAction(move.action, canonical))) throw new Error('Illegal split');
    const dead = own.indexOf(0);
    updated[player][dead] = action[1];
    updated[player][1 - dead] = own[0] + own[1] - action[1];
    message = `${actor} split ${own[0] + own[1]} into ${action[1]} + ${updated[player][1 - dead]}. Both hands are awake!`;
  } else if (action.length === 3 && ['attack', 'self_attack'].includes(action[0])) {
    const [kind, source, target] = action;
    if (![0, 1].includes(source) || ![0, 1].includes(target) ||
        (kind === 'self_attack' && source === target)) throw new Error('Illegal tap');
    const targetSide = kind === 'attack' ? 1 - player : player;
    const targetHand = hands[targetSide];
    let sourceIndex = state[0].indexOf(own[source]);
    let targetIndex = state[kind === 'attack' ? 1 : 0].indexOf(targetHand[target]);
    if (kind === 'self_attack' && own[0] === own[1]) [sourceIndex, targetIndex] = [0, 1];
    canonical = [kind, sourceIndex, targetIndex];
    if (!entry?.moves.some(move => sameAction(move.action, canonical))) throw new Error('Illegal tap');
    const total = own[source] + targetHand[target];
    updated[targetSide][target] = total < 5 ? total : 0;
    const destination = kind === 'self_attack' ? 'the other hand' : player === 0 ? 'Buddy' : 'your hand';
    message = `${actor} tapped ${destination}: ${own[source]} + ${targetHand[target]} = ${total}.`;
    if (total >= 5) message += ' That hand is resting!';
  } else throw new Error('Unknown action');
  return {hands: updated, message};
}

export function physicalAction(hands, player, action) {
  if (action[0] === 'split') return [...action];
  const order = side => [0, 1].sort((a, b) => hands[side][a] - hands[side][b]);
  return [action[0], order(player)[action[1]], order(action[0] === 'attack' ? 1 - player : player)[action[2]]];
}

export function chooseAction(hands, player, strategy, percent = 0, random = Math.random) {
  if (!validPercent(percent)) throw new Error('Use a percentage from 0 to 100');
  const entry = strategy.states[stateKey(hands, player)];
  if (!entry?.actions.length) throw new Error('No action for a finished game');
  const alternatives = entry.moves.map(move => move.action)
    .filter(action => !entry.actions.some(optimal => sameAction(optimal, action)));
  const action = percent > 0 && alternatives.length && random() < percent / 100
    ? alternatives[Math.floor(random() * alternatives.length)] : entry.actions[0];
  return physicalAction(hands, player, action);
}

export function createGame(strategy, changed, schedule = setTimeout, cancel = clearTimeout) {
  const session = {hands: [[1, 1], [1, 1]], selected: null, busy: false, percent: 0, log: []};
  let pending = null;
  function restart() {
    if (pending !== null) cancel(pending);
    pending = null;
    Object.assign(session, {hands: [[1, 1], [1, 1]], selected: null, busy: false, log: []});
    changed();
  }
  function play(action) {
    if (session.busy || winner(session.hands) !== null) return;
    if (!validPercent(session.percent)) throw new Error('Choose a suboptimal percentage from 0 to 100 first.');
    const percent = session.percent;
    const move = makeMove(session.hands, 0, action, strategy);
    session.hands = move.hands;
    session.log.push(move.message);
    session.selected = null;
    session.busy = winner(session.hands) === null;
    if (session.busy) pending = schedule(() => {
      pending = null;
      const reply = makeMove(session.hands, 1, chooseAction(session.hands, 1, strategy, percent), strategy);
      session.hands = reply.hands;
      session.log.push(reply.message);
      session.busy = false;
      changed();
    }, 850);
    changed();
  }
  function click(side, index) {
    if (session.busy || winner(session.hands) !== null) return;
    if (session.selected === null) {
      if (side === 0 && session.hands[0][index]) session.selected = index;
      changed();
    } else if (side === 0 && session.selected === index) {
      session.selected = null;
      changed();
    } else play([side === 0 ? 'self_attack' : 'attack', session.selected, index]);
  }
  return {session, restart, play, click};
}
