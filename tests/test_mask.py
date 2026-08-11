"""Tests for cogstim.generators.mask module."""

import os
import tempfile
from unittest.mock import patch

from PIL import Image

from cogstim.generators.mask import MaskGenerator
from cogstim.helpers.constants import MASK_DEFAULTS, IMAGE_DEFAULTS, DOT_DEFAULTS


def _base_config(tmpdir, **overrides):
    cfg = {
        "output_dir": tmpdir,
        "num_masks": 3,
        "num_dots": 50,
        "min_dot_radius": MASK_DEFAULTS["min_dot_radius"],
        "max_dot_radius": MASK_DEFAULTS["max_dot_radius"],
        "dot_colour": MASK_DEFAULTS["dot_colour"],
        "background_colour": MASK_DEFAULTS["background_colour"],
        "init_size": IMAGE_DEFAULTS["init_size"],
        "img_format": "png",
        "seed": 7,
    }
    cfg.update(overrides)
    return cfg


class TestMaskGeneratorInit:
    """Test MaskGenerator initialisation and configuration."""

    def test_default_values(self, tmp_path):
        config = _base_config(str(tmp_path))
        gen = MaskGenerator(config)
        assert gen.num_masks == 3
        assert gen.num_dots == 50
        assert gen.min_dot_radius == MASK_DEFAULTS["min_dot_radius"]
        assert gen.max_dot_radius == MASK_DEFAULTS["max_dot_radius"]

    def test_custom_values(self, tmp_path):
        config = _base_config(str(tmp_path), num_masks=10, num_dots=200,
                              min_dot_radius=2, max_dot_radius=40)
        gen = MaskGenerator(config)
        assert gen.num_masks == 10
        assert gen.num_dots == 200
        assert gen.min_dot_radius == 2
        assert gen.max_dot_radius == 40

    def test_colour_resolution(self, tmp_path):
        config = _base_config(str(tmp_path), dot_colour="red", background_colour="blue")
        gen = MaskGenerator(config)
        assert gen.dot_colour == "#ff0000"
        assert gen.bg_colour == "#0003f9"


class TestMaskImageCreation:
    """Test the mask image creation logic."""

    def test_create_mask_image_returns_canvas(self, tmp_path):
        gen = MaskGenerator(_base_config(str(tmp_path)))
        canvas = gen._create_mask_image()
        assert hasattr(canvas, "img")
        assert isinstance(canvas.img, Image.Image)
        assert canvas.img.size == (IMAGE_DEFAULTS["init_size"], IMAGE_DEFAULTS["init_size"])

    def test_create_mask_image_custom_size(self, tmp_path):
        gen = MaskGenerator(_base_config(str(tmp_path), init_size=256))
        canvas = gen._create_mask_image()
        assert canvas.img.size == (256, 256)


class TestMaskGeneration:
    """Test the full generate_images workflow."""

    def test_generates_correct_number_of_files(self, tmp_path):
        config = _base_config(str(tmp_path), num_masks=4, num_dots=20)
        gen = MaskGenerator(config)
        total = gen.generate_images()
        assert total == 4
        pngs = [f for f in os.listdir(str(tmp_path)) if f.endswith(".png")]
        assert len(pngs) == 4

    def test_file_naming(self, tmp_path):
        config = _base_config(str(tmp_path), num_masks=2, num_dots=10)
        gen = MaskGenerator(config)
        gen.generate_images()
        files = sorted(os.listdir(str(tmp_path)))
        assert files == ["mask_0000.png", "mask_0001.png"]

    def test_file_naming_with_version_tag(self, tmp_path):
        config = _base_config(str(tmp_path), num_masks=1, num_dots=10, version_tag="v3")
        gen = MaskGenerator(config)
        gen.generate_images()
        files = os.listdir(str(tmp_path))
        assert files == ["mask_0000_v3.png"]

    def test_jpg_format(self, tmp_path):
        config = _base_config(str(tmp_path), num_masks=1, num_dots=10, img_format="jpg")
        gen = MaskGenerator(config)
        gen.generate_images()
        files = os.listdir(str(tmp_path))
        assert files == ["mask_0000.jpg"]

    def test_seed_reproducibility(self, tmp_path):
        dir_a = tmp_path / "a"
        dir_b = tmp_path / "b"
        dir_a.mkdir()
        dir_b.mkdir()

        for d in (dir_a, dir_b):
            gen = MaskGenerator(_base_config(str(d), num_masks=1, num_dots=30, seed=99))
            gen.generate_images()

        img_a = Image.open(dir_a / "mask_0000.png")
        img_b = Image.open(dir_b / "mask_0000.png")
        assert list(img_a.tobytes()) == list(img_b.tobytes())

    def test_images_are_not_blank(self, tmp_path):
        """Mask images should contain visible dots (not a blank canvas)."""
        gen = MaskGenerator(_base_config(str(tmp_path), num_masks=1, num_dots=100))
        gen.generate_images()
        img = Image.open(os.path.join(str(tmp_path), "mask_0000.png"))
        blank = Image.new("RGB", img.size, (255, 255, 255))
        assert img.tobytes() != blank.tobytes(), "Mask image appears completely blank"


