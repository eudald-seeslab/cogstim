#!/usr/bin/env python3
"""Central registry of command-line options.

Every option the CLI accepts is declared here once, and each subcommand states
which groups of options it consumes. No subcommand defines an option of its own.

This exists because the CLI had drifted: the same concept was spelled several
ways depending on where you met it (``--dot-colour1`` in ``ans`` but
``--dot-colour-2`` in ``mask``; ``--min-point-radius`` for dot arrays but
``--min-dot-radius`` for masks), the same flag meant different things
(``--colours`` took one value in ``shapes``, two in ``colours``, any number in
``custom``), and some options were simply missing from tasks that needed them.
A single declaration makes those divergences visible and, with the consistency
test in tests/test_cli_options.py, keeps them from coming back.

Renaming an option is a breaking change for anyone with scripts, so old
spellings stay accepted as deprecated aliases that warn on use.
"""

import argparse
import warnings
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Sequence

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

# The colours a stimulus or background may take. Only these names are accepted;
# hex codes and HTML/matplotlib colour names are not supported.
COLOUR_CHOICES = ["yellow", "blue", "red", "green", "black", "white", "gray"]

SHAPE_CHOICES = ["circle", "star", "triangle", "square"]

IMAGE_FORMAT_CHOICES = ["png", "jpg", "jpeg", "bmp", "tiff"]


class DeprecatedAliasAction(argparse.Action):
    """Store a value, warning when a deprecated spelling was used to supply it.

    argparse gained ``deprecated=True`` in Python 3.13; this package supports
    3.10, hence the explicit action.
    """

    def __init__(self, option_strings, dest, deprecated=(), canonical=None, **kwargs):
        self._deprecated = set(deprecated)
        self._canonical = canonical
        super().__init__(option_strings, dest, **kwargs)

    def _warn(self, option_string):
        if option_string in self._deprecated:
            warnings.warn(
                f"{option_string} is deprecated; use {self._canonical} instead.",
                DeprecationWarning,
                stacklevel=2,
            )

    def __call__(self, parser, namespace, values, option_string=None):
        self._warn(option_string)
        setattr(namespace, self.dest, values)


class DeprecatedAliasStoreTrueAction(DeprecatedAliasAction):
    """store_true variant of DeprecatedAliasAction."""

    def __init__(self, option_strings, dest, deprecated=(), canonical=None, **kwargs):
        kwargs.setdefault("nargs", 0)
        kwargs.setdefault("default", False)
        super().__init__(
            option_strings, dest, deprecated=deprecated, canonical=canonical, **kwargs
        )

    def __call__(self, parser, namespace, values, option_string=None):
        self._warn(option_string)
        setattr(namespace, self.dest, True)


@dataclass(frozen=True)
class Option:
    """A single command-line option, declared once and reused across subcommands.

    Attributes:
        name: Canonical flag, e.g. ``--min-dot-radius-px``.
        help: Help text. The unit belongs in the flag name, not only here.
        dest: argparse destination; derived from the canonical name if omitted.
        type: Value parser.
        default: Default value.
        choices: Permitted values.
        nargs: argparse nargs.
        store_true: Declare a boolean flag.
        aliases: Deprecated spellings still accepted, which warn on use.
        metavar: argparse metavar.
    """

    name: str
    help: str
    dest: Optional[str] = None
    type: Optional[Callable] = None
    default: Any = None
    choices: Optional[Sequence] = None
    nargs: Any = None
    store_true: bool = False
    aliases: tuple = ()
    metavar: Optional[str] = None

    @property
    def destination(self) -> str:
        return self.dest or self.name.lstrip("-").replace("-", "_")

    def add_to(self, parser: argparse.ArgumentParser) -> None:
        """Register this option, and any deprecated aliases, on a parser."""
        flags = [self.name, *self.aliases]
        kwargs: dict = {"dest": self.destination, "help": self.help}

        if self.store_true:
            kwargs["default"] = self.default if self.default is not None else False
            if self.aliases:
                kwargs.update(
                    action=DeprecatedAliasStoreTrueAction,
                    deprecated=self.aliases,
                    canonical=self.name,
                )
            else:
                kwargs["action"] = "store_true"
        else:
            kwargs.update(default=self.default)
            if self.type is not None:
                kwargs["type"] = self.type
            if self.choices is not None:
                kwargs["choices"] = list(self.choices)
            if self.nargs is not None:
                kwargs["nargs"] = self.nargs
            if self.metavar is not None:
                kwargs["metavar"] = self.metavar
            if self.aliases:
                kwargs.update(
                    action=DeprecatedAliasAction,
                    deprecated=self.aliases,
                    canonical=self.name,
                )

        parser.add_argument(*flags, **kwargs)


