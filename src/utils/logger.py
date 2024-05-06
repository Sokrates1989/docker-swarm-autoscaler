# Logs information and errors both in day based files and one big file.

import os
import fileUtils
import dateStringUtils


class Logger:

    def __init__(self, logScope=None, useDateStringUtils=True):
        """
        Constructor creating logfiles and paths.
        
        Args:
            logScope (str): Scope for logging.
            useDateString (bool): Whether to use the datestringUtils or not. Prevents an infinite loop logging from datestringUtils.
        """
        if logScope is None:
            logScopeStartText = "SWARM_AUTOSCALER"
            self.logtext_verbose = logScopeStartText + "_VERBOSE"
            self.logtext_info = logScopeStartText + "_INFO"
            self.logtext_warning = logScopeStartText + "_WARNING"
            self.logtext_error = logScopeStartText + "_ERROR"
        else:
            self.logtext_verbose = "UNKNOWN_VERBOSE"
            self.logtext_info = "UNKNOWN_INFO"
            self.logtext_warning = "UNKNOWN_WARNING"
            self.logtext_error = "UNKNOWN_ERROR"

        self.logPath = os.path.join("/code", "logs")
        self.globalErrorLogFile = os.path.join(self.logPath, "errorlog.txt")
        self.globalLogFile = os.path.join(self.logPath, "log.txt")
        fileUtils.createFileIfNotExists(self.globalErrorLogFile)
        fileUtils.createFileIfNotExists(self.globalLogFile)

        self.dayLogPath = os.path.join(self.logPath, "dayBased")
        self.updateDayBasedLogFilePaths(useDateStringUtils=useDateStringUtils)

        # Prepare warning messages to log in case of warnings in setting log settings below.
        warning_messages = []

        # Log Level.
        self._valid_log_levels = ["INFO", "VERBOSE", "WARNING_AND_ERRORS_ONLY"]
        self._global_log_level = "INFO"
        try:
            self._global_log_level = os.getenv("LOG_LEVEL")
        finally:
            if self._global_log_level not in self._valid_log_levels:
                warning_msg = f"Logger: Invalid global log level provided: {self._global_log_level}, defaulting to \"INFO\""
                warning_messages.append(warning_msg)
                self._global_log_level = "INFO"

        # Log style.
        self._valid_log_styles = ["PRINT_ONLY", "LOGFILE_ONLY", "PRINT_AND_LOGFILE"]
        self._log_style = "PRINT_AND_LOGFILE"
        try:
            self._log_style = os.getenv("LOG_STYLE")
        finally:
            if self._log_style not in self._valid_log_styles:
                warning_msg = f"Logger: Invalid log style provided: {self._log_style}, defaulting to \"PRINT_AND_LOGFILE\""
                warning_messages.append(warning_msg)
                self._log_style = "PRINT_AND_LOGFILE"

        # Log all warning messages after both log level and log style are set.
        for warning_msg in warning_messages:
            self.warning(warning_msg)



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
        dayBasedLogFileName = dateStringForLogFileName + "_log.txt"
        self.dayBasedErrorLogFile = os.path.join(self.dayLogPath, dayBasedErrorLogFileName)
        self.dayBasedLogFile = os.path.join(self.dayLogPath, dayBasedLogFileName)
        fileUtils.createFileIfNotExists(self.dayBasedErrorLogFile)
        fileUtils.createFileIfNotExists(self.dayBasedLogFile)


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
            self._log(self.globalLogFile, fullLogText)
            self._log(self.dayBasedErrorLogFile, fullLogText)
            self._log(self.dayBasedLogFile, fullLogText)

        # Log style printing?
        if self._log_style == "PRINT_ONLY" or self._log_style == "PRINT_AND_LOGFILE":
            print(fullLogText)

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
            print(fullLogText)
        

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
                print(fullLogText)

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
                print(fullLogText)

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
                warning_msg = f"Logger.{sourceMethodForLogMsg}(): Invalid custom log level provided: {customLogLevel}, defaulting to global log level \"{self._global_log_level}\""
                print(warning_msg)
                self.warning(warning_msg)
        return log_level

    def _log(self, file, fullLogText):
        """
        Write a string to a file.

        Args:
            file (str): File path.
            fullLogText (str): Text to log.
        """
        with open(file, 'a+') as f:
            f.write("\n" + fullLogText)
