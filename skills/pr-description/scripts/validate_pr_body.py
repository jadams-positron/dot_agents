#!/usr/bin/env python3
"""Validate the structural contract for a rich pull-request description."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

REQUIRED_HEADINGS = ("## How to Review", "## Summary", "## Testing")
EXAMPLE_HEADING = "## Example Usage"
LIVE_EVIDENCE_HEADING = "## Live Evidence"
FORBIDDEN_PATTERNS = (
    (re.compile(r"<!--\s*CURSOR_SUMMARY", re.IGNORECASE), "Cursor summary marker"),
    (re.compile(r"generated (?:with|by|using) (?:Claude|Codex|ChatGPT|OpenAI)", re.IGNORECASE), "AI attribution"),
    (re.compile(r"co-authored-by:.*(?:Claude|Codex|ChatGPT|OpenAI)", re.IGNORECASE), "AI co-author trailer"),
    (re.compile(r"reviewed by Cursor Bugbot", re.IGNORECASE), "AI reviewer attribution"),
    (re.compile(r"\b(?:TODO|TBD):?\b", re.IGNORECASE), "unfinished placeholder"),
)


def _section_body(body: str, heading: str) -> str:
    match = re.search(
        rf"(?ms)^{re.escape(heading)}\s*$\n(.*?)(?=^##\s|\Z)", body
    )
    return match.group(1).strip() if match else ""


def validate(
    body: str,
    issue: int | None = None,
    require_example: bool = False,
    require_live_evidence: bool = False,
) -> list[str]:
    """Return every validation error found in body."""
    errors: list[str] = []
    positions: list[int] = []

    for heading in REQUIRED_HEADINGS:
        matches = list(re.finditer(rf"(?m)^{re.escape(heading)}\s*$", body))
        if len(matches) != 1:
            errors.append(f"expected exactly one {heading} heading")
            continue
        positions.append(matches[0].start())
        if not _section_body(body, heading):
            errors.append(f"{heading} must not be empty")

    if len(positions) == len(REQUIRED_HEADINGS) and positions != sorted(positions):
        errors.append("required sections must be ordered: How to Review, Summary, Testing")

    example_matches = list(re.finditer(rf"(?m)^{re.escape(EXAMPLE_HEADING)}\s*$", body))
    if require_example and len(example_matches) != 1:
        errors.append("expected exactly one ## Example Usage heading")
    if example_matches:
        if len(example_matches) > 1:
            errors.append("expected at most one ## Example Usage heading")
        elif not _section_body(body, EXAMPLE_HEADING):
            errors.append("## Example Usage must not be empty")
        elif positions and example_matches[0].start() < positions[-1]:
            errors.append("## Example Usage must appear after ## Testing")

    live_matches = list(
        re.finditer(rf"(?m)^{re.escape(LIVE_EVIDENCE_HEADING)}\s*$", body)
    )
    if require_live_evidence and len(live_matches) != 1:
        errors.append("expected exactly one ## Live Evidence heading")
    if live_matches:
        if len(live_matches) > 1:
            errors.append("expected at most one ## Live Evidence heading")
        else:
            live_body = _section_body(body, LIVE_EVIDENCE_HEADING)
            if not live_body:
                errors.append("## Live Evidence must not be empty")
            elif positions and live_matches[0].start() < positions[-1]:
                errors.append("## Live Evidence must appear after ## Testing")
            elif require_live_evidence and not (
                re.search(r"!\[[^\]]+\]\([^)]+\)", live_body)
                or re.search(r"(?m)^```", live_body)
            ):
                errors.append(
                    "## Live Evidence must contain an embedded image or fenced transcript"
                )

    if issue is not None:
        trailer = rf"(?m)^Closes #{issue}\s*$"
        if len(re.findall(trailer, body)) != 1:
            errors.append(f"expected exactly one Closes #{issue} trailer")

    for pattern, label in FORBIDDEN_PATTERNS:
        if pattern.search(body):
            errors.append(f"forbidden {label}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("body", type=Path, help="Markdown PR body file")
    parser.add_argument("--issue", type=int, help="required closing issue number")
    parser.add_argument("--require-example", action="store_true")
    parser.add_argument("--require-live-evidence", action="store_true")
    args = parser.parse_args()

    errors = validate(
        args.body.read_text(encoding="utf-8"),
        issue=args.issue,
        require_example=args.require_example,
        require_live_evidence=args.require_live_evidence,
    )
    if errors:
        for error in errors:
            print(f"error: {error}")
        return 1

    print("PR description is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
