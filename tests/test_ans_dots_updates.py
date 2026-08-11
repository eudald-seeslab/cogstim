"""Tests for updated cogstim.generators.dots_ans module."""

import pytest
from unittest.mock import patch, MagicMock, call

from cogstim.generators.dots_ans import DotsANSGenerator, GENERAL_CONFIG, TerminalPointLayoutError
from cogstim.helpers.constants import ANS_EASY_RATIOS, ANS_HARD_RATIOS
from cogstim.helpers.planner import GenerationPlan, load_ans_tasks_from_csv


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
            "version_tag": "",
            "img_format": "png",
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
            "version_tag": "",
            "img_format": "png",
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
            "version_tag": "",
            "img_format": "png",
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
            "version_tag": "",
            "img_format": "png",
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
            "version_tag": "",
            "img_format": "png",
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
            "version_tag": "",
            "img_format": "png",
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
            "version_tag": "",
            "img_format": "png",
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
            "version_tag": "",
            "img_format": "png",
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
            "version_tag": "",
            "img_format": "png",
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
            "version_tag": "",
            "img_format": "png",
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
            "version_tag": "",
            "img_format": "png",
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
            "version_tag": "",
            "img_format": "png",
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
            "version_tag": "",
            "img_format": "png",
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
            "version_tag": "",
            "img_format": "png",
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


class TestSeparatedLayout:
    """Test the separated layout mode for DotsANSGenerator."""

    def _base_config(self, **overrides):
        cfg = {
            **GENERAL_CONFIG,
            "train_num": 1,
            "test_num": 0,
            "output_dir": "/tmp/test_separated",
            "ratios": "easy",
            "ONE_COLOUR": False,
            "min_point_num": 2,
            "max_point_num": 4,
            "version_tag": "",
            "img_format": "png",
            "layout": "separated",
            "gap": 40,
        }
        cfg.update(overrides)
        return cfg

    def test_create_image_separated_calls_design_with_regions(self):
        """In separated mode, design_n_points should receive region kwargs."""
        config = self._base_config()

        with patch('cogstim.generators.dots_ans.os.makedirs'):
            generator = DotsANSGenerator(config)

        with patch('cogstim.generators.dots_ans.DotsCore') as MockCore:
            mock_np = MagicMock()
            MockCore.return_value = mock_np
            mock_np.boundary_width = 5
            mock_np.design_n_points.return_value = []
            mock_np.draw_points.return_value = MagicMock()

            generator.create_image(3, 5, equalized=False)

            calls = mock_np.design_n_points.call_args_list
            assert len(calls) == 2
            for c in calls:
                assert "region" in c.kwargs and c.kwargs["region"] is not None

    def test_create_image_separated_equalized(self):
        """Equalization should be invoked in separated mode when requested."""
        config = self._base_config()

        with patch('cogstim.generators.dots_ans.os.makedirs'):
            generator = DotsANSGenerator(config)

        with patch('cogstim.generators.dots_ans.DotsCore') as MockCore:
            mock_np = MagicMock()
            MockCore.return_value = mock_np
            mock_np.boundary_width = 5
            mock_np.design_n_points.return_value = []
            mock_np.equalize_areas.return_value = []
            mock_np.draw_points.return_value = MagicMock()

            generator.create_image(3, 5, equalized=True)

            mock_np.equalize_areas.assert_called_once()

    def test_filename_contains_separated_tag(self):
        """Filenames should include '_separated' when layout is separated."""
        config = self._base_config()

        with patch('cogstim.generators.dots_ans.os.makedirs'):
            generator = DotsANSGenerator(config)

        with patch.object(generator, 'create_and_save_once') as mock_save:
            generator.create_and_save(3, 5, equalized=False, phase="train", tag=0)
            filename_arg = mock_save.call_args[0][0]
            assert "_separated" in filename_arg

    def test_filename_no_separated_tag_in_mixed(self):
        """Filenames should NOT include '_separated' when layout is mixed."""
        config = self._base_config(layout="mixed")

        with patch('cogstim.generators.dots_ans.os.makedirs'):
            generator = DotsANSGenerator(config)

        with patch.object(generator, 'create_and_save_once') as mock_save:
            generator.create_and_save(3, 5, equalized=False, phase="train", tag=0)
            filename_arg = mock_save.call_args[0][0]
            assert "_separated" not in filename_arg

    def test_mixed_layout_does_not_pass_regions(self):
        """Mixed mode should use the original circular placement (no region)."""
        config = self._base_config(layout="mixed")

        with patch('cogstim.generators.dots_ans.os.makedirs'):
            generator = DotsANSGenerator(config)

        with patch('cogstim.generators.dots_ans.DotsCore') as MockCore:
            mock_np = MagicMock()
            MockCore.return_value = mock_np
            mock_np.design_n_points.return_value = []
            mock_np.draw_points.return_value = MagicMock()

            generator.create_image(3, 5, equalized=False)

            calls = mock_np.design_n_points.call_args_list
            assert len(calls) == 2
            for c in calls:
                assert c.kwargs.get("region") is None

    def test_one_colour_ignores_separated(self):
        """One-colour mode should fall back to mixed even if layout='separated'."""
        config = self._base_config(ONE_COLOUR=True)

        with patch('cogstim.generators.dots_ans.os.makedirs'):
            generator = DotsANSGenerator(config)

        with patch('cogstim.generators.dots_ans.DotsCore') as MockCore:
            mock_np = MagicMock()
            MockCore.return_value = mock_np
            mock_np.design_n_points.return_value = []
            mock_np.draw_points.return_value = MagicMock()

            generator.create_image(3, 0, equalized=False)

            calls = mock_np.design_n_points.call_args_list
            for c in calls:
                assert c.kwargs.get("region") is None


