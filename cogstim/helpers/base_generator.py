#!/usr/bin/env python3
"""
Base generator class for stimulus generation.

This module provides a common base class for all stimulus generators,
encapsulating shared functionality like configuration management,
directory setup, and the image generation interface.
"""

import os
import logging
from abc import ABC
from typing import Dict, Any
from cogstim.helpers.random_seed import set_seed


class BaseGenerator(ABC):
    """
    Abstract base class for all stimulus generators.
    
    This class provides common functionality for:
    - Configuration management
    - Output directory setup
    - Abstract interface for image generation
    
    Subclasses must implement:
    - setup_directories(): Create necessary output directories
    - generate_images(): Generate the actual images
    
    Attributes:
        config (dict): Configuration dictionary for the generator
        output_dir (str): Primary output directory path
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the base generator.
        
        Args:
            config: Configuration dictionary containing generator parameters.
                   Must include 'output_dir' key specifying where to save images.
                   Optional 'seed' key for reproducible random generation.
        """
        self.config = config
        self._logger = logging.getLogger(self.__class__.__name__)
        
        if 'output_dir' not in config:
            raise ValueError(
                "Configuration must include 'output_dir' key specifying "
                "where to save generated images."
            )
        
        # Initialize common generator parameters
        self.train_num = config.get("train_num", 0)
        self.test_num = config.get("test_num", 0)
        
        # Set seed for reproducibility if provided
        seed = config.get("seed", None)
        set_seed(seed)
    
    @property
    def output_dir(self) -> str:
        """
        Get the output directory path.
        
        Returns:
            str: The output directory path from config['output_dir']
        """
        return self.config['output_dir']
    
    def get_subdirectories(self) -> list:
        """
        Get list of subdirectories to create within output_dir.
        
        Returns:
            list: List of subdirectory paths (relative to output_dir).
                  Each item can be a string or tuple of path components.
                  Return empty list if no subdirectories are needed.
        """
        return []
    
    def setup_directories(self):
        """
        Create base output directory and all subdirectories.
        """
        os.makedirs(self.output_dir, exist_ok=True)
        
        for subdir in self.get_subdirectories():
            if isinstance(subdir, (list, tuple)):
                path = os.path.join(self.output_dir, *subdir)
            else:
                path = os.path.join(self.output_dir, subdir)
            os.makedirs(path, exist_ok=True)
    
    def log_generation_info(self, message: str):
        """
        Log information about the generation process.
        
        Args:
            message: Information message to log
        """
        self._logger.info(message)
    
    def iter_phases(self):
        """
        Iterate over train and test phases with their image counts.
        
        Yields:
            tuple: (phase_name, num_images) pairs for "train" and "test"
        """
        return [("train", self.train_num), ("test", self.test_num)]
    
    def write_summary_if_enabled(self, plan, phase: str):
        """
        Write summary CSV for the given phase if summary is enabled in config.
        
        Args:
            plan: GenerationPlan instance with tasks to summarize
            phase: Phase name ("train" or "test")
        """
        if self.config.get("summary", False):
            phase_output_dir = os.path.join(self.output_dir, phase)
            plan.write_summary_csv(phase_output_dir)



