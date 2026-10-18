"""Tests for cogstim.dots_core module."""

import pytest
import numpy as np
from unittest.mock import patch

from cogstim.helpers.dots_core import DotsCore, PointLayoutError


class TestNumberPointsNewMethods:
    """Test the new methods added to NumberPoints class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.np = DotsCore(
            init_size=512,
            colour_1=(255, 255, 0),  # yellow
            colour_2=(0, 0, 255),    # blue
            bg_colour=(0, 0, 0),     # black
            min_point_radius=10,
            max_point_radius=20,
            attempts_limit=100
        )

    def test_fix_total_area_success(self):
        """Test fix_total_area method with valid input."""
        # Create a point array with known area
        point_array = [
            ((100, 100, 10), "colour_1"),  # radius 10, area = π * 100
            ((200, 200, 15), "colour_1"),  # radius 15, area = π * 225
        ]
        # Current area = π * (100 + 225) = π * 325
        current_area = self.np.compute_area(point_array, "colour_1")
        target_area = current_area + 1000  # Increase by 1000
        
        # Mock boundary and overlap checks to pass
        with patch.object(self.np, '_check_within_boundaries', return_value=True), \
             patch.object(self.np, '_check_points_not_overlapping', return_value=True):
            
            result = self.np.fix_total_area(point_array, target_area)
            
            # Should return modified point array
            assert len(result) == len(point_array)
            # Radii should be increased
            for i, (point, colour) in enumerate(result):
                assert point[2] > point_array[i][0][2]  # radius increased

    def test_fix_total_area_current_area_too_big(self):
        """Test fix_total_area raises error when current area > target area."""
        point_array = [
            ((100, 100, 10), "colour_1"),
            ((200, 200, 15), "colour_1"),
        ]
        current_area = self.np.compute_area(point_array, "colour_1")
        target_area = current_area - 1000  # Smaller than current
        
        with pytest.raises(PointLayoutError, match="Current area is already bigger than target area"):
            self.np.fix_total_area(point_array, target_area)

    def test_fix_total_area_boundary_violation(self):
        """Test fix_total_area raises error when points go outside boundaries."""
        point_array = [
            ((100, 100, 10), "colour_1"),
            ((200, 200, 15), "colour_1"),
        ]
        target_area = self.np.compute_area(point_array, "colour_1") + 1000
        
        # Mock boundary check to fail
        with patch.object(self.np, '_check_within_boundaries', return_value=False):
            with pytest.raises(PointLayoutError, match="Point is outside boundaries"):
                self.np.fix_total_area(point_array, target_area)

    def test_fix_total_area_overlap_violation(self):
        """Test fix_total_area raises error when points overlap after scaling."""
        point_array = [
            ((100, 100, 10), "colour_1"),
            ((200, 200, 15), "colour_1"),
        ]
        target_area = self.np.compute_area(point_array, "colour_1") + 1000
        
        # Mock boundary check to pass but overlap check to fail
        with patch.object(self.np, '_check_within_boundaries', return_value=True), \
             patch.object(self.np, '_check_points_not_overlapping', return_value=False):
            with pytest.raises(PointLayoutError, match="Overlapping points created"):
                self.np.fix_total_area(point_array, target_area)

    def test_scale_total_area_success(self):
        """Test scale_total_area method with valid input."""
        point_array = [
            ((100, 100, 10), "colour_1"),  # area = π * 100
            ((200, 200, 15), "colour_1"),  # area = π * 225
        ]
        current_area = self.np.compute_area(point_array, "colour_1")
        target_area = current_area * 2  # Double the area
        
        # Mock boundary and overlap checks to pass
        with patch.object(self.np, '_check_within_boundaries', return_value=True), \
             patch.object(self.np, '_check_points_not_overlapping', return_value=True):
            
            result = self.np.scale_total_area(point_array, target_area)
            
            # Should return scaled point array
            assert len(result) == len(point_array)
            # Radii should be scaled by sqrt(2) approximately
            for i, (point, colour) in enumerate(result):
                expected_radius = point_array[i][0][2] * np.sqrt(2)
                assert abs(point[2] - expected_radius) < 0.1  # Allow small floating point error

    def test_scale_total_area_zero_current_area(self):
        """Test scale_total_area raises error when current area is zero."""
        point_array = []  # Empty array has zero area
        
        with pytest.raises(PointLayoutError, match="Current area is zero; cannot scale radii"):
            self.np.scale_total_area(point_array, 1000)

    def test_scale_total_area_boundary_violation(self):
        """Test scale_total_area raises error when scaled points go outside boundaries."""
        point_array = [
            ((100, 100, 10), "colour_1"),
            ((200, 200, 15), "colour_1"),
        ]
        target_area = self.np.compute_area(point_array, "colour_1") * 10  # Large scale factor
        
        # Mock boundary check to fail
        with patch.object(self.np, '_check_within_boundaries', return_value=False):
            with pytest.raises(PointLayoutError, match="Scaled point is outside boundaries"):
                self.np.scale_total_area(point_array, target_area)

    def test_scale_total_area_overlap_violation(self):
        """Test scale_total_area raises error when scaled points overlap."""
        point_array = [
            ((100, 100, 10), "colour_1"),
            ((200, 200, 15), "colour_1"),
        ]
        target_area = self.np.compute_area(point_array, "colour_1") * 10  # Large scale factor
        
        # Mock boundary check to pass but overlap check to fail
        with patch.object(self.np, '_check_within_boundaries', return_value=True), \
             patch.object(self.np, '_check_points_not_overlapping', return_value=False):
            with pytest.raises(PointLayoutError, match="Overlapping points after scaling"):
                self.np.scale_total_area(point_array, target_area)

    def test_scale_by_factor_success(self):
        """Test scale_by_factor method with valid input."""
        point_array = [
            ((100, 100, 10), "colour_1"),
            ((200, 200, 15), "colour_1"),
        ]
        factor = 1.5
        
        # Mock boundary and overlap checks to pass
        with patch.object(self.np, '_check_within_boundaries', return_value=True), \
             patch.object(self.np, '_check_points_not_overlapping', return_value=True):
            
            result = self.np.scale_by_factor(point_array, factor)
            
            # Should return scaled point array
            assert len(result) == len(point_array)
            # Radii should be scaled by factor
            for i, (point, colour) in enumerate(result):
                expected_radius = int(round(point_array[i][0][2] * factor))
                assert point[2] == expected_radius

    def test_scale_by_factor_round_radii_false(self):
        """Test scale_by_factor with round_radii=False."""
        point_array = [
            ((100, 100, 10), "colour_1"),
            ((200, 200, 15), "colour_1"),
        ]
        factor = 1.5
        
        # Mock boundary and overlap checks to pass
        with patch.object(self.np, '_check_within_boundaries', return_value=True), \
             patch.object(self.np, '_check_points_not_overlapping', return_value=True):
            
            result = self.np.scale_by_factor(point_array, factor, round_radii=False)
            
            # Radii should be scaled by factor but not rounded
            for i, (point, colour) in enumerate(result):
                expected_radius = point_array[i][0][2] * factor
                assert point[2] == expected_radius

    def test_scale_by_factor_zero_factor(self):
        """Test scale_by_factor raises error for zero or negative factor."""
        point_array = [
            ((100, 100, 10), "colour_1"),
        ]
        
        with pytest.raises(PointLayoutError, match="Scale factor must be positive"):
            self.np.scale_by_factor(point_array, 0)
        
        with pytest.raises(PointLayoutError, match="Scale factor must be positive"):
            self.np.scale_by_factor(point_array, -1)

    def test_scale_by_factor_boundary_violation(self):
        """Test scale_by_factor raises error when scaled points go outside boundaries."""
        point_array = [
            ((100, 100, 10), "colour_1"),
        ]
        factor = 100  # Very large factor
        
        # Mock boundary check to fail
        with patch.object(self.np, '_check_within_boundaries', return_value=False):
            with pytest.raises(PointLayoutError, match="Scaled point is outside boundaries"):
                self.np.scale_by_factor(point_array, factor)

    def test_scale_by_factor_overlap_violation(self):
        """Test scale_by_factor raises error when scaled points overlap."""
        point_array = [
            ((100, 100, 10), "colour_1"),
            ((200, 200, 15), "colour_1"),
        ]
        factor = 100  # Very large factor
        
        # Mock boundary check to pass but overlap check to fail
        with patch.object(self.np, '_check_within_boundaries', return_value=True), \
             patch.object(self.np, '_check_points_not_overlapping', return_value=False):
            with pytest.raises(PointLayoutError, match="Overlapping points after scaling"):
                self.np.scale_by_factor(point_array, factor)

    def test_scale_by_factor_minimum_radius(self):
        """Test scale_by_factor ensures minimum radius of 1 when rounding."""
        point_array = [
            ((100, 100, 1), "colour_1"),  # Small radius
        ]
        factor = 0.1  # Scale down
        
        # Mock boundary and overlap checks to pass
        with patch.object(self.np, '_check_within_boundaries', return_value=True), \
             patch.object(self.np, '_check_points_not_overlapping', return_value=True):
            
            result = self.np.scale_by_factor(point_array, factor)
            
            # Should ensure minimum radius of 1
            assert result[0][0][2] >= 1


class TestNumberPointsBoundaryCheck:
    """Test the new _check_within_boundaries method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.np = DotsCore(
            init_size=512,
            colour_1=(255, 255, 0),
            colour_2=(0, 0, 255),
            bg_colour=(0, 0, 0),
            min_point_radius=10,
            max_point_radius=20,
            attempts_limit=100
        )

    def test_check_within_boundaries_valid_point(self):
        """Test _check_within_boundaries with valid point."""
        point = (100, 100, 10)  # x, y, radius
        assert self.np._check_within_boundaries(point) is True

    def test_check_within_boundaries_outside_left(self):
        """Test _check_within_boundaries with point outside left boundary."""
        point = (5, 100, 10)  # x - radius = -5 < 0
        assert self.np._check_within_boundaries(point) is False

    def test_check_within_boundaries_outside_top(self):
        """Test _check_within_boundaries with point outside top boundary."""
        point = (100, 5, 10)  # y - radius = -5 < 0
        assert self.np._check_within_boundaries(point) is False

    def test_check_within_boundaries_outside_right(self):
        """Test _check_within_boundaries with point outside right boundary."""
        point = (510, 100, 10)  # x + radius = 520 > 512
        assert self.np._check_within_boundaries(point) is False

    def test_check_within_boundaries_outside_bottom(self):
        """Test _check_within_boundaries with point outside bottom boundary."""
        point = (100, 510, 10)  # y + radius = 520 > 512
        assert self.np._check_within_boundaries(point) is False

    def test_check_within_boundaries_edge_case(self):
        """Test _check_within_boundaries with point exactly on boundary.

        A dot must leave the outermost pixel ring (index 0 and init_size - 1)
        untouched: one that paints the edge row looks the same as one the canvas
        has cut off, which is the artefact reported in the JOSS review.
        """
        point = (10, 10, 10)  # x - radius = 0, y - radius = 0 (paints pixel 0)
        assert self.np._check_within_boundaries(point) is False

        point = (502, 502, 10)  # x + radius = 512, past the last pixel
        assert self.np._check_within_boundaries(point) is False

        point = (501, 501, 10)  # x + radius = 511, paints the last pixel column
        assert self.np._check_within_boundaries(point) is False

        # Test points just inside the boundary
        point = (11, 11, 10)  # x - radius = 1, y - radius = 1 (inside boundary)
        assert self.np._check_within_boundaries(point) is True

        point = (500, 500, 10)  # x + radius = 510, one clear pixel of margin
        assert self.np._check_within_boundaries(point) is True

    def test_check_within_boundaries_rounds_outwards(self):
        """Fractional bounds must round outwards, not truncate.

        A dot at x - radius == 0.5 passed the old strict "> 0" test but PIL still
        paints pixel column 0, so the dot appeared clipped.
        """
        point = (10.5, 100, 10)  # x - radius = 0.5 -> paints column 0
        assert self.np._check_within_boundaries(point) is False

        point = (501.5, 100, 10)  # x + radius = 511.5 -> paints column 511
        assert self.np._check_within_boundaries(point) is False


