import requests
import sys

from PyQt5.QtWidgets import QMessageBox

def try_update(current_version: str):
    # get github releases from API
    releases = requests.get(url="https://api.github.com/repos/iNateee/to_do/releases").json()

    latest_version_tag = releases[0]["tag_name"];

    # convert release tags into integers for comparison
    current_version_int = int(''.join(c for c in current_version if c.isdigit()))
    latest_version_int = int(''.join(c for c in latest_version_tag if c.isdigit()))

    # if new version available, prompt the user if they'd like to update
    if latest_version_int > current_version_int:
        qm = QMessageBox()
        ret = qm.question(None, '', f'A new version was found, do you want to update to version {latest_version_tag} and stop?', qm.Yes | qm.No)

        if ret == qm.Yes:
            open('todo_main.py', 'wb').write(requests.get(url=f'https://raw.githubusercontent.com/iNateee/to_do/{latest_version_tag}/todo_main.py').content);
            sys.exit()