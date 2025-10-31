"""End-to-end integration tests that generate actual images.

These tests verify that the complete pipeline works correctly by generating
real images and checking their properties. Images are saved to test_images/
directory for manual inspection.
"""

import pytest
import os
from pathlib import Path
from PIL import Image
import numpy as np

from cogstim.ans_dots import PointsGenerator, GENERAL_CONFIG as ANS_GENERAL_CONFIG
from cogstim.match_to_sample import MatchToSampleGenerator, GENERAL_CONFIG as MTS_GENERAL_CONFIG
from cogstim.shapes import ShapesGenerator
from cogstim.lines import StripePatternGenerator
from cogstim.fixation import FixationGenerator


def get_test_images_dir():
    """Get the test_images directory path, creating it if it doesn't exist."""
    test_images_dir = Path("test_images")
    test_images_dir.mkdir(exist_ok=True)
    return test_images_dir


class TestANSImageGeneration:
    """Test ANS dot array image generation end-to-end."""

    def test_ans_easy_ratios_generation(self, tmp_path):
        """Test ANS generation with easy ratios."""
        test_images_dir = get_test_images_dir()
        config = {
            **ANS_GENERAL_CONFIG,
            "train_num": 2,
            "test_num": 2,
            "output_dir": str(test_images_dir / "ans_easy"),
            "ratios": "easy",
            "ONE_COLOUR": False,
            "min_point_num": 2,
            "max_point_num": 6,
            "background_colour": "white",
            "dot_colour": "black",
            "min_point_radius": 8,
            "max_point_radius": 12,
        }
        
        generator = PointsGenerator(config)
        generator.generate_images()
        
        # Check that images were created
        output_dir = Path(config["output_dir"])
        assert output_dir.exists()
        
        # Check for both colour directories
        yellow_dir = output_dir / "yellow"
        blue_dir = output_dir / "blue"
        assert yellow_dir.exists()
        assert blue_dir.exists()
        
        # Count generated images
        yellow_images = list(yellow_dir.glob("*.png"))
        blue_images = list(blue_dir.glob("*.png"))
        
        assert len(yellow_images) > 0, "No yellow images generated"
        assert len(blue_images) > 0, "No blue images generated"
        
        # Verify image properties
        for img_path in yellow_images[:2]:  # Check first 2 images
            with Image.open(img_path) as img:
                assert img.size == (512, 512), f"Wrong image size: {img.size}"
                assert img.mode == "RGB", f"Wrong image mode: {img.mode}"
                
                # Check that image has non-white pixels (dots)
                arr = np.array(img)
                non_white = np.any(arr != [255, 255, 255], axis=-1)
                assert np.any(non_white), "Image appears to be all white"

    def test_ans_hard_ratios_generation(self, tmp_path):
        """Test ANS generation with hard ratios."""
        test_images_dir = get_test_images_dir()
        config = {
            **ANS_GENERAL_CONFIG,
            "train_num": 1,
            "test_num": 1,
            "output_dir": str(test_images_dir / "ans_hard"),
            "ratios": "hard",
            "ONE_COLOUR": False,
            "min_point_num": 3,
            "max_point_num": 8,
            "background_colour": "white",
            "dot_colour": "black",
            "min_point_radius": 6,
            "max_point_radius": 10,
        }
        
        generator = PointsGenerator(config)
        generator.generate_images()
        
        # Check that images were created
        output_dir = Path(config["output_dir"])
        assert output_dir.exists()
        
        yellow_dir = output_dir / "yellow"
        blue_dir = output_dir / "blue"
        
        yellow_images = list(yellow_dir.glob("*.png"))
        blue_images = list(blue_dir.glob("*.png"))
        
        assert len(yellow_images) > 0
        assert len(blue_images) > 0

    def test_ans_one_colour_generation(self, tmp_path):
        """Test ANS generation in one-colour mode."""
        test_images_dir = get_test_images_dir()
        config = {
            **ANS_GENERAL_CONFIG,
            "train_num": 1,
            "test_num": 1,
            "output_dir": str(test_images_dir / "ans_one_colour"),
            "ratios": "all",
            "ONE_COLOUR": True,
            "colour_1": "red",
            "min_point_num": 2,
            "max_point_num": 5,
            "background_colour": "white",
            "dot_colour": "red",
            "min_point_radius": 10,
            "max_point_radius": 15,
        }
        
        generator = PointsGenerator(config)
        generator.generate_images()
        
        # Check that images were created
        output_dir = Path(config["output_dir"])
        assert output_dir.exists()
        
        red_dir = output_dir / "red"
        assert red_dir.exists()
        
        red_images = list(red_dir.glob("*.png"))
        assert len(red_images) > 0
        
        # Verify image properties
        with Image.open(red_images[0]) as img:
            assert img.size == (512, 512)
            assert img.mode == "RGB"


