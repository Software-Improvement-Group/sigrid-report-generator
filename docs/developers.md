# Developer instructions

Pull requests welcome! If you have a small improvement, feel free to just create a pull request and assign a reviewer
from the core team. If you propose a larger change, it's best to discuss it with the core team before you get started to
ensure it aligns with our thoughts and goals. In either case, please make sure the change is maintainable and tested.
Below are some instructions to get you started.

For the architecture of this project, see [architecture.md](architecture.md).

## Install

- Go into the `report-generator` directory.
- Install your latest changes: `pip3 install -e .`  (Re-do this any time you want to run the tool using your latest
  changes)
  Note: This will override the `report-generator` tool installed using the "for end-users" method.

If you want to run the Report Generator locally without going through the motions of installing the Python package:
`./src/run.py`. The arguments are the same as for the normal entry point.

## Coding / IDE

- **IDE**: Feel free to use your favorite IDE. Visual Studio Code with the Python extension and Python Debugger
  extension from Microsoft is popular and free.
- **Maintainability**:  Make sure your code is maintainable. We have a Sigrid CI integration up and running.

## Testing

### Unit tests

- Install Python test dependencies (once, or at least infrequently): `pip3 install -e ."[test]"`
- Run Python unit tests: `pytest`
    - When writing new tests, make sure they are in the `tests/report_generator` folder, in a file that starts with
      `test_`, in a class that starts with `Test` in a function that starts with `test_`.

## Linting

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting. Install it via
`pip install -e ".[test]"`.

**Check for violations:**
```bash
ruff check . # Add --fix for autofix
ruff format . # Add --check to not autofix
```

**PyCharm integration:** Settings → Tools → Ruff. Enable all settings.

### Architecture linting

This project uses [import-linter](https://import-linter.readthedocs.io/) to enforce the architecture rules defined in
`sigrid.yaml`. Install it via `pip install -e ".[test]"`.

**Check for violations:**
```bash
lint-imports
```