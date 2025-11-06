from cogstim.generators.dots_ans import DotsANSGenerator, GENERAL_CONFIG
from pathlib import Path


def test_points_generator_creates_images(tmp_path):
    cfg = GENERAL_CONFIG | {
        "train_num": 1,
        "test_num": 1,
        "output_dir": str(tmp_path),
        "ratios": "easy",
        "EASY": True,
        "ONE_COLOUR": True,
        "version_tag": "",
        "min_point_num": 1,
        "max_point_num": 2,
    }

    gen = DotsANSGenerator(cfg)
    gen.generate_images()

    images = list(Path(cfg["output_dir"]).rglob("*.png"))
    assert len(images) > 0 