class TestMatchToSampleImageGeneration:
    """Test match-to-sample image generation end-to-end."""

    def test_mts_easy_ratios_generation(self, tmp_path):
        """Test MTS generation with easy ratios."""
        test_images_dir = get_test_images_dir()
        config = {
            **MTS_GENERAL_CONFIG,
            "train_num": 1,
            "test_num": 1,
            "output_dir": str(test_images_dir / "mts_easy"),
            "ratios": "easy",
            "min_point_num": 2,
            "max_point_num": 6,
            "background_colour": "white",
            "dot_colour": "black",
            "min_radius": 8,
            "max_radius": 12,
            "tolerance": 0.01,
            "attempts_limit": 1000,
        }
        
        generator = MatchToSampleGenerator(config)
        generator.generate_images()
        
        # Check that images were created
        output_dir = Path(config["output_dir"])
        assert output_dir.exists()
        
        # Look for sample and match images
        sample_images = list(output_dir.glob("*_s.png"))
        match_images = list(output_dir.glob("*_m.png"))
        
        assert len(sample_images) > 0, "No sample images generated"
        assert len(match_images) > 0, "No match images generated"
        
        # Verify image properties
        for img_path in sample_images[:2]:  # Check first 2 images
            with Image.open(img_path) as img:
                assert img.size == (512, 512)
                assert img.mode == "RGB"
                
                # Check that image has non-white pixels
                arr = np.array(img)
                non_white = np.any(arr != [255, 255, 255], axis=-1)
                assert np.any(non_white), "Sample image appears to be all white"

    def test_mts_hard_ratios_generation(self, tmp_path):
        """Test MTS generation with hard ratios."""
        test_images_dir = get_test_images_dir()
        config = {
            **MTS_GENERAL_CONFIG,
            "train_num": 1,
            "test_num": 1,
            "output_dir": str(test_images_dir / "mts_hard"),
            "ratios": "hard",
            "min_point_num": 3,
            "max_point_num": 8,
            "background_colour": "white",
            "dot_colour": "black",
            "min_radius": 6,
            "max_radius": 10,
            "tolerance": 0.005,  # Stricter tolerance
            "attempts_limit": 2000,
        }
        
        generator = MatchToSampleGenerator(config)
        generator.generate_images()
        
        # Check that images were created
        output_dir = Path(config["output_dir"])
        assert output_dir.exists()
        
        sample_images = list(output_dir.glob("*_s.png"))
        match_images = list(output_dir.glob("*_m.png"))
        
        assert len(sample_images) > 0
        assert len(match_images) > 0

    def test_mts_equalized_pairs(self, tmp_path):
        """Test MTS generation with area equalization."""
        test_images_dir = get_test_images_dir()
        config = {
            **MTS_GENERAL_CONFIG,
            "train_num": 1,
            "test_num": 1,
            "output_dir": str(test_images_dir / "mts_equalized"),
            "ratios": "all",
            "min_point_num": 2,
            "max_point_num": 4,
            "background_colour": "white",
            "dot_colour": "black",
            "min_radius": 10,
            "max_radius": 15,
            "tolerance": 0.01,
            "attempts_limit": 1000,
        }
        
        generator = MatchToSampleGenerator(config)
        generator.generate_images()
        
        # Check that images were created
        output_dir = Path(config["output_dir"])
        assert output_dir.exists()
        
        # Look for equalized pairs
        equalized_samples = list(output_dir.glob("*_equalized_s.png"))
        equalized_matches = list(output_dir.glob("*_equalized_m.png"))
        
        assert len(equalized_samples) > 0, "No equalized sample images generated"
        assert len(equalized_matches) > 0, "No equalized match images generated"
        
        # Verify that equalized pairs exist
        assert len(equalized_samples) == len(equalized_matches), "Mismatched equalized pairs"


