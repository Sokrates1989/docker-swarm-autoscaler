# Distributes information to logger, telegram, email based on settings.

# Definitions.
from valid_values import MessagingPlatforms

# Logger.
import logger as Logger

# Message Platforms.
import emailUtils as EmailUtils
import telegramUtils as TelegramUtils

class MessagePlatformHandler:

    def __init__(self, useDateStringUtils=True):
        """
        Constructor handling information distribution.
        """

        # Unknown service indicator.
        self._unknownServiceIndicator = "Global"

        # Accumulated messages to send later via message platforms.
        self._important_information_array = []
        self._error_array = []
        self._warning_array = []
        self._information_array = []
        self._verbose_information_array = []

        # Logger.
        self._logger = Logger.Logger(self, useDateStringUtils=useDateStringUtils)

        # Message Platforms.
        self._emailUtils = EmailUtils.EmailUtils(self, useDateStringUtils=useDateStringUtils)
        self._telegramUtils = TelegramUtils.TelegramUtils(self, useDateStringUtils=useDateStringUtils)

    
    
    def add_additional_recipients(self, autoscale_service):
        """
        Adds additional recipients to _messagePlatformHandler for the service.
        """
        # Email.
        for additional_important_email_recipient in autoscale_service.get_additional_email_recipients_important_msgs():
            self._emailUtils.add_additional_important_recipient(autoscale_service.get_service_name(), additional_important_email_recipient)
        for additional_information_email_recipient in autoscale_service.get_additional_email_recipients_information_msgs():
            self._emailUtils.add_additional_information_recipient(autoscale_service.get_service_name(), additional_information_email_recipient)
        for additional_verbose_email_recipient in autoscale_service.get_additional_email_recipients_verbose_msgs():
            self._emailUtils.add_additional_verbose_recipient(autoscale_service.get_service_name(), additional_verbose_email_recipient)

        # Telegram.
        for additional_important_telegram_recipient in autoscale_service.get_additional_telegram_recipients_important_msgs():
            self._telegramUtils.add_additional_important_recipient(autoscale_service.get_service_name(), additional_important_telegram_recipient)
        for additional_information_telegram_recipient in autoscale_service.get_additional_telegram_recipients_information_msgs():
            self._telegramUtils.add_additional_information_recipient(autoscale_service.get_service_name(), additional_information_telegram_recipient)
        for additional_verbose_telegram_recipient in autoscale_service.get_additional_telegram_recipients_verbose_msgs():
            self._telegramUtils.add_additional_verbose_recipient(autoscale_service.get_service_name(), additional_verbose_telegram_recipient)

    def handle_important_info(self, important_info, autoscale_service, scaling_metrics=[]):
        """
        Handles important information.

        Logs information directly and accumulates messages to send via other messaging platforms later.

        Args:
            important_info (str): Important info message to handle.
            autoscale_service (AutoScaleService): The autoscale service this information is about.
            scaling_metrics (Array of ScalingMetrics)
        """
        # Log directly.
        important_log_message=important_info
        # Add metric info to message.
        for scalingMetric in scaling_metrics:
            important_log_message += " - " + scalingMetric.as_string(MessagingPlatforms.LOGGING)
        self._logger.importantInfo(important_log_message, autoscale_service.get_service_log_level())

        ### Accumulate messages to send later ###
        important_info_dict = {
            "message": important_info,
            "autoscale_service": autoscale_service,
            "scaling_metrics": scaling_metrics
            }
        self._important_information_array.append(important_info_dict)

    def handle_error(self, error_info, autoscale_service=None):
        """
        Handles error information.

        Logs information directly and accumulates messages to send via other messaging platforms later.

        Args:
            autoscale_service (AutoScaleService): The autoscale service this information is about
            error_info (str): Error info message to handle.
        """
        # Log directly.
        if self._logger:
            if autoscale_service:
                self._logger.error(error_info, autoscale_service.get_service_log_level())
            else:
                self._logger.error(error_info)

        ### Accumulate messages to send later ###
        error_dict = {
            "message": error_info,
            "autoscale_service": autoscale_service
            }
        self._error_array.append(error_dict)
            

    def handle_warning(self, warning_info, autoscale_service=None, useDateStringUtils=True):
        """
        Handles warning information.

        Logs information directly and accumulates messages to send via other messaging platforms later.

        Args:
            autoscale_service (AutoScaleService): The autoscale service this information is about
            warning_info (str): Warning info message to handle.
        """
        # Log directly.
        if self._logger:
            if autoscale_service:
                self._logger.warning(warning_info, autoscale_service.get_service_log_level(), useDateStringUtils)
            else:
                self._logger.warning(warning_info, useDateStringUtils=useDateStringUtils)

        ### Accumulate messages to send later ###
        warning_dict = {
            "message": warning_info,
            "autoscale_service": autoscale_service
            }
        self._warning_array.append(warning_dict)
            

        


    def handle_information(self, information, autoscale_service=None):
        """
        Handles information.

        Logs information directly and accumulates messages to send via other messaging platforms later.

        Args:
            autoscale_service (AutoScaleService): The autoscale service this information is about
            information (str): Information message to handle.
        """
        # Log directly.
        if self._logger:
            if autoscale_service:
                self._logger.information(information, autoscale_service.get_service_log_level())
            else:
                self._logger.information(information)

        ### Accumulate messages to send later ###
        information_dict = {
            "message": information,
            "autoscale_service": autoscale_service
            }
        self._information_array.append(information_dict)
            

        

    def handle_verbose_info(self, verbose_info, autoscale_service=None):
        """
        Handles verbose information.

        Logs information directly and accumulates messages to send via other messaging platforms later.

        Args:
            autoscale_service (AutoScaleService): The autoscale service this information is about
            verbose_info (str): Verbose info message to handle.
        """
        # Log directly.
        if self._logger:
            if autoscale_service:
                self._logger.verboseInfo(verbose_info, autoscale_service.get_service_log_level())
            else:
                self._logger.verboseInfo(verbose_info)

        ### Accumulate messages to send later ###
        verbose_information_dict = {
            "message": verbose_info,
            "autoscale_service": autoscale_service
            }
        self._verbose_information_array.append(verbose_information_dict)
            
        
        

        

    def send_all_accumulated_messages(self):
        """
        Send all accumulated messages via all messaging platforms.
        """
        try:
            ### Handle accumulated messages ###
            for important_information_dict in self._important_information_array: 
                self._emailUtils.handle_important_info(important_information_dict["message"], important_information_dict["autoscale_service"], important_information_dict["scaling_metrics"])
                self._telegramUtils.handle_important_info(important_information_dict["message"], important_information_dict["autoscale_service"], important_information_dict["scaling_metrics"])
            
            for error_dict in self._error_array: 
                self._emailUtils.handle_error(error_dict["message"], error_dict["autoscale_service"])
                self._telegramUtils.handle_error(error_dict["message"], error_dict["autoscale_service"])

            for warning_dict in self._warning_array: 
                self._emailUtils.handle_warning(warning_dict["message"], warning_dict["autoscale_service"])
                self._telegramUtils.handle_warning(warning_dict["message"], warning_dict["autoscale_service"])

            for information_dict in self._information_array: 
                self._emailUtils.handle_information(information_dict["message"], information_dict["autoscale_service"])
                self._telegramUtils.handle_information(information_dict["message"], information_dict["autoscale_service"])

            for verbose_information_dict in self._verbose_information_array: 
                self._emailUtils.handle_verbose_info(verbose_information_dict["message"], verbose_information_dict["autoscale_service"])
                self._telegramUtils.handle_verbose_info(verbose_information_dict["message"], verbose_information_dict["autoscale_service"])

            # Finally send all messages.
            self._emailUtils.send_all_accumulated_messages()
            self._telegramUtils.send_all_accumulated_messages()

        except Exception as e:
            self.handle_error(f"MessagePlatformHandler.send_all_accumulated_messages(): Was not able to send messages via message platforms: <EMPHASIZE_STRING_START_TAG>{e}</EMPHASIZE_STRING_END_TAG>")
            pass # In case the instantiation of the message platforms themself causes errors.
        
        
        