# Architecture

Developer documentation. If you want to *use* CogStim, the
[user guide](../guide.md) and [options reference](../options.md) are what you
want instead.

## The shape of the package

```
cogstim/
  cli.py                    Subcommands, config builders, execution
  generators/               One module per stimulus paradigm
    shapes.py               Geometric shapes; also serves colours and custom
    dots_ans.py             Two-colour dot arrays; also serves one-colour
    match_to_sample.py      Sample/match dot array pairs
    lines.py                Rotated stripe patterns
    fixation.py             Fixation targets
    mask.py                 Dense overlapping dot masks
  helpers/
    base_generator.py       BaseGenerator: the contract every generator meets
    planner.py              GenerationPlan: what to generate, before generating
    cli_options.py          The single declaration of every CLI option
    dots_core.py            Dot placement, overlap and area equalization
    image_utils.py          ImageCanvas: all drawing, and colour resolution
    geometry.py             The record of what was drawn
    annotations.py          Exporting that record as CSV/JSON or SVG
    run_config.py           Recording and replaying a run
    constants.py            Defaults and colour definitions
```

Roughly 1900 statements, 88% covered by 315 tests.

## The four ideas worth knowing

### 1. Planning is separate from generating

A generator does not decide what to draw while drawing it. It first builds a
`GenerationPlan` — a flat list of `GenerationTask`, each carrying the parameters
for one image — and then walks it.

This is what makes `--dry-run` trustworthy. `BaseGenerator.plan_summary()` and
`generate_images()` both go through the same `build_plan()`, so a dry run and a
real run cannot disagree about what would be produced. A test asserts the
predicted total equals the files a real run writes.

It is also where the set-to-image multiplier lives. `--train-num` counts *sets*;
one set is one sweep of every condition, which the plan expands. See
[Sets and images](../guide.md#sets-and-images).

```python
def build_plan(self, phase, num_sets):
    return GenerationPlan(
        task_type="lines",
        num_repeats=num_sets,
        angles=self.angles,
        min_stripes=self.min_stripe_num,
        max_stripes=self.max_stripe_num,
    ).build()
```

### 2. Everything is drawn through ImageCanvas

No generator touches PIL directly. They call `draw_ellipse`, `draw_rectangle`,
`draw_polygon` and `draw_line` on an `ImageCanvas`, which draws the pixels *and*
records the primitive in a `Scene`.

That recording is why `--metadata` and `--img-format svg` work for every
paradigm without any generator knowing about either: annotations and vector
output are both rendered from the `Scene`, so neither can disagree with the
raster.

Pass a `label` describing what the element is in the stimulus — `dot`, `stripe`,
`fixation_disk` — because that label is what ends up in the exported
annotations.

```python
canvas.draw_ellipse((x0, y0, x1, y1), fill=colour, label="dot")
```

If a generator transforms the rasterised image after drawing, it must apply the
same transform to the `Scene`. `lines.py` is the only place this happens: it
draws upright on an oversized canvas, then rotates and crops, and calls
`scene.transformed(...)` so the recorded coordinates describe the final image.

### 3. Every option is declared once

`helpers/cli_options.py` holds the registry. Subcommands state which groups of
options they consume; none defines an option itself.

```python
_add_subcommand(
    subparsers, "lines",
    opts.COMMON, opts.TRAIN_TEST, opts.LINES_SPECIFIC,
    ...
)
```

This exists because the CLI had drifted: the same concept was spelled several
ways in different tasks, and the same flag meant different things depending on
where you met it. `tests/test_cli_options.py` encodes the naming rules so that
cannot return.

Renaming an option means adding the old spelling to `aliases`, which keeps it
working and warns. See [DEPRECATIONS.md](../../DEPRECATIONS.md).

### 4. Generators inherit their plumbing

`BaseGenerator` handles what every paradigm needs, so a generator is only the
geometry of its own stimulus:

| It gives you | What for |
|---|---|
| `save_image()` | Path building, format handling, SVG, annotation recording, counting |
| `images_written` | The measured file count, so summaries report reality |
| `seed` | The seed used, drawn if none was given, recorded for reproducibility |
| `plan_summary()` | `--dry-run`, via your `build_plan()` |
| `setup_directories()` | Output tree from `get_subdirectories()` |
| `write_annotations()` | Exporting the accumulated geometry |

A generator implements `build_plan()`, `generate_images()`,
`get_subdirectories()`, and whatever drawing it needs.

## Data flow of one run

```
cogstim lines --train-num 10 --angles 0 45
        |
        v
create_parser()            options from the cli_options registry
        |
        v
build_lines_config(args)   argparse namespace -> generator config dict
        |
        v
LinesGenerator(config)     seeds, resolves colours, creates directories
        |
        v
execute()                  --dry-run stops here, reporting plan_summary()
        |
        v
generate_images()
   build_plan(phase, sets)  ->  GenerationPlan
   for each task:
       create_rotated_stripes()   draws on an ImageCanvas, recording a Scene
       save_image()               writes the file, records the geometry
        |
        v
write_annotations()        annotations.csv / .json, if --metadata was given
write_run_config()         cogstim_config.yaml, always
report_generation()        counts what was actually written
```

## Testing conventions

- **Assert against the artefact, not the code.** `tests/test_annotations.py`
  reads pixels back out of the rendered PNG to check the exported bounding
  boxes; testing the exporter against the recorder would prove nothing.
- **Regression tests name their bug.** Several tests carry the JOSS review
  issue number and the command that exposed the problem, so the reason a check
  exists survives longer than anyone's memory of it.
- **Rules are tests.** The API naming conventions, the freshness of the
  generated docs and the promise that no default produces a blank image are all
  enforced by tests rather than by review.

## Things to be careful with

- `helpers/dots_core.py` is the trickiest code in the package: placing
  non-overlapping dots, and growing radii to equalize areas without leaving the
  canvas. Any method that changes a radius must re-check both boundaries and
  overlap. One that did not was the cause of a reported bug.
- `ShapesGenerator` takes its configuration as explicit keyword arguments rather
  than a dict, unlike every other generator. Adding a config key means adding a
  parameter there too.
- `GENERAL_CONFIG` in `dots_ans.py` and `match_to_sample.py` is a module-level
  default merged by the CLI's config builders. It is internal and will move.
