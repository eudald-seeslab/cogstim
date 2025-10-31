import tempfile
from pathlib import Path

from cogstim.lines import StripePatternGenerator


def test_stripe_pattern_generator_single_set():
    """StripePatternGenerator should create the expected number of images for a minimal config."""

    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = {
            "output_dir": tmpdir,
            "img_sets": 1,  # one repetition
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

        generator = StripePatternGenerator(cfg)
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