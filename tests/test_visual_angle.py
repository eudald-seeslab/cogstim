"""Tests for sizes given in degrees of visual angle.

Psychophysics reports sizes as the angle they subtend at the eye, and a pixel
is only an angle once the viewing distance and the display's pixel density
are known. CogStim keeps pixels as its unit and converts at the edges: degree
options become pixels before anything is drawn, and the visual properties
export gains degree columns. The files on disk are what matters, so most
tests read sizes back from the images and exports.
"""

import csv
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

from cogstim.helpers.visual_angle import ViewingGeometry


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


# At 57.3 cm one degree spans one centimetre, the classic rule of thumb.
GEOMETRY = ["--viewing-distance-cm", 57.3, "--pixels-per-cm", 40]


class TestGeometry:

    def test_one_degree_is_one_centimetre_at_57_cm(self):
        geometry = ViewingGeometry(57.3, 40)
        assert geometry.px_per_deg == pytest.approx(40, rel=1e-3)

    def test_lengths_round_trip(self):
        geometry = ViewingGeometry(60, 35)
        for degrees in (0.2, 1, 5, 12):
            assert geometry.length_deg(geometry.length_px(degrees)) == pytest.approx(degrees)

    def test_a_radius_is_half_its_diameter(self):
        geometry = ViewingGeometry(57.3, 40)
        assert geometry.radius_px(0.3) == pytest.approx(geometry.length_px(0.6) / 2)
        assert geometry.radius_px(0.3) == pytest.approx(12, rel=1e-3)

    def test_areas_use_the_size_of_a_degree(self):
        geometry = ViewingGeometry(57.3, 40)
        assert geometry.area_deg2(geometry.px_per_deg ** 2) == pytest.approx(1)

    def test_half_a_geometry_is_refused(self):
        with pytest.raises(ValueError, match="both"):
            ViewingGeometry.from_config({"viewing_distance_cm": 57.3})
        assert ViewingGeometry.from_config({}) is None

    def test_sizes_must_be_positive(self):
        with pytest.raises(ValueError):
            ViewingGeometry(0, 40)


ANS_ARGS = ["ans", "--train-num", 1, "--test-num", 0, "--min-dot-num", 4,
            "--max-dot-num", 5, "--ratios", "4/5", "--surface", "random", "--seed", 3]


class TestSizesInDegrees:

    def test_dot_radius_in_degrees_sets_the_drawn_radius(self, tmp_path):
        """0.3 degrees at 57.3 cm and 40 px/cm is a 12 px radius."""
        run_cli_ok(*ANS_ARGS, *GEOMETRY, "--min-dot-radius-deg", 0.3, "--max-dot-radius-deg", 0.3,
                   "--metadata", "csv", "--output-dir", tmp_path)

        rows = read_csv(tmp_path / "annotations.csv")
        assert rows and all(float(row["radius"]) == 12 for row in rows)

    def test_image_size_in_degrees_sets_the_canvas(self, tmp_path):
        """10 degrees at 57.3 cm and 40 px/cm is 401 px across."""
        run_cli_ok(*ANS_ARGS, *GEOMETRY, "--img-size-deg", 10, "--output-dir", tmp_path)

        for path in tmp_path.rglob("*.png"):
            with Image.open(path) as img:
                assert img.size == (401, 401)

    def test_degrees_need_the_geometry(self, tmp_path):
        result = run_cli(*ANS_ARGS, "--min-dot-radius-deg", 0.3, "--output-dir", tmp_path)
        assert result.returncode == 2
        assert "--viewing-distance-cm and --pixels-per-cm" in result.stderr

    def test_half_a_geometry_is_refused_by_the_cli(self, tmp_path):
        result = run_cli(*ANS_ARGS, "--viewing-distance-cm", 57.3, "--output-dir", tmp_path)
        assert result.returncode == 2
        assert "both" in result.stderr

    def test_export_reports_degrees_alongside_pixels(self, tmp_path):
        run_cli_ok(*ANS_ARGS, *GEOMETRY, "--visual-properties", "--output-dir", tmp_path)

        geometry = ViewingGeometry(57.3, 40)
        rows = read_csv(tmp_path / "visual_properties.csv")
        assert rows
        for row in rows:
            assert float(row["mean_diameter_deg"]) == pytest.approx(
                geometry.length_deg(float(row["mean_diameter_px"])), abs=2e-3
            )
            assert float(row["convex_hull_deg2"]) == pytest.approx(
                geometry.area_deg2(float(row["convex_hull_px"])), rel=1e-2
            )

    def test_export_stays_in_pixels_without_a_geometry(self, tmp_path):
        run_cli_ok(*ANS_ARGS, "--visual-properties", "--output-dir", tmp_path)
        rows = read_csv(tmp_path / "visual_properties.csv")
        assert rows and "mean_diameter_deg" not in rows[0]

    def test_run_summary_states_the_geometry(self, tmp_path):
        result = run_cli_ok(*ANS_ARGS, *GEOMETRY, "--output-dir", tmp_path)
        assert "1° of visual angle = 40.0 px" in result.stdout
        assert "the image spans" in result.stdout

    def test_match_to_sample_takes_degrees_too(self, tmp_path):
        run_cli_ok("match-to-sample", "--train-num", 1, "--test-num", 0, "--min-dot-num", 4,
                   "--max-dot-num", 5, "--ratios", "4/5", "--surface", "random", "--seed", 3,
                   *GEOMETRY, "--min-dot-radius-deg", 0.2, "--max-dot-radius-deg", 0.2,
                   "--metadata", "csv", "--output-dir", tmp_path)
        rows = read_csv(tmp_path / "annotations.csv")
        assert rows and all(float(row["radius"]) == 8 for row in rows)

    def test_replay_keeps_the_degrees(self, tmp_path):
        """The recorded configuration carries the degree options, so a replay converts them again."""
        first = tmp_path / "first"
        run_cli_ok(*ANS_ARGS, *GEOMETRY, "--min-dot-radius-deg", 0.3, "--max-dot-radius-deg", 0.3,
                   "--metadata", "csv", "--output-dir", first)
        replay = tmp_path / "replay"
        run_cli_ok("run", first / "cogstim_config.yaml", "--output-dir", replay)

        rows = read_csv(replay / "annotations.csv")
        assert rows and all(float(row["radius"]) == 12 for row in rows)


class TestImageSizeIsHonoured:
    """`--img-size` is documented for every task, but ans drew 512 px regardless."""

    @pytest.mark.parametrize("task, extra", [("ans", ["--ratios", "2/3"]), ("one-colour", [])])
    def test_dot_tasks_draw_the_requested_size(self, tmp_path, task, extra):
        run_cli_ok(task, "--train-num", 1, "--test-num", 0, "--min-dot-num", 2,
                   "--max-dot-num", 3, *extra, "--img-size", 256,
                   "--seed", 3, "--output-dir", tmp_path)
        files = list(tmp_path.rglob("*.png"))
        assert files
        for path in files:
            with Image.open(path) as img:
                assert img.size == (256, 256)
