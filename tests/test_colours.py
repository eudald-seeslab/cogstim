"""Hex colours must survive parsing, rendering, export and config replay."""

import argparse
import csv
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest
import yaml
from PIL import Image, ImageColor

from cogstim.cli import create_parser
from cogstim.helpers.image_utils import resolve_stimulus_colour, to_hex
from cogstim.helpers.run_config import CONFIG_FILENAME


@pytest.mark.parametrize("colour, expected", [
    ("#12aBcD", "#12abcd"),
    ("#AbC", "#aabbcc"),
    ("#000", "#000000"),
    ("#FFF", "#ffffff"),
    ("yellow", "#fffe04"),
    ("blue", "#0003f9"),
    ((12, 34, 56), (12, 34, 56)),
])
def test_colour_resolution(colour, expected):
    assert to_hex(colour) == expected


@pytest.mark.parametrize("flag", ["--background-colour", "--symbol-colour"])
@pytest.mark.parametrize("colour", [
    "#12", "#12345", "#1234567", "#ggg", "#12345g", "#123\n",
    "#ffff", "#ffffffff", "123456", "0xff0000", "chartreuse",
])
def test_invalid_cli_colours_are_rejected(flag, colour, capsys):
    with pytest.raises(SystemExit) as exc:
        create_parser().parse_args(["fixation", flag, colour])
    assert exc.value.code == 2
    error = capsys.readouterr().err
    assert flag in error
    assert "#RGB" in error and "#RRGGBB" in error


@pytest.mark.parametrize("background", ["#fff", "#FFFFFF"])
def test_hex_background_keeps_default_stimulus_visible(background):
    assert resolve_stimulus_colour(None, background, "white") == "#000000"


def test_equivalent_explicit_hex_colours_warn_and_are_honoured(caplog):
    assert resolve_stimulus_colour("#fFf", "#FFFFFF", "red") == "#ffffff"
    assert "same as the background" in caplog.text


SHAPE_ARGS = ["--min-surface", 10000, "--max-surface", 10001, "--no-jitter"]
DOT_ARGS = ["--min-dot-num", 2, "--max-dot-num", 3, "--surface", "random"]
FOREGROUND = "#12aBcD"
SECOND = "#E70"
BACKGROUND = "#123"

# Use both hex formats, mixed case, and named/hex combinations across all tasks.
CASES = {
    "shapes": ([*SHAPE_ARGS, "--shape-colours", FOREGROUND], {"#12abcd"}),
    "colours": ([*SHAPE_ARGS, "--shape-colours", FOREGROUND, SECOND],
                {"#12abcd", "#ee7700"}),
    "custom": ([*SHAPE_ARGS, "--shapes", "circle", "square",
                "--shape-colours", FOREGROUND, "blue"], {"#12abcd", "#0003f9"}),
    "ans": ([*DOT_ARGS, "--dot-colour-1", FOREGROUND, "--dot-colour-2", SECOND],
            {"#12abcd", "#ee7700"}),
    "one-colour": (["--min-dot-num", 2, "--max-dot-num", 2,
                    "--dot-colour-1", FOREGROUND], {"#12abcd"}),
    "match-to-sample": ([*DOT_ARGS, "--dot-colour-1", FOREGROUND], {"#12abcd"}),
    "mask": (["--mask-num", 1, "--dot-num", 20, "--layout", "separated",
              "--dot-colour-1", FOREGROUND, "--dot-colour-2", SECOND],
             {"#12abcd", "#ee7700"}),
    "lines": (["--angles", 0, "--min-stripe-num", 2, "--max-stripe-num", 2,
               "--line-colour-1", FOREGROUND], {"#12abcd"}),
    "fixation": (["--types", "ABC", "--symbol-colour", FOREGROUND], {"#12abcd"}),
}


def run_cli(*args):
    result = subprocess.run(
        [sys.executable, "-m", "cogstim.cli", *map(str, args)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"


@pytest.mark.parametrize("task", CASES)
@pytest.mark.parametrize("img_format", ["png", "svg"])
def test_hex_colours_render_and_export_for_every_task(tmp_path, task, img_format):
    args, expected = CASES[task]
    split = [] if task in ("mask", "fixation") else ["--train-num", 1, "--test-num", 0]
    run_cli(task, *args, *split, "--background-colour", BACKGROUND,
            "--seed", 7, "--img-format", img_format, "--metadata", "csv",
            "--output-dir", tmp_path)

    paths = list(tmp_path.rglob(f"*.{img_format}"))
    assert paths
    actual = set()
    expected_all = expected | {"#112233"}
    for path in paths:
        if img_format == "png":
            with Image.open(path) as img:
                pixels = {pixel for _, pixel in img.convert("RGB").getcolors(1_000_000)}
            assert (17, 34, 51) in pixels, f"Missing background in {path}"
            actual.update(pixels)
        else:
            root = ET.parse(path).getroot()
            fills = {node.get("fill") for node in root.iter() if node.get("fill")}
            assert "#112233" in fills, f"Missing background in {path}"
            actual.update(fills)
    if img_format == "png":
        expected_all = {ImageColor.getrgb(colour) for colour in expected_all}
    assert actual == expected_all

    with (tmp_path / "annotations.csv").open(encoding="utf-8") as handle:
        colours = {row["colour"] for row in csv.DictReader(handle)}
    # Composite fixation symbols also draw cut-outs in the background colour.
    assert colours == (expected | {"#112233"} if task == "fixation" else expected)


def test_hex_config_replay_keeps_colours_and_class_paths(tmp_path):
    first, second = tmp_path / "first", tmp_path / "second"
    run_cli("ans", *CASES["ans"][0], "--train-num", 1, "--test-num", 0,
            "--background-colour", BACKGROUND, "--seed", 7,
            "--visual-properties", "--output-dir", first)
    config = first / CONFIG_FILENAME
    options = yaml.safe_load(config.read_text(encoding="utf-8"))["options"]
    assert options["dot_colour1"] == FOREGROUND
    assert options["dot_colour2"] == SECOND
    assert options["background_colour"] == BACKGROUND
    assert {path.name for path in (first / "train").iterdir()} == {FOREGROUND, SECOND}

    run_cli("run", config, "--output-dir", second)
    original = {p.relative_to(first): p.read_bytes() for p in first.rglob("*.png")}
    replayed = {p.relative_to(second): p.read_bytes() for p in second.rglob("*.png")}
    assert original and original == replayed
    with (first / "visual_properties.csv").open(encoding="utf-8") as handle:
        assert {row["colour"] for row in csv.DictReader(handle)} == {"#12abcd", "#ee7700"}
    pairs = first / "visual_property_pairs.csv"
    assert pairs.read_bytes() == (second / pairs.name).read_bytes()


def test_all_colour_options_describe_hex_formats_in_help():
    parser = create_parser()
    subparsers = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction))
    for task in CASES:
        for action in subparsers.choices[task]._actions:
            if any("colour" in flag for flag in action.option_strings):
                assert "#RGB" in action.help and "#RRGGBB" in action.help
