# Leak Guard — Facilitator Guide

Everything you need to run the night, including the answer key. Members don't need this.

## Before the meeting (one time)
1. Create an empty public repo on GitHub called `csai-leak-guard`.
2. The setup links already point at `github.com/shreev2703/csai-leak-guard`.
   (If the repo ever moves to another account, run
   `python tools/set_username.py NEW-USERNAME` to update every link at once.)
3. Push:
   ```
   git init -b main && git add -A && git commit -m "Leak Guard"
   git remote add origin https://github.com/shreev2703/csai-leak-guard.git
   git push -u origin main
   ```
4. Open the repo's **Actions** tab: the tests run on Mac, Windows and Linux. Green = good.
5. Run the README's setup on your own laptop once to confirm it opens.
6. Post the setup lines in Discord that afternoon: "Paste this before you come, takes a minute."
7. Bring a zip of the folder on a USB stick as a backup.

## Timing (25-minute game block)
| Time | What happens |
| --- | --- |
| 2 min | Everyone opens the app, clicks **Run self-test**, sees 30/100 |
| 8 min | **Defend.** Teams improve `filter.py` and push their score up |
| 5 min | **Attack round 1.** Everyone moves one table clockwise |
| 5 min | **Attack round 2.** Move one more table |
| 5 min | **Debrief.** Each team reads its "Attacks on your filter" list, best attacks out loud |

**Scoring on the whiteboard:** each team's self-test score ÷ 10 at the end of
Defend, plus +3 for every capture. Captures are easy to count: every defending
laptop lists each attack, the attacking team's name, and whether it got through.

## What the starter catches and misses
The starter scores **30/100**: it catches the two `sk-` keys and the SSN. It
misses the password, card, email, phone, db password, GitHub token and AWS key on
purpose. Those are the leaks teams chase.

## Answer key: a filter that scores exactly 100
This one is tested automatically (`tests/smoke_test.py`). If a team is stuck,
give them one line at a time, not the whole thing.
```python
import re
REDACTION = "[REDACTED]"
PATTERNS = [r"sk-[A-Za-z0-9]+", r"ghp_[A-Za-z0-9]+", r"AKIA[A-Z0-9]{16}",
            r"\b\d{3}-\d{2}-\d{4}\b",                      # SSN
            r"\b\d{3}-\d{3}-\d{4}\b",                      # phone
            r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",   # email
            r"\b\d{4}[ -]\d{4}[ -]\d{4}[ -]\d{4}\b"]       # card
def scan(text):
    for p in PATTERNS:
        text = re.sub(p, REDACTION, text)
    m = re.search(r"(?i)password(?:\s+is)?[:\s]+(\S+)", text)   # value after "password"
    if m and "REDACT" not in m.group(1):
        text = text.replace(m.group(1), REDACTION)
    return text
```
The trap to point out: `\d+` or `\d{4}` would also hide the safe "order number
4539" and lose points for false alarms. The card pattern needs four groups.

## Good attacks to expect (for the debrief)
- Spacing a key out: `s k - A B C 1 2 3`
- Writing it backwards and saying "read right to left"
- Splitting it across two lines, or using words: "sk dash A B C"
- A secret format nobody wrote a pattern for

Each one beats a filter that only knows the exact shape. That's the lesson.

## Teaching points to land in the debrief
- **False positives vs false negatives.** Blocking "order 1488" is a false
  positive; missing a card is a false negative. Real tools tune this constantly.
- **Defense in depth.** No single pattern catches everything; you stack them.
- **Attackers adapt.** Every blocked attack teaches the attacker a new disguise.
- **This is real.** Samsung restricted ChatGPT internally in 2023 after engineers
  pasted source code into it. Tonight's filter is a tiny version of the
  data-loss-prevention tools companies run in front of AI.

## If something goes wrong
| Problem | Fix |
| --- | --- |
| Windows Defender blocks setup | They used an old one-line command. Have them follow the README's two Windows steps (`winget install astral-sh.uv`, then the download line). Most common snag: not reopening PowerShell after installing uv. |
| Installer won't work at all | **Manual fallback:** `git clone https://github.com/shreev2703/csai-leak-guard.git`, `cd csai-leak-guard`, `python leakguard.py` (Mac: `python3`). Needs only Python 3.9+, no packages. No git? GitHub → Code → Download ZIP. |
| A laptop won't install | Join a teammate. Every team only needs one laptop. |
| Browser didn't open | Open the `http://127.0.0.1:8000` link the terminal printed. |
| Someone broke `filter.py` | The page shows the line number; or click **Reset to starter**. |
| Wi-Fi is down | The game needs no internet once installed. Hand out the USB zip and run `uv run leakguard.py` in the folder. |
| Want a clean attack list | The Build tab's list is stored in `logs/attacks.jsonl`; delete that file. |

## Changing the secrets
Edit `extras/samples.json` (each `secret` must appear inside its `msg` exactly).
Run `uv run tests/smoke_test.py` afterwards; the "good filter reaches 100" check
may need its answer key updated to match.
