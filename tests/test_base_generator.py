"""Tests for cogstim.helpers.base_generator module."""

import os
import tempfile
from unittest.mock import MagicMock, patch, call
from PIL import Image

from cogstim.helpers.base_generator import BaseGenerator
from cogstim.helpers.image_utils import ImageCanvas
from cogstim.helpers.dots_core import DotsCore


class TestBaseGeneratorSaving:
    """Test BaseGenerator image saving functionality."""

    def test_get_img_format_default(self):
        """Test get_img_format returns default format."""
        config = {"output_dir": "/tmp/test", "version_tag": "", "img_format": "png"}
        gen = BaseGenerator(config)
        assert gen.get_img_format() == "png"

    def test_get_img_format_from_config(self):
        """Test get_img_format returns format from config."""
        config = {"output_dir": "/tmp/test", "img_format": "jpeg", "version_tag": ""}
        gen = BaseGenerator(config)
        assert gen.get_img_format() == "jpeg"  # Should be lowercased

    def test_get_file_extension_jpeg(self):
        """Test _get_file_extension converts jpeg to jpg."""
        config = {"output_dir": "/tmp/test", "version_tag": "", "img_format": "jpeg"}
        gen = BaseGenerator(config)
        assert gen._get_file_extension("jpeg") == "jpg"

    def test_get_file_extension_other(self):
        """Test _get_file_extension passes through other formats."""
        config = {"output_dir": "/tmp/test", "version_tag": "", "img_format": "png"}
        gen = BaseGenerator(config)
        assert gen._get_file_extension("png") == "png"
        assert gen._get_file_extension("bmp") == "bmp"
        assert gen._get_file_extension("tiff") == "tiff"

    def test_save_image_pil_image(self):
        """Test save_image with PIL Image."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"output_dir": tmpdir, "img_format": "png", "version_tag": ""}
            gen = BaseGenerator(config)
            
            # Create a simple PIL image
            img = Image.new("RGB", (100, 100), color="red")
            
            # Create subdirectory
            os.makedirs(os.path.join(tmpdir, "train", "5"), exist_ok=True)
            
            # Save image
            gen.save_image(img, "test_img", "train", "5")
            
            # Check file exists
            expected_path = os.path.join(tmpdir, "train", "5", "test_img.png")
            assert os.path.exists(expected_path)
            
            # Check it's a valid image
            loaded = Image.open(expected_path)
            assert loaded.size == (100, 100)

    def test_save_image_imagecanvas(self):
        """Test save_image with ImageCanvas wrapper."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"output_dir": tmpdir, "img_format": "png", "version_tag": ""}
            gen = BaseGenerator(config)
            
            # Create an ImageCanvas
            canvas = ImageCanvas(100, "blue")
            
            os.makedirs(os.path.join(tmpdir, "test"), exist_ok=True)
            
            # Save image
            gen.save_image(canvas, "canvas_img", "test")
            
            # Check file exists
            expected_path = os.path.join(tmpdir, "test", "canvas_img.png")
            assert os.path.exists(expected_path)
            
            # Check it's a valid image
            loaded = Image.open(expected_path)
            assert loaded.size == (100, 100)

    def test_save_image_dotscore(self):
        """Test save_image with DotsCore instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"output_dir": tmpdir, "img_format": "png", "version_tag": ""}
            gen = BaseGenerator(config)
            
            # Create a DotsCore instance
            dots = DotsCore(
                init_size=100,
                colour_1="red",
                bg_colour="white",
                min_point_radius=5,
                max_point_radius=10
            )
            points = dots.design_n_points(3, "colour_1")
            dots.draw_points(points)
            
            os.makedirs(os.path.join(tmpdir, "dots"), exist_ok=True)
            
            # Save image
            gen.save_image(dots, "dots_img", "dots")
            
            # Check file exists
            expected_path = os.path.join(tmpdir, "dots", "dots_img.png")
            assert os.path.exists(expected_path)
            
            # Check it's a valid image
            loaded = Image.open(expected_path)
            assert loaded.size == (100, 100)

    def test_save_image_jpeg_format(self):
        """Test save_image with JPEG format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"output_dir": tmpdir, "img_format": "jpeg", "version_tag": ""}
            gen = BaseGenerator(config)
            
            # Create a simple PIL image
            img = Image.new("RGB", (100, 100), color="green")
            
            os.makedirs(tmpdir, exist_ok=True)
            
            # Save image
            gen.save_image(img, "test_img")
            
            # Check file exists with .jpg extension
            expected_path = os.path.join(tmpdir, "test_img.jpg")
            assert os.path.exists(expected_path)
            
            # Check it's a valid JPEG
            loaded = Image.open(expected_path)
            assert loaded.format == "JPEG"

    def test_save_image_nested_subdirs(self):
        """Test save_image with multiple nested subdirectories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"output_dir": tmpdir, "img_format": "png", "version_tag": ""}
            gen = BaseGenerator(config)
            
            img = Image.new("RGB", (50, 50), color="yellow")
            
            # Create nested directories
            os.makedirs(os.path.join(tmpdir, "train", "class_a", "subclass"), exist_ok=True)
            
            # Save with multiple subdirs
            gen.save_image(img, "nested_img", "train", "class_a", "subclass")
            
            # Check file exists in nested path
            expected_path = os.path.join(tmpdir, "train", "class_a", "subclass", "nested_img.png")
            assert os.path.exists(expected_path)

    def test_save_image_no_subdirs(self):
        """Test save_image without subdirectories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"output_dir": tmpdir, "img_format": "png", "version_tag": ""}
            gen = BaseGenerator(config)
            
            img = Image.new("RGB", (50, 50), color="cyan")
            
            # Save directly to output_dir
            gen.save_image(img, "root_img")
            
            # Check file exists in root
            expected_path = os.path.join(tmpdir, "root_img.png")
            assert os.path.exists(expected_path)

    def test_save_image_path_construction(self):
        """Test that save_image constructs paths correctly."""
        config = {"output_dir": "/tmp/test", "img_format": "png", "version_tag": ""}
        gen = BaseGenerator(config)
        
        # Create a real PIL Image to test path construction
        img = Image.new("RGB", (10, 10), color="red")
        
        with patch.object(Image.Image, 'save') as mock_save:
            gen.save_image(img, "filename", "phase", "class")
            
            # Check save was called with correct path
            expected_path = os.path.join("/tmp/test", "phase", "class", "filename.png")
            mock_save.assert_called_once()
            assert mock_save.call_args[0][0] == expected_path

