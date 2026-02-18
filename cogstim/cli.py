#!/usr/bin/env python3
"""CLI for cogstim with task-based subcommands.

Each task (shapes, colours, ans, etc.) has its own subcommand with relevant options.

Examples:
  cogstim shapes --train-num 100 --test-num 40
  cogstim ans --ratios easy --train-num 50 --demo
  cogstim fixation --all-types
"""

import sys
import argparse
from pathlib import Path
from typing import Any, Dict

from cogstim.generators.shapes import ShapesGenerator
from cogstim.generators.dots_ans import DotsANSGenerator, GENERAL_CONFIG as ANS_GENERAL_CONFIG
from cogstim.generators.lines import LinesGenerator
from cogstim.generators.fixation import FixationGenerator
from cogstim.generators.match_to_sample import (
    MatchToSampleGenerator,
    GENERAL_CONFIG as MTS_GENERAL_CONFIG,
)
from cogstim.helpers.constants import (
    IMAGE_DEFAULTS,
    DOT_DEFAULTS,
    SHAPE_DEFAULTS,
    LINE_DEFAULTS,
    FIXATION_DEFAULTS,
    MTS_DEFAULTS,
    CLI_DEFAULTS,
)


# =============================================================================
# Helper Functions
# =============================================================================


def parse_ratios(value):
    """Parse ratios argument - either a preset string or comma-separated fractions."""
    if value in ["easy", "hard", "all"]:
        return value
    # Try to parse as comma-separated fractions (e.g., "1/2,2/3,3/4")
    try:
        ratios = []
        for fraction_str in value.split(","):
            fraction_str = fraction_str.strip()
            if "/" in fraction_str:
                numerator, denominator = fraction_str.split("/")
                ratios.append(float(numerator) / float(denominator))
            else:
                # Also accept plain decimals for backwards compatibility
                ratios.append(float(fraction_str))
        return ratios
    except (ValueError, ZeroDivisionError):
        raise argparse.ArgumentTypeError(
            f"Invalid ratios: '{value}'. Must be 'easy', 'hard', 'all', or comma-separated fractions (e.g., '1/2,2/3,3/4')"
        )


# =============================================================================
# Builder Functions
# =============================================================================


def build_shapes_config(args: argparse.Namespace) -> Dict[str, Any]:
    """Build configuration for shapes/colours subcommands."""
    shapes = args.shapes if hasattr(args, 'shapes') and args.shapes else ["circle", "star"]
    colours = args.colours if hasattr(args, 'colours') and args.colours else ["yellow"]
    
    # Determine task type based on shapes and colours
    if len(shapes) == 2 and len(colours) == 1:
        task_type = "two_shapes"
    elif len(shapes) == 1 and len(colours) == 2:
        task_type = "two_colors"
    else:
        task_type = "custom"

    jitter = not args.no_jitter

    return {
        "shapes": shapes,
        "colours": colours,
        "task_type": task_type,
        "output_dir": args.output_dir,
        "train_num": args.train_num,
        "test_num": args.test_num,
        "min_surface": args.min_surface,
        "max_surface": args.max_surface,
        "jitter": jitter,
        "background_colour": args.background_colour,
        "seed": args.seed,
        "random_rotation": args.random_rotation,
        "min_rotation": args.min_rotation,
        "max_rotation": args.max_rotation,
        "img_format": args.img_format,
        "version_tag": args.version_tag,
    }
    

def build_colours_config(args: argparse.Namespace) -> Dict[str, Any]:
    """Build configuration for colour discrimination (same shape, different colours)."""
    shape = args.shape if hasattr(args, 'shape') else "circle"
    colours = args.colours if hasattr(args, 'colours') and args.colours else ["yellow", "blue"]
    
    jitter = not args.no_jitter
    
    return {
        "shapes": [shape],
        "colours": colours,
        "task_type": "two_colors",
        "output_dir": args.output_dir,
        "train_num": args.train_num,
        "test_num": args.test_num,
        "min_surface": args.min_surface,
        "max_surface": args.max_surface,
        "jitter": jitter,
        "background_colour": args.background_colour,
        "seed": args.seed,
        "random_rotation": args.random_rotation,
        "min_rotation": args.min_rotation,
        "max_rotation": args.max_rotation,
        "img_format": args.img_format,
        "version_tag": args.version_tag,
    }