def parse_ratios(value):
    """Parse the --ratios argument: a preset name or comma-separated fractions."""
    if value in ["easy", "hard", "all"]:
        return value
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
            f"Invalid ratios: '{value}'. Must be 'easy', 'hard', 'all', or "
            "comma-separated fractions (e.g., '1/2,2/3,3/4')"
        )


# =============================================================================
# Option groups
# =============================================================================

COMMON = [
    Option("--output-dir", type=str,
           help="Root output directory (default varies by task)"),
    Option("--img-size", type=int, default=IMAGE_DEFAULTS["init_size"],
           help=f"Image size in pixels (default: {IMAGE_DEFAULTS['init_size']})"),
    Option("--img-format", type=str, default=IMAGE_DEFAULTS["img_format"],
           choices=IMAGE_FORMAT_CHOICES,
           help=f"Image file format (default: {IMAGE_DEFAULTS['img_format']})"),
    Option("--background-colour", type=str,
           default=IMAGE_DEFAULTS["background_colour"], choices=COLOUR_CHOICES,
           help=f"Background colour (default: {IMAGE_DEFAULTS['background_colour']})"),
    Option("--seed", type=int,
           help="Random seed; the same seed and options reproduce the same images"),
    Option("--version-tag", type=str, default="",
           help="Optional tag appended to every filename"),
    Option("--verbose", store_true=True, help="Enable verbose output"),
    Option("--quiet", store_true=True, help="Suppress all non-error output"),
    Option("--dry-run", store_true=True,
           help="Report how many images would be generated, and why, without writing any"),
]

TRAIN_TEST = [
    Option("--train-num", type=int, default=CLI_DEFAULTS["train_num"],
           help=("Number of training SETS to generate, not images. One set covers "
                 "every condition of the paradigm once, so it yields many images; "
                 f"use --dry-run to see how many (default: {CLI_DEFAULTS['train_num']})")),
    Option("--test-num", type=int, default=CLI_DEFAULTS["test_num"],
           help=("Number of test SETS to generate, not images "
                 f"(default: {CLI_DEFAULTS['test_num']})")),
    Option("--demo", store_true=True,
           help="Generate a small demo dataset (8 training sets)"),
]

RATIOS = [
    Option("--ratios", type=parse_ratios, default="all",
           help=("Ratio set: 'easy', 'hard', 'all', or comma-separated fractions "
                 "(e.g., '1/2,2/3,3/4') (default: all)")),
]

DOT_LAYOUT = [
    Option("--min-dot-num", dest="min_point_num", type=int, default=1,
           aliases=("--min-point-num",),
           help="Minimum number of dots per colour (default: 1)"),
    Option("--max-dot-num", dest="max_point_num", type=int, default=10,
           aliases=("--max-point-num",),
           help="Maximum number of dots per colour (default: 10)"),
    Option("--min-dot-radius-px", dest="min_point_radius", type=int,
           default=DOT_DEFAULTS["min_point_radius"], aliases=("--min-point-radius",),
           help=f"Minimum dot radius in pixels (default: {DOT_DEFAULTS['min_point_radius']})"),
    Option("--max-dot-radius-px", dest="max_point_radius", type=int,
           default=DOT_DEFAULTS["max_point_radius"], aliases=("--max-point-radius",),
           help=f"Maximum dot radius in pixels (default: {DOT_DEFAULTS['max_point_radius']})"),
    Option("--attempts-limit", type=int, default=DOT_DEFAULTS["attempts_limit"],
           help=f"Maximum attempts for dot placement (default: {DOT_DEFAULTS['attempts_limit']})"),
]

SHAPE_GEOMETRY = [
    Option("--min-surface", type=int, default=SHAPE_DEFAULTS["min_surface"],
           help=f"Minimum shape surface area in px² (default: {SHAPE_DEFAULTS['min_surface']})"),
    Option("--max-surface", type=int, default=SHAPE_DEFAULTS["max_surface"],
           help=f"Maximum shape surface area in px² (default: {SHAPE_DEFAULTS['max_surface']})"),
    Option("--surface-step-px", type=int, default=SHAPE_DEFAULTS["surface_step"],
           help=("Gap between consecutive shape surface areas. This sets how many "
                 "images a set contains: (max - min) / step per shape. Note that "
                 "the radius is rounded to whole pixels, so a step much below "
                 f"~400 produces duplicates (default: {SHAPE_DEFAULTS['surface_step']})")),
    Option("--no-jitter", store_true=True, help="Disable positional jitter"),
    Option("--random-rotation", store_true=True,
           help="Enable random rotation of shapes"),
    Option("--min-rotation", type=int, default=SHAPE_DEFAULTS["min_rotation"],
           help=f"Minimum rotation angle in degrees (default: {SHAPE_DEFAULTS['min_rotation']})"),
    Option("--max-rotation", type=int, default=SHAPE_DEFAULTS["max_rotation"],
           help=f"Maximum rotation angle in degrees (default: {SHAPE_DEFAULTS['max_rotation']})"),
]

