import itertools
import math
from random import randint
import numpy as np

from cogstim.helpers import hull_control


class PointLayoutError(ValueError):
    pass


class HullLayoutError(PointLayoutError):
    """A layout that cannot meet its hull condition; another draw may."""


class DotsCore:

    boundary_width = 5
    point_sep = 10
    # We consider equal areas if their (r1 - r2) / r1 ratio differs by less than this number:
    area_tolerance = 0.001
    # Maximum whole-pixel radius increments equalize_areas will apply before giving up
    equalize_increment_limit = 1000

    def __init__(self, init_size, colour_1, colour_2=None, bg_colour=None, mode=None,
                 min_point_radius=None, max_point_radius=None, attempts_limit=None):
        """Initialize DotsCore for dot placement on an image.
        
        Args:
            init_size: Image size in pixels (square)
            colour_1: Primary dot colour
            colour_2: Optional second dot colour for two-colour images
            bg_colour: Background colour (uses defaults.IMAGE_DEFAULTS if None)
            mode: Image mode (uses defaults.IMAGE_DEFAULTS if None)
            min_point_radius: Minimum dot radius (uses defaults.DOT_DEFAULTS if None)
            max_point_radius: Maximum dot radius (uses defaults.DOT_DEFAULTS if None)
            attempts_limit: Maximum attempts to place dots without overlap (uses defaults.DOT_DEFAULTS if None)
        """
        from cogstim.helpers.image_utils import ImageCanvas
        from cogstim.helpers.constants import IMAGE_DEFAULTS, DOT_DEFAULTS
        
        # Apply defaults if not provided
        bg_colour = bg_colour if bg_colour is not None else IMAGE_DEFAULTS["background_colour"]
        mode = mode if mode is not None else IMAGE_DEFAULTS["mode"]
        min_point_radius = min_point_radius if min_point_radius is not None else DOT_DEFAULTS["min_point_radius"]
        max_point_radius = max_point_radius if max_point_radius is not None else DOT_DEFAULTS["max_point_radius"]
        attempts_limit = attempts_limit if attempts_limit is not None else DOT_DEFAULTS["attempts_limit"]
        
        self.canvas = ImageCanvas(init_size, bg_colour, mode)
        self.init_size = init_size
        self.colour_1 = colour_1
        self.colour_2 = colour_2
        self.min_point_radius = min_point_radius
        self.max_point_radius = max_point_radius
        self.attempts_limit = attempts_limit

    def field_radius(self):
        """Radius of the circle every dot stays within by default."""
        return self.init_size / 2 - self.boundary_width

    def _create_random_point(self, centre=None, field_radius=None):
        """Generate a random dot inside a circular field.

        By default the field is the canvas circle, keeping boundary_width
        clear of the edge. A smaller field, concentric or not, is how the hull
        conditions confine the array that must extend less.
        """
        radius = randint(self.min_point_radius, self.max_point_radius)
        if field_radius is None:
            field_radius = self.field_radius()
        if centre is None:
            centre = (self.init_size / 2, self.init_size / 2)

        # Change mental coordinate system to the centre of the field
        rad = int(field_radius - radius - self.point_sep)
        if rad <= 0:
            raise PointLayoutError("The field is too small for a dot")
        rx = randint(-rad, rad)
        # Make sure we are always inside the circle
        max_ = int(np.sqrt(rad ** 2 - rx ** 2))
        ry = randint(-max_, max_)

        # Transform to coordinates with origin on the upper left quadrant
        x = rx + centre[0]
        y = ry + centre[1]

        return x, y, radius

    def _create_random_point_in_rect(self, x_min, x_max, y_min, y_max):
        """Generate a random dot constrained to a rectangular region.

        The dot (center +/- radius + point_sep) is guaranteed to fit inside the
        rectangle defined by (x_min, x_max, y_min, y_max).
        """
        radius = randint(self.min_point_radius, self.max_point_radius)
        margin = radius + self.point_sep
        x = randint(int(x_min + margin), int(x_max - margin))
        y = randint(int(y_min + margin), int(y_max - margin))
        return x, y, radius

    def _check_no_overlaps(self, point_array, new_point):
        return all([self._check_points_not_overlapping(a[0], new_point) for a in point_array])

    def _check_points_not_overlapping(self, point, new_point):
        dist = np.sqrt((point[0] - new_point[0]) ** 2 + (point[1] - new_point[1]) ** 2)

        return dist > point[2] + new_point[2] + self.point_sep

    def design_n_points(self, n, colour, point_array=None, region=None, field=None):
        """Place *n* non-overlapping dots for *colour*.

        Args:
            n: Number of dots to place.
            colour: Colour tag (``"colour_1"`` or ``"colour_2"``).
            point_array: Existing points to avoid overlapping with.
            region: Optional ``(x_min, x_max, y_min, y_max)`` rectangle that
                constrains placement.  When *None*, the default circular
                placement covering the full canvas is used.
            field: Optional ``(centre, radius)`` circle to place within
                instead, used by the hull conditions.
        """
        if point_array is None:
            point_array = []

        if region is not None:
            def point_fn():
                return self._create_random_point_in_rect(*region)
        elif field is not None:
            def point_fn():
                return self._create_random_point(*field)
        else:
            point_fn = self._create_random_point

        for _ in range(n):
            new_point = point_fn()

            attempts = 0
            while not self._check_no_overlaps(point_array, new_point):
                new_point = point_fn()
                attempts += 1
                if attempts > self.attempts_limit:
                    raise PointLayoutError("Too many attempts to create a good layout.")
            point_array.append((new_point, colour))

        return point_array

    def _draw_point(self, point, colour):
        x1 = point[0] - point[2]
        x2 = point[0] + point[2]
        y1 = point[1] - point[2]
        y2 = point[1] + point[2]
        # If only one colour is configured, always use colour_1
        if self.colour_2 is None:
            fill_colour = self.colour_1
        else:
            fill_colour = self.colour_1 if colour == "colour_1" else self.colour_2
        self.canvas.draw_ellipse((x1, y1, x2, y2), fill=fill_colour, label="dot")

    def draw_points(self, point_array):
        """Draw every dot and return the canvas.

        Returns the canvas rather than the bare PIL image so the recorded
        geometry reaches save_image, which needs it for annotations and SVG.
        """
        [self._draw_point(a[0], a[1]) for a in point_array]
        return self.canvas

    @staticmethod
    def compute_area(point_array, colour):
        return sum([np.pi * a[0][2] ** 2 for a in point_array if a[1] == colour])

    def _check_areas_equal(self, big, small):
        return (big - small) / big < self.area_tolerance

    def _get_areas(self, point_array):
        colour_1_area = self.compute_area(point_array, "colour_1")
        colour_2_area = self.compute_area(point_array, "colour_2")

        # Who is big and who is small
        small = "colour_2" if colour_1_area > colour_2_area else "colour_1"
        big_area, small_area = (
            (colour_1_area, colour_2_area) if small == "colour_2" else (colour_2_area, colour_1_area)
        )

        return small, big_area, small_area

    @staticmethod
    def _increase_radius(point, increase=1):
        return (point[0][0], point[0][1], point[0][2] + increase), point[1]

    @staticmethod
    def _set_radius(point, new_radius):
        return (point[0][0], point[0][1], new_radius), point[1]

    def equalize_areas(self, point_array):
        """Grow the dots of the smaller-area colour until both colours match in area.

        Raises:
            PointLayoutError: if equalizing would push a dot past the edge of the
                canvas, make two dots overlap, or fail to converge. Callers catch
                this and retry with a fresh layout.
        """
        # Who is big and who is small
        small, big_area, small_area = self._get_areas(point_array)

        # Make all points in small area bigger to match bigger area
        # This brings us to this problem: solve a = sum_i^n (x_i^2 + 2r_i*x_i),
        # which is not solvable analytically. Therefore, what we'll do is add
        # pixel after pixel to all points until we are close to the target value
        increments = 0
        while not self._check_areas_equal(big_area, small_area):
            # Each pass grows every dot of the smaller colour by a whole pixel, so
            # the areas can leapfrog past the tolerance and oscillate instead of
            # converging. Bound the loop rather than hanging the whole run.
            if increments >= self.equalize_increment_limit:
                raise PointLayoutError(
                    f"Areas did not converge within {self.equalize_increment_limit} "
                    "radius increments"
                )
            point_array = [self._increase_radius(a) if a[1] == small else a for a in point_array]
            increments += 1

            # Growing a radius can push a dot past the edge of the canvas. The other
            # area-adjusting methods all check this; without it here the dot is
            # silently drawn clipped.
            for point in point_array:
                if not self._check_within_boundaries(point[0]):
                    raise PointLayoutError("Equalized point is outside boundaries")

            # Recompute areas after adjustment
            small, big_area, small_area = self._get_areas(point_array)

        # Recheck that we haven't created any overlap
        for pair in itertools.combinations(point_array, 2):
            if not self._check_points_not_overlapping(pair[0][0], pair[1][0]):
                raise PointLayoutError("Overlapping points created")

        return point_array

    
    def set_area_ratio(self, point_array, target_ratio):
        """Rescale both colours so that area(colour_1) / area(colour_2) == target_ratio.

        The inverse surface condition needs the colour with fewer dots to cover
        more surface. Growing that colour alone would make its dots very large
        for the wider ratios, so the change is shared: colour_1's radii are
        multiplied by the fourth root of the required change in area ratio and
        colour_2's divided by it, which moves the mean dot size as little as
        possible. A ratio of 1 equalizes the two areas.

        Raises:
            PointLayoutError: if either colour has no dots, or a grown dot would
                leave the canvas or overlap a neighbour. Callers retry with a
                fresh layout.
        """
        area_1 = self.compute_area(point_array, "colour_1")
        area_2 = self.compute_area(point_array, "colour_2")
        if area_1 == 0 or area_2 == 0:
            raise PointLayoutError("Both colours need dots to set an area ratio")

        change = target_ratio / (area_1 / area_2)
        factor_1 = change ** 0.25
        scaled = [
            self._set_radius(p, p[0][2] * (factor_1 if p[1] == "colour_1" else 1 / factor_1))
            for p in point_array
        ]
        if not self.validate_layout(scaled):
            raise PointLayoutError(
                "Setting the area ratio pushed a dot off the canvas or into a neighbour"
            )
        return scaled

    def hull_fields(self, regions=None):
        """The field each colour may spread over: its region, or the canvas circle."""
        fields = {}
        for colour in ("colour_1", "colour_2"):
            if regions and colour in regions:
                fields[colour] = hull_control.RectField(*regions[colour], margin=self.point_sep)
            else:
                fields[colour] = hull_control.CircleField(
                    (self.init_size / 2, self.init_size / 2),
                    self.field_radius() - self.point_sep,
                )
        return fields

    def expand_hulls_to_ratio(self, point_array, target_ratio, regions=None):
        """Spread the dots so that hull(colour_1) / hull(colour_2) == target_ratio.

        Each colour's centres are scaled outwards about that colour's centroid;
        no radius changes and no dot moves inwards, so a surface condition
        already applied still holds and no dot of one colour runs into another
        of the same colour. The colour that must extend less is expected to
        have been placed in a reduced field (see hull_control), since spreading
        alone cannot make a hull smaller.

        Args:
            point_array: Placed dots, as ((x, y, r), colour) pairs.
            target_ratio: Required hull(colour_1) / hull(colour_2).
            regions: Optional {colour: (x_min, x_max, y_min, y_max)} rectangles
                the colours were confined to; the canvas circle otherwise.

        Raises:
            HullLayoutError: if this layout cannot reach the ratio by spreading
                inside its fields, or spreading makes the two colours overlap.
            PointLayoutError: if either colour has no dots.
        """
        discs = {
            colour: [p for p, c in point_array if c == colour]
            for colour in ("colour_1", "colour_2")
        }
        if not discs["colour_1"] or not discs["colour_2"]:
            raise PointLayoutError("Both colours need dots to set a hull ratio")

        fields = self.hull_fields(regions)
        moved = hull_control.expand_to_ratio(
            discs["colour_1"], fields["colour_1"],
            discs["colour_2"], fields["colour_2"],
            target_ratio,
        )
        if moved is None:
            raise HullLayoutError("This layout cannot reach the hull ratio by spreading")

        result = [(disc, "colour_1") for disc in moved[0]] + [(disc, "colour_2") for disc in moved[1]]
        if not self.validate_layout(result):
            raise HullLayoutError("Spreading the dots to the hull ratio made the colours overlap")
        return result

    def _check_within_boundaries(self, point):
        """True if the dot's rasterised extent fits inside the canvas.

        The ellipse covers whole pixels from floor(centre - radius) to
        ceil(centre + radius), so the bounds have to be compared after rounding
        outwards: a dot at ``centre - radius == 0.5`` satisfies a plain ``> 0``
        test yet still paints pixel column 0.

        The outermost pixel ring is excluded as well, so that a dot never merely
        touches the border. A dot painting the edge row is visually
        indistinguishable from one the canvas has cut off.
        """
        radius = point[2]
        return all(
            math.floor(centre - radius) >= 1
            and math.ceil(centre + radius) <= self.init_size - 2
            for centre in (point[0], point[1])
        )

    
    def fix_total_area(self, point_array, target_area):
        current_area = self.compute_area(point_array, "colour_1")
        if current_area > target_area:
            raise PointLayoutError("Current area is already bigger than target area")

        # Here we can compute analytically the increase in area for all points; 
        # we can then increase the radius of all points by the same amount
        area_diff = target_area - current_area
        num_points = len(point_array)
        # We give the same area increase to all points
        area_increase = int(area_diff / num_points)
        # Calculate new radii
        radii = [a[0][2] for a in point_array]
        increases = [2 * np.sqrt(r**2 + area_increase) - r for r in radii]
        point_array = [self._increase_radius(a, i) for a, i in zip(point_array, increases)]

        # Check that we are still within the boundaries
        for point in point_array:
            if not self._check_within_boundaries(point[0]):
                raise PointLayoutError("Point is outside boundaries")
        
        # Recheck that we haven't created any overlap
        for pair in itertools.combinations(point_array, 2):
            if not self._check_points_not_overlapping(pair[0][0], pair[1][0]):
                raise PointLayoutError("Overlapping points created")
            
        return point_array

    def scale_total_area(self, point_array, target_area):
        """Scale all radii by a common factor so the total area matches target_area.

        This method allows both shrinking and enlarging dots and may exceed the
        configured max radius if needed. It validates boundary and overlap after scaling.
        """
        current_area = self.compute_area(point_array, "colour_1")
        if current_area == 0:
            raise PointLayoutError("Current area is zero; cannot scale radii")

        scale_factor = np.sqrt(target_area / current_area)
        scaled = [
            self._set_radius(p, p[0][2] * scale_factor)
            for p in point_array
        ]

        # Boundary check
        for point in scaled:
            if not self._check_within_boundaries(point[0]):
                raise PointLayoutError("Scaled point is outside boundaries")

        # Overlap check
        for pair in itertools.combinations(scaled, 2):
            if not self._check_points_not_overlapping(pair[0][0], pair[1][0]):
                raise PointLayoutError("Overlapping points after scaling")

        return scaled

    def scale_by_factor(self, point_array, factor, round_radii=True):
        """Scale all radii by a multiplicative factor.

        - If round_radii is True, radii are rounded to nearest integer pixels.
        - Validates boundaries and overlaps after scaling.
        """
        if factor <= 0:
            raise PointLayoutError("Scale factor must be positive")

        scaled = []
        for p in point_array:
            new_r = p[0][2] * factor
            if round_radii:
                new_r = int(round(new_r))
                # Prevent zero radius due to rounding
                new_r = max(new_r, 1)
            scaled.append(self._set_radius(p, new_r))

        # Boundary check
        for point in scaled:
            if not self._check_within_boundaries(point[0]):
                raise PointLayoutError("Scaled point is outside boundaries")

        # Overlap check
        for pair in itertools.combinations(scaled, 2):
            if not self._check_points_not_overlapping(pair[0][0], pair[1][0]):
                raise PointLayoutError("Overlapping points after scaling")

        return scaled

    # --- Helpers for incremental equalization ---
    def increase_all_radii(self, point_array, increment=1):
        """Return a new point array with all radii increased by `increment`."""
        return [self._increase_radius(p, increment) for p in point_array]

    def validate_layout(self, point_array):
        """Return True if all points are within boundaries and non-overlapping."""
        for point in point_array:
            if not self._check_within_boundaries(point[0]):
                return False
        for pair in itertools.combinations(point_array, 2):
            if not self._check_points_not_overlapping(pair[0][0], pair[1][0]):
                return False
        return True
