
from cogstim.helpers.dots_core import DotsCore, PointLayoutError
from cogstim.helpers import hull_control


def equalize_pair(
    s_np: DotsCore,
    s_points,
    m_np: DotsCore,
    m_points,
    rel_tolerance: float,
    abs_tolerance: float,
    attempts_limit: int,
):
    """
    Try to equalize total areas using precise scaling when possible.
    Fallback to incremental increase if scaling fails.
    Returns (success, s_points_out, m_points_out).
    """
    area_s = s_np.compute_area(s_points, "colour_1")
    area_m = m_np.compute_area(m_points, "colour_1")

    # If already within tolerance
    diff = abs(area_s - area_m)
    denom = max(area_s, area_m, 1)
    if diff <= abs_tolerance or diff <= rel_tolerance * denom:
        return True, s_points, m_points

    # Identify smaller set, attempt scaling
    try:
        if area_s < area_m:
            target_area = area_m
            s_points = s_np.scale_total_area(s_points, target_area)
        else:
            target_area = area_s
            m_points = m_np.scale_total_area(m_points, target_area)
        # Re-check tolerance
        area_s = s_np.compute_area(s_points, "colour_1")
        area_m = m_np.compute_area(m_points, "colour_1")
        diff = abs(area_s - area_m)
        denom = max(area_s, area_m, 1)
        if diff <= abs_tolerance or diff <= rel_tolerance * denom:
            return True, s_points, m_points
    except PointLayoutError:
        pass

    # Fallback: incremental increase by +1 px to the smaller set using NumberPoints helpers
    iterations = 0
    while True:
        diff = abs(area_s - area_m)
        denom = max(area_s, area_m, 1)
        if diff <= abs_tolerance or diff <= rel_tolerance * denom:
            return True, s_points, m_points

        if area_s < area_m:
            candidate = s_np.increase_all_radii(s_points, 1)
            if not s_np.validate_layout(candidate):
                return False, s_points, m_points
            s_points = candidate
        else:
            candidate = m_np.increase_all_radii(m_points, 1)
            if not m_np.validate_layout(candidate):
                return False, s_points, m_points
            m_points = candidate

        area_s = s_np.compute_area(s_points, "colour_1")
        area_m = m_np.compute_area(m_points, "colour_1")
        iterations += 1
        if iterations >= attempts_limit:
            return False, s_points, m_points


def set_pair_area_ratio(
    s_np: DotsCore,
    s_points,
    m_np: DotsCore,
    m_points,
    target_ratio: float,
):
    """Rescale sample and match so that area(sample) / area(match) == target_ratio.

    This is the inverse surface condition for a pair of images. The change is
    shared between the two images as DotsCore.set_area_ratio shares it between
    two colours: the sample's radii are multiplied by the fourth root of the
    required change and the match's divided by it.

    Returns:
        (success, s_points_out, m_points_out); on failure the inputs come back
        unchanged, and the caller retries with a fresh layout.
    """
    area_s = s_np.compute_area(s_points, "colour_1")
    area_m = m_np.compute_area(m_points, "colour_1")
    if area_s == 0 or area_m == 0:
        return False, s_points, m_points

    change = target_ratio / (area_s / area_m)
    factor = change ** 0.25
    try:
        s_scaled = s_np.scale_by_factor(s_points, factor, round_radii=False)
        m_scaled = m_np.scale_by_factor(m_points, 1 / factor, round_radii=False)
    except PointLayoutError:
        return False, s_points, m_points
    return True, s_scaled, m_scaled


def expand_pair_hulls_to_ratio(
    s_np: DotsCore,
    s_points,
    m_np: DotsCore,
    m_points,
    target_ratio: float,
):
    """Spread sample and match dots so that hull(sample) / hull(match) == target_ratio.

    Each image is scaled outwards about its own centroid inside its canvas
    field, as DotsCore.expand_hulls_to_ratio does for the two colours of one
    image. Radii are untouched, so a surface condition applied first still
    holds. The image that must extend less is expected to have been placed in
    a reduced field, since spreading alone cannot make a hull smaller.

    Returns:
        (success, s_points_out, m_points_out); on failure the inputs come back
        unchanged, and the caller retries with a fresh layout.
    """
    moved = hull_control.expand_to_ratio(
        [p for p, _ in s_points], s_np.hull_fields()["colour_1"],
        [p for p, _ in m_points], m_np.hull_fields()["colour_1"],
        target_ratio,
    )
    if moved is None:
        return False, s_points, m_points
    s_out = [(disc, "colour_1") for disc in moved[0]]
    m_out = [(disc, "colour_1") for disc in moved[1]]
    if not s_np.validate_layout(s_out) or not m_np.validate_layout(m_out):
        return False, s_points, m_points
    return True, s_out, m_out