class TestShapesImageGeneration:
    """Test shape image generation end-to-end."""

    def test_shapes_generation(self, tmp_path):
        """Test shape generation."""
        test_images_dir = get_test_images_dir()
        generator = ShapesGenerator(
            shapes=["circle", "square", "triangle"],
            colours=["blue"],
            task_type="shape_recognition",
            output_dir=str(test_images_dir / "shapes"),
            train_num=1,
            test_num=1,
            jitter=0,
            min_surface=50,
            max_surface=100,
            background_colour="white",
        )
        generator.generate_images()
        
        # Check that images were created
        output_dir = Path(test_images_dir / "shapes")
        assert output_dir.exists()
        
        # ShapesGenerator creates train/test subdirectories with shape_colour subdirectories
        shape_images = list(output_dir.rglob("*.png"))
        assert len(shape_images) > 0
        
        # Verify image properties
        for img_path in shape_images[:2]:
            with Image.open(img_path) as img:
                assert img.size == (512, 512)
                assert img.mode == "RGB"
                
                # Check that image has non-white pixels
                arr = np.array(img)
                non_white = np.any(arr != [255, 255, 255], axis=-1)
                assert np.any(non_white), "Shape image appears to be all white"


class TestLinesImageGeneration:
    """Test line pattern image generation end-to-end."""

    def test_lines_generation(self, tmp_path):
        """Test line pattern generation."""
        test_images_dir = get_test_images_dir()
        config = {
            "output_dir": str(test_images_dir / "lines"),
            "train_num": 2,
            "test_num": 2,
            "min_thickness": 3,
            "max_thickness": 5,
            "min_spacing": 20,
            "min_stripe_num": 3,
            "max_stripe_num": 8,
            "img_size": 512,
            "angles": [0, 90],
            "max_attempts": 100,
            "tag": "test",
            "background_colour": "#000000",  # Black background
        }
        
        generator = StripePatternGenerator(config)
        generator.create_images()
        
        # Check that images were created
        output_dir = Path(test_images_dir / "lines")
        assert output_dir.exists()
        
        # StripePatternGenerator creates angle subdirectories
        line_images = list(output_dir.rglob("*.png"))
        assert len(line_images) > 0
        
        # Verify image properties
        for img_path in line_images[:2]:
            with Image.open(img_path) as img:
                assert img.size == (512, 512)
                assert img.mode == "RGB"
                
                # Check that image has non-black pixels (white stripes on black background)
                arr = np.array(img)
                non_black = np.any(arr != [0, 0, 0], axis=-1)
                assert np.any(non_black), "Line image appears to be all black"


class TestFixationImageGeneration:
    """Test fixation target image generation end-to-end."""

    def test_fixation_generation(self, tmp_path):
        """Test fixation target generation."""
        test_images_dir = get_test_images_dir()
        config = {
            "output_dir": str(test_images_dir / "fixation"),
            "train_num": 2,
            "test_num": 2,
            "types": ["A", "B", "C"],  # A=dot, B=disk, C=cross
            "img_size": 512,
            "dot_radius_px": 5,
            "disk_radius_px": 10,
            "cross_thickness_px": 3,
            "cross_arm_px": 20,
            "jitter_px": 0,
            "background_colour": "white",
            "symbol_colour": "black",
            "tag": "test",
        }
        
        generator = FixationGenerator(config)
        generator.create_images()
        
        # Check that images were created
        output_dir = Path(test_images_dir / "fixation")
        assert output_dir.exists()
        
        fixation_images = list(output_dir.glob("*.png"))
        assert len(fixation_images) > 0
        
        # Verify image properties
        for img_path in fixation_images[:2]:
            with Image.open(img_path) as img:
                assert img.size == (512, 512)
                assert img.mode == "RGB"
                
                # Check that image has non-white pixels
                arr = np.array(img)
                non_white = np.any(arr != [255, 255, 255], axis=-1)
                assert np.any(non_white), "Fixation image appears to be all white"


