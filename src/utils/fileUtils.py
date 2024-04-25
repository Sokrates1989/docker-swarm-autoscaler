## Basic file operations.

# Interaction with operating system (read write files).
import os

# For string sanitization.
import re

def createFileIfNotExists(fileToCreateIfNotExists):
	# Separate directory from filename.
	if "/" in fileToCreateIfNotExists:
		lastSlashPosition = fileToCreateIfNotExists.rfind("/")

		directoryName = fileToCreateIfNotExists[0:(lastSlashPosition)]
		if os.path.exists(directoryName) == False:
			os.makedirs(directoryName)
			os.chmod(directoryName, 0o775)

		if os.path.exists(fileToCreateIfNotExists) == False:
			os.mknod(fileToCreateIfNotExists)
			os.chmod(fileToCreateIfNotExists, 0o775)
	else:
		print("Cannot create a file without directory (pass filename containing filepath like \"path/to/file.txt\")")



# Get a valid filename for a string.
def getValidFileNameForString(stringToConvertToFileName, fileType):
	whiteListedCharactersRegEx = "[^a-zA-Z0-9.\-_]"
	validFilename = re.sub(whiteListedCharactersRegEx, '', str(stringToConvertToFileName) )
	validFilename = validFilename[:100]
	validFilename += "." + str(fileType)
	return validFilename


# Read string from file.
def readStringFromFile(fileToReadStringFrom):
	string = ""
	with open(fileToReadStringFrom, 'r') as file:
		string = file.read().rstrip()
	return string


# Overwrite string of file.
# !!! Completely removes previous content !!!
def overwriteContentOfFile(fileToEdit, newString):
	with open(fileToEdit,'w') as f:
		f.write(str(newString))
		