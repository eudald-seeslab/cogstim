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


def set_seed(seed: Optional[int]) -> None:
    """Set the random seed for both random and numpy.
    
    This sets the global random seed for both Python's random module and
    NumPy's random number generator. Call this once at the start of image
    generation to ensure reproducible results.
    
    Args:
        seed: Random seed value. If None, no seed is set (random behavior).
        
    Example:
        set_seed(1714)
        img1 = generator.create_image(n=5)
        img2 = generator.create_image(n=10)
        
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
