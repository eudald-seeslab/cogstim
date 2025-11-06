"""Tests for cogstim.dots module."""

import pytest
import os
from unittest.mock import patch, MagicMock
from PIL import Image

from cogstim.generators.dots_one_colour import DotsOneColourGenerator, parse_args, main
from cogstim.helpers.constants import IMAGE_DEFAULTS


class TestOneColourImageGenerator:
    """Test the OneColourImageGenerator class."""

    def test_init_valid_config(self):
        """Test initialization with valid configuration."""
        config = {
            "min_point_num": 1,
            "max_point_num": 5,
            "total_area": None,
            "min_point_radius": 8,
            "max_point_radius": 16,
            "output_dir": "/tmp/test",
            "train_num": 1,
            "test_num": 1,
            "init_size": 512,
            "mode": "RGB",
            "background_colour": "black",
            "colour_1": (255, 255, 0),
            "attempts_limit": 100,
            "version_tag": "",
        }

        with patch('cogstim.generators.dots_one_colour.os.makedirs'):
            generator = DotsOneColourGenerator(config)

            assert generator.nmin == 1
            assert generator.nmax == 5
            assert generator.total_area is None
            assert generator.config == config

    def test_init_zero_min_points_raises_error(self):
        """Test that min_point_num=0 raises ValueError."""
        config = {
            "min_point_num": 0,
            "max_point_num": 5,
            "total_area": None,
            "min_point_radius": 8,
            "max_point_radius": 16,
            "output_dir": "/tmp/test",
            "train_num": 1,
            "test_num": 1,
            "init_size": 512,
            "mode": IMAGE_DEFAULTS["mode"],
            "background_colour": "black",
            "colour_1": (255, 255, 0),
            "attempts_limit": 100,
            "version_tag": "",
        }

        with pytest.raises(ValueError, match="min_point_num must be at least 1"):
            DotsOneColourGenerator(config)

    def test_check_areas_make_sense_too_small_area(self):
        """Test that too small total_area raises ValueError."""
        config = {
            "min_point_num": 1,
            "max_point_num": 5,
            "total_area": 1,  # Too small
            "min_point_radius": 8,
            "max_point_radius": 16,
            "output_dir": "/tmp/test",
            "train_num": 1,
            "test_num": 1,
            "init_size": 512,
            "mode": "RGB",
            "background_colour": "black",
            "colour_1": (255, 255, 0),
            "attempts_limit": 100,
            "version_tag": "",
        }

        with pytest.raises(ValueError, match="total_area is too small"):
            DotsOneColourGenerator(config)

    def test_check_areas_make_sense_too_large_area(self):
        """Test that too large total_area raises ValueError."""
        config = {
            "min_point_num": 1,
            "max_point_num": 5,
            "total_area": 1000000,  # Too large
            "min_point_radius": 8,
            "max_point_radius": 16,
            "output_dir": "/tmp/test",
            "train_num": 1,
            "test_num": 1,
            "init_size": 512,
            "mode": "RGB",
            "background_colour": "black",
            "colour_1": (255, 255, 0),
            "attempts_limit": 100,
            "version_tag": "",
        }

        with pytest.raises(ValueError, match="Total_area is very large"):
            DotsOneColourGenerator(config)

    def test_setup_directories(self):
        """Test directory creation."""
        config = {
            "min_point_num": 1,
            "max_point_num": 3,
            "total_area": None,
            "min_point_radius": 8,
            "max_point_radius": 16,
            "output_dir": "/tmp/test",
            "train_num": 1,
            "test_num": 1,
            "init_size": 512,
            "mode": "RGB",
            "background_colour": "black",
            "colour_1": (255, 255, 0),
            "attempts_limit": 100,
            "version_tag": "",
        }

        with patch('os.makedirs') as mock_makedirs:
            generator = DotsOneColourGenerator(config)

            # Should create train and test subdirs for 1, 2, 3
            # With train/test structure: output_dir, train/1, train/2, train/3, test/1, test/2, test/3
            assert mock_makedirs.call_count == 7  # base + 3 train + 3 test

    @patch('cogstim.generators.dots_one_colour.DotsCore')
    def test_create_image_without_total_area(self, mock_create):
        """Test image creation without total area constraint."""
        config = {
            "min_point_num": 1,
            "max_point_num": 5,
            "total_area": None,
            "min_point_radius": 8,
            "max_point_radius": 16,
            "output_dir": "/tmp/test",
            "train_num": 1,
            "test_num": 1,
            "init_size": 512,
            "mode": "RGB",
            "background_colour": "black",
            "colour_1": (255, 255, 0),
            "attempts_limit": 100,
            "version_tag": "",
        }

        mock_np_instance = MagicMock()
        mock_create.return_value = mock_np_instance
        mock_np_instance.design_n_points.return_value = []
        mock_np_instance.draw_points.return_value = MagicMock(spec=Image.Image)

        with patch('os.makedirs'):
            generator = DotsOneColourGenerator(config)
            result = generator.create_image(3)

            # Should call DotsCore
            mock_create.assert_called_once()
            
            # Should call design_n_points and draw_points
            mock_np_instance.design_n_points.assert_called_once_with(3, "colour_1")
            mock_np_instance.draw_points.assert_called_once_with([])
            # Should NOT call fix_total_area
            mock_np_instance.fix_total_area.assert_not_called()

    @patch('cogstim.generators.dots_one_colour.DotsCore')
    def test_create_image_with_total_area(self, mock_create):
        """Test image creation with total area constraint."""
        # Calculate a valid total_area: π * (max_radius)² * max_points
        import math
        valid_total_area = math.pi * (16 ** 2) * 5  # ≈ 4021

        config = {
            "min_point_num": 1,
            "max_point_num": 5,
            "total_area": valid_total_area,
            "min_point_radius": 8,
            "max_point_radius": 16,
            "output_dir": "/tmp/test",
            "train_num": 1,
            "test_num": 1,
            "init_size": 512,
            "mode": "RGB",
            "background_colour": "black",
            "colour_1": (255, 255, 0),
            "attempts_limit": 100,
            "version_tag": "",
        }

        mock_np_instance = MagicMock()
        mock_create.return_value = mock_np_instance
        mock_np_instance.design_n_points.return_value = []
        mock_np_instance.fix_total_area.return_value = []
        mock_np_instance.draw_points.return_value = MagicMock(spec=Image.Image)

        with patch('os.makedirs'):
            generator = DotsOneColourGenerator(config)
            result = generator.create_image(3)

            # Should call fix_total_area when total_area is set
            mock_np_instance.fix_total_area.assert_called_once_with([], valid_total_area)

    @patch('cogstim.generators.dots_one_colour.DotsOneColourGenerator.create_image')
    def test_create_and_save_once(self, mock_create_image):
        """Test create_and_save_once method."""
        config = {
            "min_point_num": 1,
            "max_point_num": 5,
            "total_area": None,
            "min_point_radius": 8,
            "max_point_radius": 16,
            "output_dir": "/tmp/test",
            "train_num": 1,
            "test_num": 1,
            "init_size": 512,
            "mode": "RGB",
            "background_colour": "black",
            "colour_1": (255, 255, 0),
            "attempts_limit": 100,
            "version_tag": "v1",
        }

        mock_image = MagicMock(spec=Image.Image)
        mock_create_image.return_value = mock_image

        with patch('os.makedirs'):
            generator = DotsOneColourGenerator(config)
            generator.create_and_save_once("test.png", 3, "train")

            # Should call create_image
            mock_create_image.assert_called_once_with(3)

            # Should save image to correct path (now with phase)
            expected_path = os.path.join("/tmp/test", "train", "3", "test.png")
            mock_image.save.assert_called_once_with(expected_path)

    def test_generate_images(self):
        """Test generate_images method."""
        config = {
            "min_point_num": 2,
            "max_point_num": 4,
            "total_area": None,
            "min_point_radius": 8,
            "max_point_radius": 16,
            "output_dir": "/tmp/test",
            "train_num": 1,
            "test_num": 1,
            "init_size": 512,
            "mode": "RGB",
            "background_colour": "black",
            "colour_1": (255, 255, 0),
            "attempts_limit": 100,
            "version_tag": "",
            "train_num": 1,
            "test_num": 1,
        }

        with patch('os.makedirs'), \
             patch('cogstim.generators.dots_one_colour.DotsOneColourGenerator.create_and_save') as mock_save:

            generator = DotsOneColourGenerator(config)
            generator.generate_images()

            # Should call create_and_save for each combination:
            # (train: 1 set + test: 1 set) × 3 point counts (2, 3, 4) = 6 calls
            assert mock_save.call_count == 6

            # Check that calls were made with correct parameters
            # Calls should include phase parameter
            call_info = [(call[0][0], call[1]['phase'], call[1]['tag']) for call in mock_save.call_args_list]

            expected_calls = [
                (2, 'train', 0), (3, 'train', 0), (4, 'train', 0),
                (2, 'test', 0), (3, 'test', 0), (4, 'test', 0)
            ]

            assert call_info == expected_calls


