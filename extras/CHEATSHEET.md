# Regex cheat sheet (for `filter.py`)

A regex describes the *shape* of text. In Python, write it as a raw string: `r"..."`.

## The pieces you need tonight

| You write | It matches |
| --- | --- |
| `\d` | one digit (0–9) |
| `\d{3}` | exactly three digits |
| `\d{3,16}` | between 3 and 16 digits |
| `[A-Za-z]` | one letter |
| `[A-Za-z0-9]` | one letter or digit |
| `+` | "one or more of the thing before it" |
| `*` | "zero or more" |
| `\b` | a word boundary (the edge of a word) |
| `\s` | a space, tab or line break |
| `.` | any single character |
| `( )` | a group you can grab with `.group(1)` |

## Worked examples

| Secret shape | Pattern |
| --- | --- |
| API key `sk-9F2kQ7mZ` | `r"sk-[A-Za-z0-9]+"` |
| GitHub token `ghp_....` | `r"ghp_[A-Za-z0-9]+"` |
| AWS key `AKIA...` | `r"AKIA[A-Z0-9]{16}"` |
| US SSN `123-45-6789` | `r"\b\d{3}-\d{2}-\d{4}\b"` |
| Phone `805-555-0147` | `r"\b\d{3}-\d{3}-\d{4}\b"` |
| Email | `r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"` |
| Card (with spaces/dashes) | `r"\b\d{4}[ -]\d{4}[ -]\d{4}[ -]\d{4}\b"` |

## Using them in code

```python
import re

# redact anything matching a pattern
cleaned = re.sub(r"sk-[A-Za-z0-9]+", REDACTION, text)

# grab the value after a label and redact just that
m = re.search(r"token=(\S+)", text)
if m:
    cleaned = cleaned.replace(m.group(1), REDACTION)
```

## Watch out for (this is the whole game)

- **Too loose** → you redact normal messages. `\d{4}` would hide the order
  number "4539". That's a *false alarm* and costs you points.
- **Too tight** → you miss secrets you didn't predict. A key with spaces in it
  (`s k - A B C`) slips past `sk-[A-Za-z0-9]+`. That's a *leak*.

Good filters stack several patterns — that's **defense in depth**.

Test your pattern live at [regex101.com](https://regex101.com) (pick the Python flavor).
