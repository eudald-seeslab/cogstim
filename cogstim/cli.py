#!/usr/bin/env python3
"""Unified CLI to generate synthetic image datasets (shapes, ANS dots, one-colour dots, …).

Example usage
-------------
# Shape recognition
python -m cogstim.cli --shape_recognition --train_num 60 --test_num 20

# Colour recognition
python -m cogstim.cli --color_recognition --no-jitter

# ANS (dot arrays)
python -m cogstim.cli --ans --train_num 100 --test_num 40 --easy

# One-colour dot arrays
python -m cogstim.cli --one_colour --train_num 80 --test_num 20

# Custom shapes/colours
python -m cogstim.cli --custom --shapes triangle square --colors red green
"""

import argparse
import os

# Generators
from cogstim.shapes_creator import ShapesGenerator
from cogstim.points_creator import (
    PointsGenerator,
    GENERAL_CONFIG as ANS_GENERAL_CONFIG,
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
    ds_group.add_argument("--color_recognition", action="store_true", help="Generate circles in yellow and blue. Classes = colours")
    ds_group.add_argument("--ans", action="store_true", help="Generate dot-array images for Approximate Number System task")
    ds_group.add_argument("--one_colour", action="store_true", help="Generate single-colour dot-array images (number discrimination without colour cue)")
    ds_group.add_argument("--custom", action="store_true", help="Custom combination of shapes and colours (provide --shapes and --colors)")

    # Custom shapes/colours (only if --custom)
    parser.add_argument("--shapes", nargs="+", choices=["circle", "star", "triangle", "square"], help="Shapes to include (only with --custom)")
    parser.add_argument("--colors", nargs="+", choices=["yellow", "blue", "red", "green"], help="Colours to include (only with --custom)")

    # General generation parameters
    parser.add_argument("--train_num", type=int, default=50, help="Number of image sets for training")
    parser.add_argument("--test_num", type=int, default=50, help="Number of image sets for testing")
    parser.add_argument("--output_dir", type=str, default=None, help="Root output directory (default depends on dataset type)")

    # Shape-specific parameters
    parser.add_argument("--min_surface", type=int, default=10000, help="Minimum shape surface area (shapes datasets)")
    parser.add_argument("--max_surface", type=int, default=20000, help="Maximum shape surface area (shapes datasets)")
    parser.add_argument("--no-jitter", dest="no_jitter", action="store_true", help="Disable positional jitter for shapes datasets")

    # Dot-array-specific parameters
    parser.add_argument("--easy", action="store_true", help="Use easier ratios only for dot-array datasets")
    parser.add_argument("--version_tag", type=str, default="", help="Optional version tag appended to filenames (dot-array datasets)")
    parser.add_argument("--min_point_num", type=int, default=1, help="Minimum number of points per colour (dot-array datasets)")
    parser.add_argument("--max_point_num", type=int, default=10, help="Maximum number of points per colour (dot-array datasets)")

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
    elif args.color_recognition:
        task_type = "two_colors"
        shapes = ["circle"]
        colors = ["yellow", "blue"]
    else:  # custom
        if not args.shapes or not args.colors:
            raise ValueError("--shapes and --colors must be provided with --custom")
        task_type = "custom"
        shapes = args.shapes
        colors = args.colors

    jitter = not args.no_jitter

    output_dir = args.output_dir
    if output_dir is None:
        if task_type == "two_shapes":
            output_dir = "images/two_shapes"
        elif task_type == "two_colors":
            output_dir = "images/two_colors"
        else:
            output_dir = f"images/{'_'.join(shapes)}_{'_'.join(colors)}"

    return ShapesGenerator(
        shapes=shapes,
        colors=colors,
        task_type=task_type,
        img_dir=output_dir,
        train_num=args.train_num,
        test_num=args.test_num,
        min_surface=args.min_surface,
        max_surface=args.max_surface,
        jitter=jitter,
    )


def generate_dot_array_dataset(args: argparse.Namespace, one_colour: bool) -> None:
    """Generate train/test dot-array datasets using points_creator.ImageGenerator."""

    base_dir_default = "images/one_colour" if one_colour else "images/ans"
    base_dir = args.output_dir or base_dir_default

    for phase, num_sets in (("train", args.train_num), ("test", args.test_num)):
        cfg = ANS_GENERAL_CONFIG | {
            "NUM_IMAGES": num_sets,
            "IMG_DIR": os.path.join(base_dir, phase),
            "EASY": args.easy,
            "ONE_COLOUR": one_colour,
            "version_tag": args.version_tag,
            "min_point_num": args.min_point_num,
            "max_point_num": args.max_point_num,
        }

        generator = PointsGenerator(cfg)
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
    else:  # shapes datasets
        generator = build_shapes_generator(args)
        generator.generate_images()


if __name__ == "__main__":
    main() 