from cogstim.generators.shapes import ShapesGenerator
from cogstim.helpers.constants import COLOUR_MAP
import tempfile
import pytest
from unittest.mock import patch
import os


def test_draw_shape_circle():
    with tempfile.TemporaryDirectory() as tmpdir:
        sg = ShapesGenerator(
            shapes=["circle"],
            colours=["yellow"],
            task_type="two_shapes",
            output_dir=tmpdir,
            train_num=1,
            test_num=0,
            jitter=False,
            min_surface=10000,
            max_surface=10001,
            background_colour="black",
        )
        img, dist, angle = sg.draw_shape("circle", 10000, COLOUR_MAP["yellow"], jitter=False)

        # Basic sanity checks
        assert img.size == (512, 512)
        assert 0 <= dist <= 124  # within max jitter range used in code
        assert 0 <= angle <= 360


def test_shapes_generator_directory_two_shapes():
    """Test directory creation for two_shapes task type."""
    sg = ShapesGenerator(
        shapes=["circle", "star"],
        colours=["yellow"],
        task_type="two_shapes",
        output_dir=None,  # Should use default
        train_num=1,
        test_num=1,
        jitter=False,
        min_surface=1000,
        max_surface=2000,
        background_colour="black",
    )

    assert sg.output_dir == "images/two_shapes"


def test_shapes_generator_directory_two_colors():
    """Test directory creation for two_colors task type."""
    sg = ShapesGenerator(
        shapes=["circle"],
        colours=["yellow", "blue"],
        task_type="two_colors",
        output_dir=None,  # Should use default
        train_num=1,
        test_num=1,
        jitter=False,
        min_surface=1000,
        max_surface=2000,
        background_colour="black",
    )

    assert sg.output_dir == "images/two_colors"


def test_shapes_generator_directory_custom():
    """Test directory creation for custom task type."""
    sg = ShapesGenerator(
        shapes=["circle", "triangle"],
        colours=["red", "blue"],
        task_type="custom",
        output_dir=None,  # Should use default
        train_num=1,
        test_num=1,
        jitter=False,
        min_surface=1000,
        max_surface=2000,
        background_colour="black",
    )

    assert sg.output_dir == "images/circle_triangle_red_blue"


def test_shapes_generator_directory_explicit():
    """Test directory creation with explicit img_dir."""
    sg = ShapesGenerator(
        shapes=["circle"],
        colours=["yellow"],
        task_type="two_shapes",
        output_dir="/custom/path",
        train_num=1,
        test_num=1,
        jitter=False,
        min_surface=1000,
        max_surface=2000,
        background_colour="black",
    )

    assert sg.output_dir == "/custom/path"


def test_create_dirs_two_shapes():
    """Test create_dirs for two_shapes task type."""
    with patch('os.makedirs') as mock_makedirs:
        sg = ShapesGenerator(
            shapes=["circle", "star"],
            colours=["yellow"],
            task_type="two_shapes",
            output_dir="/tmp/test",
            train_num=1,
            test_num=1,
            jitter=False,
            min_surface=1000,
            max_surface=2000,
            background_colour="black",
        )

        sg.setup_directories()

        # Should create base dir + train/test subdirs for each shape
        # 1 base + 2 shapes × 2 phases = 5 dirs
        assert mock_makedirs.call_count == 5
        # Check that the right directories were created
        call_args = [call[0][0] for call in mock_makedirs.call_args_list]
        expected_dirs = [
            "/tmp/test",  # base directory
            os.path.join("/tmp/test", "train", "circle"),
            os.path.join("/tmp/test", "train", "star"),
            os.path.join("/tmp/test", "test", "circle"),
            os.path.join("/tmp/test", "test", "star"),
        ]
        for expected_dir in expected_dirs:
            assert expected_dir in call_args


def test_create_dirs_two_colors():
    """Test create_dirs for two_colors task type."""
    with patch('os.makedirs') as mock_makedirs:
        sg = ShapesGenerator(
            shapes=["circle"],
            colours=["yellow", "blue"],
            task_type="two_colors",
            output_dir="/tmp/test",
            train_num=1,
            test_num=1,
            jitter=False,
            min_surface=1000,
            max_surface=2000,
            background_colour="black",
        )

        sg.setup_directories()

        # Should create base dir + train/test subdirs for each color
        # 1 base + 2 colors × 2 phases = 5 dirs
        assert mock_makedirs.call_count == 5
        # Check that the right directories were created
        call_args = [call[0][0] for call in mock_makedirs.call_args_list]
        expected_dirs = [
            "/tmp/test",  # base directory
            os.path.join("/tmp/test", "train", "yellow"),
            os.path.join("/tmp/test", "train", "blue"),
            os.path.join("/tmp/test", "test", "yellow"),
            os.path.join("/tmp/test", "test", "blue"),
        ]
        for expected_dir in expected_dirs:
            assert expected_dir in call_args


def test_get_radius_from_surface_invalid_shape():
    """Test get_radius_from_surface with invalid shape."""
    with pytest.raises(ValueError, match="Shape invalid not implemented"):
        ShapesGenerator.get_radius_from_surface("invalid", 1000)


def test_get_vertices_invalid_shape():
    """Test get_vertices with invalid shape."""
    sg = ShapesGenerator(
        shapes=["circle"],
        colours=["yellow"],
        task_type="two_shapes",
        output_dir="/tmp/test",
        train_num=1,
        test_num=1,
        jitter=False,
        min_surface=1000,
        max_surface=2000,
        background_colour="black",
    )

    with pytest.raises(ValueError, match="Shape invalid not implemented"):
        sg.get_vertices("invalid", (256, 256), 50)


def test_generate_images_two_colors():
    """Test generate_images for two_colors task type."""
    with tempfile.TemporaryDirectory() as tmpdir:
        sg = ShapesGenerator(
            shapes=["circle"],  # Not used in two_colors mode
            colours=["yellow", "red"],
            task_type="two_colors",
            output_dir=tmpdir,
            train_num=1,
            test_num=1,
            jitter=False,
            min_surface=1000,
            max_surface=1001,  # Single surface value
            background_colour="black",
        )

        # Mock the save_image method to avoid actual file I/O
        with patch.object(sg, 'save_image') as mock_save:
            sg.generate_images()

            # Should call save_image for each color × each phase × each surface
            # 2 colors × 2 phases × 1 surface = 4 calls
            assert mock_save.call_count == 4

            # Check that all calls use the base shape (circle) with different colors
            for call in mock_save.call_args_list:
                args = call[0]
                shape_arg = args[1]  # shape parameter
                assert shape_arg == "circle"  # Should always be the base shape
