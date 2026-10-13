"""Tests for the hull conditions: the area a dot array extends over.

When dots are placed at random, the array with more dots usually extends
over a larger area, so "which patch is bigger" answers a numerosity task
without counting. Gebuis & Reynvoet (2011) vary the field each array is
placed in; CogStim sets the convex hull itself: the array that must extend
less is placed in a smaller field, then each array is spread about its
centroid, leaving radii, and so the surface condition, untouched.

The generated files are the deliverable, so the central tests read the hulls
back from the visual-properties export rather than from the code paths.
"""

import csv
import math
import subprocess
import sys
from pathlib import Path

import pytest

from cogstim.helpers.dots_core import DotsCore, PointLayoutError
from cogstim.helpers.hull_control import (
    CircleField,
    RectField,
    centroid,
    expansion_targets,
    max_hull_bound,
    max_scale,
    placement_radius,
    reduced_field_radius,
    scale_for_hull,
    unreachable_hull_pairs,
)
from cogstim.helpers.mts_geometry import expand_pair_hulls_to_ratio
from cogstim.helpers.planner import GenerationPlan, load_ans_tasks_from_csv
from cogstim.helpers.visual_properties import disc_hull_area


def run_cli(*argv):
    return subprocess.run(
        [sys.executable, "-m", "cogstim.cli", *map(str, argv)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )


def run_cli_ok(*argv):
    result = run_cli(*argv)
    assert result.returncode == 0, f"CLI failed:\n{result.stdout}\n{result.stderr}"
    return result


def read_csv(path):
    return list(csv.DictReader(Path(path).open(encoding="utf-8")))


FIELD = CircleField((256, 256), 241)


class TestSpreading:
    """Moving an array outwards about its centroid inside its field."""

    def test_spreading_stops_at_the_field_edge(self):
        """A dot 100 px from the centre can move out until it touches the field."""
        discs = [(356, 256, 20), (156, 256, 20)]  # symmetric, centroid at the centre
        assert max_scale(discs, centroid(discs), FIELD) == pytest.approx((241 - 20) / 100)

    def test_rect_field_bounds_each_axis(self):
        field = RectField(0, 400, 0, 400, margin=10)
        discs = [(100, 200, 20), (300, 200, 20)]  # centroid (200, 200), 100 px apart
        # The right dot reaches x = 400 - 20 - 10 = 370 at scale 1.7.
        assert max_scale(discs, centroid(discs), field) == pytest.approx(1.7)

    def test_a_single_dot_has_no_extent_to_scale(self):
        assert max_scale([(256, 256, 20)], (256, 256), FIELD) == 1

    def test_bisection_reaches_the_target_hull(self):
        discs = [(200, 200, 20), (300, 200, 20), (250, 300, 20)]
        about = centroid(discs)
        high = max_scale(discs, about, FIELD)
        target = 30000
        factor = scale_for_hull(discs, about, target, 1.0, high)
        moved = [(about[0] + factor * (x - about[0]), about[1] + factor * (y - about[1]), r)
                 for x, y, r in discs]
        assert disc_hull_area(moved) == pytest.approx(target, rel=2e-3)
        assert [r for _, _, r in moved] == [20, 20, 20], "radii must not change"

    def test_targets_only_ever_spread(self):
        # Both hulls 100, ratio 4: b cannot shrink, so a grows fourfold.
        assert expansion_targets(100, 100, 4, 1000, 1000) == pytest.approx((400, 100))
        # a is the smaller one at ratio 1: a grows to b.
        assert expansion_targets(50, 100, 1, 1000, 1000) == pytest.approx((100, 100))
        # a cannot pass 300, and b cannot shrink to 75: unreachable.
        assert expansion_targets(100, 100, 4, 300, 1000) is None


class TestExpandHullsToRatio:
    """DotsCore.expand_hulls_to_ratio on hand-made layouts."""

    @staticmethod
    def _core():
        return DotsCore(init_size=512, colour_1="#fffe04", colour_2="#0003f9", bg_colour="white")

    @staticmethod
    def _hulls(moved):
        return {c: disc_hull_area([p for p, col in moved if col == c]) for c in ("colour_1", "colour_2")}

    def test_reaches_the_ratio_and_keeps_the_radii(self):
        """The narrower colour spreads out to match the wider one."""
        core = self._core()
        points = [((200, 200, 20), "colour_1"), ((300, 200, 20), "colour_1"), ((250, 300, 20), "colour_1"),
                  ((200, 250, 25), "colour_2"), ((300, 250, 25), "colour_2")]

        moved = core.expand_hulls_to_ratio(points, 1.0)

        hulls = self._hulls(moved)
        assert hulls["colour_1"] == pytest.approx(hulls["colour_2"], rel=2e-3)
        assert sorted(p[2] for p, _ in moved) == [20, 20, 20, 25, 25]
        assert core.validate_layout(moved)

    def test_a_clustered_colour_spreads_to_half_the_other(self):
        core = self._core()
        points = [((120, 120, 20), "colour_1"), ((392, 120, 20), "colour_1"), ((256, 392, 20), "colour_1"),
                  ((230, 230, 20), "colour_2"), ((282, 230, 20), "colour_2"),
                  ((230, 282, 20), "colour_2"), ((282, 282, 20), "colour_2")]

        moved = core.expand_hulls_to_ratio(points, 2.0)

        hulls = self._hulls(moved)
        assert hulls["colour_1"] / hulls["colour_2"] == pytest.approx(2.0, rel=2e-3)
        # Spreading only: no dot moved towards its colour's centroid.
        assert hulls["colour_2"] > disc_hull_area([p for p, c in points if c == "colour_2"])

    def test_a_single_dot_cannot_be_given_a_larger_hull(self):
        core = self._core()
        points = [((256, 256, 20), "colour_1"),
                  ((100, 100, 20), "colour_2"), ((400, 100, 20), "colour_2"), ((250, 400, 20), "colour_2")]
        with pytest.raises(PointLayoutError):
            core.expand_hulls_to_ratio(points, 3.0)

    def test_pair_of_images(self):
        s_np, m_np = DotsCore(512, "#000000"), DotsCore(512, "#000000")
        s_points = [((206, 256, 10), "colour_1"), ((306, 256, 10), "colour_1")]
        m_points = [((240, 240, 10), "colour_1"), ((272, 240, 10), "colour_1"),
                    ((240, 272, 10), "colour_1"), ((272, 272, 10), "colour_1")]

        ok, s_out, m_out = expand_pair_hulls_to_ratio(s_np, s_points, m_np, m_points, 2.0)

        assert ok
        ratio = disc_hull_area([p for p, _ in s_out]) / disc_hull_area([p for p, _ in m_out])
        assert ratio == pytest.approx(2.0, rel=2e-3)


class TestBounds:
    """What a plan can be refused on."""

    def test_one_dot_extends_only_over_itself(self):
        assert max_hull_bound(1, 20, 30, 241) == pytest.approx(math.pi * 30 ** 2)

    def test_bounds_grow_with_the_count(self):
        maxima = [max_hull_bound(n, 20, 30, 241) for n in range(1, 8)]
        needed = [placement_radius(n, 20, 30, 10) for n in range(1, 8)]
        assert maxima == sorted(maxima) and needed == sorted(needed)

    def test_a_wider_ratio_needs_a_smaller_field(self):
        assert reduced_field_radius(4, 2, 20, 30, 241) < reduced_field_radius(4, 1, 20, 30, 241)
        assert reduced_field_radius(4, 1, 20, 30, 241) <= 241

    def test_small_counts_with_wide_ratios_are_unreachable(self):
        plan = GenerationPlan("ans", 1, 8, 1, ratios=[1 / 2], hull_conditions=["inverse"]).build()
        unreachable = {(f, m) for f, m, _, _, _ in unreachable_hull_pairs(plan.tasks, 8, 12, 241, 10)}
        assert (1, 2) in unreachable
        assert (4, 8) not in unreachable

    def test_large_dots_leave_no_room(self):
        """The default 20-30 px dots cannot invert even 4 vs 8 on a 512 px canvas."""
        plan = GenerationPlan("ans", 4, 8, 1, ratios=[1 / 2], hull_conditions=["inverse"]).build()
        assert {(f, m) for f, m, *_ in unreachable_hull_pairs(plan.tasks, 20, 30, 241, 10)} == {(4, 8)}

    def test_random_hull_is_never_refused(self):
        plan = GenerationPlan("ans", 1, 8, 1, ratios=[1 / 2]).build()
        assert unreachable_hull_pairs(plan.tasks, 20, 30, 241, 10) == []


class TestPlanning:
    def test_hull_multiplies_the_surface_conditions(self):
        plan = GenerationPlan("ans", 2, 4, 1, ratios=[1 / 2],
                              hull_conditions=["random", "equal", "inverse"]).build()
        assert len(plan.tasks) == 2 * 3 * 2  # orders x hull x default surface conditions
        assert {t.params["hull"] for t in plan.tasks} == {"random", "equal", "inverse"}

    def test_default_hull_is_random(self):
        plan = GenerationPlan("ans", 2, 4, 1, ratios=[1 / 2]).build()
        assert {t.params["hull"] for t in plan.tasks} == {"random"}

    def test_csv_hull_column(self, tmp_path):
        tasks = tmp_path / "tasks.csv"
        tasks.write_text("n1,n2,surface,hull\n4,8,equal,Inverse\n4,8,random,\n", encoding="utf-8")
        assert load_ans_tasks_from_csv(tasks) == [(4, 8, "equal", "inverse"), (4, 8, "random", "random")]

    def test_unknown_hull_is_refused(self, tmp_path):
        tasks = tmp_path / "tasks.csv"
        tasks.write_text("n1,n2,hull\n4,8,wide\n", encoding="utf-8")
        with pytest.raises(ValueError, match="hull must be one of"):
            load_ans_tasks_from_csv(tasks)


# Hull conditions need dots small enough to leave room: the default 20-30 px
# radius on a 512 px canvas only allows ratios close to 1.
ANS_ARGS = ["ans", "--train-num", 1, "--test-num", 0,
            "--min-dot-num", 4, "--max-dot-num", 8, "--ratios", "1/2,2/3",
            "--min-dot-radius-px", 8, "--max-dot-radius-px", 12,
            "--seed", 5, "--visual-properties"]


class TestGeneratedStimuli:

    def test_inverse_hull_contradicts_number_by_the_mirrored_factor(self, tmp_path):
        run_cli_ok(*ANS_ARGS, "--hull", "inverse", "--output-dir", tmp_path)

        pairs = read_csv(tmp_path / "visual_property_pairs.csv")
        assert pairs and all("_hull_inverse" in row["image_1"] for row in pairs)
        for row in pairs:
            assert float(row["convex_hull_px_diff"]) < 0, row["image_1"]
            assert float(row["convex_hull_px_ratio"]) == pytest.approx(
                float(row["numerical_ratio"]), rel=1e-2
            ), row["image_1"]

    def test_equal_hull_matches_the_hulls(self, tmp_path):
        run_cli_ok(*ANS_ARGS, "--hull", "equal", "--output-dir", tmp_path)

        pairs = read_csv(tmp_path / "visual_property_pairs.csv")
        assert pairs and all("_hull_equal" in row["image_1"] for row in pairs)
        for row in pairs:
            assert float(row["convex_hull_px_ratio"]) == pytest.approx(1, abs=1e-2), row["image_1"]

    def test_hull_and_surface_conditions_hold_together(self, tmp_path):
        """Moving dots does not change their size, so both conditions are exact."""
        run_cli_ok(*ANS_ARGS, "--surface", "equal", "--hull", "inverse", "--output-dir", tmp_path)

        for row in read_csv(tmp_path / "visual_property_pairs.csv"):
            assert "_equal_hull_inverse" in row["image_1"]
            assert float(row["total_surface_px_ratio"]) == pytest.approx(1, abs=1e-2)
            assert float(row["convex_hull_px_ratio"]) == pytest.approx(
                float(row["numerical_ratio"]), rel=1e-2
            )

    def test_separated_layout_keeps_each_colour_in_its_half(self, tmp_path):
        """The halves are small, so this needs smaller dots than the default."""
        run_cli_ok("ans", "--train-num", 1, "--test-num", 0, "--min-dot-num", 4,
                   "--max-dot-num", 6, "--ratios", "2/3", "--seed", 5,
                   "--min-dot-radius-px", 5, "--max-dot-radius-px", 8,
                   "--layout", "separated", "--hull", "inverse",
                   "--metadata", "csv", "--visual-properties", "--output-dir", tmp_path)

        for row in read_csv(tmp_path / "annotations.csv"):
            if row["colour"] == "#fffe04":
                assert float(row["bbox_x_max"]) <= 256, row["image"]
            else:
                assert float(row["bbox_x_min"]) >= 256, row["image"]
        for row in read_csv(tmp_path / "visual_property_pairs.csv"):
            assert float(row["convex_hull_px_ratio"]) == pytest.approx(
                float(row["numerical_ratio"]), rel=1e-2
            ), row["image_1"]

    def test_mts_inverse_hull(self, tmp_path):
        run_cli_ok("match-to-sample", "--train-num", 1, "--test-num", 0,
                   "--min-dot-num", 4, "--max-dot-num", 8, "--ratios", "1/2",
                   "--min-dot-radius-px", 8, "--max-dot-radius-px", 12,
                   "--seed", 5, "--surface", "random", "--hull", "inverse",
                   "--visual-properties", "--output-dir", tmp_path)

        files = list(tmp_path.rglob("*.png"))
        assert files and all("_ri_" in path.name for path in files)
        for row in read_csv(tmp_path / "visual_property_pairs.csv"):
            expected = float(row["numerical_ratio"]) if row["n_1"] != row["n_2"] else 1.0
            assert float(row["convex_hull_px_ratio"]) == pytest.approx(expected, rel=1e-2), row["image_1"]

    def test_default_output_carries_no_hull_suffix(self, tmp_path):
        run_cli_ok(*ANS_ARGS, "--output-dir", tmp_path)
        assert not any("_hull_" in path.name for path in tmp_path.rglob("*.png"))

    def test_unreachable_pairs_are_refused_when_planning(self, tmp_path):
        """A dry run is enough to learn that 1 vs 2 cannot invert its hull."""
        result = run_cli("ans", "--train-num", 1, "--min-dot-num", 1, "--max-dot-num", 4,
                         "--ratios", "1/2", "--hull", "inverse", "--dry-run",
                         "--output-dir", tmp_path)
        assert result.returncode == 2
        assert "cannot meet their hull condition" in result.stderr
        assert "1 vs 2" in result.stderr
        assert not list(tmp_path.rglob("*.png"))
