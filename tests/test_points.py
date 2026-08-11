from cogstim.helpers.dots_core import DotsCore
from cogstim.helpers.constants import COLOUR_MAP


def _make_number_points(init_size: int = 512):
    return DotsCore(
        init_size=init_size,
        colour_1=COLOUR_MAP["yellow"],
        colour_2=COLOUR_MAP["blue"],
        bg_colour=COLOUR_MAP["black"],
        mode="RGB",
        min_point_radius=5,
        max_point_radius=8,
        attempts_limit=500,
    )


def test_design_points_no_overlap():
    """Created points should not overlap with each other."""
    generator = _make_number_points()
    points = generator.design_n_points(5, "colour_1")

    assert len(points) == 5

    # Verify no overlaps
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            assert generator._check_points_not_overlapping(points[i][0], points[j][0])


def test_equalize_areas():
    """equalize_areas() should make the yellow and blue point areas roughly equal."""
    generator = _make_number_points()
    # Manually craft two distant points to guarantee no overlaps during equalisation
    point_yellow = ((100, 100, 10), "colour_1")
    point_blue = ((400, 400, 30), "colour_2")
    point_array = [point_yellow, point_blue]

    equalized = generator.equalize_areas(point_array)

    yellow_area = generator.compute_area(equalized, "colour_1")
    blue_area = generator.compute_area(equalized, "colour_2")

    # Areas should now be (almost) equal
    rel_diff = abs(yellow_area - blue_area) / max(yellow_area, blue_area)
    assert rel_diff < generator.area_tolerance

    # Still no overlap
    assert generator._check_points_not_overlapping(equalized[0][0], equalized[1][0])


class TestRectangularPlacement:
    """Tests for _create_random_point_in_rect and region-constrained design_n_points."""

    def test_point_in_rect_stays_within_bounds(self):
        """All generated dots must fit entirely inside the given rectangle."""
        gen = _make_number_points()
        x_min, x_max, y_min, y_max = 50, 200, 30, 480

        for _ in range(200):
            x, y, r = gen._create_random_point_in_rect(x_min, x_max, y_min, y_max)
            assert x - r >= x_min, f"dot left edge {x - r} < x_min {x_min}"
            assert x + r <= x_max, f"dot right edge {x + r} > x_max {x_max}"
            assert y - r >= y_min, f"dot top edge {y - r} < y_min {y_min}"
            assert y + r <= y_max, f"dot bottom edge {y + r} > y_max {y_max}"

    def test_design_n_points_with_region_no_overlap(self):
        """Dots placed inside a region must not overlap each other."""
        gen = _make_number_points()
        region = (10, 250, 10, 500)
        points = gen.design_n_points(6, "colour_1", region=region)

        assert len(points) == 6
        for i in range(len(points)):
            for j in range(i + 1, len(points)):
                assert gen._check_points_not_overlapping(points[i][0], points[j][0])

    def test_design_n_points_with_region_respects_bounds(self):
        """Every dot placed with a region must fit inside that region."""
        gen = _make_number_points()
        region = (50, 200, 50, 460)
        points = gen.design_n_points(5, "colour_1", region=region)

        for pt, _ in points:
            x, y, r = pt
            assert x - r >= region[0]
            assert x + r <= region[1]
            assert y - r >= region[2]
            assert y + r <= region[3]

    def test_separated_colours_do_not_overlap(self):
        """Dots placed in non-overlapping left/right regions must not overlap."""
        gen = _make_number_points()
        left = (5, 220, 5, 507)
        right = (292, 507, 5, 507)

        points = gen.design_n_points(5, "colour_1", region=left)
        points = gen.design_n_points(5, "colour_2", point_array=points, region=right)

        assert len(points) == 10
        for i in range(len(points)):
            for j in range(i + 1, len(points)):
                assert gen._check_points_not_overlapping(points[i][0], points[j][0])

    def test_equalize_areas_after_separated_placement(self):
        """Area equalization must still work when dots are in separate halves."""
        gen = _make_number_points()
        # Hand-craft well-separated dots so equalization can grow radii safely
        points = [
            ((60, 100, 8), "colour_1"),
            ((60, 250, 8), "colour_1"),
            ((60, 400, 8), "colour_1"),
            ((400, 100, 20), "colour_2"),
            ((400, 300, 20), "colour_2"),
        ]

        equalized = gen.equalize_areas(points)

        area_1 = gen.compute_area(equalized, "colour_1")
        area_2 = gen.compute_area(equalized, "colour_2")
        rel_diff = abs(area_1 - area_2) / max(area_1, area_2)
        assert rel_diff < gen.area_tolerance
