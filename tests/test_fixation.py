"""Tests for cogstim.fixation module."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch
from PIL import Image
import numpy as np

from cogstim.generators.fixation import FixationGenerator


class TestFixationGenerator:
    """Test the FixationGenerator class."""

    def test_init(self):
        """Test initialization with valid config."""
        config = {
            "output_dir": "/tmp/test",
            "img_sets": 1,
            "types": ["A", "B", "C"],
            "img_size": 256,
            "dot_radius_px": 5,
            "disk_radius_px": 10,
            "cross_thickness_px": 3,
            "cross_arm_px": 20,
            "jitter_px": 0,
            "background_colour": "white",
            "symbol_colour": "black",
            "tag": "",
        }

        generator = FixationGenerator(config)

        assert generator.output_dir == "/tmp/test"
        assert generator.img_sets == 1
        assert generator.types == ["A", "B", "C"]
        assert generator.size == 256
        assert generator.jitter_px == 0

    def test_center_with_jitter_disabled(self):
        """Test _center_with_jitter when jitter is disabled."""
        config = {
            "output_dir": "/tmp/test",
            "img_sets": 1,
            "types": ["A"],
            "img_size": 256,
            "dot_radius_px": 5,
            "disk_radius_px": 10,
            "cross_thickness_px": 3,
            "cross_arm_px": 20,
            "jitter_px": 0,  # No jitter
            "background_colour": "white",
            "symbol_colour": "black",
            "tag": "",
        }

        generator = FixationGenerator(config)
        center = generator._center_with_jitter()

        # Should return exact center
        assert center == (128, 128)  # 256 // 2

    def test_center_with_jitter_enabled(self):
        """Test _center_with_jitter when jitter is enabled."""
        config = {
            "output_dir": "/tmp/test",
            "img_sets": 1,
            "types": ["A"],
            "img_size": 256,
            "dot_radius_px": 5,
            "disk_radius_px": 10,
            "cross_thickness_px": 3,
            "cross_arm_px": 20,
            "jitter_px": 5,  # Enable jitter
            "background_colour": "white",
            "symbol_colour": "black",
            "tag": "",
        }

        generator = FixationGenerator(config)
        center = generator._center_with_jitter()

        # Should be close to center but with some jitter
        cx, cy = center
        assert 128 - 5 <= cx <= 128 + 5  # Within jitter range
        assert 128 - 5 <= cy <= 128 + 5  # Within jitter range

    def test_blank_image(self):
        """Test _blank_image creates correct blank image."""
        config = {
            "output_dir": "/tmp/test",
            "img_sets": 1,
            "types": ["A"],
            "img_size": 128,
            "dot_radius_px": 5,
            "disk_radius_px": 10,
            "cross_thickness_px": 3,
            "cross_arm_px": 20,
            "jitter_px": 0,
            "background_colour": (255, 0, 0),  # Red background
            "symbol_colour": "black",
            "tag": "",
        }

        generator = FixationGenerator(config)
        canvas = generator._blank_canvas()
        
        from cogstim.helpers.image_utils import ImageCanvas
        assert isinstance(canvas, ImageCanvas)
        
        img = canvas.img
        assert img.size == (128, 128)
        assert img.mode == "RGB"

        # Check background color
        arr = np.array(img)
        assert np.all(arr[0, 0] == [255, 0, 0])  # Red pixel

    def test_draw_symbol_unknown_type(self):
        """Test _draw_symbol with unknown fixation type raises error."""
        config = {
            "output_dir": "/tmp/test",
            "img_sets": 1,
            "types": ["A"],
            "img_size": 128,
            "dot_radius_px": 5,
            "disk_radius_px": 10,
            "cross_thickness_px": 3,
            "cross_arm_px": 20,
            "jitter_px": 0,
            "background_colour": "white",
            "symbol_colour": "black",
            "tag": "",
        }

        generator = FixationGenerator(config)

        with pytest.raises(ValueError, match="Unknown fixation type: INVALID"):
            generator._draw_symbol("invalid")

    @patch('cogstim.generators.fixation.os.makedirs')
    def test_create_directories(self, mock_makedirs):
        """Test setup_directories creates output directory."""
        config = {
            "output_dir": "/tmp/test/fixation",
            "img_sets": 1,
            "types": ["A"],
            "img_size": 128,
            "dot_radius_px": 5,
            "disk_radius_px": 10,
            "cross_thickness_px": 3,
            "cross_arm_px": 20,
            "jitter_px": 0,
            "background_colour": "white",
            "symbol_colour": "black",
            "tag": "",
        }

        generator = FixationGenerator(config)
        generator.setup_directories()

        mock_makedirs.assert_called_once_with("/tmp/test/fixation", exist_ok=True)

    def test_generate_images(self):
        """Test generate_images generates the expected files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config = {
                "output_dir": tmp_dir,
                "img_sets": 1,
                "types": ["A", "B"],  # Just two types for faster test
                "img_size": 64,  # Small size for faster test
                "dot_radius_px": 2,
                "disk_radius_px": 5,
                "cross_thickness_px": 1,
                "cross_arm_px": 8,
                "jitter_px": 0,
                "background_colour": "white",
                "symbol_colour": "black",
                "tag": "test",
            }

            generator = FixationGenerator(config)
            generator.generate_images()

            # Should create 2 images (1 set × 2 types)
            images = list(Path(tmp_dir).glob("*.png"))
            assert len(images) == 2

            # Check filenames contain the types and tag
            image_names = [img.name for img in images]
            assert any("A" in name and "test" in name for name in image_names)
            assert any("B" in name and "test" in name for name in image_names)

            # Verify images are valid
            for img_path in images:
                with Image.open(img_path) as img:
                    assert img.size == (64, 64)
                    assert img.mode == "RGB"