class TestCLIIntegration:
    """Test CLI integration with actual image generation."""

    def test_cli_ans_generation(self, tmp_path):
        """Test CLI ANS generation."""
        from cogstim.cli import main
        import sys
        from unittest.mock import patch
        
        test_images_dir = get_test_images_dir()
        cli_args = [
            "--ans",
            "--train_num", "1",
            "--test_num", "1",
            "--min_point_num", "2",
            "--max_point_num", "4",
            "--ratios", "easy",
            "--output_dir", str(test_images_dir / "cli_ans"),
        ]
        
        with patch.object(sys, 'argv', ['cogstim'] + cli_args):
            main()
        
        # Check that images were created
        train_dir = test_images_dir / "cli_ans" / "train"
        test_dir = test_images_dir / "cli_ans" / "test"
        
        assert train_dir.exists()
        assert test_dir.exists()
        
        # Check for colour subdirectories
        yellow_train = train_dir / "yellow"
        blue_train = train_dir / "blue"
        
        assert yellow_train.exists()
        assert blue_train.exists()
        
        # Check that images were generated
        train_images = list(yellow_train.glob("*.png")) + list(blue_train.glob("*.png"))
        assert len(train_images) > 0

    def test_cli_match_to_sample_generation(self, tmp_path):
        """Test CLI match-to-sample generation."""
        from cogstim.cli import main
        import sys
        from unittest.mock import patch
        
        test_images_dir = get_test_images_dir()
        cli_args = [
            "--match_to_sample",
            "--train_num", "1",
            "--test_num", "1",
            "--min_point_num", "2",
            "--max_point_num", "4",
            "--ratios", "easy",
            "--output_dir", str(test_images_dir / "cli_mts"),
        ]
        
        with patch.object(sys, 'argv', ['cogstim'] + cli_args):
            main()
        
        # Check that images were created
        train_dir = test_images_dir / "cli_mts" / "train"
        test_dir = test_images_dir / "cli_mts" / "test"
        
        assert train_dir.exists()
        assert test_dir.exists()
        
        # Check that sample and match images were generated
        train_samples = list(train_dir.glob("*_s.png"))
        train_matches = list(train_dir.glob("*_m.png"))
        
        assert len(train_samples) > 0
        assert len(train_matches) > 0

    def test_cli_one_colour_generation(self, tmp_path):
        """Test CLI one-colour generation."""
        from cogstim.cli import main
        import sys
        from unittest.mock import patch
        
        test_images_dir = get_test_images_dir()
        cli_args = [
            "--one_colour",
            "--train_num", "1",
            "--test_num", "1",
            "--min_point_num", "2",
            "--max_point_num", "4",
            "--ratios", "all",
            "--output_dir", str(test_images_dir / "cli_one_colour"),
        ]
        
        with patch.object(sys, 'argv', ['cogstim'] + cli_args):
            main()
        
        # Check that images were created
        train_dir = test_images_dir / "cli_one_colour" / "train"
        test_dir = test_images_dir / "cli_one_colour" / "test"
        
        assert train_dir.exists()
        assert test_dir.exists()
        
        # Check for colour subdirectory
        yellow_train = train_dir / "yellow"
        assert yellow_train.exists()
        
        # Check that images were generated
        train_images = list(yellow_train.glob("*.png"))
        assert len(train_images) > 0


