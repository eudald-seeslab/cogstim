# CogStim – Complete LLM Documentation

**Single-file documentation optimized for Large Language Model consumption.**

This document combines all technical documentation for the CogStim repository:
1. **Context & Overview** - Quick start and core concepts
2. **Architecture** - System design and patterns
3. **API Reference** - Complete class and method documentation

**Version**: 0.5.0  
**Last Updated**: Auto-generated  
**Repository**: https://github.com/eudald-seeslab/cogstim

---

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



---

# CogStim Architecture

## Overview

CogStim follows a template method pattern with a plugin-style generator architecture. All stimulus generators inherit from a common base class that handles infrastructure (directories, saving, configuration), while specialized generators implement domain-specific image creation logic.

**Design Principles**:
1. **Separation of Concerns**: Infrastructure vs domain logic
2. **Configuration over Arguments**: Dictionary-based configuration
3. **Template Method Pattern**: Base class defines skeleton, subclasses fill in details
4. **Unified Planning**: Centralized task generation via `GenerationPlan`
5. **Reproducibility**: Seed-controlled randomization throughout

---

## Class Hierarchy

### Core Abstract Base

```
BaseGenerator (abstract)
    ├── ShapesGenerator
    ├── DotsANSGenerator
    ├── DotsOneColourGenerator
    ├── LinesGenerator
    ├── MatchToSampleGenerator
    └── FixationGenerator
```

### Supporting Classes

```
DotsCore
    └── Used by: DotsANSGenerator, DotsOneColourGenerator, MatchToSampleGenerator

ImageCanvas
    └── Used by: All generators for PIL operations

GenerationPlan
    └── Used by: All generators for task planning

GenerationTask
    └── Created by: GenerationPlan
    └── Consumed by: All generators
```

---

## Class Relationships

### Inheritance Relationship

**BaseGenerator** provides:
- Configuration management (`self.config`)
- Directory creation (`setup_directories()`, `get_subdirectories()`)
- Image saving (`save_image()`)
- Phase iteration (`iter_phases()`)
- Seed initialization (via `random_seed.py`)
- Summary writing (`write_summary_if_enabled()`)

**Concrete Generators** implement:
- `get_subdirectories()` - Define output directory structure
- `generate_images()` - Main generation logic
- Domain-specific image creation methods

### Composition Relationships

**DotsCore** is composed within dot-based generators:
- **DotsANSGenerator**: Creates two DotsCore instances for two-colour arrays
- **DotsOneColourGenerator**: Creates one DotsCore instance
- **MatchToSampleGenerator**: Creates two DotsCore instances (sample and match)

**ImageCanvas** is used by all generators:
- Wraps PIL Image and ImageDraw
- Provides consistent drawing interface
- Used directly in ShapesGenerator, LinesGenerator, FixationGenerator
- Used indirectly through DotsCore in dot-based generators

**GenerationPlan** orchestrates task generation:
- Each generator creates a plan with task-specific parameters
- Plan computes all parameter combinations
- Generator iterates over plan tasks to create images

---

## Data Flow

### High-Level Flow

```
CLI Args / Python Config
    ↓
Configuration Dictionary
    ↓
Generator Constructor
    ↓
generate_images() called
    ↓
setup_directories()
    ↓
For each phase (train/test):
    ↓
    GenerationPlan.build()
    ↓
    For each task in plan:
        ↓
        Create image with parameters
        ↓
        Save image via save_image()
```

### Detailed Flow for Shapes

```
ShapesGenerator.__init__(config)
    ↓
BaseGenerator.__init__(config)
    ↓
set_seed(config.get("seed"))
    ↓
generate_images() called
    ↓
setup_directories()
    │   ↓
    │   os.makedirs() for each class directory
    ↓
For phase in ["train", "test"]:
    ↓
    GenerationPlan.build()
    │   ↓
    │   Compute all (shape, color, surface) combinations
    │   ↓
    │   Create GenerationTask for each × num_repeats
    ↓
    For task in plan.tasks:
        ↓
        draw_shape(shape, surface, color)
        │   ↓
        │   ImageCanvas(size, bg_color)
        │   ↓
        │   Calculate radius from surface
        │   ↓
        │   Apply jitter if enabled
        │   ↓
        │   Apply rotation if enabled
        │   ↓
        │   get_vertices(shape, center, radius, rotation)
        │   ↓
        │   canvas.draw_ellipse() or canvas.draw_polygon()
        │   ↓
        │   Return PIL Image
        ↓
        save_image(img, filename, phase, class)
        │   ↓
        │   Construct full path
        │   ↓
        │   Handle format conversion
        │   ↓
        │   PIL Image.save()
```