def build_ans_config(args: argparse.Namespace) -> Dict[str, Any]:
    """Build configuration for ANS (two-colour dot arrays)."""
    cfg = {
        **ANS_GENERAL_CONFIG,
        **{
            "train_num": args.train_num,
            "test_num": args.test_num,
            "output_dir": args.output_dir,
            "ratios": args.ratios,
            "ONE_COLOUR": False,
            "version_tag": getattr(args, 'version_tag', ''),
            "min_point_num": args.min_point_num,
            "max_point_num": args.max_point_num,
            "background_colour": args.background_colour,
            "min_point_radius": args.min_point_radius,
            "max_point_radius": args.max_point_radius,
            "attempts_limit": args.attempts_limit,
            "seed": args.seed,
            "img_format": args.img_format,
            "version_tag": args.version_tag,
        },
    }

    # Allow custom colours for ANS
    if hasattr(args, 'dot_colour1'):
        cfg["colour_1"] = args.dot_colour1
    if hasattr(args, 'dot_colour2'):
        cfg["colour_2"] = args.dot_colour2
    
    return cfg


def build_one_colour_config(args: argparse.Namespace) -> Dict[str, Any]:
    """Build configuration for one-colour dot arrays."""
    cfg = {
        **ANS_GENERAL_CONFIG,
        **{
            "train_num": args.train_num,
            "test_num": args.test_num,
            "output_dir": args.output_dir,
            "ratios": getattr(args, 'ratios', 'all'),
            "ONE_COLOUR": True,
            "version_tag": getattr(args, 'version_tag', ''),
            "min_point_num": args.min_point_num,
            "max_point_num": args.max_point_num,
            "background_colour": args.background_colour,
            "min_point_radius": args.min_point_radius,
            "max_point_radius": args.max_point_radius,
            "attempts_limit": args.attempts_limit,
            "seed": args.seed,
            "colour_1": args.dot_colour,
            "colour_2": None,
            "img_format": args.img_format,
            "version_tag": args.version_tag,
        },
    }
    
    return cfg


def build_mts_config(args: argparse.Namespace) -> Dict[str, Any]:
    """Build configuration for match-to-sample."""
    cfg = {
        **MTS_GENERAL_CONFIG,
        **{
            "train_num": args.train_num,
            "test_num": args.test_num,
            "output_dir": args.output_dir,
            "ratios": args.ratios,
            "version_tag": getattr(args, 'version_tag', ''),
            "min_point_num": args.min_point_num,
            "max_point_num": args.max_point_num,
            "background_colour": args.background_colour,
            "min_point_radius": args.min_point_radius,
            "max_point_radius": args.max_point_radius,
            "dot_colour": args.dot_colour,
            "attempts_limit": args.attempts_limit,
            "init_size": args.img_size,
            "seed": args.seed,
            "img_format": args.img_format,
            "version_tag": args.version_tag,
        },
    }
    
    # Override tolerances if specified
    if hasattr(args, 'tolerance') and args.tolerance is not None:
        cfg["tolerance"] = args.tolerance
    if hasattr(args, 'abs_tolerance') and args.abs_tolerance is not None:
        cfg["abs_tolerance"] = args.abs_tolerance

    if getattr(args, 'tasks_csv', None):
        cfg["tasks_csv"] = args.tasks_csv
        cfg["tasks_copies"] = getattr(args, 'tasks_copies', 1)
    
    return cfg


def build_lines_config(args: argparse.Namespace) -> Dict[str, Any]:
    """Build configuration for lines/stripes."""
    return {
        "output_dir": args.output_dir,
        "train_num": args.train_num,
        "test_num": args.test_num,
        "angles": args.angles,
        "min_stripe_num": args.min_stripes,
        "max_stripe_num": args.max_stripes,
        "img_size": args.img_size,
        "tag": getattr(args, 'tag', ''),
        "min_thickness": args.min_thickness,
        "max_thickness": args.max_thickness,
        "min_spacing": args.min_spacing,
        "max_attempts": getattr(args, 'max_attempts', 10000),
        "background_colour": args.background_colour,
        "seed": args.seed,
        "img_format": args.img_format,
        "version_tag": args.version_tag,
    }


