#!/usr/bin/env python3
"""Control of the area a dot array extends over.

The convex hull of an array grows with its number of dots when the dots are
placed at random: more dots are more likely to reach the edges of the field.
In CogStim's output the array with more dots had the larger hull in about
seven pairs out of ten, whatever the surface condition, so "which patch is
bigger" answered the task without counting. Gebuis & Reynvoet (2011) handle
this by varying the field each array is placed in; here the hull itself is
set, so that a pair can be given equal hulls, or a hull ratio that contradicts
the numerical ratio.

Two moves do it. The array that must extend less is placed inside a smaller
field to begin with; shrinking an already placed array by pulling its dots
together stops at the first two that touch, which with ordinary dot sizes is
almost at once. Then each array is spread out, its centres scaled about its
centroid, until the two hulls stand in the required ratio. Spreading never
makes dots overlap, and no radius changes, so a surface condition applied to
the same image still holds exactly. Dots stay inside the field they were
placed in, so no layout appears that random placement could not have produced.

Not every pair can meet a hull condition: one dot extends over nothing but
itself, and n dots cannot be placed inside a field below a certain size. The
bounds here size the smaller field and let a plan be refused before anything
is drawn, naming the pairs.
"""

import math
from dataclasses import dataclass
from typing import List, Sequence, Tuple

from cogstim.helpers.visual_properties import disc_hull_area

# Fraction of a field's area that random placement can fill with dots before
# it starts failing. Random sequential placement of equal discs jams at about
# 55% in an unbounded plane; the edge of a small field lowers that.
PLACEMENT_DENSITY = 0.45

# The field the smaller array is placed in is sized from a bound on how far
# the other array can spread, reduced by this factor. A randomly placed array
# spreads much less than the bound before one of its dots reaches the edge:
# over random layouts of 3 to 8 dots, the median reached 0.3 to 0.5 of it, so
# a smaller field makes the other array's job easier. But when the two arrays
# share a field, a smaller field also means the clustered array must spread
# further, into the other, when the other's hull turns out large; measured
# over both regimes, 0.75 kept retries lowest while still refusing, at plan
# time, the pairs that never succeed.
FIELD_SAFETY = 0.75

# A hull counts as reached when within this fraction of its target.
HULL_TOLERANCE = 1e-3
MAX_BISECTIONS = 40

Disc = Tuple[float, float, float]


class UnreachableConditionError(ValueError):
    """A hull condition that no layout of the planned dots can meet.

    A ValueError so the command line reports it as a configuration problem,
    which is what it is: the remedy is a different dot count, ratio, dot size
    or image size, not another random draw.
    """


@dataclass(frozen=True)
class CircleField:
    """A circular field: every disc lies within ``radius`` of ``centre``."""

    centre: Tuple[float, float]
    radius: float

    def scale_bounds(self, disc: Disc, about: Tuple[float, float]) -> Tuple[float, float]:
        """Scale factors about ``about`` that keep this disc inside the field.

        Solving |e + s d|^2 <= (R - r)^2 for s, with d the disc's offset from
        the scaling centre and e that centre's offset from the field centre.
        A disc already outside its field (its radius may have grown since
        placement) is left unconstrained here; the canvas check at the end
        still applies.
        """
        x, y, r = disc
        dx, dy = x - about[0], y - about[1]
        ex, ey = about[0] - self.centre[0], about[1] - self.centre[1]
        a = dx * dx + dy * dy
        b = 2 * (ex * dx + ey * dy)
        c = ex * ex + ey * ey - (self.radius - r) ** 2
        if a == 0:
            return 0.0, math.inf
        discriminant = b * b - 4 * a * c
        if discriminant < 0:
            return 0.0, math.inf
        root = math.sqrt(discriminant)
        low, high = (-b - root) / (2 * a), (-b + root) / (2 * a)
        if not low <= 1 <= high:
            return 0.0, math.inf
        return max(low, 0.0), high


