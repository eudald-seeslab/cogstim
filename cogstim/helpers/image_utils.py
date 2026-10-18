#!/usr/bin/env python3
"""
Image utility classes for the cogstim package.

This module provides a wrapper over PIL Image operations to centralize
all image creation and drawing functionality. 
"""
import logging

from PIL import Image, ImageDraw

from cogstim.helpers.constants import COLOUR_MAP
from cogstim.helpers.geometry import (
    DrawnElement,
    Scene,
    ELLIPSE,
    RECTANGLE,
    POLYGON,
    LINE,
)

_logger = logging.getLogger(__name__)


def to_hex(colour):
    """Resolve a colour name to its hex code, passing hex codes through."""
    return COLOUR_MAP.get(colour, colour)


def _luminance(hex_colour):
    """Perceived luminance of a #rrggbb colour, 0 (black) to 1 (white)."""
    value = hex_colour.lstrip("#")
    if len(value) != 6:
        return 0.5
    try:
        r, g, b = (int(value[i:i + 2], 16) / 255 for i in (0, 2, 4))
    except ValueError:
        return 0.5
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def resolve_stimulus_colour(requested, background, default):
    """Pick a stimulus colour that is actually visible against the background.

    Drawing a stimulus in the background colour yields a blank image. That is
    not hypothetical: `cogstim lines` drew white stripes on the default white
    background, and `cogstim fixation --all-types` drew white symbols on white,
    so both produced entirely blank output out of the box.

    An explicitly requested colour is always honoured -- silently substituting a
    colour the caller asked for would be worse than a blank image -- but it warns.
    A colour that merely came from a default is replaced by black or white,
    whichever contrasts with the background.

    Args:
        requested: Colour the caller asked for, or None to use the default.
        background: Background colour name or hex code.
        default: Colour to use when nothing was requested.

    Returns:
        str: Hex colour code to draw with.
    """
    background_hex = to_hex(background)

    if requested is not None:
        colour_hex = to_hex(requested)
        if colour_hex == background_hex:
            _logger.warning(
                f"Stimulus colour '{requested}' is the same as the background; "
                "the generated images will be blank."
            )
        return colour_hex

    default_hex = to_hex(default)
    if default_hex != background_hex:
        return default_hex

    return "#000000" if _luminance(background_hex) > 0.5 else "#ffffff"


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
        # Everything drawn here is also recorded, which is what lets the same
        # stimulus be written as vector output or exported as annotations.
        self.scene = Scene(width=size, height=size, background=to_hex(bg_colour))

    @property
    def img(self):
        """Access underlying PIL Image."""
        return self._img

    @property
    def elements(self):
        """The primitives drawn on this canvas, in drawing order."""
        return self.scene.elements

    @classmethod
    def from_image(cls, img, scene):
        """Wrap an already-rendered image together with its geometry.

        Used where a generator transforms the rasterised image after drawing --
        the lines task rotates and crops -- and needs to carry the matching
        transformed geometry alongside it.

        Args:
            img: A PIL Image.
            scene: The Scene describing it, in the image's own coordinates.

        Returns:
            ImageCanvas: A canvas backed by that image.
        """
        canvas = cls.__new__(cls)
        canvas._img = img
        canvas._draw = ImageDraw.Draw(img)
        canvas.size = img.size[0]
        canvas.mode = img.mode
        canvas.scene = scene
        return canvas

    @staticmethod
    def _corners(xy):
        """Normalise PIL's several bounding-box spellings to two corner points."""
        if len(xy) == 2:
            (x0, y0), (x1, y1) = xy
        else:
            x0, y0, x1, y1 = xy
        return ((x0, y0), (x1, y1))

    def draw_ellipse(self, xy, fill, label="ellipse"):
        """Draw an ellipse.
        
        Args:
            xy: Tuple of (x1, y1, x2, y2) coordinates
            fill: Fill colour
            label: What this element is in the stimulus, recorded for export
        """
        self._draw.ellipse(xy, fill=fill)
        self.scene.add(DrawnElement(ELLIPSE, self._corners(xy), to_hex(fill), label))
    
    def draw_line(self, xy, fill, width=1):
        """Draw a line.
        
        Args:
            xy: Tuple of (x1, y1, x2, y2) coordinates
            fill: Line colour
            width: Line width in pixels
        """
        self._draw.line(xy, fill=fill, width=width)
        self.scene.add(
            DrawnElement(LINE, self._corners(xy), to_hex(fill), "line", width)
        )
    
    def draw_polygon(self, points, fill, outline=None, label="polygon"):
        """Draw a polygon.
        
        Args:
            points: List of (x, y) coordinate tuples
            fill: Fill colour
            outline: Optional outline colour
            label: What this element is in the stimulus, recorded for export
        """
        self._draw.polygon(points, fill=fill, outline=outline)
        self.scene.add(
            DrawnElement(POLYGON, tuple(tuple(p) for p in points), to_hex(fill), label)
        )
    
    def draw_rectangle(self, xy, fill=None, outline=None, label="rectangle"):
        """Draw a rectangle.
        
        Args:
            xy: Tuple of (x1, y1, x2, y2) coordinates
            fill: Optional fill colour
            outline: Optional outline colour
            label: What this element is in the stimulus, recorded for export
        """
        self._draw.rectangle(xy, fill=fill, outline=outline)
        if fill is not None:
            self.scene.add(
                DrawnElement(RECTANGLE, self._corners(xy), to_hex(fill), label)
            )
    
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