TASKS_CSV = [
    Option("--tasks-csv", type=str, metavar="PATH",
           help=("Path to a CSV specifying tasks. When set, --ratios and "
                 "--min/--max-point-num are ignored.")),
    Option("--tasks-copies", type=int, default=1, metavar="N",
           help="Number of copies of the task distribution (default: 1)"),
]

# 'mixed' is the historical spelling of 'full' in the ans task, kept working so
# existing commands do not break. Both tasks now offer the same vocabulary.
LAYOUT_CHOICES = ["full", "mixed", "separated"]

SEPARATED_LAYOUT = [
    Option("--layout", type=str, default=DOT_DEFAULTS["layout"],
           choices=LAYOUT_CHOICES,
           help=("Dot placement: 'full' (all dots share the canvas) or "
                 "'separated' (colour 1 left, colour 2 right). "
                 "'mixed' is a deprecated synonym for 'full'.")),
    Option("--gap", type=int, default=DOT_DEFAULTS["gap"],
           help=f"Pixel gap between halves in separated layout (default: {DOT_DEFAULTS['gap']})"),
]


# --- Task-specific groups ----------------------------------------------------

SHAPES_SPECIFIC = [
    Option("--shapes", nargs="+", choices=SHAPE_CHOICES, default=["circle", "star"],
           help="The two shapes to discriminate between"),
    Option("--shape-colours", dest="colours", nargs="+", choices=COLOUR_CHOICES,
           default=["yellow"], aliases=("--colours",),
           help="The single colour both shapes are drawn in"),
]

COLOURS_SPECIFIC = [
    Option("--shape", type=str, choices=SHAPE_CHOICES, default="circle",
           help="Shape to use for both classes"),
    Option("--shape-colours", dest="colours", nargs="+", choices=COLOUR_CHOICES,
           default=["yellow", "blue"], aliases=("--colours",),
           help="The two colours to discriminate between"),
]

CUSTOM_SPECIFIC = [
    Option("--shapes", nargs="+", choices=SHAPE_CHOICES,
           help="Shapes to include (required)"),
    Option("--shape-colours", dest="colours", nargs="+", choices=COLOUR_CHOICES,
           aliases=("--colours",), help="Colours to include (required)"),
]

ANS_SPECIFIC = [
    Option("--dot-colour-1", dest="dot_colour1", type=str, choices=COLOUR_CHOICES,
           aliases=("--dot-colour1",),
           help="First dot colour (default: yellow, or its inverse when that "
                "matches the background)"),
    Option("--dot-colour-2", dest="dot_colour2", type=str, choices=COLOUR_CHOICES,
           aliases=("--dot-colour2",),
           help="Second dot colour (default: blue, or its inverse when that "
                "matches the background)"),
]

ONE_COLOUR_SPECIFIC = [
    Option("--dot-colour-1", dest="dot_colour", type=str, choices=COLOUR_CHOICES,
           aliases=("--dot-colour",),
           help=(f"Dot colour (default: {DOT_DEFAULTS['dot_colour']}, or its "
                 "inverse when that matches the background)")),
]

MTS_SPECIFIC = [
    Option("--dot-colour-1", dest="dot_colour", type=str, choices=COLOUR_CHOICES,
           aliases=("--dot-colour",),
           help=(f"Dot colour (default: {MTS_DEFAULTS['dot_colour']}, or its "
                 "inverse when that matches the background)")),
    Option("--tolerance", type=float,
           help=f"Relative tolerance for area equalization (default: {MTS_DEFAULTS['tolerance']})"),
    Option("--abs-tolerance", type=int,
           help=f"Absolute area tolerance in pixels (default: {MTS_DEFAULTS['abs_tolerance']})"),
]

MASK_SPECIFIC = [
    Option("--mask-num", dest="num_masks", aliases=("--num-masks",), type=int, default=MASK_DEFAULTS["num_masks"],
           help=f"Number of mask variants to generate (default: {MASK_DEFAULTS['num_masks']})"),
    Option("--dot-num", dest="num_dots", aliases=("--num-dots",), type=int, default=MASK_DEFAULTS["num_dots"],
           help=f"Number of dots per mask (default: {MASK_DEFAULTS['num_dots']})"),
    Option("--min-dot-radius-px", dest="min_dot_radius", type=int,
           default=MASK_DEFAULTS["min_dot_radius"], aliases=("--min-dot-radius",),
           help=f"Minimum dot radius in pixels (default: {MASK_DEFAULTS['min_dot_radius']})"),
    Option("--max-dot-radius-px", dest="max_dot_radius", type=int,
           default=MASK_DEFAULTS["max_dot_radius"], aliases=("--max-dot-radius",),
           help=f"Maximum dot radius in pixels (default: {MASK_DEFAULTS['max_dot_radius']})"),
    Option("--dot-colour-1", dest="dot_colour", type=str, choices=COLOUR_CHOICES,
           aliases=("--dot-colour",),
           help=(f"Dot colour (default: {MASK_DEFAULTS['dot_colour']}, or its "
                 "inverse when that matches the background)")),
    Option("--dot-colour-2", type=str, choices=COLOUR_CHOICES,
           help="Optional second dot colour; each dot is randomly assigned one of the two"),
]

