# Contributing to CogStim

Contributions are welcome, whether that is reporting a problem, asking a
question, or sending code. This page covers all three.

If you use CogStim for research, hearing about it is genuinely useful — it tells
us which paradigms matter and where the rough edges are. Open an issue or a
discussion and say what you built.

## Reporting a problem

Open an issue: <https://github.com/eudald-seeslab/cogstim/issues>

The issue templates ask for the command you ran, what you expected and what
happened. The single most useful thing you can include is the
`cogstim_config.yaml` written into your output directory: it records every
option and the resolved seed, so the run can be reproduced exactly.

```bash
cogstim run path/to/output/cogstim_config.yaml
```

If the images look wrong, attach one. If nothing was generated, include the full
terminal output.

## Asking for help

- **Usage questions**: open a
  [Discussion](https://github.com/eudald-seeslab/cogstim/discussions), or an
  issue with the *Question* template if discussions are unavailable.
- **Documentation**: start with the [user guide](docs/guide.md), the
  [options reference](docs/options.md) and the [FAQ](docs/faq.md).
- **Response time**: this is a small project maintained alongside other work.
  Expect a reply within about a week. If an issue has gone quiet for longer than
  that, a polite nudge is welcome rather than unwelcome.

## Setting up for development

```bash
git clone https://github.com/eudald-seeslab/cogstim.git
cd cogstim
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Running the tests

```bash
pytest                            # whole suite with coverage
pytest tests/test_cli_options.py  # one file
pytest -k annotation              # tests matching a name
pytest --no-cov                   # faster, skips the coverage report
```

The suite takes well under a minute. Coverage is reported to the terminal and
written to `htmlcov/`.

Two checks live outside `pytest` and are worth running before opening a pull
request:

```bash
python scripts/docs_smoke.py               # every documented example still runs
python scripts/generate_options_doc.py     # regenerate docs/options.md
```

The options reference is generated from the CLI, and a test fails if the
committed file no longer matches. If you add or rename an option, run the
generator and commit the result.

## Making a change

Read [docs/development/architecture.md](docs/development/architecture.md) first;
it explains where things live and how a generator is structured.
[Adding a generator](docs/development/adding-a-generator.md) walks through a new
stimulus type end to end.

A few conventions the codebase holds to, enforced by
`tests/test_cli_options.py`:

- **Options are declared once**, in `cogstim/helpers/cli_options.py`. No
  subcommand defines an option of its own.
- **One name for one concept.** A flag that appears in several tasks means the
  same thing in all of them.
- **Units belong in the name.** A pixel measurement ends in `-px`.
- **Defaults must produce a visible stimulus** on any background.

## Pull requests

A pull request will be merged when:

1. **The tests pass**, on every Python version in CI (3.10 through 3.13).
2. **New behaviour has a test.** For a bug fix, a test that fails before the fix
   and passes after it. Tests that check code against itself are not much use —
   where possible, assert against the rendered image, as
   `tests/test_annotations.py` does by reading pixels back out.
3. **Documentation is updated** where the change is user-visible, including
   regenerating `docs/options.md`.
4. **Nothing breaks without warning.** Renaming an option means keeping the old
   spelling as a deprecated alias; see [DEPRECATIONS.md](DEPRECATIONS.md).
5. **The change is described.** Say what problem it solves, not only what it
   does.

Small, focused pull requests are easier to review and get merged faster. If you
are planning something substantial, open an issue first so we can agree the
approach before you spend the time.

You do not need to be a Python expert to contribute. Documentation fixes,
clearer error messages and reports of confusing behaviour are all valuable, and
several of the improvements in this project came from exactly that.

## Branches

- `main` is the development branch; all code changes go here.
- `paper` carries the JOSS manuscript in `paper/` and is kept in step with
  `main` by merging `main` into it. Nothing lands on `paper` that is not
  either the manuscript or a merge from `main`.

Work on a branch off `main` and open a pull request against `main`.

## Releases

Versions follow [semantic versioning](https://semver.org). Deprecated options
are removed only in a major release, and never without having warned in a
previous one.