def build_fixation_config(args: argparse.Namespace) -> Dict[str, Any]:
    """Build configuration for fixation targets."""
    all_types = ["A", "B", "C", "AB", "AC", "BC", "ABC"]
    
    if hasattr(args, 'all_types') and args.all_types:
        selected_types = all_types
    else:
        selected_types = args.types if hasattr(args, 'types') and args.types else all_types
    
    return {
        "output_dir": args.output_dir,
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
        "seed": args.seed,
        "img_format": args.img_format,
        "version_tag": args.version_tag,
    }


def build_custom_config(args: argparse.Namespace) -> Dict[str, Any]:
    """Build configuration for custom shapes/colours."""
    if not args.shapes or not args.colours:
        raise ValueError("--shapes and --colours are required for custom task")
    
    jitter = not args.no_jitter
    
    return {
        "shapes": args.shapes,
        "colours": args.colours,
        "task_type": "custom",
        "output_dir": args.output_dir,
        "train_num": args.train_num,
        "test_num": args.test_num,
        "min_surface": args.min_surface,
        "max_surface": args.max_surface,
        "jitter": jitter,
        "background_colour": args.background_colour,
        "seed": args.seed,
        "random_rotation": args.random_rotation,
        "min_rotation": args.min_rotation,
        "max_rotation": args.max_rotation,
        "version_tag": args.version_tag,
        "img_format": args.img_format,
    }


# =============================================================================
# Dispatch Functions
# =============================================================================


def run_shapes(args: argparse.Namespace) -> None:
    """Execute shapes generation."""
    config = build_shapes_config(args)
    generator = ShapesGenerator(**config)
    generator.generate_images()
    
    if not args.quiet:
        total = args.train_num + args.test_num
        print(f"\n✓ Generated {total} images. Output: {config['output_dir']}")


def run_colours(args: argparse.Namespace) -> None:
    """Execute colour discrimination generation."""
    config = build_colours_config(args)
    generator = ShapesGenerator(**config)
    generator.generate_images()
    
    if not args.quiet:
        total = args.train_num + args.test_num
        print(f"\n✓ Generated {total} images. Output: {config['output_dir']}")


def run_ans(args: argparse.Namespace) -> None:
    """Execute ANS dot array generation."""
    config = build_ans_config(args)
    generator = DotsANSGenerator(config)
    generator.generate_images()
    
    if not args.quiet:
        total = args.train_num + args.test_num
        print(f"\n✓ Generated {total} images. Output: {config['output_dir']}")


def run_one_colour(args: argparse.Namespace) -> None:
    """Execute one-colour dot array generation."""
    config = build_one_colour_config(args)
    generator = DotsANSGenerator(config)
    generator.generate_images()
    
    if not args.quiet:
        total = args.train_num + args.test_num
        print(f"\n✓ Generated {total} images. Output: {config['output_dir']}")


def run_mts(args: argparse.Namespace) -> None:
    """Execute match-to-sample generation."""
    config = build_mts_config(args)
    generator = MatchToSampleGenerator(config)
    generator.generate_images()
    
    if not args.quiet:
        total = args.train_num + args.test_num
        print(f"\n✓ Generated {total} image pairs. Output: {config['output_dir']}")


def run_lines(args: argparse.Namespace) -> None:
    """Execute lines/stripes generation."""
    config = build_lines_config(args)
    generator = LinesGenerator(config)
    generator.generate_images()
    
    if not args.quiet:
        total = args.train_num + args.test_num
        print(f"\n✓ Generated {total} images. Output: {config['output_dir']}")


def run_fixation(args: argparse.Namespace) -> None:
    """Execute fixation target generation."""
    config = build_fixation_config(args)
    generator = FixationGenerator(config)
    generator.generate_images()

    if not args.quiet:
        num_types = len(config['types'])
        print(f"\n✓ Generated {num_types} fixation images. Output: {config['output_dir']}")


def run_custom(args: argparse.Namespace) -> None:
    """Execute custom shapes/colours generation."""
    config = build_custom_config(args)
    generator = ShapesGenerator(**config)
    generator.generate_images()

    if not args.quiet:
        total = args.train_num + args.test_num
        print(f"\n✓ Generated {total} images. Output: {config['output_dir']}")


# =============================================================================
# Argument Parsing - Common Options
# =============================================================================


