"""Tests for the visual properties export and the small-numerosity warning.

Gebuis & Reynvoet (2011, Behavior Research Methods, 43, 981-986) showed that
the visual properties of a dot array always covary with its numerosity in some
way, and that a stimulus generator should therefore report them so the
covariation can be checked after the fact rather than assumed away. They also
showed that arrays of fewer than 4 dots cannot have their area extended matched
to a larger array's without introducing another confound.

As with the annotations, the export is only worth anything if it describes the
images that were actually written, so the central tests check it against the
files on disk rather than against the code that produced them.
"""

import csv
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from cogstim.helpers.constants import SMALL_NUMEROSITY
from cogstim.helpers.geometry import DrawnElement, Scene, ELLIPSE
from cogstim.helpers.planner import GenerationPlan, small_numerosity_warning
from cogstim.helpers.visual_properties import (
    PAIR_FIELDS,
    PROPERTY_FIELDS,
    convex_hull_area,
    disc_hull_area,
    group_properties,
    image_property_records,
    pair_property_records,
)


def run_cli(*argv):
    """Invoke the CLI in a subprocess and return the completed process."""
    result = subprocess.run(
        [sys.executable, "-m", "cogstim.cli", *map(str, argv)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert result.returncode == 0, f"CLI failed:\n{result.stdout}\n{result.stderr}"
    return result


def read_csv(path):
    return list(csv.DictReader(Path(path).open(encoding="utf-8")))


# Counts start at 4 so that these runs do not trigger the small-numerosity
# warning, which has tests of its own below.
ANS_ARGS = ["ans", "--train-num", 1, "--test-num", 0,
            "--min-dot-num", 4, "--max-dot-num", 6, "--ratios", "easy",
            "--seed", 11]

MTS_ARGS = ["match-to-sample", "--train-num", 1, "--test-num", 0,
            "--min-dot-num", 4, "--max-dot-num", 6, "--ratios", "easy",
            "--seed", 11]


class TestConvexHull:
    """The area extended, which Gebuis & Reynvoet take as the hull of the dots."""

    def test_discs_at_square_corners_match_the_minkowski_sum(self):
        """Equal discs at the corners of a square: hull = square, grown by r."""
        side, r = 100.0, 20.0
        got = disc_hull_area([(0, 0, r), (side, 0, r), (0, side, r), (side, side, r)])
        expected = side ** 2 + 4 * side * r + math.pi * r ** 2
        assert got == pytest.approx(expected, rel=1e-3)

    def test_a_single_dot_extends_only_over_itself(self):
        """One dot's area extended is the dot, which is the root of the confound."""
        assert disc_hull_area([(50, 50, 25)]) == pytest.approx(math.pi * 25 ** 2, rel=2e-3)

    def test_collinear_points_span_no_area(self):
        assert convex_hull_area([(0, 0), (1, 1), (2, 2)]) == 0.0

    def test_interior_points_do_not_change_the_hull(self):
        assert convex_hull_area([(0, 0), (4, 0), (0, 3), (1, 1)]) == pytest.approx(6.0)


class TestArrayProperties:
    """The five properties of one array, and how an image splits into arrays."""

    def test_properties_of_known_discs(self):
        props = group_properties([(100, 100, 10), (200, 100, 20)])

        assert props["n_dots"] == 2
        assert props["total_surface_px"] == pytest.approx(math.pi * (100 + 400))
        assert props["mean_diameter_px"] == pytest.approx(30)
        assert props["total_circumference_px"] == pytest.approx(2 * math.pi * 30)
        assert props["density"] == pytest.approx(
            props["convex_hull_px"] / props["total_surface_px"]
        )

    def test_an_image_is_split_by_dot_colour(self):
        """Each colour of an ANS image is its own array; other elements are not dots."""
        scene = Scene(300, 300, "#000000")
        scene.add(DrawnElement(ELLIPSE, ((90, 90), (110, 110)), "#fffe04", "dot"))
        scene.add(DrawnElement(ELLIPSE, ((190, 90), (210, 110)), "#fffe04", "dot"))
        scene.add(DrawnElement(ELLIPSE, ((90, 190), (130, 230)), "#0003f9", "dot"))
        scene.add(DrawnElement(ELLIPSE, ((0, 0), (10, 10)), "#ffffff", "fixation_dot"))

        records = image_property_records("img.png", scene)
        by_colour = {record["colour"]: record for record in records}

        assert set(by_colour) == {"#fffe04", "#0003f9"}
        assert by_colour["#fffe04"]["n_dots"] == 2
        assert by_colour["#fffe04"]["mean_diameter_px"] == pytest.approx(20)
        assert by_colour["#0003f9"]["n_dots"] == 1
        assert by_colour["#0003f9"]["total_surface_px"] == pytest.approx(math.pi * 400)
        assert all(set(record) == set(PROPERTY_FIELDS) for record in records)


class TestPairComparison:
    """Differences within a pair, signed so that positive means congruent."""

    @staticmethod
    def _record(image, colour, n, surface, hull):
        return {
            "image": image, "colour": colour, "n_dots": n,
            "total_surface_px": surface, "mean_diameter_px": 10.0,
            "total_circumference_px": 10.0, "convex_hull_px": hull,
            "density": hull / surface,
        }

    def test_differences_are_taken_from_the_more_numerous_array(self):
        records = [
            self._record("a.png", "#fffe04", 2, 100.0, 1000.0),
            self._record("a.png", "#0003f9", 5, 150.0, 800.0),
        ]
        [row] = pair_property_records(
            records, [(("a.png", "#fffe04"), ("a.png", "#0003f9"))]
        )

        # The sides keep the paradigm's order; only the comparison is reoriented.
        assert (row["n_1"], row["n_2"]) == (2, 5)
        assert row["numerical_distance"] == 3
        assert row["numerical_ratio"] == pytest.approx(0.4)
        assert row["weber_fraction"] == pytest.approx(0.6)
        # More dots, more surface: congruent, so positive.
        assert row["total_surface_px_diff"] == pytest.approx(50)
        # More dots, smaller hull: incongruent, so negative.
        assert row["convex_hull_px_diff"] == pytest.approx(-200)
        assert row["convex_hull_px_ratio"] == pytest.approx(0.8)
        assert set(row) == set(PAIR_FIELDS)

    def test_equal_counts_keep_side_one_first(self):
        records = [
            self._record("s.png", "#000000", 4, 100.0, 500.0),
            self._record("m.png", "#000000", 4, 120.0, 500.0),
        ]
        [row] = pair_property_records(
            records, [(("s.png", "#000000"), ("m.png", "#000000"))]
        )
        assert row["weber_fraction"] == 0
        assert row["total_surface_px_diff"] == pytest.approx(-20)

    def test_a_side_without_dots_yields_no_pair(self):
        records = [self._record("a.png", "#fffe04", 2, 100.0, 1000.0)]
        pairs = [(("a.png", "#fffe04"), ("a.png", "#0003f9"))]
        assert pair_property_records(records, pairs) == []


class TestExportDescribesTheImages:
    """The files must describe what was written, not what was planned."""

    def test_total_surface_agrees_with_the_painted_pixels(self, tmp_path):
        """Summed dot area must match the pixels on disk, within rasterisation.

        Pillow paints a dot of radius r about (r + 0.5) wide, so the painted
        area runs a few percent above pi * r^2; anything beyond that would mean
        the export describes different dots from the ones drawn.
        """
        run_cli("one-colour", "--train-num", 1, "--min-dot-num", 5, "--max-dot-num", 5,
                "--seed", 7, "--background-colour", "black", "--visual-properties",
                "--output-dir", tmp_path)

        rows = read_csv(tmp_path / "visual_properties.csv")
        assert rows
        for row in rows:
            with Image.open(tmp_path / row["image"]) as img:
                pixels = np.asarray(img.convert("RGB"))
            painted = int(np.count_nonzero(np.any(pixels != 0, axis=-1)))
            assert float(row["total_surface_px"]) == pytest.approx(painted, rel=0.1), (
                f"{row['image']}: export says {row['total_surface_px']} px but "
                f"{painted} px are painted"
            )

    def test_ans_pairs_are_the_two_colours_of_each_image(self, tmp_path):
        run_cli(*ANS_ARGS, "--visual-properties", "--output-dir", tmp_path)

        properties = read_csv(tmp_path / "visual_properties.csv")
        pairs = read_csv(tmp_path / "visual_property_pairs.csv")
        images = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*.png"))

        assert sorted({row["image"] for row in properties}) == images
        assert len(properties) == 2 * len(images)
        assert len(pairs) == len(images)
        for row in pairs:
            assert row["image_1"] == row["image_2"]
            assert row["colour_1"] != row["colour_2"]
            # img_{n1}_{n2}_{rep}[...].png
            n1, n2 = (int(part) for part in Path(row["image_1"]).name.split("_")[1:3])
            assert (int(row["n_1"]), int(row["n_2"])) == (n1, n2)

    def test_equalized_ans_images_report_matched_surfaces(self, tmp_path):
        """The export must reflect the equalization the filename claims."""
        run_cli(*ANS_ARGS, "--visual-properties", "--output-dir", tmp_path)

        pairs = read_csv(tmp_path / "visual_property_pairs.csv")
        equalized = [row for row in pairs if "_equalized" in row["image_1"]]
        random_sizes = [row for row in pairs if "_equalized" not in row["image_1"]]
        assert equalized and random_sizes

        for row in equalized:
            assert float(row["total_surface_px_ratio"]) == pytest.approx(1, abs=0.01)
        # With random sizes, more dots means more surface: the cue is congruent.
        assert all(float(row["total_surface_px_diff"]) > 0 for row in random_sizes)

    def test_mts_pairs_link_the_sample_and_match_of_each_trial(self, tmp_path):
        run_cli(*MTS_ARGS, "--visual-properties", "--output-dir", tmp_path)

        pairs = read_csv(tmp_path / "visual_property_pairs.csv")
        images = list(tmp_path.rglob("*.png"))
        assert len(pairs) == len(images) // 2

        for row in pairs:
            # mts_{trial}_{r|e}_{a|b}_{n}: sample is b, match is a.
            sample = Path(row["image_1"]).stem.split("_")
            match = Path(row["image_2"]).stem.split("_")
            assert sample[1] == match[1], "a pair must come from one trial"
            assert (sample[3], match[3]) == ("b", "a")
            assert (int(row["n_1"]), int(row["n_2"])) == (int(sample[4]), int(match[4]))

    def test_one_colour_has_arrays_but_no_pairs(self, tmp_path):
        run_cli("one-colour", "--train-num", 1, "--min-dot-num", 4, "--max-dot-num", 5,
                "--seed", 11, "--visual-properties", "--output-dir", tmp_path)
        assert (tmp_path / "visual_properties.csv").exists()
        assert not (tmp_path / "visual_property_pairs.csv").exists()

    def test_svg_output_is_described_too(self, tmp_path):
        run_cli(*ANS_ARGS, "--img-format", "svg", "--visual-properties",
                "--output-dir", tmp_path)
        rows = read_csv(tmp_path / "visual_properties.csv")
        assert rows and all(row["image"].endswith(".svg") for row in rows)

    def test_nothing_written_by_default(self, tmp_path):
        """The export is opt-in, so existing workflows are unaffected."""
        run_cli(*ANS_ARGS, "--output-dir", tmp_path)
        assert not (tmp_path / "visual_properties.csv").exists()
        assert not (tmp_path / "visual_property_pairs.csv").exists()


class TestSmallNumerosityWarning:
    """Pairs below 4 dots are warned about, since their hull cannot be controlled."""

    @staticmethod
    def _ans_plan(min_n, max_n):
        plan = GenerationPlan(task_type="ans", min_point_num=min_n, max_point_num=max_n,
                              num_repeats=1, ratios=[1 / 2, 2 / 3])
        plan.build()
        return plan

    def test_pairs_below_the_threshold_are_listed_once_each(self):
        pairs = self._ans_plan(1, 6).small_numerosity_pairs()

        assert pairs
        assert all(smaller < SMALL_NUMEROSITY for smaller, _ in pairs)
        assert len(pairs) == len(set(pairs)), "both colour orders must collapse to one pair"
        assert (1, 2) in pairs and (3, 6) in pairs
        assert (4, 6) not in pairs

    def test_no_warning_once_every_array_has_enough_dots(self):
        assert small_numerosity_warning(self._ans_plan(SMALL_NUMEROSITY, 8)) is None

    def test_single_arrays_are_not_pairs(self):
        plan = GenerationPlan(task_type="one_colour", min_point_num=1, max_point_num=3,
                              num_repeats=1, ratios=[])
        plan.build()
        assert plan.small_numerosity_pairs() == []

    def test_matching_pairs_have_no_distance_to_confound(self, tmp_path):
        """A 2-vs-2 match trial compares nothing numerically."""
        tasks = tmp_path / "tasks.csv"
        tasks.write_text("sample,match,equalized\n2,2,FALSE\n2,3,FALSE\n", encoding="utf-8")
        plan = GenerationPlan(task_type="mts", min_point_num=1, max_point_num=3,
                              num_repeats=1, ratios=[])
        plan.build_from_mts_csv(tasks, num_copies=1)

        assert plan.small_numerosity_pairs() == [(2, 3)]

    @pytest.mark.parametrize("task", ["ans", "match-to-sample"])
    def test_cli_warns_when_planning_small_pairs(self, tmp_path, task):
        """The warning shows in a dry run, which is when options get chosen."""
        result = run_cli(task, "--train-num", 1, "--min-dot-num", 1, "--max-dot-num", 4,
                         "--ratios", "easy", "--dry-run", "--output-dir", tmp_path)
        assert "fewer than 4 dots" in result.stderr
        assert "--min-dot-num 4" in result.stderr

    @pytest.mark.parametrize("task", ["ans", "match-to-sample"])
    def test_cli_is_silent_from_four_dots_up(self, tmp_path, task):
        result = run_cli(task, "--train-num", 1, "--min-dot-num", 4, "--max-dot-num", 8,
                         "--ratios", "easy", "--dry-run", "--output-dir", tmp_path)
        assert "fewer than 4 dots" not in result.stderr
