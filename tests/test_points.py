from PIL import Image
from cogstim.dots_core import NumberPoints


def _make_number_points(init_size: int = 512):
    img = Image.new("RGB", (init_size, init_size), color="#000000")
    return NumberPoints(
        img=img,
        init_size=init_size,
        yellow="#fffe04",
        blue="#0003f9",
        min_point_radius=5,
        max_point_radius=8,
        attempts_limit=500,
    )


def test_design_points_no_overlap():
    """Created points should not overlap with each other."""
    generator = _make_number_points()
    points = generator.design_n_points(5, "yellow")

    assert len(points) == 5

    # Verify no overlaps
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            assert generator._check_points_not_overlapping(points[i][0], points[j][0])


def test_equalize_areas():
    """equalize_areas() should make the yellow and blue point areas roughly equal."""
    generator = _make_number_points()
    # Manually craft two distant points to guarantee no overlaps during equalisation
    point_yellow = ((100, 100, 10), "yellow")
    point_blue = ((400, 400, 30), "blue")
    point_array = [point_yellow, point_blue]

    equalized = generator.equalize_areas(point_array)

    yellow_area = generator.compute_area(equalized, "yellow")
    blue_area = generator.compute_area(equalized, "blue")

    # Areas should now be (almost) equal
    rel_diff = abs(yellow_area - blue_area) / max(yellow_area, blue_area)
    assert rel_diff < generator.area_tolerance

    # Still no overlap
    assert generator._check_points_not_overlapping(equalized[0][0], equalized[1][0])