def add_common_options(parser: argparse.ArgumentParser) -> None:
    """Add common options available to all subcommands."""
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Root output directory (default varies by task)"
    )
    parser.add_argument(
        "--img-size",
        type=int,
        default=IMAGE_DEFAULTS["init_size"],
        help=f"Image size in pixels (default: {IMAGE_DEFAULTS['init_size']})"
    )
    parser.add_argument(
        "--img-format",
        type=str,
        default=IMAGE_DEFAULTS["img_format"],
        choices=["png", "jpg", "jpeg", "bmp", "tiff"],
        help=f"Image format (default: {IMAGE_DEFAULTS['img_format']})"
    )
    parser.add_argument(
        "--background-colour",
        type=str,
        default=IMAGE_DEFAULTS["background_colour"],
        choices=["yellow", "blue", "red", "green", "black", "white", "gray"],
        help=f"Background colour (default: {IMAGE_DEFAULTS['background_colour']})"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible generation"
    )
    parser.add_argument(
        "--version-tag",
        type=str,
        default="",
        help="Optional version tag appended to filenames"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress all non-error output"
    )


def add_train_test_options(parser: argparse.ArgumentParser) -> None:
    """Add train/test count options."""
    parser.add_argument(
        "--train-num",
        type=int,
        default=CLI_DEFAULTS["train_num"],
        help=f"Number of training images to generate (default: {CLI_DEFAULTS['train_num']})"
    )
    parser.add_argument(
        "--test-num",
        type=int,
        default=CLI_DEFAULTS["test_num"],
        help=f"Number of test images to generate (default: {CLI_DEFAULTS['test_num']})"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Generate a small demo dataset (8 training images)"
    )


def add_dot_options(parser: argparse.ArgumentParser, include_ratios: bool = True) -> None:
    """Add dot-array-specific options."""
    if include_ratios:
        parser.add_argument(
            "--ratios",
            type=parse_ratios,
            default="all",
            help="Ratio set: 'easy', 'hard', 'all', or comma-separated fractions (e.g., '1/2,2/3,3/4') (default: all)"
        )
    
    parser.add_argument(
        "--min-point-num",
        type=int,
        default=1,
        help="Minimum number of points per colour (default: 1)"
    )
    parser.add_argument(
        "--max-point-num",
        type=int,
        default=10,
        help="Maximum number of points per colour (default: 10)"
    )
    parser.add_argument(
        "--min-point-radius",
        type=int,
        default=DOT_DEFAULTS["min_point_radius"],
        help=f"Minimum dot radius in pixels (default: {DOT_DEFAULTS['min_point_radius']})"
    )
    parser.add_argument(
        "--max-point-radius",
        type=int,
        default=DOT_DEFAULTS["max_point_radius"],
        help=f"Maximum dot radius in pixels (default: {DOT_DEFAULTS['max_point_radius']})"
    )
    parser.add_argument(
        "--attempts-limit",
        type=int,
        default=DOT_DEFAULTS["attempts_limit"],
        help=f"Maximum attempts for dot placement (default: {DOT_DEFAULTS['attempts_limit']})"
    )


def add_shape_options(parser: argparse.ArgumentParser) -> None:
    """Add shape-specific options."""
    parser.add_argument(
        "--min-surface",
        type=int,
        default=SHAPE_DEFAULTS["min_surface"],
        help=f"Minimum shape surface area (default: {SHAPE_DEFAULTS['min_surface']})"
    )
    parser.add_argument(
        "--max-surface",
        type=int,
        default=SHAPE_DEFAULTS["max_surface"],
        help=f"Maximum shape surface area (default: {SHAPE_DEFAULTS['max_surface']})"
    )
    parser.add_argument(
        "--no-jitter",
        action="store_true",
        help="Disable positional jitter"
    )
    parser.add_argument(
        "--random-rotation",
        action="store_true",
        help="Enable random rotation of shapes"
    )
    parser.add_argument(
        "--min-rotation",
        type=int,
        default=SHAPE_DEFAULTS["min_rotation"],
        help=f"Minimum rotation angle in degrees (default: {SHAPE_DEFAULTS['min_rotation']})"
    )
    parser.add_argument(
        "--max-rotation",
        type=int,
        default=SHAPE_DEFAULTS["max_rotation"],
        help=f"Maximum rotation angle in degrees (default: {SHAPE_DEFAULTS['max_rotation']})"
    )


# =============================================================================
# Subcommand Definitions
# =============================================================================


