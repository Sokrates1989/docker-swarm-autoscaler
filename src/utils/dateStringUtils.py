# Date based string functions like getting string of current day for logfiles.

# Get date.
from datetime import datetime
# For making time timezone aware.
import pytz
# Get environment vars.
import os

# MessagePlatformHandler.
import messagePlatformHandler as MessagePlatformHandler

def getDateStringForLogFileName():
    """
    Get a string representing the current date formatted for log file names.

    Returns:
        str: A string representing the current date in the format "YYYY_MM_DD".
    """
    # Get the current date adjusted to the timezone.
    now = datetime.now(getTimezone())
    return now.strftime("%Y_%m_%d")

def getDateStringForLogTag():
    """
    Get a string representing the current datetime formatted for log tags.

    Returns:
        str: A string representing the current datetime in the format "[YYYY-MM-DD HH:MM:SS]".
    """
    # Get the current datetime adjusted to the timezone.
    now = datetime.now(getTimezone())
    # Format the datetime as a string with a specific format.
    date_time = now.strftime("%Y-%m-%d %H:%M:%S")
    # Construct the log tag string.
    currentLogTimeString = "[" + date_time + "]"
    return currentLogTimeString

def getTimezone():
    """
    Get the timezone based on the environment variable TIMEZONE.

    View all valid timezones: 

    Returns:
        pytz.timezone: A pytz timezone object representing the timezone.
    """
    # Default timezone to UTC.
    timezone = 'Etc/UTC'
    try:
        # Try to get the timezone from the environment variable.
        timezone = os.getenv("TIMEZONE")
    except Exception as e:
        # Log a warning if timezone could not be retrieved from environment.
        warning_msg = f"DateStringUtils: Could not get TIMEZONE from environment: {str(e)}"
        messagePlatformHandler = MessagePlatformHandler.MessagePlatformHandler(useDateStringUtils=False)
        messagePlatformHandler.handle_warning(warning_msg, useDateStringUtils=False)
    finally:
        # Check if the provided timezone is valid.
        if timezone not in pytz.all_timezones:
            # Log a warning if the timezone is invalid and default to UTC.
            warning_msg = f"DateStringUtils: Invalid timezone provided: {timezone}, defaulting to Etc/UTC"
            messagePlatformHandler = MessagePlatformHandler.MessagePlatformHandler(useDateStringUtils=False)
            messagePlatformHandler.handle_warning(warning_msg, useDateStringUtils=False)
            timezone = "Etc/UTC"

    # Return the timezone object.
    return pytz.timezone(timezone)
