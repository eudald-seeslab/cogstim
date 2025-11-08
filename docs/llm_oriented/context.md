# CogStim – LLM Context Documentation

## Project Overview

CogStim is a Python library for generating synthetic visual stimulus datasets used in cognitive neuroscience and psychophysics experiments. It produces PNG images of various stimuli including shapes, dots, lines, and fixation targets, organized into train/test directories by class. The library provides both a Python API and a comprehensive CLI.

**Core Purpose**: Generate reproducible, parameterized image datasets for machine learning experiments in cognitive science research.

---

## Quick Architecture Map

```
cogstim/
├── __init__.py                    # Public API exports
├── cli.py                         # Command-line interface (975 lines)
├── generators/                    # Six stimulus generators
│   ├── __init__.py
│   ├── shapes.py                 # Shape discrimination (circle, star, triangle, square)
│   ├── dots_ans.py               # Two-colour dot arrays (ANS tasks)
│   ├── dots_one_colour.py        # Single-colour dot arrays (quantity tasks)
│   ├── lines.py                  # Rotated stripe patterns
│   ├── match_to_sample.py        # Dot array pairs with area equalization
│   └── fixation.py               # Fixation targets (A, B, C, AB, AC, BC, ABC)
└── helpers/                       # Core utilities and infrastructure
    ├── __init__.py
    ├── base_generator.py         # Abstract base class for all generators
    ├── dots_core.py              # Dot placement and area equalization engine
    ├── image_utils.py            # PIL wrapper (ImageCanvas)
    ├── constants.py              # Default configurations and colour maps
    ├── mts_geometry.py           # Match-to-sample equalization algorithms
    ├── planner.py                # Task generation planning system
    ├── random_seed.py            # Seed management for reproducibility
    └── summary_writer.py         # CSV summary generation
```

---

## Core Concepts

### 1. BaseGenerator Pattern

All generators inherit from `BaseGenerator` (`helpers/base_generator.py`):
- **Configuration Management**: All generators accept a configuration dictionary
- **Directory Setup**: Automatic creation of output directories via `setup_directories()`
- **Image Saving**: Unified `save_image()` method handles all file I/O
- **Phase Iteration**: Built-in support for train/test splits via `iter_phases()`
- **Seed Handling**: Automatic random seed initialization from config

**Key Methods**:
- `__init__(config)` - Initialize with configuration dictionary
- `setup_directories()` - Create output directory structure
- `generate_images()` - Main entry point (must be implemented by subclasses)
- `save_image(img, filename_without_ext, *subdirs)` - Save image to disk
- `iter_phases()` - Iterate over ("train", train_num), ("test", test_num)

### 2. Configuration Dictionary Pattern

All generators use dictionaries for configuration, not argument lists. Common keys:
- `output_dir` (required) - Where to save images
- `train_num` - Number of training image sets
- `test_num` - Number of test image sets
- `seed` - Random seed for reproducibility
- `img_format` - Image format (png, jpg, etc.)
- `background_colour` - Background colour name
- Generator-specific parameters (shapes, colours, point numbers, etc.)

### 3. DotsCore Engine

`helpers/dots_core.py` is the core dot placement system:
- **Random Placement**: Places dots randomly within circular boundary without overlap
- **Area Equalization**: Adjusts dot sizes so two colour groups have equal total area
- **Boundary Validation**: Ensures all dots stay within image bounds
- **Overlap Prevention**: Maintains minimum separation between dots

**Key Methods**:
- `design_n_points(n, colour, point_array)` - Place n dots of given colour
- `equalize_areas(point_array)` - Make two colour groups have equal total area
- `fix_total_area(point_array, target_area)` - Scale all dots to match target area
- `draw_points(point_array)` - Render dots to image

### 4. Phase-Based Generation

All generators organize output into `train/` and `test/` subdirectories, further divided by class:

```
images/shapes/
  ├── train/
  │   ├── circle/        # Class subdirectory
  │   └── star/
  └── test/
      ├── circle/
      └── star/
```

### 5. Image Set Concept

The `--train-num` and `--test-num` CLI parameters specify **image sets**, not individual images:
- **Shapes/Colours**: ~200 images per set (all combinations of parameters)
- **ANS/Dots**: ~75 images per set (depends on ratios and point ranges)
- **Lines**: Varies by angle and stripe count combinations
- Each "set" is one complete iteration through all parameter combinations

### 6. Reproducibility via Seeds

Using `--seed INTEGER` makes generation deterministic:
- Seeds are handled by `helpers/random_seed.py`
- Same seed + same parameters = identical images
- Without seed, Python's default randomization is used

