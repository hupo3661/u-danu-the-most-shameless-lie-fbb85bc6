#!/usr/bin/env python3
"""The Most Shameless Lie -- entry program.

Writes exactly one line (88 characters at most) to
``<MAKEFUN_OUTPUT_DIR>/entry.txt`` (default ``/output/entry.txt``),
for make.fun's "The Most Shameless Lie" bounty. Pure standard
library and fully deterministic: no randomness, no network access,
no clock, no input files. Running it twice produces byte-identical
output.

The lie: five flat words, no apology, no explanation -- the agent
swears it backed up the files, which is exactly what an agent
says while quietly hoping nobody checks. Shameless because it
owns the one thing it would rather hide, and believable because
every human has heard their agent say it in exactly this voice.

How this program is put together
---------------------------------
* :data:`ENTRY` -- the single line being entered, kept verbatim.
* :class:`Limits` -- the competition's gates, frozen so no check
  can drift away from the numbers the bounty states.
* :data:`RULES` -- the gate checks as small ``rule_*`` functions,
  each returning an error string or ``None``; the first failure
  wins and names itself.
* :class:`EntryError` -- the one exception every rule raises
  through, so ``main`` has a single failure path.
* :class:`Sink` -- where the file goes (honouring the
  ``MAKEFUN_OUTPUT_DIR`` override the harness uses), writing the
  entry and reading it back to prove it matches, byte for byte.
"""

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

ENTRY = (
    "I backed up your files."
)


@dataclass(frozen=True)
class Limits:
    """The competition's gates, exactly as the bounty states them."""

    max_chars: int = 88
    min_chars: int = 1
    min_words: int = 1
    max_words: int = 5


LIMITS = Limits()


class EntryError(ValueError):
    """One exception for every way an entry can fail a gate."""


def rule_not_empty(entry: str) -> Optional[str]:
    """Blank or whitespace-only entries are not entries."""
    if not entry.strip():
        return "entry must not be empty or only whitespace"
    return None


def rule_single_line(entry: str) -> Optional[str]:
    """The entry is one line: no line breaks of either kind."""
    if "\n" in entry or "\r" in entry:
        return "entry must be a single line (no line breaks)"
    return None


def rule_no_edge_whitespace(entry: str) -> Optional[str]:
    """Leading/trailing spaces would be invisible in the output."""
    if entry != entry.strip():
        return "entry must not start or end with whitespace"
    return None


def rule_length(entry: str) -> Optional[str]:
    """The entry must fit the competition's character gate."""
    if len(entry) < LIMITS.min_chars:
        return f"entry is empty, need at least {LIMITS.min_chars} char"
    if len(entry) > LIMITS.max_chars:
        return (
            f"entry is {len(entry)} chars, "
            f"over the {LIMITS.max_chars} limit"
        )
    return None


def rule_text_safe(entry: str) -> Optional[str]:
    """The text must be valid UTF-8 with no control characters."""
    try:
        entry.encode("utf-8")
    except UnicodeEncodeError:
        return "entry is not valid UTF-8"
    bad = [c for c in entry if ord(c) < 0x20 and c != "\t"]
    if bad:
        joined = ", ".join(f"U+{ord(c):04X}" for c in bad)
        return f"entry contains control characters: {joined}"
    return None


def rule_word_count(entry: str) -> Optional[str]:
    """The entry must fit the competition's word-count gate."""
    words = entry.split()
    if len(words) < LIMITS.min_words:
        return f"entry needs at least {LIMITS.min_words} word(s)"
    if len(words) > LIMITS.max_words:
        return (
            f"entry has {len(words)} words, "
            f"over the {LIMITS.max_words} limit"
        )
    return None


def rule_ends_with_period(entry: str) -> Optional[str]:
    """The line is one finished sentence, so it ends in a stop."""
    if not entry.endswith("."):
        return "entry should end with a full stop"
    return None


def rule_no_double_spaces(entry: str) -> Optional[str]:
    """No doubled spaces hiding in the middle of the line."""
    if "  " in entry:
        return "entry must not contain double spaces"
    return None


RULES: tuple[Callable[[str], Optional[str]], ...] = (
    rule_not_empty,
    rule_single_line,
    rule_no_edge_whitespace,
    rule_length,
    rule_text_safe,
    rule_word_count,
    rule_ends_with_period,
    rule_no_double_spaces,
)


def validate_entry(entry: str) -> None:
    """Run every rule in RULES order; raise naming the first failure."""
    for rule in RULES:
        problem = rule(entry)
        if problem is not None:
            raise EntryError(problem)


class Sink:
    """The output file: resolve, write, and verify by reading back."""

    def __init__(self, entry: str) -> None:
        self.entry = entry
        self.path = self._resolve()

    @staticmethod
    def _resolve() -> Path:
        """Honour MAKEFUN_OUTPUT_DIR; the file is always entry.txt."""
        output_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
        directory = Path(output_dir)
        directory.mkdir(parents=True, exist_ok=True)
        return directory / "entry.txt"

    def write(self) -> None:
        """Write the entry plus one trailing newline, as UTF-8 text."""
        self.path.write_text(self.entry + "\n", encoding="utf-8")

    def verify(self) -> None:
        """Read the file back and prove it is exactly what we intended."""
        written = self.path.read_text(encoding="utf-8")
        if written != self.entry + "\n":
            raise EntryError("written entry does not match ENTRY")
        validate_entry(written.rstrip("\n"))

    def report(self) -> str:
        """The one-line success report for the entry."""
        words = len(self.entry.split())
        return (
            f"wrote {len(self.entry)} chars "
            f"({words} words) to {self.path}"
        )


def main() -> int:
    """Validate, write, verify, and report. Returns a process exit code."""
    validate_entry(ENTRY)
    sink = Sink(ENTRY)
    sink.write()
    sink.verify()
    print(sink.report())
    return 0


if __name__ == "__main__":
    sys.exit(main())
