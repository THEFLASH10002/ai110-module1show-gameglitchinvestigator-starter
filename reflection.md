# 💭 Reflection: Game Glitch Investigator

Answer each question in 3 to 5 sentences. Be specific and honest about what actually happened while you worked. This is about your process, not trying to sound perfect.

*(Note: I wrote these answers myself and then had the AI read them over at the end to catch typos and tell me where I was being vague. It pushed me to put the actual numbers in instead of just saying "the score was wrong," which was fair.)*

## 1. What was broken when you started?

The first time I ran it, honestly the game looked fine. Title, difficulty dropdown, score, a box to type in. Nothing screamed broken until I actually started guessing. Then it fell apart pretty fast: the hints sent me the wrong direction every time, it let me type in numbers that weren't even in the range, and it ended a round while the screen still said I had a turn left. Nothing ever crashed, which is what made it annoying to track down. These are all logic bugs, not errors, so Python never complained once.

**Bug 1 - it ended the game and showed me the answer when I still had an attempt.**
I expected that if it says "Attempts left: 1" then I get to use that guess. Instead I made the guess and it immediately said "Out of attempts! The secret was 42" while the line right above it still said I had 1 left. Normal mode claims 8 attempts in the sidebar but I only ever got 7. When I looked at the code, `attempts` starts at `1` instead of `0`, so the count is off from the first render, and the banner gets drawn before the counter goes up so it's always one behind.

**Bug 2 - the hints were backwards, it kept saying go higher even at 100.**
I expected guessing too high to tell me to go lower. Instead I guessed 100 on Normal, which is the max, and it told me to go HIGHER. There's nowhere to go from 100. The weird part is the code actually gets the comparison right, it returns "Too High" correctly, but the message attached to it says "Go HIGHER!" The two message strings are just swapped in the return statements. So the game knew the right answer and told me the opposite anyway.

**Bug 3 - I can guess way over 100.**
The banner says guess between 1 and 100, so I expected anything outside that to get rejected. Nope, I typed 500 and it took it, used up an attempt, and gave me a hint about it. Negative numbers work too. There's no range check in `parse_guess` at all, it only checks that the text converts to a number. I also noticed the banner says "1 and 100" even on Easy mode where the range is supposed to be 1-20.

**Bug Reproduction Log**

Document at least 3 bugs you found. Add rows as needed.

| Input | Expected Behavior | Actual Behavior | Console Output / Error |
|-------|-------------------|-----------------|------------------------|
| Guess `100`, secret was 42 | "Go LOWER" since 100 is above it | "📈 Go HIGHER!" at the top of the range | none |
| Guess `5`, secret was 42 | "Go HIGHER" | "📉 Go LOWER!" | none |
| Guess `500` | Rejected, shouldn't cost an attempt | Accepted, counted as an attempt, gave a hint | none |
| Guess `-7` | Rejected | Accepted as a valid guess | none |
| Submitted my last guess while banner said "Attempts left: 1" | I get that guess | Game over + revealed the secret, banner above still said 1 left | none |
| On Easy, read the banner | Should say 1 and 20 | Still says "between 1 and 100" | none |

One more I only found by reading the code, not by playing: on every even attempt the app does `secret = str(...)` before comparing. Comparing an int to a string throws a `TypeError`, but there's an `except TypeError` block that catches it and compares them as text instead, so `"9" > "100"` comes out True and a guess of 9 gets called "Too High." Nothing ever prints to the console. That one bothered me the most because there was no way to catch it from the outside.

---

## 2. How did you use AI as a teammate?

I used Claude Code in VS Code, mostly in agent mode so it could touch `app.py`, `logic_utils.py`, and the tests at the same time. My rule for myself was to drop a `# FIXME: Logic breaks here` comment on the line I suspected first, then only ask about one bug at a time. When I gave it too much at once it started rewriting stuff I hadn't asked about. Reading every diff before accepting it was the part that actually mattered, especially since an AI wrote this broken code in the first place.

**Something it got right: the refactor and the swapped hints.**
I gave it one instruction with a few steps in it: move `check_guess` into `logic_utils.py`, fix the high/low bug, update the import. It figured out that the comparison logic was never wrong, only the message strings were swapped, which I hadn't realized. I'd assumed the whole function was broken. It also suggested putting the messages in a dictionary so the outcome and the text can't get separated again. I checked it by running pytest, where my test asserts a guess of 100 against a secret of 42 comes back "Too High" and the hint does *not* contain "HIGHER". Then I reloaded the game and guessed 100 and finally got "Go LOWER!"

