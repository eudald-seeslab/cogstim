# Roadmap

What CogStim covers today, why, and what is planned. Suggestions and
contributions towards any of this are welcome — open an issue to discuss an item
before starting on it.

## What is covered, and why

CogStim covers **numerosity and basic visual discrimination**: the paradigms
where the experimental difficulty lies in controlling confounds across many
stimuli rather than in rendering any single one.

| Task | Paradigm |
|---|---|
| `ans` | Approximate Number System, two-colour dot arrays |
| `one-colour` | Numerosity without colour cues |
| `match-to-sample` | Enumeration and matching, with area equalization |
| `shapes` / `colours` / `custom` | Shape and colour discrimination |
| `lines` | Orientation discrimination |
| `fixation` | Fixation targets |
| `mask` | Backward and forward masking |

These share a problem that offline generation is unusually good at. A numerosity
experiment needs the total dot area matched across conditions, dots that never
overlap, and every combination of counts and ratios present in balanced numbers.
That is a constraint-satisfaction problem over a whole stimulus set, not a
drawing problem, and it is awkward to express inside a runtime presentation
loop. Generating the set ahead of time makes the constraints checkable, the
stimuli inspectable before an experiment runs, and the same assets reusable
across presentation software.

Paradigms whose difficulty is in *presentation* rather than *construction* —
precise timing, gaze-contingent updates, adaptive staircases — are better served
by PsychoPy, Psychtoolbox or jsPsych, and CogStim does not attempt them.

## Planned

Ordered roughly by how often they have been asked for. No dates: this is
maintained alongside other work.

### More shapes

`shapes` currently supports circle, star, triangle and square. Requested
additions:

- Rectangles with controllable side length and aspect ratio
- Trapezoids within a bounding-box ratio and a range of parallel-side ratios
- Regular polygons: pentagon, hexagon, and *n*-gons generally
- Spirals

The shape system takes a target surface area and returns vertices, so most of
these are a `get_radius_from_surface` case and a vertex function. This is the
most approachable item on the list for a first contribution.

### Gratings and textures

- Sinusoidal and square-wave gratings, by spatial frequency and orientation
- Plaids, as superimposed gratings
- Random-dot and noise textures

These extend the orientation work `lines` already does and are a natural fit for
the existing plan-and-draw structure.

### Visual search arrays

Target-present and target-absent displays with controlled set sizes and
distractor similarity. This needs placement logic beyond what `dots_core`
does — distractors positioned by similarity rather than only by non-overlap —
so it is a larger piece than the shape work.

### Motion stimuli

Random-dot kinematograms with controllable coherence. This is the one item that
does not fit the current architecture: it needs frame sequences rather than
single images, so it would mean extending the output model to image series or
video, not just adding a generator.

## Under consideration

- **Hex and named colour formats.** Only seven named colours are accepted today.
  Hex would be cheap; matplotlib or HTML colour names would need a dependency or
  a table.
- **Perceptual colour control**, so that colour-discrimination stimuli can be
  specified in a perceptually uniform space rather than by name.
- **Degrees of visual angle** as an alternative to pixels, given a viewing
  distance and display size. This would touch every size option, so it needs a
  clear design before it starts.
- **Export presets** for common downstream tools — COCO-format annotations for
  object detection, and ready-made import structures for Qualtrics or jsPsych.

## Deliberately not planned

- **Running experiments.** Presentation, timing and response collection are what
  PsychoPy, Psychtoolbox and jsPsych do well. CogStim produces assets those
  tools present.
- **A graphical interface.** The command line plus a
  [configuration file](docs/guide.md) covers the scripted, reproducible use this
  is built for. A GUI would be a substantial separate project.
- **Runtime stimulus generation.** Deciding stimuli during an experiment
  reintroduces the coupling that offline generation exists to avoid.

## Changing this roadmap

It reflects what has been asked for, which is a small sample. If you need
something that is not here, or need something here sooner, say so in an issue —
that is the main signal used to decide what to work on next.
