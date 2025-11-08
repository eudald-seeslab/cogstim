# FAQ & Troubleshooting

Common questions and solutions for CogStim users.

## General Usage

### Q: Which flags matter for my task?

**A:** Each task has a dedicated section in the [User Guide](guide.md) with only the relevant options. At the end of each section, you'll find a concise table listing flags specific to that task.

**Quick navigation:**
- [Shapes options](guide.md#shapes-options-reference)
- [Colours options](guide.md#colours-options-reference)
- [ANS options](guide.md#ans-options-reference)
- [One-Colour options](guide.md#one-colour-options-reference)
- [Match-to-Sample options](guide.md#match-to-sample-options-reference)
- [Lines options](guide.md#lines-options-reference)
- [Fixation options](guide.md#fixation-options-reference)
- [Custom options](guide.md#custom-options-reference)

---

### Q: How do I make my runs reproducible?

**A:** Use the `--seed` option with an integer value:

```bash
cogstim shapes --train-num 10 --test-num 5 --seed 1234
```

Running this command multiple times will always produce the same images. Without a seed, each run generates different random variations.

**See also:** [Quick Start – Reproducibility](index.md#reproducibility)

---

### Q: What does "image sets" mean? How many actual images will I get?

**A:** An "image set" is a group of images that combines all possible parameter combinations for that task. The number of actual images per set varies:

- **shapes/colours:** ~200 images per set (variations in position, size, rotation)
- **ans:** ~75 images per set (depends on ratios and point ranges)
- **one-colour:** varies by quantity range (e.g., 1–10 produces 10+ images per set)
- **match-to-sample:** produces pairs (sample + match) per set
- **lines:** varies by number of angles and stripe counts

When you specify `--train-num 10`, you're requesting 10 *sets*, which may yield hundreds or thousands of individual images.

**See also:** [Quick Start – Understanding Image Sets](index.md#understanding-image-sets)

---

## Image Generation Issues

### Q: My images are clipped after I changed `--img-size`. What's wrong?

**A:** Reducing `--img-size` can cause shapes or dots to be clipped at the edges if surface areas or radii are too large for the canvas.

**Solution 1 – Reduce shape/dot sizes:**

For shapes:
```bash
cogstim shapes --img-size 256 --min-surface 2500 --max-surface 5000
```

For dots:
```bash
cogstim ans --img-size 256 --min-point-radius 10 --max-point-radius 15
```


**Solution 2 – Increase image size:**

```bash
cogstim shapes --img-size 1024
```

**Rule of thumb:** Leave margins of at least 20–30% of the image size for shapes/dots to avoid edge clipping.

**Note**: we are working towards creating a specific error for this case so that no "impossible" images are created.

---

### Q: Dot placement keeps failing. How do I fix it?

**A:** Dot placement can fail when:
1. Too many dots are requested for the canvas size
2. Dot radii are too large
3. The `attempts-limit` is too low

**Solution 1 – Increase `--attempts-limit`:**

```bash
cogstim ans --attempts-limit 20000 --train-num 10 --test-num 5
```

The default is 10,000 for ANS/one-colour and 5,000 for match-to-sample.

**Solution 2 – Reduce dot counts or radii:**

```bash
cogstim ans \
  --max-point-num 8 \
  --max-point-radius 25 \
  --train-num 10 --test-num 5
```

**Solution 3 – Increase image size:**

```bash
cogstim ans --img-size 1024 --train-num 10 --test-num 5
```

**See also:** [User Guide – ANS](guide.md#ans--approximate-number-system) for dot-related options.

---

### Q: Why do some ANS/match-to-sample images say "equalized" and others don't?

**A:** For ANS and match-to-sample tasks, CogStim generates two types of images:

1. **Equalized** (`*_equalized`): Total surface area is controlled between the two colours/quantities. This removes cumulative surface as a confounding cue.
2. **Non-equalized** (no suffix): Dot sizes are random, so surface area varies naturally.

This split allows you to test whether participants rely on surface area cues. Typically, half the images are equalized and half are not.

**See also:** [User Guide – ANS](guide.md#note-on-equalization) for details on the equalization strategy.

---

## Task-Specific Questions

### Q: How do I generate only vertical and horizontal lines (no diagonals)?

**A:** Use the `--angles` flag with specific values:

```bash
cogstim lines --angles 0 90 --train-num 10 --test-num 5
```

**See also:** [Recipes – Lines at Specific Angles](recipes.md#recipe-5-lines-at-specific-angles-04590135)

---

### Q: Can I generate more than two shapes or colours?

**A:** Yes! Use the `custom` task:

```bash
cogstim custom \
  --shapes circle star triangle \
  --colours red green blue \
  --train-num 10 --test-num 5
```

This produces 9 classes (3 shapes × 3 colours).

**See also:** [User Guide – Custom](guide.md#custom--custom-shapecolour-combinations)

---

### Q: What's the difference between `shapes` and `colours` tasks?

**A:** 
- **`shapes`:** Two different shapes in the same colour (e.g., yellow circles vs yellow stars)
- **`colours`:** One shape in two different colours (e.g., yellow circles vs blue circles)

Both are convenience shortcuts. For more complex combinations, use the `custom` task.

**See also:** [User Guide – Shapes](guide.md#shapes--shape-discrimination) and [User Guide – Colours](guide.md#colours--colour-discrimination)

---

### Q: How do I disable positional jitter for shapes/colours?

**A:** Use the `--no-jitter` flag:

```bash
cogstim colours --train-num 10 --test-num 5 --no-jitter
```

This places shapes in fixed positions, which is useful when position should not be a cue.

**See also:** [User Guide – Colours – Advanced Tweak](guide.md#advanced-tweak-fixed-position-stimuli)

---

### Q: Which fixation target type should I use?

**A:** Thaler et al. (2013) recommend the **ABC** type for best fixational stability. This combines a disk, cross, and central dot with cut-outs.

```bash
cogstim fixation --types ABC --background-colour black --symbol-colour white
```

**See also:** [Recipes – Fixation ABC](recipes.md#recipe-7-fixation-abc-with-recommended-parameters) and [User Guide – Fixation](guide.md#fixation--fixation-targets)

---

## Advanced Customisation

### Q: Can I control the exact size of shapes or dots?

**A:** Yes, using surface area ranges for shapes and radius ranges for dots:

**For shapes:**
```bash
cogstim shapes --min-surface 15000 --max-surface 25000
```

**For dots:**
```bash
cogstim ans --min-point-radius 15 --max-point-radius 25
```

These control the size variation within your stimuli.

---

### Q: How do I tighten the surface area equalization in match-to-sample?

**A:** Adjust the `--tolerance` parameter:

```bash
cogstim match-to-sample --tolerance 0.005 --train-num 10
```

Default is `0.01` (1% relative tolerance). Lowering it makes the equalization stricter.

**See also:** [User Guide – Match-to-Sample – Advanced Tweak](guide.md#advanced-tweak-tighter-equalization-tolerance)

---

### Q: Can I change the output directory?

**A:** Yes, use `--output-dir`:

```bash
cogstim shapes --train-num 10 --test-num 5 --output-dir my_shapes
```

This saves images to `my_shapes/train/` and `my_shapes/test/` instead of the default `images/shapes/`.

---

## Debugging & Development

### Q: How can I enable verbose output to debug generation?

**A:** Use the `--verbose` flag:

```bash
cogstim shapes --train-num 10 --verbose
```

This shows detailed progress and diagnostic information during generation.

---

### Q: I want to verify examples from the docs still work. Is there a test?

**A:** Yes! Run the documentation smoke test:

```bash
python scripts/docs_smoke.py
```

This runs minimal examples for each subcommand and verifies that outputs are generated correctly.

---

## Still Need Help?

If your question isn't answered here:

1. Check the [User Guide](guide.md) for detailed task documentation
2. Try the [Recipes](recipes.md) for copy-paste solutions to common goals
3. Run `cogstim <task> --help` for task-specific options
4. Open an issue on [GitHub](https://github.com/eudald-seeslab/cogstim/issues)
5. Write me at eudald at correig dot net.

