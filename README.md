# CSAI Club — Leak Guard 🛡️

People paste passwords, API keys and personal info into AI chatbots every day, and
that info leaks. **Tonight you build the safety filter that scrubs secrets out of a
message before an AI ever sees it.**

It's a capture-the-flag game in two rounds:

1. **Defend.** Improve your filter so it catches every secret without blocking normal messages.
2. **Attack.** Walk to another team's laptop and try to sneak a secret past *their* filter.

You only ever edit one file: **`filter.py`**, right in your browser.

---

## Setup

Copy the line for your computer, paste it into a terminal, press Enter.

**Mac** (open the Terminal app):
```
curl -LsSf https://raw.githubusercontent.com/shreev2703/csai-leak-guard/main/install.sh | sh
```

**Windows** (open PowerShell from the Start menu):
```
powershell -ExecutionPolicy ByPass -c "irm https://raw.githubusercontent.com/shreev2703/csai-leak-guard/main/install.ps1 | iex"
```

That's it. It installs [uv](https://docs.astral.sh/uv/) (which handles Python for you),
puts the game in a `csai-leak-guard` folder in your home folder, and opens it in
your browser. The first run takes about a minute.

- **To start it again later, paste the same line again.** It keeps your changes.
- **To stop it,** press `Ctrl+C` in the terminal.
- No account, no API key, no internet needed once it's installed.
- It only runs on your own laptop (`http://127.0.0.1:8000`). Nobody on the Wi-Fi can reach it.
- Every "secret" in the game is fake.

**Got the folder some other way (zip, USB)?** Open a terminal in the
`csai-leak-guard` folder and run `uv run leakguard.py`. (No `uv` yet? Install it with
the first line of the setup command for your computer, or from
[docs.astral.sh/uv](https://docs.astral.sh/uv/getting-started/installation/).)

---

## Round 1 — Defend (blue team, 8 minutes)

1. Your browser shows your filter on the left and the scoreboard on the right.
2. Click **Run self-test**. The starter filter scores **30 / 100**: it catches a few
   secrets and misses the rest on purpose. Each miss is listed as a **LEAK**.
3. Improve `filter.py` (the three levels are below), click **Save**, test again.
4. Goal: catch every secret **without** changing the normal pizza-order messages.

## Round 2 — Attack (red team, 2 × 5 minutes)

1. Make sure your own filter is saved (switching to the Attack tab saves it for you).
2. **Walk to the next team's laptop.** There's no hacking over the network: you
   just use their screen. Open the **Attack** tab.
3. Type your team name, a message that hides a secret, and the exact secret you hid.
4. Click **Launch attack**. If the secret survives their filter, you **capture** it: **+3 points**.

Every attack shows up on the defending laptop under **Attacks on your filter**, with
the attacking team's name, so captures count themselves.

**Rules:** attack through the Attack tab only, don't touch the other team's code,
keep messages clean, and never type a real password or key.

---

## The three levels of `filter.py`

Everyone has a real job, whatever their coding level:

| Level | What you do | Example |
| --- | --- | --- |
| **1. No coding** | Add words to `BLOCKED_WORDS` | `"password"` |
| **2. Patterns** | Add a regex to `PATTERNS`: the *shape* of a secret | `r"ghp_[A-Za-z0-9]+"` |
| **3. Python** | Add your own logic inside `scan()` | redact the word that comes right after `password` |

The starter file already works, so you can't start from a blank page. You can't break
anything either: a bad edit shows the error and its line number, and **Reset to
starter** brings back the original. The Tab key inserts 4 spaces.

Regex help: [`extras/CHEATSHEET.md`](extras/CHEATSHEET.md) (every pattern you'll need).

---

## Score

- **Defend:** your self-test score at the end of round 1, divided by 10 (up to **+10**).
- **Attack:** **+3** for every secret you get past another team.
- **Bonus:** **+1** for the attack the room votes most creative.

The self-test score rewards catching secrets and punishes false alarms:
`100 × (secrets caught ÷ 10) − 60 × (normal messages blocked ÷ 10)`.
That's the real trade-off every data-loss-prevention tool fights.

---

## Troubleshooting

| Problem | Fix |
| --- | --- |
| Browser didn't open | Open the `http://127.0.0.1:...` link the terminal printed. |
| "Port in use" | It tries the next 20 ports automatically; use the link it prints. |
| My edit broke it | Read the red error and its line number, or click **Reset to starter**. |
| Windows says scripts are disabled | Make sure you pasted the *whole* line, including `powershell -ExecutionPolicy ByPass`. |
| Nothing works on my laptop | Join a teammate. Each team only needs one laptop. |

---

## What's in the folder

| File | What it is |
| --- | --- |
| `filter.py` | **The only file you edit.** Blocked words, patterns, and `scan()`. |
| `leakguard.py` | The game: a tiny local web server, the scoring and the self-test. One file, Python standard library only. |
| `ui.html` | The page you see in the browser. |
| `extras/filter_starter.py` | The original starter, used by **Reset to starter**. |
| `extras/samples.json` | The 10 secrets to catch and 10 normal messages to leave alone (all fake). |
| `extras/CHEATSHEET.md` | One-page regex cheat sheet. |
| `tests/smoke_test.py` | Automatic test of the whole game (`uv run tests/smoke_test.py`). |
| `FACILITATOR.md` | For whoever runs the meeting: setup checklist, timing, answer key. |

Run the self-test without the browser: `uv run leakguard.py --check`

Built for CSAI Club, Cybersecurity Awareness Month.
