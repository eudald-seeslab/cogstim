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
from cogstim.generators.mask import MaskGenerator
from cogstim.helpers.constants import (
    IMAGE_DEFAULTS,
    DOT_DEFAULTS,
    SHAPE_DEFAULTS,
    LINE_DEFAULTS,
    FIXATION_DEFAULTS,
    MTS_DEFAULTS,
    MASK_DEFAULTS,
    CLI_DEFAULTS,
)
from cogstim.helpers import cli_options as opts
from cogstim.helpers.cli_options import add_options, parse_ratios
from cogstim.helpers.run_config import (
    argv_from_config,
    write_run_config,
    _package_version,
)


# =============================================================================
# Helper Functions
# =============================================================================


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
        "surface_step": args.surface_step_px,
        "jitter": jitter,
        "background_colour": args.background_colour,
        "seed": args.seed,
        "random_rotation": args.random_rotation,
        "min_rotation": args.min_rotation,
        "max_rotation": args.max_rotation,
        "img_format": args.img_format,
        "metadata": args.metadata,
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
        "surface_step": args.surface_step_px,
        "jitter": jitter,
        "background_colour": args.background_colour,
        "seed": args.seed,
        "random_rotation": args.random_rotation,
        "min_rotation": args.min_rotation,
        "max_rotation": args.max_rotation,
        "img_format": args.img_format,
        "metadata": args.metadata,
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
            "metadata": args.metadata,
            "version_tag": args.version_tag,
            "layout": args.layout,
            "gap": args.gap,
        },
    }

    # Allow custom colours for ANS
    # Class subdirectories are named after these colours, so they must stay
    # concrete names; only override when the user actually chose one.
    if getattr(args, 'dot_colour1', None) is not None:
        cfg["colour_1"] = args.dot_colour1
    if getattr(args, 'dot_colour2', None) is not None:
        cfg["colour_2"] = args.dot_colour2

    if getattr(args, 'tasks_csv', None):
        cfg["tasks_csv"] = args.tasks_csv
        cfg["tasks_copies"] = getattr(args, 'tasks_copies', 1)
    
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
            "colour_1": args.dot_colour or DOT_DEFAULTS["dot_colour"],
            "colour_2": None,
            "img_format": args.img_format,
            "metadata": args.metadata,
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
            "metadata": args.metadata,
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


def build_mask_config(args: argparse.Namespace) -> Dict[str, Any]:
    """Build configuration for mask generation."""
    cfg = {
        "output_dir": args.output_dir,
        "num_masks": args.num_masks,
        "num_dots": args.num_dots,
        "min_dot_radius": args.min_dot_radius,
        "max_dot_radius": args.max_dot_radius,
        "dot_colour": args.dot_colour,
        "dot_colour_2": args.dot_colour_2,
        "background_colour": args.background_colour,
        "init_size": args.img_size,
        "layout": args.layout,
        "gap": args.gap,
        "seed": args.seed,
        "img_format": args.img_format,
        "metadata": args.metadata,
        "version_tag": args.version_tag,
    }
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
        "line_colour": args.line_colour,
        "max_attempts": getattr(args, 'max_attempts', 10000),
        "background_colour": args.background_colour,
        "seed": args.seed,
        "img_format": args.img_format,
        "metadata": args.metadata,
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
        "metadata": args.metadata,
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
        "surface_step": args.surface_step_px,
        "jitter": jitter,
        "background_colour": args.background_colour,
        "seed": args.seed,
        "random_rotation": args.random_rotation,
        "min_rotation": args.min_rotation,
        "max_rotation": args.max_rotation,
        "version_tag": args.version_tag,
        "img_format": args.img_format,
        "metadata": args.metadata,
    }


# =============================================================================
# Dispatch Functions
# =============================================================================


def execute(args, config, generator, note: str = "") -> None:
    """Run the generator, or under --dry-run report what it would produce."""
    if args.dry_run:
        report_dry_run(args, config, generator, note)
        return

    generator.generate_images()

    annotation_paths = generator.write_annotations()

    # Record what was run alongside what it produced. The seed comes from the
    # generator because it may have been drawn rather than supplied, and without
    # it a run started without --seed could never be reproduced.
    config_path = None
    if generator.images_written:
        try:
            config_path = write_run_config(config["output_dir"], args, generator.seed)
        except (ImportError, OSError) as exc:
            print(f"\nWarning: could not write the run configuration: {exc}",
                  file=sys.stderr)

    report_generation(args, config, generator, note)

    if not args.quiet:
        for path in annotation_paths:
            print(f"  Stimulus annotations written to {path}")
        if config_path:
            print(f"  Options used were written to {config_path}")
            print(f"  Reproduce this run with: cogstim run {config_path}")


