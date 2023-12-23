import os
import sys
import datetime
import pickle
import pandas as pd
import updater
from plyer import notification

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QIcon, QPainter, QPixmap
from PyQt5.QtWidgets import (QApplication, QDialog, QFileDialog, QFrame, QGridLayout, QHBoxLayout,
                             QLabel, QLineEdit, QMainWindow, QMenu, QMessageBox, QPushButton, QScrollArea,
                             QSizePolicy, QSystemTrayIcon, QTimeEdit, QVBoxLayout, QWidget, QCalendarWidget,
                             QCheckBox, QComboBox, QDateEdit, QDialogButtonBox, QFormLayout, QInputDialog)


CURRENT_VERSION = "v1.02"


class Schedule:
    def __init__(self, name, importance, completion_time, in_charge, reminder_time):
        self.name = name
        self.importance = importance
        self.completion_time = completion_time
        self.in_charge = in_charge
        self.reminder_time = reminder_time
        self.actual_time = None
        self.starred = False
        self.notification_shown = False  # Track if notification for this task has been shown


    def mark_completed(self, actual_time):
        self.actual_time = actual_time

    def ensure_starred_attribute(self):
        if not hasattr(self, 'starred'):
            self.starred = False

class ScheduleApp(QMainWindow):
    """
    Main application window for the Schedule management system.
    """
    def __init__(self):
        # First, try updating
        updater.try_update(CURRENT_VERSION);

        # Initializes the main window and its UI components.
        super().__init__()
        self.schedules = self.load_schedules()
        self.initUI()
        self.initNotificationTimer()  # initialize the timer for notifications

        # Define the symbol and font for the icon
        symbol = '✔︎'
        font = QFont("Arial", 72)  # Adjust the font and size as necessary

        # Create a QPixmap, render the symbol onto it, and convert it to QIcon
        pixmap = QPixmap(64, 64)  # Adjust size as needed for visibility
        pixmap.fill(Qt.transparent)  # Set background transparent
        painter = QPainter(pixmap)
        painter.setPen(Qt.darkBlue)  # Set the pen color to black or any color that makes the icon visible
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, symbol)  # Draw the symbol in the center
        painter.end()
        icon = QIcon(pixmap)

        # Set the application and tray icons using the symbol
        self.setWindowIcon(icon)
        self.tray_icon = QSystemTrayIcon(icon, self)

        # Create a menu for the tray icon
        tray_menu = QMenu()
        open_action = tray_menu.addAction("Open CheXy")
        open_action.triggered.connect(self.show)  # Reopen the window
        exit_action = tray_menu.addAction("Exit")
        exit_action.triggered.connect(self.quit_application)  # Quit the application completely
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def initUI(self):
        # Sets up the user interface, layout, and widgets.

        self.setWindowTitle(f"CheXy v{CURRENT_VERSION}")  # Correctly include version in title

        self.setGeometry(400, 200, 800, 600)
        self.setMinimumSize(700, 550)

        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        button_frame = QWidget()
        button_layout = QVBoxLayout(button_frame)
        self.create_buttons(button_layout)

        main_layout.addWidget(button_frame)

        middle_frame = QWidget()
        middle_layout = QVBoxLayout(middle_frame)
        self.create_calendar(middle_layout)
        self.create_category_frames(middle_layout)

        main_layout.addWidget(middle_frame)

        right_frame = QWidget()
        right_layout = QVBoxLayout(right_frame)
        self.create_tasks_area(right_layout)

        main_layout.addWidget(right_frame)

        self.display_all_tasks()

    def create_buttons(self, layout):
        # Creates and arranges interactive buttons in the given layout.

        buttons_info = [
            ("➕️", self.add_schedule),
            ("🗑️️", self.delete_schedule),
            ("📝", self.modify_schedule),  # Ensure this method exists
            ("📤", self.export_schedules),
            ("💫", self.star_task)
        ]

        for text, function in buttons_info:
            button = QPushButton(text)
            button.clicked.connect(function)
            button.setStyleSheet("font-size: 24px; background: transparent; border: none;")
            button.setCursor(Qt.PointingHandCursor)
            layout.addWidget(button)

    def create_calendar(self, layout):
        # Creates a calendar widget and adds it to the given layout.

        calendar_frame = QFrame()
        calendar_frame.setStyleSheet("background-color: white; border-radius: 10px;")
        calendar_layout = QVBoxLayout(calendar_frame)
        self.calendar = QCalendarWidget()
        self.calendar.setStyleSheet("background-color: white;")
        calendar_layout.addWidget(self.calendar)
        layout.addWidget(calendar_frame)

    def create_category_frames(self, layout):
        # Creates frames for different task categories like Today, Up-Coming, etc.

        categories_layout = QGridLayout()
        categories = [
            ("Today", self.display_today_tasks),
            ("Up-Coming", self.display_upcoming_tasks),
            ("Starred", self.display_starred_tasks),
            ("Completed", self.display_completed_tasks),
            ("All Tasks", self.display_all_tasks)
        ]

        for i, (title, callback) in enumerate(categories):
            frame = self.create_category_frame(title, callback)
            if title == "All Tasks":
                categories_layout.addWidget(frame, 2, 0, 1, 2)  # Span two columns for "All Tasks"
            else:
                categories_layout.addWidget(frame, i // 2, i % 2)

        layout.addLayout(categories_layout)

    def create_category_frame(self, title, callback):
        # Creates a single category frame with the given title and callback function.

        frame = QFrame()
        frame.mousePressEvent = lambda event: callback()
        layout = QVBoxLayout(frame)
        label = QLabel(title)
        label.setAlignment(Qt.AlignCenter)
        frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        frame.setMinimumHeight(80)
        frame.setStyleSheet("QFrame { border-radius: 10px; background-color: white; } QLabel { font-weight: bold; }")
        label.setFont(QFont("Baloo Bhaijaan", 16))
        layout.addWidget(label)
        return frame


    def create_tasks_area(self, layout):
        # Sets up the area where tasks will be displayed.

        # Add the category label to the top of the tasks area
        self.category_label = QLabel("")  # Create the category label
        self.category_label.setAlignment(Qt.AlignCenter)
        self.category_label.setFont(QFont("Kodchasan", 30, QFont.Bold))
        layout.addWidget(self.category_label)  # Add the label to the layout

        # Create the tasks frame and layout
        self.tasks_frame = QWidget()
        self.tasks_layout = QVBoxLayout(self.tasks_frame)

        # Create the scroll area for tasks
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.tasks_frame)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 0;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                width: 0px;
                height: 0px;
                background: transparent;
            }
        """)

        # Container for the scroll area with rounded corners
        tasks_container = QWidget()
        tasks_container_layout = QVBoxLayout(tasks_container)
        tasks_container_layout.addWidget(scroll_area)
        tasks_container_layout.setContentsMargins(10, 10, 10, 10)
        tasks_container.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 10px;
            }
        """)

        # Add the tasks container to the layout
        layout.addWidget(tasks_container)


    def display_today_tasks(self):
        # Filters and displays tasks due today.

        today = datetime.datetime.now().date()
        self.display_filtered_tasks(lambda s: s.completion_time.date() == today, "Today")

    def display_upcoming_tasks(self):
        # Filters and displays upcoming tasks.

        today = datetime.datetime.now().date()
        self.display_filtered_tasks(lambda s: s.completion_time.date() > today, "Up-Coming")

    def display_starred_tasks(self):
        # Filters and displays starred tasks.

        self.display_filtered_tasks(lambda s: s.starred, "Starred")

    def display_completed_tasks(self):
        # Filters and displays completed tasks.

        self.display_filtered_tasks(lambda s: s.actual_time is not None, "Completed")

    def display_all_tasks(self):
        # Displays all tasks.

        self.display_filtered_tasks(lambda s: True, "All Tasks")

    def display_filtered_tasks(self, filter_func, category_name="All Tasks"):
        # Displays tasks filtered by the given function and updates the category label.

        # Set the category name on the category label
        self.category_label.setText(category_name)

        # Clear existing tasks
        for i in reversed(range(self.tasks_layout.count())):
            widget = self.tasks_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        # Display filtered tasks
        for schedule in filter(filter_func, self.schedules):
            self.display_task(schedule)

    def display_task(self, schedule):
        # Displays a single task in the task area.

        task_frame = QWidget()
        outer_layout = QHBoxLayout(task_frame)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        task_layout = QHBoxLayout()
        task_layout.setContentsMargins(0, 0, 0, 0)
        task_layout.setSpacing(10)

        checkbox = QCheckBox()
        checkbox.setChecked(schedule.actual_time is not None)
        checkbox.stateChanged.connect(lambda state, s=schedule: self.mark_completed(state, s))
        task_layout.addWidget(checkbox)

        content_frame = QWidget()
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)

        importance_symbol = self.get_importance_symbol(schedule.importance, schedule.actual_time is not None)
        star_status = QLabel("💫" if schedule.starred else "")
        content_layout.addWidget(star_status)

        name_label = QLabel(f"{importance_symbol} {schedule.name}")
        name_font = QFont("Hiragino Maru Gothic ProN", 18, QFont.Bold)
        name_label.setFont(name_font)
        content_layout.addWidget(name_label)

        details_label = QLabel(f"Completion: {schedule.completion_time.strftime('%m-%d-%Y')}, In Charge: {schedule.in_charge}")
        details_font = QFont("Tsukushi A Round Gothic", 13, QFont.StyleItalic)
        details_label.setFont(details_font)
        content_layout.addWidget(details_label)

        content_frame.setLayout(content_layout)
        task_layout.addWidget(content_frame)

        outer_layout.addLayout(task_layout)
        outer_layout.addStretch(1)

        if schedule.actual_time is not None:
            self.apply_grey_style(name_label, details_label, star_status)

        self.tasks_layout.addWidget(task_frame)
        separator_line = self.create_separator_line()
        self.tasks_layout.addWidget(separator_line)

    def get_importance_symbol(self, importance, completed):
        # Returns a symbol representing the importance of a task.

        if completed:
            return {"low": "🗒️", "medium": "🗒️🗒️", "high": "🗒️🗒️🗒️"}.get(importance, "")
        return {"low": "📗", "medium": "📙📙", "high": "📕📕📕"}.get(importance, "")

    def apply_grey_style(self, name_label, details_label, star_status):
        # Applies a grey style to completed tasks for visual distinction.

        light_grey_style = "color: #D3D3D3;"
        name_label.setStyleSheet(light_grey_style)
        details_label.setStyleSheet(light_grey_style)
        star_status.setStyleSheet(light_grey_style)

    def create_separator_line(self):
        # Creates a horizontal line for separating tasks visually.

        separator_line = QFrame()
        separator_line.setFrameShape(QFrame.HLine)
        separator_line.setFrameShadow(QFrame.Sunken)
        separator_line.setStyleSheet("background-color: darkgrey;")
        separator_line.setFixedHeight(1)
        return separator_line

    def mark_completed(self, state, schedule):
        # Marks a task as completed or uncompleted based on the checkbox state.

        if state == Qt.Checked:
            schedule.mark_completed(datetime.datetime.now())
        else:
            schedule.mark_completed(None)
        self.display_all_tasks()
        self.save_schedules()  # Save changes

    def get_new_importance(self):
        # Opens a dialog to select new importance for a task.

        dialog = QDialog(self)
        dialog.setWindowTitle("Select New Importance")
        layout = QVBoxLayout(dialog)

        combobox = QComboBox()
        combobox.addItems(["High", "Medium", "Low"])
        layout.addWidget(combobox)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, dialog)
        layout.addWidget(buttonBox)

        buttonBox.accepted.connect(dialog.accept)
        buttonBox.rejected.connect(dialog.reject)

        result = dialog.exec_()
        if result == QDialog.Accepted:
            return combobox.currentText(), True
        else:
            return None, False

    def create_calendar(self, layout):
        # Displays tasks due on a specific date.

        calendar_frame = QFrame()
        calendar_frame.setStyleSheet("background-color: white; border-radius: 10px;")
        calendar_layout = QVBoxLayout(calendar_frame)
        self.calendar = QCalendarWidget()
        self.calendar.setStyleSheet("background-color: white;")
        self.calendar.clicked.connect(self.display_tasks_on_date)  # Connect the signal
        calendar_layout.addWidget(self.calendar)
        layout.addWidget(calendar_frame)

    def display_tasks_on_date(self, date):
        # Displays tasks due on a specific date.

        tasks_on_date = [s for s in self.schedules if s.completion_time.date() == date.toPyDate()]
        self.show_tasks_popup(tasks_on_date, date)

    def show_tasks_popup(self, tasks, date):
        # Shows a popup with tasks for a specific date.

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Tasks for {date.toString('yyyy-MM-dd')}")
        layout = QVBoxLayout(dialog)

        if not tasks:
            layout.addWidget(QLabel("No tasks due on this day."))
        else:
            for task in tasks:
                layout.addWidget(QLabel(f"Task: {task.name}, Importance: {task.importance}"))

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok, Qt.Horizontal, dialog)
        layout.addWidget(buttonBox)
        buttonBox.accepted.connect(dialog.accept)

        dialog.exec_()

    def add_or_modify_schedule(self, schedule=None):
        # Adds a new schedule or modifies an existing one.

        dialog = QDialog(self)
        dialog.setWindowTitle("Add/Modify Schedule" if schedule else "Add Schedule")
        layout = QFormLayout(dialog)

        # Input fields with labels
        name_edit = QLineEdit(schedule.name if schedule else "")
        importance_combo = QComboBox()
        importance_combo.addItems(["High", "Medium", "Low"])
        if schedule:
            importance_combo.setCurrentText(schedule.importance.capitalize())

        completion_date_edit = QDateEdit(
            schedule.completion_time.date() if schedule else datetime.datetime.now().date())
        completion_date_edit.setCalendarPopup(True)
        completion_time_edit = QTimeEdit(
            schedule.completion_time.time() if schedule else datetime.datetime.now().time())

        in_charge_edit = QLineEdit(schedule.in_charge if schedule else "")
        reminder_time_edit = QLineEdit(
            str(schedule.reminder_time) if schedule and schedule.reminder_time is not None else "")

        layout.addRow("Name:", name_edit)
        layout.addRow("Importance:", importance_combo)
        layout.addRow("Completion Date:", completion_date_edit)
        layout.addRow("Completion Time:", completion_time_edit)
        layout.addRow("Person In Charge:", in_charge_edit)
        layout.addRow("Reminder Time (days):", reminder_time_edit)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, dialog)
        layout.addWidget(buttonBox)

        buttonBox.accepted.connect(dialog.accept)
        buttonBox.rejected.connect(dialog.reject)

        result = dialog.exec_()
        if result == QDialog.Accepted:
            name = name_edit.text()
            importance = importance_combo.currentText().lower()
            completion_date = completion_date_edit.date().toPyDate()
            completion_time = completion_time_edit.time().toPyTime()
            completion_datetime = datetime.datetime.combine(completion_date, completion_time)
            in_charge = in_charge_edit.text()

            reminder_time_str = reminder_time_edit.text().strip()
            reminder_time = int(reminder_time_str) if reminder_time_str.isdigit() else 1  # Default or input

            if schedule:
                schedule.name = name
                schedule.importance = importance
                schedule.completion_time = completion_datetime
                schedule.in_charge = in_charge
                schedule.reminder_time = reminder_time
                schedule.notification_shown = False  # Reset notification status
            else:
                new_schedule = Schedule(name, importance, completion_datetime, in_charge, reminder_time)
                self.schedules.append(new_schedule)

            self.display_all_tasks()
            self.save_schedules()

    def add_schedule(self):

        # Directly calls the unified method without a schedule object
        self.add_or_modify_schedule()

    def delete_schedule(self):
        # Deletes a selected schedule.

        schedule_to_delete = self.select_schedule("Delete Schedule",
                                                  "Enter keywords to search for the schedule to delete:")
        if schedule_to_delete:
            self.schedules.remove(schedule_to_delete)
            QMessageBox.information(self, "Success", f"Schedule '{schedule_to_delete.name}' deleted successfully.")
            self.display_all_tasks()
            self.save_schedules()

    def normalize_string(self, input_string):
        # Normalizes a string for comparison purposes.

        return ''.join(input_string.lower().split())

    def select_schedule_to_modify(self):
        # Selects a schedule based on user input.

        # Create a dialog to choose a schedule
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Schedule to Modify")
        layout = QVBoxLayout(dialog)

        # Create a combo box filled with schedule names
        combobox = QComboBox()
        for schedule in self.schedules:
            combobox.addItem(schedule.name)
        layout.addWidget(combobox)

        # Add OK and Cancel buttons
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttonBox)
        buttonBox.accepted.connect(dialog.accept)
        buttonBox.rejected.connect(dialog.reject)

        # Show the dialog and return the selected schedule if OK was clicked
        result = dialog.exec_()
        if result == QDialog.Accepted:
            selected_name = combobox.currentText()
            return next((s for s in self.schedules if s.name == selected_name), None)
        return None


    def select_schedule(self, title, prompt):
        # Selects a schedule based on user input.

        keyword, ok = QInputDialog.getText(self, title, prompt)
        if ok and keyword:
            matching_schedules = self.search_tasks_by_keyword(keyword)

            if not matching_schedules:
                QMessageBox.information(self, "No Match", "No schedules found with the given keyword.")
                return None

            if len(matching_schedules) > 1:
                items = [s.name for s in matching_schedules]
                schedule_name, ok = QInputDialog.getItem(self, "Select Schedule", "Select a schedule:", items, 0, False)
                if not ok:
                    return None
                return next(s for s in matching_schedules if self.normalize_string(s.name) == self.normalize_string(schedule_name))
            else:
                return matching_schedules[0]
        return None

    def modify_schedule(self):
        # Modifies a selected schedule.

        schedule_to_modify = self.select_schedule("Modify Schedule",
                                                  "Enter keywords to search for the schedule to modify:")
        if schedule_to_modify:
            self.add_or_modify_schedule(schedule_to_modify)

    def modify_selected_schedule(self, schedule):
        # Modifies the selected schedule with new details.

        new_name, ok = QInputDialog.getText(self, 'New Name', 'Enter new name (leave blank for no change):')
        if ok:
            new_importance, ok = self.get_new_importance()
            if ok:
                new_completion_time, ok = QInputDialog.getText(self, 'New Completion Time',
                                                               'Enter new scheduled completion time (MM-DD-YYYY, leave blank for no change):')
                if ok:
                    new_in_charge, ok = QInputDialog.getText(self, 'New Person In Charge',
                                                             'Enter the new name of the person in charge (leave blank for no change):')
                    if ok:
                        new_reminder_time, ok = QInputDialog.getInt(self, 'New Reminder Time',
                                                                    'Enter new reminder time in days (leave blank for no change):',
                                                                    min=1)

                        if new_name:
                            schedule.name = new_name
                        if new_importance:
                            schedule.importance = new_importance.lower()
                        if new_completion_time:
                            try:
                                new_completion_date = datetime.datetime.strptime(new_completion_time, "%m-%d-%Y")
                                schedule.completion_time = new_completion_date
                            except ValueError:
                                QMessageBox.critical(self, "Error", "Invalid date format.")
                                return
                        if new_in_charge:
                            schedule.in_charge = new_in_charge
                        if new_reminder_time > 0:
                            schedule.reminder_time = new_reminder_time

                        self.display_all_tasks()
                        self.save_schedules()  # Save changes

    def search_tasks_by_keyword(self, keyword):
        # Searches tasks by a given keyword.

        normalized_keyword = self.normalize_string(keyword)
        return [schedule for schedule in self.schedules if normalized_keyword in self.normalize_string(schedule.name)]

    def star_task(self):
        # Toggles the star status of a selected task.

        keyword, ok = QInputDialog.getText(self, 'Star Schedule', 'Enter keywords to search for the schedule:')
        if ok and keyword:
            matching_schedules = self.search_tasks_by_keyword(keyword)

            if not matching_schedules:
                QMessageBox.information(self, "No Match", "No schedules found with the given keyword.")
                return

            if len(matching_schedules) > 1:
                items = [s.name for s in matching_schedules]
                schedule_name, ok = QInputDialog.getItem(self, "Select Schedule", "Select a schedule to star:", items, 0, False)
                if not ok:
                    return
                schedule_to_star = next(s for s in matching_schedules if s.name == schedule_name)
            else:
                schedule_to_star = matching_schedules[0]

            schedule_to_star.starred = not schedule_to_star.starred
            QMessageBox.information(self, "Info", f"Star status changed for '{schedule_to_star.name}'.")
            self.display_all_tasks()
            self.save_schedules()

    def initNotificationTimer(self):
        # Initializes a timer to periodically check for upcoming tasks and notify the user.

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_for_upcoming_tasks)
        self.timer.start(1000)  # Check every 1 second

    def check_for_upcoming_tasks(self):
        # Checks for upcoming tasks and triggers notifications as needed.

        current_datetime = datetime.datetime.now()
        for schedule in self.schedules:
            if schedule.actual_time or schedule.notification_shown:  # Skip if task is done or notification shown
                continue

            time_until_due = schedule.completion_time - current_datetime
            seconds_until_due = time_until_due.total_seconds()

            if seconds_until_due <= 0:  # Task is due now
                self.notify_user(schedule, "due now")
            elif time_until_due.days == 7 and seconds_until_due <= 604800:  # 7 days
                self.notify_user(schedule, "due in 7 days")
            elif time_until_due.days == 3 and seconds_until_due <= 259200:  # 3 days
                self.notify_user(schedule, "due in 3 days")
            elif time_until_due.days == 2 and seconds_until_due <= 172800:  # 2 days
                self.notify_user(schedule, "due in 2 days")
            elif time_until_due.days == 1 and seconds_until_due <= 86400:  # 1 day
                self.notify_user(schedule, "due in 1 day")
            elif time_until_due.days == schedule.reminder_time:  # Custom reminder
                self.notify_user(schedule, f"custom reminder - {schedule.reminder_time} days before due")

    def notify_user(self, schedule, message):
        try:
            if not schedule.notification_shown:  # Check if notification has already been shown
                notificationMessage = f"'{schedule.name}' is {message}."
                if schedule.importance in ['high']:  # or whatever criteria you define for "important"
                    # Show slide-in notification
                    notification.notify(
                        title='Important Task Reminder',
                        message=notificationMessage + " Right-click the tray icon to open.",
                        app_name='ScheduleApp'
                    )
                    # Show custom popup that ensures the main window is focused after closing
                    self.show_custom_popup(notificationMessage)

                else:
                    # Show only slide-in notifications for less important tasks
                    notification.notify(
                        title='Task Reminder',
                        message=notificationMessage + " Right-click the tray icon to open.",
                        app_name='ScheduleApp'
                    )

                schedule.notification_shown = True  # Mark that notification has been shown
        except Exception as e:
            print("Failed to show notification:", e)

    def show_custom_popup(self, message):
        # Custom method to show a popup and focus the main window after closing
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        # Modify the message below as needed
        customMessage = f"Reminder: {message}\nPlease check the schedule for more details."
        msgBox.setText(customMessage)
        msgBox.setWindowTitle("Task Reminder")
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.buttonClicked.connect(self.on_popup_closed)  # Connect the closed event to a custom handler
        msgBox.exec_()

    def on_popup_closed(self, i):
        # Custom handler for when the popup is closed
        self.show()  # Show the main window
        self.raise_()  # Bring the main window to the front
        self.activateWindow()  # Focus the main window

    def closeEvent(self, event):
        # Reimplements the close event to minimize to tray instead of exiting.

        """Reimplement the close event to minimize to tray instead of exiting."""
        event.ignore()
        self.hide()  # Hide the window
        self.tray_icon.showMessage(
            "ScheduleApp",
            "ScheduleApp is still running. Click the tray icon to restore.",
            QSystemTrayIcon.Information,
            2000
        )

    def export_schedules(self):
        # Exports schedules to an Excel file.

        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Excel files (*.xlsx)")
        if file_path:
            # Ensure the file has the correct extension
            if not file_path.endswith('.xlsx'):
                file_path += '.xlsx'

            try:
                # Create a DataFrame from schedules
                data = {
                    "Name": [schedule.name for schedule in self.schedules],
                    "Importance": [schedule.importance for schedule in self.schedules],
                    "Completion Time": [schedule.completion_time.strftime('%m-%d-%Y') for schedule in self.schedules],
                    "In Charge": [schedule.in_charge for schedule in self.schedules],
                    "Reminder Time": [schedule.reminder_time for schedule in self.schedules],
                    "Actual Time": [(schedule.actual_time.strftime('%m-%d-%Y') if schedule.actual_time else "N/A") for
                                    schedule in self.schedules],
                    "Starred": [schedule.starred for schedule in self.schedules]
                }
                df = pd.DataFrame(data)
                # Write DataFrame to an Excel file
                df.to_excel(file_path, index=False)
                QMessageBox.information(self, "Success", "Schedules exported successfully to Excel.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred while exporting schedules: {e}")

    def quit_application(self):
        #Ensures a clean exit
        self.tray_icon.hide()  # Optional: hide the tray icon immediately
        QApplication.quit()  # Quit the application

    def save_schedules(self):
        try:
            home_dir = os.path.expanduser('~')
            file_path = os.path.join(home_dir, 'schedules.pkl')  # Save in the home directory
            with open(file_path, 'wb') as output:
                pickle.dump(self.schedules, output, pickle.HIGHEST_PROTOCOL)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while saving schedules: {e}")

    def load_schedules(self):
        try:
            home_dir = os.path.expanduser('~')
            file_path = os.path.join(home_dir, 'schedules.pkl')
            with open(file_path, 'rb') as input:
                schedules = pickle.load(input)
                for schedule in schedules:
                    schedule.ensure_starred_attribute()
                    if not hasattr(schedule, 'notification_shown'):
                        schedule.notification_shown = False
                return schedules
        except (FileNotFoundError, EOFError):
            return []


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ScheduleApp()
    try:
        ex.show()
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        print("Program interrupted by user, exiting...")
        sys.exit(0)


# pyinstaller --onefile --windowed --icon=/Users/nathanm/Downloads/to_do-main/CheXy.png --name CheXy todo_main.py
# pyinstaller --onefile --windowed --icon=/Users/nathanm/Downloads/to_do-main/CheXy.png --name CheXy --additional-hooks-dir=/Users/nathanm/Downloads/to_do-main/ /Users/nathanm/Downloads/to_do-main/todo_main.py
