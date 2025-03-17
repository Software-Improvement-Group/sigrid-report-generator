# Installation - report generator

## Prerequisites

- Have Python 3.9 or later available and set up so that you can install and use Python packages.

## Install (for end-users)

1. Clone this repository and `cd` into it.
1. Install the tool itself: `pip3 install -e ./report-generator"`. This should complete succesfully.
    - If this fails with an error message that says something like "error: can't create or remove files in install
      directory", try adding `--user` to the above command.
    - If this fails with an error message saying something like "error: externally-managed-environment", try installing
      in a `venv` (Virtual environment). If you don't know how that works, ask for help.
2. If this is your first time installing Python packages/commands, you may need to add the Python bin directory to your
   `PATH` environment variable. Here are the steps to do this:

    1. **Determine the Python bin directory**:
        - The Python bin directory is typically located in the `bin` subdirectory of your Python installation.

    2. **Modify your shell configuration file**:
        - Open your shell configuration file in a text editor. This file is usually named `.bashrc`, `.zshrc`,
          `.profile`, or `.bash_profile`.
        - Add the following line to the file, replacing `/path/to/python/bin` with the actual path to your Python bin
          directory:

          ```sh
          export PATH="/path/to/python/bin:$PATH"
          ```

    3. **Apply the changes**:
        - Save the file and close the text editor.
        - Apply the changes by running the following command in your terminal (for Unix-like systems):

          ```sh
          source ~/.bashrc  # or source ~/.zshrc, or source ~/.profile, depending on the file you edited
          ```

        - For Windows, you can add the Python bin directory to the `Path` environment variable through the System
          Properties > Environment Variables interface.

   By following these steps, you ensure that the Python bin directory is included in your `PATH`, allowing you to run
   Python and its associated tools from any directory.

Alternatively, you can use the docker image: `softwareimprovementgroup/sigrid-integrations`

## Developer instructions

See [developers.md](developers.md)