---

## Generator Reference

### ShapesGenerator (`generators/shapes.py`)

**Purpose**: Generate shape discrimination tasks with geometric shapes in various colours.

**Key Parameters**:
- `shapes` - List of shapes: ["circle", "star", "triangle", "square"]
- `colours` - List of colour names from COLOUR_MAP
- `task_type` - "two_shapes" | "two_colors" | "custom"
- `min_surface`, `max_surface` - Surface area range in pixels²
- `jitter` - Boolean, adds positional randomness
- `random_rotation` - Boolean, enables rotation
- `min_rotation`, `max_rotation` - Rotation angle range in degrees

**Output Structure**: `{phase}/{class}/` where class is shape name, colour name, or "shape_colour"

**CLI Commands**:
```bash
cogstim shapes --train-num 60 --test-num 20
cogstim colours --shape circle --colours yellow blue
cogstim custom --shapes triangle square --colours red green
```

**Python API**:
```python
from cogstim import ShapesGenerator

config = {
    "shapes": ["circle", "star"],
    "colours": ["yellow"],
    "task_type": "two_shapes",
    "output_dir": "images/shapes",
    "train_num": 10,
    "test_num": 5,
    "min_surface": 10000,
    "max_surface": 20000,
    "jitter": True,
    "background_colour": "white",
    "seed": 1234,
    "random_rotation": False,
    "img_format": "png",
    "version_tag": "",
}
gen = ShapesGenerator(**config)
gen.generate_images()
```

---

### DotsANSGenerator (`generators/dots_ans.py`)

**Purpose**: Generate Approximate Number System (ANS) two-colour dot arrays for numerosity discrimination.

**Key Parameters**:
- `ratios` - "easy" | "hard" | "all" | list of floats
- `colour_1`, `colour_2` - Colour names (e.g., "yellow", "blue")
- `ONE_COLOUR` - Boolean, if True generates single-colour arrays
- `min_point_num`, `max_point_num` - Range of dots per colour
- `min_point_radius`, `max_point_radius` - Dot size range in pixels
- `attempts_limit` - Max attempts for dot placement

**Output Structure**: `{phase}/{dominant_colour}/` where images are classified by which colour has more dots

**CLI Commands**:
```bash
cogstim ans --ratios easy --train-num 100 --test-num 40
cogstim one-colour --train-num 50 --dot-colour yellow --min-point-num 1 --max-point-num 5
```

**Python API**:
```python
from cogstim.generators.dots_ans import DotsANSGenerator, GENERAL_CONFIG

config = {
    **GENERAL_CONFIG,
    "train_num": 10,
    "test_num": 5,
    "output_dir": "images/ans",
    "ratios": "easy",
    "ONE_COLOUR": False,
    "min_point_num": 1,
    "max_point_num": 10,
    "seed": 1234,
}
gen = DotsANSGenerator(config)
gen.generate_images()
```

---

### MatchToSampleGenerator (`generators/match_to_sample.py`)

**Purpose**: Generate pairs of dot arrays (sample/match) with optional area equalization for numerosity matching tasks.

**Key Parameters**:
- `ratios` - "easy" | "hard" | "all" | list of floats
- `min_point_num`, `max_point_num` - Range of dots per image
- `dot_colour` - Single colour for all dots
- `tolerance` - Relative tolerance for area equalization (default: 0.01)
- `abs_tolerance` - Absolute area tolerance in pixels (default: 2)

**Output Structure**: `{phase}/` with pairs: `img_n_m_rep_s.png` (sample) and `img_n_m_rep_m.png` (match)

**CLI Command**:
```bash
cogstim match-to-sample --ratios easy --train-num 50 --test-num 20 --dot-colour yellow
```

**Python API**:
```python
from cogstim import MatchToSampleGenerator

config = {
    "train_num": 10,
    "test_num": 5,
    "output_dir": "images/mts",
    "ratios": "easy",
    "min_point_num": 1,
    "max_point_num": 10,
    "dot_colour": "black",
    "init_size": 512,
    "seed": 1234,
}
gen = MatchToSampleGenerator(config)
gen.generate_images()
```

---

### LinesGenerator (`generators/lines.py`)

**Purpose**: Generate rotated stripe/line patterns for orientation discrimination tasks.

**Key Parameters**:
- `angles` - List of rotation angles in degrees (e.g., [0, 45, 90, 135])
- `min_stripe_num`, `max_stripe_num` - Range of stripes per image
- `min_thickness`, `max_thickness` - Stripe thickness range in pixels
- `min_spacing` - Minimum spacing between stripes in pixels

