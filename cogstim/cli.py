#!/usr/bin/env python3
"""Unified CLI to generate synthetic image datasets (shapes, ANS dots, one-colour dots, …).

Example usage
-------------
# Shape recognition
python -m cogstim.cli --shape_recognition --train_num 60 --test_num 20

# Colour recognition
python -m cogstim.cli --colour_recognition --no-jitter

# ANS (dot arrays)
python -m cogstim.cli --ans --train_num 100 --test_num 40

# One-colour dot arrays
python -m cogstim.cli --one_colour --train_num 80 --test_num 20

# Custom shapes/colours
python -m cogstim.cli --custom --shapes triangle square --colours red green
"""

import argparse

# Generators
from cogstim.generators.shapes import ShapesGenerator
from cogstim.generators.dots_ans import (
    DotsANSGenerator,
    GENERAL_CONFIG as ANS_GENERAL_CONFIG,
)
from cogstim.generators.lines import LinesGenerator
from cogstim.generators.fixation import FixationGenerator
from cogstim.generators.match_to_sample import MatchToSampleGenerator, GENERAL_CONFIG as MTS_GENERAL_CONFIG
from cogstim.helpers.constants import (
    IMAGE_DEFAULTS,
    DOT_DEFAULTS,
    SHAPE_DEFAULTS,
    LINE_DEFAULTS,
    FIXATION_DEFAULTS,
)


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Unified synthetic image dataset generator (shapes, dot arrays, …)"
    )

    # Dataset type (mutually exclusive)
    ds_group = parser.add_mutually_exclusive_group(required=True)
    ds_group.add_argument("--shape_recognition", action="store_true", help="Generate yellow circles & stars. Classes = shapes")
    ds_group.add_argument("--colour_recognition", action="store_true", help="Generate circles in yellow and blue. Classes = colours")
    ds_group.add_argument("--ans", action="store_true", help="Generate dot-array images for Approximate Number System task")
    ds_group.add_argument("--one_colour", action="store_true", help="Generate single-colour dot-array images (number discrimination without colour cue)")
    ds_group.add_argument("--custom", action="store_true", help="Custom combination of shapes and colours (provide --shapes and --colors)")
    ds_group.add_argument("--lines", action="store_true", help="Generate images with rotated stripe/line patterns")  # NEW DATASET FLAG
    ds_group.add_argument("--fixation", action="store_true", help="Generate fixation target images (A, B, C, AB, AC, BC, ABC)")
    ds_group.add_argument("--match_to_sample", action="store_true", help="Generate match-to-sample dot-array pairs (sample/match)")

    # Custom shapes/colours (only if --custom)
    parser.add_argument("--shapes", nargs="+", choices=["circle", "star", "triangle", "square"], help="Shapes to include (only with --custom)")
    parser.add_argument("--colours", nargs="+", choices=["yellow", "blue", "red", "green", "black", "white", "gray"], help="Colours to include (only with --custom)")

    # General generation parameters
    parser.add_argument("--train_num", type=int, default=50, help="Number of image sets for training")
    parser.add_argument("--test_num", type=int, default=50, help="Number of image sets for testing")
    parser.add_argument("--output_dir", type=str, default=None, help="Root output directory (default depends on dataset type)")
    parser.add_argument("--background_colour", type=str, default=IMAGE_DEFAULTS["background_colour"], help=f"Background colour for generated images (default: {IMAGE_DEFAULTS['background_colour']})")
    parser.add_argument("--symbol_colour", type=str, default=FIXATION_DEFAULTS["symbol_colour"], choices=["yellow", "blue", "red", "green", "black", "white", "gray"], help=f"Fixation symbol colour (default: {FIXATION_DEFAULTS['symbol_colour']})")

    # Shape-specific parameters
    parser.add_argument("--min_surface", type=int, default=SHAPE_DEFAULTS["min_surface"], help=f"Minimum shape surface area (shapes datasets, default: {SHAPE_DEFAULTS['min_surface']})")
    parser.add_argument("--max_surface", type=int, default=SHAPE_DEFAULTS["max_surface"], help=f"Maximum shape surface area (shapes datasets, default: {SHAPE_DEFAULTS['max_surface']})")
    parser.add_argument("--no-jitter", dest="no_jitter", action="store_true", help="Disable positional jitter for shapes datasets")

    # Dot-array-specific parameters
    parser.add_argument("--ratios", type=str, choices=["easy", "hard", "all"], default="all", help="Ratio set to use for dot-array datasets")
    parser.add_argument("--version_tag", type=str, default="", help="Optional version tag appended to filenames (dot-array datasets)")
    parser.add_argument("--min_point_num", type=int, default=1, help="Minimum number of points per colour (dot-array datasets)")
    parser.add_argument("--max_point_num", type=int, default=10, help="Maximum number of points per colour (dot-array datasets)")
    parser.add_argument("--min_point_radius", type=int, default=DOT_DEFAULTS["min_point_radius"], help=f"Minimum dot radius in pixels (dot-array datasets, default: {DOT_DEFAULTS['min_point_radius']})")
    parser.add_argument("--max_point_radius", type=int, default=DOT_DEFAULTS["max_point_radius"], help=f"Maximum dot radius in pixels (dot-array datasets, default: {DOT_DEFAULTS['max_point_radius']})")
    parser.add_argument("--dot_colour", type=str, choices=["yellow", "blue", "red", "green", "black", "white", "gray"], default=DOT_DEFAULTS["dot_colour"], help=f"Dot colour for one-colour dot-array images (default: {DOT_DEFAULTS['dot_colour']})")
    parser.add_argument("--attempts_limit", type=int, default=DOT_DEFAULTS["attempts_limit"], help=f"Maximum attempts for dot placement (dot-array datasets, default: {DOT_DEFAULTS['attempts_limit']})")
    
    # Match-to-sample specific parameters
    parser.add_argument("--tolerance", type=float, help=f"Relative tolerance for area equalization in MTS (e.g., 0.01 for 1%%, default varies by task)")
    parser.add_argument("--abs_tolerance", type=int, help=f"Absolute area tolerance in pixels for MTS equalization (default varies by task)")

    # Line-pattern-specific parameters  # NEW ARGUMENT GROUP
    parser.add_argument("--angles", type=int, nargs="+", default=[0, 45, 90, 135], help="Rotation angles for stripe patterns (lines dataset)")
    parser.add_argument("--min_stripes", type=int, default=2, help="Minimum number of stripes per image (lines dataset)")
    parser.add_argument("--max_stripes", type=int, default=10, help="Maximum number of stripes per image (lines dataset)")
    parser.add_argument("--img_size", type=int, default=IMAGE_DEFAULTS["init_size"], help=f"Image size in pixels (lines dataset, default: {IMAGE_DEFAULTS['init_size']})")
    parser.add_argument("--tag", type=str, default="", help="Optional tag appended to filenames (lines dataset)")
    parser.add_argument("--min_thickness", type=int, default=LINE_DEFAULTS["min_thickness"], help=f"Minimum stripe thickness (lines dataset, default: {LINE_DEFAULTS['min_thickness']})")
    parser.add_argument("--max_thickness", type=int, default=LINE_DEFAULTS["max_thickness"], help=f"Maximum stripe thickness (lines dataset, default: {LINE_DEFAULTS['max_thickness']})")
    parser.add_argument("--min_spacing", type=int, default=LINE_DEFAULTS["min_spacing"], help=f"Minimum spacing between stripes (lines dataset, default: {LINE_DEFAULTS['min_spacing']})")
    parser.add_argument("--max_attempts", type=int, default=10000, help="Maximum attempts to place non-overlapping stripes (lines dataset)")

    # Fixation-specific parameters
    parser.add_argument("--types", nargs="+", default=["A", "B", "C", "AB", "AC", "BC", "ABC"], choices=["A", "B", "C", "AB", "AC", "BC", "ABC"], help="Fixation target types to generate")
    parser.add_argument("--all_types", action="store_true", help="Generate all fixation types (A, B, C, AB, AC, BC, ABC)")
    parser.add_argument("--dot_radius_px", type=int, default=FIXATION_DEFAULTS["dot_radius_px"], help=f"Radius of the central dot in pixels (A/ABC, default: {FIXATION_DEFAULTS['dot_radius_px']})")
    parser.add_argument("--disk_radius_px", type=int, default=FIXATION_DEFAULTS["disk_radius_px"], help=f"Radius of the filled disk in pixels (B/AB/BC/ABC, default: {FIXATION_DEFAULTS['disk_radius_px']})")
    parser.add_argument("--cross_thickness_px", type=int, default=FIXATION_DEFAULTS["cross_thickness_px"], help=f"Bar thickness for the cross in pixels (C/AC/BC/ABC, default: {FIXATION_DEFAULTS['cross_thickness_px']})")
    parser.add_argument("--cross_arm_px", type=int, default=FIXATION_DEFAULTS["cross_arm_px"], help=f"Half-length of each cross arm from the center in pixels (default: {FIXATION_DEFAULTS['cross_arm_px']})")
    parser.add_argument("--jitter_px", type=int, default=FIXATION_DEFAULTS["jitter_px"], help=f"Max positional jitter of the fixation center in pixels (default: {FIXATION_DEFAULTS['jitter_px']})")

    # Reproducibility parameter (applies to all datasets)
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducible generation (applies to all dataset types)")

    return parser.parse_args()


