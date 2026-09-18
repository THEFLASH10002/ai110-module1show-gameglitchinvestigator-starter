# 💭 Reflection: Game Glitch Investigator

Answer each question in 3 to 5 sentences. Be specific and honest about what actually happened while you worked. This is about your process, not trying to sound perfect.

## 1. What was broken when you started?

The first time I ran `python -m streamlit run app.py` the game looked completely finished. It had a title, a difficulty selector in the sidebar, a score, an attempt counter, and a text box for guesses, so nothing looked suspicious until I actually started guessing. Once I played a few rounds it fell apart fast: the hints pointed me the wrong direction, the game let me type numbers that were nowhere near the allowed range, and it ended a round while the screen was still telling me I had an attempt left. The code runs without crashing, which is exactly what made it tricky, because every one of these bugs is a logic error and not a syntax error. Below are the three bugs I could reproduce on demand.

**Bug 1 - The game ended and revealed the answer while the screen still said I had an attempt left.**
I expected that if the banner said "Attempts left: 1," I would get to make that one final guess, and only after using it would the game end and show me the secret number. What actually happened was that I made that guess and the game immediately printed "Out of attempts! The secret was 42" on the same screen where the banner above it still read "Attempts left: 1." On Normal difficulty the sidebar promises 8 attempts, but I only ever got to make 7 guesses. Looking at the code, `st.session_state.attempts` is initialized to `1` instead of `0` in [app.py](app.py), so the counter is off by one from the very first render, and the "attempts left" banner is drawn before the submit handler increments the counter, so the number on screen is always stale. A related problem is that the "Developer Debug Info" expander prints the secret number directly on the page, so the answer is visible the whole game if you open it.

**Bug 2 - The hints are backwards, so it kept telling me to go HIGHER even when I guessed 100.**
I expected that guessing a number above the secret would tell me to go lower, and guessing below it would tell me to go higher. Instead the arrows and the words were swapped: I guessed 100 on Normal difficulty (the top of the range) and it still told me "Go HIGHER!", which is impossible advice. The internal outcome label is actually correct - `check_guess` correctly returns `"Too High"` when `guess > secret` - but the message paired with it is `"Go HIGHER!"` and the `"Too Low"` branch is paired with `"Go LOWER!"`. The two message strings are simply swapped in the return statements, so the game's own logic knows the right answer and then tells the player the opposite.

**Bug 3 - I can guess numbers way outside the allowed range.**
I expected the game to reject anything outside the stated range and not charge me an attempt for it, since the banner says to guess between 1 and 100. Instead I typed 500 and the game happily accepted it, burned one of my attempts, and gave me a hint about it. Negative numbers like -7 work too. The `parse_guess` function in [app.py](app.py) only checks that the input converts to an integer and never compares it against `low` and `high`, so there is no bounds validation at all. This bug also exposed a second one next to it: the range is supposed to change with difficulty (Easy is 1-20 and Hard is 1-50), but the banner is hard-coded to say "between 1 and 100" no matter what difficulty is selected, and the "New Game" button calls `random.randint(1, 100)` and ignores the difficulty range completely.

**Bug Reproduction Log**

Document at least 3 bugs you found. Add rows as needed.

| Input | Expected Behavior | Actual Behavior | Console Output / Error |
|-------|-------------------|-----------------|------------------------|
| Normal difficulty, guess `100` while the secret was 42 | Hint reads "Go LOWER" because 100 is above the secret | Hint reads "📈 Go HIGHER!" even though 100 is the top of the range | none - no error, the app renders normally |
| Normal difficulty, guess `5` while the secret was 42 | Hint reads "Go HIGHER" because 5 is below the secret | Hint reads "📉 Go LOWER!" | none |
| Normal difficulty, guess `500` | Input rejected as out of range, attempt not counted | Guess accepted, counted as an attempt, and a hint was shown for it | none - `parse_guess("500")` returns `(True, 500, None)` |
| Normal difficulty, guess `-7` | Input rejected as out of range | Guess accepted as a valid number and counted as an attempt | none - `parse_guess("-7")` returns `(True, -7, None)` |
| Normal difficulty, submit the 7th guess while the banner reads "Attempts left: 1" | I get to use that last attempt; game continues if I am wrong | Game immediately ended with "Out of attempts! The secret was 42" while the banner above still read "Attempts left: 1" | none |
| Easy difficulty selected, then read the guess banner | Banner should say "between 1 and 20" to match the Easy range | Banner still says "Guess a number between 1 and 100" | none |
| Guess `9` on the 2nd attempt while the secret was 100 | Hint reads "Go HIGHER" because 9 is far below 100 | Hint reads "📈 Go HIGHER!" but for the wrong reason - it classified 9 as *Too High* | none - a `TypeError` is raised internally but silently swallowed by the `except TypeError` block, which then compares `"9" > "100"` as text |

On that last row, I found that on every even-numbered attempt the app converts the secret to a string with `secret = str(st.session_state.secret)` before calling `check_guess`. Comparing an `int` to a `str` raises a `TypeError`, but the function catches it and falls back to comparing the two values as text, so `"9" > "100"` is True and a guess of 9 gets labeled "Too High." The error never reaches the console, which is why I only found it by reading the code after the hints looked random.

---

## 2. How did you use AI as a teammate?

I used Claude Code inside VS Code as my AI coding assistant, mostly in agent mode so it could edit `app.py`, `logic_utils.py`, and the test file together and I could read the diff before keeping anything. My workflow was to mark the crime scene with a `# FIXME: Logic breaks here` comment first, then work one bug at a time so the AI stayed focused on a single problem instead of rewriting the whole game at once. I treated it like a fast pair programmer that needs checking rather than an authority, because this entire codebase was AI-generated and buggy in the first place, which was a good reminder not to trust confident-looking output.

