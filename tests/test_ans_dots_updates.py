"""Tests for updated cogstim.generators.dots_ans module."""

import pytest
from unittest.mock import patch, MagicMock, call

from cogstim.generators.dots_ans import DotsANSGenerator, GENERAL_CONFIG, TerminalPointLayoutError
from cogstim.helpers.constants import ANS_EASY_RATIOS, ANS_HARD_RATIOS


class TestPointsGeneratorRatiosMode:
    """Test the new ratios functionality in DotsANSGenerator."""

    def test_ratios_easy(self):
        """Test that ratios='easy' uses ANS_EASY_RATIOS."""
        config = {
            **GENERAL_CONFIG,
            "train_num": 1,
            "test_num": 1,
            "output_dir": "/tmp/test",
            "ratios": "easy",
            "ONE_COLOUR": False,
            "min_point_num": 1,
            "max_point_num": 10,
        }
        
        with patch('cogstim.generators.dots_ans.os.makedirs'):
            generator = DotsANSGenerator(config)
            assert generator.ratios == ANS_EASY_RATIOS

    def test_ratios_hard(self):
        """Test that ratios='hard' uses ANS_HARD_RATIOS."""
        config = {
            **GENERAL_CONFIG,
            "train_num": 1,
            "test_num": 1,
            "output_dir": "/tmp/test",
            "ratios": "hard",
            "ONE_COLOUR": False,
            "min_point_num": 1,
            "max_point_num": 10,
        }
        
        with patch('cogstim.generators.dots_ans.os.makedirs'):
            generator = DotsANSGenerator(config)
            assert generator.ratios == ANS_HARD_RATIOS

    def test_ratios_all(self):
        """Test that ratios='all' uses both easy and hard ratios."""
        config = {
            **GENERAL_CONFIG,
            "train_num": 1,
            "test_num": 1,
            "output_dir": "/tmp/test",
            "ratios": "all",
            "ONE_COLOUR": False,
            "min_point_num": 1,
            "max_point_num": 10,
        }
        
        with patch('cogstim.generators.dots_ans.os.makedirs'):
            generator = DotsANSGenerator(config)
            expected_ratios = ANS_EASY_RATIOS + ANS_HARD_RATIOS
            assert generator.ratios == expected_ratios

    def test_ratios_all(self):
        """Test that ratios='all' uses both easy and hard ratios."""
        config = {
            **GENERAL_CONFIG,
            "train_num": 1,
            "test_num": 1,
            "output_dir": "/tmp/test",
            "ratios": "all",
            "ONE_COLOUR": False,
            "min_point_num": 1,
            "max_point_num": 10,
        }

        with patch('cogstim.generators.dots_ans.os.makedirs'):
            generator = DotsANSGenerator(config)
            expected_ratios = ANS_EASY_RATIOS + ANS_HARD_RATIOS
            assert generator.ratios == expected_ratios

    def test_ratios_invalid_raises_error(self):
        """Test that invalid ratios raises ValueError."""
        config = {
            **GENERAL_CONFIG,
            "train_num": 1,
            "test_num": 1,
            "output_dir": "/tmp/test",
            "ratios": "invalid",
            "ONE_COLOUR": False,
            "min_point_num": 1,
            "max_point_num": 10,
        }
        
        with patch('cogstim.generators.dots_ans.os.makedirs'):
            with pytest.raises(ValueError, match="Invalid ratio mode: invalid"):
                DotsANSGenerator(config)

    def test_legacy_easy_flag_precedence(self):
        """Test that explicit ratios takes precedence over legacy EASY flag."""
        config = {
            **GENERAL_CONFIG,
            "train_num": 1,
            "test_num": 1,
            "output_dir": "/tmp/test",
            "ratios": "hard",  # Explicit ratios
            "EASY": True,  # Legacy flag
            "ONE_COLOUR": False,
            "min_point_num": 1,
            "max_point_num": 10,
        }
        
        with patch('cogstim.generators.dots_ans.os.makedirs'):
            generator = DotsANSGenerator(config)
            # Should use hard ratios despite EASY=True
            assert generator.ratios == ANS_HARD_RATIOS


