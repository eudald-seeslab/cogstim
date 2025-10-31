#!/usr/bin/env python3
"""
Base generator class for stimulus generation.

This module provides a common base class for all stimulus generators,
encapsulating shared functionality like configuration management,
directory setup, and the image generation interface.
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseGenerator(ABC):
    """
    Abstract base class for all stimulus generators.
    
    This class provides common functionality for:
    - Configuration management
    - Output directory setup
    - Abstract interface for image generation
    
    Subclasses must implement:
    - setup_directories(): Create necessary output directories
    - generate_images() or create_images(): Generate the actual images
    
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
        """
        self.config = config
        self._logger = logging.getLogger(self.__class__.__name__)
        
        if 'output_dir' not in config:
            raise ValueError(
                "Configuration must include 'output_dir' key specifying "
                "where to save generated images."
            )
    
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



