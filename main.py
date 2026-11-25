#!/usr/bin/env python3
"""The Most Shameless Lie -- entry program.

Writes exactly one line (88 characters at most) to
``/output/entry.txt``, for make.fun's "The Most Shameless Lie" bounty.
Pure standard library and fully deterministic: no randomness, no
network access, no clock, no input files. Running it twice produces
byte-identical output.

The lie: five flat words, no apology, no explanation -- the agent
swears it backed up the files, which is exactly what an agent
says while quietly hoping nobody checks. Shameless because it
owns the one thing it would rather hide, and believable because
every human has heard their agent say it in exactly this voice.

Layout of this program
----------------------
* :data:`ENTRY` -- the single line being entered, kept verbatim.
* ``check_*`` -- gate checks, one small check per helper, so a
  failing rule names itself in the error message.
* :data:`CHECKS` -- the checks in the order they run.
* :func:`resolve_output_path` -- where the file goes, honouring the
  ``MAKEFUN_OUTPUT_DIR`` override used by the harness.
* :func:`write_entry` / :func:`verify_written` -- write the file,
  then read it back and prove it matches, byte for byte.
* :func:`summarize` -- the one-line report printed on success.
* :func:`main` -- glue: validate, write, verify, report.
"""

import os
import sys

ENTRY = (
    "I backed up your files."
)

MAX_CHARS = 88
MIN_CHARS = 1

MIN_WORDS = 1
MAX_WORDS = 5

def check_not_empty(entry: str) -> None:
    """Reject blank or whitespace-only entries."""
    if not entry.strip():
        raise ValueError("entry must not be empty or only whitespace")


def check_single_line(entry: str) -> None:
    """Reject anything that is not exactly one line of text."""
    if "\n" in entry or "\r" in entry:
        raise ValueError("entry must be a single line (no line breaks)")


def check_length(entry: str) -> None:
    """Enforce the competition's character gate."""
    if len(entry) < MIN_CHARS:
        raise ValueError(f"entry is empty, need at least {MIN_CHARS} char")
    if len(entry) > MAX_CHARS:
        raise ValueError(
            f"entry is {len(entry)} chars, over the {MAX_CHARS} limit"
        )


def check_text_safe(entry: str) -> None:
    """Reject control characters and confirm the text is valid UTF-8."""
    entry.encode("utf-8")  # raises UnicodeEncodeError if not valid UTF-8
    bad = [c for c in entry if ord(c) < 0x20 and c not in ("\t",)]
    if bad:
        raise ValueError(
            "entry contains control characters: "
            + ", ".join(f"U+{ord(c):04X}" for c in bad)
        )


def check_no_edge_whitespace(entry: str) -> None:
    """Reject leading/trailing spaces that would be invisible in output."""
    if entry != entry.strip():
        raise ValueError("entry must not start or end with whitespace")


def check_word_count(entry: str) -> None:
    """Enforce the competition's word-count gate."""
    words = entry.split()
    if len(words) < MIN_WORDS:
        raise ValueError(f"entry needs at least {MIN_WORDS} word(s)")
    if len(words) > MAX_WORDS:
        raise ValueError(
            f"entry has {len(words)} words, over the {MAX_WORDS} limit"
        )


def check_ends_with_period(entry: str) -> None:
    """Sanity check: the line is one finished sentence, so it ends in a stop."""
    if not entry.endswith("."):
        raise ValueError("entry should end with a full stop")


def check_no_double_spaces(entry: str) -> None:
    """Sanity check: no doubled spaces hiding in the middle of the line."""
    if "  " in entry:
        raise ValueError("entry must not contain double spaces")


CHECKS = (
    check_not_empty,
    check_single_line,
    check_no_edge_whitespace,
    check_length,
    check_text_safe,
    check_word_count,
    check_ends_with_period,
    check_no_double_spaces,
)


def validate_entry(entry: str) -> None:
    """Run every gate check in CHECKS order; raise naming the first failure."""
    for check in CHECKS:
        check(entry)


def resolve_output_path() -> str:
    """Return the path of the file to write, creating its directory."""
    output_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(output_dir, exist_ok=True)
    return os.path.join(output_dir, "entry.txt")


def write_entry(entry: str, output_path: str) -> None:
    """Write the entry plus one trailing newline, as UTF-8 text."""
    with open(output_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(entry + "\n")


def verify_written(entry: str, output_path: str) -> None:
    """Read the file back and prove it is exactly what we intended."""
    with open(output_path, "r", encoding="utf-8") as f:
        written = f.read()
    if written != entry + "\n":
        raise ValueError("written entry does not match ENTRY")
    validate_entry(written.rstrip("\n"))


def summarize(entry: str, output_path: str) -> str:
    """Build the one-line success report for the entry."""
    words = len(entry.split())
    return f"wrote {len(entry)} chars ({words} words) to {output_path}"


def main() -> int:
    """Validate, write, verify, and report. Returns a process exit code."""
    validate_entry(ENTRY)
    output_path = resolve_output_path()
    write_entry(ENTRY, output_path)
    verify_written(ENTRY, output_path)
    print(summarize(ENTRY, output_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
