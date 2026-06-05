# Developer instructions

Pull requests welcome! If you have a small improvement, feel free to just create a pull request and assign a reviewer
from the core team. If you propose a larger change, it's best to discuss it with the core team before you get started to
ensure it aligns with our thoughts and goals. In either case, please make sure the change is maintainable and tested.
Below are some instructions to get you started.

For the architecture of this project, see [architecture.md](architecture.md).

## Install

- Go into the `report-generator` directory.
- Create a virtual environment (required for development): `python3 -m venv .venv`
- Activate the virtual environment:
  - macOS/Linux: `source .venv/bin/activate`
  - Windows (PowerShell): `.venv\Scripts\Activate.ps1`
  - Windows (cmd): `.venv\Scripts\activate.bat`
- Upgrade pip in the venv: `python -m pip install --upgrade pip`
- Install your latest changes in the venv: `python -m pip install -e .` (re-do this any time you want to run the tool
  using your latest changes)
  Note: This will override the `report-generator` tool installed using the "for end-users" method.
- If you plan to run tests or linting, install the extra dependencies in the same venv:
  `python -m pip install -e ".[test]"`

Always run `pip` inside the activated virtual environment to avoid installing packages globally.

If you want to run the Report Generator locally without going through the motions of installing the Python package:
`./src/run.py`. The arguments are the same as for the normal entry point.

## Coding / IDE

- **IDE**: Feel free to use your favorite IDE. Visual Studio Code with the Python extension and Python Debugger
  extension from Microsoft is popular and free.
- **PyCharm**: Configure PyCharm to use the `.venv` interpreter so it installs packages inside the virtual environment.
  Go to Settings/Preferences → Project → Python Interpreter → Add Interpreter, then either:
  - **Existing environment**: select `.venv/bin/python` (macOS/Linux) or `.venv\Scripts\python.exe` (Windows), or
  - **New environment**: let PyCharm create a venv for the project and use that as the interpreter.
- **Maintainability**:  Make sure your code is maintainable. We have a Sigrid CI integration up and running.

## Testing

### Unit tests

- Install Python test dependencies (once, or at least infrequently): `python -m pip install -e ".[test]"`
- Run Python unit tests: `python -m pytest`
    - When writing new tests, make sure they are in the `tests/report_generator` folder, in a file that starts with
      `test_`, in a class that starts with `Test` in a function that starts with `test_`.

## Linting

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting. Install it via
`python -m pip install -e ".[test]"`.

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