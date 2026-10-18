"""
filter.py  —  THIS IS THE ONLY FILE YOU EDIT
=============================================

Your job: find secrets in a message and replace them with [REDACTED], WITHOUT
wrecking normal messages like "I'd like a large pepperoni".

You improve the filter in three levels. Do as many as you can:

    LEVEL 1  (no real coding) : add words to BLOCKED_WORDS
    LEVEL 2  (patterns)       : add regex patterns to PATTERNS
    LEVEL 3  (Python)         : add your own logic at the bottom of scan()

After any change, SAVE this file, then click "Run self-test" in the browser.
The starter already catches a few things. It misses plenty on purpose. Go find
the leaks the self-test reports and close them.

Cheat sheet for regex:  extras/CHEATSHEET.md
"""

import re

REDACTION = "[REDACTED]"


# ─────────────────────────────────────────────────────────────────────────────
# LEVEL 1 — BLOCKED WORDS
# Any message containing one of these words (case-insensitive) has that word
# redacted. Great for obvious giveaways. Add your own between the quotes.
# ─────────────────────────────────────────────────────────────────────────────
BLOCKED_WORDS = [
    "password",
    # "hunter2pizza!",     # <- try adding the exact secrets the self-test shows
]


# ─────────────────────────────────────────────────────────────────────────────
# LEVEL 2 — PATTERNS (regex)
# Each pattern describes the SHAPE of a secret, so you catch ones you've never
# seen. Example: "sk-" followed by a bunch of letters/numbers is an API key.
# Add patterns to this list. Each is a raw string:  r"...."
# ─────────────────────────────────────────────────────────────────────────────
PATTERNS = [
    r"sk-[A-Za-z0-9]+",                 # API keys that start with sk-
    r"\b\d{3}-\d{2}-\d{4}\b",           # US SSN like 123-45-6789
    # r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",   # <- email? try it
    # r"\b\d{4}[ -]\d{4}[ -]\d{4}[ -]\d{4}\b",        # <- credit card numbers? try it
]


# ─────────────────────────────────────────────────────────────────────────────
# scan(text)  — the engine calls this. Return the cleaned text.
# You can also return (cleaned_text, list_of_things_you_caught) if you want the
# browser to show what you caught. Most teams won't need to touch the top of
# this function — add your LEVEL 3 ideas where it says "YOUR CODE HERE".
# ─────────────────────────────────────────────────────────────────────────────
def scan(text):
    cleaned = text
    hits = []

    # Level 1: blocked words
    for word in BLOCKED_WORDS:
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        if pattern.search(cleaned):
            hits.append(word)
            cleaned = pattern.sub(REDACTION, cleaned)

    # Level 2: patterns
    for pat in PATTERNS:
        if re.search(pat, cleaned):
            hits.append(pat)
            cleaned = re.sub(pat, REDACTION, cleaned)

    # ── LEVEL 3 — YOUR CODE HERE ──────────────────────────────────────────────
    # Some secrets have no shape, but you can spot them by the words AROUND them.
    # Tip: SEARCH the original `text`, then EDIT `cleaned` (Level 1 may already
    # have hidden the word "password" inside `cleaned`).
    #
    # Example: hide whatever comes right after "password" or "password is:".
    # To turn it on, delete the "# " at the start of the 3 lines below.
    #
    # m = re.search(r"password(?: is)?[:\s]+(\S+)", text, re.IGNORECASE)
    # if m:
    #     cleaned = cleaned.replace(m.group(1), REDACTION)
    #
    # More ideas, roughly easiest to hardest:
    #   • the same trick for "token=" or "key:"
    #   • a secret split across a line break (the message has a "\n" in it)
    #   • a card number, but NOT an order number like "order 1488"
    # ──────────────────────────────────────────────────────────────────────────

    return cleaned, hits
