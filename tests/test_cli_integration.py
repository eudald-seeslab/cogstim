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
        sys.argv = ["cogstim.cli", *map(str, args_list)]
        # Reload the module to ensure no stale state between invocations
        importlib.reload(cli)
        cli.main()
    finally:
        sys.argv = original_argv


# ---------------------------------------------------------------------------
# Parametrised happy-path scenarios
# ---------------------------------------------------------------------------

SCENARIOS = [
    (
        [
            "--shape_recognition",
            "--train_num",
            1,
            "--test_num",
            1,
            "--min_surface",
            10000,
            "--max_surface",
            10001,
            "--no-jitter",
        ],
        1,  # Expect at least one PNG produced
    ),
    (
        [
            "--one_colour",
            "--train_num",
            1,
            "--test_num",
            1,
            "--min_point_num",
            1,
            "--max_point_num",
            1,
        ],
        1,
    ),
    (
        [
            "--lines",
            "--train_num",
            1,
            "--test_num",
            1,
            "--angles",
            0,
            "--min_stripes",
            2,
            "--max_stripes",
            2,
            "--img_size",
            128,
            "--min_thickness",
            5,
            "--max_thickness",
            6,
            "--min_spacing",
            2,
        ],
        1,
    ),
    (
        [
            "--match_to_sample",
            "--train_num",
            1,
            "--test_num",
            1,
            "--min_point_num",
            2,
            "--max_point_num",
            3,
            "--ratios",
            "easy",
        ],
        2,  # Expect at least 2 PNGs (sample and match)
    ),
]


@pytest.mark.parametrize("cli_args, min_images", SCENARIOS)
def test_cli_happy_path(cli_args, min_images, tmp_path):
    """End-to-end smoke test exercising the public CLI.

    For each representative dataset type we invoke the CLI with minimal
    parameters, write output into a temporary directory, and assert that at
    least one image is produced. This guards against breaking changes in the
    user-facing entry point while keeping the workload lightweight.
    """
    # Ensure outputs land in the temporary directory isolated per test
    cli_args = [*cli_args, "--output_dir", str(tmp_path)]

    _run_cli_with_args(cli_args)

    images = list(Path(tmp_path).rglob("*.png"))
    assert len(images) >= min_images, "CLI should generate at least one PNG image."


def test_cli_match_to_sample_specific_features(tmp_path):
    """Test match_to_sample specific CLI features."""
    # Test with easy ratios
    cli_args = [
        "--match_to_sample",
        "--train_num", 1,
        "--test_num", 1,
        "--min_point_num", 2,
        "--max_point_num", 4,
        "--ratios", "easy",
        "--output_dir", str(tmp_path),
    ]
    
    _run_cli_with_args(cli_args)
    
    images = list(Path(tmp_path).rglob("*.png"))
    assert len(images) >= 2, "Should generate sample and match images"
    
    # Check that we have both _s.png and _m.png files
    sample_files = [img for img in images if img.name.endswith("_s.png")]
    match_files = [img for img in images if img.name.endswith("_m.png")]
    assert len(sample_files) > 0, "Should have sample files"
    assert len(match_files) > 0, "Should have match files"


def test_cli_match_to_sample_with_equalization(tmp_path):
    """Test match_to_sample with equalization enabled."""
    cli_args = [
        "--match_to_sample",
        "--train_num", 1,
        "--test_num", 1,
        "--min_point_num", 2,
        "--max_point_num", 3,
        "--ratios", "all",
        "--output_dir", str(tmp_path),
    ]
    
    _run_cli_with_args(cli_args)
    
    images = list(Path(tmp_path).rglob("*.png"))
    assert len(images) >= 2, "Should generate images"
    
    # Check for equalized files
    equalized_files = [img for img in images if "equalized" in img.name]
    assert len(equalized_files) > 0, "Should have equalized files"