def report_dry_run(args, config, generator, note: str = "") -> None:
    """Print what a real run would produce, without writing anything.

    The set-to-image multiplier is large and paradigm-specific -- a single
    `shapes` set is 200 images -- so users need to see the breakdown before
    committing the disk space. The counts come from the same build_plan() the
    real run uses, so the two cannot disagree.
    """
    summary = generator.plan_summary()
    total = sum(images for _phase, _sets, images in summary)
    detail = f" ({note})" if note else ""

    # The output directory tree is still created, since generators set it up on
    # construction; no image is written.
    print(f"\nDry run: no images written{detail}.")
    for phase, sets, images in summary:
        if sets:
            per_set = images // sets if sets else 0
            print(f"  {phase}: {sets} sets x {per_set} images = {images} images")
        else:
            print(f"  {phase}: {images} images")
    print(f"  total: {total} images in '{config['output_dir']}'")


def report_generation(args, config, generator, note: str = "") -> None:
    """Print an accurate summary of what was written to disk.

    ``--train-num`` and ``--test-num`` count *sets*, not images: one set is a
    full sweep of the condition combinations a paradigm defines, so a single set
    produces many images. Reporting the set count as an image count made
    ``shapes --train-num 10 --test-num 5`` announce "15 images" while writing
    3000 files. The count comes from the generator, which tracks every file it
    actually saved, so the number is measured rather than predicted.

    Args:
        args: Parsed CLI arguments.
        config: Generator configuration (used for the output directory).
        generator: The generator that ran; supplies ``images_written``.
        note: Optional clarification appended to the set count, e.g. "image pairs".
    """
    written = generator.images_written

    if written == 0:
        # Exiting 0 having produced nothing looks like success. It usually means
        # no condition survived the requested constraints -- for instance a dot
        # count range too narrow to contain any pair matching the chosen ratios.
        print(
            "\nWarning: no images were generated. No condition matched the "
            "options given; widen --min-dot-num/--max-dot-num, choose different "
            "--ratios, or run with --dry-run to see what was planned.",
            file=sys.stderr,
        )
        return

    if args.quiet:
        return

    sets = getattr(args, "train_num", 0) + getattr(args, "test_num", 0)

    if sets > 0:
        detail = f" ({note})" if note else ""
        per_set = written // sets if sets else 0
        summary = (
            f"{written} images from {sets} sets{detail}, "
            f"{per_set} images per set"
        )
    else:
        summary = f"{written} images"

    print(f"\n✓ Generated {summary}. Output: {config['output_dir']}")


def run_shapes(args: argparse.Namespace) -> None:
    """Execute shapes generation."""
    config = build_shapes_config(args)
    generator = ShapesGenerator(**config)
    execute(args, config, generator)


def run_colours(args: argparse.Namespace) -> None:
    """Execute colour discrimination generation."""
    config = build_colours_config(args)
    generator = ShapesGenerator(**config)
    execute(args, config, generator)


def run_ans(args: argparse.Namespace) -> None:
    """Execute ANS dot array generation."""
    config = build_ans_config(args)
    generator = DotsANSGenerator(config)
    execute(args, config, generator)


def run_one_colour(args: argparse.Namespace) -> None:
    """Execute one-colour dot array generation."""
    config = build_one_colour_config(args)
    generator = DotsANSGenerator(config)
    execute(args, config, generator)


def run_mts(args: argparse.Namespace) -> None:
    """Execute match-to-sample generation."""
    config = build_mts_config(args)
    generator = MatchToSampleGenerator(config)
    execute(args, config, generator, note="image pairs")


def run_mask(args: argparse.Namespace) -> None:
    """Execute mask generation."""
    config = build_mask_config(args)
    generator = MaskGenerator(config)
    execute(args, config, generator)


def run_lines(args: argparse.Namespace) -> None:
    """Execute lines/stripes generation."""
    config = build_lines_config(args)
    generator = LinesGenerator(config)
    execute(args, config, generator)


def run_fixation(args: argparse.Namespace) -> None:
    """Execute fixation target generation."""
    config = build_fixation_config(args)
    generator = FixationGenerator(config)
    execute(args, config, generator)


def run_from_config(args: argparse.Namespace) -> None:
    """Replay a saved configuration.

    The configuration is turned back into command-line arguments and pushed
    through the normal parser, so a config file is validated exactly like a
    typed command rather than through a second, divergent code path.
    """
    argv = argv_from_config(args.config)
    if args.output_dir:
        argv += ["--output-dir", args.output_dir]

    parser = create_parser()
    replayed = parser.parse_args(argv)
    validate_and_adjust_args(replayed)
    replayed.func(replayed)


def run_custom(args: argparse.Namespace) -> None:
    """Execute custom shapes/colours generation."""
    config = build_custom_config(args)
    generator = ShapesGenerator(**config)
    execute(args, config, generator)


