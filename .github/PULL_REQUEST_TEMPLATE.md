## What this changes

<!-- The problem it solves, not only what it does. -->

## Why

<!-- Link the issue if there is one: Fixes #123 -->

## Checklist

Full detail in [CONTRIBUTING.md](../CONTRIBUTING.md).

- [ ] `pytest` passes
- [ ] New behaviour has a test. For a bug fix, one that fails before the change
      and passes after it
- [ ] `python scripts/generate_options_doc.py` re-run, if any option changed
- [ ] `python scripts/docs_smoke.py` passes, if any documented example changed
- [ ] Documentation updated, if the change is user-visible
- [ ] Any renamed option keeps its old spelling as a deprecated alias, and is
      listed in [DEPRECATIONS.md](../DEPRECATIONS.md)

## Anything reviewers should look at closely

<!-- Optional: a decision you were unsure about, an alternative you rejected. -->
