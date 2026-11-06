"""A small NiceGUI game: uv run python chopsticks/run_ui.py.

The screen board is (human hands, AI hands), with stable left/right positions.
The adapter below translates screen actions to the core game's sorted indices.
"""

import argparse
import asyncio
import math
from pathlib import Path

from nicegui import app, ui

if __package__:
    from .chopsticks import legal_moves, normalize_state
    from .play_ai import choose_action
    from .solve import solve
else:
    from chopsticks import legal_moves, normalize_state
    from play_ai import choose_action
    from solve import solve

ASSETS = Path(__file__).resolve().parent / "assets"
STRATEGY = solve()
AI_SUBOPTIMAL_PERCENT = 0
app.add_static_files("/chopsticks-assets", ASSETS)


def valid_suboptimal_percent(value):
    return isinstance(value, (int, float)) and math.isfinite(value) and 0 <= value <= 100


def canonical_state(hands, player):
    if player not in (0, 1):
        raise ValueError("Player must be 0 or 1")
    return normalize_state((hands[player], hands[1 - player]))


def physical_action(hands, player, action):
    """Map a solver action to screen indices without moving any hand cards."""
    state = canonical_state(hands, player)
    if action not in dict(legal_moves(state)):
        raise ValueError("Illegal action")
    if action[0] == "split":
        return action
    kind, source, target = action
    own_order = sorted(range(2), key=lambda i: hands[player][i])
    target_side = 1 - player if kind == "attack" else player
    target_order = sorted(range(2), key=lambda i: hands[target_side][i])
    return kind, own_order[source], target_order[target]


def make_move(hands, player, action):
    """Validate a screen action, return a new board and a short explanation."""
    state = canonical_state(hands, player)
    own = hands[player]
    actor = "You" if player == 0 else "Buddy"
    updated = [list(hand) for hand in hands]
    if len(action) == 2 and action[0] == "split":
        left = action[1]
        canonical = action
        if canonical not in dict(legal_moves(state)):
            raise ValueError("Illegal split")
        dead = own.index(0)
        updated[player][dead] = left
        updated[player][1 - dead] = sum(own) - left
        message = f"{actor} split {sum(own)} into {left} + {sum(own) - left}. Both hands are awake!"
    elif len(action) == 3 and action[0] in ("attack", "self_attack"):
        kind, source, target = action
        if source not in (0, 1) or target not in (0, 1):
            raise ValueError("Hand index must be 0 or 1")
        if kind == "self_attack" and source == target:
            raise ValueError("A hand cannot tap itself")
        target_side = 1 - player if kind == "attack" else player
        target_hand = hands[target_side]
        source_index = state[0].index(own[source])
        target_index = state[1 if kind == "attack" else 0].index(target_hand[target])
        if kind == "self_attack" and own[0] == own[1]:
            source_index, target_index = 0, 1
        canonical = kind, source_index, target_index
        if canonical not in dict(legal_moves(state)):
            raise ValueError("Illegal tap")
        total = own[source] + target_hand[target]
        updated[target_side][target] = total if total < 5 else 0
        destination = "the other hand" if kind == "self_attack" else "Buddy" if player == 0 else "your hand"
        message = f"{actor} tapped {destination}: {own[source]} + {target_hand[target]} = {total}."
        if total >= 5:
            message += " That hand is resting!"
    else:
        raise ValueError("Unknown action")
    return tuple(tuple(hand) for hand in updated), message


def winner(hands):
    """Return the winning side (human 0, AI 1), or None."""
    normalize_state(hands)
    if tuple(hands[0]) == (0, 0):
        return 1
    if tuple(hands[1]) == (0, 0):
        return 0
    return None


