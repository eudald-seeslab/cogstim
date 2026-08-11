import re
import os
import sys
from pathlib import Path
import importlib
import pytest


# ---------------------------------------------------------------------------
# Helper to invoke the CLI programmatically
# ---------------------------------------------------------------------------

def _run_cli_with_args(args_list):
    """Invoke `cogstim.cli.main()` with a fresh `sys.argv`.

    The CLI parses `sys.argv` directly, so we temporarily patch it, execute the
    main function, and then restore the original argv to avoid side-effects.
    """
    import cogstim.cli as cli

    original_argv = sys.argv.copy()
    try:
        sys.argv = ["cogstim", *map(str, args_list)]
        # Reload the module to ensure no stale state between invocations
        importlib.reload(cli)
        cli.main()
    finally:
        sys.argv = original_argv


# ---------------------------------------------------------------------------
# Tests for new subcommand interface
# ---------------------------------------------------------------------------

def test_cli_shapes_subcommand(tmp_path):
    """Test shapes subcommand."""
    cli_args = [
        "shapes",
        "--train-num", 2,
        "--test-num", 1,
        "--min-surface", 10000,
        "--max-surface", 10001,
        "--no-jitter",
        "--output-dir", str(tmp_path),
        "--version-tag", "",
    ]
    
    _run_cli_with_args(cli_args)
    
    images = list(Path(tmp_path).rglob("*.png"))
    assert len(images) >= 1, "Should generate at least one image"


def test_cli_colours_subcommand(tmp_path):
    """Test colours subcommand."""
    cli_args = [
        "colours",
        "--train-num", 2,
        "--test-num", 1,
        "--shape", "circle",
        "--shape-colours", "yellow", "blue",
        "--output-dir", str(tmp_path),
        "--version-tag", "",
    ]
    
    _run_cli_with_args(cli_args)
    
    images = list(Path(tmp_path).rglob("*.png"))
    assert len(images) >= 1, "Should generate at least one image"


def test_cli_ans_subcommand(tmp_path):
    """Test ANS subcommand."""
    cli_args = [
        "ans",
        "--train-num", 2,
        "--test-num", 1,
        "--ratios", "easy",
        "--min-dot-num", 1,
        "--max-dot-num", 2,
        "--output-dir", str(tmp_path),
        "--version-tag", "",
    ]
    
    _run_cli_with_args(cli_args)
    
    images = list(Path(tmp_path).rglob("*.png"))
    assert len(images) >= 1, "Should generate at least one image"


def test_cli_ans_with_tasks_csv(tmp_path):
    """Test ANS subcommand with --tasks-csv and --tasks-copies."""
    csv_path = tmp_path / "tasks.csv"
    csv_path.write_text("n1,n2,equalized\n3,5,TRUE\n2,4,FALSE\n")
    cli_args = [
        "ans",
        "--tasks-csv", str(csv_path),
        "--tasks-copies", 2,
        "--train-num", 1,
        "--test-num", 0,
        "--output-dir", str(tmp_path),
        "--version-tag", "",
    ]
    _run_cli_with_args(cli_args)
    images = list(Path(tmp_path).rglob("*.png"))
    assert len(images) == 4, f"Expected 4 images (2 CSV rows * 2 copies), got {len(images)}"


def test_cli_one_colour_subcommand(tmp_path):
    """Test one-colour subcommand."""
    cli_args = [
        "one-colour",
        "--train-num", 2,
        "--test-num", 1,
        "--min-dot-num", 1,
        "--max-dot-num", 2,
        "--dot-colour-1", "yellow",
        "--output-dir", str(tmp_path),
        "--version-tag", "",
    ]
    
    _run_cli_with_args(cli_args)
    
    images = list(Path(tmp_path).rglob("*.png"))
    assert len(images) >= 1, "Should generate at least one image"