@dataclass(frozen=True)
class RectField:
    """A rectangular field, as used by the separated layout."""

    x_min: float
    x_max: float
    y_min: float
    y_max: float
    margin: float

    @property
    def centre(self) -> Tuple[float, float]:
        return ((self.x_min + self.x_max) / 2, (self.y_min + self.y_max) / 2)

    @property
    def inscribed_radius(self) -> float:
        return min(self.x_max - self.x_min, self.y_max - self.y_min) / 2

    def scale_bounds(self, disc: Disc, about: Tuple[float, float]) -> Tuple[float, float]:
        x, y, r = disc
        low, high = 0.0, math.inf
        for position, origin, lower, upper in (
            (x, about[0], self.x_min, self.x_max),
            (y, about[1], self.y_min, self.y_max),
        ):
            d = position - origin
            if d == 0:
                continue
            bounds = sorted((
                (lower + r + self.margin - origin) / d,
                (upper - r - self.margin - origin) / d,
            ))
            low, high = max(low, bounds[0]), min(high, bounds[1])
        if not low <= 1 <= high:
            return 0.0, math.inf
        return low, high


def centroid(discs: Sequence[Disc]) -> Tuple[float, float]:
    return (
        sum(d[0] for d in discs) / len(discs),
        sum(d[1] for d in discs) / len(discs),
    )


def scaled(discs: Sequence[Disc], factor: float, about: Tuple[float, float]) -> List[Disc]:
    """The discs with their centres scaled about a point; radii unchanged."""
    ax, ay = about
    return [(ax + factor * (x - ax), ay + factor * (y - ay), r) for x, y, r in discs]


def hull_at(discs: Sequence[Disc], factor: float, about: Tuple[float, float]) -> float:
    return disc_hull_area(scaled(discs, factor, about))


def max_scale(discs: Sequence[Disc], about, field) -> float:
    """The largest scale factor that keeps every disc inside the field.

    Infinite when nothing constrains the array, which happens only when every
    disc sits on the scaling centre; it is then 1, since such an array has no
    extent to scale.
    """
    high = math.inf
    for disc in discs:
        high = min(high, field.scale_bounds(disc, about)[1])
    return high if math.isfinite(high) else 1.0


def scale_for_hull(discs, about, target: float, low: float, high: float) -> float:
    """The scale factor in [low, high] whose hull is closest to the target.

    The hull grows with the factor, so bisection finds it. The ends are
    returned when the target lies beyond them.
    """
    if hull_at(discs, high, about) <= target:
        return high
    if hull_at(discs, low, about) >= target:
        return low
    for _ in range(MAX_BISECTIONS):
        mid = (low + high) / 2
        area = hull_at(discs, mid, about)
        if abs(area - target) <= HULL_TOLERANCE * target:
            return mid
        if area < target:
            low = mid
        else:
            high = mid
    return (low + high) / 2


def expansion_targets(hull_a, hull_b, ratio, max_a, max_b):
    """Hull targets (a, b) with a / b == ratio reachable by spreading alone.

    Neither array can shrink, so b is raised to a / ratio when it falls short
    and a is then set from it; when that takes a past what its field allows,
    a stops at the field and b must already be small enough.

    Returns:
        (target_a, target_b), or None when spreading cannot get there.
    """
    b = max(hull_b, hull_a / ratio)
    a = ratio * b
    if a > max_a:
        a, b = max_a, max_a / ratio
    slack = 1 + HULL_TOLERANCE
    if b < hull_b / slack or b > max_b * slack or a < hull_a / slack:
        return None
    return a, b


def expand_to_ratio(discs_a, field_a, discs_b, field_b, ratio):
    """Spread two arrays so that hull(a) / hull(b) == ratio.

    Returns:
        (discs_a, discs_b) moved, or None when spreading inside the fields
        cannot reach the ratio. Overlaps between the two arrays are not
        checked here; the caller validates and retries with another layout.
    """
    about_a, about_b = centroid(discs_a), centroid(discs_b)
    high_a, high_b = max_scale(discs_a, about_a, field_a), max_scale(discs_b, about_b, field_b)
    targets = expansion_targets(
        disc_hull_area(discs_a), disc_hull_area(discs_b), ratio,
        hull_at(discs_a, high_a, about_a), hull_at(discs_b, high_b, about_b),
    )
    if targets is None:
        return None
    factor_a = scale_for_hull(discs_a, about_a, targets[0], 1.0, max(high_a, 1.0))
    factor_b = scale_for_hull(discs_b, about_b, targets[1], 1.0, max(high_b, 1.0))
    return scaled(discs_a, factor_a, about_a), scaled(discs_b, factor_b, about_b)


