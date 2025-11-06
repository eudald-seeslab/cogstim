#!/usr/bin/env python3
"""
Constants and default configuration values for the cogstim package.

This module provides a single source of truth for all constants, default values,
and configuration parameters used across generators, CLI, and tests.
"""

# =============================================================================
# Color definitions
# =============================================================================

COLOUR_MAP = {
    "black": "#000000",
    "blue": "#0003f9",
    "yellow": "#fffe04",
    "red": "#ff0000",
    "green": "#00ff00",
    "gray": "#808080",
    "white": "#ffffff",
}


# =============================================================================
# Ratio configurations for discrimination tasks
# =============================================================================

# ANS ratios (two-colour dot arrays)
ANS_EASY_RATIOS = [
    1 / 5,
    1 / 4,
    1 / 3,
    2 / 5,
    1 / 2,
    3 / 5,
    2 / 3,
    3 / 4,
]

ANS_HARD_RATIOS = [
    4 / 5,
    5 / 6,
    6 / 7,
    7 / 8,
    8 / 9,
    9 / 10,
    10 / 11,
    11 / 12,
]

# Match-to-sample ratios
MTS_EASY_RATIOS = [
    2 / 3,
    3 / 4,
    4 / 5,
    5 / 6,
    6 / 7,
]

MTS_HARD_RATIOS = [
    7 / 8,
    8 / 9,
    9 / 10,
    10 / 11,
    11 / 12,
]


# =============================================================================
# Default parameters for image generation
# =============================================================================

# Image generation defaults
IMAGE_DEFAULTS = {
    "init_size": 512,
    "background_colour": "white",
    "mode": "RGB",
}

# Dot generation defaults
DOT_DEFAULTS = {
    "min_point_radius": 20,
    "max_point_radius": 30,
    "attempts_limit": 10000,
    "dot_colour": "yellow",
}

# Shape generation defaults
SHAPE_DEFAULTS = {
    "min_surface": 10000,
    "max_surface": 20000,
}

# Line generation defaults
LINE_DEFAULTS = {
    "min_thickness": 10,
    "max_thickness": 30,
    "min_spacing": 5,
}

# Fixation generation defaults
FIXATION_DEFAULTS = {
    "img_size": 512,
    "dot_radius_px": 6,
    "disk_radius_px": 48,
    "cross_thickness_px": 12,
    "cross_arm_px": 128,
    "jitter_px": 0,
    "symbol_colour": "white",
}

# Match-to-sample defaults
MTS_DEFAULTS = {
    "min_point_radius": 5,
    "max_point_radius": 15,
    "attempts_limit": 5000,
    "tolerance": 0.01,  # 1% relative difference for area equalization
    "abs_tolerance": 2,  # absolute area tolerance in pixels
    "dot_colour": "black",
    "background_colour": "white",
}

