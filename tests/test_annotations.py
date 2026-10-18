"""Tests for stimulus annotations and vector output.

Reviewer @srvanderplas rejected the paper's computer-vision and eye-tracking
claims in JOSS review openjournals/joss-reviews#10532 because the package wrote
images and nothing describing what was in them, and the paper claimed SVG
output that --img-format never accepted.

The annotations are only worth anything if they agree with the pixels, so the
central test here checks them against the rendered image rather than against
the code that produced them.
"""

import csv
import json
import subprocess
import sys
import xml.etree.ElementTree as ElementTree
from pathlib import Path

import pytest
from PIL import Image

from cogstim.helpers.geometry import DrawnElement, Scene, ELLIPSE, RECTANGLE
from cogstim.helpers.annotations import scene_to_svg


def run_cli(*argv):
    """Invoke the CLI in a subprocess and return the completed process."""
    result = subprocess.run(
        [sys.executable, "-m", "cogstim.cli", *map(str, argv)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert result.returncode == 0, f"CLI failed:\n{result.stdout}\n{result.stderr}"
    return result


DOTS_ARGS = ["ans", "--train-num", 1, "--test-num", 0,
             "--min-dot-num", 2, "--max-dot-num", 3, "--ratios", "easy",
             "--seed", 11]


class TestAnnotationsDescribeTheImage:
    """The exported geometry must match what was actually drawn."""

    def test_annotated_dot_centres_carry_the_annotated_colour(self, tmp_path):
        """Every annotated dot's centre pixel is that dot's colour.

        This is the property that makes the export usable for training or for
        eye-tracking: if a bounding box did not sit on the feature it claims to
        describe, the file would be worse than useless.
        """
        run_cli(*DOTS_ARGS, "--metadata", "csv", "--output-dir", tmp_path)

        rows = list(csv.DictReader((tmp_path / "annotations.csv").open(encoding="utf-8")))
        assert rows, "No annotations were exported"

        checked = 0
        for row in rows:
            if row["kind"] != ELLIPSE:
                continue
            image_path = tmp_path / row["image"]
            with Image.open(image_path) as img:
                pixel = img.convert("RGB").getpixel(
                    (round(float(row["centre_x"])), round(float(row["centre_y"])))
                )
            expected = row["colour"].lstrip("#")
            expected_rgb = tuple(int(expected[i:i + 2], 16) for i in (0, 2, 4))
            assert pixel == expected_rgb, (
                f"{row['image']} element {row['element_index']}: annotation says "
                f"{row['colour']} at ({row['centre_x']}, {row['centre_y']}) "
                f"but the pixel is {pixel}"
            )
            checked += 1
        assert checked > 0, "No ellipse annotations to verify"

    def test_bounding_boxes_lie_within_the_canvas(self, tmp_path):
        """Recorded boxes must describe the finished image, not a working canvas."""
        run_cli(*DOTS_ARGS, "--metadata", "csv", "--output-dir", tmp_path)

        rows = list(csv.DictReader((tmp_path / "annotations.csv").open(encoding="utf-8")))
        for row in rows:
            with Image.open(tmp_path / row["image"]) as img:
                width, height = img.size
            assert float(row["bbox_x_min"]) >= 0
            assert float(row["bbox_y_min"]) >= 0
            assert float(row["bbox_x_max"]) <= width
            assert float(row["bbox_y_max"]) <= height

    def test_dot_count_matches_the_filename(self, tmp_path):
        """ANS filenames encode the dot counts; the annotations must agree."""
        run_cli(*DOTS_ARGS, "--metadata", "csv", "--output-dir", tmp_path)

        rows = list(csv.DictReader((tmp_path / "annotations.csv").open(encoding="utf-8")))
        per_image = {}
        for row in rows:
            per_image.setdefault(row["image"], []).append(row)

        for image, elements in per_image.items():
            # img_{n1}_{n2}_{rep}[...].png
            name = Path(image).name
            n1, n2 = (int(part) for part in name.split("_")[1:3])
            assert len(elements) == n1 + n2, (
                f"{image} should contain {n1 + n2} dots but {len(elements)} "
                "were annotated"
            )

    def test_json_export_groups_by_image(self, tmp_path):
        """The JSON form nests elements under their image and records the canvas."""
        run_cli(*DOTS_ARGS, "--metadata", "json", "--output-dir", tmp_path)

        payload = json.loads((tmp_path / "annotations.json").read_text(encoding="utf-8"))
        assert payload["canvas"]["width"] > 0
        assert payload["images"]
        for entry in payload["images"]:
            assert entry["elements"]
            assert {"label", "kind", "centre_x", "bbox_x_min"} <= set(entry["elements"][0])

    def test_no_annotations_written_by_default(self, tmp_path):
        """Annotations are opt-in, so existing workflows are unaffected."""
        run_cli(*DOTS_ARGS, "--output-dir", tmp_path)
        assert not (tmp_path / "annotations.csv").exists()
        assert not (tmp_path / "annotations.json").exists()


class TestVectorOutput:
    """SVG output, which the paper claimed but --img-format never accepted."""

    @pytest.mark.parametrize(
        "argv",
        [
            ["ans", "--train-num", 1, "--test-num", 0, "--min-dot-num", 2,
             "--max-dot-num", 3, "--ratios", "easy"],
            ["shapes", "--train-num", 1, "--test-num", 0, "--surface-step-px", 5000],
            ["lines", "--train-num", 1, "--test-num", 0, "--angles", 45],
            ["fixation", "--types", "ABC"],
            ["mask", "--mask-num", 1, "--dot-num", 20],
        ],
    )
    def test_every_task_can_produce_valid_svg(self, tmp_path, argv):
        """Each task writes SVG that parses and carries the drawn elements."""
        run_cli(*argv, "--img-format", "svg", "--seed", 5, "--output-dir", tmp_path)

        files = list(tmp_path.rglob("*.svg"))
        assert files, "No SVG files were written"

        for path in files[:3]:
            root = ElementTree.parse(path).getroot()
            assert root.tag.endswith("svg")
            drawn = [
                child for child in root
                if child.get("data-label") is not None
            ]
            assert drawn, f"{path.name} contains no stimulus elements"

    def test_svg_dimensions_match_the_requested_size(self, tmp_path):
        run_cli("fixation", "--types", "B", "--img-format", "svg",
                "--img-size", 256, "--output-dir", tmp_path)

        root = ElementTree.parse(next(tmp_path.rglob("*.svg"))).getroot()
        assert root.get("width") == "256"
        assert root.get("height") == "256"


class TestSceneToSvg:
    """Unit-level checks of the vector rendering itself."""

    def test_ellipse_becomes_an_ellipse_tag(self):
        scene = Scene(100, 100, "#ffffff")
        scene.add(DrawnElement(ELLIPSE, ((10, 20), (30, 60)), "#ff0000", "dot"))

        svg = scene_to_svg(scene)
        root = ElementTree.fromstring(svg)
        ellipse = [c for c in root if c.tag.endswith("ellipse")][0]

        assert ellipse.get("cx") == "20"
        assert ellipse.get("cy") == "40"
        assert ellipse.get("rx") == "10"
        assert ellipse.get("ry") == "20"
        assert ellipse.get("fill") == "#ff0000"

    def test_rotating_a_rectangle_yields_a_polygon(self):
        """A rotated box is no longer axis-aligned, so it cannot stay a rect."""
        element = DrawnElement(RECTANGLE, ((0, 0), (10, 10)), "#000000", "stripe")
        rotated = element.transformed(45, centre=(5, 5), offset=(0, 0))

        assert rotated.kind == "polygon"
        assert len(rotated.points) == 4

    def test_transform_is_identity_without_rotation_or_offset(self):
        element = DrawnElement(RECTANGLE, ((1, 2), (3, 4)), "#000000")
        same = element.transformed(0, centre=(0, 0), offset=(0, 0))
        assert [tuple(round(v, 6) for v in p) for p in same.points] == [(1, 2), (3, 4)]
