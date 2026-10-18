"""
Point every setup link at a GitHub account:

    python tools/set_username.py your-github-username

It rewrites the account name in the README, both install scripts and the
facilitator guide (whatever account they point at now). Then commit and push.
"""
import re
import sys
from pathlib import Path

FILES = ["README.md", "install.sh", "install.ps1", "FACILITATOR.md"]
PATTERNS = [
    r"(raw\.githubusercontent\.com/)[A-Za-z0-9-]+(/csai-leak-guard)",
    r"(github\.com/)[A-Za-z0-9-]+(/csai-leak-guard)",
    r'(GITHUB_USER=")[A-Za-z0-9-]+(")',
    r'(\$GithubUser = ")[A-Za-z0-9-]+(")',
]


def main():
    if len(sys.argv) != 2 or not re.fullmatch(r"[A-Za-z0-9-]{1,39}", sys.argv[1]):
        print("Usage: python tools/set_username.py <github-username>")
        sys.exit(1)
    user = sys.argv[1]
    root = Path(__file__).resolve().parent.parent
    for name in FILES:
        path = root / name
        text = path.read_text(encoding="utf-8")
        total = 0
        for pat in PATTERNS:
            text, n = re.subn(pat, lambda m: m.group(1) + user + m.group(2), text)
            total += n
        path.write_text(text, encoding="utf-8", newline="")
        print(f"  {name}: {total} link(s) set")
    print(f"Done. Setup lines now point at github.com/{user}/csai-leak-guard")


if __name__ == "__main__":
    main()
