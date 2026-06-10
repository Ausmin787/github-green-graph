#!/usr/bin/env python3
"""
Draw pixel art text on your GitHub contribution graph using backdated commits.

The script creates real git commits backdated to past dates so that GitHub's
contribution graph lights up in the shape of your chosen text or pattern.
Run it once per year to refresh the art (old commits fall off after 52 weeks).

Usage:
    python scripts/draw_art.py "HELLO"
    python scripts/draw_art.py "OPEN TO WORK" --intensity 4 --push
    python scripts/draw_art.py "CODE" --dry-run

Requirements:
    - Run from inside the target git repository (or pass --repo-path)
    - The repo must already have a remote named 'origin' (if using --push)
    - Your git user.email must match a verified email on your GitHub account
"""

import argparse
import os
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

# Allow running from any directory by adding scripts/ to path
sys.path.insert(0, str(Path(__file__).parent))
from font_data import CHAR_GAP, CHAR_HEIGHT, CHAR_WIDTH, FONT

# In the 7-row graph (Sun=row0 .. Sat=row6), text lives in rows 1-5 (Mon-Fri)
_TEXT_ROW_OFFSET = 1   # text starts at Monday (row 1)
_GRAPH_MAX_WEEKS = 52


def _text_to_columns(text: str) -> list[list[int]]:
    """
    Convert a string to a list of pixel columns for the contribution graph.

    Returns a list of columns where each column is a list of CHAR_HEIGHT ints
    (1 = lit pixel, 0 = empty). Characters are separated by CHAR_GAP empty columns.
    Unknown characters are treated as spaces.
    """
    columns: list[list[int]] = []
    text = text.upper()

    for i, char in enumerate(text):
        bitmap = FONT.get(char, FONT[" "])
        for col in range(CHAR_WIDTH):
            columns.append([int(bitmap[row][col]) for row in range(CHAR_HEIGHT)])
        if i < len(text) - 1:
            for _ in range(CHAR_GAP):
                columns.append([0] * CHAR_HEIGHT)

    return columns


def _graph_start_sunday() -> date:
    """
    Return the Sunday that anchors the left edge of the 52-week contribution graph.

    GitHub's graph starts at the Sunday of the week that was 52 weeks ago.
    weekday() convention: Mon=0 … Sun=6, so days_back = (weekday+1) % 7 reaches
    the preceding Sunday (or stays if already Sunday).
    """
    approx_start = date.today() - timedelta(weeks=_GRAPH_MAX_WEEKS)
    days_back = (approx_start.weekday() + 1) % 7
    return approx_start - timedelta(days=days_back)


def _print_preview(columns: list[list[int]]) -> None:
    print("\nContribution graph preview  (# = commit, . = empty):")
    print("  +" + "-" * len(columns) + "+")
    day_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    for offset in range(CHAR_HEIGHT):
        label = day_names[offset + _TEXT_ROW_OFFSET]
        row = "".join("#" if col[offset] else "." for col in columns)
        print(f"  {label}|{row}|")
    print("  +" + "-" * len(columns) + "+")
    print(f"\n  Text width : {len(columns)} weeks")
    print(f"  Graph width: {_GRAPH_MAX_WEEKS} weeks available\n")


def _make_backdated_commits(
    target_date: date,
    count: int,
    repo_path: Path,
    log_file: Path,
    dry_run: bool,
) -> None:
    """Append `count` git commits backdated to target_date."""
    # Explicit UTC offset so git doesn't interpret the timestamp in the local timezone,
    # which would shift commits to the wrong calendar day on GitHub's UTC-based graph.
    date_str = target_date.strftime("%Y-%m-%dT12:00:00+00:00")
    env = {**os.environ, "GIT_AUTHOR_DATE": date_str, "GIT_COMMITTER_DATE": date_str}

    if dry_run:
        print(f"  [dry-run] {count}x commit on {target_date}")
        return

    for i in range(count):
        with open(log_file, "a") as fh:
            fh.write(f"{date_str} {i}\n")
        try:
            subprocess.run(
                ["git", "add", str(log_file)],
                cwd=repo_path, env=env, check=True, capture_output=True,
            )
            subprocess.run(
                ["git", "commit", "-m", f"activity: {target_date} ({i + 1}/{count})"],
                cwd=repo_path, env=env, check=True, capture_output=True,
            )
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or b"").decode(errors="replace")
            print(f"\nERROR: git command failed on {target_date} commit {i + 1}:\n{stderr}")
            raise


def draw(
    text: str,
    intensity: int,
    col_offset: int,
    dry_run: bool,
    yes: bool,
    push: bool,
    repo_path: Path,
) -> None:
    columns = _text_to_columns(text)
    total_weeks_needed = len(columns) + col_offset

    if total_weeks_needed > _GRAPH_MAX_WEEKS:
        print(
            f"ERROR: '{text}' needs {len(columns)} weeks + {col_offset} offset "
            f"= {total_weeks_needed} weeks, but the graph shows only "
            f"{_GRAPH_MAX_WEEKS}.\nShorten the text or reduce --col-offset."
        )
        sys.exit(1)

    _print_preview(columns)

    start_sunday = _graph_start_sunday()
    today = date.today()
    # Separate file from the daily-commit workflow's log.txt to avoid content collisions.
    log_file = repo_path / "activity" / "art-log.txt"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    lit_pixels = sum(1 for col in columns for px in col if px)
    print(f"Pixels to draw : {lit_pixels}")
    print(f"Commits to make: {lit_pixels * intensity}")
    print(f"Graph starts   : {start_sunday} (Sunday)\n")

    if not dry_run and not yes:
        if not sys.stdin.isatty():
            print("ERROR: stdin is not a terminal. Pass --yes to skip the confirmation prompt.")
            sys.exit(1)
        answer = input("Proceed? This will add many backdated commits. [y/N] ").strip().lower()
        if answer != "y":
            print("Aborted.")
            sys.exit(0)

    made = 0
    for col_idx, column in enumerate(columns):
        week = col_idx + col_offset
        for row_idx, pixel in enumerate(column):
            if not pixel:
                continue
            graph_row = row_idx + _TEXT_ROW_OFFSET
            target_date = start_sunday + timedelta(weeks=week, days=graph_row)
            if target_date > today:
                # Future dates don't appear on the graph yet; skip silently
                continue
            _make_backdated_commits(target_date, intensity, repo_path, log_file, dry_run)
            made += intensity

    print(f"\nDone — {made} commit(s) created.")

    if push and not dry_run:
        print("Pushing to remote …")
        subprocess.run(["git", "push"], cwd=repo_path, check=True)
        print("Pushed! Your graph will update within a few minutes.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("text", help="Text to draw (A-Z, 0-9, spaces, !?.-+)")
    parser.add_argument(
        "--intensity",
        type=int,
        default=3,
        choices=[1, 2, 3, 4],
        help="Commits per lit pixel — controls green shade (default: 3)",
    )
    parser.add_argument(
        "--col-offset",
        type=int,
        default=2,
        help="Blank weeks before the text starts (default: 2)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would happen without touching git history",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip the confirmation prompt (useful for scripted / CI runs)",
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help="Push to origin automatically after drawing",
    )
    parser.add_argument(
        "--repo-path",
        type=Path,
        default=Path("."),
        help="Path to the git repo (default: current directory)",
    )
    args = parser.parse_args()
    draw(
        text=args.text,
        intensity=args.intensity,
        col_offset=args.col_offset,
        dry_run=args.dry_run,
        yes=args.yes,
        push=args.push,
        repo_path=args.repo_path.resolve(),
    )


if __name__ == "__main__":
    main()
