"""Helper modules and utilities for the CogStim library."""

from cogstim.helpers.base_generator import BaseGenerator
from cogstim.helpers.dots_core import DotsCore, PointLayoutError
from cogstim.helpers.planner import GenerationPlan, GenerationTask, resolve_ratios
from cogstim.helpers.image_utils import ImageCanvas
from cogstim.helpers.random_seed import set_seed
from cogstim.helpers.constants import (
    COLOUR_MAP,
    IMAGE_DEFAULTS,
    DOT_DEFAULTS,
    SHAPE_DEFAULTS,
    LINE_DEFAULTS,
    FIXATION_DEFAULTS,
    MTS_DEFAULTS,
    ANS_EASY_RATIOS,
    ANS_HARD_RATIOS,
    MTS_EASY_RATIOS,
    MTS_HARD_RATIOS,
)

__all__ = [
    # Base classes
    "BaseGenerator",
    "DotsCore",
    "PointLayoutError",
    # Planning
    "GenerationPlan",
    "GenerationTask",
    "resolve_ratios",
    # Utilities
    "ImageCanvas",
    "set_seed",
    # Constants
    "COLOUR_MAP",
    "IMAGE_DEFAULTS",
    "DOT_DEFAULTS",
    "SHAPE_DEFAULTS",
    "LINE_DEFAULTS",
    "FIXATION_DEFAULTS",
    "MTS_DEFAULTS",
    "ANS_EASY_RATIOS",
    "ANS_HARD_RATIOS",
    "MTS_EASY_RATIOS",
    "MTS_HARD_RATIOS",
]

