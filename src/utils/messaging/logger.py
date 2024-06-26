# Logs information and errors both in day based files and one big file.

import os
import fileUtils
import dateStringUtils

# MessagePlatformHandler.
import messagePlatformHandler as MessagePlatformHandler


class Logger:

    def __init__(self, messagePlatformHandler: MessagePlatformHandler, logScope=None, useDateStringUtils=True):
        """
        Constructor creating logfiles and paths.
        
        Args:
            logScope (str): Scope for logging.
            useDateString (bool): Whether to use the datestringUtils or not. Prevents an infinite loop logging from datestringUtils.
        """
        self._messagePlatformHandler = messagePlatformHandler
        
        if logScope is None:
            logScopeStartText = "SWARM_AUTOSCALER"
            self.logtext_verbose = logScopeStartText + "_VERBOSE"
            self.logtext_info = logScopeStartText + "_INFO"
            self.logtext_warning = logScopeStartText + "_WARNING"
            self.logtext_error = logScopeStartText + "_ERROR"
            self.logtext_important = logScopeStartText + "_IMPORTANT"
        else:
            self.logtext_verbose = "UNKNOWN_VERBOSE"
            self.logtext_info = "UNKNOWN_INFO"
            self.logtext_warning = "UNKNOWN_WARNING"
            self.logtext_error = "UNKNOWN_ERROR"
            self.logtext_important = "UNKNOWN_IMPORTANT"

        self.logPath = os.path.join("/code", "logs")
        self.globalErrorLogFile = os.path.join(self.logPath, "errorlog.txt")
        self.globalImportantLogFile = os.path.join(self.logPath, "importantlog.txt")
        self.globalLogFile = os.path.join(self.logPath, "log.txt")
        fileUtils.createFileIfNotExists(self.globalErrorLogFile)
        fileUtils.createFileIfNotExists(self.globalImportantLogFile)
        fileUtils.createFileIfNotExists(self.globalLogFile)

        self.dayLogPath = os.path.join(self.logPath, "dayBased")
        self.updateDayBasedLogFilePaths(useDateStringUtils=useDateStringUtils)

        # Prepare warning messages to log in case of warnings in setting log settings below.
        warning_messages = []

        # Log Level.
        self._valid_log_levels = ["INFO", "VERBOSE", "IMPORTANT_ONLY"]
        self._global_log_level = "INFO"
        try:
            self._global_log_level = os.getenv("LOG_LEVEL")
        finally:
            if self._global_log_level not in self._valid_log_levels:
                warning_msg = f"Logger: Invalid global log level provided: <EMPHASIZE_STRING_START_TAG>{self._global_log_level}</EMPHASIZE_STRING_END_TAG>, defaulting to <EMPHASIZE_STRING_START_TAG>INFO</EMPHASIZE_STRING_END_TAG>"
                warning_messages.append(warning_msg)
                self._global_log_level = "INFO"

        # Log style.
        self._valid_log_styles = ["PRINT_ONLY", "LOGFILE_ONLY", "PRINT_AND_LOGFILE"]
        self._log_style = "PRINT_AND_LOGFILE"
        try:
            self._log_style = os.getenv("LOG_STYLE")
        finally:
            if self._log_style not in self._valid_log_styles:
                warning_msg = f"Logger: Invalid log style provided: <EMPHASIZE_STRING_START_TAG>{self._log_style}</EMPHASIZE_STRING_END_TAG>, defaulting to <EMPHASIZE_STRING_START_TAG>PRINT_AND_LOGFILE</EMPHASIZE_STRING_END_TAG>"
                warning_messages.append(warning_msg)
                self._log_style = "PRINT_AND_LOGFILE"

        # Log all warning messages after both log level and log style are set.
        for warning_msg in warning_messages:
            # Since instantiation itself is not complete, we log directly instead of letting messagePlatformHandler handle things.
            self.warning(warning_msg, useDateStringUtils=useDateStringUtils)



    def updateDayBasedLogFilePaths(self, useDateStringUtils=True):
        """
        Create dayBased logfile paths.

        Args:
            useDateString (bool): Whether to use the datestringUtils or not. Prevents an infinite loop logging from datestringUtils.
        """
        dateStringForLogFileName = "timezone_error"
        if useDateStringUtils:
            dateStringForLogFileName = dateStringUtils.getDateStringForLogFileName()
        dayBasedErrorLogFileName = dateStringForLogFileName + "_errorlog.txt"
        dayBasedImportantLogFileName = dateStringForLogFileName + "_importantlog.txt"
        dayBasedLogFileName = dateStringForLogFileName + "_log.txt"
        self.dayBasedErrorLogFile = os.path.join(self.dayLogPath, dayBasedErrorLogFileName)
        self.dayBasedImportantLogFile = os.path.join(self.dayLogPath, dayBasedImportantLogFileName)
        self.dayBasedLogFile = os.path.join(self.dayLogPath, dayBasedLogFileName)
        fileUtils.createFileIfNotExists(self.dayBasedErrorLogFile)
        fileUtils.createFileIfNotExists(self.dayBasedImportantLogFile)
        fileUtils.createFileIfNotExists(self.dayBasedLogFile)


    def importantInfo(self, importantInfoToLog, customLogLevel=None):
        """
        Logs an Error to 4 logfiles.

        Args:
            importantInfoToLog (str): Important info message to log.
            customLogLevel (str|None): An override for the global log level. Services can have individual log levels.
        """
        self.updateDayBasedLogFilePaths()
        fullLogText = "" + dateStringUtils.getDateStringForLogTag() + " - " + "[" + self.logtext_important + "]" + " - [" + importantInfoToLog + "]"

        # Log style logging?
        if self._log_style == "LOGFILE_ONLY" or self._log_style == "PRINT_AND_LOGFILE":
            self._log(self.globalImportantLogFile, fullLogText)
            self._log(self.globalLogFile, fullLogText)
            self._log(self.dayBasedImportantLogFile, fullLogText)
            self._log(self.dayBasedLogFile, fullLogText)

        # Log style printing?
        if self._log_style == "PRINT_ONLY" or self._log_style == "PRINT_AND_LOGFILE":
            self._print_log_message(fullLogText)


    def error(self, errorToLog, customLogLevel=None):
        """
        Logs an Error to 4 logfiles.

        Args:
            errorToLog (str): Error message to log.
            customLogLevel (str|None): An override for the global log level. Services can have individual log levels.
        """
        self.updateDayBasedLogFilePaths()
        fullLogText = "" + dateStringUtils.getDateStringForLogTag() + " - " + "[" + self.logtext_error + "]" + " - [" + errorToLog + "]"

        # Log style logging?
        if self._log_style == "LOGFILE_ONLY" or self._log_style == "PRINT_AND_LOGFILE":
            self._log(self.globalErrorLogFile, fullLogText)
            self._log(self.globalImportantLogFile, fullLogText)
            self._log(self.globalLogFile, fullLogText)
            self._log(self.dayBasedErrorLogFile, fullLogText)
            self._log(self.dayBasedImportantLogFile, fullLogText)
            self._log(self.dayBasedLogFile, fullLogText)

        # Log style printing?
        if self._log_style == "PRINT_ONLY" or self._log_style == "PRINT_AND_LOGFILE":
            self._print_log_message(fullLogText)

    def warning(self, warningToLog, customLogLevel=None, useDateStringUtils=True):
        """
        Logs a Warning to 4 logfiles.

        Args:
            warningToLog (str): Warning message to log.
            customLogLevel (str|None): An override for the global log level. Services can have individual log levels.
            useDateString (bool): Whether to use the datestringUtils or not. Prevents an infinite loop logging from datestringUtils.
        """   
        self.updateDayBasedLogFilePaths(useDateStringUtils=useDateStringUtils)

        # Prepare Warning message with or without datestring.
        fullLogText = ""
        if useDateStringUtils:
            fullLogText += dateStringUtils.getDateStringForLogTag() + " - "
        fullLogText += "[" + self.logtext_warning + "]" + " - [" + warningToLog + "]"

        # Log style logging?
        if self._log_style == "LOGFILE_ONLY" or self._log_style == "PRINT_AND_LOGFILE":
            self._log(self.globalErrorLogFile, fullLogText)
            self._log(self.globalLogFile, fullLogText)
            self._log(self.dayBasedErrorLogFile, fullLogText)
            self._log(self.dayBasedLogFile, fullLogText)

        # Log style printing?
        if self._log_style == "PRINT_ONLY" or self._log_style == "PRINT_AND_LOGFILE":
            self._print_log_message(fullLogText)
        

    def information(self, informationToLog, customLogLevel=None):
        """
        Logs an Information to 2 logfiles.

        Args:
            informationToLog (str): Information message to log.
            customLogLevel (str|None): An override for the global log level. Services can have individual log levels.
        """
        # Determine log level from global log level and customlogLevel.
        log_level=self._determine_log_level(customLogLevel, "information")
        
        # Log level sufficient?
        if log_level == "VERBOSE" or log_level == "INFO":
            # Prepare log message.
            self.updateDayBasedLogFilePaths()
            fullLogText = "" + dateStringUtils.getDateStringForLogTag() + " - " + "[" + self.logtext_info + "]" + " - [" + informationToLog + "]"

            # Log style logging?
            if self._log_style == "LOGFILE_ONLY" or self._log_style == "PRINT_AND_LOGFILE":
                self._log(self.globalLogFile, fullLogText)
                self._log(self.dayBasedLogFile, fullLogText)

            # Log style printing?
            if self._log_style == "PRINT_ONLY" or self._log_style == "PRINT_AND_LOGFILE":
                self._print_log_message(fullLogText)

    def verboseInfo(self, verboseInformationToLog, customLogLevel=None):
        """
        Logs a verbose info to 2 logfiles, if logger is in verbose mode.

        Args:
            verboseInformationToLog (str): Verbose information message to log.
            customLogLevel (str|None): An override for the global log level. Services can have individual log levels.
        """
        # Determine log level from global log level and customlogLevel.
        log_level=self._determine_log_level(customLogLevel, "verboseInfo")

        # Log level sufficient?
        if log_level == "VERBOSE":
            # Prepare log message.
            self.updateDayBasedLogFilePaths()
            fullLogText = "" + dateStringUtils.getDateStringForLogTag() + " - " + "[" + self.logtext_verbose + "]" + " - [" + verboseInformationToLog + "]"

            # Log style logging?
            if self._log_style == "LOGFILE_ONLY" or self._log_style == "PRINT_AND_LOGFILE":
                self._log(self.globalLogFile, fullLogText)
                self._log(self.dayBasedLogFile, fullLogText)

            # Log style printing?
            if self._log_style == "PRINT_ONLY" or self._log_style == "PRINT_AND_LOGFILE":
                self._print_log_message(fullLogText)

    def _determine_log_level(self, customLogLevel, sourceMethodForLogMsg):
        """
        Determines the log level based on the global log level and custom log level.

        Args:
            customLogLevel          (str): Custom log level provided.
            sourceMethodForLogMsg   (str): The source method to put into log message in case of an error.

        Returns:
            str: The determined log level.
        """
        log_level = self._global_log_level
        if customLogLevel is not None:
            if customLogLevel in self._valid_log_levels:
                log_level = customLogLevel
            else:
                warning_msg = f"Logger.{sourceMethodForLogMsg}(): Invalid custom log level provided: <EMPHASIZE_STRING_START_TAG>{customLogLevel}</EMPHASIZE_STRING_END_TAG>, defaulting to global log level <EMPHASIZE_STRING_START_TAG>{self._global_log_level}</EMPHASIZE_STRING_END_TAG>"
                self._print_log_message(warning_msg)
                self._messagePlatformHandler.handle_warning(warning_msg)
        return log_level

    def _log(self, file, fullLogText):
        """
        Write a string to a file.

        Replaces Special tags to improve output.

        Args:
            file (str): File path.
            fullLogText (str): Text to log.
        """
        # String replacements.
        fullLogText=fullLogText.replace("<EMPHASIZE_STRING_START_TAG>", "\"")
        fullLogText=fullLogText.replace("</EMPHASIZE_STRING_END_TAG>", "\"")
        
        # Write message.
        with open(file, 'a+') as f:
            f.write("\n" + fullLogText)


    def _print_log_message(self, message_to_print:str):
        """
        Print message to cli.

        Replaces Special tags to improve output.

        Args:
            message_to_print (str): The message to pring.
        """
        # String replacements.
        message_to_print=message_to_print.replace("<EMPHASIZE_STRING_START_TAG>", "\"")
        message_to_print=message_to_print.replace("</EMPHASIZE_STRING_END_TAG>", "\"")

        # Print message.
        print(message_to_print)
