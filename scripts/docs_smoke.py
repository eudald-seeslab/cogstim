#!/usr/bin/env python3
"""
Smoke test for documentation examples.

Runs minimal examples for each subcommand and verifies:
- Non-empty output directories
- Metadata/output files exist where expected

This ensures docs examples stay in sync with the actual CLI behavior.
"""

import sys
import shutil
import subprocess
import tempfile
from pathlib import Path


def get_cogstim_command() -> list[str]:
    """Get the command to run cogstim (either installed or development mode)."""
    try:
        result = subprocess.run(
            ["cogstim", "--version"],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            return ["cogstim"]
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    return [sys.executable, "-m", "cogstim.cli"]


COGSTIM_CMD = get_cogstim_command()


def run_command(cmd: list[str], desc: str) -> bool:
    """Run a command and return success status."""
    print(f"\n{'=' * 60}")
    print(f"Testing: {desc}")
    print(f"Command: {' '.join(cmd)}")
    print('=' * 60)
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=120
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        print(f"✓ {desc} succeeded")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {desc} failed with exit code {e.returncode}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False
    except subprocess.TimeoutExpired:
        print(f"✗ {desc} timed out")
        return False


def verify_output(output_dir: Path, task: str, expected_dirs: list[str]) -> bool:
    """Verify that output directories are non-empty."""
    if not output_dir.exists():
        print(f"✗ Output directory {output_dir} does not exist")
        return False
    
    print(f"\nVerifying output in {output_dir}...")
    
    all_good = True
    for expected_dir in expected_dirs:
        dir_path = output_dir / expected_dir
        if not dir_path.exists():
            print(f"✗ Expected directory {dir_path} not found")
            all_good = False
            continue
        
        # Check if directory contains files (not just empty)
        files = list(dir_path.rglob("*.png"))
        if not files:
            print(f"✗ Directory {dir_path} contains no PNG files")
            all_good = False
        else:
            print(f"✓ {dir_path} contains {len(files)} PNG files")
    
    return all_good


def test_shapes(temp_dir: Path) -> bool:
    """Test shapes subcommand."""
    output_dir = temp_dir / "shapes"
    cmd = [
        *COGSTIM_CMD, "shapes",
        "--train-num", "2",
        "--test-num", "1",
        "--output-dir", str(output_dir),
        "--seed", "1234"
    ]
    
    if not run_command(cmd, "shapes --train-num 2 --test-num 1"):
        return False
    
    return verify_output(
        output_dir,
        "shapes",
        ["train/circle", "train/star", "test/circle", "test/star"]
    )


def test_colours(temp_dir: Path) -> bool:
    """Test colours subcommand."""
    output_dir = temp_dir / "colours"
    cmd = [
        *COGSTIM_CMD, "colours",
        "--train-num", "2",
        "--test-num", "1",
        "--output-dir", str(output_dir),
        "--seed", "1234"
    ]
    
    if not run_command(cmd, "colours --train-num 2 --test-num 1"):
        return False
    
    return verify_output(
        output_dir,
        "colours",
        ["train/yellow", "train/blue", "test/yellow", "test/blue"]
    )


def test_ans(temp_dir: Path) -> bool:
    """Test ANS subcommand."""
    output_dir = temp_dir / "ans"
    cmd = [
        *COGSTIM_CMD, "ans",
        "--ratios", "easy",
        "--train-num", "2",
        "--test-num", "1",
        "--output-dir", str(output_dir),
        "--seed", "1234"
    ]
    
    if not run_command(cmd, "ans --ratios easy --train-num 2 --test-num 1"):
        return False
    
    return verify_output(
        output_dir,
        "ans",
        ["train/yellow", "train/blue", "test/yellow", "test/blue"]
    )


def test_one_colour(temp_dir: Path) -> bool:
    """Test one-colour subcommand."""
    output_dir = temp_dir / "one_colour"
    cmd = [
        *COGSTIM_CMD, "one-colour",
        "--train-num", "2",
        "--test-num", "1",
        "--min-point-num", "1",
        "--max-point-num", "5",
        "--output-dir", str(output_dir),
        "--seed", "1234"
    ]
    
    if not run_command(cmd, "one-colour --train-num 2 --test-num 1"):
        return False
    
    return verify_output(
        output_dir,
        "one-colour",
        ["train/yellow", "test/yellow"]
    )


def test_match_to_sample(temp_dir: Path) -> bool:
    """Test match-to-sample subcommand."""
    output_dir = temp_dir / "match_to_sample"
    cmd = [
        *COGSTIM_CMD, "match-to-sample",
        "--ratios", "easy",
        "--train-num", "2",
        "--test-num", "1",
        "--min-point-num", "2",
        "--max-point-num", "4",
        "--output-dir", str(output_dir),
        "--seed", "1234"
    ]
    
    if not run_command(cmd, "match-to-sample --train-num 2 --test-num 1"):
        return False
    
    # Check that train and test dirs exist and contain sample/match pairs
    train_dir = output_dir / "train"
    test_dir = output_dir / "test"
    
    if not train_dir.exists() or not test_dir.exists():
        print(f"✗ train or test directory missing in {output_dir}")
        return False
    
    train_samples = list(train_dir.glob("*_s.png"))
    train_matches = list(train_dir.glob("*_m.png"))
    test_samples = list(test_dir.glob("*_s.png"))
    test_matches = list(test_dir.glob("*_m.png"))
    
    print(f"\nVerifying match-to-sample output:")
    print(f"✓ train/ contains {len(train_samples)} sample images")
    print(f"✓ train/ contains {len(train_matches)} match images")
    print(f"✓ test/ contains {len(test_samples)} sample images")
    print(f"✓ test/ contains {len(test_matches)} match images")
    
    if not train_samples or not train_matches or not test_samples or not test_matches:
        print("✗ Missing sample or match images")
        return False
    
    return True


def test_lines(temp_dir: Path) -> bool:
    """Test lines subcommand."""
    output_dir = temp_dir / "lines"
    cmd = [
        *COGSTIM_CMD, "lines",
        "--train-num", "2",
        "--test-num", "1",
        "--angles", "0", "90",
        "--output-dir", str(output_dir),
        "--seed", "1234"
    ]
    
    if not run_command(cmd, "lines --train-num 2 --test-num 1 --angles 0 90"):
        return False
    
    return verify_output(
        output_dir,
        "lines",
        ["train/0", "train/90", "test/0", "test/90"]
    )


def test_fixation(temp_dir: Path) -> bool:
    """Test fixation subcommand."""
    output_dir = temp_dir / "fixation"
    cmd = [
        *COGSTIM_CMD, "fixation",
        "--types", "A", "B", "ABC",
        "--output-dir", str(output_dir),
        "--seed", "1234"
    ]
    
    if not run_command(cmd, "fixation --types A B ABC"):
        return False
    
    # Check that specific fixation files exist
    expected_files = ["fix_A.png", "fix_B.png", "fix_ABC.png"]
    all_good = True
    
    print(f"\nVerifying fixation output:")
    for filename in expected_files:
        filepath = output_dir / filename
        if not filepath.exists():
            print(f"✗ Expected file {filepath} not found")
            all_good = False
        else:
            print(f"✓ {filepath} exists")
    
    return all_good


def test_custom(temp_dir: Path) -> bool:
    """Test custom subcommand."""
    output_dir = temp_dir / "custom"
    cmd = [
        *COGSTIM_CMD, "custom",
        "--shapes", "triangle", "square",
        "--colours", "red", "green",
        "--train-num", "2",
        "--test-num", "1",
        "--output-dir", str(output_dir),
        "--seed", "1234"
    ]
    
    if not run_command(cmd, "custom --shapes triangle square --colours red green"):
        return False
    
    return verify_output(
        output_dir,
        "custom",
        [
            "train/triangle_red", "train/triangle_green",
            "train/square_red", "train/square_green",
            "test/triangle_red", "test/triangle_green",
            "test/square_red", "test/square_green",
        ]
    )


def main():
    """Run all smoke tests."""
    print("=" * 60)
    print("CogStim Documentation Smoke Tests")
    print("=" * 60)
    print(f"\nUsing command: {' '.join(COGSTIM_CMD)}")
    print(f"Python: {sys.executable}\n")
    
    # Create a temporary directory for test outputs
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        print(f"\nUsing temporary directory: {temp_path}\n")
        
        tests = [
            ("shapes", test_shapes),
            ("colours", test_colours),
            ("ans", test_ans),
            ("one-colour", test_one_colour),
            ("match-to-sample", test_match_to_sample),
            ("lines", test_lines),
            ("fixation", test_fixation),
            ("custom", test_custom),
        ]
        
        results = {}
        for name, test_func in tests:
            try:
                results[name] = test_func(temp_path)
            except Exception as e:
                print(f"\n✗ Test '{name}' raised an exception: {e}")
                import traceback
                traceback.print_exc()
                results[name] = False
        
        # Print summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for name, success in results.items():
            status = "✓ PASS" if success else "✗ FAIL"
            print(f"{status}: {name}")
        
        print(f"\n{passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 All smoke tests passed!")
            return 0
        else:
            print(f"\n❌ {total - passed} test(s) failed")
            return 1


if __name__ == "__main__":
    sys.exit(main())

