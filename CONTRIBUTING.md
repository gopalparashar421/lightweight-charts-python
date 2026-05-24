# Contributing to python-lightweight-charts

Thank you for your interest in contributing!

## Development Setup

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (fast Python package manager)
- [Node.js](https://nodejs.org/) (only if you are modifying TypeScript sources)

### Install dependencies

```bash
# Clone the repo
git clone https://github.com/gopalparashar421/lightweight-charts-python.git
cd lightweight-charts-python

# Install Python dependencies (including dev tools: pytest, ruff)
uv sync --group dev
```

### Pre-commit hooks (one-time setup)

Hooks run automatically on every `git commit` and catch style issues before they reach CI.

```bash
pip install pre-commit
pre-commit install
```

To run hooks manually against all files:

```bash
pre-commit run --all-files
```

## Running Tests

```bash
uv run python -m pytest test/ -v
```

Tests that require a live display (pywebview window) are skipped automatically in CI.
To run them locally, ensure you have a display available:

```bash
uv run python -m pytest test/ -v -k "not skip"
```

## Code Style

All Python code is formatted and linted with [Ruff](https://docs.astral.sh/ruff/).

```bash
uv run ruff check lightweight_charts/ test/   # lint
uv run ruff format lightweight_charts/ test/  # format
```

## Building the TypeScript bundle

The compiled JS bundle (`lightweight_charts/js/bundle.js`) is committed to the repo.
Only rebuild it if you modify TypeScript sources under `src/`:

```bash
npm install
npm run build
```

## Building the docs locally

Docs are built with [Sphinx](https://www.sphinx-doc.org/) and hosted on Read the Docs.
To build and preview them locally:

```bash
# Install docs dependencies (defined in the [docs] group in pyproject.toml)
uv sync --group docs

# Build HTML output
uv run sphinx-build -W --keep-going -b html docs/source docs/_build/html

# Open in your browser (macOS / Linux)
open docs/_build/html/index.html
# Windows
start docs/_build/html/index.html
```

The `-W` flag turns Sphinx warnings into errors — the same flag used in CI — so
you'll catch broken cross-references and missing toctree entries before pushing.

If you add, rename, or remove a public class or method, also update the matching
page under `docs/source/reference/` and verify the build passes before opening a PR.

## Pull Requests

All pull requests must receive **approval from a maintainer or repo collaborator** before merging.
No PR may be merged without at least one approving review from [@gopalparashar421](https://github.com/gopalparashar421) or another listed collaborator.

### Contributor responsibilities

Before opening a PR, you are responsible for:

1. **Version bump** — increment the version in both `pyproject.toml` (`version = "..."`) and `lightweight_charts/__version__` to the appropriate next semver value.
2. **Changelog** — add an entry under the new version heading in `CHANGELOG.md` using the **Added / Changed / Fixed / Removed** format. Do not leave the changelog blank.

A PR checklist is embedded in the pull request template (`.github/PULL_REQUEST_TEMPLATE.md`).

## Releases

Releases are published to PyPI automatically by pushing a version tag:

```bash
git tag v1.0.1
git push origin v1.0.1
```

The tag version must match `pyproject.toml` and `lightweight_charts/__version__`.
