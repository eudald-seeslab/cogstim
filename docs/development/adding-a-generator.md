# Adding a stimulus type

A worked example of adding a new paradigm, using a hypothetical `gratings` task.
Read [architecture.md](architecture.md) first for the concepts.

There are five steps. None of them is large, because `BaseGenerator` already
handles file naming, formats, counting, seeding, annotations and `--dry-run`.

## 1. Declare the options

In `cogstim/helpers/cli_options.py`, add a group. Do not define options inside
the subcommand — `tests/test_cli_options.py` will fail if you do.

```python
GRATINGS_SPECIFIC = [
    Option("--grating-colour-1", dest="grating_colour", type=str,
           choices=COLOUR_CHOICES,
           help="Bar colour (default: black, or its inverse when that "
                "matches the background)"),
    Option("--min-spatial-frequency-cpd", type=float, default=0.5,
           help="Minimum spatial frequency in cycles per degree"),
    Option("--max-spatial-frequency-cpd", type=float, default=8.0,
           help="Maximum spatial frequency in cycles per degree"),
]
```

The naming rules are checked automatically:

- Colours are `--<element>-colour[-N]`.
- A measurement carries its unit: `-px`, `-deg`, `-cpd`.
- A `--min-X` needs a `--max-X`, unless it is a constraint rather than a range
  endpoint (add it to `UNPAIRED_MINIMUMS` with a reason if so).
- A flag shared with another task must mean the same thing there.
- Leave a stimulus colour's default as `None` so the generator can pick one that
  contrasts with the background.

## 2. Write the generator

```python
from cogstim.helpers.base_generator import BaseGenerator
from cogstim.helpers.image_utils import ImageCanvas, resolve_stimulus_colour
from cogstim.helpers.planner import GenerationPlan


class GratingsGenerator(BaseGenerator):
    """Sinusoidal or square-wave gratings at a range of spatial frequencies."""

    def __init__(self, config):
        super().__init__(config)
        self.background_colour = config["background_colour"]
        self.colour = resolve_stimulus_colour(
            config.get("grating_colour"), self.background_colour, "black"
        )
        self.setup_directories()

    def get_subdirectories(self):
        """One class directory per orientation, under train/ and test/."""
        return [(phase, str(angle))
                for phase in ("train", "test")
                for angle in self.angles]

    def build_plan(self, phase, num_sets):
        """One task per (orientation, spatial frequency), once per set."""
        return GenerationPlan(
            task_type="gratings",
            num_repeats=num_sets,
            ...
        ).build()

    def generate_images(self):
        self.setup_directories()
        for phase, num_sets in self.iter_phases():
            plan = self.build_plan(phase, num_sets)
            self.log_generation_info(
                f"Generating {len(plan)} images for {phase}..."
            )
            for task in plan.tasks:
                canvas = self.draw_grating(**task.params)
                self.save_image(canvas, self.filename_for(task), phase, ...)
            self.write_summary_if_enabled(plan, phase)
```

Two things that matter more than they look:

**Return the canvas from your drawing method, not `canvas.img`.** The canvas
carries the recorded geometry; the bare image does not. Passing the image to
`save_image()` silently loses annotations and makes SVG output impossible for
your task.

**Label what you draw.** The label is what appears in the exported annotations.

```python
canvas.draw_rectangle(bar_bounds, fill=self.colour, label="grating_bar")
```

`GenerationPlan` needs to know how to expand your task type: add an
`expand_gratings_tasks()` alongside the existing ones and a branch in `build()`.

## 3. Wire up the subcommand

In `cogstim/cli.py`, a config builder and a runner:

```python
def build_gratings_config(args):
    return {
        "output_dir": args.output_dir,
        "train_num": args.train_num,
        "test_num": args.test_num,
        "grating_colour": args.grating_colour,
        "background_colour": args.background_colour,
        "seed": args.seed,
        "img_format": args.img_format,
        "metadata": args.metadata,
        "version_tag": args.version_tag,
    }


def run_gratings(args):
    config = build_gratings_config(args)
    execute(args, config, GratingsGenerator(config))
```

And register it in `create_parser()`:

```python
def setup_gratings_subcommand(subparsers):
    _add_subcommand(
        subparsers, "gratings",
        opts.COMMON, opts.TRAIN_TEST, opts.GRATINGS_SPECIFIC,
        help="Generate sinusoidal grating stimuli",
        description="...",
        epilog="Example: cogstim gratings --train-num 20",
        func=run_gratings,
    )
```

`execute()` gives you `--dry-run`, the accurate summary, annotation export and
the recorded run configuration for free.

## 4. Test it

The shared consistency tests pick up your task automatically once it is
registered — including the check that its defaults do not produce a blank image
on either a white or a black background. Add tests for the geometry itself:

```python
def test_bar_count_matches_spatial_frequency(tmp_path):
    ...

def test_annotations_match_the_pixels(tmp_path):
    """Read the rendered image back rather than trusting the recorder."""
    ...
```

Then run the full suite and the documentation checks:

```bash
pytest
python scripts/generate_options_doc.py
python scripts/docs_smoke.py
```

## 5. Document it

- Add a section to `docs/guide.md`, with a minimal command and the **measured**
  number of images per set — get it from `--dry-run`, do not estimate.
- Add the images-per-set row to the table in
  [Sets and images](../guide.md#sets-and-images).
- Add a recipe to `docs/recipes.md` if there is an obvious research use.
- Regenerate `docs/options.md`; a test fails if you forget.