class TestSeparatedLayout:
    """Test the separated layout (two halves with gap)."""

    def test_layout_attribute(self, tmp_path):
        gen = MaskGenerator(_base_config(str(tmp_path), layout="separated"))
        assert gen.layout == "separated"

    def test_default_layout_is_full(self, tmp_path):
        gen = MaskGenerator(_base_config(str(tmp_path)))
        assert gen.layout == "full"

    def test_separated_file_naming(self, tmp_path):
        config = _base_config(str(tmp_path), num_masks=2, num_dots=20, layout="separated")
        gen = MaskGenerator(config)
        gen.generate_images()
        files = sorted(os.listdir(str(tmp_path)))
        assert files == ["mask_0000_separated.png", "mask_0001_separated.png"]

    def test_separated_with_version_tag(self, tmp_path):
        config = _base_config(str(tmp_path), num_masks=1, num_dots=20,
                              layout="separated", version_tag="v2")
        gen = MaskGenerator(config)
        gen.generate_images()
        files = os.listdir(str(tmp_path))
        assert files == ["mask_0000_separated_v2.png"]

    def test_separated_generates_correct_count(self, tmp_path):
        config = _base_config(str(tmp_path), num_masks=5, num_dots=30, layout="separated")
        gen = MaskGenerator(config)
        total = gen.generate_images()
        assert total == 5
        assert len(os.listdir(str(tmp_path))) == 5

    def test_separated_gap_leaves_empty_strip(self, tmp_path):
        """The vertical centre strip (the gap) should stay background colour."""
        gap = 60
        size = 256
        config = _base_config(str(tmp_path), num_masks=1, num_dots=600,
                              layout="separated", gap=gap, init_size=size,
                              dot_colour="black", background_colour="white",
                              min_dot_radius=3, max_dot_radius=5, seed=17)
        gen = MaskGenerator(config)
        gen.generate_images()
        img = Image.open(os.path.join(str(tmp_path), "mask_0000_separated.png"))
        half = size // 2
        gap_start = half - gap // 2
        gap_end = half + gap // 2
        # Sample a column of pixels in the gap centre
        gap_centre_x = (gap_start + gap_end) // 2
        bg = (255, 255, 255)
        for y in range(size):
            assert img.getpixel((gap_centre_x, y)) == bg, (
                f"Pixel at ({gap_centre_x}, {y}) should be background in the gap"
            )

    def test_separated_image_not_blank(self, tmp_path):
        config = _base_config(str(tmp_path), num_masks=1, num_dots=100, layout="separated")
        gen = MaskGenerator(config)
        gen.generate_images()
        img = Image.open(os.path.join(str(tmp_path), "mask_0000_separated.png"))
        blank = Image.new("RGB", img.size, (255, 255, 255))
        assert img.tobytes() != blank.tobytes()

    def test_separated_seed_reproducibility(self, tmp_path):
        dir_a = tmp_path / "a"
        dir_b = tmp_path / "b"
        dir_a.mkdir()
        dir_b.mkdir()
        for d in (dir_a, dir_b):
            gen = MaskGenerator(_base_config(str(d), num_masks=1, num_dots=50,
                                             layout="separated", seed=77))
            gen.generate_images()
        img_a = Image.open(dir_a / "mask_0000_separated.png")
        img_b = Image.open(dir_b / "mask_0000_separated.png")
        assert img_a.tobytes() == img_b.tobytes()

    def test_custom_gap(self, tmp_path):
        gen = MaskGenerator(_base_config(str(tmp_path), layout="separated", gap=80))
        assert gen.gap == 80