def test_cli_match_to_sample_subcommand(tmp_path):
    """Test match-to-sample subcommand."""
    cli_args = [
        "match-to-sample",
        "--train-num", 1,
        "--test-num", 1,
        "--min-dot-num", 2,
        "--max-dot-num", 3,
        "--ratios", "easy",
        "--output-dir", str(tmp_path),
    ]
    
    _run_cli_with_args(cli_args)
    
    images = list(Path(tmp_path).rglob("*.png"))
    assert len(images) >= 2, "Should generate sample and match images"
    
    # Check that we have both sample (role b) and match (role a) files
    sample_files = [img for img in images if "_b_" in img.name and img.name.endswith(".png")]
    match_files = [img for img in images if "_a_" in img.name and img.name.endswith(".png")]
    assert len(sample_files) > 0, "Should have sample files"
    assert len(match_files) > 0, "Should have match files"


def test_cli_match_to_sample_with_tasks_csv(tmp_path):
    """Test match-to-sample with --tasks-csv and --tasks-copies."""
    csv_path = tmp_path / "tasks.csv"
    csv_path.write_text("sample,match,equalized\n3,4,TRUE\n5,5,FALSE\n")
    cli_args = [
        "match-to-sample",
        "--tasks-csv", str(csv_path),
        "--tasks-copies", 2,
        "--train-num", 1,
        "--test-num", 0,
        "--output-dir", str(tmp_path),
    ]
    _run_cli_with_args(cli_args)
    images = list(Path(tmp_path).rglob("*.png"))
    assert len(images) >= 2, "Should generate sample and match images (2 tasks * 2 copies = 4 pairs)"
    sample_files = [img for img in images if "_b_" in img.name and img.name.endswith(".png")]
    assert len(sample_files) >= 2


def test_cli_lines_subcommand(tmp_path):
    """Test lines subcommand."""
    cli_args = [
        "lines",
        "--train-num", 1,
        "--test-num", 1,
        "--angles", 0, 90,
        "--min-stripe-num", 2,
        "--max-stripe-num", 2,
        "--img-size", 128,
        "--output-dir", str(tmp_path),
        "--version-tag", "",
    ]
    
    _run_cli_with_args(cli_args)
    
    images = list(Path(tmp_path).rglob("*.png"))
    assert len(images) >= 1, "Should generate at least one image"


def test_cli_fixation_subcommand(tmp_path):
    """Test fixation subcommand."""
    cli_args = [
        "fixation",
        "--all-types",
        "--output-dir", str(tmp_path),
        "--img-size", 256,
        "--background-colour", "black",
        "--symbol-colour", "white",
    ]
    
    _run_cli_with_args(cli_args)
    
    images = list(Path(tmp_path).rglob("*.png"))
    assert len(images) == 7, f"Expected 7 fixation images, got {len(images)}"
    
    # Check that all expected types are present
    image_names = [img.name for img in images]
    expected_types = ["A", "B", "C", "AB", "AC", "BC", "ABC"]
    for expected_type in expected_types:
        assert any(expected_type in name for name in image_names), f"Missing fixation type {expected_type}"


def test_cli_fixation_specific_types(tmp_path):
    """Test fixation with specific types selected."""
    cli_args = [
        "fixation",
        "--types", "A", "C", "ABC",
        "--output-dir", str(tmp_path),
    ]
    
    _run_cli_with_args(cli_args)
    
    images = list(Path(tmp_path).rglob("*.png"))
    assert len(images) == 3, f"Expected 3 fixation images, got {len(images)}"


def test_cli_custom_subcommand(tmp_path):
    """Test custom subcommand."""
    cli_args = [
        "custom",
        "--shapes", "circle", "triangle",
        "--shape-colours", "red", "blue",
        "--train-num", 1,
        "--test-num", 1,
        "--min-surface", 1000,
        "--max-surface", 2000,
        "--output-dir", str(tmp_path),
        "--version-tag", "",
    ]
    
    _run_cli_with_args(cli_args)
    
    images = list(Path(tmp_path).rglob("*.png"))
    assert len(images) >= 2, f"Expected at least 2 images, got {len(images)}"


