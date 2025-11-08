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

