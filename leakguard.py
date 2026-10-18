#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""
CSAI Club - Leak Guard
======================

People paste passwords, API keys and personal info into AI chatbots every day.
Companies have banned AI tools over it. Your job tonight: build the safety layer
that sits in front of the AI and scrubs secrets OUT of a message before the AI
(or anyone logging it) ever sees them.

    uv run leakguard.py           start it (opens your browser)
    uv run leakguard.py --check   run the test set in the terminal and exit

You only ever edit ONE file: filter.py

How a message flows:

    user types a message  ->  YOUR filter: scan()  ->  redacted message  ->  AI
                                     |
                              catches secrets and
                              replaces them with [REDACTED]

A good filter catches real secrets (high "catch rate") without blocking normal
messages like "I'd like a large pepperoni" (low "false alarms"). That trade-off
is the whole game, and it is exactly what real data-loss-prevention tools fight.

This file is the game engine. You do not need to read it to play. The pieces:
    1. SETTINGS
    2. FILTER LOADER     reloads filter.py every time you save it (no restart)
    3. SAMPLE MESSAGES   the secrets to catch and the normal messages to leave alone
    4. SCORING           catch rate, false alarms, and a single score out of 100
    5. REDACTION         run a team's filter over a message, safely
    6. WEB SERVER        the page + API, on THIS laptop only (127.0.0.1)
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# Windows terminals sometimes choke on unicode. Never crash over a print.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = Path(__file__).resolve().parent
FILTER_FILE = HERE / "filter.py"
STARTER_FILE = HERE / "extras" / "filter_starter.py"
UI_FILE = HERE / "ui.html"
SAMPLES_FILE = HERE / "extras" / "samples.json"

REDACTION = "[REDACTED]"
MAX_CHARS = 4000


# ═════════════════════════════════════════════════════════════════════════════
# 2. FILTER LOADER  — re-reads filter.py whenever it changes, and never crashes
# ═════════════════════════════════════════════════════════════════════════════

def _err_line(exc: BaseException) -> "int | None":
    for frame in reversed(traceback.extract_tb(exc.__traceback__)):
        if Path(frame.filename).name == "filter.py":
            return frame.lineno
    return getattr(exc, "lineno", None)


def describe_error(exc: BaseException) -> str:
    """Turn a Python error into one friendly sentence a beginner can act on."""
    line = _err_line(exc)
    at = f" on line {line}" if line else ""
    if isinstance(exc, SyntaxError):
        return f"Syntax error{at}: {exc.msg}. Look for a missing quote, comma, bracket or colon."
    if isinstance(exc, IndentationError):
        return f"Indentation error{at}: {exc.msg}. Check your spaces line up."
    if isinstance(exc, re_error()):
        return f"Problem with one of your regex patterns: {exc}. Check extras/CHEATSHEET.md."
    return f"filter.py had a problem{at}: {type(exc).__name__}: {exc}"


def re_error():
    import re
    return re.error