def test_cli_demo_mode(tmp_path):
    """Test --demo flag."""
    cli_args = [
        "shapes",
        "--demo",
        "--output-dir", str(tmp_path),
        "--version-tag", "",
    ]
    
    _run_cli_with_args(cli_args)
    
    images = list(Path(tmp_path).rglob("*.png"))
    # Demo mode should generate 8 training images (4 per class × 2 classes)
    assert len(images) >= 4, f"Demo mode should generate images, got {len(images)}"


def test_cli_custom_missing_required_args():
    """Test custom subcommand with missing required arguments."""
    cli_args = [
        "custom",
        "--shapes", "circle",
        "--train-num", 1,
    ]
    
    # Missing --shape-colours should raise an error during parsing
    with pytest.raises(SystemExit):
        _run_cli_with_args(cli_args)

# ---------------------------------------------------------------------------
# Additional feature tests
# ---------------------------------------------------------------------------

def test_cli_with_seed(tmp_path):
    """Test reproducibility with --seed."""
    cli_args_1 = [
        "shapes",
        "--train-num", 2,
        "--test-num", 0,
        "--seed", 1234,
        "--output-dir", str(tmp_path / "run1"),
    ]
    
    cli_args_2 = [
        "shapes",
        "--train-num", 2,
        "--test-num", 0,
        "--seed", 1234,
        "--output-dir", str(tmp_path / "run2"),
    ]
    
    _run_cli_with_args(cli_args_1)
    _run_cli_with_args(cli_args_2)
    
    images_1 = sorted(Path(tmp_path / "run1").rglob("*.png"))
    images_2 = sorted(Path(tmp_path / "run2").rglob("*.png"))
    
    assert len(images_1) == len(images_2), "Same seed should produce same number of images"
    assert len(images_1) > 0, "Should generate images"


def test_cli_quiet_mode(tmp_path, capsys):
    """Test --quiet flag suppresses output."""
    cli_args = [
        "shapes",
        "--train-num", 1,
        "--test-num", 0,
        "--quiet",
        "--output-dir", str(tmp_path),
        "--version-tag", "",
    ]
    
    _run_cli_with_args(cli_args)
    
    captured = capsys.readouterr()
    # Quiet mode should suppress the success message
    assert "✓" not in captured.out or len(captured.out) == 0


def test_cli_version_tag(tmp_path):
    """Test --version-tag flag."""
    cli_args = [
        "ans",
        "--train-num", 1,
        "--test-num", 0,
        "--version-tag", "v2",
        "--min-dot-num", 1,
        "--max-dot-num", 2,
        "--output-dir", str(tmp_path),
    ]
    
    _run_cli_with_args(cli_args)
    
    images = list(Path(tmp_path).rglob("*.png"))
    assert len(images) >= 1, "Should generate images"
    # Check that version tag appears in filenames
    assert any("v2" in img.name for img in images), "Version tag should appear in filenames"


# ---------------------------------------------------------------------------
# Output encoding
# ---------------------------------------------------------------------------

def test_cli_survives_ascii_only_stdout(tmp_path):
    """A successful run must not fail when stdout cannot encode non-ASCII.

    Regression test: the summary messages contain a check mark. On Windows a
    redirected stream defaults to cp1252, so piping the output raised
    UnicodeEncodeError after every image had already been written. Because
    UnicodeEncodeError subclasses ValueError, the CLI reported it as a
    "Configuration error" and exited 2, turning a successful run into a failure.
    """
    import subprocess

    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "ascii"

    proc = subprocess.run(
        [
            sys.executable, "-m", "cogstim.cli", "one-colour",
            "--train-num", "1",
            "--test-num", "0",
            "--min-dot-num", "1",
            "--max-dot-num", "2",
            "--seed", "1",
            "--output-dir", str(tmp_path),
        ],
        capture_output=True,
        text=True,
        encoding="ascii",
        errors="replace",
        env=env,
    )

    assert proc.returncode == 0, (
        f"CLI exited {proc.returncode} with ASCII-only stdout.\n"
        f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
    )
    assert "Configuration error" not in proc.stderr
    assert list(Path(tmp_path).rglob("*.png")), "Should still generate images"