**Output Structure**: `{phase}/{angle}/` where angle is the rotation in degrees

**CLI Command**:
```bash
cogstim lines --train-num 50 --test-num 20 --angles 0 45 90 135 --min-stripes 3 --max-stripes 5
```

**Python API**:
```python
from cogstim import LinesGenerator

config = {
    "output_dir": "images/lines",
    "train_num": 10,
    "test_num": 5,
    "angles": [0, 90],
    "min_stripe_num": 2,
    "max_stripe_num": 10,
    "img_size": 512,
    "seed": 1234,
}
gen = LinesGenerator(config)
gen.generate_images()
```

---

### FixationGenerator (`generators/fixation.py`)

**Purpose**: Generate fixation target images with different element combinations (following Thaler et al., 2013).

**Key Parameters**:
- `types` - List of fixation types: ["A", "B", "C", "AB", "AC", "BC", "ABC"]
  - A: small central dot
  - B: filled disk
  - C: cross
  - AB: disk with dot
  - AC: cross with dot
  - BC: disk with cross-shaped cut-out
  - ABC: disk with cross and central dot cut-outs
- `symbol_colour` - Colour of the fixation symbol
- `dot_radius_px` - Central dot radius in pixels
- `disk_radius_px` - Filled disk radius in pixels
- `cross_thickness_px` - Cross bar thickness in pixels
- `cross_arm_px` - Half-length of cross arms in pixels

**Output Structure**: `images/fixation/` (no train/test split)

**CLI Command**:
```bash
cogstim fixation --all-types --background-colour black --symbol-colour white
```

**Python API**:
```python
from cogstim import FixationGenerator

config = {
    "output_dir": "images/fixation",
    "types": ["A", "B", "C", "ABC"],
    "img_size": 512,
    "background_colour": "black",
    "symbol_colour": "white",
    "dot_radius_px": 6,
    "disk_radius_px": 48,
    "cross_thickness_px": 12,
    "cross_arm_px": 128,
    "seed": 1234,
}
gen = FixationGenerator(config)
gen.generate_images()
```

---

## File Map

### Where to Find Key Functionality

| Functionality | File | Key Classes/Functions |
|--------------|------|----------------------|
| Public API exports | `cogstim/__init__.py` | All generator classes, constants |
| CLI entry point | `cogstim/cli.py` | `main()`, subcommand setup |
| Shape generation | `generators/shapes.py` | `ShapesGenerator` |
| ANS dot arrays | `generators/dots_ans.py` | `DotsANSGenerator` |
| Single-colour dots | `generators/dots_one_colour.py` | `DotsOneColourGenerator` |
| Line patterns | `generators/lines.py` | `LinesGenerator` |
| Match-to-sample | `generators/match_to_sample.py` | `MatchToSampleGenerator` |
| Fixation targets | `generators/fixation.py` | `FixationGenerator` |
| Base generator class | `helpers/base_generator.py` | `BaseGenerator` (abstract) |
| Dot placement engine | `helpers/dots_core.py` | `DotsCore`, `PointLayoutError` |
| PIL image wrapper | `helpers/image_utils.py` | `ImageCanvas` |
| Configuration defaults | `helpers/constants.py` | All `*_DEFAULTS` dicts, `COLOUR_MAP` |
| Area equalization | `helpers/mts_geometry.py` | `equalize_pair()` |
| Task planning | `helpers/planner.py` | `GenerationPlan` |
| Seed management | `helpers/random_seed.py` | `set_seed()` |
| CSV summaries | `helpers/summary_writer.py` | Summary writing utilities |

---

## Common Patterns

### 1. Random Seed Handling

```python
from cogstim.helpers.random_seed import set_seed

# In any generator's __init__:
seed = config.get("seed", None)
set_seed(seed)  # Handles None gracefully
```

### 2. Image Saving

```python
# All generators use BaseGenerator.save_image():
self.save_image(img, "filename_without_ext", "train", "class_name")

# Handles:
# - Format conversion (jpeg → jpg)
# - Path construction
# - Multiple image types (PIL Image, ImageCanvas, DotsCore)
```

### 3. Directory Setup

```python
# Override get_subdirectories() to specify structure:
def get_subdirectories(self):
    subdirs = []
    for phase in ["train", "test"]:
        for class_name in self.classes:
            subdirs.append((phase, class_name))
    return subdirs

# Then call parent's setup_directories():
super().setup_directories()
```

### 4. Configuration Merging