# ---------------------------------------------------------------------------
# Helper builders
# ---------------------------------------------------------------------------


def build_shapes_generator(args: argparse.Namespace) -> ShapesGenerator:
    """Instantiate ShapesGenerator according to CLI flags."""

    if args.shape_recognition:
        task_type = "two_shapes"
        shapes = ["circle", "star"]
        colors = ["yellow"]
    elif args.colour_recognition:
        task_type = "two_colors"
        shapes = ["circle"]
        colors = ["yellow", "blue"]
    else:  # custom
        if not args.shapes or not args.colours:
            raise ValueError("--shapes and --colours must be provided with --custom")
        task_type = "custom"
        shapes = args.shapes
        colors = args.colours

    jitter = not args.no_jitter

    output_dir = args.output_dir
    if output_dir is None:
        if task_type == "two_shapes":
            output_dir = "images/two_shapes"
        elif task_type == "two_colors":
            output_dir = "images/two_colors"
        else:
            output_dir = f"images/{'_'.join(shapes)}_{'_'.join(colors)}"

    config = {
        "shapes": shapes,
        "colours": colors,
        "task_type": task_type,
        "output_dir": output_dir,
        "train_num": args.train_num,
        "test_num": args.test_num,
        "min_surface": args.min_surface,
        "max_surface": args.max_surface,
        "jitter": jitter,
        "background_colour": args.background_colour,
        "seed": args.seed,
    }
    
    return ShapesGenerator(**config)