# ---------------------------------------------------------------------------
# Reported counts must match what is on disk
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "subcommand, extra_args",
    [
        ("shapes", ["--min-surface", 10000, "--max-surface", 12000]),
        ("colours", ["--min-surface", 10000, "--max-surface", 12000]),
        ("ans", ["--min-dot-num", 1, "--max-dot-num", 3]),
        ("one-colour", ["--min-dot-num", 1, "--max-dot-num", 3]),
        ("match-to-sample", ["--min-dot-num", 1, "--max-dot-num", 3]),
        ("lines", ["--angles", 0, 90]),
    ],
)
def test_reported_count_matches_files_written(tmp_path, capsys, subcommand, extra_args):
    """The summary line must state the number of files actually created.

    Regression test for openjournals/joss-reviews#10532. --train-num and
    --test-num count sets, not images, but the summary printed their sum as an
    image count: `shapes --train-num 10 --test-num 5` announced "15 images"
    while writing 3000 files. Both reviewers were misled by this.
    """
    _run_cli_with_args([
        subcommand,
        "--train-num", 2,
        "--test-num", 1,
        "--seed", 4321,
        *extra_args,
        "--output-dir", str(tmp_path),
    ])

    output = capsys.readouterr().out
    on_disk = len([p for p in Path(tmp_path).rglob("*") if p.is_file()])

    match = re.search(r"Generated (\d+) images", output)
    assert match, f"No image count in summary: {output!r}"
    reported = int(match.group(1))

    assert reported == on_disk, (
        f"{subcommand} reported {reported} images but wrote {on_disk} files"
    )
    # The set count must still be visible, and must not be confused with images.
    assert "3 sets" in output, f"Set count missing from summary: {output!r}"


@pytest.mark.parametrize(
    "subcommand, extra_args",
    [
        ("shapes", ["--min-surface", 10000, "--max-surface", 12000]),
        ("ans", ["--min-dot-num", 1, "--max-dot-num", 3]),
        ("one-colour", ["--min-dot-num", 1, "--max-dot-num", 3]),
        ("match-to-sample", ["--min-dot-num", 1, "--max-dot-num", 3]),
        ("lines", ["--angles", 0, 90]),
    ],
)
def test_dry_run_predicts_actual_output(tmp_path, capsys, subcommand, extra_args):
    """--dry-run must predict exactly what a real run writes.

    Both come from the same build_plan(), so a divergence here means the
    prediction and the generation have drifted apart -- the class of problem
    that produced the misleading counts reported in the JOSS review.
    """
    common = ["--train-num", 2, "--test-num", 1, "--seed", 4321, *extra_args]

    dry_dir = tmp_path / "dry"
    _run_cli_with_args([subcommand, *common, "--dry-run", "--output-dir", str(dry_dir)])
    dry_output = capsys.readouterr().out

    assert not [p for p in dry_dir.rglob("*") if p.is_file()], (
        "--dry-run must not write any images"
    )

    predicted = re.search(r"total: (\d+) images", dry_output)
    assert predicted, f"No total in dry-run output: {dry_output!r}"

    real_dir = tmp_path / "real"
    _run_cli_with_args([subcommand, *common, "--output-dir", str(real_dir)])
    capsys.readouterr()

    on_disk = len([p for p in real_dir.rglob("*") if p.is_file()])
    assert int(predicted.group(1)) == on_disk, (
        f"{subcommand}: dry run predicted {predicted.group(1)} images, "
        f"real run wrote {on_disk}"
    )
