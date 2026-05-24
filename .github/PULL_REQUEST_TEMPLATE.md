## Description

<!-- Briefly describe what this PR does and why. Link any related issues with "Closes #..." -->

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactor / code quality

## Checklist

- [ ] I have bumped the version in `pyproject.toml` and `lightweight_charts/__version__`
- [ ] I have added an entry in `CHANGELOG.md` under the new version (Added / Changed / Fixed / Removed)
- [ ] My code passes `ruff check` and `ruff format --check` with no errors
- [ ] I have added or updated tests where appropriate
- [ ] All existing tests pass (`uv run python -m pytest test/ -v`)
- [ ] Pre-commit hooks pass (`pre-commit run --all-files`)
- [ ] If TypeScript sources were changed, the bundle has been rebuilt (`npm run build`)
- [ ] I have reviewed my own diff before requesting review
