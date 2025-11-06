#!/usr/bin/env python3
"""
Image utility classes for the cogstim package.

This module provides a wrapper over PIL Image operations to centralize
all image creation and drawing functionality.
"""
from PIL import Image, ImageDraw


class ImageCanvas:
    """Wrapper class for PIL Image and ImageDraw operations.
    
    This class encapsulates all PIL library calls, providing a clean interface
    for creating and drawing on images across all generators.
    """
    
    def __init__(self, size, bg_colour, mode="RGB"):
        """Create a blank image canvas.
        
        Args:
            size: Image size in pixels (creates a square image)
            bg_colour: Background colour (tuple, hex string, or colour name)
            mode: Image mode (default "RGB")
        """
        self._img = Image.new(mode, (size, size), color=bg_colour)
        self._draw = ImageDraw.Draw(self._img)
        self.size = size
        self.mode = mode
    
    @property
    def img(self):
        """Access underlying PIL Image."""
        return self._img
    
    def draw_ellipse(self, xy, fill):
        """Draw an ellipse.
        
        Args:
            xy: Tuple of (x1, y1, x2, y2) coordinates
            fill: Fill colour
        """
        self._draw.ellipse(xy, fill=fill)
    
    def draw_line(self, xy, fill, width=1):
        """Draw a line.
        
        Args:
            xy: Tuple of (x1, y1, x2, y2) coordinates
            fill: Line colour
            width: Line width in pixels
        """
        self._draw.line(xy, fill=fill, width=width)
    
    def draw_polygon(self, points, fill, outline=None):
        """Draw a polygon.
        
        Args:
            points: List of (x, y) coordinate tuples
            fill: Fill colour
            outline: Optional outline colour
        """
        self._draw.polygon(points, fill=fill, outline=outline)
    
    def draw_rectangle(self, xy, fill=None, outline=None):
        """Draw a rectangle.
        
        Args:
            xy: Tuple of (x1, y1, x2, y2) coordinates
            fill: Optional fill colour
            outline: Optional outline colour
        """
        self._draw.rectangle(xy, fill=fill, outline=outline)
    
    def save(self, path, **kwargs):
        """Save the image to a file.
        
        Args:
            path: File path to save to
            **kwargs: Additional arguments passed to PIL Image.save()
        """
        self._img.save(path, **kwargs)
    
    def resize(self, new_size):
        """Resize the image.
        
        Args:
            new_size: New size in pixels (for square image) or (width, height) tuple
            
        Returns:
            New ImageCanvas with resized image
        """
        if isinstance(new_size, int):
            new_size = (new_size, new_size)
        resized_img = self._img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Create new ImageCanvas with resized image
        canvas = ImageCanvas.__new__(ImageCanvas)
        canvas._img = resized_img
        canvas._draw = ImageDraw.Draw(resized_img)
        canvas.size = new_size[0] if new_size[0] == new_size[1] else new_size
        canvas.mode = self.mode
        return canvas
