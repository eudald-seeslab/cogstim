"""Random seed management for reproducible image generation.

This module provides utilities to control random number generation across
the cogstim package, ensuring reproducible results when a seed is specified.

Usage:
    # Set seed once at the start of generation
    from cogstim.random_seed import set_seed
    
    set_seed(1714)  # All subsequent random operations are reproducible
    generator.generate_images()  # Same images every time with seed=1714
"""

import random
import numpy as np
from typing import Optional


def set_seed(seed: Optional[int]) -> int:
    """Set the random seed for both random and numpy, and report which was used.

    A run without an explicit seed used to be unreproducible and left no record
    of what it had done. One is now drawn and returned, so callers can write it
    alongside the output and reproduce the run afterwards -- which matters for
    stimuli that end up in an experiment.

    Args:
        seed: Random seed value. If None, a seed is drawn.

    Returns:
        int: The seed actually used.

    Example:
        used = set_seed(None)   # draws, applies and reports a seed
        set_seed(used)          # reproduces that run exactly
    """
    if seed is None:
        seed = random.randrange(2 ** 32)

    random.seed(seed)
    np.random.seed(seed)
    return seed
