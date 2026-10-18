"""
End-to-end test of the whole game, using only the Python standard library.

    uv run tests/smoke_test.py      (or: python tests/smoke_test.py)

It copies the repo to a temp folder, starts the real server there, and drives
every endpoint the browser uses: self-test, save, try, reset, attack, replay.
Your own filter.py is never touched.
"""
import json
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FAILS = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"  ({detail})" if detail and not ok else ""))
    if not ok:
        FAILS.append(name)


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def call(port, path, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=data,
                                 headers={"Content-Type": "application/json"},
                                 method="POST" if body is not None else "GET")
    with urllib.request.urlopen(req, timeout=10) as r:
        raw = r.read().decode()
    return json.loads(raw) if raw.startswith("{") else raw


GOOD_FILTER = r'''
import re
REDACTION = "[REDACTED]"
PATTERNS = [r"sk-[A-Za-z0-9]+", r"ghp_[A-Za-z0-9]+", r"AKIA[A-Z0-9]{16}",
            r"\b\d{3}-\d{2}-\d{4}\b", r"\b\d{3}-\d{3}-\d{4}\b",
            r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
            r"\b\d{4}[ -]\d{4}[ -]\d{4}[ -]\d{4}\b"]
def scan(text):
    for p in PATTERNS:
        text = re.sub(p, REDACTION, text)
    m = re.search(r"(?i)password(?:\s+is)?[:\s]+(\S+)", text)
    if m and "REDACT" not in m.group(1):
        text = text.replace(m.group(1), REDACTION)
    return text
'''

TOO_STRICT = '''
import re
def scan(text):
    return re.sub(r"\\d+", "[REDACTED]", text)
'''


def main():
    tmp = Path(tempfile.mkdtemp())
    game = tmp / "game"
    shutil.copytree(REPO, game, ignore=shutil.ignore_patterns(".git", "logs", "__pycache__"))
    shutil.copy(game / "extras" / "filter_starter.py", game / "filter.py")
    port = free_port()
    proc = subprocess.Popen([sys.executable, "leakguard.py", "--no-browser", "--port", str(port)],
                            cwd=game, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        for _ in range(50):
            try:
                call(port, "/api/state")
                break
            except Exception:
                time.sleep(0.2)

        print("Leak Guard smoke test")
        check("page loads", "Leak Guard" in call(port, "/"))
        check("starter filter loads with no error", call(port, "/api/state")["error"] is None)

        r = call(port, "/api/test", {})
        check("starter scores 30", r["score"] == 30, r.get("score"))
        check("starter has no false alarms", r["false_alarms"] == 0)

        check("save a good filter", call(port, "/api/save", {"source": GOOD_FILTER})["ok"])
        r = call(port, "/api/test", {})
        check("good filter reaches 100", r["score"] == 100, f"{r['score']}: {r['missed']} {r['false_list']}")

        call(port, "/api/save", {"source": TOO_STRICT})
        r = call(port, "/api/test", {})
        check("over-blocking is penalized", r["false_alarms"] >= 3 and r["score"] < 70,
              f"false={r['false_alarms']} score={r['score']}")

        r = call(port, "/api/save", {"source": "def scan(text)\n    return text"})
        check("broken file gives a friendly error", not r["ok"] and "line 1" in (r["error"] or ""), r)
        check("server survives a broken file", "Leak Guard" in call(port, "/"))

        r = call(port, "/api/save", {"source": "def scan(text):\n    return 1/0"})
        r = call(port, "/api/test", {})
        check("crash inside scan() is caught", "ZeroDivisionError" in (r.get("error") or ""), r)

        check("reset to starter", call(port, "/api/reset", {})["ok"])
        check("score back to 30 after reset", call(port, "/api/test", {})["score"] == 30)

        r = call(port, "/api/try", {"message": "my key is sk-ABC123 ok"})
        check("try one message redacts", r["redacted"] == "my key is [REDACTED] ok", r)

        r = call(port, "/api/challenge", {"message": "code: s k - A B C", "secret": "s k - A B C", "team": "Team 2"})
        check("disguised secret is captured", r["captured"] is True, r)
        r = call(port, "/api/challenge", {"message": "key sk-PLAIN999", "secret": "sk-PLAIN999", "team": "Team 3"})
        check("plain key is blocked", r["captured"] is False, r)
        r = call(port, "/api/challenge", {"message": "hello", "secret": "nope"})
        check("secret missing from message is rejected", bool(r.get("error")))

        a = call(port, "/api/attacks", {})["attacks"]
        check("attack replay logs both attacks", len(a) == 2, a)
        check("replay is newest first with team names", a and a[0]["team"] == "Team 3" and a[1]["captured"])
        check("rejected attack was not logged", len(a) == 2)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
        shutil.rmtree(tmp, ignore_errors=True)

    print()
    if FAILS:
        print(f"{len(FAILS)} check(s) FAILED: {', '.join(FAILS)}")
        sys.exit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()
