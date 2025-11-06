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
        """Test _check_within_boundaries with point exactly on boundary."""
        point = (10, 10, 10)  # x - radius = 0, y - radius = 0 (on boundary)
        assert self.np._check_within_boundaries(point) is False  # Boundary is exclusive
        
        point = (502, 502, 10)  # x + radius = 512, y + radius = 512 (on boundary)
        assert self.np._check_within_boundaries(point) is False  # Boundary is exclusive
        
        # Test points just inside the boundary
        point = (11, 11, 10)  # x - radius = 1, y - radius = 1 (inside boundary)
        assert self.np._check_within_boundaries(point) is True
        
        point = (501, 501, 10)  # x + radius = 511, y + radius = 511 (inside boundary)
        assert self.np._check_within_boundaries(point) is True
