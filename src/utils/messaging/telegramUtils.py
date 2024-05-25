# Sends Telegram status reports.

# Get environment variables.
import os

# Telegram bots.
import telebot

# Definitions.
from valid_values import MessagingPlatforms, LogLevel, MessageLevel

# Conversion.
import converterUtils

# MessagePlatformHandler.
import messagePlatformHandler as MessagePlatformHandler

class TelegramUtils:

    def __init__(self, messagePlatformHandler: MessagePlatformHandler, useDateStringUtils=True):
        """
        Constructor for utils class to send telegrams.
        
        Args:
            messagePlatformHandler (MessagePlatformHandler): In case of warnings: be able to send those via all available platforms.
            useDateString (bool): Whether to use the datestringUtils or not. Prevents an infinite loop from datestringUtils.
        """
        self._messagePlatformHandler = messagePlatformHandler

        # Unknown service indicator.
        self._unknownServiceIndicator = "Global"

        # Messages.
        self._messages_to_send = {}

        # Services.
        self._services = []

        # Default recipients based on each information level.
        self._default_recipients_important=[]
        self._default_recipients_information=[]
        self._default_recipients_verbose=[]

        # Additional recipients for each service.
        self._additional_recipients_important = {}
        self._additional_recipients_information = {}
        self._additional_recipients_verbose = {}

        # Prepare messages to log in case of warnings, verbose information and information.
        warning_messages = []
        verbose_info_messages = []
        info_messages = []
        
        # Are Telegram status messages enabled?
        self._telegram_enabled = os.getenv("TELEGRAM_ENABLED")
        if self._telegram_enabled.lower() == "true":
            info_messages.append(f"TelegramUtils: Telegram enabled as set in Environment Variable <EMPHASIZE_STRING_START_TAG>TELEGRAM_ENABLED</EMPHASIZE_STRING_END_TAG>. Value: <EMPHASIZE_STRING_START_TAG>{self._telegram_enabled}</EMPHASIZE_STRING_END_TAG>")
            self._telegram_enabled = True
        elif self._telegram_enabled.lower() == "false":
            info_messages.append(f"TelegramUtils: Telegram disabled as set in Environment Variable <EMPHASIZE_STRING_START_TAG>TELEGRAM_ENABLED</EMPHASIZE_STRING_END_TAG>. Value: <EMPHASIZE_STRING_START_TAG>{self._telegram_enabled}</EMPHASIZE_STRING_END_TAG>")
            self._telegram_enabled = False
        else:
            warning_messages.append(f"TelegramUtils: Environment Variable <EMPHASIZE_STRING_START_TAG>TELEGRAM_ENABLED</EMPHASIZE_STRING_END_TAG>: Invalid value: <EMPHASIZE_STRING_START_TAG>{self._telegram_enabled}</EMPHASIZE_STRING_END_TAG>. Defaulting to  <EMPHASIZE_STRING_START_TAG>False</EMPHASIZE_STRING_END_TAG>")
            self._telegram_enabled = False

        
        # Setup telegram sender and recipients.
        if self._telegram_enabled:

            # Sender Bot token.
            try:
                TELEGRAM_SENDER_BOT_TOKEN_FILE = os.getenv("TELEGRAM_SENDER_BOT_TOKEN_FILE")
                with open(f"{TELEGRAM_SENDER_BOT_TOKEN_FILE}", "r") as telegram_sender_bot_token_file:
                    self._sender_telegram_bot_token = telegram_sender_bot_token_file.read().strip()

                    # Log that bot token was taken from secret file, if it holds potentially valid information.
                    if self._sender_telegram_bot_token.lower() != "none":
                        verbose_info_messages.append(f"TelegramUtils: Telegram sender bot token taken from secret file.")
            except:
                pass
            finally:
                # In case of an error or the secret is not set.
                if not self._sender_telegram_bot_token or self._sender_telegram_bot_token.lower() == "none":
                    self._sender_telegram_bot_token = os.getenv('TELEGRAM_SENDER_BOT_TOKEN').strip().strip("\"")
                    warning_messages.append(f"TelegramUtils: Telegram sender bot token taken from .env. Please use secret instead.")
            if not self._sender_telegram_bot_token:
                warning_messages.append(f"TelegramUtils: No bot token for Telegram sender provided. Disabling Telegram status messages.")
                self._telegram_enabled = False

            # Initiate telegram bot from bot token.
            try:
                self._sender_telegram_bot = telebot.TeleBot(self._sender_telegram_bot_token, parse_mode="HTML")
            except Exception as e:
                warning_messages.append(f"TelegramUtils: Unable to initiate telegram bot. Disabling Telegram status messages. Error: <EMPHASIZE_STRING_START_TAG>{e}</EMPHASIZE_STRING_END_TAG>")
                self._telegram_enabled = False
            

            # Default Recipients.
            self._default_recipients_important, important_recipients_warnings = converterUtils.get_telegram_array_from_telegram_chats_list_string(os.getenv('TELEGRAM_RECIPIENTS_IMPORTANT').strip().strip("\""))
            self._default_recipients_information, information_recipients_warnings = converterUtils.get_telegram_array_from_telegram_chats_list_string(os.getenv('TELEGRAM_RECIPIENTS_INFORMATION').strip().strip("\""))
            self._default_recipients_verbose, verbose_recipients_warnings = converterUtils.get_telegram_array_from_telegram_chats_list_string(os.getenv('TELEGRAM_RECIPIENTS_VERBOSE').strip().strip("\""))

            ### Log recipients ###
            # Important message recipients.
            if self._default_recipients_important:
                default_recipients_string=", ".join([str(recipient).lower() for recipient in self._default_recipients_important])
                verbose_info_messages.append(f"TelegramUtils: Default telegram recipients for important messages: <EMPHASIZE_STRING_START_TAG>{default_recipients_string}</EMPHASIZE_STRING_END_TAG>")
            else:
                verbose_info_messages.append(f"TelegramUtils: No default telegram recipients for important messages.")
            # Information message recipients.
            if self._default_recipients_information:
                default_recipients_string=", ".join([str(recipient).lower() for recipient in self._default_recipients_information])
                verbose_info_messages.append(f"TelegramUtils: Default telegram recipients for information messages: <EMPHASIZE_STRING_START_TAG>{default_recipients_string}</EMPHASIZE_STRING_END_TAG>")
            else:
                verbose_info_messages.append(f"TelegramUtils: No default telegram recipients for information messages.")
            # Verbose info message recipients.
            if self._default_recipients_verbose:
                default_recipients_string=", ".join([str(recipient).lower() for recipient in self._default_recipients_verbose])
                verbose_info_messages.append(f"TelegramUtils: Default telegram recipients for verbose messages: <EMPHASIZE_STRING_START_TAG>{default_recipients_string}</EMPHASIZE_STRING_END_TAG>")
            else:
                verbose_info_messages.append(f"TelegramUtils: No default telegram recipients for verbose messages.")

            # Append warnings.
            for warning in important_recipients_warnings:
                warning_messages.append(f"TelegramUtils: Environment Variable <EMPHASIZE_STRING_START_TAG>TELEGRAM_RECIPIENTS_IMPORTANT</EMPHASIZE_STRING_END_TAG> <EMPHASIZE_STRING_START_TAG>{os.getenv('TELEGRAM_RECIPIENTS_IMPORTANT')}</EMPHASIZE_STRING_END_TAG> partially invalid: {warning}")
            for warning in information_recipients_warnings:
                warning_messages.append(f"TelegramUtils: Environment Variable <EMPHASIZE_STRING_START_TAG>TELEGRAM_RECIPIENTS_INFORMATION</EMPHASIZE_STRING_END_TAG> <EMPHASIZE_STRING_START_TAG>{os.getenv('TELEGRAM_RECIPIENTS_INFORMATION')}</EMPHASIZE_STRING_END_TAG> partially invalid: {warning}")
            for warning in verbose_recipients_warnings:
                warning_messages.append(f"TelegramUtils: Environment Variable <EMPHASIZE_STRING_START_TAG>TELEGRAM_RECIPIENTS_VERBOSE</EMPHASIZE_STRING_END_TAG> <EMPHASIZE_STRING_START_TAG>{os.getenv('TELEGRAM_RECIPIENTS_VERBOSE')}</EMPHASIZE_STRING_END_TAG> partially invalid: {warning}")

            

        ### Handle warnings, information and verbose info after finishing instantiation as far as possible ###
        # Warnings.
        for message in warning_messages:
            self._messagePlatformHandler.handle_warning(message)
        # Information.
        for message in info_messages:
            self._messagePlatformHandler.handle_information(message)
        # Verbose infos.
        for message in verbose_info_messages:
            self._messagePlatformHandler.handle_verbose_info(message)



    def add_additional_important_recipient(self, service_name, telegram_chat_id):
        """
        Adds an additional recipient for important messages for a service.
        
        Args:
            service_name (string): The service to append recipient to.
            telegram_chat_id (string): The telegram chat id to add to recipients for important messages.
        """
        if service_name not in self._additional_recipients_important:
            self._additional_recipients_important[service_name] = []
        self._add_service_name(service_name)
        self._additional_recipients_important[service_name].append(telegram_chat_id)
        # Log verbose info about recipient.
        self._messagePlatformHandler.handle_verbose_info(f"TelegramUtils: Service <EMPHASIZE_STRING_START_TAG>{service_name}</EMPHASIZE_STRING_END_TAG>: Additional <EMPHASIZE_STRING_START_TAG>important</EMPHASIZE_STRING_END_TAG> recipient: <EMPHASIZE_STRING_START_TAG>{telegram_chat_id}</EMPHASIZE_STRING_END_TAG>")


    def add_additional_information_recipient(self, service_name, telegram_chat_id):
        """
        Adds an additional recipient for information messages for a service.
        
        Args:
            service_name (string): The service to append recipient to.
            telegram_chat_id (string): The telegram chat id to add to recipients for information messages.
        """
        if service_name not in self._additional_recipients_information:
            self._additional_recipients_information[service_name] = []
        self._add_service_name(service_name)
        self._additional_recipients_information[service_name].append(telegram_chat_id)
        # Log verbose info about recipient.
        self._messagePlatformHandler.handle_verbose_info(f"TelegramUtils: Service <EMPHASIZE_STRING_START_TAG>{service_name}</EMPHASIZE_STRING_END_TAG>: Additional <EMPHASIZE_STRING_START_TAG>information</EMPHASIZE_STRING_END_TAG> recipient: <EMPHASIZE_STRING_START_TAG>{telegram_chat_id}</EMPHASIZE_STRING_END_TAG>")


    def add_additional_verbose_recipient(self, service_name, telegram_chat_id):
        """
        Adds an additional recipient for verbose messages for a service.
        
        Args:
            service_name (string): The service to append recipient to.
            telegram_chat_id (string): The telegram chat id to add to recipients for verbose messages.
        """
        if service_name not in self._additional_recipients_verbose:
            self._additional_recipients_verbose[service_name] = []
        self._add_service_name(service_name)
        self._additional_recipients_verbose[service_name].append(telegram_chat_id)
        # Log verbose info about recipient.
        self._messagePlatformHandler.handle_verbose_info(f"TelegramUtils: Service <EMPHASIZE_STRING_START_TAG>{service_name}</EMPHASIZE_STRING_END_TAG>: Additional <EMPHASIZE_STRING_START_TAG>verbose</EMPHASIZE_STRING_END_TAG> recipient: <EMPHASIZE_STRING_START_TAG>{telegram_chat_id}</EMPHASIZE_STRING_END_TAG>")


    def handle_important_info(self, important_info, autoscale_service, scaling_metrics=[]):
        """
        Handles important information.

        Accumulates messages to send later.

        Args:
            important_info (str): Important info message to handle.
            autoscale_service (AutoScaleService): The autoscale service this information is about.
            scaling_metrics (Array of ScalingMetrics)
        """
        ### Accumulate messages to send later ###
        service_name = autoscale_service.get_service_name()

        # Prepare message.
        important_telegram_message=important_info
        # Add metric info to message.
        for scalingMetric in scaling_metrics:
            important_telegram_message += "\n" + scalingMetric.as_string(MessagingPlatforms.TELEGRAM)
        # Add message to array.
        if service_name not in self._messages_to_send:
            self._messages_to_send[service_name] = {}
        if "important" not in self._messages_to_send[service_name]:
            self._messages_to_send[service_name]["important"] = []
        self._messages_to_send[service_name]["important"].append(important_telegram_message)

    def handle_error(self, error_info, autoscale_service=None):
        """
        Handles error information.

        Accumulates messages to send later.

        Args:
            autoscale_service (AutoScaleService): The autoscale service this information is about
            error_info (str): Error info message to handle.
        """
        # Get servicename.
        if autoscale_service:
            service_name = autoscale_service.get_service_name()
        else:
            service_name = self._unknownServiceIndicator

        # Accumulate messages to send later.
        if service_name not in self._messages_to_send:
            self._messages_to_send[service_name] = {}
        if "error" not in self._messages_to_send[service_name]:
            self._messages_to_send[service_name]["error"] = []
        self._add_service_name(service_name)
        self._messages_to_send[service_name]["error"].append(error_info)


    def handle_warning(self, warning_info, autoscale_service=None):
        """
        Handles warning information.

        Accumulates messages to send later.

        Args:
            autoscale_service (AutoScaleService): The autoscale service this information is about
            warning_info (str): Warning info message to handle.
        """
        # Get servicename.
        if autoscale_service:
            service_name = autoscale_service.get_service_name()
        else:
            service_name = self._unknownServiceIndicator

        # Accumulate messages to send later.
        if service_name not in self._messages_to_send:
            self._messages_to_send[service_name] = {}
        if "warning" not in self._messages_to_send[service_name]:
            self._messages_to_send[service_name]["warning"] = []
        self._add_service_name(service_name)
        self._messages_to_send[service_name]["warning"].append(warning_info)



    def handle_information(self, information, autoscale_service=None):
        """
        Handles information.

        Accumulates messages to send later.

        Args:
            autoscale_service (AutoScaleService): The autoscale service this information is about
            information (str): Information message to handle.
        """
        # Get servicename.
        if autoscale_service:
            service_name = autoscale_service.get_service_name()
        else:
            service_name = self._unknownServiceIndicator

        # Accumulate messages to send later.
        if service_name not in self._messages_to_send:
            self._messages_to_send[service_name] = {}
        if "information" not in self._messages_to_send[service_name]:
            self._messages_to_send[service_name]["information"] = []
        self._add_service_name(service_name)
        self._messages_to_send[service_name]["information"].append(information)


    def handle_verbose_info(self, verbose_info, autoscale_service=None):
        """
        Handles verbose information.

        Accumulates messages to send later.

        Args:
            autoscale_service (AutoScaleService): The autoscale service this information is about
            verbose_info (str): Verbose info message to handle.
        """
        # Get servicename.
        if autoscale_service:
            service_name = autoscale_service.get_service_name()
        else:
            service_name = self._unknownServiceIndicator
            
        # Accumulate messages to send later.
        if service_name not in self._messages_to_send:
            self._messages_to_send[service_name] = {}
        if "verbose" not in self._messages_to_send[service_name]:
            self._messages_to_send[service_name]["verbose"] = []
        self._add_service_name(service_name)
        self._messages_to_send[service_name]["verbose"].append(verbose_info)


    def _send_telegram_message(self, recipient_telegram, subject, message):
        """
        Send telegram message to user.

        All messages MUST be sent via this method, to avoid Bad Request: message is too long.

        Args:
            recipient_telegram (str): Valid telegram chat id to send telegram message to.
            subject (str): The topic of the message.
            message (str): The message to be sent to the user.
        """
        # Make subject part of the message.
        message = "<b>" + subject + "</b>" + message

        # Replace emphasize String Tags.
        message=message.replace("<EMPHASIZE_STRING_START_TAG>", "<b>")
        message=message.replace("</EMPHASIZE_STRING_END_TAG>", "</b>")

        # Does message have to be split?
        if len(message) > 4096:

            individualMessagesToSend = self.splitLongTextIntoWorkingMessages(message)
            for individualMessageToSend in individualMessagesToSend:
                try:
                    self._sender_telegram_bot.send_message(recipient_telegram, individualMessageToSend)
                except Exception as e:
                    self._messagePlatformHandler.handle_error(f"TelegramUtils: Could not send telegram message <EMPHASIZE_STRING_START_TAG>{individualMessageToSend}</EMPHASIZE_STRING_END_TAG> to recipient <EMPHASIZE_STRING_START_TAG>{recipient_telegram}</EMPHASIZE_STRING_END_TAG>. Error message: <EMPHASIZE_STRING_START_TAG>{e}</EMPHASIZE_STRING_END_TAG>")

        else:
            # Message does not have to be split.
            try:
                self._sender_telegram_bot.send_message(recipient_telegram, message)
            except Exception as e:
                self._messagePlatformHandler.handle_error(f"TelegramUtils: Could not send telegram message <EMPHASIZE_STRING_START_TAG>{message}</EMPHASIZE_STRING_END_TAG> to recipient <EMPHASIZE_STRING_START_TAG>{recipient_telegram}</EMPHASIZE_STRING_END_TAG>. Error message: <EMPHASIZE_STRING_START_TAG>{e}</EMPHASIZE_STRING_END_TAG>")



    def _add_service_name(self, service_name):
        """
        Add a service name to the list of services if it's not already present.

        Args:
            service_name (str): The name of the service to add.

        Returns:
            None
        """
        if service_name not in self._services:
            self._services.append(service_name)

    
    # Recipient["recipient_name"]["service_name"] = most_information_level
    def _get_all_recipients(self):
        recipients = {}

        # Adding default recipients.
        for recipient_telegram in self._default_recipients_verbose:
            if recipient_telegram not in recipients:
                recipients[recipient_telegram] = {service: LogLevel.VERBOSE for service in self._services}

        for recipient_telegram in self._default_recipients_information:
            if recipient_telegram not in recipients:
                recipients[recipient_telegram] = {service: LogLevel.INFO for service in self._services}

        for recipient_telegram in self._default_recipients_important:
            if recipient_telegram not in recipients:
                recipients[recipient_telegram] = {service: LogLevel.IMPORTANT_ONLY for service in self._services}

        # Adding additional recipients and overrides.
        for service_name in self._additional_recipients_important:
            for recipient_telegram in self._additional_recipients_important[service_name]:
                if recipient_telegram not in recipients:
                    recipients[recipient_telegram] = {service_name: LogLevel.IMPORTANT_ONLY}
                else:
                    if service_name not in recipients[recipient_telegram]:
                        recipients[recipient_telegram][service_name] = LogLevel.IMPORTANT_ONLY
                        
        for service_name in self._additional_recipients_information:
            for recipient_telegram in self._additional_recipients_information[service_name]:
                if recipient_telegram not in recipients:
                    recipients[recipient_telegram] = {service_name: LogLevel.INFO}
                else:
                    if service_name not in recipients[recipient_telegram] or recipients[recipient_telegram][service_name] == LogLevel.IMPORTANT_ONLY:
                        recipients[recipient_telegram][service_name] = LogLevel.INFO         
                        
        for service_name in self._additional_recipients_verbose:
            for recipient_telegram in self._additional_recipients_verbose[service_name]:
                if recipient_telegram not in recipients:
                    recipients[recipient_telegram] = {service_name: LogLevel.VERBOSE}
                else:
                    recipients[recipient_telegram][service_name] = LogLevel.VERBOSE
                        
        return recipients
    
    def send_all_accumulated_messages(self):
        """
        Send all accumulated messages via telegram to respective recipients.
        """
        if not self._telegram_enabled:
            return

        # Prepare a message for every recipient.
        recipients = self._get_all_recipients()
        for recipient_chat_id in recipients:
            send_message = False  # Only send message, if there is any message for any service.
            msg_to_send = ""
            subject = "Autoscaler info: "
            highest_message_level = MessageLevel.VERBOSE

            # Function to process messages for a given service_name.
            def process_service_messages(service_name):
                nonlocal send_message, msg_to_send, subject, highest_message_level

                service_message = ""
                service_message_levels = []

                # Important messages
                if "important" in self._messages_to_send.get(service_name, {}):
                    service_message += f"\n<u>Important</u>\n"
                    for message in self._messages_to_send[service_name]["important"]:
                        service_message += f"‼️ {message}\n"
                    highest_message_level = self._determine_highest_message_level(highest_message_level, MessageLevel.IMPORTANT)
                    service_message_levels.append(MessageLevel.IMPORTANT)

                # Error messages
                if "error" in self._messages_to_send.get(service_name, {}):
                    service_message += f"\n<u>Errors</u>\n"
                    for message in self._messages_to_send[service_name]["error"]:
                        service_message += f"🛑 {message}\n"
                    highest_message_level = self._determine_highest_message_level(highest_message_level, MessageLevel.ERROR)
                    service_message_levels.append(MessageLevel.ERROR)

                # Warning messages
                if "warning" in self._messages_to_send.get(service_name, {}):
                    service_message += f"\n<u>Warnings</u>\n"
                    for message in self._messages_to_send[service_name]["warning"]:
                        service_message += f"⚠️ {message}\n"
                    highest_message_level = self._determine_highest_message_level(highest_message_level, MessageLevel.WARNING)
                    service_message_levels.append(MessageLevel.WARNING)

                # Information messages (if recipient is subscribed)
                if recipients[recipient_chat_id][service_name] in [LogLevel.VERBOSE, LogLevel.INFO]:
                    if "information" in self._messages_to_send.get(service_name, {}):
                        service_message += f"\n<u>Information</u>\n"
                        for message in self._messages_to_send[service_name]["information"]:
                            service_message += f"ℹ {message}\n"
                        highest_message_level = self._determine_highest_message_level(highest_message_level, MessageLevel.INFO)
                        service_message_levels.append(MessageLevel.INFO)

                # Verbose messages (if recipient is subscribed)
                if recipients[recipient_chat_id][service_name] == LogLevel.VERBOSE:
                    if "verbose" in self._messages_to_send.get(service_name, {}):
                        service_message += f"\n<u>Verbose</u>\n"
                        for message in self._messages_to_send[service_name]["verbose"]:
                            service_message += f"🔍 {message}\n"
                        highest_message_level = self._determine_highest_message_level(highest_message_level, MessageLevel.VERBOSE)
                        service_message_levels.append(MessageLevel.VERBOSE)

                # Append messages to final message if any
                if service_message:
                    send_message = True
                    subject += service_name + ", "
                    service_log_level_string = ", ".join([level.level.lower() for level in service_message_levels])
                    service_log_level_string = f" ({service_log_level_string})"
                    msg_to_send += f"\n\n<code>Service {service_name}{service_log_level_string}</code>\n" if service_name != self._unknownServiceIndicator else f"\n\n<code>{service_name}{service_log_level_string}</code>\n"
                    msg_to_send += service_message + "\n"

            # First process the self._unknownServiceIndicator service if subscribed.
            if self._unknownServiceIndicator in recipients[recipient_chat_id]:
                process_service_messages(self._unknownServiceIndicator)

            # Process other services.
            for service_name in recipients[recipient_chat_id]:
                if service_name != self._unknownServiceIndicator:
                    process_service_messages(service_name)

            # Only send message if there is any message
            if send_message:
                subject = subject.rstrip(", ")

                # Reflect log level in the subject
                if highest_message_level == MessageLevel.IMPORTANT:
                    subject = subject.replace("Autoscaler info: ", "‼️ <u>AUTOSCALER IMPORTANT INFO</u>: ")
                elif highest_message_level == MessageLevel.ERROR:
                    subject = subject.replace("Autoscaler info: ", "🛑 <u>Autoscaler ERROR</u>: ")
                elif highest_message_level == MessageLevel.WARNING:
                    subject = subject.replace("Autoscaler info: ", "⚠️ <u>Autoscaler WARNING</u>: ")
                elif highest_message_level == MessageLevel.INFO:
                    subject = subject.replace("Autoscaler info: ", "🆗ℹ Autoscaler info: ")
                elif highest_message_level == MessageLevel.VERBOSE:
                    subject = subject.replace("Autoscaler info: ", "🔍 Autoscaler verbose info: ")

                # Send the telegram message
                self._send_telegram_message(recipient_chat_id, subject, msg_to_send)

        

    def _determine_highest_message_level(self, currently_highest_message_level: MessageLevel, potential_new_message_level: MessageLevel):
        """
        Determine the highest log level based on the current highest level and a potential new level.

        Args:
            currently_highest_message_level (MessageLevel): The current highest log level.
            potential_new_log_level (MessageLevel): The potential new log level to be compared.

        Returns:
            MessageLevel: The determined highest log level after comparison.
        """
        # If the current highest log level is IMPORTANT, it remains IMPORTANT since it's the most important level.
        if currently_highest_message_level == MessageLevel.IMPORTANT:
            return MessageLevel.IMPORTANT
        
        # If the current highest log level is ERROR.
        elif currently_highest_message_level == MessageLevel.ERROR:
            if potential_new_message_level == MessageLevel.IMPORTANT:
                return MessageLevel.IMPORTANT
            else:
                return currently_highest_message_level
        
        # If the current highest log level is WARNING.
        elif currently_highest_message_level == MessageLevel.WARNING:
            if potential_new_message_level == MessageLevel.IMPORTANT:
                return MessageLevel.IMPORTANT
            elif potential_new_message_level == MessageLevel.ERROR:
                return MessageLevel.ERROR
            else:
                return currently_highest_message_level
        
        # If the current highest log level is INFO.
        elif currently_highest_message_level == MessageLevel.INFO:
            if potential_new_message_level == MessageLevel.IMPORTANT:
                return MessageLevel.IMPORTANT
            elif potential_new_message_level == MessageLevel.ERROR:
                return MessageLevel.ERROR
            elif potential_new_message_level == MessageLevel.WARNING:
                return MessageLevel.WARNING
            else:
                return currently_highest_message_level
        
        # If the current highest log level is VERBOSE, we consider the new potential log level.
        elif currently_highest_message_level == MessageLevel.VERBOSE:
            return potential_new_message_level
        
        # If none of the above conditions are met, we return the current highest log level.
        else:
            return currently_highest_message_level



    def splitLongTextIntoWorkingMessages(self, messageToSplit: str):
        """
        Splits long texts into sendable individual telegram messages.

        Args:
            messageToSplit (str): The message to be split.

        Returns:
            Array of strings: An array of sendable telegram messages.
        """
        individualMessagesToSend = []
        if len(messageToSplit) < 4096:
            individualMessagesToSend.append(messageToSplit)
            return individualMessagesToSend
        else:
            # Split message by service.
            if messageToSplit.count("<code>") > 1: 

                groupedItems = messageToSplit.split("<code>")
                currentIndividualMessage = ""
                potentialIndividualMessage = ""

                # Create sendable, just small enough messages.
                for index, item in enumerate(groupedItems):

                    # Only add tag back if it is not the first item.
                    if index != 0:
                        item = "<code>" + item
                        
                    # Ensure item itself is not too big.
                    if len(item) > 4096:
                        # Create sendable, just small enough messages after splitting message further.
                        subitems = self.splitLongTextIntoWorkingMessages(item)
                        for subitem in subitems:
                            potentialIndividualMessage += subitem
                            if len(potentialIndividualMessage) < 4096:
                                currentIndividualMessage = potentialIndividualMessage
                            else:
                                individualMessagesToSend.append(currentIndividualMessage)
                                currentIndividualMessage = ""
                                potentialIndividualMessage = subitem
                    else:
                        potentialIndividualMessage += item
                        if len(potentialIndividualMessage) < 4096:
                            currentIndividualMessage = potentialIndividualMessage
                        else:
                            individualMessagesToSend.append(currentIndividualMessage)
                            currentIndividualMessage = ""
                            potentialIndividualMessage = item

                # Add last item.
                if potentialIndividualMessage:
                    individualMessagesToSend.append(potentialIndividualMessage)

            # Split message by messagelevel messages.
            elif messageToSplit.count("<u>") > 1: 

                groupedItems = messageToSplit.split("<u>")
                currentIndividualMessage = ""
                potentialIndividualMessage = ""

                # Create sendable, just small enough messages.
                for index, item in enumerate(groupedItems):

                    # Only add tag back if it is not the first item.
                    if index != 0:
                        item = "<u>" + item

                    # Ensure item itself is not too big.
                    if len(item) > 4096:
                        # Create sendable, just small enough messages after splitting message further.
                        subitems = self.splitLongTextIntoWorkingMessages(item)
                        for subitem in subitems:
                            potentialIndividualMessage += subitem
                            if len(potentialIndividualMessage) < 4096:
                                currentIndividualMessage = potentialIndividualMessage
                            else:
                                individualMessagesToSend.append(currentIndividualMessage)
                                currentIndividualMessage = ""
                                potentialIndividualMessage = subitem
                    else:
                        potentialIndividualMessage += item
                        if len(potentialIndividualMessage) < 4096:
                            currentIndividualMessage = potentialIndividualMessage
                        else:
                            individualMessagesToSend.append(currentIndividualMessage)
                            currentIndividualMessage = ""
                            potentialIndividualMessage = item

                # Add last item.
                if potentialIndividualMessage:
                    individualMessagesToSend.append(potentialIndividualMessage)

            else:
                # Split Message by new line breaks.
                groupedItems = messageToSplit.split("\n")
                currentIndividualMessage = ""
                potentialIndividualMessage = ""

                # Create sendable, just small enough messages.
                for item in groupedItems:
                    potentialIndividualMessage += "\n" + item
                    if len(potentialIndividualMessage) < 4096:
                        currentIndividualMessage = potentialIndividualMessage
                    else:
                        individualMessagesToSend.append(currentIndividualMessage)
                        currentIndividualMessage = ""
                        potentialIndividualMessage = "\n" + item

                # Add last item.
                if potentialIndividualMessage:
                    individualMessagesToSend.append(potentialIndividualMessage)

            # Return messages.
            return individualMessagesToSend
