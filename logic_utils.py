# FIX: Moved from app.py unchanged (agent mode). parse_guess needs it to know
# the real bounds, so it had to live beside it instead of in the UI file.
def get_range_for_difficulty(difficulty: str):
    """Return (low, high) inclusive range for a given difficulty."""
    if difficulty == "Easy":
        return 1, 20
    if difficulty == "Normal":
        return 1, 100
    if difficulty == "Hard":
        return 1, 50
    return 1, 100


# FIX: Refactored from app.py and given a bounds check. I asked the AI to add
# range validation; it wrote the check but kept the old parse_guess(raw)
# signature, so I had it thread low/high through from get_range_for_difficulty.
def parse_guess(raw: str, low: int, high: int):
    """
    Parse user input into an int guess and confirm it falls inside [low, high].

    Returns: (ok: bool, guess_int: int | None, error_message: str | None)
    """
    if raw is None or raw.strip() == "":
        return False, None, "Enter a guess."

    raw = raw.strip()

    try:
        if "." in raw:
            value = int(float(raw))
        else:
            value = int(raw)
    except Exception:
        return False, None, "That is not a number."

    # BUG 3 FIX: the original had no bounds check at all, so 500 and -7 were
    # accepted as valid guesses and burned an attempt.
    if value < low or value > high:
        return False, None, f"Out of range. Guess a number between {low} and {high}."

    return True, value, None


# FIX: Refactored out of app.py into logic_utils.py with the AI in agent mode.
# I described the "Go HIGHER at 100" symptom; the AI located the swapped return
# values and proposed this lookup map so the outcome and text stay in sync.
# Maps an outcome to the hint shown to the player.
# BUG 2 FIX: these were swapped in app.py -- "Too High" was paired with
# "Go HIGHER!", so the game told the player the opposite of the truth.
HINT_MESSAGES = {
    "Win": "🎉 Correct!",
    "Too High": "📉 Go LOWER!",
    "Too Low": "📈 Go HIGHER!",
}


def check_guess(guess, secret):
    """
    Compare guess to secret and return the outcome as a string.

    Returns one of: "Win", "Too High", "Too Low"

    Both values are coerced to int so a stringified secret can never push
    this into a text comparison where "9" > "100" is True.
    """
    # FIX: the int() coercion was my addition, not the AI's. Its first draft
    # only reordered the messages and left the TypeError fallback in place,
    # which would have kept the "9" > "100" text-comparison bug alive.
    guess = int(guess)
    secret = int(secret)

    if guess == secret:
        return "Win"
    if guess > secret:
        return "Too High"
    return "Too Low"


def get_hint_message(outcome: str):
    """Return the player-facing hint text for an outcome from check_guess."""
    return HINT_MESSAGES.get(outcome, "")


# FIX: Moved from app.py with the AI, but deliberately NOT fixed. The AI
# offered to correct the scoring bug in the same pass; I declined so this
# refactor stays reviewable and the scoring bug gets its own commit.
def update_score(current_score: int, outcome: str, attempt_number: int):
    """Update score based on outcome and attempt number."""
    if outcome == "Win":
        points = 100 - 10 * (attempt_number + 1)
        if points < 10:
            points = 10
        return current_score + points

    # FIXME: (not fixed yet) Logic breaks here. A wrong "Too High" guess on an
    # even attempt ADDS 5 points instead of subtracting. Moved here unchanged
    # so the scoring bug can be fixed on its own.
    if outcome == "Too High":
        if attempt_number % 2 == 0:
            return current_score + 5
        return current_score - 5

    if outcome == "Too Low":
        return current_score - 5

    return current_score