# --- Sizing the smaller field, and refusing a plan ---------------------------

def max_hull_bound(n: int, r_min: float, r_max: float, field_radius: float) -> float:
    """Upper bound on the hull n dots can extend over inside a circular field.

    ``field_radius`` is the radius every disc stays within. The centres can
    reach at most field_radius - r_min from the centre, where the regular
    n-gon has the largest area and perimeter of any inscribed n-gon; the discs
    add at most a rim of r_max around it.
    """
    if n <= 0:
        return 0.0
    if n == 1:
        return math.pi * r_max ** 2
    rim = field_radius - r_min
    if n == 2:
        hull_of_centres, perimeter = 0.0, 4 * rim
    else:
        hull_of_centres = n / 2 * rim ** 2 * math.sin(2 * math.pi / n)
        perimeter = 2 * n * rim * math.sin(math.pi / n)
    bound = hull_of_centres + perimeter * r_max + math.pi * r_max ** 2
    return min(bound, math.pi * field_radius ** 2)


def reduced_field_radius(n_large: int, ratio: float, r_min, r_max, field_radius) -> float:
    """Radius of the field the array with the smaller hull is placed in.

    The other array can extend over at most max_hull_bound, and in practice
    less, so the smaller array's hull must stay below that divided by the
    ratio, which a field of this radius guarantees.
    """
    largest = FIELD_SAFETY * max_hull_bound(n_large, r_min, r_max, field_radius)
    return min(field_radius, math.sqrt(largest / ratio / math.pi))


def placement_radius(n: int, r_min: float, r_max: float, point_sep: float) -> float:
    """Smallest field radius n dots can be placed in by random placement.

    Each dot claims a disc of its mean radius plus half the separation, and
    random placement fills at most PLACEMENT_DENSITY of the field with them.
    """
    if n <= 0:
        return 0.0
    claimed = (r_min + r_max) / 2 + point_sep / 2
    return point_sep / 2 + claimed * math.sqrt(n / PLACEMENT_DENSITY)


def smaller_hull_side(n1: int, n2: int) -> int:
    """Which side of a pair gets the smaller field: 1 or 2.

    The side with more dots, whose hull would otherwise be the larger one;
    the second side when the counts are equal.
    """
    return 1 if n1 > n2 else 2


def unreachable_hull_pairs(tasks, r_min, r_max, field_radius, point_sep):
    """Dot-count pairs in a plan whose hull condition cannot be met.

    Args:
        tasks: GenerationTask objects with n1, n2 and hull in their params.
        r_min, r_max: The dot radius range the dots are drawn from.
        field_radius: Radius of the field the dots are placed in.
        point_sep: Minimum gap between dots.

    Returns:
        list: Sorted unique (fewer, more, hull, field, needed) tuples, where
        field is the radius the more numerous array would have to fit in and
        needed the smallest radius it can be placed in.
    """
    found = {}
    for task in tasks:
        n1, n2 = task.params.get("n1"), task.params.get("n2")
        hull = task.params.get("hull", "random")
        if n1 is None or n2 is None or hull == "random":
            continue
        fewer, more = min(n1, n2), max(n1, n2)
        ratio = more / fewer if hull == "inverse" else 1.0
        field = reduced_field_radius(fewer, ratio, r_min, r_max, field_radius)
        needed = placement_radius(more, r_min, r_max, point_sep)
        if field < needed:
            found[(fewer, more, hull)] = (field, needed)
    return sorted((f, m, h, *v) for (f, m, h), v in found.items())
