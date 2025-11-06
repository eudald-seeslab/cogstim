"""Tests for scripts in the scripts/ directory."""

import pytest
import tempfile
import csv
import os
from pathlib import Path
from unittest.mock import patch
import numpy as np
from PIL import Image

# Import the script modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from mts_area_report import compute_foreground_area, main as mts_area_report_main, FILENAME_RE
from mts_check_equalization import main as mts_check_equalization_main


class TestMtsAreaReport:
    """Tests for mts_area_report.py script."""

    def test_compute_foreground_area_black_dots(self):
        """Test compute_foreground_area with black dots on white background."""
        # Create a test image with black dots on white background
        img = Image.new("RGB", (100, 100), color=(255, 255, 255))  # White background
        img_array = np.array(img)
        
        # Add some black pixels (foreground)
        img_array[10:20, 10:20] = [0, 0, 0]  # 10x10 black square
        img_array[30:40, 30:40] = [0, 0, 0]  # 10x10 black square
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            Image.fromarray(img_array).save(tmp.name)
            tmp_path = Path(tmp.name)
        
        try:
            area = compute_foreground_area(tmp_path)
            # Should count 200 black pixels (2 squares of 10x10 each)
            assert area == 200
        finally:
            tmp_path.unlink()

    def test_compute_foreground_area_no_foreground(self):
        """Test compute_foreground_area with no foreground pixels."""
        # Create a completely white image
        img = Image.new("RGB", (100, 100), color=(255, 255, 255))
        
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            img.save(tmp.name)
            tmp_path = Path(tmp.name)
        
        try:
            area = compute_foreground_area(tmp_path)
            assert area == 0
        finally:
            tmp_path.unlink()

    def test_filename_regex_matching(self):
        """Test FILENAME_RE regex pattern matching."""
        # Test valid filenames
        valid_cases = [
            ("img_2_3_0_s.png", {"n": "2", "m": "3", "tag": "0", "eq": None}),
            ("img_4_5_10_equalized_s.png", {"n": "4", "m": "5", "tag": "10", "eq": "_equalized"}),
            ("img_1_1_test_s.png", {"n": "1", "m": "1", "tag": "test", "eq": None}),
            ("img_6_8_42_equalized_s.png", {"n": "6", "m": "8", "tag": "42", "eq": "_equalized"}),
        ]
        
        for filename, expected in valid_cases:
            match = FILENAME_RE.match(filename)
            assert match is not None, f"Should match {filename}"
            assert match.group("n") == expected["n"]
            assert match.group("m") == expected["m"]
            assert match.group("tag") == expected["tag"]
            assert match.group("eq") == expected["eq"]

    def test_filename_regex_non_matching(self):
        """Test FILENAME_RE regex pattern with non-matching filenames."""
        invalid_cases = [
            "img_2_3_0_m.png",  # Ends with _m.png instead of _s.png
            "img_2_3_s.png",    # Missing tag
            "test.png",         # Doesn't follow pattern
            "img_2_3_0_s.jpg",  # Wrong extension
        ]
        
        for filename in invalid_cases:
            match = FILENAME_RE.match(filename)
            assert match is None, f"Should not match {filename}"

    def test_main_function_with_valid_files(self):
        """Test main function with valid MTS files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test images
            img_dir = Path(tmpdir)
            
            # Create sample and match images
            for base_name in ["img_2_3_0_s", "img_2_3_0_m", "img_4_5_1_equalized_s", "img_4_5_1_equalized_m"]:
                img = Image.new("RGB", (100, 100), color=(255, 255, 255))
                # Add some black pixels to make it non-empty
                img_array = np.array(img)
                img_array[10:20, 10:20] = [0, 0, 0]
                Image.fromarray(img_array).save(img_dir / f"{base_name}.png")
            
            # Create output CSV
            output_csv = img_dir / "test_output.csv"
            
            # Mock sys.argv to simulate command line arguments
            with patch('sys.argv', ['mts_area_report.py', '--dir', str(img_dir), '--out', str(output_csv)]):
                mts_area_report_main()
            
            # Check that CSV was created
            assert output_csv.exists()
            
            # Read and verify CSV content
            with open(output_csv, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                assert len(rows) == 2  # Should have 2 pairs
                
                # Check first row
                row1 = rows[0]
                assert row1['n'] == '2'
                assert row1['m'] == '3'
                assert row1['tag'] == '0'
                assert row1['equalized'] == '0'
                assert int(row1['s_area_px']) > 0
                assert int(row1['m_area_px']) > 0
                
                # Check second row
                row2 = rows[1]
                assert row2['n'] == '4'
                assert row2['m'] == '5'
                assert row2['tag'] == '1'
                assert row2['equalized'] == '1'

    def test_main_function_with_incomplete_pairs(self):
        """Test main function with incomplete pairs (missing match files)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            img_dir = Path(tmpdir)
            
            # Create only sample files (no match files)
            for base_name in ["img_2_3_0_s", "img_4_5_1_equalized_s"]:
                img = Image.new("RGB", (100, 100), color=(255, 255, 255))
                img_array = np.array(img)
                img_array[10:20, 10:20] = [0, 0, 0]
                Image.fromarray(img_array).save(img_dir / f"{base_name}.png")
            
            output_csv = img_dir / "test_output.csv"
            
            with patch('sys.argv', ['mts_area_report.py', '--dir', str(img_dir), '--out', str(output_csv)]):
                mts_area_report_main()
            
            # Should create empty CSV (no complete pairs)
            assert output_csv.exists()
            with open(output_csv, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 0

    def test_main_function_with_nonexistent_directory(self):
        """Test main function with non-existent directory."""
        with pytest.raises(FileNotFoundError):
            with patch('sys.argv', ['mts_area_report.py', '--dir', '/nonexistent/dir']):
                mts_area_report_main()


class TestMtsCheckEqualization:
    """Tests for mts_check_equalization.py script."""

    def test_main_function_with_valid_csv(self):
        """Test main function with valid CSV data."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
            writer = csv.DictWriter(tmp, fieldnames=['base', 'n', 'm', 'equalized', 's_area_px', 'm_area_px', 's_file', 'm_file'])
            writer.writeheader()
            writer.writerow({
                'base': 'img_2_3_0',
                'n': '2',
                'm': '3',
                'equalized': '0',
                's_area_px': '1000',
                'm_area_px': '1500',
                's_file': '/tmp/s.png',
                'm_file': '/tmp/m.png'
            })
            writer.writerow({
                'base': 'img_4_5_1_equalized',
                'n': '4',
                'm': '5',
                'equalized': '1',
                's_area_px': '2000',
                'm_area_px': '2000',
                's_file': '/tmp/s_eq.png',
                'm_file': '/tmp/m_eq.png'
            })
            tmp_path = tmp.name
        
        try:
            with patch('sys.argv', ['mts_check_equalization.py', tmp_path]):
                # Capture stdout
                with patch('sys.stdout') as mock_stdout:
                    mts_check_equalization_main()
                    
                    # Check that output was written
                    assert mock_stdout.write.called
        finally:
            os.unlink(tmp_path)

    def test_main_function_with_relative_tolerance_check(self):
        """Test main function with relative tolerance checking."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
            writer = csv.DictWriter(tmp, fieldnames=['base', 'n', 'm', 'equalized', 's_area_px', 'm_area_px', 's_file', 'm_file'])
            writer.writeheader()
            # Add equalized pair with large difference
            writer.writerow({
                'base': 'img_2_3_0_equalized',
                'n': '2',
                'm': '3',
                'equalized': '1',
                's_area_px': '1000',
                'm_area_px': '2000',  # 100% difference
                's_file': '/tmp/s.png',
                'm_file': '/tmp/m.png'
            })
            tmp_path = tmp.name
        
        try:
            with patch('sys.argv', ['mts_check_equalization.py', tmp_path, '--rel_tol', '0.01']):
                with patch('sys.stdout') as mock_stdout:
                    mts_check_equalization_main()
                    assert mock_stdout.write.called
        finally:
            os.unlink(tmp_path)

    def test_main_function_with_removal_flagging(self):
        """Test main function with removal flagging."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
            writer = csv.DictWriter(tmp, fieldnames=['base', 'n', 'm', 'equalized', 's_area_px', 'm_area_px', 's_file', 'm_file'])
            writer.writeheader()
            # Add equalized pair with large difference
            writer.writerow({
                'base': 'img_2_3_0_equalized',
                'n': '2',
                'm': '3',
                'equalized': '1',
                's_area_px': '1000',
                'm_area_px': '2000',  # 100% difference
                's_file': '/tmp/s.png',
                'm_file': '/tmp/m.png'
            })
            tmp_path = tmp.name
        
        try:
            with patch('sys.argv', ['mts_check_equalization.py', tmp_path, '--remove_over_rel', '0.1']):
                with patch('sys.stdout') as mock_stdout:
                    mts_check_equalization_main()
                    assert mock_stdout.write.called
        finally:
            os.unlink(tmp_path)

    def test_main_function_with_deletion(self):
        """Test main function with actual file deletion."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            s_file = Path(tmpdir) / "s.png"
            m_file = Path(tmpdir) / "m.png"
            s_file.write_bytes(b"fake image data")
            m_file.write_bytes(b"fake image data")
            
            # Create CSV
            csv_file = Path(tmpdir) / "test.csv"
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['base', 'n', 'm', 'equalized', 's_area_px', 'm_area_px', 's_file', 'm_file'])
                writer.writeheader()
                writer.writerow({
                    'base': 'img_2_3_0_equalized',
                    'n': '2',
                    'm': '3',
                    'equalized': '1',
                    's_area_px': '1000',
                    'm_area_px': '2000',  # Large difference
                    's_file': str(s_file),
                    'm_file': str(m_file)
                })
            
            with patch('sys.argv', ['mts_check_equalization.py', str(csv_file), '--remove_over_rel', '0.1', '--delete']):
                with patch('sys.stdout') as mock_stdout:
                    mts_check_equalization_main()
                    
                    # Check that files were deleted
                    assert not s_file.exists()
                    assert not m_file.exists()

    def test_main_function_with_nonexistent_csv(self):
        """Test main function with non-existent CSV file."""
        with pytest.raises(FileNotFoundError):
            with patch('sys.argv', ['mts_check_equalization.py', '/nonexistent/file.csv']):
                mts_check_equalization_main()

    def test_main_function_with_invalid_csv_data(self):
        """Test main function with invalid CSV data."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
            writer = csv.DictWriter(tmp, fieldnames=['base', 'n', 'm', 'equalized', 's_area_px', 'm_area_px', 's_file', 'm_file'])
            writer.writeheader()
            # Add row with invalid data
            writer.writerow({
                'base': 'img_2_3_0',
                'n': 'invalid',  # Invalid integer
                'm': '3',
                'equalized': '0',
                's_area_px': '1000',
                'm_area_px': '1500',
                's_file': '/tmp/s.png',
                'm_file': '/tmp/m.png'
            })
            tmp_path = tmp.name
        
        try:
            with patch('sys.argv', ['mts_check_equalization.py', tmp_path]):
                with patch('sys.stdout') as mock_stdout:
                    mts_check_equalization_main()
                    # Should handle invalid data gracefully
                    assert mock_stdout.write.called
        finally:
            os.unlink(tmp_path)

    def test_relative_difference_calculation(self):
        """Test relative difference calculation logic."""
        # Test the rel_diff function logic
        def rel_diff(a: int, b: int) -> float:
            denom = max(a, b, 1)
            return abs(a - b) / denom
        
        # Test cases
        assert rel_diff(1000, 1000) == 0.0  # Equal values
        assert abs(rel_diff(1000, 1100) - 0.09090909090909091) < 1e-10  # ~9.09% difference
        assert rel_diff(1000, 2000) == 0.5  # 50% difference
        assert rel_diff(0, 1000) == 1.0     # 100% difference (handles zero)

    def test_tolerance_checking_logic(self):
        """Test tolerance checking logic."""
        def within_tolerance(ad: int, rd: float, abs_tol: int, rel_tol: float) -> bool:
            return ad <= abs_tol or rd <= rel_tol
        
        # Test cases
        assert within_tolerance(1, 0.001, 2, 0.01) is True   # Within absolute tolerance
        assert within_tolerance(5, 0.005, 2, 0.01) is True  # Within relative tolerance
        assert within_tolerance(5, 0.02, 2, 0.01) is False  # Outside both tolerances
        assert within_tolerance(1, 0.02, 2, 0.01) is True   # Within absolute tolerance
