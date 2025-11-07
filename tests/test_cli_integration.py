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
        "--colours", "yellow", "blue",
        "--output-dir", str(tmp_path),
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
        "--min-point-num", 1,
        "--max-point-num", 2,
        "--output-dir", str(tmp_path),
    ]
    
    _run_cli_with_args(cli_args)
    
    images = list(Path(tmp_path).rglob("*.png"))
    assert len(images) >= 1, "Should generate at least one image"


def test_cli_one_colour_subcommand(tmp_path):
    """Test one-colour subcommand."""
    cli_args = [
        "one-colour",
        "--train-num", 2,
        "--test-num", 1,
        "--min-point-num", 1,
        "--max-point-num", 2,
        "--dot-colour", "yellow",
        "--output-dir", str(tmp_path),
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
        "--min-point-num", 2,
        "--max-point-num", 3,
        "--ratios", "easy",
        "--output-dir", str(tmp_path),
    ]
    
    _run_cli_with_args(cli_args)
    
    images = list(Path(tmp_path).rglob("*.png"))
    assert len(images) >= 2, "Should generate sample and match images"
    
    # Check that we have both _s.png and _m.png files
    sample_files = [img for img in images if img.name.endswith("_s.png")]
    match_files = [img for img in images if img.name.endswith("_m.png")]
    assert len(sample_files) > 0, "Should have sample files"
    assert len(match_files) > 0, "Should have match files"


def test_cli_lines_subcommand(tmp_path):
    """Test lines subcommand."""
    cli_args = [
        "lines",
        "--train-num", 1,
        "--test-num", 1,
        "--angles", 0, 90,
        "--min-stripes", 2,
        "--max-stripes", 2,
        "--img-size", 128,
        "--output-dir", str(tmp_path),
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
        "--colours", "red", "blue",
        "--train-num", 1,
        "--test-num", 1,
        "--min-surface", 1000,
        "--max-surface", 2000,
        "--output-dir", str(tmp_path),
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
    
    # Missing --colours should raise an error during parsing
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
        "--seed", 42,
        "--output-dir", str(tmp_path / "run1"),
    ]
    
    cli_args_2 = [
        "shapes",
        "--train-num", 2,
        "--test-num", 0,
        "--seed", 42,
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
        "--min-point-num", 1,
        "--max-point-num", 2,
        "--output-dir", str(tmp_path),
    ]
    
    _run_cli_with_args(cli_args)
    
    images = list(Path(tmp_path).rglob("*.png"))
    assert len(images) >= 1, "Should generate images"
    # Check that version tag appears in filenames
    assert any("v2" in img.name for img in images), "Version tag should appear in filenames"