```python
# CLI builds configs from command-line args + defaults:
config = {
    **GENERAL_CONFIG,  # Default values
    "train_num": args.train_num,  # Override with CLI args
    "test_num": args.test_num,
    "seed": args.seed,
}
```

### 5. Retry Logic for Dot Placement

```python
attempts = 0
while attempts < self.config["attempts_limit"]:
    try:
        img = self.create_image(n1, n2, equalized)
        break
    except PointLayoutError:
        attempts += 1
        if attempts == self.config["attempts_limit"]:
            raise TerminalPointLayoutError("Too many attempts")
```

---

## Constants and Defaults

From `helpers/constants.py`:

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
    "init_size": 512,           # Image size in pixels
    "background_colour": "white",
    "mode": "RGB",
    "img_format": "png",
}
```

### Dot Defaults
```python
DOT_DEFAULTS = {
    "min_point_radius": 20,     # Minimum dot radius
    "max_point_radius": 30,     # Maximum dot radius
    "attempts_limit": 10000,    # Max placement attempts
    "dot_colour": "yellow",
}
```

### Shape Defaults
```python
SHAPE_DEFAULTS = {
    "min_surface": 10000,       # Minimum shape area in pixels²
    "max_surface": 20000,       # Maximum shape area in pixels²
    "random_rotation": False,
    "min_rotation": 0,
    "max_rotation": 360,
}
```

### Ratio Configurations
```python
ANS_EASY_RATIOS = [1/5, 1/4, 1/3, 2/5, 1/2, 3/5, 2/3, 3/4]
ANS_HARD_RATIOS = [4/5, 5/6, 6/7, 7/8, 8/9, 9/10, 10/11, 11/12]

MTS_EASY_RATIOS = [2/3, 3/4, 4/5, 5/6, 6/7]
MTS_HARD_RATIOS = [7/8, 8/9, 9/10, 10/11, 11/12]
```

---

## Development Guidelines

### Creating a New Generator

1. **Inherit from BaseGenerator**:
```python
from cogstim.helpers.base_generator import BaseGenerator

class MyGenerator(BaseGenerator):
    def __init__(self, config):
        super().__init__(config)
        # Your initialization
```

2. **Implement get_subdirectories()**:
```python
def get_subdirectories(self):
    return [("train", "class1"), ("train", "class2"),
            ("test", "class1"), ("test", "class2")]
```

3. **Implement generate_images()**:
```python
def generate_images(self):
    self.setup_directories()
    
    for phase, num_images in self.iter_phases():
        for i in range(num_images):
            # Generate image
            img = self.create_image()
            # Save using parent's method
            self.save_image(img, f"img_{i}", phase, class_name)
```

4. **Use configuration dictionary pattern**:
```python
# Don't use many arguments
# Do use a config dict with sensible defaults
```

### Adding New Shapes

Edit `generators/shapes.py`:

1. Add radius calculation to `get_radius_from_surface()`:
```python
elif shape == "hexagon":
    return math.sqrt(surface / (3 * math.sqrt(3) / 2))
```

2. Add vertex calculation to `get_vertices()`:
```python
elif shape == "hexagon":
    vertices = [calculate_hexagon_vertices(center, radius)]
```

3. Add to CLI choices in `cli.py`:
```python
choices=["circle", "star", "triangle", "square", "hexagon"]
```

### Testing Conventions

- Tests live in `tests/` directory
- Use pytest for all tests
- Test files follow pattern `test_*.py`
- Run tests: `pytest tests/`
- Coverage report: `pytest --cov=cogstim`

### Code Style

- British spelling for CLI arguments (`--colour`, `--centre`)
- American spelling in code (`color` in code, unless referring to CLI)
- Use type hints where appropriate
- Docstrings for all public classes and methods
- Follow PEP 8 style guidelines

---

## CLI Architecture

The CLI (`cli.py`) uses argparse with subcommands:

```
cogstim <task> [options]
```

**Main Components**:
1. **Subcommand Setup Functions**: `setup_shapes_subcommand()`, etc.
2. **Config Builder Functions**: `build_shapes_config()`, etc.
3. **Dispatch Functions**: `run_shapes()`, etc.
4. **Common Option Groups**: `add_common_options()`, `add_train_test_options()`, etc.

**Flow**:
```
CLI args → config builder → Generator class → generate_images()
```

---

## Error Handling

### Custom Exceptions

- `PointLayoutError` - Dot placement failed (single attempt)
- `TerminalPointLayoutError` - Exhausted all placement attempts
- Both defined in relevant generator files

### Retry Pattern

Most dot-based generators use retry logic:
```python
for attempt in range(attempts_limit):
    try:
        return create_image()
    except PointLayoutError:
        if attempt == attempts_limit - 1:
            raise TerminalPointLayoutError()