### Detailed Flow for ANS Dots

```
DotsANSGenerator.__init__(config)
    ↓
BaseGenerator.__init__(config)
    ↓
resolve_ratios() → self.ratios
    ↓
setup_directories()
    ↓
generate_images() called
    ↓
For phase in ["train", "test"]:
    ↓
    GenerationPlan.build()
    │   ↓
    │   compute_positions() based on ratios
    │   ↓
    │   expand_ans_tasks() for each position
    │       ↓
    │       Create 4 tasks per (n, m):
    │       - (n, m) non-equalized
    │       - (m, n) non-equalized
    │       - (n, m) equalized
    │       - (m, n) equalized
    ↓
    For task in plan.tasks:
        ↓
        create_image(n1, n2, equalized)
        │   ↓
        │   DotsCore(init_size, colour_1, colour_2, ...)
        │   ↓
        │   design_n_points(n1, "colour_1")
        │   │   ↓
        │   │   For each point:
        │   │       ↓
        │   │       _create_random_point()
        │   │       │   ↓
        │   │       │   Random position within circular boundary
        │   │       │   ↓
        │   │       │   Random radius in [min_radius, max_radius]
        │   │       ↓
        │   │       _check_no_overlaps()
        │   │       │   ↓
        │   │       │   Check distance > sum of radii + separation
        │   │       ↓
        │   │       Retry if overlapping (up to attempts_limit)
        │   ↓
        │   design_n_points(n2, "colour_2", point_array)
        │   ↓
        │   If equalized:
        │       ↓
        │       equalize_areas(point_array)
        │       │   ↓
        │       │   Compute area for each colour
        │       │   ↓
        │       │   Incrementally increase smaller colour radii
        │       │   ↓
        │       │   Check no overlaps after adjustment
        │   ↓
        │   draw_points(point_array)
        │   │   ↓
        │   │   canvas.draw_ellipse() for each point
        │   ↓
        │   Return PIL Image
        ↓
        save_image(img, filename, phase, colour_class)
```

### Detailed Flow for Match-to-Sample

```
MatchToSampleGenerator.generate_images()
    ↓
For phase in ["train", "test"]:
    ↓
    GenerationPlan.build()
    │   ↓
    │   compute_positions() based on ratios
    │   ↓
    │   expand_mts_tasks() for each position
    │       ↓
    │       Create 6 tasks per (n, m):
    │       - (n, m) non-equalized
    │       - (m, n) non-equalized
    │       - (n, m) equalized
    │       - (m, n) equalized
    │       - (n, n) equalized
    │       - (m, m) non-equalized
    ↓
    For task in plan.tasks:
        ↓
        create_image_pair(n1, n2, equalize)
        │   ↓
        │   Create sample DotsCore
        │   ↓
        │   design_n_points(n1) → s_points
        │   ↓
        │   Create match DotsCore
        │   ↓
        │   design_n_points(n2) → m_points
        │   ↓
        │   If equalize:
        │       ↓
        │       equalize_pair(s_np, s_points, m_np, m_points)
        │       │   ↓
        │       │   Compute area_s and area_m
        │       │   ↓
        │       │   Try scale_total_area() on smaller set
        │       │   │   ↓
        │       │   │   scale_factor = sqrt(target_area / current_area)
        │       │   │   ↓
        │       │   │   Scale all radii uniformly
        │       │   │   ↓
        │       │   │   Validate boundaries and overlaps
        │       │   ↓
        │       │   If scaling fails:
        │       │       ↓
        │       │       Incremental increase by +1px per iteration
        │       │       ↓
        │       │       Check tolerance after each increase
        │   ↓
        │   Return (s_np, s_points, m_np, m_points)
        ↓
        save_image_pair()
        │   ↓
        │   save_image(sample, filename_s, phase)
        │   ↓
        │   save_image(match, filename_m, phase)
```

