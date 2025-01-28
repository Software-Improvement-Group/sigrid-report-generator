# Installation - report generator

## Prerequisites

- Have Python 3.9 or later available and set up so that you can install and use Python packages. This should be preinstalled on SIG Macbooks.

## Install (for end-users)

1. Install the tool itself: `pip3 install -e "git+ssh://git@code.sig.eu/sig/delivery/report-generator.git#egg=report-generator"`. This should complete succesfully.
   - If this fails with the error "ssh: Could not resolve hostname code.sig.eu", make sure you are connected to SIG internal network (VPN) and can log in to https://code.sig.eu in your browser.
   - If this fails and somewhere in the output it says "Permission denied (public key)", you need to add your public key to code.sig.eu settings for authentication:
     - Copy the full contents from the file `~/.ssh/id_rsa.pub` (It should look something like `id-rsa AAAAsdabfkjadsbfsjdaBSFJK... jan@janlaptop`)
     - in https://code.sig.eu, make sure you are logged in. Click your user icon (top left), go to preferences go to SSH Keys, then Add new key and paste the contents from `id_rsa.pub` in the big box. Leave other settings alone (or delete the expiry date if you don't want to redo this in a year from now) and save by pressing "Add key".
   - If this fails with an error message that says something like "error: can't create or remove files in install directory", try adding `--user` to the above command.
   - If this fails with an error message saying something like "error: externally-managed-environment", try installing in a `venv` (Virtual environment). If you don't know how that works, ask for help.
2. If this is your first time installing python packages/commands: Open up the file called `.zshrc` in your Home directory. If this file does not exist, create it. The file may be hidden in finder. In your terminal you can type: `open ~/.zshrc`. At the bottom, add this on a new line:
   `export PATH=${HOME}/Library/Python/3.9/bin:${PATH}` and save your changes.

## Developer instructions

See [developers.md](developers.md)