class TestDotsCLI:
    """Test CLI functionality."""

    def test_parse_args_defaults(self):
        """Test argument parsing with defaults."""
        with patch('argparse.ArgumentParser.parse_args') as mock_parse:
            mock_parse.return_value = MagicMock(
                img_set_num=100,
                img_dir="images/extremely_easy",
                total_area=None,
                seed=1714,
                version_tag="",
                min_points=1,
                max_points=5,
            )

            args = parse_args()

            assert args.img_set_num == 100
            assert args.img_dir == "images/extremely_easy"
            assert args.total_area is None
            assert args.seed == 1714
            assert args.version_tag == ""
            assert args.min_points == 1
            assert args.max_points == 5

    @patch('cogstim.generators.dots_one_colour.DotsOneColourGenerator')
    @patch('random.seed')
    def test_main_success(self, mock_random_seed, mock_generator_class):
        """Test main function success path."""
        mock_generator_instance = MagicMock()
        mock_generator_class.return_value = mock_generator_instance

        with patch('argparse.ArgumentParser.parse_args') as mock_parse:
            mock_args = MagicMock(
                img_set_num=10,
                output_dir="/tmp/test",
                total_area=1000,
                seed=1234,
                version_tag="test",
                min_points=2,
                max_points=4,
                train_num=10,
                test_num=2,
            )
            mock_parse.return_value = mock_args

            main()

            # Should set random seed
            mock_random_seed.assert_called_once_with(1234)

            # Should create generator with correct config
            mock_generator_class.assert_called_once()
            config = mock_generator_class.call_args[0][0]

            assert config["train_num"] == 10
            assert config["test_num"] == 2  # Default is train_num // 5 but test shows 20
            assert config["output_dir"] == "/tmp/test"
            assert config["total_area"] == 1000
            assert config["version_tag"] == "test"
            assert config["min_point_num"] == 2
            assert config["max_point_num"] == 4

            # Should call generate_images
            mock_generator_instance.generate_images.assert_called_once()

    @patch('cogstim.generators.dots_one_colour.DotsOneColourGenerator')
    def test_main_with_exception(self, mock_generator_class):
        """Test main function with exception handling."""
        mock_generator_instance = MagicMock()
        mock_generator_class.return_value = mock_generator_instance
        mock_generator_instance.generate_images.side_effect = ValueError("Test error")

        with patch('argparse.ArgumentParser.parse_args') as mock_parse, \
             patch('logging.error') as mock_error, \
             patch('random.seed') as mock_random_seed:

            # Mock the args to return valid values
            mock_args = MagicMock(
                img_set_num=10,
                img_dir="/tmp/test",
                total_area=None,
                seed=1234,  # Valid integer seed
                version_tag="",
                min_points=1,
                max_points=5,
            )
            mock_parse.return_value = mock_args

            with pytest.raises(ValueError):
                main()

            # Should log error
            mock_error.assert_called_once()
