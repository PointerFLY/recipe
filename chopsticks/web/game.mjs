import {createGame, makeMove, validPercent, winner} from './engine.mjs';

const $ = id => document.getElementById(id);
const rules = $('rules');
$('help').addEventListener('click', () => rules.showModal());
let game, strategy;

function act(callback) {
  $('notice').textContent = '';
  try { callback(); } catch (error) { $('notice').textContent = error.message; }
}

function handCard(side, index) {
  const {session} = game;
  const count = session.hands[side][index];
  const selected = side === 0 && session.selected === index;
  let enabled = side === 0 && count > 0, target = false;
  if (session.selected !== null && !selected) {
    try {
      makeMove(session.hands, 0, [side === 0 ? 'self_attack' : 'attack', session.selected, index], strategy);
      target = true;
    } catch { /* A resting or otherwise illegal target remains disabled. */ }
    enabled = target;
  }
  const button = document.createElement('button');
  button.type = 'button';
  button.id = `hand-${side}-${index}`;
  button.className = `hand-card${selected ? ' selected' : target ? ' target' : ''}${count === 0 ? ' resting' : ''}`;
  button.disabled = !enabled || session.busy || winner(session.hands) !== null;
  button.setAttribute('aria-pressed', String(selected));
  const position = index === 0 ? 'left' : 'right';
  button.setAttribute('aria-label', `${side === 0 ? 'Your' : "Buddy's"} ${position} hand: ${count} finger${count === 1 ? '' : 's'}`);
  button.innerHTML = `<span class="hand-tag">${selected ? 'PICKED' : target ? 'TAP HERE' : count === 0 ? 'RESTING' : position.toUpperCase()}</span><span class="hand-photo${side === 1 ? ' buddy-photo' : ''}" aria-hidden="true"><img class="hand-sheet" src="./assets/hands.png" width="1983" height="793" alt="" draggable="false" style="left:${-count * 100}%"></span><span class="hand-count"><span class="count-number">${count}</span><span>${count === 0 ? 'resting' : count === 1 ? 'finger' : 'fingers'}</span></span>`;
  button.addEventListener('click', () => act(() => game.click(side, index)));
  return button;
}

function render() {
  const focused = document.activeElement?.id;
  const {session} = game;
  const result = winner(session.hands);
  $('buddy-hands').replaceChildren(handCard(1, 0), handCard(1, 1));
  $('your-hands').replaceChildren(handCard(0, 0), handCard(0, 1));
  $('buddy-status').textContent = session.busy ? 'Thinking…' : result === null ? 'Ready to play' : 'Round complete';
  $('turn-card').classList.toggle('celebration', result === 0);
  $('turn-icon').textContent = result === 0 ? '🏆' : result === 1 ? '♥' : session.busy ? '…' : '☝';
  $('turn-title').textContent = result === 0 ? 'You did it!' : result === 1 ? 'Buddy wins this round' : session.busy ? 'Buddy is thinking…' : session.selected !== null ? 'Now choose a target' : 'Your turn, bright spark!';
  $('turn-subtitle').textContent = result !== null ? 'Nice thinking. Ready for another game?' : session.busy ? "Watch Buddy's next tap." : session.selected !== null ? 'Tap a glowing hand. Tap your picked hand to cancel.' : 'Pick one of your hands, then tap a target.';
  $('splits').replaceChildren();
  if (result === null && !session.busy && session.hands[0].includes(0)) {
    const total = session.hands[0][0] + session.hands[0][1];
    if (total > 1) {
      $('splits').append('Wake up your resting hand:');
      for (let left = 1; left <= Math.floor(total / 2); left++) {
        const button = document.createElement('button');
        button.className = 'split-button';
        button.textContent = `Split ${left} + ${total - left}`;
        button.addEventListener('click', () => act(() => game.play(['split', left])));
        $('splits').append(button);
      }
    }
  }
  $('moves').replaceChildren();
  if (!session.log.length) $('moves').textContent = 'Your story starts with a tap.';
  for (const message of session.log.slice(-2)) {
    const line = document.createElement('div');
    line.className = 'move-message';
    line.textContent = message;
    $('moves').append(line);
  }
  // Preserve keyboard focus when replacing hand buttons during a selection.
  if (focused?.startsWith('hand-')) $(focused)?.focus();
}

$('percent').addEventListener('input', event => {
  const value = event.target.value === '' ? NaN : event.target.valueAsNumber;
  if (game) game.session.percent = value;
  const valid = validPercent(value);
  event.target.setAttribute('aria-invalid', String(!valid));
  $('percent-error').textContent = valid ? '' : 'Use a percentage from 0 to 100.';
});
$('restart').addEventListener('click', () => act(() => game.restart()));

async function start() {
  try {
    const response = await fetch(new URL('./strategy.json', import.meta.url));
    if (!response.ok) throw new Error(`Strategy request failed (${response.status})`);
    strategy = await response.json();
    if (strategy.version !== 1 || !strategy.states?.['1111']?.moves.length) throw new Error('Invalid game strategy');
    game = createGame(strategy, render);
    game.session.percent = $('percent').value === '' ? NaN : $('percent').valueAsNumber;
    $('restart').disabled = false;
    render();
  } catch {
    $('turn-title').textContent = 'Buddy could not load';
    $('turn-subtitle').textContent = 'Check your connection and reload to try again.';
    const retry = document.createElement('button');
    retry.className = 'split-button';
    retry.textContent = 'Try again';
    retry.addEventListener('click', () => { retry.remove(); start(); });
    $('splits').append(retry);
  }
}
start();
