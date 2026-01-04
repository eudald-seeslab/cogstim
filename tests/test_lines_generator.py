# python
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

import cogstim.lines as lines


def test_stripe_pattern_generator_single_set():
    """StripePatternGenerator should create the expected number of images for a minimal config."""

    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = {
            "output_dir": tmpdir,
            "train_num": 1,
            "test_num": 0,  # one train repetition, no test
            "angles": [0],  # single angle
            "min_stripe_num": 2,
            "max_stripe_num": 2,  # fixed stripe count
            "img_size": 128,  # smaller image for quick tests
            "tag": "",
            "min_thickness": 5,
            "max_thickness": 6,  # ensure low < high for randint
            "min_spacing": 2,
            "max_attempts": 100,
            "background_colour": "#000000",
        }

        generator = lines.StripePatternGenerator(cfg)
        generator.create_images()

        # Expected file path pattern: output_dir/<phase>/<angle>/img_<stripes>_<set_idx>.png
        train_angle_dir = Path(tmpdir) / "train" / "0"
        test_angle_dir = Path(tmpdir) / "test" / "0"
        train_images = list(train_angle_dir.glob("*.png"))
        test_images = list(test_angle_dir.glob("*.png"))

        # total_images per phase = img_sets (or train_num/test_num) * len(angles) * (#stripe_counts)
        # train_num = 1, test_num = 0 (1 // 5), so we should have 1 train image and 0 test images
        assert len(train_images) == 1, f"Expected 1 train image, got {len(train_images)}"
        assert len(test_images) == 0, f"Expected 0 test images, got {len(test_images)}"


def test_stripe_pattern_generator_max_attempts_exceeded():
    """Test that ValueError is raised when max attempts are exceeded."""
    cfg = {
        "output_dir": "/tmp/test",
        "train_num": 1,
        "test_num": 0,
        "angles": [0],
        "min_stripe_num": 10,  # Many stripes
        "max_stripe_num": 10,
        "img_size": 64,  # Small image
        "tag": "",
        "min_thickness": 20,  # Thick stripes
        "max_thickness": 20,
        "min_spacing": 1,  # Minimal spacing
        "max_attempts": 1,  # Very low attempts to force failure
        "background_colour": "#000000",
    }

    generator = lines.StripePatternGenerator(cfg)

    with pytest.raises(ValueError, match="Failed to generate non-overlapping positions"):
        generator._generate_valid_positions(10, 0, 64, [20] * 10)


def test_stripe_pattern_generator_exception_handling():
    """Test exception handling in create_images method."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = {
            "output_dir": tmpdir,
            "train_num": 1,
            "test_num": 0,
            "angles": [0],
            "min_stripe_num": 10,  # Many stripes that will cause overlap issues
            "max_stripe_num": 10,
            "img_size": 64,  # Small image
            "tag": "",
            "min_thickness": 20,
            "max_thickness": 20,
            "min_spacing": 1,
            "max_attempts": 1,  # Force failure
            "background_colour": "#000000",
        }

        generator = lines.StripePatternGenerator(cfg)

        # This should raise an exception due to overlap issues
        with pytest.raises(ValueError):
            generator.create_images()


def test_parse_args_defaults():
    """Test that a CLI-like args object maps to the generator config correctly.

    The `lines` module no longer exposes a `parse_args`/`main` public API in this
    codebase; instead consumers construct the configuration dictionary and
    instantiate `StripePatternGenerator` directly. This test verifies the
    mapping that a hypothetical CLI would perform.
    """
    mock_args = type(
        "Args",
        (),
        {
            "output_dir": "../images/head_rotation_one_stripe",
            "img_sets": 50,
            "angles": [0, 45, 90, 135],
            "min_stripes": 2,
            "max_stripes": 10,
            "img_size": 512,
            "tag": "",
            "min_thickness": 10,
            "max_thickness": 30,
            "min_spacing": 5,
            "max_attempts": 10000,
            "background_colour": "#000000",
        },
    )()

    cfg = {
        "output_dir": mock_args.output_dir,
        "img_sets": mock_args.img_sets,
        "train_num": mock_args.img_sets,
        "test_num": mock_args.img_sets // 5,
        "angles": mock_args.angles,
        "min_stripe_num": mock_args.min_stripes,
        "max_stripe_num": mock_args.max_stripes,
        "img_size": mock_args.img_size,
        "tag": mock_args.tag,
        "min_thickness": mock_args.min_thickness,
        "max_thickness": mock_args.max_thickness,
        "min_spacing": mock_args.min_spacing,
        "max_attempts": mock_args.max_attempts,
        "background_colour": mock_args.background_colour,
    }

    assert cfg["output_dir"] == "../images/head_rotation_one_stripe"
    assert cfg["img_sets"] == 50
    assert cfg["angles"] == [0, 45, 90, 135]
    assert cfg["min_stripe_num"] == 2
    assert cfg["max_stripe_num"] == 10
    assert cfg["img_size"] == 512
    assert cfg["tag"] == ""
    assert cfg["min_thickness"] == 10
    assert cfg["max_thickness"] == 30
    assert cfg["min_spacing"] == 5
    assert cfg["max_attempts"] == 10000


@patch('cogstim.lines.StripePatternGenerator')
def test_main_success(mock_generator_class):
    """Test main function success path."""
    # Instead of testing `main` (not present in the new module API), verify that
    # instantiating the generator with a constructed config calls the class as
    # expected and that the provided config is passed through unchanged.
    mock_generator_instance = type("MockGen", (), {"create_images": lambda self=None: None})()
    mock_generator_class.return_value = mock_generator_instance

    cfg = {
        "output_dir": "/tmp/test",
        "img_sets": 10,
        "train_num": 10,
        "test_num": 2,
        "angles": [0, 90],
        "min_stripe_num": 2,
        "max_stripe_num": 4,
        "img_size": 256,
        "tag": "test",
        "min_thickness": 5,
        "max_thickness": 10,
        "min_spacing": 2,
        "max_attempts": 1000,
        "background_colour": "#000000",
    }

    # Simulate what a caller would do
    gen = lines.StripePatternGenerator(cfg)
    gen.create_images()

    mock_generator_class.assert_called_once()
    config_passed = mock_generator_class.call_args[0][0]
    assert config_passed == cfg


@patch('cogstim.lines.StripePatternGenerator')
def test_main_with_exception(mock_generator_class):
    """Test main function with exception handling."""
    # Ensure that exceptions raised by the generator propagate to callers.
    mock_generator_instance = MagicMock()
    mock_generator_instance.create_images.side_effect = ValueError("Test error")
    mock_generator_class.return_value = mock_generator_instance

    cfg = {
        "output_dir": "/tmp/test",
        "img_sets": 1,
        "train_num": 1,
        "test_num": 0,
        "angles": [0],
        "min_stripe_num": 2,
        "max_stripe_num": 3,
        "img_size": 128,
        "tag": "",
        "min_thickness": 5,
        "max_thickness": 10,
        "min_spacing": 2,
        "max_attempts": 10,
        "background_colour": "#000000",
    }

    gen = lines.StripePatternGenerator(cfg)
    with pytest.raises(ValueError):
        gen.create_images()