MASK_LAYOUT = [
    Option("--layout", type=str, default="full", choices=LAYOUT_CHOICES,
           help=("'full' fills the entire canvas; 'separated' splits it into two "
                 "halves with a gap. 'mixed' is a deprecated synonym for 'full'.")),
    Option("--gap", type=int, default=DOT_DEFAULTS["gap"],
           help=f"Pixel gap between halves in separated layout (default: {DOT_DEFAULTS['gap']})"),
]

LINES_SPECIFIC = [
    Option("--angles", type=int, nargs="+", default=[0, 45, 90, 135],
           help="Rotation angles for stripe patterns"),
    # Left unset so the generator can fall back to a colour that contrasts with
    # whatever background was chosen; an explicit value here is always honoured.
    Option("--line-colour-1", dest="line_colour", type=str, choices=COLOUR_CHOICES,
           help=(f"Stripe colour (default: {LINE_DEFAULTS['line_colour']}, or its "
                 "inverse when that matches the background)")),
    Option("--min-stripe-num", dest="min_stripes", type=int, default=2,
           aliases=("--min-stripes",), help="Minimum number of stripes per image"),
    Option("--max-stripe-num", dest="max_stripes", type=int, default=10,
           aliases=("--max-stripes",), help="Maximum number of stripes per image"),
    Option("--min-line-thickness-px", dest="min_thickness", type=int,
           default=LINE_DEFAULTS["min_thickness"], aliases=("--min-thickness",),
           help=f"Minimum stripe thickness in pixels (default: {LINE_DEFAULTS['min_thickness']})"),
    Option("--max-line-thickness-px", dest="max_thickness", type=int,
           default=LINE_DEFAULTS["max_thickness"], aliases=("--max-thickness",),
           help=f"Maximum stripe thickness in pixels (default: {LINE_DEFAULTS['max_thickness']})"),
    Option("--min-line-spacing-px", dest="min_spacing", type=int,
           default=LINE_DEFAULTS["min_spacing"], aliases=("--min-spacing",),
           help=f"Minimum gap between stripes in pixels (default: {LINE_DEFAULTS['min_spacing']})"),
]

FIXATION_SPECIFIC = [
    Option("--types", nargs="+", choices=["A", "B", "C", "AB", "AC", "BC", "ABC"],
           default=["A", "B", "C", "AB", "AC", "BC", "ABC"],
           help="Fixation target types to generate"),
    Option("--all-types", store_true=True, help="Generate all fixation types"),
    # See the note on --line-colour-1.
    Option("--symbol-colour", type=str, choices=COLOUR_CHOICES,
           help=(f"Fixation symbol colour (default: {FIXATION_DEFAULTS['symbol_colour']}, "
                 "or its inverse when that matches the background)")),
    Option("--dot-radius-px", type=int, default=FIXATION_DEFAULTS["dot_radius_px"],
           help=f"Radius of the central dot in pixels (default: {FIXATION_DEFAULTS['dot_radius_px']})"),
    Option("--disk-radius-px", type=int, default=FIXATION_DEFAULTS["disk_radius_px"],
           help=f"Radius of the filled disk in pixels (default: {FIXATION_DEFAULTS['disk_radius_px']})"),
    Option("--cross-thickness-px", type=int, default=FIXATION_DEFAULTS["cross_thickness_px"],
           help=f"Bar thickness for the cross in pixels (default: {FIXATION_DEFAULTS['cross_thickness_px']})"),
    Option("--cross-arm-px", type=int, default=FIXATION_DEFAULTS["cross_arm_px"],
           help=f"Half-length of each cross arm in pixels (default: {FIXATION_DEFAULTS['cross_arm_px']})"),
    Option("--jitter-px", type=int, default=FIXATION_DEFAULTS["jitter_px"],
           help=f"Maximum positional jitter in pixels (default: {FIXATION_DEFAULTS['jitter_px']})"),
]


def add_options(parser: argparse.ArgumentParser, *groups) -> None:
    """Register the given option groups on a parser.

    Args:
        parser: The subcommand parser.
        *groups: Sequences of Option, or individual Option instances.
    """
    for group in groups:
        options = [group] if isinstance(group, Option) else group
        for option in options:
            option.add_to(parser)
