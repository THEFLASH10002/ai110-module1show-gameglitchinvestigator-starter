# 🎮 Game Glitch Investigator: The Impossible Guesser

## 🚨 The Situation

You asked an AI to build a simple "Number Guessing Game" using Streamlit.
It wrote the code, ran away, and now the game is unplayable. 

- You can't win.
- The hints lie to you.
- The secret number seems to have commitment issues.

## 🛠️ Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Run the broken app: `python -m streamlit run app.py`

## 🕵️‍♂️ Your Mission

1. **Play the game.** Open the "Developer Debug Info" tab in the app to see the secret number. Try to win.
2. **Find the State Bug.** Why does the secret number change every time you click "Submit"? Ask ChatGPT: *"How do I keep a variable from resetting in Streamlit when I click a button?"*
3. **Fix the Logic.** The hints ("Higher/Lower") are wrong. Fix them.
4. **Refactor & Test.** - Move the logic into `logic_utils.py`.
   - Run `pytest` in your terminal.
   - Keep fixing until all tests pass!

## 📝 Document Your Experience

**What the game is supposed to do.** It's a number guessing game built with Streamlit. You pick a difficulty in the sidebar, the game picks a secret number in that range, and you get a limited number of attempts to find it. After each guess it tells you whether to go higher or lower and updates your score.

**Bugs I found.**

1. **The hints were backwards.** Guessing above the secret told me to go HIGHER. I guessed 100 on Normal and it still said "Go HIGHER!", which is impossible.
2. **I could guess numbers outside the range.** Typing 500 or -7 was accepted as a valid guess and used up one of my attempts.
3. **The game ended while the screen said I still had an attempt left**, and then showed me the answer. On Normal it promises 8 attempts but I only got 7.

**Fixes I applied.** I fixed the first two.

- Moved `check_guess` and `parse_guess` out of `app.py` and into `logic_utils.py` so the rules can be tested without launching Streamlit.
- Fixed the swapped hint messages, and replaced them with a lookup table so the outcome and the text can't get out of sync again.
- Removed a line in `app.py` that turned the secret into a string on even-numbered attempts. That was quietly making the game compare numbers as text, so `"9" > "100"` was True.
- Added a range check to `parse_guess`, made the banner show the real difficulty range instead of a hard-coded 1 to 100, and stopped rejected input from costing an attempt.
- Made "New Game" use the difficulty's range. I had to do this one: once guesses are range-checked, an Easy game (1-20) that rolled a secret of 73 would be impossible to win.

**Still broken on purpose** (marked with `FIXME` for the next round): the attempts off-by-one, a scoring bug where a wrong guess on an even attempt *adds* 5 points, and the "New Game" button doing nothing after you lose because it never resets `status`.

## 📸 Demo Walkthrough

A real playthrough on **Normal** difficulty (range 1-100), where the secret was **42**:

1. I type **40** and hit Submit → "📈 Go HIGHER!" — score drops to **-5**.
2. I type **70** → "📉 Go LOWER!" — the hint now points the right way, so I know the answer is between 40 and 70. Score **-10**.
3. I type **500** → rejected with "Out of range. Guess a number between 1 and 100." The attempt counter does **not** move and my score stays at -10. Before the fix this was accepted as a real guess.
4. I type **50** → "📉 Go LOWER!" Score goes **up** to -5, which is wrong — that's the scoring bug I haven't fixed yet.
5. I type **42** → balloons, "🎉 Correct!" and "You won! The secret was 42. Final score: 35." The game locks and tells me to start a new one.

If I switch the sidebar to **Easy**, the banner changes to "Guess a number between 1 and 20" and a guess of 50 gets rejected. Before the fix the banner always claimed 1 to 100 no matter what difficulty was selected.

## 🧪 Test Results

I did the edge-case testing challenge, so this covers the boundary values (1, 100, 0, 101), negative numbers, empty input, non-numeric input, and a string secret.

```
$ python -m pytest tests/ -v
============================= test session starts =============================
platform win32 -- Python 3.14.3, pytest-9.1.1, pluggy-1.6.0
cachedir: .pytest_cache
rootdir: C:\Users\kenne\OneDrive\Documents\GitHub\ai110-module1show-gameglitchinvestigator-starter1
plugins: anyio-4.13.0
collecting ... collected 14 items

tests/test_game_logic.py::test_winning_guess PASSED                      [  7%]
tests/test_game_logic.py::test_guess_too_high PASSED                     [ 14%]
tests/test_game_logic.py::test_guess_too_low PASSED                      [ 21%]
tests/test_game_logic.py::test_hint_for_too_high_says_go_lower PASSED    [ 28%]
tests/test_game_logic.py::test_hint_for_too_low_says_go_higher PASSED    [ 35%]
tests/test_game_logic.py::test_top_of_range_guess_is_never_too_low PASSED [ 42%]
tests/test_game_logic.py::test_string_secret_still_compares_as_a_number PASSED [ 50%]
tests/test_game_logic.py::test_guess_above_range_is_rejected PASSED      [ 57%]
tests/test_game_logic.py::test_negative_guess_is_rejected PASSED         [ 64%]
tests/test_game_logic.py::test_guess_outside_easy_range_is_rejected PASSED [ 71%]
tests/test_game_logic.py::test_guess_inside_range_is_accepted PASSED     [ 78%]
tests/test_game_logic.py::test_range_boundaries_are_inclusive PASSED     [ 85%]
tests/test_game_logic.py::test_non_numeric_input_is_still_rejected PASSED [ 92%]
tests/test_game_logic.py::test_empty_input_is_still_rejected PASSED      [100%]

============================= 14 passed in 0.06s ==============================
```

Before I started, all 3 of the starter tests failed with `NotImplementedError` because every function in `logic_utils.py` was still an empty stub.

## 🚀 Stretch Features

- [ ] [If you choose to complete Challenge 4, describe the Enhanced UI changes here — a screenshot is optional]