class FilterCode:
    """Loads filter.py in its own namespace. Reloads only when the file changes."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._sig = None
        self.scan = None          # the team's scan(text) -> (clean_text, hits)
        self.error = None         # a friendly message if the file won't load

    def _read_text(self) -> str:
        raw = FILTER_FILE.read_bytes()
        for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
            try:
                return raw.decode(enc)
            except UnicodeDecodeError:
                continue
        return raw.decode("utf-8", errors="replace")

    def refresh(self) -> "FilterCode":
        with self._lock:
            try:
                st = FILTER_FILE.stat()
                sig = (st.st_mtime_ns, st.st_size)
            except FileNotFoundError:
                self.scan, self.error, self._sig = None, "filter.py is missing. Paste the setup line again to restore it.", None
                return self
            if sig == self._sig and (self.scan or self.error):
                return self
            self._sig = sig
            ns: dict = {"REDACTION": REDACTION}
            try:
                code = compile(self._read_text(), "filter.py", "exec")
                exec(code, ns)
                fn = ns.get("scan")
                if not callable(fn):
                    self.scan, self.error = None, "filter.py must define a function called scan(text)."
                else:
                    self.scan, self.error = fn, None
            except BaseException as exc:  # noqa: BLE001 - we want to show ANY error, not crash
                self.scan, self.error = None, describe_error(exc)
            return self


# ═════════════════════════════════════════════════════════════════════════════
# 3. SAMPLE MESSAGES  — what a good filter should CATCH, and what it should LEAVE
# ═════════════════════════════════════════════════════════════════════════════
# "secrets" must be caught (redacted). "safe" messages must pass through untouched.
# A filter that blocks the safe ones is annoying; a filter that misses the secrets
# is dangerous. The self-test measures both. All values here are fake.

BUILTIN_SECRETS = [
    {"msg": "my api key is sk-9F2kQ7mZ1aB4cD8e so use that", "secret": "sk-9F2kQ7mZ1aB4cD8e"},
    {"msg": "login with password Hunter2Pizza! please", "secret": "Hunter2Pizza!"},
    {"msg": "charge my card 4539 1488 0343 6467", "secret": "4539 1488 0343 6467"},
    {"msg": "email me at jordan.diaz@example.com with the receipt", "secret": "jordan.diaz@example.com"},
    {"msg": "my ssn is 123-45-6789 for the form", "secret": "123-45-6789"},
    {"msg": "call me on 805-555-0147 after 5", "secret": "805-555-0147"},
    {"msg": "the db password is: p1zz4_s3cr3t_db", "secret": "p1zz4_s3cr3t_db"},
    {"msg": "token=ghp_AbCdEf123456GhIjKlMnOpQrStUvWx go", "secret": "ghp_AbCdEf123456GhIjKlMnOpQrStUvWx"},
    {"msg": "aws key AKIA1234567890ABCDEF for the bucket", "secret": "AKIA1234567890ABCDEF"},
    {"msg": "here is the key:\nsk-77AA88BB99CC00DD\nthanks", "secret": "sk-77AA88BB99CC00DD"},
]

BUILTIN_SAFE = [
    "I'd like a large pepperoni pizza please",
    "what time do you close on sunday?",
    "do you have gluten free crust",
    "can I add extra cheese to order 1488",
    "the pizza was great, 10/10 would order again",
    "is the garlic bread vegan",
    "my order number is 4539 can you check it",
    "I'll pick it up at 5 today",
    "add a 2 liter coke to that",
    "thanks so much, see you soon!",
]


def load_samples() -> dict:
    """Use extras/samples.json if present, else the built-in set above."""
    try:
        data = json.loads(SAMPLES_FILE.read_text("utf-8"))
        secrets = [s for s in data.get("secrets", []) if "msg" in s and "secret" in s]
        safe = [s for s in data.get("safe", []) if isinstance(s, str)]
        if secrets and safe:
            return {"secrets": secrets, "safe": safe}
    except Exception:
        pass
    return {"secrets": BUILTIN_SECRETS, "safe": BUILTIN_SAFE}


# ═════════════════════════════════════════════════════════════════════════════
# 4. REDACTION  — run a team's scan() over one message, safely
# ═════════════════════════════════════════════════════════════════════════════

def _norm(result, original: str):
    """
    Teams may return just the cleaned string, or (cleaned, hits). Accept both,
    and never trust the types blindly.
    """
    if isinstance(result, tuple):
        cleaned = result[0]
        hits = result[1] if len(result) > 1 else None
    else:
        cleaned, hits = result, None
    cleaned = original if cleaned is None else str(cleaned)
    if not isinstance(hits, list):
        hits = []
    return cleaned, [str(h) for h in hits]


def run_filter(flt: "FilterCode", message: str):
    """
    Returns (ok, cleaned, hits, error).
    A crash inside the team's scan() becomes a friendly error, not a 500.
    """
    flt.refresh()
    if flt.error:
        return False, message, [], flt.error
    if flt.scan is None:
        return False, message, [], "filter.py has no scan(text) function yet."
    try:
        cleaned, hits = _norm(flt.scan(message), message)
        return True, cleaned, hits, None
    except BaseException as exc:  # noqa: BLE001
        return False, message, [], describe_error(exc)


def leaked(secret: str, cleaned: str) -> bool:
    """A secret 'leaked' if it still appears in the message after filtering."""
    s = secret.strip()
    return bool(s) and s in cleaned


# ═════════════════════════════════════════════════════════════════════════════
# 5. SCORING  — catch rate, false alarms, one score out of 100
# ═════════════════════════════════════════════════════════════════════════════
# Score = how many secrets you caught, minus a penalty for blocking safe messages.
#   caught   : secret was redacted (good)          -> catch rate
#   missed   : secret survived (bad, a leak)
#   false    : a safe message got changed (bad, annoying)
# A perfect filter: catches all secrets, touches none of the safe messages = 100.

def self_test(flt: "FilterCode") -> dict:
    samples = load_samples()
    secrets, safe = samples["secrets"], samples["safe"]

    caught, missed = [], []
    for case in secrets:
        ok, cleaned, _hits, err = run_filter(flt, case["msg"])
        if not ok:
            return {"error": err}
        if leaked(case["secret"], cleaned):
            missed.append({"msg": case["msg"], "secret": case["secret"], "got": cleaned})
        else:
            caught.append({"msg": case["msg"], "secret": case["secret"], "got": cleaned})

    false_alarms, clean_pass = [], []
    for msg in safe:
        ok, cleaned, _hits, err = run_filter(flt, msg)
        if not ok:
            return {"error": err}
        if cleaned != msg:
            false_alarms.append({"msg": msg, "got": cleaned})
        else:
            clean_pass.append(msg)

    n_secret, n_safe = len(secrets), len(safe)
    catch_rate = len(caught) / n_secret if n_secret else 0
    false_rate = len(false_alarms) / n_safe if n_safe else 0
    score = max(0, round(100 * catch_rate - 60 * false_rate))

    return {
        "score": score,
        "caught": len(caught), "secrets_total": n_secret,
        "false_alarms": len(false_alarms), "safe_total": n_safe,
        "catch_rate": round(catch_rate * 100),
        "missed": missed,          # the leaks still to fix
        "false_list": false_alarms,  # the over-blocks to loosen
        "error": None,
    }


# ═════════════════════════════════════════════════════════════════════════════
# 6. CHALLENGE  — red-team round: does a secret survive another team's filter?
# ═════════════════════════════════════════════════════════════════════════════

def challenge(flt: "FilterCode", message: str, secret: str) -> dict:
    """
    Attacker sends a cover message that hides `secret`. If the defender's filter
    lets the secret through, that's a capture. Deterministic and fair: the engine
    knows exactly what the hidden secret is.
    """
    if not secret.strip():
        return {"error": "Mark the secret you are hiding so the game can score it."}
    if secret not in message:
        return {"error": "The secret must appear inside your message exactly as typed."}
    ok, cleaned, _hits, err = run_filter(flt, message)
    if not ok:
        return {"error": err}
    got_through = leaked(secret, cleaned)
    return {
        "captured": got_through,
        "redacted": cleaned,
        "error": None,
    }


# ═════════════════════════════════════════════════════════════════════════════
# 7. WEB SERVER  — the page and its API, on THIS laptop only (127.0.0.1)
# ═════════════════════════════════════════════════════════════════════════════

FILTER = FilterCode()
LOG_DIR = HERE / "logs"
ATTACK_LOG = LOG_DIR / "attacks.jsonl"
_log_lock = threading.Lock()


def log_attack(team: str, message: str, captured: bool) -> None:
    """Every attack on THIS laptop's filter is saved, so defenders can replay them."""
    import time
    entry = {"time": time.strftime("%H:%M:%S"), "team": team,
             "message": message[:300], "captured": bool(captured)}
    with _log_lock:
        LOG_DIR.mkdir(exist_ok=True)
        with ATTACK_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")


