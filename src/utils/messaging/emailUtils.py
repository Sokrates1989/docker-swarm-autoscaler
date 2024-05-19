# Sends emails.

# Email specific imports.
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Get environment variables.
import os

# Definitions.
from valid_values import MessagingPlatforms, LogLevel, MessageLevel, VALID_SMTP_PORTS

# Conversion.
import converterUtils

# MessagePlatformHandler.
import messagePlatformHandler as MessagePlatformHandler

class EmailUtils:

    def __init__(self, messagePlatformHandler: MessagePlatformHandler, useDateStringUtils=True):
        """
        Constructor for utils class to send emails.
        
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
        
        # Are E-Mail status messages enabled?
        self._email_enabled = os.getenv("EMAIL_ENABLED")
        if self._email_enabled.lower() == "true":
            info_messages.append(f"EmailUtils: Email enabled as set in Environment Variable <EMPHASIZE_STRING_START_TAG>EMAIL_ENABLED</EMPHASIZE_STRING_END_TAG>. Value: <EMPHASIZE_STRING_START_TAG>{self._email_enabled}</EMPHASIZE_STRING_END_TAG>")
            self._email_enabled = True
        elif self._email_enabled.lower() == "false":
            info_messages.append(f"EmailUtils: Email disabled as set in Environment Variable <EMPHASIZE_STRING_START_TAG>EMAIL_ENABLED</EMPHASIZE_STRING_END_TAG>. Value: <EMPHASIZE_STRING_START_TAG>{self._email_enabled}</EMPHASIZE_STRING_END_TAG>")
            self._email_enabled = False
        else:
            warning_messages.append(f"EmailUtils: Environment Variable <EMPHASIZE_STRING_START_TAG>EMAIL_ENABLED</EMPHASIZE_STRING_END_TAG>: Invalid value: <EMPHASIZE_STRING_START_TAG>{self._email_enabled}</EMPHASIZE_STRING_END_TAG>. Defaulting to  <EMPHASIZE_STRING_START_TAG>False</EMPHASIZE_STRING_END_TAG>")
            self._email_enabled = False

        
        # Setup email sender and recipients.
        if self._email_enabled:
            self._sender={}

            # Sender User.
            self._sender["user"] = os.getenv('EMAIL_SENDER_USER').strip().strip("\"")
            if not "user" in self._sender:
                warning_messages.append(f"EmailUtils: No user for Email sender provided. Disabling Email status messages.")
                self._email_enabled = False

            # Sender Password.
            try:
                EMAIL_SENDER_PASSWORD_FILE = os.getenv("EMAIL_SENDER_PASSWORD_FILE")
                with open(f"{EMAIL_SENDER_PASSWORD_FILE}", "r") as email_sender_password_file:
                    self._sender["password"] = email_sender_password_file.read().strip()
                    verbose_info_messages.append(f"EmailUtils: Email sender password taken from secret file.")
            except:
                pass
            finally:
                # If there is no SECRET_FILE.
                if not "password" in self._sender:
                    self._sender["password"] = os.getenv('EMAIL_SENDER_PASSWORD').strip().strip("\"")
                    verbose_info_messages.append(f"EmailUtils: Email sender password taken from .env.")
            if not "password" in self._sender or not self._sender["password"]:
                warning_messages.append(f"EmailUtils: No Password for Email sender provided. Disabling Email status messages.")
                self._email_enabled = False


            # Sender Host.
            self._sender["host"] = os.getenv('EMAIL_SENDER_HOST').strip().strip("\"")
            if not "host" in self._sender:
                warning_messages.append(f"EmailUtils: No host for Email sender provided. Disabling Email status messages.")
                self._email_enabled = False


            # Sender Port.
            self._sender["port"] = os.getenv('EMAIL_SENDER_PORT').strip().strip("\"")
            if "port" in self._sender:
                valid_ports_string = "Valid ports: %s" % (", ".join(map(str, VALID_SMTP_PORTS)))
                if self._sender["port"].isnumeric():
                    self._sender["port"] = int(self._sender["port"])
                    if int(self._sender["port"]) not in VALID_SMTP_PORTS:
                        warning_messages.append(f"EmailUtils: Port <EMPHASIZE_STRING_START_TAG>{self._sender['port']}</EMPHASIZE_STRING_END_TAG> for Email sender is not valid. {valid_ports_string}. Disabling Email status messages.")
                        self._email_enabled = False
                else:
                    warning_messages.append(f"EmailUtils: Port <EMPHASIZE_STRING_START_TAG>{self._sender['port']}</EMPHASIZE_STRING_END_TAG> for Email sender is not numeric. {valid_ports_string}. Disabling Email status messages.")
                    self._email_enabled = False
            else:
                warning_messages.append(f"EmailUtils: No port for Email sender provided. Disabling Email status messages.")
                self._email_enabled = False

            # Default Recipients.
            self._default_recipients_important, important_recipients_warnings = converterUtils.get_email_array_from_emails_list_string(os.getenv('EMAIL_RECIPIENTS_IMPORTANT').strip().strip("\""))
            self._default_recipients_information, information_recipients_warnings = converterUtils.get_email_array_from_emails_list_string(os.getenv('EMAIL_RECIPIENTS_INFORMATION').strip().strip("\""))
            self._default_recipients_verbose, verbose_recipients_warnings = converterUtils.get_email_array_from_emails_list_string(os.getenv('EMAIL_RECIPIENTS_VERBOSE').strip().strip("\""))

            ### Log recipients ###
            # Important message recipients.
            if self._default_recipients_important:
                default_recipients_string=", ".join([str(recipient).lower() for recipient in self._default_recipients_important])
                verbose_info_messages.append(f"EmailUtils: Default email recipients for important messages: <EMPHASIZE_STRING_START_TAG>{default_recipients_string}</EMPHASIZE_STRING_END_TAG>")
            else:
                verbose_info_messages.append(f"EmailUtils: No default email recipients for important messages.")
            # Information message recipients.
            if self._default_recipients_information:
                default_recipients_string=", ".join([str(recipient).lower() for recipient in self._default_recipients_information])
                verbose_info_messages.append(f"EmailUtils: Default email recipients for information messages: <EMPHASIZE_STRING_START_TAG>{default_recipients_string}</EMPHASIZE_STRING_END_TAG>")
            else:
                verbose_info_messages.append(f"EmailUtils: No default email recipients for information messages.")
            # Verbose info message recipients.
            if self._default_recipients_verbose:
                default_recipients_string=", ".join([str(recipient).lower() for recipient in self._default_recipients_verbose])
                verbose_info_messages.append(f"EmailUtils: Default email recipients for verbose messages: <EMPHASIZE_STRING_START_TAG>{default_recipients_string}</EMPHASIZE_STRING_END_TAG>")
            else:
                verbose_info_messages.append(f"EmailUtils: No default email recipients for verbose messages.")

            # Append warnings.
            for warning in important_recipients_warnings:
                warning_messages.append(f"Environment Variable <EMPHASIZE_STRING_START_TAG>EMAIL_RECIPIENTS_IMPORTANT</EMPHASIZE_STRING_END_TAG> <EMPHASIZE_STRING_START_TAG>{os.getenv('EMAIL_RECIPIENTS_IMPORTANT')}</EMPHASIZE_STRING_END_TAG> partially invalid: {warning}")
            for warning in information_recipients_warnings:
                warning_messages.append(f"Environment Variable <EMPHASIZE_STRING_START_TAG>EMAIL_RECIPIENTS_INFORMATION</EMPHASIZE_STRING_END_TAG> <EMPHASIZE_STRING_START_TAG>{os.getenv('EMAIL_RECIPIENTS_INFORMATION')}</EMPHASIZE_STRING_END_TAG> partially invalid: {warning}")
            for warning in verbose_recipients_warnings:
                warning_messages.append(f"Environment Variable <EMPHASIZE_STRING_START_TAG>EMAIL_RECIPIENTS_VERBOSE</EMPHASIZE_STRING_END_TAG> <EMPHASIZE_STRING_START_TAG>{os.getenv('EMAIL_RECIPIENTS_VERBOSE')}</EMPHASIZE_STRING_END_TAG> partially invalid: {warning}")

            
        # Test sender login.
        if self._email_enabled:
            smpt_login_successful=self._test_smtp_login(self._sender)
            if smpt_login_successful != True:
                warning_messages.append(f"EmailUtils smtp login test failed: {smpt_login_successful}. Disabling Email status messages.")
                self._email_enabled = False

                

        ### Handle warnings, information and verbose info after finishing instantiation as far as possible ###
        # Warnings.
        for message in warning_messages:
            self.handle_warning(message) # Since instantiation itself is not fully complete.
            self._messagePlatformHandler.handle_warning(message)
        # Information.
        for message in info_messages:
            self.handle_information(message) # Since instantiation itself is not fully complete.
            self._messagePlatformHandler.handle_information(message)
        # Verbose infos.
        for message in verbose_info_messages:
            self.handle_verbose_info(message) # Since instantiation itself is not fully complete.
            self._messagePlatformHandler.handle_verbose_info(message)



    def add_additional_important_recipient(self, service_name, email_address):
        """
        Adds an additional recipient for important messages for a service.
        
        Args:
            service_name (string): The service to append recipient to.
            email_address (string): The email address to add to recipients for important messages.
        """
        if service_name not in self._additional_recipients_important:
            self._additional_recipients_important[service_name] = []
        self._add_service_name(service_name)
        self._additional_recipients_important[service_name].append(email_address)
        # Log verbose info about recipient.
        self._messagePlatformHandler.handle_verbose_info(f"EmailUtils: Service <EMPHASIZE_STRING_START_TAG>{service_name}</EMPHASIZE_STRING_END_TAG>: Additional <EMPHASIZE_STRING_START_TAG>important</EMPHASIZE_STRING_END_TAG> recipient: <EMPHASIZE_STRING_START_TAG>{email_address}</EMPHASIZE_STRING_END_TAG>")


    def add_additional_information_recipient(self, service_name, email_address):
        """
        Adds an additional recipient for information messages for a service.
        
        Args:
            service_name (string): The service to append recipient to.
            email_address (string): The email address to add to recipients for information messages.
        """
        if service_name not in self._additional_recipients_information:
            self._additional_recipients_information[service_name] = []
        self._add_service_name(service_name)
        self._additional_recipients_information[service_name].append(email_address)
        # Log verbose info about recipient.
        self._messagePlatformHandler.handle_verbose_info(f"EmailUtils: Service <EMPHASIZE_STRING_START_TAG>{service_name}</EMPHASIZE_STRING_END_TAG>: Additional <EMPHASIZE_STRING_START_TAG>information</EMPHASIZE_STRING_END_TAG> recipient: <EMPHASIZE_STRING_START_TAG>{email_address}</EMPHASIZE_STRING_END_TAG>")


    def add_additional_verbose_recipient(self, service_name, email_address):
        """
        Adds an additional recipient for verbose messages for a service.
        
        Args:
            service_name (string): The service to append recipient to.
            email_address (string): The email address to add to recipients for verbose messages.
        """
        if service_name not in self._additional_recipients_verbose:
            self._additional_recipients_verbose[service_name] = []
        self._add_service_name(service_name)
        self._additional_recipients_verbose[service_name].append(email_address)
        # Log verbose info about recipient.
        self._messagePlatformHandler.handle_verbose_info(f"EmailUtils: Service <EMPHASIZE_STRING_START_TAG>{service_name}</EMPHASIZE_STRING_END_TAG>: Additional <EMPHASIZE_STRING_START_TAG>verbose</EMPHASIZE_STRING_END_TAG> recipient: <EMPHASIZE_STRING_START_TAG>{email_address}</EMPHASIZE_STRING_END_TAG>")


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
        important_mail_message=important_info
        # Add metric info to message.
        for scalingMetric in scaling_metrics:
            important_mail_message += "\n" + scalingMetric.as_string(MessagingPlatforms.EMAIL)
        # Add message to array.
        if service_name not in self._messages_to_send:
            self._messages_to_send[service_name] = {}
        if "important" not in self._messages_to_send[service_name]:
            self._messages_to_send[service_name]["important"] = []
        self._messages_to_send[service_name]["important"].append(important_mail_message)

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


    def _test_smtp_login(self, sender):
        try:
            if (sender["port"]) not in VALID_SMTP_PORTS: 
                raise Exception("Port %s not one of %s" % (sender["port"], VALID_SMTP_PORTS))

            if sender["port"] in (465,):
                server = smtplib.SMTP_SSL(sender["host"], sender["port"])
            else:
                server = smtplib.SMTP(sender["host"], sender["port"])

            # Optional.
            server.ehlo()

            if sender["port"] in (587,): 
                server.starttls()
                
            server.login(sender["user"], sender["password"])
            server.quit()
            return True
        except Exception as e:
            return f"SMTP login failed. Error: <EMPHASIZE_STRING_START_TAG>{e}</EMPHASIZE_STRING_END_TAG>"


    def _send_email(self, sender, recipient_email, subject, message):

        # Set up the MIME.
        msg = MIMEMultipart()
        msg['From'] = sender["user"]
        msg['To'] = recipient_email
        msg['Subject'] = subject

        try:
            if sender["port"] not in VALID_SMTP_PORTS: 
                raise Exception("Port %s not one of %s" % (sender["port"], VALID_SMTP_PORTS))

            if sender["port"] in (465,):
                server = smtplib.SMTP_SSL(sender["host"], sender["port"])
            else:
                server = smtplib.SMTP(sender["host"], sender["port"])

            # Optional.
            server.ehlo()

            if sender["port"] in (587,): 
                server.starttls()

        except Exception as e:
            return e

        server.login(sender["user"], sender["password"])

        # Make message html.
        message = "<html><body>" + message + "</html></body>"

        # Replace new linnes \n with <br/> to make them work with html.
        message = message.replace("\n", "<br/>")

        # Replace emphasize String Tags.
        message=message.replace("<EMPHASIZE_STRING_START_TAG>", "<b>")
        message=message.replace("</EMPHASIZE_STRING_END_TAG>", "</b>")

        # Attach message.
        msg.attach(MIMEText(message, 'html'))

        # Send the email.
        server.sendmail(sender["user"], recipient_email, msg.as_string())

        # Close the connection.
        server.quit()


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
        for recipient_email in self._default_recipients_verbose:
            if recipient_email not in recipients:
                recipients[recipient_email] = {service: LogLevel.VERBOSE for service in self._services}

        for recipient_email in self._default_recipients_information:
            if recipient_email not in recipients:
                recipients[recipient_email] = {service: LogLevel.INFO for service in self._services}

        for recipient_email in self._default_recipients_important:
            if recipient_email not in recipients:
                recipients[recipient_email] = {service: LogLevel.IMPORTANT_ONLY for service in self._services}

        # Adding additional recipients and overrides.
        for service_name in self._additional_recipients_important:
            for recipient_email in self._additional_recipients_important[service_name]:
                if recipient_email not in recipients:
                    recipients[recipient_email] = {service_name: LogLevel.IMPORTANT_ONLY}
                else:
                    if service_name not in recipients[recipient_email]:
                        recipients[recipient_email][service_name] = LogLevel.IMPORTANT_ONLY
                        
        for service_name in self._additional_recipients_information:
            for recipient_email in self._additional_recipients_information[service_name]:
                if recipient_email not in recipients:
                    recipients[recipient_email] = {service_name: LogLevel.INFO}
                else:
                    if service_name not in recipients[recipient_email] or recipients[recipient_email][service_name] == LogLevel.IMPORTANT_ONLY:
                        recipients[recipient_email][service_name] = LogLevel.INFO         
                        
        for service_name in self._additional_recipients_verbose:
            for recipient_email in self._additional_recipients_verbose[service_name]:
                if recipient_email not in recipients:
                    recipients[recipient_email] = {service_name: LogLevel.VERBOSE}
                else:
                    recipients[recipient_email][service_name] = LogLevel.VERBOSE
                        
        return recipients
    

    def send_all_accumulated_messages(self):
        """
        Send all accumulated messages via email to respective recipients.
        """
        if not self._email_enabled:
            return

        # Prepare a message for every recipient.
        recipients = self._get_all_recipients()
        for recipient_mail in recipients:
            send_mail = False # Only send mail, if there is any message for any service.
            msg_to_send = ""
            subject = "Autoscaler info: "
            highest_message_level = MessageLevel.VERBOSE
            # What services is the recipient subscribed to?
            for service_name in recipients[recipient_mail]:

                # Determine if there is any message of the service for the recipient.
                service_message = ""
                service_message_levels=[]

                # Important messages.
                if "important" in self._messages_to_send[service_name]:
                    service_message += f"<p><u>Important</u><br/>"
                    # Add each message from the array.
                    for message in self._messages_to_send[service_name]["important"]:
                        service_message += f"- {message}\n"
                    service_message += "</p>"
                    highest_message_level = self._determine_highest_message_level(highest_message_level, MessageLevel.IMPORTANT)
                    service_message_levels.append(MessageLevel.IMPORTANT)

                # Error messages.
                if "error" in self._messages_to_send[service_name]:
                    service_message += f"<p><u>Errors</u><br/>"
                    # Add each message from the array.
                    for message in self._messages_to_send[service_name]["error"]:
                        service_message += f"- {message}\n"
                    service_message += "</p>"
                    highest_message_level = self._determine_highest_message_level(highest_message_level, MessageLevel.ERROR)
                    service_message_levels.append(MessageLevel.ERROR)

                # Warning messages.
                if "warning" in self._messages_to_send[service_name]:
                    service_message += f"<p><u>Warnings</u><br/>"
                    # Add each message from the array.
                    for message in self._messages_to_send[service_name]["warning"]:
                        service_message += f"- {message}\n"
                    service_message += "</p>"
                    highest_message_level = self._determine_highest_message_level(highest_message_level, MessageLevel.WARNING)
                    service_message_levels.append(MessageLevel.WARNING)

                
                # Is recipient subscribed for informataion level?
                if recipients[recipient_mail][service_name] == LogLevel.VERBOSE or recipients[recipient_mail][service_name] == LogLevel.INFO:

                    # Information messages.
                    if "information" in self._messages_to_send[service_name]:
                        service_message += f"<p><u>Information</u><br/>"
                        # Add each message from the array.
                        for message in self._messages_to_send[service_name]["information"]:
                            service_message += f"- {message}\n"
                        service_message += "</p>"
                        highest_message_level = self._determine_highest_message_level(highest_message_level, MessageLevel.INFO)
                        service_message_levels.append(MessageLevel.INFO)

                # Is recipient subscribed for verbose level?
                if recipients[recipient_mail][service_name] == LogLevel.VERBOSE:

                    # Verbose messages.
                    if "verbose" in self._messages_to_send[service_name]:
                        service_message += f"<p><u>Verbose</u><br/>"
                        # Add each message from the array.
                        for message in self._messages_to_send[service_name]["verbose"]:
                            service_message += f"- {message}\n"
                        service_message += "</p>"
                        highest_message_level = self._determine_highest_message_level(highest_message_level, MessageLevel.VERBOSE)
                        service_message_levels.append(MessageLevel.VERBOSE)


                # Is there any message for the user of the serivce?
                if service_message != "":

                    # Indicate, that mail can be sent.
                    send_mail = True

                    # Add service to subject.
                    subject += service_name + ", "
                    
                    ## Heading ##
                    # Add service log levels to heading.
                    service_log_level_string=", ".join([str(message_level.value).lower() for message_level in service_message_levels])
                    service_log_level_string = f" ({service_log_level_string})"
                    # Add HTML to heading.
                    if service_name == self._unknownServiceIndicator:
                        msg_to_send += f"<p style=\"font-size:25px;\"><b>{service_name}</b>{service_log_level_string}</p>"
                    else:
                        msg_to_send += f"<p style=\"font-size:25px;\">Service <b>{service_name}</b>{service_log_level_string}</p>"

                    # Append service message.
                    msg_to_send += service_message + "\n"
            
            # Only send mail, if there is any message.
            if send_mail:

                # Remove the last comma of subject.
                subject = subject[:-2]

                # Change subject to also reflect log level in email.
                if highest_message_level == MessageLevel.IMPORTANT:
                    subject = subject.replace("Autoscaler info: ", "AUTOSCALER IMPORTANT INFO: ")
                elif highest_message_level == MessageLevel.ERROR:
                    subject = subject.replace("Autoscaler info: ", "Autoscaler ERROR: ")
                elif highest_message_level == MessageLevel.WARNING:
                    subject = subject.replace("Autoscaler info: ", "Autoscaler WARNING: ")
                elif highest_message_level == MessageLevel.INFO:
                    subject = subject.replace("Autoscaler info: ", "Autoscaler info: ")
                elif highest_message_level == MessageLevel.VERBOSE:
                    subject = subject.replace("Autoscaler info: ", "Autoscaler verbose info: ")

                # Finally send the email.
                self._send_email(self._sender, recipient_mail, subject, msg_to_send)

        

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