**A suggestion that was correct: refactoring `check_guess` and fixing the swapped hints.**
I gave it a multi-step instruction: move `check_guess` into `logic_utils.py`, fix the high/low bug, and update the import in `app.py`. It correctly found that the outcome labels were never wrong at all - `check_guess` already returned `"Too High"` when `guess > secret` - and that the actual defect was the message strings being swapped in the return statements. It replaced them with a `HINT_MESSAGES` dictionary so the outcome and the text can't drift apart again. I verified it two ways: I ran `pytest`, where my new `test_top_of_range_guess_is_never_too_low` asserts that a guess of 100 against a secret of 42 returns `"Too High"` and that the hint does **not** contain the word "HIGHER", and then I reloaded the live game and guessed 100 on Normal and finally got "📉 Go LOWER!" instead of the impossible advice from before.

**A suggestion that was misleading: the starter docstring's return contract.**
The AI-written stub in `logic_utils.py` documented `check_guess` as returning a tuple of `(outcome, message)`, and `app.py` unpacked it that way with `outcome, message = check_guess(...)`. When I first asked the AI to implement the function, it followed that docstring and returned a tuple - which looked completely reasonable and matched the existing call site. It was wrong for this project, because the starter test in `tests/test_game_logic.py` asserts `check_guess(60, 50) == "Too High"`, comparing against a plain string. A tuple can never equal a string, so following the AI's own docstring would have left all three starter tests failing no matter how correct the high/low logic was. I caught this by running `pytest` before and after instead of assuming the fix worked, and I resolved it by having `check_guess` return only the outcome string and adding a separate `get_hint_message(outcome)` function for the UI text. That satisfied the starter tests unmodified and gave better separation anyway, since the comparison logic no longer knows anything about emoji. The lesson was that the AI trusted a comment over the tests, and the comment was part of the bug.

**A second suggestion I had to correct: a fix that was 90% right.**
When I asked it to add bounds checking to `parse_guess`, it wrote a clean check but stopped there. That patch would have made the game *unwinnable*: the "New Game" button called `random.randint(1, 100)` regardless of difficulty, so an Easy game (range 1-20) could hold a secret of 73 that my new validation would refuse to let me guess. I found this by thinking through the Easy case rather than by running it. Instead of discarding the whole edit, I highlighted that line and asked for a targeted follow-up, which produced the range-aware `random.randint(low, high)` and a reset when the difficulty changes mid-game. It also originally kept the old `parse_guess(raw)` signature, so I had it thread `low`/`high` through from `get_range_for_difficulty`.

---

## 3. Debugging and testing your fixes

I decided a bug was really fixed only when it failed in three places and then passed in all three: a direct call to the function, a `pytest` run, and the live game in the browser. Before touching anything I ran `pytest` to get a baseline, which was **3 failed** because every function in `logic_utils.py` was still a `raise NotImplementedError` stub. That baseline mattered, because it meant a passing test later actually proved something instead of passing by accident. I also worked one bug at a time and re-ran the suite after each change, so if something broke I knew exactly which edit caused it.

The most useful test I wrote was the one that came straight out of the bug report: `test_top_of_range_guess_is_never_too_low`, which calls `check_guess(100, 42)` and asserts the outcome is `"Too High"` and that `get_hint_message` does not contain "HIGHER". I also wrote `test_string_secret_still_compares_as_a_number`, which asserts `check_guess(9, "100") == "Too Low"`. That second one taught me the most about my own code. The original bug was hidden because `app.py` cast the secret to a string on even attempts, `check_guess` raised a `TypeError`, and the `except TypeError:` block silently caught it and compared `"9" > "100"` as text - so the game gave a confidently wrong hint and printed nothing to the console. Writing a test that passes a string on purpose forced me to make `check_guess` coerce both values with `int()` rather than just deleting the bad line in `app.py`, which kills the whole category of bug instead of the one instance of it.

For Bug 3 I wrote `test_range_boundaries_are_inclusive` to pin down the edges, since off-by-one errors at 1 and 100 are exactly the kind of thing I would not notice by playing. It checks that 1 and 100 are accepted while 0 and 101 are rejected. My final suite is **14 passing tests**: the 3 original starter tests plus 11 I added. I finished by running `python -m streamlit run app.py` and manually replaying every row of my bug reproduction table from Phase 1 - guessing 100, guessing 500, guessing -7, and switching to Easy to confirm the banner now says "between 1 and 20" instead of 1 and 100.

The AI helped design the tests, but I had to push back on how it verified things. Its instinct was to assert on the exact hint string including the emoji, which would break the moment anyone reworded the message; I changed those to check for the substring "LOWER" or "HIGHER" so the test checks the behavior I actually care about instead of the decoration. It was genuinely good at suggesting edge cases I had not considered, like whitespace input and the inclusive boundary values. One habit I picked up is that reviewing the diff catches things tests do not: while reading the final diff I noticed the "New Game" button never resets `status`, so after a loss it reruns, hits the `status != "playing"` check, and calls `st.stop()` - meaning the button silently does nothing. No test covered that because it lives in Streamlit UI flow, not in `logic_utils.py`. I left it marked with a `FIXME` for the next round along with the attempts off-by-one and the scoring bug.

---

## 4. What did you learn about Streamlit and state?

- How would you explain Streamlit "reruns" and session state to a friend who has never used Streamlit?

---

## 5. Looking ahead: your developer habits

- What is one habit or strategy from this project that you want to reuse in future labs or projects?
  - This could be a testing habit, a prompting strategy, or a way you used Git.
- What is one thing you would do differently next time you work with AI on a coding task?
- In one or two sentences, describe how this project changed the way you think about AI generated code.
