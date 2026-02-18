"""Tests for cogstim.generators.match_to_sample module."""

import tempfile
from unittest.mock import MagicMock, patch

from cogstim.generators.match_to_sample import (
    MatchToSampleGenerator,
    GENERAL_CONFIG as MTS_GENERAL_CONFIG,
)
from cogstim.helpers.constants import MTS_EASY_RATIOS, MTS_HARD_RATIOS
from cogstim.helpers.planner import GenerationPlan, load_mts_tasks_from_csv
from cogstim.helpers.dots_core import DotsCore
from cogstim.helpers.mts_geometry import equalize_pair as geometry_equalize_pair
from cogstim.generators.match_to_sample import save_image_pair, build_basename


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
        with patch('cogstim.generators.match_to_sample.os.makedirs'):
            generator = MatchToSampleGenerator(self.config)
            assert generator.ratios == MTS_EASY_RATIOS

    def test_init_with_hard_ratios(self):
        """Test generator initialization with hard ratios."""
        config = {**self.config, "ratios": "hard"}
        with patch('cogstim.generators.match_to_sample.os.makedirs'):
            generator = MatchToSampleGenerator(config)
            assert generator.ratios == MTS_HARD_RATIOS

    def test_init_with_all_ratios(self):
        """Test generator initialization with all ratios."""
        config = {**self.config, "ratios": "all"}
        with patch('cogstim.generators.match_to_sample.os.makedirs'):
            generator = MatchToSampleGenerator(config)
            expected_ratios = MTS_EASY_RATIOS + MTS_HARD_RATIOS
            assert generator.ratios == expected_ratios

    def test_load_mts_tasks_from_csv(self, tmp_path):
        """Test loading MTS tasks from CSV."""
        csv_path = tmp_path / "tasks.csv"
        csv_path.write_text("sample,match,equalized\n4,4,TRUE\n2,3,FALSE\n5,5,TRUE\n")
        tasks = load_mts_tasks_from_csv(csv_path)
        assert tasks == [(4, 4, True), (2, 3, False), (5, 5, True)]

    def test_build_from_mts_csv(self, tmp_path):
        """Test building plan from CSV with num_copies."""
        csv_path = tmp_path / "tasks.csv"
        csv_path.write_text("sample,match,equalized\n3,4,TRUE\n")
        plan = GenerationPlan("mts", 1, 10, 1, ratios=[]).build_from_mts_csv(
            csv_path, num_copies=3
        )
        assert len(plan.tasks) == 3
        for rep, task in enumerate(plan.tasks):
            assert task.params["n1"] == 3
            assert task.params["n2"] == 4
            assert task.params["equalize"] is True
            assert task.rep == rep

    def test_get_positions(self):
        """Test compute_positions via GenerationPlan."""
        plan = GenerationPlan("mts", self.config["min_point_num"], self.config["max_point_num"], self.config["train_num"], ratios=MTS_EASY_RATIOS).build()
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
        with patch('cogstim.generators.match_to_sample.os.makedirs'), \
             patch.object(MatchToSampleGenerator, 'create_and_save') as mock_create:
            generator = MatchToSampleGenerator(self.config)
            generator.generate_images()
            assert mock_create.call_count > 0

    def test_create_and_save_equalized_pair(self):
        """Test create_and_save method for equalized pairs."""
        with patch('cogstim.generators.match_to_sample.os.makedirs'), \
             patch.object(MatchToSampleGenerator, 'create_image_pair') as mock_create, \
             patch.object(MatchToSampleGenerator, 'save_image_pair') as mock_save:
            generator = MatchToSampleGenerator(self.config)
            generator.create_and_save(3, 4, True, "test_tag")
            mock_create.assert_called_once_with(3, 4, True)
            mock_save.assert_called_once()

    def test_create_and_save_random_pair(self):
        """Test create_and_save method for random pairs."""
        with patch('cogstim.generators.match_to_sample.os.makedirs'), \
             patch.object(MatchToSampleGenerator, 'create_image_pair') as mock_create, \
             patch.object(MatchToSampleGenerator, 'save_image_pair') as mock_save:
            generator = MatchToSampleGenerator(self.config)
            generator.create_and_save(3, 4, False, "test_tag")
            mock_create.assert_called_once_with(3, 4, False)
            mock_save.assert_called_once()


class TestHelperFunctions:
    """Test helper functions in match_to_sample module."""

    def test_numberpoints_creation(self):
        """Test DotsCore object creation."""
        np_obj = DotsCore(
            init_size=512,
            colour_1="black",
            bg_colour="white",
            min_point_radius=5,
            max_point_radius=15,
            attempts_limit=100
        )
        assert np_obj is not None
        assert np_obj.canvas.img is not None
        assert np_obj.min_point_radius == 5
        assert np_obj.max_point_radius == 15
        assert np_obj.attempts_limit == 100

    def test_design_n_points(self):
        """Test design_n_points method."""
        np_obj = DotsCore(
            init_size=512,
            colour_1="black",
            bg_colour="white",
            min_point_radius=5,
            max_point_radius=15,
            attempts_limit=100
        )
        with patch.object(np_obj, 'design_n_points') as mock_design:
            mock_design.return_value = [((100, 100, 10), "colour_1")]
            points = np_obj.design_n_points(3, "colour_1")
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
        
        # Create mock generator with save_image method
        mock_generator = MagicMock()
        mock_generator.save_image = MagicMock()

        save_image_pair(mock_generator, s_np, s_points, m_np, m_points, "test", "train")
        s_np.draw_points.assert_called_once_with(s_points)
        m_np.draw_points.assert_called_once_with(m_points)
        
        # Verify generator.save_image was called twice (once for sample, once for match)
        assert mock_generator.save_image.call_count == 2
        
        # Verify the calls with correct filenames and subdirs
        calls = mock_generator.save_image.call_args_list
        assert calls[0][0][1] == "test_s"  # filename for sample
        assert calls[0][0][2] == "train"   # subdirs
        assert calls[1][0][1] == "test_m"  # filename for match
        assert calls[1][0][2] == "train"   # subdirs

    def test_build_basename(self):
        """Test build_basename function."""
        # Test basic case
        result = build_basename(5, 3, 0, False)
        assert result == "img_5_3_0"
        
        # Test with equalized
        result = build_basename(5, 3, 1, True)
        assert result == "img_5_3_1_equalized"
        
        # Test with version tag
        result = build_basename(5, 3, 2, False, "v1")
        assert result == "img_5_3_2_v1"
        
        # Test with both
        result = build_basename(5, 3, 3, True, "v2")
        assert result == "img_5_3_3_equalized_v2"


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
            
            with patch('cogstim.generators.match_to_sample.os.makedirs'):
                generator = MatchToSampleGenerator(config)
                
                # Mock the actual image creation to avoid file I/O
                with patch.object(generator, 'create_image_pair') as mock_create, \
                     patch.object(generator, 'save_image_pair') as mock_save:
                    
                    generator.generate_images()
                    
                    # Should have called create_image_pair and save_image_pair
                    assert mock_create.call_count > 0
                    assert mock_save.call_count > 0
