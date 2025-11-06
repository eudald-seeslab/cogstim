"""CogStim: Cognitive stimulus generation library for ML experiments."""

# Import main generator classes for convenient access
from cogstim.generators.shapes import ShapesGenerator
from cogstim.generators.dots_ans import DotsANSGenerator
from cogstim.generators.dots_one_colour import DotsOneColourGenerator
from cogstim.generators.lines import LinesGenerator
from cogstim.generators.match_to_sample import MatchToSampleGenerator
from cogstim.generators.fixation import FixationGenerator

# Import base classes and utilities
from cogstim.helpers.base_generator import BaseGenerator
from cogstim.helpers.dots_core import DotsCore, PointLayoutError
from cogstim.helpers.constants import (
    COLOUR_MAP,
    IMAGE_DEFAULTS,
    DOT_DEFAULTS,
    SHAPE_DEFAULTS,
    LINE_DEFAULTS,
    FIXATION_DEFAULTS,
    MTS_DEFAULTS,
)

__all__ = [
    # Generators
    "ShapesGenerator",
    "DotsANSGenerator",
    "DotsOneColourGenerator",
    "LinesGenerator",
    "MatchToSampleGenerator",
    "FixationGenerator",
    # Base classes
    "BaseGenerator",
    "DotsCore",
    "PointLayoutError",
    # Constants
    "COLOUR_MAP",
    "IMAGE_DEFAULTS",
    "DOT_DEFAULTS",
    "SHAPE_DEFAULTS",
    "LINE_DEFAULTS",
    "FIXATION_DEFAULTS",
    "MTS_DEFAULTS",
]