@ui.page("/")
def game_page():
    # Each browser page has its own board and AI setting.
    session = {"hands": ((1, 1), (1, 1)), "selected": None, "busy": False,
               "percent": AI_SUBOPTIMAL_PERCENT, "epoch": 0, "log": [], "turns": 0}
    css_version = (ASSETS / "game.css").stat().st_mtime_ns
    ui.add_head_html(f'<link rel="stylesheet" href="/chopsticks-assets/game.css?v={css_version}">')
    ui.colors(primary="#19796b", secondary="#ed9c45", accent="#ed9c45")

    def restart():
        session.update(hands=((1, 1), (1, 1)), selected=None, busy=False,
                       epoch=session["epoch"] + 1, log=[], turns=0)
        board.refresh()
        recent_moves.refresh()

    async def play(action):
        if session["busy"] or winner(session["hands"]) is not None:
            return
        percent = session["percent"]
        if not valid_suboptimal_percent(percent):
            ui.notify("Choose a suboptimal percentage from 0 to 100 first.", type="warning")
            return
        try:
            hands, message = make_move(session["hands"], 0, action)
        except ValueError:
            ui.notify("Try a glowing hand, or pick your hand again to cancel.")
            return
        epoch = session["epoch"]
        session.update(hands=hands, selected=None, busy=True, turns=session["turns"] + 1)
        session["log"].append(message)
        board.refresh()
        recent_moves.refresh()
        try:
            if winner(hands) is None:
                await asyncio.sleep(0.85)
                if epoch != session["epoch"]:
                    return  # A new game cancels the pending computer turn.
                state = canonical_state(hands, 1)
                action = choose_action(state, STRATEGY, percent)
                action = physical_action(hands, 1, action)
                hands, message = make_move(hands, 1, action)
                session["hands"] = hands
                session["log"].append(message)
        finally:
            if epoch == session["epoch"]:
                session["busy"] = False
                board.refresh()
                recent_moves.refresh()

    async def hand_clicked(side, index):
        if session["busy"] or winner(session["hands"]) is not None:
            return
        selected = session["selected"]
        if selected is None:
            if side == 0 and session["hands"][0][index]:
                session["selected"] = index
                board.refresh()
            return
        if side == 0 and index == selected:
            session["selected"] = None
            board.refresh()
            return
        kind = "self_attack" if side == 0 else "attack"
        await play((kind, selected, index))

    def hand_card(side, index):
        count = session["hands"][side][index]
        selected = side == 0 and session["selected"] == index
        enabled = side == 0 and count > 0
        target = False
        if session["selected"] is not None and not selected:
            kind = "self_attack" if side == 0 else "attack"
            try:
                make_move(session["hands"], 0, (kind, session["selected"], index))
                target = True
            except ValueError:
                pass
            enabled = target
        enabled = enabled and not session["busy"] and winner(session["hands"]) is None
        classes = "hand-card" + (" selected" if selected else " target" if target else "")
        if count == 0:
            classes += " resting"
        owner = "Your" if side == 0 else "Buddy's"
        position = "left" if index == 0 else "right"
        label = f"{owner} {position} hand: {count} finger{'s' if count != 1 else ''}"
        with ui.button(on_click=lambda e: hand_clicked(side, index), color=None).props(
            f'flat no-caps aria-label="{label}"'
        ).classes(classes) as button:
            ui.label("PICKED" if selected else "TAP HERE" if target else "RESTING" if count == 0 else position.upper()).classes("hand-tag")
            with ui.element("div").classes("hand-photo" + (" buddy-photo" if side == 1 else "")).props('aria-hidden="true"'):
                ui.element("img").props(
                    'src="/chopsticks-assets/hands.png" width="1983" height="793" alt="" draggable="false"'
                ).classes("hand-sheet").style(f"left: {-count * 100}%")
            with ui.element("div").classes("hand-count"):
                ui.label(str(count)).classes("count-number")
                ui.label("resting" if count == 0 else "finger" if count == 1 else "fingers")
        button.mark(f"hand-{side}-{index}")
        button.set_enabled(enabled)

    @ui.refreshable
    def board():
        result = winner(session["hands"])
        with ui.element("section").classes("play-board"):
            with ui.element("div").classes("player-heading"):
                with ui.element("div").classes("player-identity"):
                    ui.icon("smart_toy").classes("buddy-avatar")
                    with ui.column().classes("identity-copy"):
                        ui.label("YOUR CHALLENGER").classes("eyebrow")
                        ui.label("Buddy").classes("player-name")
                ui.label("Thinking…" if session["busy"] and result is None else "Ready to play").classes("player-status")
            with ui.element("div").classes("hands-row buddy-hands"):
                hand_card(1, 0)
                hand_card(1, 1)

            with ui.element("div").classes("turn-card" + (" celebration" if result == 0 else "")):
                ui.icon("emoji_events" if result == 0 else "favorite" if result == 1 else "more_horiz" if session["busy"] else "touch_app").classes("turn-icon")
                with ui.column().classes("turn-copy"):
                    title = "You did it!" if result == 0 else "Buddy wins this round" if result == 1 else "Buddy is thinking…" if session["busy"] else "Now choose a target" if session["selected"] is not None else "Your turn, bright spark!"
                    subtitle = "Nice thinking. Ready for another game?" if result is not None else "Watch Buddy's next tap." if session["busy"] else "Tap a glowing hand. Tap your picked hand to cancel." if session["selected"] is not None else "Pick one of your hands, then tap a target."
                    ui.label(title).classes("turn-title")
                    ui.label(subtitle).classes("turn-subtitle")

            with ui.element("div").classes("hands-row your-hands"):
                hand_card(0, 0)
                hand_card(0, 1)
            with ui.element("div").classes("your-heading"):
                ui.label("YOU").classes("eyebrow")
                ui.label("Little hands. Clever moves.").classes("your-caption")
            if result is None and not session["busy"] and 0 in session["hands"][0] and sum(session["hands"][0]) > 1:
                with ui.element("div").classes("split-row"):
                    ui.icon("call_split")
                    ui.label("Wake up your resting hand:")
                    total = sum(session["hands"][0])
                    for left in range(1, total // 2 + 1):
                        ui.button(f"Split {left} + {total - left}",
                                  on_click=lambda e, left=left: play(("split", left))).props("no-caps unelevated").classes("split-button")

    @ui.refreshable
    def recent_moves():
        with ui.element("div").classes("recent-moves"):
            ui.label("THE LAST TAPS").classes("eyebrow")
            if not session["log"]:
                ui.label("Your story starts with a tap.").classes("muted")
            for message in session["log"][-2:]:
                ui.label(message).classes("move-message")

    with ui.dialog() as rules, ui.card().classes("rules-card"):
        ui.label("A tiny game of big ideas").classes("panel-title")
        ui.label("1. Pick your hand, then tap Buddy's hand or your other hand.")
        ui.label("2. Add the fingers together. At 5 or more, the tapped hand rests.")
        ui.label("3. One resting hand? Split 2, 3 or 4 fingers to wake it up.")
        ui.label("4. Get both of Buddy's hands resting to win!")
        ui.button("Let's play", on_click=rules.close).props("no-caps unelevated")

    with ui.column().classes("app-shell"):
        with ui.element("header").classes("site-header"):
            with ui.element("div").classes("brand"):
                ui.icon("pan_tool").classes("brand-mark")
                with ui.column().classes("brand-copy"):
                    ui.label("Chopsticks Club").classes("brand-name")
                    ui.label("A LITTLE THINKING GOES A LONG WAY").classes("brand-tagline")
            with ui.row().classes("header-actions"):
                ui.button("How to play", icon="help_outline", on_click=rules.open).props("flat no-caps").classes("help-button")
                ui.button("New game", icon="refresh", on_click=restart).props("no-caps unelevated").classes("new-game-button")
        with ui.element("main").classes("workspace"):
            board()
            with ui.element("aside").classes("sidebar"):
                with ui.element("section").classes("welcome-panel"):
                    ui.label("LET'S PLAY & LEARN").classes("eyebrow")
                    ui.label("A little tap.\nA bright idea.").classes("welcome-title")
                    ui.label("Add fingers, spot a clever move, and give Buddy a challenge.").classes("welcome-copy")
                    with ui.element("div").classes("mini-lesson"):
                        ui.label("2 + 3 = 5").classes("lesson-equation")
                        ui.label("Five or more? Time for that hand to rest.")
                with ui.element("section").classes("settings-panel"):
                    ui.number("Suboptimal percentage", value=session["percent"], min=0, max=100,
                              step=5, precision=1, suffix="%",
                              on_change=lambda e: session.update(percent=e.value),
                              validation={"Use a percentage from 0 to 100": valid_suboptimal_percent}
                              ).props("outlined rounded").classes("percentage-input")
                recent_moves()
        with ui.element("footer").classes("site-footer"):
            ui.icon("wb_sunny")
            ui.label("No timer. Take your time. Every tap is a chance to learn.")


def main(argv=None):
    global AI_SUBOPTIMAL_PERCENT
    parser = argparse.ArgumentParser(description="Play Chopsticks in your browser.")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--no-show", action="store_true", help="do not open a browser automatically")
    parser.add_argument("--suboptimal-percent", type=float, default=0,
                        help="initial chance of a nonoptimal AI move, 0–100 (default: 0)")
    args = parser.parse_args(argv)
    if not valid_suboptimal_percent(args.suboptimal_percent):
        parser.error("--suboptimal-percent must be between 0 and 100")
    AI_SUBOPTIMAL_PERCENT = args.suboptimal_percent
    ui.run(title="Chopsticks Club", host=args.host, port=args.port,
           show=not args.no_show, reload=False, favicon="✋")


if __name__ == "__main__":
    main()