---

## Key Design Decisions

### 1. Configuration Dictionary Pattern

**Decision**: Use dictionaries for configuration instead of long argument lists.

**Rationale**:
- Easier to merge defaults with user-provided values
- Simplifies passing configuration down the call stack
- Makes it easy to add new parameters without changing signatures
- Better for CLI-to-API translation

**Implementation**:
```python
config = {
    **DEFAULT_CONFIG,
    "train_num": args.train_num,
    "output_dir": args.output_dir,
    "seed": args.seed,
}
generator = MyGenerator(config)
```

### 2. Template Method Pattern for Generators

**Decision**: BaseGenerator defines the skeleton, subclasses implement specifics.

**Rationale**:
- Eliminates code duplication across generators
- Ensures consistent behavior (directory creation, image saving)
- Separates infrastructure from domain logic
- Makes it easy to add new generators

**Implementation**:
```python
class BaseGenerator(ABC):
    def __init__(self, config):
        # Common initialization
    
    def save_image(self, img, filename, *subdirs):
        # Common saving logic
    
    def iter_phases(self):
        # Common iteration logic
    
    @abstractmethod
    def get_subdirectories(self):
        # Subclass-specific
    
    @abstractmethod
    def generate_images(self):
        # Subclass-specific
```

### 3. Unified Planning via GenerationPlan

**Decision**: Centralize task computation in a single planning class.

**Rationale**:
- Previously, each generator had its own position/task computation logic
- Led to code duplication and inconsistent behavior
- `GenerationPlan` provides a single source of truth
- Makes it easier to add summary generation and reproducibility

**Implementation**:
```python
plan = GenerationPlan(
    task_type="ans",
    min_point_num=1,
    max_point_num=10,
    num_repeats=100,
    ratios="easy"
).build()

for task in plan.tasks:
    # task.params contains all parameters
    create_and_save(**task.params)
```

### 4. DotsCore as Reusable Engine

**Decision**: Separate dot placement logic into a dedicated class.

**Rationale**:
- Three generators need dot placement (ANS, one-colour, MTS)
- Each has slightly different needs (one vs two colours, equalization)
- DotsCore provides a flexible, composable engine
- Easier to test and maintain

**API Design**:
```python
dots = DotsCore(init_size, colour_1, colour_2, bg_colour, ...)
points = dots.design_n_points(5, "colour_1")
points = dots.design_n_points(3, "colour_2", point_array=points)
points = dots.equalize_areas(points)  # Optional
img = dots.draw_points(points)
```

### 5. ImageCanvas Wrapper

**Decision**: Wrap PIL Image/ImageDraw in a dedicated class.

**Rationale**:
- Centralizes all PIL interactions
- Provides a cleaner interface for generators
- Makes it easier to switch image libraries if needed
- Simplifies testing (can mock ImageCanvas)

**Usage**:
```python
canvas = ImageCanvas(size=512, bg_colour="white", mode="RGB")
canvas.draw_ellipse([(x1, y1), (x2, y2)], fill="yellow")
canvas.draw_polygon(vertices, fill="blue")
img = canvas.img  # Get underlying PIL Image
```

### 6. Retry Logic for Dot Placement

**Decision**: Implement retry at generator level, not in DotsCore.

**Rationale**:
- DotsCore raises `PointLayoutError` when placement fails
- Generator catches and retries (up to `attempts_limit`)
- Keeps DotsCore focused on placement logic
- Generator controls retry strategy

**Pattern**:
```python
for attempt in range(attempts_limit):
    try:
        img = create_image()
        break
    except PointLayoutError:
        if attempt == attempts_limit - 1:
            raise TerminalPointLayoutError()
```

### 7. Phase-Based Directory Structure

**Decision**: Organize output as `{output_dir}/{phase}/{class}/`.

**Rationale**:
- Standard machine learning convention
- Easy to split into train/test datasets
- Simplifies dataset loading in ML frameworks
- Clear separation of concerns

**Implementation**:
```python
def get_subdirectories(self):
    subdirs = []
    for phase in ["train", "test"]:
        for class_name in self.classes:
            subdirs.append((phase, class_name))
    return subdirs
```

### 8. Seed Management