class TestPointsGeneratorOneColourMode:
    """Test one-colour mode functionality."""

    def test_one_colour_mode_positions(self):
        """Test that one-colour mode generates correct positions."""
        config = {
            **GENERAL_CONFIG,
            "train_num": 1,
            "test_num": 1,
            "output_dir": "/tmp/test",
            "ratios": "all",
            "ONE_COLOUR": True,
            "min_point_num": 1,
            "max_point_num": 5,
        }
        
        with patch('cogstim.generators.dots_ans.os.makedirs'):
            generator = DotsANSGenerator(config)
            positions = generator.get_positions()
            
            # Should generate single counts, ignoring second value
            expected = [(1, 0), (2, 0), (3, 0), (4, 0), (5, 0)]
            assert positions == expected

    def test_one_colour_mode_generate_images(self):
        """Test that one-colour mode generates correct number of images."""
        config = {
            **GENERAL_CONFIG,
            "train_num": 2,
            "test_num": 2,
            "output_dir": "/tmp/test",
            "ratios": "all",
            "ONE_COLOUR": True,
            "min_point_num": 1,
            "max_point_num": 3,
        }
        
        with patch('cogstim.generators.dots_ans.os.makedirs'):
            generator = DotsANSGenerator(config)
            positions = generator.get_positions()
            
            # One-colour mode: multiplier = 1, positions = 3
            # Total = (train_num + test_num) * 3 * 1 = (2 + 2) * 3 * 1 = 12
            multiplier = 1
            total_images = (generator.train_num + generator.test_num) * len(positions) * multiplier
            assert total_images == 12

    def test_two_colour_mode_generate_images(self):
        """Test that two-colour mode generates correct number of images."""
        config = {
            **GENERAL_CONFIG,
            "train_num": 2,
            "test_num": 2,
            "output_dir": "/tmp/test",
            "ratios": "all",
            "ONE_COLOUR": False,
            "min_point_num": 1,
            "max_point_num": 3,
        }
        
        with patch('cogstim.generators.dots_ans.os.makedirs'):
            generator = DotsANSGenerator(config)
            positions = generator.get_positions()
            
            # Two-colour mode: multiplier = 4 (both orders + equalized/non-equalized)
            multiplier = 4
            total_images = (generator.train_num + generator.test_num) * len(positions) * multiplier
            assert total_images > 0  # Should generate some images


