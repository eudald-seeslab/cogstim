"""Keeps generated documentation in step with the code it documents.

The thread running through JOSS review openjournals/joss-reviews#10532 is
documentation that did not match behaviour: "documentation does not match
output, and command line output does not match file output", option tables
that omitted flags which existed, and file counts that were simply wrong.

Regenerating the reference is only half a fix; without this check it drifts
again the first time somebody adds an option and forgets to re-run the script.
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GENERATOR = REPO_ROOT / "scripts" / "generate_options_doc.py"


def test_options_reference_matches_the_cli():
    """docs/options.md must be regenerated whenever an option changes."""
    result = subprocess.run(
        [sys.executable, str(GENERATOR), "--check"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, (
        "The generated options reference is out of date with the CLI.\n"
        "Run: python scripts/generate_options_doc.py\n\n"
        f"{result.stdout}{result.stderr}"
    )


def test_generated_reference_covers_every_task():
    """Every subcommand must appear in the reference."""
    import argparse

    from cogstim.cli import create_parser

    content = (REPO_ROOT / "docs" / "options.md").read_text(encoding="utf-8")

    parser = create_parser()
    subparsers = [
        action for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    ][0]

    missing = [
        name for name in subparsers.choices
        if f"## `cogstim {name}`" not in content
    ]
    assert not missing, f"Tasks missing from docs/options.md: {missing}"
