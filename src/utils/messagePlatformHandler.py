# Distributes information to logger, telegram, email based on settings.

# Definitions.
from valid_values import MessagingPlatforms

# Logger.
import logger as Logger

class MessagePlatformHandler:

    def __init__(self, useDateStringUtils=True):
        """
        Constructor handling information distribution.
        """
        # Accumulated messages.
        self._importantEmailMessages = {}
        self._importantTelegramMessages = {}
        self._errorMessages = {}
        self._warningMessages = {}
        self._informationMessages = {}
        self._verboseMessages = {}

        # Unknown service indicator.
        self._unknownServiceIndicator = "unknown service"

        # Logger.
        self._logger = Logger.Logger(useDateStringUtils=useDateStringUtils)

    def handle_important_info(self, important_info, autoscale_service, scaling_metrics=[]):
        """
        Handles important information.

        Logs information directly and accumulates messages to send via other messaging platforms later.

        Args:
            autoscale_service (AutoScaleService): The autoscale service this information is about
            important_info (str): Important info message to handle.
        """
        # Log directly.
        important_log_message=important_info
        # Add metric info to message.
        for scalingMetric in scaling_metrics:
            important_log_message += " - " + scalingMetric.as_string(MessagingPlatforms.LOGGING)
        self._logger.importantInfo(important_log_message, autoscale_service.get_service_log_level())

        ### Accumulate messages to send later ###
        service_name = autoscale_service.get_service_name()

        # E-Mail.
        important_mail_message=important_info
        # Add metric info to message.
        for scalingMetric in scaling_metrics:
            important_mail_message += "\n" + scalingMetric.as_string(MessagingPlatforms.EMAIL)
        # Add message to array.
        if service_name not in self._importantEmailMessages:
            self._importantEmailMessages[service_name] = []
        self._importantEmailMessages[service_name].append(important_mail_message)

        # Telegram.
        important_telegram_message=important_info
        # Add metric info to message.
        for scalingMetric in scaling_metrics:
            important_telegram_message += "\n" + scalingMetric.as_string(MessagingPlatforms.TELEGRAM)
        # Add message to array.
        if service_name not in self._importantTelegramMessages:
            self._importantTelegramMessages[service_name] = []
        self._importantTelegramMessages[service_name].append(important_telegram_message)

    def handle_error(self, error_info, autoscale_service=None):
        """
        Handles error information.

        Logs information directly and accumulates messages to send via other messaging platforms later.

        Args:
            autoscale_service (AutoScaleService): The autoscale service this information is about
            error_info (str): Error info message to handle.
        """
        # Log directly.
        if autoscale_service:
            service_name = autoscale_service.get_service_name()
            self._logger.error(error_info, autoscale_service.get_service_log_level())
        else:
            service_name = self._unknownServiceIndicator

        # Accumulate messages to send later.
        if service_name not in self._errorMessages:
            self._errorMessages[service_name] = []
        self._errorMessages[service_name].append(error_info)

    def handle_warning(self, warning_info, autoscale_service, useDateStringUtils=True):
        """
        Handles warning information.

        Logs information directly and accumulates messages to send via other messaging platforms later.

        Args:
            autoscale_service (AutoScaleService): The autoscale service this information is about
            warning_info (str): Warning info message to handle.
        """
        # Log directly.
        self._logger.warning(warning_info, autoscale_service.get_service_log_level(), useDateStringUtils)

        # Accumulate messages to send later.
        service_name = autoscale_service.get_service_name()
        if service_name not in self._warningMessages:
            self._warningMessages[service_name] = []
        self._warningMessages[service_name].append(warning_info)

    def handle_information(self, information, autoscale_service):
        """
        Handles information.

        Logs information directly and accumulates messages to send via other messaging platforms later.

        Args:
            autoscale_service (AutoScaleService): The autoscale service this information is about
            information (str): Information message to handle.
        """
        # Log directly.
        self._logger.information(information, autoscale_service.get_service_log_level())

        # Accumulate messages to send later.
        service_name = autoscale_service.get_service_name()
        if service_name not in self._informationMessages:
            self._informationMessages[service_name] = []
        self._informationMessages[service_name].append(information)

    def handle_verbose_info(self, verbose_info, autoscale_service):
        """
        Handles verbose information.

        Logs information directly and accumulates messages to send via other messaging platforms later.

        Args:
            autoscale_service (AutoScaleService): The autoscale service this information is about
            verbose_info (str): Verbose info message to handle.
        """
        # Log directly.
        self._logger.verboseInfo(verbose_info, autoscale_service.get_service_log_level())

        # Accumulate messages to send later.
        service_name = autoscale_service.get_service_name()
        if service_name not in self._verboseMessages:
            self._verboseMessages[service_name] = []
        self._verboseMessages[service_name].append(verbose_info)

        

    def send_all_accumulated_messages(self):
        """
        Send all accumulated messages via all messaging platforms.
        """
        # TODO Implement message sending.