class TestImageProperties:
    """Test properties of generated images."""

    def test_image_dimensions_consistency(self, tmp_path):
        """Test that all generated images have consistent dimensions."""
        test_images_dir = get_test_images_dir()
        # Generate different types of images
        configs = [
            {
                **ANS_GENERAL_CONFIG,
                "train_num": 1,
            "test_num": 1,
                "output_dir": str(test_images_dir / "ans_test"),
                "ratios": "easy",
                "ONE_COLOUR": True,
                "colour_1": "blue",
                "min_point_num": 2,
                "max_point_num": 4,
            },
            {
                **MTS_GENERAL_CONFIG,
                "train_num": 1,
            "test_num": 1,
                "output_dir": str(test_images_dir / "mts_test"),
                "ratios": "easy",
                "min_point_num": 2,
                "max_point_num": 4,
            },
        ]
        
        generators = [
            PointsGenerator(configs[0]),
            MatchToSampleGenerator(configs[1]),
        ]
        
        # Generate images
        for generator in generators:
            generator.generate_images()
        
        # Check all generated images
        all_images = []
        for config in configs:
            output_dir = Path(config["output_dir"])
            if output_dir.exists():
                all_images.extend(output_dir.rglob("*.png"))
        
        assert len(all_images) > 0, "No images were generated"
        
        # Verify all images have the same dimensions
        for img_path in all_images:
            with Image.open(img_path) as img:
                assert img.size == (512, 512), f"Image {img_path} has wrong size: {img.size}"
                assert img.mode == "RGB", f"Image {img_path} has wrong mode: {img.mode}"

    def test_image_content_diversity(self, tmp_path):
        """Test that generated images have diverse content."""
        test_images_dir = get_test_images_dir()
        config = {
            **ANS_GENERAL_CONFIG,
            "train_num": 3,
            "test_num": 3,
            "output_dir": str(test_images_dir / "diversity_test"),
            "ratios": "all",
            "ONE_COLOUR": True,
            "colour_1": "red",
            "min_point_num": 2,
            "max_point_num": 8,
        }

        generator = PointsGenerator(config)
        generator.generate_images()
        
        # Get generated images
        output_dir = Path(config["output_dir"])
        red_dir = output_dir / "red"
        images = sorted(list(red_dir.glob("*.png")))  # Sort to ensure consistent order

        assert len(images) >= 3, "Not enough images generated"

        # Check that images are different (not identical)
        image_arrays = []
        for img_path in images:
            with Image.open(img_path) as img:
                arr = np.array(img)
                image_arrays.append(arr)

        # Find at least one pair of different images
        found_difference = False
        for i in range(len(image_arrays)):
            for j in range(i + 1, len(image_arrays)):
                if not np.array_equal(image_arrays[i], image_arrays[j]):
                    found_difference = True
                    break
            if found_difference:
                break

        assert found_difference, "All images are identical - randomization is not working"

    def test_image_file_properties(self, tmp_path):
        """Test file properties of generated images."""
        test_images_dir = get_test_images_dir()
        config = {
            **MTS_GENERAL_CONFIG,
            "train_num": 1,
            "test_num": 1,
            "output_dir": str(test_images_dir / "file_properties_test"),
            "ratios": "easy",
            "min_point_num": 2,
            "max_point_num": 4,
        }
        
        generator = MatchToSampleGenerator(config)
        generator.generate_images()
        
        # Get generated images
        output_dir = Path(config["output_dir"])
        images = list(output_dir.glob("*.png"))
        
        assert len(images) > 0, "No images generated"
        
        # Check file properties
        for img_path in images:
            # Check file exists and is readable
            assert img_path.exists(), f"Image file {img_path} does not exist"
            assert img_path.is_file(), f"{img_path} is not a file"
            assert img_path.stat().st_size > 0, f"Image file {img_path} is empty"
            
            # Check that it's a valid PNG
            with Image.open(img_path) as img:
                assert img.format == "PNG", f"Image {img_path} is not a PNG"
                assert img.size[0] > 0 and img.size[1] > 0, f"Image {img_path} has invalid size"