```

---

## Output Format

### File Naming Conventions

**Shapes**: `{shape}_{surface}_{distance}_{angle}_{rotation}_{iteration}.png`
**Dots (ANS)**: `img_{n1}_{n2}_{tag}[_equalized][_version].png`
**Dots (One Colour)**: `img_{n}_{tag}[_ac][_version].png`
**Match-to-Sample**: `img_{n1}_{n2}_{rep}[_equalized][_version]_{s|m}.png`
**Lines**: `img_{num_stripes}_{rep}[_tag].png`
**Fixation**: `fix_{type}[_tag].png`

### Directory Structure

```
{output_dir}/
├── train/
│   ├── {class_1}/
│   │   ├── img_*.png
│   │   └── ...
│   └── {class_2}/
└── test/
    ├── {class_1}/
    └── {class_2}/
```

---

## Dependencies

**Core Dependencies** (from `pyproject.toml`):
- `Pillow>=9.0.0` - Image generation
- `numpy>=1.21.0` - Numerical operations
- `tqdm>=4.60.0` - Progress bars

**Development Dependencies**:
- `pytest`, `pytest-cov` - Testing
- `coverage`, `coveralls` - Coverage reporting
- `black`, `ruff` - Code formatting and linting

**Documentation**:
- `mkdocs-material` - Documentation generation

---

## Quick Reference

### Most Common Commands

```bash
# Shape discrimination
cogstim shapes --train-num 60 --test-num 20 --seed 1234

# Colour discrimination
cogstim colours --train-num 60 --test-num 20 --colours yellow blue

# ANS easy ratios
cogstim ans --ratios easy --train-num 100 --test-num 40

# Single-colour quantity
cogstim one-colour --train-num 50 --dot-colour red --min-point-num 1 --max-point-num 5

# Match-to-sample
cogstim match-to-sample --ratios easy --train-num 50 --test-num 20

# Lines/gratings
cogstim lines --train-num 50 --angles 0 90 --min-stripes 3 --max-stripes 5

# Fixation targets
cogstim fixation --all-types --background-colour black --symbol-colour white
```

### Python API Example

```python
from cogstim import ShapesGenerator, DotsANSGenerator

# Shapes
shapes_config = {
    "shapes": ["circle", "star"],
    "colours": ["yellow"],
    "task_type": "two_shapes",
    "output_dir": "my_images/shapes",
    "train_num": 50,
    "test_num": 20,
    "min_surface": 10000,
    "max_surface": 20000,
    "jitter": True,
    "background_colour": "white",
    "seed": 42,
    "random_rotation": False,
    "img_format": "png",
    "version_tag": "",
}
gen = ShapesGenerator(**shapes_config)
gen.generate_images()

# ANS Dots
from cogstim.generators.dots_ans import GENERAL_CONFIG

dots_config = {
    **GENERAL_CONFIG,
    "train_num": 100,
    "test_num": 40,
    "output_dir": "my_images/ans",
    "ratios": "easy",
    "ONE_COLOUR": False,
    "seed": 42,
}
dots_gen = DotsANSGenerator(dots_config)
dots_gen.generate_images()
```

---

## References

The generators implement tasks from these research papers:

- **ANS (Two-colour dots)**: Halberda, J., Mazzocco, M. M. M., & Feigenson, L. (2008). Individual differences in non-verbal number acuity correlate with maths achievement. *Nature, 455*(7213), 665-668.

- **Match-to-sample**: Sella, F., Lanfranchi, S., & Zorzi, M. (2013). Enumeration skills in Down syndrome. *Research in Developmental Disabilities, 34*(11), 3798-3806.

- **Lines**: Srinivasan, M. V. (2021). Vision, perception, navigation and 'cognition' in honeybees and applications to aerial robotics. *Biochemical and Biophysical Research Communications, 564*, 4-17.

- **Fixation targets**: Thaler, L., Schütz, A. C., Goodale, M. A., & Gegenfurtner, K. R. (2013). What is the best fixation target? The effect of target shape on stability of fixational eye movements. *Vision Research, 76*, 31–42.

---

## Version Information

- **Current Version**: 0.5.0 (from `pyproject.toml`)
- **Python Requirement**: >=3.10
- **License**: MIT
- **Repository**: https://github.com/eudald-seeslab/cogstim

