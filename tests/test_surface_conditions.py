"""Tests for the surface conditions of dot-array pairs: random, equal, inverse.

Gebuis & Reynvoet (2011) point out that a stimulus set in which a visual cue
only ever agrees with number, or says nothing, lets a participant answer from
the cue alone. With random dot sizes the total surface grows with the count,
and with equal surfaces it is uninformative; neither trial type contradicts
number. The inverse condition does: the array with fewer dots covers more
surface, by the factor the other has more dots, so that over the whole set
surface predicts nothing.

The generated files are the deliverable, so the central tests check them on
disk through the visual-properties export rather than through the code paths.
"""

import csv
import subprocess
import sys
from pathlib import Path

import pytest

from cogstim.helpers.constants import DEFAULT_SURFACE_CONDITIONS
from cogstim.helpers.dots_core import DotsCore, PointLayoutError
from cogstim.helpers.mts_geometry import set_pair_area_ratio
from cogstim.helpers.planner import GenerationPlan, load_mts_tasks_from_csv


def run_cli(*argv):
    """Invoke the CLI in a subprocess and return the completed process."""
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


class TestSetAreaRatio:
    """DotsCore.set_area_ratio, which implements the inverse condition in one image."""

    @staticmethod
    def _core():
        return DotsCore(init_size=512, colour_1="#fffe04", colour_2="#0003f9", bg_colour="white")

    def test_reaches_the_requested_ratio_exactly(self):
        core = self._core()
        points = [((100, 100, 20), "colour_1"),
                  ((400, 400, 20), "colour_2"), ((100, 400, 20), "colour_2")]

        scaled = core.set_area_ratio(points, 3.0)

        ratio = core.compute_area(scaled, "colour_1") / core.compute_area(scaled, "colour_2")
        assert ratio == pytest.approx(3.0)

    def test_change_is_shared_between_the_colours(self):
        """Colour 1 grows and colour 2 shrinks by the same factor."""
        core = self._core()
        points = [((100, 100, 20), "colour_1"), ((400, 400, 20), "colour_2")]

        # Equal areas, so the ratio must change fourfold: sqrt(2) on each radius.
        scaled = core.set_area_ratio(points, 4.0)

        r1, r2 = scaled[0][0][2], scaled[1][0][2]
        assert r1 == pytest.approx(20 * 2 ** 0.5)
        assert r2 == pytest.approx(20 / 2 ** 0.5)

    def test_a_ratio_of_one_equalizes(self):
        core = self._core()
        points = [((100, 100, 10), "colour_1"), ((400, 400, 30), "colour_2")]

        scaled = core.set_area_ratio(points, 1.0)

        assert core.compute_area(scaled, "colour_1") == pytest.approx(
            core.compute_area(scaled, "colour_2")
        )

    def test_growing_into_a_neighbour_is_a_layout_error(self):
        core = self._core()
        # 60 px apart: fine at radius 20, not once colour 1 doubles to 40.
        points = [((100, 100, 20), "colour_1"), ((160, 100, 20), "colour_2")]
        with pytest.raises(PointLayoutError):
            core.set_area_ratio(points, 16.0)

    def test_growing_past_the_edge_is_a_layout_error(self):
        core = self._core()
        points = [((30, 30, 20), "colour_1"), ((400, 400, 20), "colour_2")]
        with pytest.raises(PointLayoutError):
            core.set_area_ratio(points, 16.0)

    def test_a_colour_without_dots_is_a_layout_error(self):
        core = self._core()
        with pytest.raises(PointLayoutError):
            core.set_area_ratio([((100, 100, 20), "colour_1")], 2.0)


class TestSetPairAreaRatio:
    """The same condition across the two images of a match-to-sample trial."""

    def test_sample_and_match_reach_the_ratio(self):
        s_np, m_np = DotsCore(512, "#000000"), DotsCore(512, "#000000")
        s_points = [((100, 100, 10), "colour_1")]
        m_points = [((200, 200, 10), "colour_1"), ((400, 400, 10), "colour_1")]

        ok, s_out, m_out = set_pair_area_ratio(s_np, s_points, m_np, m_points, 2.0)

        assert ok
        ratio = s_np.compute_area(s_out, "colour_1") / m_np.compute_area(m_out, "colour_1")
        assert ratio == pytest.approx(2.0)

    def test_failure_returns_the_original_points(self):
        s_np, m_np = DotsCore(512, "#000000"), DotsCore(512, "#000000")
        s_points = [((12, 12, 10), "colour_1")]  # hugging the corner
        m_points = [((200, 200, 10), "colour_1")]

        ok, s_out, m_out = set_pair_area_ratio(s_np, s_points, m_np, m_points, 100.0)

        assert not ok
        assert (s_out, m_out) == (s_points, m_points)