class TestLoadAnsTasksFromCsv:
    """Test loading ANS tasks from a CSV file."""

    def test_basic_loading(self, tmp_path):
        csv_path = tmp_path / "tasks.csv"
        csv_path.write_text("n1,n2,equalized\n3,5,TRUE\n2,4,FALSE\n7,7,YES\n")
        tasks = load_ans_tasks_from_csv(csv_path)
        assert tasks == [(3, 5, True), (2, 4, False), (7, 7, True)]

    def test_missing_equalized_defaults_false(self, tmp_path):
        csv_path = tmp_path / "tasks.csv"
        csv_path.write_text("n1,n2,equalized\n3,5,\n")
        tasks = load_ans_tasks_from_csv(csv_path)
        assert tasks == [(3, 5, False)]

    def test_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_ans_tasks_from_csv(tmp_path / "nonexistent.csv")


class TestBuildFromAnsCsv:
    """Test GenerationPlan.build_from_ans_csv."""

    def test_basic_plan(self, tmp_path):
        csv_path = tmp_path / "tasks.csv"
        csv_path.write_text("n1,n2,equalized\n3,5,TRUE\n2,4,FALSE\n")
        plan = GenerationPlan("ans", 1, 10, 1, ratios=[]).build_from_ans_csv(
            csv_path, num_copies=1
        )
        assert len(plan.tasks) == 2
        assert plan.tasks[0].params["n1"] == 3
        assert plan.tasks[0].params["n2"] == 5
        assert plan.tasks[0].params["equalize"] is True
        assert plan.tasks[1].params["n1"] == 2
        assert plan.tasks[1].params["n2"] == 4
        assert plan.tasks[1].params["equalize"] is False

    def test_multiple_copies(self, tmp_path):
        csv_path = tmp_path / "tasks.csv"
        csv_path.write_text("n1,n2,equalized\n6,8,FALSE\n")
        plan = GenerationPlan("ans", 1, 10, 1, ratios=[]).build_from_ans_csv(
            csv_path, num_copies=3
        )
        assert len(plan.tasks) == 3
        for task in plan.tasks:
            assert task.params["n1"] == 6
            assert task.params["n2"] == 8
        assert len({t.rep for t in plan.tasks}) == 3

    def test_duplicate_rows_unique_reps(self, tmp_path):
        csv_path = tmp_path / "tasks.csv"
        csv_path.write_text("n1,n2,equalized\n4,4,TRUE\n4,4,TRUE\n")
        plan = GenerationPlan("ans", 1, 10, 1, ratios=[]).build_from_ans_csv(
            csv_path, num_copies=1
        )
        assert len(plan.tasks) == 2
        assert plan.tasks[0].rep != plan.tasks[1].rep

    def test_one_colour_csv(self, tmp_path):
        csv_path = tmp_path / "tasks.csv"
        csv_path.write_text("n1,n2,equalized\n5,0,FALSE\n3,0,FALSE\n")
        plan = GenerationPlan("one_colour", 1, 10, 1, ratios=[]).build_from_ans_csv(
            csv_path, num_copies=1
        )
        assert len(plan.tasks) == 2
        assert plan.tasks[0].task_type == "one_colour"
        assert plan.tasks[0].params["n"] == 5
        assert plan.tasks[1].params["n"] == 3

    def test_wrong_task_type_raises(self, tmp_path):
        csv_path = tmp_path / "tasks.csv"
        csv_path.write_text("n1,n2,equalized\n3,5,TRUE\n")
        with pytest.raises(ValueError, match="build_from_ans_csv only applies"):
            GenerationPlan("mts", 1, 10, 1, ratios=[]).build_from_ans_csv(csv_path)


class TestAnsGeneratorCsvIntegration:
    """Test DotsANSGenerator with CSV-driven task lists."""

    def _base_config(self, **overrides):
        cfg = {
            **GENERAL_CONFIG,
            "train_num": 1,
            "test_num": 0,
            "output_dir": "/tmp/test_ans_csv",
            "ratios": "easy",
            "ONE_COLOUR": False,
            "min_point_num": 1,
            "max_point_num": 10,
            "version_tag": "",
            "img_format": "png",
            "layout": "mixed",
            "gap": 40,
        }
        cfg.update(overrides)
        return cfg

    def test_generate_images_uses_csv(self, tmp_path):
        """When tasks_csv is set, the plan should be built from CSV."""
        csv_path = tmp_path / "tasks.csv"
        csv_path.write_text("n1,n2,equalized\n3,5,TRUE\n2,4,FALSE\n")

        config = self._base_config(
            output_dir=str(tmp_path),
            tasks_csv=str(csv_path),
            tasks_copies=1,
        )

        with patch('cogstim.generators.dots_ans.os.makedirs'):
            generator = DotsANSGenerator(config)

        with patch.object(generator, 'create_and_save') as mock_save:
            generator.generate_images()
            assert mock_save.call_count == 2
            first_call = mock_save.call_args_list[0]
            assert first_call[0][:2] == (3, 5)
            assert first_call[1]["equalized"] is True

    def test_generate_images_csv_copies(self, tmp_path):
        """tasks_copies multiplies the CSV rows."""
        csv_path = tmp_path / "tasks.csv"
        csv_path.write_text("n1,n2,equalized\n3,5,FALSE\n")

        config = self._base_config(
            output_dir=str(tmp_path),
            tasks_csv=str(csv_path),
            tasks_copies=3,
        )

        with patch('cogstim.generators.dots_ans.os.makedirs'):
            generator = DotsANSGenerator(config)

        with patch.object(generator, 'create_and_save') as mock_save:
            generator.generate_images()
            assert mock_save.call_count == 3
