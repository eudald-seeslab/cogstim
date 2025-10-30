import itertools
from random import randint
from PIL import Image, ImageDraw
import numpy as np

np.random.seed(1234)


class PointLayoutError(ValueError):
    pass


class NumberPoints:

    boundary_width = 5
    point_sep = 10
    # We consider equal areas if their (r1 - r2) / r1 ratio differs by less than this number:
    area_tolerance = 0.001

    def __init__(self, img, init_size, colour_1, colour_2, min_point_radius=8, max_point_radius=16, attempts_limit=10):
        self.img = img
        self.init_size = init_size
        self.draw = ImageDraw.Draw(img)
        self.colour_1 = colour_1
        self.colour_2 = colour_2
        self.min_point_radius = min_point_radius
        self.max_point_radius = max_point_radius
        self.attempts_limit = attempts_limit

    def _create_random_point(self):
        radius = randint(self.min_point_radius, self.max_point_radius)
        limit = self.boundary_width + radius + self.point_sep

        # Change mental coordinate system to the center of the square
        rad = int(self.init_size / 2 - limit)
        rx = randint(-rad, rad)
        # Make sure we are always inside the circle
        max_ = int(np.sqrt((self.init_size / 2 - limit) ** 2 - rx ** 2))
        ry = randint(-max_, max_)

        # Transform to coordinates with origin on the upper left quadrant
        x = rx + self.init_size / 2
        y = ry + self.init_size / 2

        return x, y, radius

    def _check_no_overlaps(self, point_array, new_point):
        return all([self._check_points_not_overlapping(a[0], new_point) for a in point_array])

    def _check_points_not_overlapping(self, point, new_point):
        dist = np.sqrt((point[0] - new_point[0]) ** 2 + (point[1] - new_point[1]) ** 2)

        return dist > point[2] + new_point[2] + self.point_sep

    def design_n_points(self, n, colour, point_array=None):

        if point_array is None:
            point_array = []

        for _ in range(n):
            new_point = self._create_random_point()

            attempts = 0
            while not self._check_no_overlaps(point_array, new_point):
                new_point = self._create_random_point()
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
        self.draw.ellipse((x1, y1, x2, y2), fill=fill_colour)

    def draw_points(self, point_array):
        [self._draw_point(a[0], a[1]) for a in point_array]
        return self.img

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

        # Who is big and who is small
        small, big_area, small_area = self._get_areas(point_array)

        # Make all points in small area bigger to match bigger area
        # This brings us to this problem: solve a = sum_i^n (x_i^2 + 2r_i*x_i),
        # which is not solvable analytically. Therefore, what we'll do is add
        # pixel after pixel to all points until we are close to the target value
        while not self._check_areas_equal(big_area, small_area):
            point_array = [self._increase_radius(a) if a[1] == small else a for a in point_array]
            # Recompute
            small, big_area, small_area = self._get_areas(point_array)

        # Recheck that we haven't created any overlap
        for pair in itertools.combinations(point_array, 2):
            if not self._check_points_not_overlapping(pair[0][0], pair[1][0]):
                raise PointLayoutError("Overlapping points created")

        return point_array

    
    def _check_within_boundaries(self, point):
        return (all([point[i] - point[2] > 0 for i in range(2)]) and 
                all([point[i] + point[2] < self.init_size for i in range(2)]))

    
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
        # get current radii
        radii = [a[0][2] for a in point_array]
        # increase radii
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

    # --- New helpers for incremental equalization fallback ---
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


# --- Consolidated utilities for dot placement and image creation ---

def create_numberpoints_image(bg_colour: str, dot_colour: str, min_radius: int, max_radius: int, 
                               attempts_limit: int, init_size: int = None, colour_2=None):
    """Create a PIL Image and NumberPoints instance for dot placement.
    
    This is a unified utility for creating a blank dot-array image canvas and initializing
    a NumberPoints object for random dot placement. Supports both single-colour and two-colour modes.
    
    Args:
        bg_colour: Background color (name or hex string)
        dot_colour: Primary dot color (name or hex string, or tuple for colour_1)
        min_radius: Minimum dot radius in pixels
        max_radius: Maximum dot radius in pixels
        attempts_limit: Maximum attempts for point placement
        init_size: Image size (defaults to 512 if not provided)
        colour_2: Optional second color for two-colour mode (can be None, name, hex, or tuple)
    
    Returns:
        Tuple of (PIL.Image, NumberPoints instance)
    """
    from cogstim.helpers import COLOUR_MAP, SIZES
    
    if init_size is None:
        init_size = SIZES["init_size"]
    
    # Handle colour mapping: if dot_colour is a string name, map it; otherwise use as-is
    if isinstance(dot_colour, str) and dot_colour in COLOUR_MAP:
        mapped_colour_1 = COLOUR_MAP[dot_colour]
    else:
        mapped_colour_1 = dot_colour
    
    # Handle colour_2: if provided as string name, map it; if None, stays None
    mapped_colour_2 = None
    if colour_2 is not None:
        if isinstance(colour_2, str) and colour_2 in COLOUR_MAP:
            mapped_colour_2 = COLOUR_MAP[colour_2]
        else:
            mapped_colour_2 = colour_2
    
    img = Image.new("RGB", (init_size, init_size), color=bg_colour)
    np_obj = NumberPoints(
        img,
        init_size,
        colour_1=mapped_colour_1,
        colour_2=mapped_colour_2,
        min_point_radius=min_radius,
        max_point_radius=max_radius,
        attempts_limit=attempts_limit,
    )
    return img, np_obj


def generate_random_points(np_obj: NumberPoints, n_points: int, colour: str = "colour_1", 
                           point_array=None):
    """Generate n random points on a NumberPoints canvas without overlaps.
    
    This is a unified utility for placing random dots on a NumberPoints canvas.
    
    Args:
        np_obj: NumberPoints instance to place points on
        n_points: Number of points to generate
        colour: Colour identifier to use ("colour_1" or "colour_2")
        point_array: Optional existing point array to add to
    
    Returns:
        List of point tuples: [((x, y, radius), colour), ...]
    """
    return np_obj.design_n_points(n_points, colour, point_array=point_array)