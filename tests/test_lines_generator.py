import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

from cogstim.generators.lines import LinesGenerator, parse_args, main


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

        generator = LinesGenerator(cfg)
        generator.generate_images()

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

    generator = LinesGenerator(cfg)

    with pytest.raises(ValueError, match="Failed to generate non-overlapping positions"):
        generator._generate_valid_positions(10, 0, 64, [20] * 10)


def test_stripe_pattern_generator_exception_handling():
    """Test exception handling in generate_images method."""
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

        generator = LinesGenerator(cfg)

        # This should raise an exception due to overlap issues
        with pytest.raises(ValueError):
            generator.generate_images()


def test_parse_args_defaults():
    """Test argument parsing with defaults."""
    with patch('argparse.ArgumentParser.parse_args') as mock_parse:
        mock_parse.return_value = type('Args', (), {
            'output_dir': '../images/head_rotation_one_stripe',
            'img_sets': 50,
            'angles': [0, 45, 90, 135],
            'min_stripes': 2,
            'max_stripes': 10,
            'img_size': 512,
            'tag': '',
            'min_thickness': 10,
            'max_thickness': 30,
            'min_spacing': 5,
            'max_attempts': 10000,
        })()

        args = parse_args()

        assert args.output_dir == '../images/head_rotation_one_stripe'
        assert args.img_sets == 50
        assert args.angles == [0, 45, 90, 135]
        assert args.min_stripes == 2
        assert args.max_stripes == 10
        assert args.img_size == 512
        assert args.tag == ''
        assert args.min_thickness == 10
        assert args.max_thickness == 30
        assert args.min_spacing == 5
        assert args.max_attempts == 10000


@patch('cogstim.generators.lines.LinesGenerator')
def test_main_success(mock_generator_class):
    """Test main function success path."""
    mock_generator_instance = type('MockGen', (), {'generate_images': lambda: None})()

    with patch('cogstim.generators.lines.parse_args') as mock_parse:
        mock_args = type('Args', (), {
            'output_dir': '/tmp/test',
            'img_sets': 10,
            'angles': [0, 90],
            'min_stripes': 2,
            'max_stripes': 4,
            'img_size': 256,
            'tag': 'test',
            'min_thickness': 5,
            'max_thickness': 10,
            'min_spacing': 2,
            'max_attempts': 1000,
        })()

        mock_parse.return_value = mock_args

        main()

        # Should create generator with correct config
        mock_generator_class.assert_called_once()
        config = mock_generator_class.call_args[0][0]

        assert config["output_dir"] == "/tmp/test"
        assert config["img_sets"] == 10
        assert config["angles"] == [0, 90]
        assert config["min_stripe_num"] == 2
        assert config["max_stripe_num"] == 4
        assert config["img_size"] == 256
        assert config["tag"] == "test"


@patch('cogstim.generators.lines.LinesGenerator')
def test_main_with_exception(mock_generator_class):
    """Test main function with exception handling."""
    mock_generator_instance = MagicMock()
    mock_generator_instance.generate_images.side_effect = ValueError("Test error")
    mock_generator_class.return_value = mock_generator_instance

    with patch('cogstim.generators.lines.parse_args'), \
         patch('logging.error') as mock_error:

        with pytest.raises(ValueError):
            main()

        # Should log error
        mock_error.assert_called_once()