**Decision**: Centralize seed handling in `random_seed.py`.

**Rationale**:
- Python's random and numpy's random need separate seeding
- Ensures reproducibility across all generators
- Single point of control for randomization
- Handles None seed gracefully

**Implementation**:
```python
def set_seed(seed):
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
```

---

## Module Dependencies

### Core Dependencies

```
cogstim/
├── generators/
│   ├── All depend on:
│   │   ├── helpers.base_generator
│   │   ├── helpers.constants
│   │   └── helpers.planner (for task generation)
│   │
│   ├── shapes.py
│   │   └── helpers.image_utils (ImageCanvas)
│   │
│   ├── dots_ans.py
│   │   └── helpers.dots_core (DotsCore)
│   │
│   ├── dots_one_colour.py
│   │   └── helpers.dots_core (DotsCore)
│   │
│   ├── match_to_sample.py
│   │   ├── helpers.dots_core (DotsCore)
│   │   └── helpers.mts_geometry (equalize_pair)
│   │
│   ├── lines.py
│   │   └── helpers.image_utils (ImageCanvas)
│   │
│   └── fixation.py
│       └── helpers.image_utils (ImageCanvas)
│
└── helpers/
    ├── base_generator.py
    │   └── helpers.random_seed (set_seed)
    │
    ├── dots_core.py
    │   └── helpers.image_utils (ImageCanvas)
    │
    ├── planner.py
    │   └── (no internal dependencies)
    │
    ├── mts_geometry.py
    │   └── helpers.dots_core (DotsCore, PointLayoutError)
    │
    ├── image_utils.py
    │   └── PIL (external)
    │
    ├── constants.py
    │   └── (no dependencies)
    │
    └── random_seed.py
        └── random, numpy (external)
```

### External Dependencies

- **Pillow (PIL)**: All generators for image creation
- **numpy**: Dot generators for numerical operations, geometric calculations
- **tqdm**: All generators for progress bars
- **argparse**: CLI only
- **random**: All generators for randomization

---

## Extension Points

### Adding a New Generator

1. **Create Generator Class**:
```python
from cogstim.helpers.base_generator import BaseGenerator

class MyGenerator(BaseGenerator):
    def __init__(self, config):
        super().__init__(config)
        # Your initialization
    
    def get_subdirectories(self):
        # Define your directory structure
        return [("train", "class1"), ("test", "class1")]
    
    def generate_images(self):
        self.setup_directories()
        
        for phase, num_images in self.iter_phases():
            for i in range(num_images):
                img = self.create_my_image()
                self.save_image(img, f"img_{i}", phase, "class1")
```

2. **Add to Package Exports** (`cogstim/__init__.py`):
```python
from cogstim.generators.my_generator import MyGenerator

__all__ = [
    # ... existing exports
    "MyGenerator",
]
```

3. **Add CLI Subcommand** (`cogstim/cli.py`):
```python
def setup_my_subcommand(subparsers):
    parser = subparsers.add_parser("my-task", help="...")
    add_common_options(parser)
    # Add task-specific options
    parser.set_defaults(func=run_my_task)

def run_my_task(args):
    config = build_my_config(args)
    gen = MyGenerator(config)
    gen.generate_images()

# In create_parser():
setup_my_subcommand(subparsers)
```

### Adding a New Shape

Edit `generators/shapes.py`:

1. **Add Surface-to-Radius Formula**:
```python
@staticmethod
def get_radius_from_surface(shape: str, surface: float) -> float:
    # ... existing shapes
    elif shape == "pentagon":
        # Calculate radius for pentagon with given surface
        return math.sqrt(surface / formula_here)
```

2. **Add Vertex Calculation**:
```python
def get_vertices(self, shape: str, center: tuple, radius: int, rotation_angle: int = 0) -> list:
    # ... existing shapes
    elif shape == "pentagon":
        vertices = self.create_pentagon_vertices(center, radius)
```

3. **Update CLI Choices** (`cogstim/cli.py`):
```python
parser.add_argument(
    "--shapes",
    choices=["circle", "star", "triangle", "square", "pentagon"],
    # ...
)
```

### Adding a New Configuration Parameter

1. **Add to Constants** (`helpers/constants.py`):
```python
MY_DEFAULTS = {
    "new_param": 42,
}
```