def generate_dot_array_dataset(args: argparse.Namespace, one_colour: bool) -> None:
    """Generate train/test dot-array datasets using points_creator.ImageGenerator."""

    base_dir_default = "images/one_colour" if one_colour else "images/ans"
    base_dir = args.output_dir or base_dir_default

    cfg = {
        **ANS_GENERAL_CONFIG,
        **{
            "train_num": args.train_num,
            "test_num": args.test_num,
            "output_dir": base_dir,
            "ratios": args.ratios,
            "ONE_COLOUR": one_colour,
            "version_tag": args.version_tag,
            "min_point_num": args.min_point_num,
            "max_point_num": args.max_point_num,
            "background_colour": args.background_colour,
            "min_point_radius": args.min_point_radius,
            "max_point_radius": args.max_point_radius,
            "attempts_limit": args.attempts_limit,
            "seed": args.seed,
        },
    }

    # Override colours for one-colour mode to use selected dot colour
    if one_colour:
        cfg["colour_1"] = args.dot_colour
        cfg["colour_2"] = None
    generator = DotsANSGenerator(cfg)
    generator.generate_images()


def generate_match_to_sample_dataset(args: argparse.Namespace) -> None:
    base_dir_default = "images/match_to_sample"
    base_dir = args.output_dir or base_dir_default

    cfg = {
        **MTS_GENERAL_CONFIG,
        **{
            "train_num": args.train_num,
            "test_num": args.test_num,
            "output_dir": base_dir,
            "ratios": args.ratios,
            "version_tag": args.version_tag,
            "min_point_num": args.min_point_num,
            "max_point_num": args.max_point_num,
            "background_colour": args.background_colour,
            "min_point_radius": args.min_point_radius,
            "max_point_radius": args.max_point_radius,
            "dot_colour": args.dot_colour,
            "attempts_limit": args.attempts_limit,
            "init_size": args.img_size,
            "seed": args.seed,
        },
    }
    
    # Add tolerance parameters if provided (otherwise use defaults from MTS_GENERAL_CONFIG)
    if args.tolerance is not None:
        cfg["tolerance"] = args.tolerance
    if args.abs_tolerance is not None:
        cfg["abs_tolerance"] = args.abs_tolerance
    generator = MatchToSampleGenerator(cfg)
    generator.generate_images()


