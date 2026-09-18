# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agent Workflow (SF8)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

I used Claude Code in VS Code in agent mode. The main instruction I gave it was a multi-step one: "Move the `check_guess` function to `logic_utils.py`, update the logic to fix the high/low bug, and update the import in `app.py`." I gave it a second, separate one later for the range bug: add bounds checking to `parse_guess` and move it into `logic_utils.py` too. I deliberately kept these as two different conversations so it stayed on one bug at a time, because when I gave it more than that it started changing things I hadn't asked about.

**What did the agent do?**

- Read `app.py`, `logic_utils.py`, and `tests/test_game_logic.py` to see how the UI and logic files related to each other.
- Ran `pytest` first to get a baseline (3 failed, all `NotImplementedError` from the empty stubs).
- Moved `check_guess` into `logic_utils.py`, fixed the swapped hint messages, and replaced them with a `HINT_MESSAGES` dictionary.
- Moved `parse_guess` and `get_range_for_difficulty` over, added the range check, and threaded `low`/`high` through from the caller.
- Updated the imports in `app.py` and deleted the old local copies.
- Wrote 11 new regression tests and re-ran `pytest` after each bug (14 passing at the end).
- Restarted the Streamlit app so I could confirm the fixes in the browser.

**What did you have to verify or fix manually?**

Three things:

1. **The return type was wrong.** It implemented `check_guess` to return a `(outcome, message)` tuple, because that's what the stub's docstring said and how `app.py` unpacked it. But the starter test asserts `check_guess(60, 50) == "Too High"` against a plain string, so all three starter tests would have stayed red. I had it return just the outcome string and add a separate `get_hint_message()` instead. The AI trusted a docstring that was itself part of the bug.
2. **The range fix was incomplete and would have made the game unwinnable.** It added bounds checking to `parse_guess` but left "New Game" calling `random.randint(1, 100)` regardless of difficulty. On Easy (1-20) you could get a secret of 73 that the new validation would refuse to let you type. I pointed at that line and asked for a targeted follow-up rather than discarding the whole edit.
3. **It left the attempt counter in the wrong place.** The increment still happened before parsing, so rejected input kept costing a turn. I moved it into the valid branch myself.

I also told it *not* to fix the scoring bug in the same pass, so the refactor stayed reviewable and that bug could get its own commit.

---

## Test Generation (SF7)

> Document how you used AI to help generate or improve tests.

| Edge Case | Prompt Used | AI-Suggested Test | Did It Pass? | Your Reasoning |
|-----------|-------------|-------------------|--------------|----------------|
| Guess at the top of the range | "Write a pytest case for the bug where guessing 100 still said Go HIGHER" | `test_top_of_range_guess_is_never_too_low` — asserts `check_guess(100, 42) == "Too High"` and that the hint doesn't contain "HIGHER" | Yes, after the fix | This is the exact bug from my report, so it's the one test I most wanted. I changed its assertion from an exact emoji string match to a substring check so rewording the message won't break it. |
| Secret passed in as a string | "What happens if the secret is a string instead of an int?" | `test_string_secret_still_compares_as_a_number` — asserts `check_guess(9, "100") == "Too Low"` | Yes, after adding `int()` coercion | This was the most useful one. My instinct was to just delete the `str()` line in `app.py`, but this test made me fix it inside `check_guess` so the whole category of bug dies instead of one instance. |
| Range boundaries (1, 100, 0, 101) | "Add tests for the inclusive boundaries of the guess range" | `test_range_boundaries_are_inclusive` — 1 and 100 accepted, 0 and 101 rejected | Yes | Off-by-one at the edges is exactly what I'd never catch by playing. I wouldn't have thought to test 0 and 101 specifically. |
| Negative input | "What other invalid inputs should I test?" | `test_negative_guess_is_rejected` — `parse_guess("-7", 1, 100)` returns `ok=False` | Yes, after the fix | Came straight out of my bug log. `-7` used to be accepted as a real guess. |
| Out-of-range on a *different* difficulty | Same prompt as above | `test_guess_outside_easy_range_is_rejected` — 50 is valid on Normal but rejected on Easy (1-20) | Yes | This one caught that the bounds have to come from the difficulty, not be hard-coded. Good catch by the AI. |
| Whitespace / empty / non-numeric input | "What other invalid inputs should I test?" | `test_non_numeric_input_is_still_rejected`, `test_empty_input_is_still_rejected` | Yes | These were already handled by the original code, so they're guard-rail tests to make sure my refactor didn't break behavior that already worked. |

**Overall:** the AI was genuinely good at suggesting edge cases I hadn't considered (whitespace, the 0/101 boundaries, the cross-difficulty case). Where I had to override it was in *how* it asserted things — it kept wanting to compare the full hint string including the emoji, which tests the decoration rather than the behavior.
