## Date based string functions like getting string of current day for logfiles.

# Get date.
from datetime import datetime
# For getting unixtimestamp.
import time

# Get string like "2022_03_31".
def getDateStringForLogFileName():
	now  = datetime.now()
	return now.strftime("%Y_%m_%d")

# Get string like "[2022-03-31 22:02:04]".
def getDateStringForLogTag():
	now  = datetime.now()
	date_time = now.strftime("%Y-%m-%d %H:%M:%S")
	currentLogTimeString = "[" + date_time + "]"
	return currentLogTimeString