def setup_shapes_subcommand(subparsers) -> None:
    """Setup 'shapes' subcommand for shape discrimination."""
    parser = subparsers.add_parser(
        "shapes",
        help="Generate shape discrimination dataset (e.g., circles vs stars)",
        description="Generate images of different shapes in the same colour for shape recognition tasks.",
        epilog="Example: cogstim shapes --train-num 100 --test-num 40",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    
    add_common_options(parser)
    add_train_test_options(parser)
    add_shape_options(parser)
    
    parser.add_argument(
        "--shapes",
        nargs=2,
        choices=["circle", "star", "triangle", "square"],
        default=["circle", "star"],
        help="Two shapes for discrimination"
    )
    parser.add_argument(
        "--colours",
        nargs=1,
        choices=["yellow", "blue", "red", "green", "black", "white", "gray"],
        default=["yellow"],
        help="Colour for both shapes"
    )
    
    parser.set_defaults(func=run_shapes)


def setup_colours_subcommand(subparsers) -> None:
    """Setup 'colours' subcommand for colour discrimination."""
    parser = subparsers.add_parser(
        "colours",
        help="Generate colour discrimination dataset (same shape, different colours)",
        description="Generate images of the same shape in different colours for colour recognition tasks.",
        epilog="Example: cogstim colours --train-num 100 --test-num 40 --colours yellow blue",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    
    add_common_options(parser)
    add_train_test_options(parser)
    add_shape_options(parser)
    
    parser.add_argument(
        "--shape",
        type=str,
        choices=["circle", "star", "triangle", "square"],
        default="circle",
        help="Shape to use for both classes"
    )
    parser.add_argument(
        "--colours",
        nargs=2,
        choices=["yellow", "blue", "red", "green", "black", "white", "gray"],
        default=["yellow", "blue"],
        help="Two colours for discrimination"
    )
    
    parser.set_defaults(func=run_colours)


def setup_ans_subcommand(subparsers) -> None:
    """Setup 'ans' subcommand for two-colour dot arrays."""
    parser = subparsers.add_parser(
        "ans",
        help="Generate ANS (Approximate Number System) dot arrays with two colours",
        description="Generate two-colour dot array images for approximate number system tasks. Classes are based on dominant colour.",
        epilog="Example: cogstim ans --ratios easy --train-num 100 --test-num 40",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    
    add_common_options(parser)
    add_train_test_options(parser)
    add_dot_options(parser, include_ratios=True)
    
    parser.add_argument(
        "--dot-colour1",
        type=str,
        choices=["yellow", "blue", "red", "green", "black", "white", "gray"],
        default="yellow",
        help="First dot colour"
    )
    parser.add_argument(
        "--dot-colour2",
        type=str,
        choices=["yellow", "blue", "red", "green", "black", "white", "gray"],
        default="blue",
        help="Second dot colour"
    )
    
    parser.set_defaults(func=run_ans)


def setup_one_colour_subcommand(subparsers) -> None:
    """Setup 'one-colour' subcommand for single-colour dot arrays."""
    parser = subparsers.add_parser(
        "one-colour",
        help="Generate single-colour dot arrays (quantity discrimination)",
        description="Generate single-colour dot array images. Classes are based on quantity without colour cues.",
        epilog="Example: cogstim one-colour --train-num 80 --test-num 20 --dot-colour yellow",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    
    add_common_options(parser)
    add_train_test_options(parser)
    add_dot_options(parser, include_ratios=False)
    
    parser.add_argument(
        "--dot-colour",
        type=str,
        choices=["yellow", "blue", "red", "green", "black", "white", "gray"],
        default=DOT_DEFAULTS["dot_colour"],
        help=f"Dot colour (default: {DOT_DEFAULTS['dot_colour']})"
    )
    
    parser.set_defaults(func=run_one_colour)


def setup_mts_subcommand(subparsers) -> None:
    """Setup 'match-to-sample' subcommand."""
    parser = subparsers.add_parser(
        "match-to-sample",
        help="Generate match-to-sample dot array pairs",
        description="Generate sample/match image pairs for match-to-sample tasks with area equalization.",
        epilog="Example: cogstim match-to-sample --ratios easy --train-num 50 --test-num 20",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    
    add_common_options(parser)
    add_train_test_options(parser)
    add_dot_options(parser, include_ratios=True)
    
    parser.add_argument(
        "--dot-colour",
        type=str,
        choices=["yellow", "blue", "red", "green", "black", "white", "gray"],
        default=MTS_DEFAULTS["dot_colour"],
        help=f"Dot colour (default: {MTS_DEFAULTS['dot_colour']})"
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=None,
        help=f"Relative tolerance for area equalization (default: {MTS_DEFAULTS['tolerance']})"
    )
    parser.add_argument(
        "--abs-tolerance",
        type=int,
        default=None,
        help=f"Absolute area tolerance in pixels (default: {MTS_DEFAULTS['abs_tolerance']})"
    )
    parser.add_argument(
        "--tasks-csv",
        type=str,
        default=None,
        metavar="PATH",
        help="Path to CSV file specifying tasks (columns: sample, match, equalized). When set, ratios and min/max-point-num are ignored."
    )
    parser.add_argument(
        "--tasks-copies",
        type=int,
        default=1,
        metavar="N",
        help="Number of copies of the tasks distribution (default: 1). Applies when --tasks-csv is used."
    )
    
    parser.set_defaults(func=run_mts)


def setup_lines_subcommand(subparsers) -> None:
    """Setup 'lines' subcommand for stripe patterns."""
    parser = subparsers.add_parser(
        "lines",
        help="Generate rotated stripe/line pattern images",
        description="Generate images with rotated stripe patterns at different angles.",
        epilog="Example: cogstim lines --train-num 50 --test-num 20 --angles 0 45 90 135",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    
    add_common_options(parser)
    add_train_test_options(parser)
    
    parser.add_argument(
        "--angles",
        type=int,
        nargs="+",
        default=[0, 45, 90, 135],
        help="Rotation angles for stripe patterns"
    )
    parser.add_argument(
        "--min-stripes",
        type=int,
        default=2,
        help="Minimum number of stripes per image"
    )
    parser.add_argument(
        "--max-stripes",
        type=int,
        default=10,
        help="Maximum number of stripes per image"
    )
    parser.add_argument(
        "--min-thickness",
        type=int,
        default=LINE_DEFAULTS["min_thickness"],
        help=f"Minimum stripe thickness (default: {LINE_DEFAULTS['min_thickness']})"
    )
    parser.add_argument(
        "--max-thickness",
        type=int,
        default=LINE_DEFAULTS["max_thickness"],
        help=f"Maximum stripe thickness (default: {LINE_DEFAULTS['max_thickness']})"
    )
    parser.add_argument(
        "--min-spacing",
        type=int,
        default=LINE_DEFAULTS["min_spacing"],
        help=f"Minimum spacing between stripes (default: {LINE_DEFAULTS['min_spacing']})"
    )
    
    parser.set_defaults(func=run_lines)


def setup_fixation_subcommand(subparsers) -> None:
    """Setup 'fixation' subcommand for fixation targets."""
    parser = subparsers.add_parser(
        "fixation",
        help="Generate fixation target images (A, B, C, AB, AC, BC, ABC)",
        description="Generate fixation target images with different element combinations.",
        epilog="Example: cogstim fixation --all-types --background-colour black",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    
    add_common_options(parser)
    
    parser.add_argument(
        "--types",
        nargs="+",
        choices=["A", "B", "C", "AB", "AC", "BC", "ABC"],
        default=["A", "B", "C", "AB", "AC", "BC", "ABC"],
        help="Fixation target types to generate"
    )
    parser.add_argument(
        "--all-types",
        action="store_true",
        help="Generate all fixation types"
    )
    parser.add_argument(
        "--symbol-colour",
        type=str,
        default=FIXATION_DEFAULTS["symbol_colour"],
        choices=["yellow", "blue", "red", "green", "black", "white", "gray"],
        help=f"Fixation symbol colour (default: {FIXATION_DEFAULTS['symbol_colour']})"
    )
    parser.add_argument(
        "--dot-radius-px",
        type=int,
        default=FIXATION_DEFAULTS["dot_radius_px"],
        help=f"Radius of the central dot in pixels (default: {FIXATION_DEFAULTS['dot_radius_px']})"
    )
    parser.add_argument(
        "--disk-radius-px",
        type=int,
        default=FIXATION_DEFAULTS["disk_radius_px"],
        help=f"Radius of the filled disk in pixels (default: {FIXATION_DEFAULTS['disk_radius_px']})"
    )
    parser.add_argument(
        "--cross-thickness-px",
        type=int,
        default=FIXATION_DEFAULTS["cross_thickness_px"],
        help=f"Bar thickness for the cross in pixels (default: {FIXATION_DEFAULTS['cross_thickness_px']})"
    )
    parser.add_argument(
        "--cross-arm-px",
        type=int,
        default=FIXATION_DEFAULTS["cross_arm_px"],
        help=f"Half-length of each cross arm in pixels (default: {FIXATION_DEFAULTS['cross_arm_px']})"
    )
    parser.add_argument(
        "--jitter-px",
        type=int,
        default=FIXATION_DEFAULTS["jitter_px"],
        help=f"Maximum positional jitter in pixels (default: {FIXATION_DEFAULTS['jitter_px']})"
    )
    
    parser.set_defaults(func=run_fixation)


def setup_custom_subcommand(subparsers) -> None:
    """Setup 'custom' subcommand for arbitrary shape/colour combinations."""
    parser = subparsers.add_parser(
        "custom",
        help="Generate custom shape/colour combinations",
        description="Generate images with custom combinations of shapes and colours.",
        epilog="Example: cogstim custom --shapes triangle square --colours red green --train-num 50",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    
    add_common_options(parser)
    add_train_test_options(parser)
    add_shape_options(parser)
    
    parser.add_argument(
        "--shapes",
        nargs="+",
        choices=["circle", "star", "triangle", "square"],
        required=True,
        help="Shapes to include (required)"
    )
    parser.add_argument(
        "--colours",
        nargs="+",
        choices=["yellow", "blue", "red", "green", "black", "white", "gray"],
        required=True,
        help="Colours to include (required)"
    )
    
    parser.set_defaults(func=run_custom)


# =============================================================================
# Main Parser Setup
# =============================================================================


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="cogstim",
        description="Generate synthetic visual stimulus datasets for cognitive research",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available tasks:
  shapes          Shape discrimination (e.g., circles vs stars)
  colours         Colour discrimination (same shape, different colours)
  ans             Two-colour dot arrays (Approximate Number System)
  one-colour      Single-colour dot arrays (quantity discrimination)
  match-to-sample Match-to-sample dot array pairs
  lines           Rotated stripe/line patterns
  fixation        Fixation target images
  custom          Custom shape/colour combinations

Examples:
  cogstim shapes --train-num 100 --test-num 40
  cogstim ans --ratios easy --train-num 50 --demo
  cogstim fixation --all-types --background-colour black

For help on a specific task:
  cogstim <task> --help
        """,
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="cogstim 0.4.1"
    )
    
    subparsers = parser.add_subparsers(
        title="tasks",
        description="Available stimulus generation tasks",
        dest="task",
        required=False,
    )
    
    setup_shapes_subcommand(subparsers)
    setup_colours_subcommand(subparsers)
    setup_ans_subcommand(subparsers)
    setup_one_colour_subcommand(subparsers)
    setup_mts_subcommand(subparsers)
    setup_lines_subcommand(subparsers)
    setup_fixation_subcommand(subparsers)
    setup_custom_subcommand(subparsers)
    
    return parser


# =============================================================================
# Validation & Execution
# =============================================================================


def validate_and_adjust_args(args: argparse.Namespace) -> None:
    """Validate arguments and apply demo mode adjustments."""
    # Handle demo mode
    if hasattr(args, 'demo') and args.demo:
        args.train_num = 8
        args.test_num = 0
        if not args.quiet:
            print("Demo mode: generating 8 training images for quick preview.")
    
    # Set default output directories if not specified
    if args.output_dir is None:
        task_name = args.task if hasattr(args, 'task') else 'output'
        args.output_dir = f"images/{task_name}"


# =============================================================================
# Main Entry Point
# =============================================================================


def main() -> None:
    """Main CLI entry point."""
    try:
        parser = create_parser()
        args = parser.parse_args()
        
        # If no task specified, show help
        if not hasattr(args, 'func'):
            parser.print_help()
            sys.exit(0)
        
        # Validate and adjust arguments
        validate_and_adjust_args(args)
        
        # Execute the task
        args.func(args)
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(130)
    except ValueError as e:
        print(f"\nConfiguration error: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 