# =============================================================================
# Subcommand Definitions
# =============================================================================
#
# Every option comes from the registry in cogstim/helpers/cli_options.py. A
# subcommand states which groups of options it consumes; it never defines one
# itself. tests/test_cli_options.py enforces that.


def _add_subcommand(subparsers, name, *groups, help, description, epilog, func):
    """Create a subcommand from option groups in the registry."""
    parser = subparsers.add_parser(
        name,
        help=help,
        description=description,
        epilog=epilog,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    add_options(parser, *groups)
    parser.set_defaults(func=func)
    return parser


def setup_shapes_subcommand(subparsers) -> None:
    """Setup 'shapes' subcommand for shape discrimination."""
    _add_subcommand(
        subparsers, "shapes",
        opts.COMMON, opts.TRAIN_TEST, opts.SHAPE_GEOMETRY, opts.SHAPES_SPECIFIC,
        help="Generate shape discrimination dataset (e.g., circles vs stars)",
        description="Generate images of different shapes in the same colour for shape recognition tasks.",
        epilog="Example: cogstim shapes --train-num 100 --test-num 40",
        func=run_shapes,
    )


def setup_colours_subcommand(subparsers) -> None:
    """Setup 'colours' subcommand for colour discrimination."""
    _add_subcommand(
        subparsers, "colours",
        opts.COMMON, opts.TRAIN_TEST, opts.SHAPE_GEOMETRY, opts.COLOURS_SPECIFIC,
        help="Generate colour discrimination dataset (same shape, different colours)",
        description="Generate images of the same shape in different colours for colour recognition tasks.",
        epilog="Example: cogstim colours --train-num 100 --test-num 40 --colours yellow blue",
        func=run_colours,
    )


def setup_ans_subcommand(subparsers) -> None:
    """Setup 'ans' subcommand for two-colour dot arrays."""
    _add_subcommand(
        subparsers, "ans",
        opts.COMMON, opts.TRAIN_TEST, opts.RATIOS, opts.DOT_LAYOUT,
        opts.ANS_SPECIFIC, opts.SEPARATED_LAYOUT, opts.TASKS_CSV,
        help="Generate ANS (Approximate Number System) dot arrays with two colours",
        description="Generate two-colour dot array images for approximate number system tasks. Classes are based on dominant colour.",
        epilog="Example: cogstim ans --ratios easy --train-num 100 --test-num 40",
        func=run_ans,
    )


def setup_one_colour_subcommand(subparsers) -> None:
    """Setup 'one-colour' subcommand for single-colour dot arrays."""
    _add_subcommand(
        subparsers, "one-colour",
        opts.COMMON, opts.TRAIN_TEST, opts.DOT_LAYOUT, opts.ONE_COLOUR_SPECIFIC,
        help="Generate single-colour dot arrays (quantity discrimination)",
        description="Generate single-colour dot array images. Classes are based on quantity without colour cues.",
        epilog="Example: cogstim one-colour --train-num 80 --test-num 20 --dot-colour yellow",
        func=run_one_colour,
    )


def setup_mts_subcommand(subparsers) -> None:
    """Setup 'match-to-sample' subcommand."""
    _add_subcommand(
        subparsers, "match-to-sample",
        opts.COMMON, opts.TRAIN_TEST, opts.RATIOS, opts.DOT_LAYOUT,
        opts.MTS_SPECIFIC, opts.TASKS_CSV,
        help="Generate match-to-sample dot array pairs",
        description="Generate sample/match image pairs for match-to-sample tasks with area equalization.",
        epilog="Example: cogstim match-to-sample --ratios easy --train-num 50 --test-num 20",
        func=run_mts,
    )


def setup_mask_subcommand(subparsers) -> None:
    """Setup 'mask' subcommand for visual mask generation."""
    _add_subcommand(
        subparsers, "mask",
        opts.COMMON, opts.MASK_SPECIFIC, opts.MASK_LAYOUT,
        help="Generate visual mask images (dense overlapping dot patterns)",
        description="Generate N mask images filled with overlapping dots of varying sizes. "
                    "Useful as backward/forward masks in match-to-sample or ANS paradigms.",
        epilog="Example: cogstim mask --num-masks 10 --num-dots 400 --img-size 512",
        func=run_mask,
    )


def setup_lines_subcommand(subparsers) -> None:
    """Setup 'lines' subcommand for stripe patterns."""
    _add_subcommand(
        subparsers, "lines",
        opts.COMMON, opts.TRAIN_TEST, opts.LINES_SPECIFIC,
        help="Generate rotated stripe/line pattern images",
        description="Generate images with rotated stripe patterns at different angles.",
        epilog="Example: cogstim lines --train-num 50 --test-num 20 --angles 0 45 90 135",
        func=run_lines,
    )


def setup_fixation_subcommand(subparsers) -> None:
    """Setup 'fixation' subcommand for fixation targets."""
    _add_subcommand(
        subparsers, "fixation",
        opts.COMMON, opts.FIXATION_SPECIFIC,
        help="Generate fixation target images (A, B, C, AB, AC, BC, ABC)",
        description="Generate fixation target images with different element combinations.",
        epilog="Example: cogstim fixation --all-types --background-colour black",
        func=run_fixation,
    )


def setup_custom_subcommand(subparsers) -> None:
    """Setup 'custom' subcommand for arbitrary shape/colour combinations."""
    parser = _add_subcommand(
        subparsers, "custom",
        opts.COMMON, opts.TRAIN_TEST, opts.SHAPE_GEOMETRY, opts.CUSTOM_SPECIFIC,
        help="Generate custom shape/colour combinations",
        description="Generate images with custom combinations of shapes and colours.",
        epilog="Example: cogstim custom --shapes triangle square --colours red green --train-num 50",
        func=run_custom,
    )
    # Unlike the other tasks, custom has no sensible default set of stimuli.
    for action in parser._actions:
        if action.dest in ("shapes", "colours"):
            action.required = True


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
  mask            Visual masks (dense overlapping dot patterns)
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
        # Read from package metadata rather than hardcoded: the literal here had
        # drifted to 0.8.0 while pyproject.toml said 0.8.1.
        version=f"cogstim {_package_version()}",
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
    setup_mask_subcommand(subparsers)
    setup_lines_subcommand(subparsers)
    setup_fixation_subcommand(subparsers)
    setup_custom_subcommand(subparsers)

    replay = subparsers.add_parser(
        "run",
        help="Generate from a saved configuration file",
        description=(
            "Re-run a generation from the cogstim_config.yaml written alongside "
            "a previous run's output, reproducing it exactly."
        ),
        epilog="Example: cogstim run images/shapes/cogstim_config.yaml",
    )
    replay.add_argument("config", help="Path to a cogstim configuration file")
    replay.add_argument(
        "--output-dir", default=None,
        help="Write to this directory instead of the one in the configuration",
    )
    replay.set_defaults(func=run_from_config)

    return parser


# =============================================================================
# Validation & Execution
# =============================================================================


# How many shapes and colours each task needs. --shapes and --shape-colours
# accept any number of values so that the same flag means the same thing in
# every subcommand; the per-task limits are checked here instead of through
# differing nargs, which is what made --colours mean three different things.
STIMULUS_ARITY = {
    "shapes": {"shapes": 2, "colours": 1},
    "colours": {"colours": 2},
}


def validate_stimulus_arity(args: argparse.Namespace) -> None:
    """Check that a task was given as many shapes and colours as it needs."""
    expected = STIMULUS_ARITY.get(getattr(args, "task", None))
    if not expected:
        return
    for dest, count in expected.items():
        values = getattr(args, dest, None)
        if values is not None and len(values) != count:
            flag = "--shapes" if dest == "shapes" else "--shape-colours"
            raise ValueError(
                f"'{args.task}' needs exactly {count} value(s) for {flag}, "
                f"got {len(values)}: {' '.join(values)}. "
                f"Use the 'custom' task for other combinations."
            )


def validate_and_adjust_args(args: argparse.Namespace) -> None:
    """Validate arguments and apply demo mode adjustments."""
    validate_stimulus_arity(args)

    # 'mixed' was the ans spelling of what mask called 'full'. Both are accepted;
    # normalise so logs and filenames use one word for one thing.
    if getattr(args, "layout", None) == "mixed":
        args.layout = "full"

    # Handle demo mode
    if hasattr(args, 'demo') and args.demo:
        args.train_num = 8
        args.test_num = 0
        if not args.quiet:
            print("Demo mode: generating 8 training sets for quick preview.")

    # Set default output directories if not specified
    if args.output_dir is None:
        task_name = args.task if hasattr(args, 'task') else 'output'
        args.output_dir = f"images/{task_name}"


# =============================================================================
# Main Entry Point
# =============================================================================


def configure_output_encoding() -> None:
    """Make stdout/stderr tolerant of the non-ASCII glyphs we print.

    On Windows a redirected stream defaults to the locale codepage (cp1252),
    which cannot encode characters such as the check mark used in the summary
    messages. Without this, a run that generated every image correctly still
    fails as soon as its output is piped to a file, a CI log, or another process.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            # Detached or already-wrapped stream; printing still works, and the
            # errors="replace" fallback below keeps a failure from being fatal.
            pass


def main() -> None:
    """Main CLI entry point."""
    configure_output_encoding()
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
    except UnicodeEncodeError as e:
        # Subclass of ValueError, so it must be caught first or it gets reported
        # as a configuration error, which sends users looking in the wrong place.
        print(f"\nOutput encoding error: {e}", file=sys.stderr)
        sys.exit(1)
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
