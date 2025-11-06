#!/usr/bin/env python3
"""
Default configuration values for the cogstim package.

This module provides a single source of truth for all default values used
across generators, CLI, and tests. Any changes to defaults should be made here.
"""

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
    "min_radius": 5,
    "max_radius": 15,
    "tolerance": 0.05,
}

