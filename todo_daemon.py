import datetime
import pickle
import time
from plyer import notification
from apscheduler.schedulers.background import BackgroundScheduler

SCHEDULE_FILE = 'schedules.pkl'  # Adjust with the correct path if needed

def load_schedules():
    try:
        with open(SCHEDULE_FILE, 'rb') as input:
            schedules = pickle.load(input)
            return schedules
    except (FileNotFoundError, EOFError):
        print("Schedule file not found or empty.")
        return []

def notify_user(schedule, message):
    # Send notification using plyer
    notification.notify(
        title='Task Reminder',
        message=f"'{schedule.name}' is {message}!",
        app_name='ScheduleApp'
    )

def check_for_upcoming_tasks():
    schedules = load_schedules()
    current_datetime = datetime.datetime.now()
    for schedule in schedules:
        if schedule.actual_time or schedule.notification_shown:  # Skip if task is done or notification shown
            continue

        time_until_due = schedule.completion_time - current_datetime
        seconds_until_due = time_until_due.total_seconds()

        # Define your logic for when to notify users here
        if 0 <= seconds_until_due <= 86400:  # Notify if due within the next 24 hours
            notify_user(schedule, "due soon")
            schedule.notification_shown = True  # Update the flag to avoid repeat notifications

            # Save the state back to file
            try:
                with open(SCHEDULE_FILE, 'wb') as output:
                    pickle.dump(schedules, output, pickle.HIGHEST_PROTOCOL)
            except Exception as e:
                print("Failed to save schedules:", e)

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_for_upcoming_tasks, 'interval', minutes=1)  # Adjust interval as needed
    scheduler.start()

    print("Background activity script running. Press Ctrl+C to exit.")
    try:
        # This is here to simulate application activity (which keeps the main thread alive).
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