class TestPointsGeneratorErrorHandling:
    """Test error handling in PointsGenerator."""

    def test_terminal_point_layout_error(self):
        """Test that TerminalPointLayoutError is raised when attempts limit is exceeded."""
        config = {
            **GENERAL_CONFIG,
            "train_num": 1,
            "test_num": 1,
            "output_dir": "/tmp/test",
            "ratios": "all",
            "attempts_limit": 1,  # Very low limit
            "ONE_COLOUR": True,
            "min_point_num": 1,
            "max_point_num": 1,
        }
        
        with patch('cogstim.generators.dots_ans.os.makedirs'):
            generator = DotsANSGenerator(config)
            
            # Mock create_and_save_once to always raise PointLayoutError
            from cogstim.helpers.dots_core import PointLayoutError
            with patch.object(generator, 'create_and_save_once', side_effect=PointLayoutError("Too many attempts")):
                with pytest.raises(TerminalPointLayoutError):
                    generator.create_and_save(1, 0, False, "test")

    def test_create_image_one_colour_mode(self):
        """Test create_image method in one-colour mode."""
        config = {
            **GENERAL_CONFIG,
            "train_num": 1,
            "test_num": 1,
            "output_dir": "/tmp/test",
            "ratios": "all",
            "ONE_COLOUR": True,
            "colour_1": "yellow",
            "min_point_num": 1,
            "max_point_num": 1,
        }
        
        with patch('cogstim.generators.dots_ans.os.makedirs'):
            generator = DotsANSGenerator(config)
            
            # Mock DotsCore
            with patch('cogstim.generators.dots_ans.DotsCore') as mock_create:
                mock_np = MagicMock()
                mock_create.return_value = mock_np
                mock_np.design_n_points.return_value = []
                mock_np.draw_points.return_value = MagicMock()
                
                result = generator.create_image(2, 0, False)
                
                # Should call design_n_points twice (once for each colour, even in one-colour mode)
                assert mock_np.design_n_points.call_count == 2
                # Should not call equalize_areas in one-colour mode
                mock_np.equalize_areas.assert_not_called()

    def test_create_image_two_colour_mode_equalized(self):
        """Test create_image method in two-colour mode with equalization."""
        config = {
            **GENERAL_CONFIG,
            "train_num": 1,
            "test_num": 1,
            "output_dir": "/tmp/test",
            "ratios": "all",
            "ONE_COLOUR": False,
            "colour_1": "yellow",
            "colour_2": "blue",
            "min_point_num": 1,
            "max_point_num": 1,
        }
        
        with patch('cogstim.generators.dots_ans.os.makedirs'):
            generator = DotsANSGenerator(config)
            
            # Mock DotsCore
            with patch('cogstim.generators.dots_ans.DotsCore') as mock_create:
                mock_np = MagicMock()
                mock_create.return_value = mock_np
                mock_np.design_n_points.return_value = []
                mock_np.equalize_areas.return_value = []
                mock_np.draw_points.return_value = MagicMock()
                
                result = generator.create_image(2, 3, True)
                
                # Should call design_n_points twice for both colours
                assert mock_np.design_n_points.call_count == 2
                # Should call equalize_areas when equalized=True
                mock_np.equalize_areas.assert_called_once()


class TestPointsGeneratorDirectorySetup:
    """Test directory setup functionality."""

    def test_setup_directories_one_colour(self):
        """Test directory setup for one-colour mode."""
        config = {
            **GENERAL_CONFIG,
            "train_num": 1,
            "test_num": 1,
            "output_dir": "/tmp/test",
            "ratios": "all",
            "ONE_COLOUR": True,
            "colour_1": "yellow",
        }
        
        with patch('cogstim.generators.dots_ans.os.makedirs') as mock_makedirs:
            generator = DotsANSGenerator(config)
            
            # Should create main directory, train/yellow, and test/yellow
            import os
            expected_calls = [
                call("/tmp/test", exist_ok=True),
                call(os.path.join("/tmp/test", "train", "yellow"), exist_ok=True),
                call(os.path.join("/tmp/test", "test", "yellow"), exist_ok=True),
            ]
            mock_makedirs.assert_has_calls(expected_calls, any_order=True)

    def test_setup_directories_two_colour(self):
        """Test directory setup for two-colour mode."""
        config = {
            **GENERAL_CONFIG,
            "train_num": 1,
            "test_num": 1,
            "output_dir": "/tmp/test",
            "ratios": "all",
            "ONE_COLOUR": False,
            "colour_1": "yellow",
            "colour_2": "blue",
        }
        
        with patch('cogstim.generators.dots_ans.os.makedirs') as mock_makedirs:
            generator = DotsANSGenerator(config)
            
            # Should create main directory, train/test for both colours
            import os
            expected_calls = [
                call("/tmp/test", exist_ok=True),
                call(os.path.join("/tmp/test", "train", "yellow"), exist_ok=True),
                call(os.path.join("/tmp/test", "test", "yellow"), exist_ok=True),
                call(os.path.join("/tmp/test", "train", "blue"), exist_ok=True),
                call(os.path.join("/tmp/test", "test", "blue"), exist_ok=True),
            ]
            mock_makedirs.assert_has_calls(expected_calls, any_order=True)
