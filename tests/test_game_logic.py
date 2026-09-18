from logic_utils import (
    check_guess,
    get_hint_message,
    get_range_for_difficulty,
    parse_guess,
)

def test_winning_guess():
    # If the secret is 50 and guess is 50, it should be a win
    result = check_guess(50, 50)
    assert result == "Win"

def test_guess_too_high():
    # If secret is 50 and guess is 60, hint should be "Too High"
    result = check_guess(60, 50)
    assert result == "Too High"

def test_guess_too_low():
    # If secret is 50 and guess is 40, hint should be "Too Low"
    result = check_guess(40, 50)
    assert result == "Too Low"


# ---------------------------------------------------------------------------
# BUG 2 regression tests: the hint messages used to be swapped, so a guess
# above the secret told the player to "Go HIGHER!".
# ---------------------------------------------------------------------------

def test_hint_for_too_high_says_go_lower():
    # Guessing 60 against a secret of 50 must point the player DOWN
    outcome = check_guess(60, 50)
    assert outcome == "Too High"
    assert "LOWER" in get_hint_message(outcome)


def test_hint_for_too_low_says_go_higher():
    # Guessing 40 against a secret of 50 must point the player UP
    outcome = check_guess(40, 50)
    assert outcome == "Too Low"
    assert "HIGHER" in get_hint_message(outcome)


def test_top_of_range_guess_is_never_too_low():
    # The original bug: guessing 100 (top of range) still said "Go HIGHER!"
    outcome = check_guess(100, 42)
    assert outcome == "Too High"
    assert "HIGHER" not in get_hint_message(outcome)


def test_string_secret_still_compares_as_a_number():
    # app.py used to cast the secret to str on even attempts, which made
    # check_guess compare "9" > "100" as text and call 9 "Too High".
    assert check_guess(9, "100") == "Too Low"


# ---------------------------------------------------------------------------
# BUG 3 regression tests: guesses outside the allowed range used to be
# accepted as valid and cost the player an attempt.
# ---------------------------------------------------------------------------

def test_guess_above_range_is_rejected():
    ok, value, err = parse_guess("500", 1, 100)
    assert ok is False
    assert value is None
    assert "range" in err.lower()


def test_negative_guess_is_rejected():
    ok, value, err = parse_guess("-7", 1, 100)
    assert ok is False
    assert value is None


def test_guess_outside_easy_range_is_rejected():
    # 50 is fine on Normal but out of bounds on Easy (1-20)
    low, high = get_range_for_difficulty("Easy")
    assert (low, high) == (1, 20)
    ok, _, _ = parse_guess("50", low, high)
    assert ok is False


def test_guess_inside_range_is_accepted():
    ok, value, err = parse_guess("42", 1, 100)
    assert ok is True
    assert value == 42
    assert err is None


def test_range_boundaries_are_inclusive():
    assert parse_guess("1", 1, 100)[0] is True
    assert parse_guess("100", 1, 100)[0] is True
    assert parse_guess("0", 1, 100)[0] is False
    assert parse_guess("101", 1, 100)[0] is False


def test_non_numeric_input_is_still_rejected():
    ok, _, err = parse_guess("abc", 1, 100)
    assert ok is False
    assert err == "That is not a number."


def test_empty_input_is_still_rejected():
    ok, _, err = parse_guess("", 1, 100)
    assert ok is False
    assert err == "Enter a guess."