2. **Update Generator** to use the parameter:
```python
self.new_param = config.get("new_param", MY_DEFAULTS["new_param"])
```

3. **Add CLI Option** (`cogstim/cli.py`):
```python
parser.add_argument(
    "--new-param",
    type=int,
    default=MY_DEFAULTS["new_param"],
    help="Description of new parameter"
)
```

4. **Update Config Builder**:
```python
def build_my_config(args):
    return {
        # ... existing config
        "new_param": args.new_param,
    }
```

### Extending DotsCore

To add new dot manipulation methods:

1. **Add Method to DotsCore** (`helpers/dots_core.py`):
```python
def my_new_method(self, point_array, param):
    # Your logic here
    # Should return modified point_array
    # Should validate boundaries and overlaps
    return modified_array
```

2. **Use in Generator**:
```python
points = dots.design_n_points(5, "colour_1")
points = dots.my_new_method(points, param)
img = dots.draw_points(points)
```

### Adding a New Task Type to GenerationPlan

1. **Add Expansion Method** (`helpers/planner.py`):
```python
def expand_my_task(self, param1, param2, rep):
    self.tasks.append(GenerationTask("my_task", rep,
                                    param1=param1, param2=param2))
```

2. **Update build() Method**:
```python
def build(self, task_subtype=None):
    # ... existing task types
    elif self.task_type == "my_task":
        for rep in range(self.num_repeats):
            # Iterate over your parameter space
            self.expand_my_task(param1, param2, rep)
```

---

## Testing Strategy

### Unit Tests

- **BaseGenerator**: Test directory creation, save logic, config handling
- **DotsCore**: Test placement, equalization, area computation
- **ImageCanvas**: Test drawing operations, image creation
- **GenerationPlan**: Test task generation, position computation
- **Each Generator**: Test image creation with known seeds

### Integration Tests

- **CLI**: Test each subcommand end-to-end
- **Reproducibility**: Test that same seed produces identical images
- **File Output**: Verify directory structure and file naming

### Test Organization

```
tests/
├── test_base_generator.py
├── test_dots_core_new_methods.py
├── test_dots.py
├── test_shapes_creator.py
├── test_match_to_sample.py
├── test_lines_generator.py
├── test_fixation.py
├── test_cli_integration.py
└── test_integration_end_to_end.py
```

---

## Performance Considerations

### Bottlenecks

1. **Dot Placement**: `design_n_points()` can be slow with many dots or small image
   - Uses retry loop up to `attempts_limit`
   - Solution: Increase image size or reduce dot count/size

2. **Area Equalization**: Incremental increase can take many iterations
   - Match-to-sample equalization is most affected
   - Solution: Use `scale_total_area()` when possible (implemented in `mts_geometry.py`)

3. **Disk I/O**: Saving thousands of images
   - Solution: Use faster format (JPEG vs PNG), parallelize if needed

### Optimization Strategies

1. **Retry Limits**: Set reasonable `attempts_limit` (default 10000)
2. **Batch Generation**: Generate multiple images before saving
3. **Format Choice**: JPEG is faster than PNG, but lossy
4. **Progress Bars**: Use tqdm for user feedback during long operations

---

## Concurrency Considerations

**Current State**: Single-threaded generation.

**Parallelization Opportunities**:
1. **Phase-Level**: Generate train and test in parallel
2. **Class-Level**: Generate different classes in parallel
3. **Batch-Level**: Generate multiple images concurrently

**Challenges**:
- Random seed management (would need per-thread seeding)
- PIL thread safety (generally safe, but verify)
- File I/O contention (use separate directories)

**Future Direction**: Could add `--parallel` flag with `multiprocessing.Pool`.

---

## Summary

CogStim's architecture prioritizes:
1. **Extensibility**: Easy to add new generators and shapes
2. **Maintainability**: Clear separation of concerns, minimal duplication
3. **Reproducibility**: Seed-controlled randomization throughout
4. **Consistency**: Unified interfaces and patterns across all generators
5. **Testability**: Clear module boundaries and dependency injection

The template method pattern combined with composition (DotsCore, ImageCanvas, GenerationPlan) provides a flexible foundation for cognitive stimulus generation while keeping the codebase clean and maintainable.



---

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