**Something it got wrong: it trusted a comment over the tests.**
The stub in `logic_utils.py` had a docstring saying `check_guess` returns a tuple of `(outcome, message)`, and `app.py` unpacked it that way too. So when I asked the AI to write the function, it returned a tuple. Totally reasonable, it matched the docstring and the call site. But it's wrong here, because the starter test does `assert check_guess(60, 50) == "Too High"` against a plain string. A tuple is never going to equal a string, so all three starter tests would've stayed red no matter how good the logic was. I only caught it because I ran pytest instead of assuming it worked. I fixed it by having `check_guess` return just the outcome and adding a separate `get_hint_message()` for the emoji text. That made the starter tests pass without me editing them, which felt like the right call since I shouldn't be changing the tests to match my code. The thing I took away is that the AI believed a comment that was itself part of the bug.

**Something that was close but would've broken the game.**
I asked it to add the range check to `parse_guess` and it wrote a clean one, but it stopped there. That alone would've made the game impossible to win, because "New Game" called `random.randint(1, 100)` no matter what difficulty you picked. So on Easy you could get a secret of 73 and my new validation would refuse to let me type it. I caught that by thinking through the Easy case, not by running it. I didn't throw the whole edit away, I just pointed at that line and asked for a follow-up.

---

## 3. Debugging and testing your fixes

I only counted a bug as fixed if it failed and then passed in three places: calling the function directly, pytest, and the actual game in the browser. I ran pytest before changing anything and got 3 failed, since every function in `logic_utils.py` was still a stub that raised `NotImplementedError`. Having that baseline mattered, otherwise a green test later doesn't really prove anything. I also did one bug at a time and re-ran the suite after each, so when something broke I knew what broke it.

The test that taught me the most was `test_string_secret_still_compares_as_a_number`, which asserts `check_guess(9, "100")` returns "Too Low". My first instinct was to just delete the `str()` line in `app.py` and call it done. But writing a test that deliberately passes a string made me fix it properly by converting both values with `int()` inside `check_guess`. That kills the whole category of bug instead of the one place it happened to show up. I also wrote `test_range_boundaries_are_inclusive` for Bug 3 because off-by-one at 1 and 100 is exactly the thing I'd never notice just by playing. Ended up at 14 passing, 3 starter and 11 mine.

AI helped me come up with edge cases I wouldn't have thought of, like whitespace in the input and the boundary values. But I had to push back on how it wrote the assertions. It wanted to check the hint string exactly, emoji and all, which would break the second anybody reworded the message. I changed those to just look for "LOWER" or "HIGHER" so the test checks the behavior and not the decoration. The other thing I learned is that reading the diff catches stuff tests don't. While reviewing my own changes I noticed "New Game" never resets `status`, so after you lose it reruns, hits the game over check, and stops. The button does nothing. No test would've caught that because it's Streamlit flow, not logic. I left it as a FIXME.

---

## 4. What did you learn about Streamlit and state?

The way I'd explain it is that Streamlit re-runs your entire file from the top every single time you touch anything. Click a button, type in a box, change a dropdown, and the whole script runs again from line 1. So a normal variable is useless, because it gets recreated from scratch on every interaction. That's why the secret number would reset if you stored it in a plain variable, and it's basically the whole reason this game was broken in weird ways.

`st.session_state` is the workaround. It's a dictionary that survives between re-runs, so anything you want to keep (the secret, the score, the attempt count) has to live in there. The `if "secret" not in st.session_state:` pattern is how you say "only set this the first time, don't overwrite it on every re-run."

What actually tripped me up was the order things run in. The banner showing "Attempts left" gets drawn near the top of the file, but the code that increases the counter is near the bottom. So on the run where you submit a guess, the banner already rendered with the old number before the counter changed. The number on screen is stale by one, and you don't see the update until the *next* re-run. I would not have guessed that from looking at the code. It only clicked once I started thinking about the file as a script that runs top to bottom, not as a UI that updates when data changes.

---

## 5. Looking ahead: your developer habits

The habit I want to keep is running the tests *before* I fix anything. Seeing 3 failed at the start meant that when it said 14 passed later, I knew my changes did that. If I'd just written the fix and run the tests once at the end I would've had no idea whether they were passing because of me or because they were weak tests. Marking the suspicious line with a FIXME comment before asking the AI anything was also way more useful than I expected, it gave me something concrete to point at instead of describing the bug in a paragraph.

Next time I'd ask the AI for smaller changes. A couple of times I accepted a big multi-file edit and then had to read a diff that touched things I never asked about, which took longer than doing it in two steps would have. I'd also stop assuming a fix works because the code looks right. The range check *looked* perfect and would've made the game unwinnable.

Mostly this changed how much I trust code that looks finished. This whole app ran without a single error and was completely broken. No red squiggles, no stack traces, nothing in the console, and the hints were confidently telling me the exact opposite of the truth. AI writes code that looks right, and "looks right" and "is right" turn out to be pretty different things. I don't think that means don't use it, it saved me a lot of time on the refactor. It just means I'm the one who has to verify, and tests are how you do that instead of going off vibes.