class TestTwoColourMasks:
    """Test two-colour mask generation (for ANS-style masks)."""

    def test_no_second_colour_by_default(self, tmp_path):
        gen = MaskGenerator(_base_config(str(tmp_path)))
        assert gen.dot_colour_2 is None

    def test_second_colour_resolved(self, tmp_path):
        gen = MaskGenerator(_base_config(str(tmp_path), dot_colour_2="blue"))
        assert gen.dot_colour_2 == "#0003f9"

    def test_two_colour_image_contains_both_colours(self, tmp_path):
        """With two colours on a contrasting background, both should appear."""
        config = _base_config(
            str(tmp_path), num_masks=1, num_dots=500, seed=13,
            dot_colour="yellow", dot_colour_2="blue",
            background_colour="black", init_size=256,
        )
        gen = MaskGenerator(config)
        gen.generate_images()
        img = Image.open(os.path.join(str(tmp_path), "mask_0000.png"))
        colours_found = set()
        for x in range(img.size[0]):
            for y in range(img.size[1]):
                colours_found.add(img.getpixel((x, y)))
        # Yellow = #fffe04 = (255, 254, 4), Blue = #0003f9 = (0, 3, 249)
        has_yellow = any(px[0] > 200 and px[2] < 50 for px in colours_found)
        has_blue = any(px[2] > 200 and px[0] < 50 for px in colours_found)
        assert has_yellow, "Expected yellow dots in two-colour mask"
        assert has_blue, "Expected blue dots in two-colour mask"

    def test_two_colour_separated_colours_per_side(self, tmp_path):
        """In separated+two-colour mode, left half should be colour_1 and
        right half should be colour_2 (no mixing)."""
        size = 256
        gap = 60
        config = _base_config(
            str(tmp_path), num_masks=1, num_dots=600, seed=31,
            dot_colour="yellow", dot_colour_2="blue",
            background_colour="black", layout="separated",
            gap=gap, init_size=size, min_dot_radius=3, max_dot_radius=6,
        )
        gen = MaskGenerator(config)
        gen.generate_images()
        img = Image.open(os.path.join(str(tmp_path), "mask_0000_separated.png"))

        half = size // 2
        gap_half = gap // 2
        bg = (0, 0, 0)

        # Left half: only background or yellow-ish pixels (high R, low B)
        for x in range(0, half - gap_half):
            for y in range(size):
                px = img.getpixel((x, y))
                if px != bg:
                    assert px[0] > 200 and px[2] < 50, (
                        f"Left pixel ({x},{y})={px} should be yellow, not blue"
                    )

        # Right half: only background or blue-ish pixels (high B, low R)
        for x in range(half + gap_half, size):
            for y in range(size):
                px = img.getpixel((x, y))
                if px != bg:
                    assert px[2] > 200 and px[0] < 50, (
                        f"Right pixel ({x},{y})={px} should be blue, not yellow"
                    )

    def test_two_colour_seed_reproducibility(self, tmp_path):
        dir_a = tmp_path / "a"
        dir_b = tmp_path / "b"
        dir_a.mkdir()
        dir_b.mkdir()
        for d in (dir_a, dir_b):
            gen = MaskGenerator(_base_config(
                str(d), num_masks=1, num_dots=60, seed=55,
                dot_colour="yellow", dot_colour_2="blue",
            ))
            gen.generate_images()
        img_a = Image.open(dir_a / "mask_0000.png")
        img_b = Image.open(dir_b / "mask_0000.png")
        assert img_a.tobytes() == img_b.tobytes()

    def test_single_colour_has_no_second_colour_pixels(self, tmp_path):
        """Without dot_colour_2, all dots should be the primary colour only."""
        config = _base_config(
            str(tmp_path), num_masks=1, num_dots=200, seed=8,
            dot_colour="red", background_colour="white", init_size=128,
        )
        gen = MaskGenerator(config)
        gen.generate_images()
        img = Image.open(os.path.join(str(tmp_path), "mask_0000.png"))
        for x in range(img.size[0]):
            for y in range(img.size[1]):
                px = img.getpixel((x, y))
                # Every pixel should be either white bg or red-ish
                assert px[2] < 50 or px == (255, 255, 255), (
                    f"Unexpected colour {px} at ({x},{y}) in single-colour mask"
                )