class TestEqualizeAreasBoundaries:
    """equalize_areas must not grow dots past the edge of the canvas.

    Regression tests for the artefact reported in JOSS review
    openjournals/joss-reviews#10532 by @et22: equalized ANS images contained
    dots clipped by the image border. equalize_areas grew the radii of the
    smaller-area colour in a loop but only re-checked overlap afterwards, never
    the canvas bounds -- unlike fix_total_area, scale_total_area and
    scale_by_factor, which all validated both.
    """

    def setup_method(self):
        self.core = DotsCore(
            init_size=512,
            colour_1=(255, 255, 0),
            colour_2=(0, 0, 255),
            bg_colour=(0, 0, 0),
            min_point_radius=10,
            max_point_radius=20,
            attempts_limit=100,
        )

    def test_raises_instead_of_growing_out_of_bounds(self):
        """A dot that would be pushed off-canvas raises rather than being clipped."""
        # colour_2 sits against the top-left corner with almost no room to grow;
        # colour_1 has a far larger area, so equalization must inflate colour_2.
        point_array = [
            ((256, 256, 60), "colour_1"),
            ((20, 20, 5), "colour_2"),
        ]
        with pytest.raises(PointLayoutError):
            self.core.equalize_areas(point_array)

    def test_equalized_points_stay_within_boundaries(self):
        """When equalization succeeds, every dot is still fully on the canvas."""
        point_array = [
            ((256, 150, 30), "colour_1"),
            ((256, 350, 20), "colour_2"),
        ]
        result = self.core.equalize_areas(point_array)
        for point, _colour in result:
            assert self.core._check_within_boundaries(point), (
                f"Equalized point {point} falls outside the canvas"
            )

    def test_does_not_mutate_input(self):
        """Equalizing returns a new array and leaves the caller's copy intact."""
        point_array = [
            ((256, 150, 30), "colour_1"),
            ((256, 350, 20), "colour_2"),
        ]
        original = list(point_array)
        self.core.equalize_areas(point_array)
        assert point_array == original

    def test_gives_up_instead_of_looping_forever(self):
        """Areas that cannot converge raise rather than hanging the run.

        Each pass grows every dot of the smaller colour by a whole pixel, so the
        areas can leapfrog the tolerance and oscillate indefinitely.
        """
        self.core.equalize_increment_limit = 5
        point_array = [
            ((256, 256, 200), "colour_1"),
            ((100, 100, 1), "colour_2"),
        ]
        with pytest.raises(PointLayoutError):
            self.core.equalize_areas(point_array)
