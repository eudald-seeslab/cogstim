# Deprecations

Everything listed here still works and emits a `DeprecationWarning` when used.
Nothing is removed without warning first.

To see the warnings in your own scripts, run Python with `-W default`:

```bash
python -W default -m cogstim ans --dot-colour1 yellow
```

## Scheduled for removal

These are kept only so that existing scripts keep running while the current
release settles. They will be removed in a future release.

### Option names

The command-line options were renamed to one scheme: colours are
`--<element>-colour[-N]`, pixel measurements end in `-px`, and counts end in
`-num`. Every old spelling is still accepted.

The full mapping is in the [options reference](docs/options.md#renamed-options).

### Option values

| Deprecated | Use instead |
|---|---|
| `--layout mixed` | `--layout full` |

`ans` called a layout "mixed" that `mask` called "full" for the same thing.

### Python API

| Deprecated | Use instead |
|---|---|
| `DotsOneColourGenerator` | `DotsANSGenerator` with `ONE_COLOUR=True` |
| `cogstim.generators.lines.parse_args` / `main` | The `cogstim lines` command |
| `cogstim.generators.dots_one_colour.parse_args` / `main` | The `cogstim one-colour` command |

`DotsOneColourGenerator` is a parallel implementation of the `one-colour` task.
The CLI has used `DotsANSGenerator` for it for some time, so the older class no
longer receives the fixes made there and should not be relied on.

The per-module `parse_args`/`main` functions predate the unified `cogstim`
command. They still use the old option names and lack every option added since,
including `--dry-run`, `--metadata` and the run configuration.

## Not deprecated, but internal

`GENERAL_CONFIG` in `cogstim.generators.dots_ans` and
`cogstim.generators.match_to_sample` is a module-level default used by the CLI's
configuration builders. It is not part of the public API and may move without a
deprecation cycle.
