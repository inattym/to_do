import requests
import sys
import os
import subprocess
from packaging import version
from PyQt5.QtWidgets import QMessageBox, QApplication

def check_dependencies():
    try:
        import requests
        from PyQt5.QtWidgets import QMessageBox, QApplication
        from packaging import version
    except ImportError as e:
        print(f"Missing dependency: {str(e)}")
        print("Please install all required dependencies.")
        sys.exit(1)

def try_update(current_version: str):
    check_dependencies()

    try:
        # Get GitHub releases from API
        response = requests.get("https://api.github.com/repos/inattym/to_do/releases",
                                headers={"Accept": "application/vnd.github.v3+json"})
        response.raise_for_status()  # Raises an HTTPError for bad responses
        releases = response.json()

        if not releases:
            print("No releases found.")
            return

        latest_version_tag = releases[0]["tag_name"]

        # Use packaging.version for robust version comparison
        if version.parse(latest_version_tag) > version.parse(current_version):
            app = QApplication.instance() or QApplication(sys.argv)
            qm = QMessageBox()
            ret = qm.question(None, 'Update Available',
                              f'A new version {latest_version_tag} is available. Do you want to update?',
                              qm.Yes | qm.No)

            if ret == qm.Yes:
                # Download the new version
                new_content = requests.get(
                    f'https://raw.githubusercontent.com/inattym/to_do/{latest_version_tag}/todo_main.py').content

                # Write the new content to a temporary file
                temp_file = 'todo_main_new.py'
                try:
                    with open(temp_file, 'wb') as f:
                        f.write(new_content)

                    # Replace the old file with the new one
                    os.replace(temp_file, 'todo_main.py')
                except PermissionError:
                    QMessageBox.warning(None, "Update Error",
                                        "Permission denied. Run the application with appropriate permissions.")
                    return
                except Exception as e:
                    QMessageBox.warning(None, "Update Error", f"Failed to write new version: {str(e)}")
                    return

                QMessageBox.information(None, "Update Successful",
                                        "Update completed. The application will now restart.")

                # Restart the application
                subprocess.Popen([sys.executable] + sys.argv)
                sys.exit(0)

    except requests.RequestException as e:
        QMessageBox.warning(None, "Update Error", f"Network error: {str(e)}")
    except Exception as e:
        QMessageBox.warning(None, "Update Error", f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    try_update("1.0.2")  # Replace with your current version