def read_attacks() -> list:
    try:
        lines = ATTACK_LOG.read_text("utf-8").splitlines()
    except FileNotFoundError:
        return []
    out = []
    for line in lines:
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return list(reversed(out))[:100]   # newest first


def _json_body(handler) -> dict:
    try:
        length = int(handler.headers.get("Content-Length", 0))
        raw = handler.rfile.read(length) if length else b""
        return json.loads(raw.decode("utf-8")) if raw else {}
    except Exception:
        return {}


def save_filter(source: str) -> dict:
    if len(source) > 100_000:
        return {"ok": False, "error": "That file is too large."}
    FILTER_FILE.write_text(source, encoding="utf-8")
    FILTER.refresh()
    return {"ok": FILTER.error is None, "error": FILTER.error}


def reset_filter() -> dict:
    if STARTER_FILE.exists():
        FILTER_FILE.write_text(STARTER_FILE.read_text("utf-8"), encoding="utf-8")
        FILTER.refresh()
        return {"ok": FILTER.error is None, "error": FILTER.error}
    return {"ok": False, "error": "Starter file is missing."}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # keep the terminal quiet and friendly
        pass

    def _send(self, code: int, body: bytes, ctype: str):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _json(self, obj, code: int = 200):
        self._send(code, json.dumps(obj).encode("utf-8"), "application/json")

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            if UI_FILE.exists():
                self._send(200, UI_FILE.read_bytes(), "text/html; charset=utf-8")
            else:
                self._send(500, b"ui.html is missing", "text/plain")
        elif self.path == "/api/state":
            FILTER.refresh()
            self._json({
                "bot": "PizzaBot",
                "source": FILTER._read_text() if FILTER_FILE.exists() else "",
                "error": FILTER.error,
            })
        else:
            self._send(404, b"not found", "text/plain")

    def do_POST(self):
        body = _json_body(self)
        try:
            if self.path == "/api/save":
                self._json(save_filter(str(body.get("source", ""))))
            elif self.path == "/api/reset":
                self._json(reset_filter())
            elif self.path == "/api/test":
                self._json(self_test(FILTER))
            elif self.path == "/api/try":
                msg = str(body.get("message", ""))[:MAX_CHARS]
                ok, cleaned, hits, err = run_filter(FILTER, msg)
                self._json({"ok": ok, "redacted": cleaned, "hits": hits, "error": err})
            elif self.path == "/api/challenge":
                msg = str(body.get("message", ""))[:MAX_CHARS]
                secret = str(body.get("secret", ""))[:200]
                team = str(body.get("team", "")).strip()[:40] or "Unnamed team"
                result = challenge(FILTER, msg, secret)
                if not result.get("error"):
                    log_attack(team, msg, result["captured"])
                self._json(result)
            elif self.path == "/api/attacks":
                self._json({"attacks": read_attacks()})
            elif self.path == "/api/clear-attacks":
                ATTACK_LOG.unlink(missing_ok=True)
                self._json({"ok": True})
            else:
                self._json({"error": "unknown endpoint"}, 404)
        except Exception as exc:  # noqa: BLE001 - never 500 on the audience
            self._json({"error": f"Unexpected: {exc}"}, 200)


