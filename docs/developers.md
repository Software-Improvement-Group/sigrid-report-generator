# Developer instructions

Merge requests welcome! If you have a small improvement, feel free to just create a merge request and assign a reviewer from the core team. If you propose a larger change, it's best to discuss it with the core team before you get started to ensure it aligns with our thoughts and goals. In either case, please make sure the change is maintainable and tested. Below are some instructions to get you started.

## Download

- Go to the directory where you want to store the tool in your terminal and run: `git clone git@code.sig.eu:sig/delivery/report-generator.git`

## Install

- Go into the directory of the folder you just downloaded: `cd report-generator`
- Install your latest changes: `pip3 install -e .`  (Re-do this any time you want to run the tool using your latest changes)
Note: This will override the `report-generator` tool installed using the "for end-users" method.

If you want to run the Report Generator locally without going through the motions of installing the Python package: `./src/run.py`. The arguments are the same as for the normal entry point. 

## Coding / IDE

- **IDE**: Feel free to use your favorite IDE. Visual Studio Code with the Python extension and Python Debugger extension from Microsoft is popular and free.
- **Maintainability**:  Make sure your code is maintainable. We have a [Sigrid](https://sigrid-says.com/sig/report-generator/) and CI integration up and running.

## Testing

### Unit tests

- Install Python test dependencies (once, or at least infrequently): `pip3 install -e ."[test]"`
- Run Python unit tests: `pytest`
  - When writing new tests, make sure they are in the `tests/report_generator` folder, in a file that starts with `test_`, in a class that starts with `Test` in a function that starts with `test_`.

### Visual tests

Right now this is manual effort, but if the standard templates mature, borrow the visual testing implementation from `TechValidationSlides`.