class TestPlanning:
    """How the conditions multiply the tasks of a plan."""

    def test_default_conditions_are_random_and_equal(self):
        plan = GenerationPlan("ans", 2, 4, 1, ratios=[1 / 2]).build()

        assert set(DEFAULT_SURFACE_CONDITIONS) == {"random", "equal"}
        assert {task.params["surface"] for task in plan.tasks} == {"random", "equal"}
        assert len(plan.tasks) == 4, "one pair, two colour orders, two conditions"

    def test_each_condition_adds_both_colour_orders(self):
        plan = GenerationPlan("ans", 2, 4, 1, ratios=[1 / 2],
                              surface_conditions=["random", "equal", "inverse"]).build()

        assert len(plan.tasks) == 6
        inverse = [task for task in plan.tasks if task.params["surface"] == "inverse"]
        assert {(t.params["n1"], t.params["n2"]) for t in inverse} == {(2, 4), (4, 2)}

    def test_mts_keeps_match_and_non_match_balanced(self):
        plan = GenerationPlan("mts", 2, 4, 1, ratios=[1 / 2],
                              surface_conditions=["random", "equal", "inverse"]).build()

        assert len(plan.tasks) == 12
        matching = [task for task in plan.tasks if task.params["n1"] == task.params["n2"]]
        assert len(matching) == 6

    def test_mts_csv_refuses_the_old_equalized_column(self, tmp_path):
        tasks = tmp_path / "tasks.csv"
        tasks.write_text("sample,match,equalized\n3,4,TRUE\n", encoding="utf-8")
        with pytest.raises(ValueError, match="'equalized' column was replaced by 'surface'"):
            load_mts_tasks_from_csv(tasks)


ANS_ARGS = ["ans", "--train-num", 1, "--test-num", 0,
            "--min-dot-num", 4, "--max-dot-num", 8, "--ratios", "1/2,2/3",
            "--seed", 5, "--visual-properties"]


class TestGeneratedStimuli:
    """What lands on disk under each condition."""

    def test_inverse_surface_contradicts_number_by_the_mirrored_factor(self, tmp_path):
        """With 4 vs 8 dots, the 4 dots cover twice the surface of the 8."""
        run_cli_ok(*ANS_ARGS, "--surface", "inverse", "--output-dir", tmp_path)

        pairs = read_csv(tmp_path / "visual_property_pairs.csv")
        assert pairs and all("_inverse" in row["image_1"] for row in pairs)
        for row in pairs:
            assert float(row["total_surface_px_diff"]) < 0, row["image_1"]
            assert float(row["total_surface_px_ratio"]) == pytest.approx(
                float(row["numerical_ratio"]), rel=1e-2
            ), row["image_1"]

    def test_three_conditions_give_one_file_each_per_pair(self, tmp_path):
        run_cli_ok(*ANS_ARGS, "--surface", "random", "equal", "inverse",
                   "--output-dir", tmp_path)

        names = [path.name for path in tmp_path.rglob("*.png")]
        n_equal = sum("_equal" in name for name in names)
        n_inverse = sum("_inverse" in name for name in names)
        n_random = len(names) - n_equal - n_inverse
        assert n_random == n_equal == n_inverse > 0

    def test_default_is_half_random_half_equal(self, tmp_path):
        run_cli_ok(*ANS_ARGS, "--output-dir", tmp_path)

        names = [path.name for path in tmp_path.rglob("*.png")]
        assert not any("_inverse" in name for name in names)
        n_equal = sum("_equal" in name for name in names)
        assert n_equal == len(names) - n_equal > 0

    def test_mts_inverse_pairs(self, tmp_path):
        run_cli_ok("match-to-sample", "--train-num", 1, "--test-num", 0,
                   "--min-dot-num", 4, "--max-dot-num", 8, "--ratios", "1/2",
                   "--seed", 5, "--surface", "inverse", "--visual-properties",
                   "--output-dir", tmp_path)

        files = list(tmp_path.rglob("*.png"))
        assert files and all("_i_" in path.name for path in files)

        for row in read_csv(tmp_path / "visual_property_pairs.csv"):
            if row["n_1"] != row["n_2"]:
                assert float(row["total_surface_px_diff"]) < 0, row["image_1"]
                assert float(row["total_surface_px_ratio"]) == pytest.approx(
                    float(row["numerical_ratio"]), rel=1e-2
                ), row["image_1"]
            else:
                # Equal counts have no direction to invert, so surfaces match.
                assert float(row["total_surface_px_ratio"]) == pytest.approx(1, abs=1e-2)

    def test_csv_surface_column_selects_the_condition(self, tmp_path):
        tasks = tmp_path / "tasks.csv"
        tasks.write_text("n1,n2,surface\n4,8,inverse\n4,8,equal\n4,8,random\n",
                         encoding="utf-8")
        out = tmp_path / "out"

        run_cli_ok("ans", "--tasks-csv", tasks, "--train-num", 1, "--seed", 3,
                   "--output-dir", out)

        names = sorted(path.name for path in out.rglob("*.png"))
        assert names == ["img_4_8_0_inverse.png", "img_4_8_1_equal.png", "img_4_8_2.png"]

    def test_old_equalized_csv_is_refused_with_an_explanation(self, tmp_path):
        tasks = tmp_path / "tasks.csv"
        tasks.write_text("n1,n2,equalized\n3,5,TRUE\n", encoding="utf-8")

        result = run_cli("ans", "--tasks-csv", tasks, "--train-num", 1,
                         "--output-dir", tmp_path / "out")

        assert result.returncode != 0
        assert "'equalized' column was replaced by 'surface'" in result.stdout + result.stderr

    def test_unknown_condition_is_refused_by_the_parser(self, tmp_path):
        result = run_cli("ans", "--surface", "matched", "--output-dir", tmp_path)
        assert result.returncode != 0
        assert "invalid choice" in result.stderr