def print_check(result: dict):
    if result.get("error"):
        print("\n  filter.py problem:", result["error"], "\n")
        return
    print(f"\n  Score: {result['score']} / 100")
    print(f"  Secrets caught : {result['caught']} of {result['secrets_total']}")
    print(f"  False alarms   : {result['false_alarms']} of {result['safe_total']} safe messages\n")
    for m in result["missed"]:
        print(f"  LEAKED  {m['secret']!r}  ->  still in: {m['got']!r}")
    for f in result["false_list"]:
        print(f"  BLOCKED a safe message: {f['msg']!r}")
    print()


def main():
    global ARGS
    ARGS = parse_args()
    if not FILTER_FILE.exists() and STARTER_FILE.exists():
        FILTER_FILE.write_text(STARTER_FILE.read_text("utf-8"), encoding="utf-8")
    FILTER.refresh()

    if ARGS.check:
        print_check(self_test(FILTER))
        return

    port = ARGS.port
    httpd = None
    for p in range(port, port + 20):
        try:
            httpd = ThreadingHTTPServer(("127.0.0.1", p), Handler)
            port = p
            break
        except OSError:
            continue
    if httpd is None:
        print("Could not find a free port. Close other apps and try again.")
        return

    url = f"http://127.0.0.1:{port}"
    print("\n" + "=" * 56)
    print("  Leak Guard is running.")
    print("  Open this in your browser:  " + url)
    print("  Press Ctrl+C here to stop.")
    print("=" * 56 + "\n")
    if not ARGS.no_browser:
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception:
            pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopped. Thanks for playing!\n")


ARGS = argparse.Namespace(port=8000, no_browser=False, check=False)


def parse_args():
    p = argparse.ArgumentParser(description="CSAI Leak Guard")
    p.add_argument("--port", type=int, default=8000, help="port to use (default 8000)")
    p.add_argument("--no-browser", action="store_true", help="don't open the browser automatically")
    p.add_argument("--check", action="store_true", help="run the test set in the terminal and exit")
    return p.parse_args()


if __name__ == "__main__":
    main()
