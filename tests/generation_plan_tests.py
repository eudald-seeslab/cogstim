"""Tests for the unified GenerationPlan across all modes."""

import pytest
from cogstim.mts_helpers.planner import GenerationPlan, resolve_ratios
from cogstim.config import ANS_EASY_RATIOS, ANS_HARD_RATIOS, MTS_EASY_RATIOS, MTS_HARD_RATIOS


class TestUnifiedGenerationPlan:
    """Test unified GenerationPlan for all generation modes."""
    
    def test_ans_mode(self):
        """Test ANS mode generates 4 variants per position pair."""
        plan = GenerationPlan(
            mode="ans",
            ratios=ANS_EASY_RATIOS,
            min_point_num=1,
            max_point_num=5,
            num_repeats=1,
            easy_ratios=ANS_EASY_RATIOS,
            hard_ratios=ANS_HARD_RATIOS
        ).build()
        
        positions = plan.compute_positions()
        # Each position should generate 4 tasks (both orders x 2 equalization states)
        expected_tasks = len(positions) * 4 * 1  # positions * variants * repeats
        assert len(plan.tasks) == expected_tasks
        
        # Verify task structure
        for task in plan.tasks:
            assert "n1" in task
            assert "n2" in task
            assert "rep" in task
            assert "equalize" in task
    
    def test_mts_mode(self):
        """Test MTS mode generates 6 variants per position pair."""
        plan = GenerationPlan(
            mode="mts",
            ratios=MTS_EASY_RATIOS,
            min_point_num=2,
            max_point_num=6,
            num_repeats=1
        ).build()
        
        positions = plan.compute_positions()
        # Each position should generate 6 tasks (4 + 2 equal pairs)
        expected_tasks = len(positions) * 6 * 1
        assert len(plan.tasks) == expected_tasks
    
    def test_one_colour_mode(self):
        """Test one-colour mode generates one task per count."""
        plan = GenerationPlan(
            mode="one_colour",
            min_point_num=1,
            max_point_num=5,
            num_repeats=2
        ).build()
        
        # Should generate one task per count per repeat
        expected_tasks = 5 * 2  # counts * repeats
        assert len(plan.tasks) == expected_tasks
        
        # Verify task structure
        for task in plan.tasks:
            assert task["n2"] == 0
            assert task["equalize"] is False
    
    def test_lines_mode(self):
        """Test lines mode generates tasks for all angle-stripe combinations."""
        angles = [0, 45, 90, 135]
        min_stripes = 2
        max_stripes = 5
        
        plan = GenerationPlan(
            mode="lines",
            angles=angles,
            min_stripe_num=min_stripes,
            max_stripe_num=max_stripes,
            num_repeats=3
        ).build()
        
        # Should generate one task per angle per stripe count per repeat
        stripe_counts = max_stripes - min_stripes + 1
        expected_tasks = len(angles) * stripe_counts * 3
        assert len(plan.tasks) == expected_tasks
        
        # Verify task structure
        for task in plan.tasks:
            assert "angle" in task
            assert "num_stripes" in task
            assert "rep" in task
            assert task["angle"] in angles
            assert min_stripes <= task["num_stripes"] <= max_stripes
    
    def test_shapes_mode_two_shapes(self):
        """Test shapes mode with two_shapes task type."""
        plan = GenerationPlan(
            mode="shapes",
            shapes=["circle", "star"],
            colours=["yellow"],
            min_surface=100,
            max_surface=300,
            surface_step=100,
            num_repeats=2
        ).build()
        
        # surfaces: 100, 200 (2 surfaces)
        # shapes: 2
        # colours: 1
        # repeats: 2
        expected_tasks = 2 * 2 * 1 * 2
        assert len(plan.tasks) == expected_tasks
        
        # Verify task structure
        for task in plan.tasks:
            assert "shape" in task
            assert "colour" in task
            assert "surface" in task
            assert "rep" in task
    
    def test_shapes_mode_two_colors(self):
        """Test shapes mode with two_colors task type."""
        plan = GenerationPlan(
            mode="shapes",
            shapes=["circle"],
            colours=["yellow", "blue"],
            min_surface=100,
            max_surface=200,
            surface_step=100,
            num_repeats=1
        ).build()
        
        # surfaces: 100 (1 surface)
        # shapes: 1 (circle)
        # colours: 2
        # repeats: 1
        expected_tasks = 1 * 1 * 2 * 1
        assert len(plan.tasks) == expected_tasks
    
    def test_shapes_mode_custom(self):
        """Test shapes mode with custom task type."""
        plan = GenerationPlan(
            mode="shapes",
            shapes=["circle", "square"],
            colours=["red", "green"],
            min_surface=100,
            max_surface=200,
            surface_step=100,
            num_repeats=1
        ).build()
        
        # surfaces: 1
        # shapes: 2
        # colours: 2
        # repeats: 1
        expected_tasks = 1 * 2 * 2 * 1
        assert len(plan.tasks) == expected_tasks
    
    def test_resolve_ratios_easy(self):
        """Test ratio resolution for easy mode."""
        ratios = resolve_ratios("easy", ANS_EASY_RATIOS, ANS_HARD_RATIOS)
        assert ratios == list(ANS_EASY_RATIOS)
    
    def test_resolve_ratios_hard(self):
        """Test ratio resolution for hard mode."""
        ratios = resolve_ratios("hard", ANS_EASY_RATIOS, ANS_HARD_RATIOS)
        assert ratios == list(ANS_HARD_RATIOS)
    
    def test_resolve_ratios_all(self):
        """Test ratio resolution for all mode."""
        ratios = resolve_ratios("all", ANS_EASY_RATIOS, ANS_HARD_RATIOS)
        assert ratios == list(ANS_EASY_RATIOS) + list(ANS_HARD_RATIOS)
    
    def test_resolve_ratios_invalid(self):
        """Test that invalid ratio mode raises ValueError."""
        with pytest.raises(ValueError, match="Invalid ratio mode"):
            resolve_ratios("invalid", ANS_EASY_RATIOS, ANS_HARD_RATIOS)
