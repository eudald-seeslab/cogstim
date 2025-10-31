"""Tests for cogstim.match_to_sample module."""

import tempfile
from unittest.mock import MagicMock, patch

from cogstim.match_to_sample import (
    MatchToSampleGenerator,
    GENERAL_CONFIG as MTS_GENERAL_CONFIG,
    try_build_random_pair,
    generate_pair,
    save_pair_with_basename,
)
from cogstim.config import MTS_EASY_RATIOS, MTS_HARD_RATIOS
from cogstim.mts_helpers.planner import GenerationPlan
from cogstim.mts_helpers.factory import create_numberpoints_image, generate_random_points
from cogstim.mts_helpers.geometry import equalize_pair as geometry_equalize_pair
from cogstim.mts_helpers.io import save_image_pair


class TestMatchToSampleGenerator:
    """Test the MatchToSampleGenerator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            **MTS_GENERAL_CONFIG,
            "train_num": 1,
            "test_num": 1,
            "output_dir": "/tmp/test",
            "min_point_num": 1,
            "max_point_num": 5,
            "ratios": "easy",
        }

    def test_init_with_easy_ratios(self):
        """Test generator initialization with easy ratios."""
        with patch('cogstim.match_to_sample.os.makedirs'):
            generator = MatchToSampleGenerator(self.config)
            assert generator.ratios == MTS_EASY_RATIOS

    def test_init_with_hard_ratios(self):
        """Test generator initialization with hard ratios."""
        config = {**self.config, "ratios": "hard"}
        with patch('cogstim.match_to_sample.os.makedirs'):
            generator = MatchToSampleGenerator(config)
            assert generator.ratios == MTS_HARD_RATIOS

    def test_init_with_all_ratios(self):
        """Test generator initialization with all ratios."""
        config = {**self.config, "ratios": "all"}
        with patch('cogstim.match_to_sample.os.makedirs'):
            generator = MatchToSampleGenerator(config)
            expected_ratios = MTS_EASY_RATIOS + MTS_HARD_RATIOS
            assert generator.ratios == expected_ratios

    def test_get_positions(self):
        """Test compute_positions via GenerationPlan."""
        plan = GenerationPlan(self.config["ratios"], self.config["min_point_num"], self.config["max_point_num"], self.config["train_num"]).build()
        positions = plan.compute_positions()
        assert isinstance(positions, list)
        for n, m in positions:
            assert isinstance(n, int)
            assert isinstance(m, int)
            assert n >= self.config["min_point_num"]
            assert n <= self.config["max_point_num"]
            assert m >= self.config["min_point_num"]
            assert m <= self.config["max_point_num"]
            if n != m:
                ratio = n / m
                assert ratio in plan.ratios or (1/ratio) in plan.ratios

    def test_generate_images(self):
        """Test generate_images method."""
        with patch('cogstim.match_to_sample.os.makedirs'), \
             patch.object(MatchToSampleGenerator, 'create_and_save') as mock_create:
            generator = MatchToSampleGenerator(self.config)
            generator.generate_images()
            assert mock_create.call_count > 0

    def test_create_and_save_equalized_pair(self):
        """Test create_and_save method for equalized pairs."""
        with patch('cogstim.match_to_sample.os.makedirs'), \
             patch.object(MatchToSampleGenerator, 'create_image_pair') as mock_create, \
             patch.object(MatchToSampleGenerator, 'save_image_pair') as mock_save:
            generator = MatchToSampleGenerator(self.config)
            generator.create_and_save(3, 4, True, "test_tag")
            mock_create.assert_called_once_with(3, 4, True)
            mock_save.assert_called_once()

    def test_create_and_save_random_pair(self):
        """Test create_and_save method for random pairs."""
        with patch('cogstim.match_to_sample.os.makedirs'), \
             patch.object(MatchToSampleGenerator, 'create_image_pair') as mock_create, \
             patch.object(MatchToSampleGenerator, 'save_image_pair') as mock_save:
            generator = MatchToSampleGenerator(self.config)
            generator.create_and_save(3, 4, False, "test_tag")
            mock_create.assert_called_once_with(3, 4, False)
            mock_save.assert_called_once()


class TestHelperFunctions:
    """Test helper functions in match_to_sample module."""

    def test_create_numberpoints_image(self):
        """Test create_numberpoints_image function."""
        img, np_obj = create_numberpoints_image(
            bg_colour="white",
            dot_colour="black",
            min_radius=5,
            max_radius=15,
            attempts_limit=100
        )
        assert img is not None
        assert np_obj is not None
        assert np_obj.min_point_radius == 5
        assert np_obj.max_point_radius == 15
        assert np_obj.attempts_limit == 100

    def test_generate_random_points(self):
        """Test generate_random_points function."""
        img, np_obj = create_numberpoints_image(
            bg_colour="white",
            dot_colour="black",
            min_radius=5,
            max_radius=15,
            attempts_limit=100
        )
        with patch.object(np_obj, 'design_n_points') as mock_design:
            mock_design.return_value = [((100, 100, 10), "colour_1")]
            points = generate_random_points(np_obj, 3)
            mock_design.assert_called_once_with(3, "colour_1")
            assert points == [((100, 100, 10), "colour_1")]

    def test_equalize_total_area_success(self):
        """Test equalize_pair (geometry) with successful equalization."""
        s_np = MagicMock()
        m_np = MagicMock()
        call_count = {'s': 0, 'm': 0}
        def s_area_side_effect(points, colour):
            call_count['s'] += 1
            return 1000 if call_count['s'] == 1 else 1200
        def m_area_side_effect(points, colour):
            call_count['m'] += 1
            return 1200
        s_np.compute_area.side_effect = s_area_side_effect
        m_np.compute_area.side_effect = m_area_side_effect
        s_np._check_within_boundaries.return_value = True
        s_np._check_points_not_overlapping.return_value = True
        s_points = [((100, 100, 10), "colour_1")]
        m_points = [((200, 200, 15), "colour_1")]
        result = geometry_equalize_pair(
            s_np, s_points, m_np, m_points,
            rel_tolerance=0.01, abs_tolerance=10, attempts_limit=100
        )
        assert result[0] is True
        assert s_np.compute_area.call_count >= 2
        assert m_np.compute_area.call_count >= 2

    def test_equalize_total_area_failure_boundary(self):
        """Test equalize_pair with boundary violation."""
        s_np = MagicMock()
        m_np = MagicMock()
        s_np.compute_area.side_effect = lambda points, colour: 1000
        m_np.compute_area.side_effect = lambda points, colour: 1500
        s_np._check_within_boundaries.return_value = False
        s_points = [((100, 100, 10), "colour_1")]
        m_points = [((200, 200, 15), "colour_1")]
        result = geometry_equalize_pair(
            s_np, s_points, m_np, m_points,
            rel_tolerance=0.01, abs_tolerance=10, attempts_limit=100
        )
        assert result[0] is False

    def test_equalize_total_area_failure_overlap(self):
        """Test equalize_pair with overlap violation."""
        s_np = MagicMock()
        m_np = MagicMock()
        s_np.compute_area.side_effect = lambda points, colour: 1000
        m_np.compute_area.side_effect = lambda points, colour: 1500
        s_np._check_within_boundaries.return_value = True
        s_np._check_points_not_overlapping.return_value = False
        s_points = [((100, 100, 10), "colour_1")]
        m_points = [((200, 200, 15), "colour_1")]
        result = geometry_equalize_pair(
            s_np, s_points, m_np, m_points,
            rel_tolerance=0.01, abs_tolerance=10, attempts_limit=100
        )
        assert result[0] is False

    def test_equalize_total_area_failure_attempts_limit(self):
        """Test equalize_pair attempts limit exceeded."""
        s_np = MagicMock()
        m_np = MagicMock()
        s_np.compute_area.return_value = 1000
        m_np.compute_area.return_value = 1500
        s_np._check_within_boundaries.return_value = True
        s_np._check_points_not_overlapping.return_value = True
        s_points = [((100, 100, 10), "colour_1")]
        m_points = [((200, 200, 15), "colour_1")]
        result = geometry_equalize_pair(
            s_np, s_points, m_np, m_points,
            rel_tolerance=0.01, abs_tolerance=10, attempts_limit=2
        )
        assert result[0] is False

    def test_save_image_pair(self):
        """Test save_image_pair function."""
        s_np = MagicMock()
        m_np = MagicMock()
        s_points = [((100, 100, 10), "colour_1")]
        m_points = [((200, 200, 15), "colour_1")]
        with patch('cogstim.match_to_sample.os.path.join') as mock_join, \
             patch('builtins.open', MagicMock()):
            mock_join.side_effect = ["/tmp/test_s.png", "/tmp/test_m.png"]
            save_image_pair(s_np, s_points, m_np, m_points, "/tmp", "test")
            s_np.draw_points.assert_called_once_with(s_points)
            m_np.draw_points.assert_called_once_with(m_points)
            s_np.img.save.assert_called_once_with("/tmp/test_s.png")
            m_np.img.save.assert_called_once_with("/tmp/test_m.png")

    def test_try_build_random_pair_success(self):
        """Test try_build_random_pair function with successful pair creation."""
        with patch('cogstim.match_to_sample._create_np_image') as mock_create, \
             patch('cogstim.match_to_sample.generate_random_points') as mock_generate:
            mock_img = MagicMock()
            mock_np = MagicMock()
            mock_create.return_value = (mock_img, mock_np)
            mock_generate.side_effect = [
                [((100, 100, 10), "colour_1")],
                [((200, 200, 15), "colour_1")],
            ]
            result = try_build_random_pair(
                n_first=2, n_second=3,
                bg_colour="white", dot_colour="black",
                min_radius=5, max_radius=15,
                attempts_limit=100,
                error_label="test"
            )
            assert result is not None
            assert len(result) == 4
            assert mock_create.call_count == 2
            assert mock_generate.call_count == 2

    def test_try_build_random_pair_failure(self):
        """Test try_build_random_pair function with failure."""
        from cogstim.dots_core import PointLayoutError
        with patch('cogstim.match_to_sample._create_np_image',
                   side_effect=PointLayoutError("Too many attempts")):
            result = try_build_random_pair(
                n_first=2, n_second=3,
                bg_colour="white", dot_colour="black",
                min_radius=5, max_radius=15,
                attempts_limit=100,
                error_label="test"
            )
            assert result is None

    def test_generate_pair_without_equalization(self):
        """Test generate_pair function without equalization."""
        with patch('cogstim.match_to_sample.try_build_random_pair') as mock_try:
            mock_try.return_value = (MagicMock(), [], MagicMock(), [])
            args = MagicMock()
            args.background_colour = "white"
            args.dot_colour = "black"
            args.min_radius = 5
            args.max_radius = 15
            args.attempts_limit = 100
            pair, success = generate_pair(2, 3, args, "test", equalize=False)
            assert pair is not None
            assert success is None
            mock_try.assert_called_once()

    def test_generate_pair_with_equalization_success(self):
        """Test generate_pair function with successful equalization."""
        with patch('cogstim.match_to_sample.try_build_random_pair') as mock_try, \
             patch('cogstim.match_to_sample._equalize_geom') as mock_equalize:
            mock_try.return_value = (MagicMock(), [], MagicMock(), [])
            mock_equalize.return_value = True
            args = MagicMock()
            args.background_colour = "white"
            args.dot_colour = "black"
            args.min_radius = 5
            args.max_radius = 15
            args.attempts_limit = 100
            args.tolerance = 0.01
            pair, success = generate_pair(2, 3, args, "test", equalize=True)
            assert pair is not None
            assert success is True
            mock_equalize.assert_called_once()

    def test_generate_pair_with_equalization_failure(self):
        """Test generate_pair function with failed equalization."""
        with patch('cogstim.match_to_sample.try_build_random_pair') as mock_try, \
             patch('cogstim.match_to_sample._equalize_geom') as mock_equalize:
            mock_try.return_value = (MagicMock(), [], MagicMock(), [])
            mock_equalize.return_value = False
            args = MagicMock()
            args.background_colour = "white"
            args.dot_colour = "black"
            args.min_radius = 5
            args.max_radius = 15
            args.attempts_limit = 100
            args.tolerance = 0.01
            pair, success = generate_pair(2, 3, args, "test", equalize=True)
            assert pair is not None
            assert success is False

    def test_save_pair_with_basename(self):
        """Test save_pair_with_basename function."""
        s_np = MagicMock()
        s_points = [((100, 100, 10), "colour_1")]
        m_np = MagicMock()
        m_points = [((200, 200, 15), "colour_1")]
        pair = (s_np, s_points, m_np, m_points)
        with patch('cogstim.mts_helpers.io.save_image_pair') as mock_save:
            save_pair_with_basename(pair, "/tmp", "test")
            mock_save.assert_called_once_with(s_np, s_points, m_np, m_points, "/tmp", "test")


class TestMatchToSampleIntegration:
    """Integration tests for match_to_sample module."""

    def test_full_generation_workflow(self):
        """Test the complete generation workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                **MTS_GENERAL_CONFIG,
                "train_num": 1,
            "test_num": 1,
                "output_dir": tmpdir,
                "min_point_num": 2,
                "max_point_num": 3,
                "ratios": "easy",
            }
            
            with patch('cogstim.match_to_sample.os.makedirs'):
                generator = MatchToSampleGenerator(config)
                
                # Mock the actual image creation to avoid file I/O
                with patch.object(generator, 'create_image_pair') as mock_create, \
                     patch.object(generator, 'save_image_pair') as mock_save:
                    
                    generator.generate_images()
                    
                    # Should have called create_image_pair and save_image_pair
                    assert mock_create.call_count > 0
                    assert mock_save.call_count > 0