def generate_lines_dataset(args: argparse.Namespace) -> None:
    """Generate train/test stripe-pattern line datasets using LinesGenerator."""

    base_dir_default = "images/lines"
    base_dir = args.output_dir or base_dir_default

    cfg = {
        "output_dir": base_dir,
        "train_num": args.train_num,
        "test_num": args.test_num,
        "angles": args.angles,
        "min_stripe_num": args.min_stripes,
        "max_stripe_num": args.max_stripes,
        "img_size": args.img_size,
        "tag": args.tag,
        "min_thickness": args.min_thickness,
        "max_thickness": args.max_thickness,
        "min_spacing": args.min_spacing,
        "max_attempts": args.max_attempts,
        "background_colour": args.background_colour,
        "seed": args.seed,
    }
    generator = LinesGenerator(cfg)
    generator.generate_images()


def generate_fixation_dataset(args: argparse.Namespace) -> None:
    """Generate train/test fixation-target datasets using FixationGenerator."""

    all_types = ["A", "B", "C", "AB", "AC", "BC", "ABC"]
    selected_types = all_types if args.all_types else args.types
    cfg = {
        "output_dir": args.output_dir or "images/fixation",
        "img_sets": 1,
        "types": selected_types,
        "img_size": args.img_size,
        "dot_radius_px": args.dot_radius_px,
        "disk_radius_px": args.disk_radius_px,
        "cross_thickness_px": args.cross_thickness_px,
        "cross_arm_px": args.cross_arm_px,
        "jitter_px": args.jitter_px,
        "background_colour": args.background_colour,
        "symbol_colour": args.symbol_colour,
        "tag": args.tag,
        "seed": args.seed,
    }
    generator = FixationGenerator(cfg)
    generator.generate_images()


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------


def main() -> None:
    args = parse_arguments()

    if args.ans:
        generate_dot_array_dataset(args, one_colour=False)
    elif args.one_colour:
        generate_dot_array_dataset(args, one_colour=True)
    elif args.lines:
        generate_lines_dataset(args)
    elif args.fixation:
        generate_fixation_dataset(args)
    elif args.match_to_sample:
        generate_match_to_sample_dataset(args)
    else:
        generator = build_shapes_generator(args)
        generator.generate_images()


if __name__ == "__main__":
    main() 