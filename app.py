import random
import streamlit as st

# FIX: Refactored game logic into logic_utils.py using the AI in agent mode.
# app.py is now UI only -- every rule the game enforces lives in logic_utils
# so it can be tested by pytest without starting Streamlit.
from logic_utils import (
    check_guess,
    get_hint_message,
    get_range_for_difficulty,
    parse_guess,
    update_score,
)

st.set_page_config(page_title="Glitchy Guesser", page_icon="🎮")

st.title("🎮 Game Glitch Investigator")
st.caption("An AI-generated guessing game. Something is off.")

st.sidebar.header("Settings")

difficulty = st.sidebar.selectbox(
    "Difficulty",
    ["Easy", "Normal", "Hard"],
    index=1,
)

attempt_limit_map = {
    "Easy": 6,
    "Normal": 8,
    "Hard": 5,
}
attempt_limit = attempt_limit_map[difficulty]

low, high = get_range_for_difficulty(difficulty)

st.sidebar.caption(f"Range: {low} to {high}")
st.sidebar.caption(f"Attempts allowed: {attempt_limit}")

# FIX: I caught this one, not the AI. Its bounds-check patch was ~90% right
# but would have left a stale out-of-range secret in session state, so I
# asked for a targeted follow-up to reset the round on a difficulty change.
# BUG 3 FIX: now that guesses are bounds-checked, a secret left over from a
# previous difficulty (e.g. 73 while playing Easy 1-20) would be unreachable.
# Start a fresh round whenever the difficulty changes.
if st.session_state.get("difficulty") != difficulty:
    st.session_state.difficulty = difficulty
    st.session_state.secret = random.randint(low, high)
    st.session_state.attempts = 1
    st.session_state.status = "playing"
    st.session_state.history = []

if "secret" not in st.session_state:
    st.session_state.secret = random.randint(low, high)

# FIXME: BUG 1 (not fixed yet) - Logic breaks here. Should start at 0; the
# off-by-one costs the player one attempt and makes the banner read stale.
if "attempts" not in st.session_state:
    st.session_state.attempts = 1

if "score" not in st.session_state:
    st.session_state.score = 0

if "status" not in st.session_state:
    st.session_state.status = "playing"

if "history" not in st.session_state:
    st.session_state.history = []

st.subheader("Make a guess")

# FIX: AI spotted that low/high were already computed above but never used.
# BUG 3 FIX: was hard-coded to "1 and 100" regardless of difficulty.
st.info(
    f"Guess a number between {low} and {high}. "
    f"Attempts left: {attempt_limit - st.session_state.attempts}"
)

with st.expander("Developer Debug Info"):
    st.write("Secret:", st.session_state.secret)
    st.write("Attempts:", st.session_state.attempts)
    st.write("Score:", st.session_state.score)
    st.write("Difficulty:", difficulty)
    st.write("History:", st.session_state.history)

raw_guess = st.text_input(
    "Enter your guess:",
    key=f"guess_input_{difficulty}"
)

col1, col2, col3 = st.columns(3)
with col1:
    submit = st.button("Submit Guess 🚀")
with col2:
    new_game = st.button("New Game 🔁")
with col3:
    show_hint = st.checkbox("Show hint", value=True)

if new_game:
    st.session_state.attempts = 0
    # FIX: follow-up prompt after I pointed out an Easy game could roll a 73.
    # BUG 3 FIX: was random.randint(1, 100) and ignored the difficulty range.
    st.session_state.secret = random.randint(low, high)
    st.success("New game started.")
    st.rerun()

if st.session_state.status != "playing":
    if st.session_state.status == "won":
        st.success("You already won. Start a new game to play again.")
    else:
        st.error("Game over. Start a new game to try again.")
    st.stop()

if submit:
    ok, guess_int, err = parse_guess(raw_guess, low, high)

    if not ok:
        # FIX: my change. The AI left the increment at the top of the block;
        # I moved it into the valid branch so junk input is free.
        # BUG 3 FIX: the attempt counter used to increment before parsing, so
        # rejected input still cost the player a turn.
        st.error(err)
    else:
        st.session_state.attempts += 1
        st.session_state.history.append(guess_int)

        # FIX: two-line result of a multi-step agent-mode prompt (move
        # check_guess, fix the high/low bug, update the import here).
        # BUG 2 FIX: the secret is always compared as an int now. It used to
        # be cast to str on even attempts, which silently broke the comparison.
        outcome = check_guess(guess_int, st.session_state.secret)
        message = get_hint_message(outcome)

        if show_hint:
            st.warning(message)

        st.session_state.score = update_score(
            current_score=st.session_state.score,
            outcome=outcome,
            attempt_number=st.session_state.attempts,
        )

        if outcome == "Win":
            st.balloons()
            st.session_state.status = "won"
            st.success(
                f"You won! The secret was {st.session_state.secret}. "
                f"Final score: {st.session_state.score}"
            )
        else:
            if st.session_state.attempts >= attempt_limit:
                st.session_state.status = "lost"
                st.error(
                    f"Out of attempts! "
                    f"The secret was {st.session_state.secret}. "
                    f"Score: {st.session_state.score}"
                )

st.divider()
st.caption("Built by an AI that claims this code is production-ready.")
