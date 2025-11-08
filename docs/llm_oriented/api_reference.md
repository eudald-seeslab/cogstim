# CogStim API Reference

Complete reference documentation for all public classes, methods, and configuration parameters.

---

## Table of Contents

1. [Generators](#generators)
   - [BaseGenerator](#basegenerator)
   - [ShapesGenerator](#shapesgenerator)
   - [DotsANSGenerator](#dotsansgenerator)
   - [DotsOneColourGenerator](#dotsonecolourgenerator)
   - [MatchToSampleGenerator](#matchtosamplegenerator)
   - [LinesGenerator](#linesgenerator)
   - [FixationGenerator](#fixationgenerator)
2. [Core Utilities](#core-utilities)
   - [DotsCore](#dotscore)
   - [ImageCanvas](#imagecanvas)
   - [GenerationPlan](#generationplan)
3. [Constants](#constants)
4. [Exceptions](#exceptions)

---

## Generators

### BaseGenerator

Abstract base class for all stimulus generators.

**Module**: `cogstim.helpers.base_generator`

**Constructor**:
```python
BaseGenerator(config: Dict[str, Any])
```

**Parameters**:
- `config` (dict): Configuration dictionary. Must include `output_dir` key.

**Attributes**:
- `config` (dict): Configuration dictionary
- `train_num` (int): Number of training image sets
- `test_num` (int): Number of test image sets
- `output_dir` (str): Output directory path

**Methods**:

#### `setup_directories()`
Create base output directory and all subdirectories.

**Returns**: None

**Raises**: OSError if directory creation fails

---

#### `get_subdirectories() -> list`
Get list of subdirectories to create within output_dir.

**Returns**: List of subdirectory paths (relative to output_dir)

**Note**: Subclasses should override this method.

---

#### `generate_images()`
Generate all images. Abstract method that must be implemented by subclasses.

**Returns**: None

---

#### `save_image(img, filename_without_ext: str, *subdirs)`
Save an image to disk with proper path construction and format handling.

**Parameters**:
- `img`: Image to save (PIL Image, ImageCanvas, or DotsCore)
- `filename_without_ext` (str): Filename without extension
- `*subdirs`: Variable number of subdirectory names

**Returns**: None

**Example**:
```python
self.save_image(img, "img_5_0", "train", "yellow")
# Saves to: output_dir/train/yellow/img_5_0.png
```

---

#### `iter_phases() -> list`
Iterate over train and test phases with their image counts.

**Returns**: List of (phase_name, num_images) tuples

**Example**:
```python
for phase, num_images in self.iter_phases():
    # phase is "train" or "test"
    # num_images is train_num or test_num
```

---

#### `get_img_format() -> str`
Get image format from configuration.

**Returns**: Image format string (e.g., 'png', 'jpeg', 'jpg')

---

#### `log_generation_info(message: str)`
Log information about the generation process.

**Parameters**:
- `message` (str): Information message to log

**Returns**: None

---

### ShapesGenerator

Generator for geometric shape discrimination tasks.

**Module**: `cogstim.generators.shapes`

**Constructor**:
```python
ShapesGenerator(
    shapes,
    colours,
    task_type,
    output_dir,
    train_num,
    test_num,
    jitter,
    min_surface,
    max_surface,
    background_colour,
    seed,
    img_format,
    version_tag,
    random_rotation,
    min_rotation=None,
    max_rotation=None
)
```

**Parameters**:
- `shapes` (list): List of shape names: ["circle", "star", "triangle", "square"]
- `colours` (list): List of colour names from COLOUR_MAP
- `task_type` (str): "two_shapes" | "two_colors" | "custom"
- `output_dir` (str): Output directory path
- `train_num` (int): Number of training image sets
- `test_num` (int): Number of test image sets
- `jitter` (bool): Enable positional jitter
- `min_surface` (int): Minimum shape surface area in pixels²
- `max_surface` (int): Maximum shape surface area in pixels²
- `background_colour` (str): Background colour name
- `seed` (int | None): Random seed for reproducibility
- `img_format` (str): Image format (default: "png")
- `version_tag` (str): Optional tag for filenames
- `random_rotation` (bool): Enable random rotation
- `min_rotation` (int): Minimum rotation angle in degrees (required if random_rotation=True)
- `max_rotation` (int): Maximum rotation angle in degrees (required if random_rotation=True)

**Configuration Defaults**:
```python
SHAPE_DEFAULTS = {
    "min_surface": 10000,
    "max_surface": 20000,
    "random_rotation": False,
    "min_rotation": 0,
    "max_rotation": 360,
}
```

**Output Structure**:
- `two_shapes`: `{phase}/{shape_name}/`
- `two_colors`: `{phase}/{colour_name}/`
- `custom`: `{phase}/{shape}_{colour}/`

**Example**:
```python
from cogstim import ShapesGenerator

gen = ShapesGenerator(
    shapes=["circle", "star"],
    colours=["yellow"],
    task_type="two_shapes",
    output_dir="images/shapes",
    train_num=50,
    test_num=20,
    jitter=True,
    min_surface=10000,
    max_surface=20000,
    background_colour="white",
    seed=42,
    img_format="png",
    version_tag="",
    random_rotation=False
)
gen.generate_images()
```

**Static Methods**:

#### `get_radius_from_surface(shape: str, surface: float) -> float`
Calculate the radius needed to achieve a specific surface area for different shapes.

**Parameters**:
- `shape` (str): "circle", "triangle", "square", or "star"
- `surface` (float): Desired surface area in pixels²

**Returns**: Radius as float

**Raises**: ValueError if shape is not implemented

---

### DotsANSGenerator

Generator for Approximate Number System (ANS) two-colour dot arrays.

**Module**: `cogstim.generators.dots_ans`

**Constructor**:
```python
DotsANSGenerator(config: dict)
```

**Parameters**:
- `config` (dict): Configuration dictionary

**Required Configuration Keys**:
- `train_num` (int): Number of training image sets
- `test_num` (int): Number of test image sets
- `output_dir` (str): Output directory path
- `ratios` (str | list): "easy" | "hard" | "all" | list of floats
- `ONE_COLOUR` (bool): If True, generates single-colour arrays
- `colour_1` (str): First colour name
- `colour_2` (str | None): Second colour name (None if ONE_COLOUR=True)
- `min_point_num` (int): Minimum number of dots per colour
- `max_point_num` (int): Maximum number of dots per colour
- `background_colour` (str): Background colour name
- `min_point_radius` (int): Minimum dot radius in pixels
- `max_point_radius` (int): Maximum dot radius in pixels
- `attempts_limit` (int): Maximum attempts for dot placement
- `seed` (int | None): Random seed
- `img_format` (str): Image format
- `version_tag` (str): Optional version tag

**Default Configuration**:
```python
GENERAL_CONFIG = {
    "colour_1": "yellow",
    "colour_2": "blue",
    "attempts_limit": 10000,
    "background_colour": "black",
    "min_point_radius": 20,
    "max_point_radius": 30,
}
```

**Ratio Constants**:
```python
ANS_EASY_RATIOS = [1/5, 1/4, 1/3, 2/5, 1/2, 3/5, 2/3, 3/4]
ANS_HARD_RATIOS = [4/5, 5/6, 6/7, 7/8, 8/9, 9/10, 10/11, 11/12]
```

**Output Structure**: `{phase}/{dominant_colour}/`

**Example**:
```python
from cogstim.generators.dots_ans import DotsANSGenerator, GENERAL_CONFIG

config = {
    **GENERAL_CONFIG,
    "train_num": 100,
    "test_num": 40,
    "output_dir": "images/ans",
    "ratios": "easy",
    "ONE_COLOUR": False,
    "min_point_num": 1,
    "max_point_num": 10,
    "seed": 42,
    "img_format": "png",
    "version_tag": "",
}
gen = DotsANSGenerator(config)
gen.generate_images()
```

**Methods**:

#### `get_positions() -> List[Tuple[int, int]]`
Get valid (n1, n2) position pairs based on configured ratios.

**Returns**: List of (n1, n2) tuples

---

#### `create_image(n1: int, n2: int, equalized: bool) -> PIL.Image`
Create a single ANS image with n1 dots of colour_1 and n2 dots of colour_2.

**Parameters**:
- `n1` (int): Number of dots for colour_1
- `n2` (int): Number of dots for colour_2
- `equalized` (bool): If True, equalize total surface areas

**Returns**: PIL Image

**Raises**: PointLayoutError if placement fails

---

### DotsOneColourGenerator

Generator for single-colour dot arrays with quantity discrimination.

**Module**: `cogstim.generators.dots_one_colour`

**Constructor**:
```python
DotsOneColourGenerator(config: dict)
```

**Parameters**:
- `config` (dict): Configuration dictionary

**Required Configuration Keys**:
- `train_num` (int): Number of training image sets
- `test_num` (int): Number of test image sets
- `output_dir` (str): Output directory path
- `colour_1` (str): Dot colour name
- `min_point_num` (int): Minimum number of dots (must be ≥ 1)
- `max_point_num` (int): Maximum number of dots
- `total_area` (float | None): Fixed total area for all images (optional)
- `init_size` (int): Image size in pixels
- `background_colour` (str): Background colour
- `mode` (str): Image mode (default: "RGB")
- `min_point_radius` (int): Minimum dot radius in pixels
- `max_point_radius` (int): Maximum dot radius in pixels
- `attempts_limit` (int): Maximum attempts for dot placement
- `seed` (int | None): Random seed
- `img_format` (str): Image format
- `version_tag` (str): Optional version tag

**Output Structure**: `{phase}/{n}/` where n is the number of dots

**Example**:
```python
from cogstim.generators.dots_one_colour import DotsOneColourGenerator

config = {
    "train_num": 50,
    "test_num": 20,
    "output_dir": "images/one_colour",
    "colour_1": "yellow",
    "min_point_num": 1,
    "max_point_num": 5,
    "total_area": None,  # or specify fixed area
    "init_size": 512,
    "background_colour": "#000000",
    "mode": "RGB",
    "min_point_radius": 20,
    "max_point_radius": 30,
    "attempts_limit": 10000,
    "seed": 42,
    "img_format": "png",
    "version_tag": "",
}
gen = DotsOneColourGenerator(config)
gen.generate_images()
```

**Methods**:

#### `create_image(n: int) -> PIL.Image`
Create a single image with n dots.

**Parameters**:
- `n` (int): Number of dots

**Returns**: PIL Image

**Raises**: PointLayoutError if placement fails

---

### MatchToSampleGenerator

Generator for match-to-sample dot array pairs with area equalization.

**Module**: `cogstim.generators.match_to_sample`

**Constructor**:
```python
MatchToSampleGenerator(config: dict)
```

**Parameters**:
- `config` (dict): Configuration dictionary

**Required Configuration Keys**:
- `train_num` (int): Number of training image sets
- `test_num` (int): Number of test image sets
- `output_dir` (str): Output directory path
- `ratios` (str | list): "easy" | "hard" | "all" | list of floats
- `min_point_num` (int): Minimum number of dots per image
- `max_point_num` (int): Maximum number of dots per image
- `dot_colour` (str): Colour for all dots
- `init_size` (int): Image size in pixels
- `background_colour` (str): Background colour
- `min_point_radius` (int): Minimum dot radius
- `max_point_radius` (int): Maximum dot radius
- `tolerance` (float): Relative tolerance for area equalization (default: 0.01)
- `abs_tolerance` (int): Absolute tolerance in pixels (default: 2)
- `attempts_limit` (int): Maximum attempts for placement
- `seed` (int | None): Random seed
- `img_format` (str): Image format
- `version_tag` (str): Optional version tag

**Default Configuration**:
```python
MTS_DEFAULTS = {
    "min_point_radius": 5,
    "max_point_radius": 15,
    "attempts_limit": 5000,
    "tolerance": 0.01,
    "abs_tolerance": 2,
    "dot_colour": "black",
    "background_colour": "white",
}
```

**Ratio Constants**:
```python
MTS_EASY_RATIOS = [2/3, 3/4, 4/5, 5/6, 6/7]
MTS_HARD_RATIOS = [7/8, 8/9, 9/10, 10/11, 11/12]
```

**Output Structure**: `{phase}/` with pairs: `img_n_m_rep_s.png` and `img_n_m_rep_m.png`

**Example**:
```python
from cogstim import MatchToSampleGenerator

config = {
    "train_num": 50,
    "test_num": 20,
    "output_dir": "images/mts",
    "ratios": "easy",
    "min_point_num": 1,
    "max_point_num": 10,
    "dot_colour": "black",
    "init_size": 512,
    "background_colour": "white",
    "min_point_radius": 5,
    "max_point_radius": 15,
    "tolerance": 0.01,
    "abs_tolerance": 2,
    "attempts_limit": 5000,
    "seed": 42,
    "img_format": "png",
    "version_tag": "",
}
gen = MatchToSampleGenerator(config)
gen.generate_images()
```

**Methods**:

#### `create_image_pair(n1: int, n2: int, equalize: bool) -> tuple | None`
Create a pair of images (sample and match).

**Parameters**:
- `n1` (int): Number of dots in sample
- `n2` (int): Number of dots in match
- `equalize` (bool): If True, equalize total areas

**Returns**: Tuple of (s_np, s_points, m_np, m_points) or None if equalization fails

**Raises**: PointLayoutError if placement fails

---

### LinesGenerator

Generator for rotated stripe/line patterns.

**Module**: `cogstim.generators.lines`

**Constructor**:
```python
LinesGenerator(config: dict)
```

**Parameters**:
- `config` (dict): Configuration dictionary

**Required Configuration Keys**:
- `train_num` (int): Number of training image sets
- `test_num` (int): Number of test image sets
- `output_dir` (str): Output directory path
- `angles` (list): List of rotation angles in degrees
- `min_stripe_num` (int): Minimum number of stripes per image
- `max_stripe_num` (int): Maximum number of stripes per image
- `img_size` (int): Image size in pixels
- `min_thickness` (int): Minimum stripe thickness in pixels
- `max_thickness` (int): Maximum stripe thickness in pixels
- `min_spacing` (int): Minimum spacing between stripes in pixels
- `max_attempts` (int): Maximum attempts for non-overlapping placement
- `background_colour` (str): Background colour
- `tag` (str): Optional tag for filenames
- `seed` (int | None): Random seed
- `img_format` (str): Image format
- `version_tag` (str): Optional version tag

**Default Configuration**:
```python
LINE_DEFAULTS = {
    "min_thickness": 10,
    "max_thickness": 30,
    "min_spacing": 5,
}
```

**Output Structure**: `{phase}/{angle}/`

**Example**:
```python
from cogstim import LinesGenerator

config = {
    "output_dir": "images/lines",
    "train_num": 50,
    "test_num": 20,
    "angles": [0, 45, 90, 135],
    "min_stripe_num": 2,
    "max_stripe_num": 10,
    "img_size": 512,
    "min_thickness": 10,
    "max_thickness": 30,
    "min_spacing": 5,
    "max_attempts": 10000,
    "background_colour": "#000000",
    "tag": "",
    "seed": 42,
    "img_format": "png",
    "version_tag": "",
}
gen = LinesGenerator(config)
gen.generate_images()
```

**Methods**:

#### `create_rotated_stripes(num_stripes: int, angle: int) -> PIL.Image`
Create an image with the specified number of stripes at the given angle.

**Parameters**:
- `num_stripes` (int): Number of stripes
- `angle` (int): Rotation angle in degrees

**Returns**: PIL Image

**Raises**: ValueError if non-overlapping positions cannot be found

---

### FixationGenerator

Generator for fixation target images (A, B, C, AB, AC, BC, ABC).

**Module**: `cogstim.generators.fixation`

**Constructor**:
```python
FixationGenerator(config: dict)
```

**Parameters**:
- `config` (dict): Configuration dictionary

**Required Configuration Keys**:
- `output_dir` (str): Output directory path
- `types` (list): List of fixation types to generate
- `img_size` (int): Image size in pixels
- `dot_radius_px` (int): Radius of central dot in pixels
- `disk_radius_px` (int): Radius of filled disk in pixels
- `cross_thickness_px` (int): Thickness of cross bars in pixels
- `cross_arm_px` (int): Half-length of cross arms in pixels
- `jitter_px` (int): Maximum positional jitter in pixels (default: 0)
- `background_colour` (str): Background colour
- `symbol_colour` (str): Symbol colour
- `tag` (str): Optional tag for filenames
- `seed` (int | None): Random seed
- `img_format` (str): Image format
- `version_tag` (str): Optional version tag

**Default Configuration**:
```python
FIXATION_DEFAULTS = {
    "img_size": 512,
    "dot_radius_px": 6,
    "disk_radius_px": 48,
    "cross_thickness_px": 12,
    "cross_arm_px": 128,
    "jitter_px": 0,
    "symbol_colour": "white",
}
```

**Fixation Types**:
- `A`: Small central dot
- `B`: Filled disk
- `C`: Cross (orthogonal bars)
- `AB`: Disk with central dot
- `AC`: Cross with central dot
- `BC`: Disk with cross-shaped cut-out
- `ABC`: Disk with cross-shaped cut-out and central dot

**Output Structure**: `{output_dir}/` (no train/test split)

**Example**:
```python
from cogstim import FixationGenerator

config = {
    "output_dir": "images/fixation",
    "types": ["A", "B", "C", "ABC"],
    "img_size": 512,
    "dot_radius_px": 6,
    "disk_radius_px": 48,
    "cross_thickness_px": 12,
    "cross_arm_px": 128,
    "jitter_px": 0,
    "background_colour": "black",
    "symbol_colour": "white",
    "tag": "",
    "seed": 42,
    "img_format": "png",
    "version_tag": "",
}
gen = FixationGenerator(config)
gen.generate_images()
```

---

## Core Utilities

### DotsCore

Core engine for dot placement with overlap prevention and area equalization.

**Module**: `cogstim.helpers.dots_core`

**Constructor**:
```python
DotsCore(
    init_size,
    colour_1,
    colour_2=None,
    bg_colour=None,
    mode=None,
    min_point_radius=None,
    max_point_radius=None,
    attempts_limit=None
)
```

**Parameters**:
- `init_size` (int): Image size in pixels (square)
- `colour_1` (str): Primary dot colour (hex or colour name)
- `colour_2` (str | None): Optional second dot colour for two-colour images
- `bg_colour` (str | None): Background colour (defaults to IMAGE_DEFAULTS["background_colour"])
- `mode` (str | None): Image mode (defaults to IMAGE_DEFAULTS["mode"])
- `min_point_radius` (int | None): Minimum dot radius (defaults to DOT_DEFAULTS["min_point_radius"])
- `max_point_radius` (int | None): Maximum dot radius (defaults to DOT_DEFAULTS["max_point_radius"])
- `attempts_limit` (int | None): Maximum attempts for placement (defaults to DOT_DEFAULTS["attempts_limit"])

**Attributes**:
- `canvas` (ImageCanvas): The image canvas
- `init_size` (int): Image size
- `colour_1` (str): First colour
- `colour_2` (str | None): Second colour
- `min_point_radius` (int): Minimum radius
- `max_point_radius` (int): Maximum radius
- `attempts_limit` (int): Attempt limit
- `boundary_width` (int): Border width (class variable, default: 5)
- `point_sep` (int): Minimum separation between dots (class variable, default: 10)
- `area_tolerance` (float): Tolerance for area equality (class variable, default: 0.001)

**Methods**:

#### `design_n_points(n: int, colour: str, point_array=None) -> list`
Place n dots of the given colour without overlap.

**Parameters**:
- `n` (int): Number of dots to place
- `colour` (str): "colour_1" or "colour_2"
- `point_array` (list | None): Existing point array to extend

**Returns**: Point array (list of ((x, y, radius), colour) tuples)

**Raises**: PointLayoutError if placement fails after attempts_limit tries

---

#### `draw_points(point_array: list) -> PIL.Image`
Draw all points in the array to the canvas.

**Parameters**:
- `point_array` (list): Point array from design_n_points()

**Returns**: PIL Image

---

#### `equalize_areas(point_array: list) -> list`
Adjust dot sizes so two colour groups have equal total area.

**Parameters**:
- `point_array` (list): Point array with two colours

**Returns**: Modified point array with equalized areas

**Raises**: PointLayoutError if equalization creates overlaps

---

#### `fix_total_area(point_array: list, target_area: float) -> list`
Scale all dots to match a specific total area.

**Parameters**:
- `point_array` (list): Point array
- `target_area` (float): Target total area in pixels²

**Returns**: Modified point array with target total area

**Raises**: PointLayoutError if current area > target area or if scaling creates issues

---

#### `scale_total_area(point_array: list, target_area: float) -> list`
Scale all radii by a common factor so total area matches target_area.

**Parameters**:
- `point_array` (list): Point array
- `target_area` (float): Target total area

**Returns**: Scaled point array

**Raises**: PointLayoutError if scaling creates overlaps or boundary violations

---

#### `scale_by_factor(point_array: list, factor: float, round_radii: bool = True) -> list`
Scale all radii by a multiplicative factor.

**Parameters**:
- `point_array` (list): Point array
- `factor` (float): Scale factor (must be > 0)
- `round_radii` (bool): Round radii to integers

**Returns**: Scaled point array

**Raises**: PointLayoutError if factor ≤ 0 or scaling creates issues

---

#### `increase_all_radii(point_array: list, increment: int = 1) -> list`
Return a new point array with all radii increased by increment.

**Parameters**:
- `point_array` (list): Point array
- `increment` (int): Pixels to add to each radius

**Returns**: Modified point array

---

#### `validate_layout(point_array: list) -> bool`
Check if all points are within boundaries and non-overlapping.

**Parameters**:
- `point_array` (list): Point array

**Returns**: True if valid, False otherwise

---

#### `compute_area(point_array: list, colour: str) -> float` (static)
Compute total area of all points with given colour.

**Parameters**:
- `point_array` (list): Point array
- `colour` (str): "colour_1" or "colour_2"

**Returns**: Total area in pixels²

---

### ImageCanvas

Wrapper for PIL Image operations.

**Module**: `cogstim.helpers.image_utils`

**Constructor**:
```python
ImageCanvas(size, bg_colour, mode="RGB")
```

**Parameters**:
- `size` (int): Image size in pixels (square)
- `bg_colour` (str): Background colour (tuple, hex string, or name)
- `mode` (str): Image mode (default: "RGB")

**Attributes**:
- `size` (int): Image size
- `mode` (str): Image mode
- `img` (PIL.Image): Underlying PIL Image (property)

**Methods**:

#### `draw_ellipse(xy, fill)`
Draw an ellipse.

**Parameters**:
- `xy` (tuple): (x1, y1, x2, y2) coordinates
- `fill` (str): Fill colour

**Returns**: None

---

#### `draw_polygon(points, fill, outline=None)`
Draw a polygon.

**Parameters**:
- `points` (list): List of (x, y) coordinate tuples
- `fill` (str): Fill colour
- `outline` (str | None): Optional outline colour

**Returns**: None

---

#### `draw_rectangle(xy, fill=None, outline=None)`
Draw a rectangle.

**Parameters**:
- `xy` (tuple): (x1, y1, x2, y2) coordinates
- `fill` (str | None): Optional fill colour
- `outline` (str | None): Optional outline colour

**Returns**: None

---

#### `draw_line(xy, fill, width=1)`
Draw a line.

**Parameters**:
- `xy` (tuple): (x1, y1, x2, y2) coordinates
- `fill` (str): Line colour
- `width` (int): Line width in pixels

**Returns**: None

---

#### `save(path, **kwargs)`
Save the image to a file.

**Parameters**:
- `path` (str): File path
- `**kwargs`: Additional arguments for PIL Image.save()

**Returns**: None

---

#### `resize(new_size) -> ImageCanvas`
Resize the image.

**Parameters**:
- `new_size` (int | tuple): New size (int for square, or (width, height))

**Returns**: New ImageCanvas with resized image

---

### GenerationPlan

Unified planning mechanism for stimulus generation across all task types.

**Module**: `cogstim.helpers.planner`

**Constructor**:
```python
GenerationPlan(
    task_type: str,
    min_point_num: int = 0,
    max_point_num: int = 0,
    num_repeats: int = 1,
    ratios: Optional[List[float]] = None,
    shapes: Optional[List[str]] = None,
    colors: Optional[List[str]] = None,
    min_surface: Optional[int] = None,
    max_surface: Optional[int] = None,
    surface_step: Optional[int] = None,
    angles: Optional[List[int]] = None,
    min_stripes: Optional[int] = None,
    max_stripes: Optional[int] = None
)
```

**Parameters**:
- `task_type` (str): Type of task ("ans", "mts", "one_colour", "shapes", "lines")
- `min_point_num` (int): Minimum number of points (for ans/mts/one_colour)
- `max_point_num` (int): Maximum number of points (for ans/mts/one_colour)
- `num_repeats` (int): Number of repetitions per combination
- `ratios` (list | None): List of ratios for ANS/MTS tasks
- `shapes` (list | None): List of shape names (for shapes tasks)
- `colors` (list | None): List of colour names (for shapes tasks)
- `min_surface` (int | None): Minimum surface area (for shapes tasks)
- `max_surface` (int | None): Maximum surface area (for shapes tasks)
- `surface_step` (int | None): Step between surface values (for shapes tasks)
- `angles` (list | None): List of rotation angles (for lines tasks)
- `min_stripes` (int | None): Minimum number of stripes (for lines tasks)
- `max_stripes` (int | None): Maximum number of stripes (for lines tasks)

**Attributes**:
- `tasks` (list): List of GenerationTask objects (populated by build())

**Methods**:

#### `build(task_subtype: Optional[str] = None) -> GenerationPlan`
Build the complete task list based on task type and parameters.

**Parameters**:
- `task_subtype` (str | None): For shapes tasks: "two_shapes", "two_colors", or "custom"

**Returns**: self (for method chaining)

**Example**:
```python
plan = GenerationPlan(
    task_type="ans",
    min_point_num=1,
    max_point_num=10,
    num_repeats=100,
    ratios=[1/2, 2/3, 3/4]
).build()

for task in plan.tasks:
    n1 = task.params['n1']
    n2 = task.params['n2']
    equalize = task.params['equalize']
    # Create image...
```

---

#### `compute_positions() -> List[Tuple[int, int]]`
Compute valid (n1, n2) position pairs based on ratios.

**Returns**: List of (n, m) tuples where n ≤ m

---

#### `write_summary_csv(output_dir: str, filename: str = "summary.csv")`
Write the generation plan as a CSV summary.

**Parameters**:
- `output_dir` (str): Directory where CSV will be written
- `filename` (str): CSV filename (default: "summary.csv")

**Returns**: None

---

#### `__len__() -> int`
Return the number of tasks in the plan.

---

#### `__iter__()`
Iterate over tasks.

---

### GenerationTask

Represents a single generation task with all parameters.

**Module**: `cogstim.helpers.planner`

**Constructor**:
```python
GenerationTask(task_type: str, rep: int = 0, **params)
```

**Parameters**:
- `task_type` (str): Type of task
- `rep` (int): Repetition/iteration number
- `**params`: Task-specific parameters

**Attributes**:
- `task_type` (str): Task type
- `rep` (int): Repetition number
- `params` (dict): Parameter dictionary

**Methods**:

#### `to_dict() -> Dict[str, Any]`
Convert task to dictionary format.

**Returns**: Dictionary with task_type, rep, and all params

---

## Constants

**Module**: `cogstim.helpers.constants`

### Colour Map

```python
COLOUR_MAP = {
    "black": "#000000",
    "blue": "#0003f9",
    "yellow": "#fffe04",
    "red": "#ff0000",
    "green": "#00ff00",
    "gray": "#808080",
    "white": "#ffffff",
}
```

### Image Defaults

```python
IMAGE_DEFAULTS = {
    "init_size": 512,
    "background_colour": "white",
    "mode": "RGB",
    "img_format": "png",
}
```

### CLI Defaults

```python
CLI_DEFAULTS = {
    "train_num": 10,
    "test_num": 0,
}
```

### Dot Defaults

```python
DOT_DEFAULTS = {
    "min_point_radius": 20,
    "max_point_radius": 30,
    "attempts_limit": 10000,
    "dot_colour": "yellow",
}
```

### Shape Defaults

```python
SHAPE_DEFAULTS = {
    "min_surface": 10000,
    "max_surface": 20000,
    "random_rotation": False,
    "min_rotation": 0,
    "max_rotation": 360,
}
```

### Line Defaults

```python
LINE_DEFAULTS = {
    "min_thickness": 10,
    "max_thickness": 30,
    "min_spacing": 5,
}
```

### Fixation Defaults

```python
FIXATION_DEFAULTS = {
    "img_size": 512,
    "dot_radius_px": 6,
    "disk_radius_px": 48,
    "cross_thickness_px": 12,
    "cross_arm_px": 128,
    "jitter_px": 0,
    "symbol_colour": "white",
}
```

### Match-to-Sample Defaults

```python
MTS_DEFAULTS = {
    "min_point_radius": 5,
    "max_point_radius": 15,
    "attempts_limit": 5000,
    "tolerance": 0.01,
    "abs_tolerance": 2,
    "dot_colour": "black",
    "background_colour": "white",
}
```

### ANS Ratios

```python
ANS_EASY_RATIOS = [
    1/5, 1/4, 1/3, 2/5, 1/2, 3/5, 2/3, 3/4
]

ANS_HARD_RATIOS = [
    4/5, 5/6, 6/7, 7/8, 8/9, 9/10, 10/11, 11/12
]
```

### Match-to-Sample Ratios

```python
MTS_EASY_RATIOS = [
    2/3, 3/4, 4/5, 5/6, 6/7
]

MTS_HARD_RATIOS = [
    7/8, 8/9, 9/10, 10/11, 11/12
]
```

---

## Exceptions

### PointLayoutError

**Module**: `cogstim.helpers.dots_core`

**Inherits**: `ValueError`

**Description**: Raised when dot placement fails (single attempt).

**Usage**:
```python
try:
    point_array = dots.design_n_points(10, "colour_1")
except PointLayoutError:
    # Handle placement failure
```

---

### TerminalPointLayoutError

**Module**: Generator modules (`dots_ans.py`, `dots_one_colour.py`)

**Inherits**: `ValueError`

**Description**: Raised when all placement attempts are exhausted.

**Usage**:
```python
try:
    generator.generate_images()
except TerminalPointLayoutError as e:
    print(f"Failed after all attempts: {e}")
```

---

## Helper Functions

### resolve_ratios

**Module**: `cogstim.helpers.planner`

```python
resolve_ratios(
    ratios: str | List[float],
    easy_ratios: List[float],
    hard_ratios: List[float]
) -> List[float]
```

**Description**: Resolve ratios from either a string mode or a direct list.

**Parameters**:
- `ratios`: Either "easy", "hard", "all", or a list of ratios
- `easy_ratios`: List of easy ratios
- `hard_ratios`: List of hard ratios

**Returns**: List of ratios

**Raises**: ValueError if string mode is invalid

**Example**:
```python
from cogstim.helpers.planner import resolve_ratios
from cogstim.helpers.constants import ANS_EASY_RATIOS, ANS_HARD_RATIOS

ratios = resolve_ratios("easy", ANS_EASY_RATIOS, ANS_HARD_RATIOS)
# Returns ANS_EASY_RATIOS

ratios = resolve_ratios("all", ANS_EASY_RATIOS, ANS_HARD_RATIOS)
# Returns ANS_EASY_RATIOS + ANS_HARD_RATIOS

ratios = resolve_ratios([1/2, 2/3], ANS_EASY_RATIOS, ANS_HARD_RATIOS)
# Returns [0.5, 0.666...]
```

---

### set_seed

**Module**: `cogstim.helpers.random_seed`

```python
set_seed(seed: int | None)
```

**Description**: Set random seed for both Python's random and numpy.random.

**Parameters**:
- `seed` (int | None): Random seed (if None, no action is taken)

**Returns**: None

**Example**:
```python
from cogstim.helpers.random_seed import set_seed

set_seed(42)  # Makes generation reproducible
set_seed(None)  # No effect (default random behavior)
```

---

## Usage Examples

### Basic Shape Generation

```python
from cogstim import ShapesGenerator

gen = ShapesGenerator(
    shapes=["circle", "star"],
    colours=["yellow"],
    task_type="two_shapes",
    output_dir="my_images/shapes",
    train_num=50,
    test_num=20,
    jitter=True,
    min_surface=10000,
    max_surface=20000,
    background_colour="white",
    seed=42,
    img_format="png",
    version_tag="v1",
    random_rotation=True,
    min_rotation=0,
    max_rotation=360
)
gen.generate_images()
```

### ANS with Custom Ratios

```python
from cogstim.generators.dots_ans import DotsANSGenerator, GENERAL_CONFIG

config = {
    **GENERAL_CONFIG,
    "train_num": 100,
    "test_num": 40,
    "output_dir": "my_images/ans_custom",
    "ratios": [1/3, 1/2, 2/3],  # Custom ratios
    "ONE_COLOUR": False,
    "colour_1": "red",
    "colour_2": "green",
    "min_point_num": 3,
    "max_point_num": 8,
    "seed": 1234,
    "img_format": "jpg",
    "version_tag": "experiment1",
}
gen = DotsANSGenerator(config)
gen.generate_images()
```

### Match-to-Sample with Tight Tolerance

```python
from cogstim import MatchToSampleGenerator

config = {
    "train_num": 50,
    "test_num": 20,
    "output_dir": "my_images/mts_tight",
    "ratios": "easy",
    "min_point_num": 2,
    "max_point_num": 6,
    "dot_colour": "blue",
    "init_size": 512,
    "background_colour": "white",
    "min_point_radius": 10,
    "max_point_radius": 20,
    "tolerance": 0.005,  # Tighter tolerance (0.5%)
    "abs_tolerance": 1,   # Tighter absolute tolerance
    "attempts_limit": 10000,
    "seed": 999,
    "img_format": "png",
    "version_tag": "tight",
}
gen = MatchToSampleGenerator(config)
gen.generate_images()
```

### Custom Line Patterns

```python
from cogstim import LinesGenerator

config = {
    "output_dir": "my_images/lines_custom",
    "train_num": 100,
    "test_num": 50,
    "angles": [0, 30, 60, 90, 120, 150],  # 6 angles
    "min_stripe_num": 5,
    "max_stripe_num": 8,
    "img_size": 1024,  # Larger images
    "min_thickness": 15,
    "max_thickness": 25,
    "min_spacing": 10,
    "max_attempts": 20000,
    "background_colour": "#ffffff",
    "tag": "exp2",
    "seed": 555,
    "img_format": "png",
    "version_tag": "",
}
gen = LinesGenerator(config)
gen.generate_images()
```

---

## Version Information

- **Package Version**: 0.5.0
- **Python Requirement**: >=3.10
- **License**: MIT

