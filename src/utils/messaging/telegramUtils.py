# Sends emails.

# Email specific imports.
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Get environment variables.
import os

# Definitions.
from valid_values import MessagingPlatforms, LogLevel

# Conversion.
import converterUtils

# MessagePlatformHandler.
import messagePlatformHandler as MessagePlatformHandler

class TelegramUtils:

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

        # Prepare warning messages to log in case of warnings in setting log settings below.
        warning_messages = []


        # Are E-Mail status messages enabled?
        self._email_enabled = os.getenv("EMAIL_ENABLED")
        if self._email_enabled.lower() == "true":
            self._email_enabled = True
        elif self._email_enabled.lower() == "false":
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
            except:
                pass
            finally:
                # If there is no SECRET_FILE.
                if not "password" in self._sender:
                    self._sender["password"] = os.getenv('EMAIL_SENDER_PASSWORD').strip().strip("\"")
            if not "password" in self._sender:
                warning_messages.append(f"EmailUtils: No Password for Email sender provided. Disabling Email status messages.")
                self._email_enabled = False


            # Sender Host.
            self._sender["host"] = os.getenv('EMAIL_SENDER_HOST').strip().strip("\"")
            if not "host" in self._sender:
                warning_messages.append(f"EmailUtils: No host for Email sender provided. Disabling Email status messages.")
                self._email_enabled = False


            # Sender Port.
            self._sender["port"] = os.getenv('EMAIL_SENDER_HOST').strip().strip("\"")
            if not "port" in self._sender:
                warning_messages.append(f"EmailUtils: No port for Email sender provided. Disabling Email status messages.")
                self._email_enabled = False

            # Default Recipients.
            important_recipients, warnings = converterUtils.get_email_array_from_emails_list_string(os.getenv('EMAIL_RECIPIENTS_IMPORTANT').strip().strip("\""))
            information_recipients, warnings = converterUtils.get_email_array_from_emails_list_string(os.getenv('EMAIL_RECIPIENTS_INFORMATION').strip().strip("\""))
            verbose_recipients, warnings = converterUtils.get_email_array_from_emails_list_string(os.getenv('EMAIL_RECIPIENTS_VERBOSE').strip().strip("\""))
            self._default_recipients_important = important_recipients
            self._default_recipients_information = information_recipients
            self._default_recipients_verbose = verbose_recipients
            
        # Test sender login.
        if self._email_enabled:
            smpt_login_successful=self._test_smtp_login(self._sender)
            if not smpt_login_successful:
                warning_messages.append(f"EmailUtils smtp login test failed: {smpt_login_successful}. Disabling Email status messages.")
                self._email_enabled = False

                

        # Log all warning messages after both log level and log style are set.
        for warning_msg in warning_messages:
            self._messagePlatformHandler.handle_warning(warning_msg)



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


    def handle_warning(self, warning_info, autoscale_service):
        """
        Handles warning information.

        Accumulates messages to send later.

        Args:
            autoscale_service (AutoScaleService): The autoscale service this information is about
            warning_info (str): Warning info message to handle.
        """
        # Accumulate messages to send later.
        service_name = autoscale_service.get_service_name()
        if service_name not in self._messages_to_send:
            self._messages_to_send[service_name] = {}
        if "warning" not in self._messages_to_send[service_name]:
            self._messages_to_send[service_name]["warning"] = []
        self._add_service_name(service_name)
        self._messages_to_send[service_name]["warning"].append(warning_info)

    def handle_information(self, information, autoscale_service):
        """
        Handles information.

        Accumulates messages to send later.

        Args:
            autoscale_service (AutoScaleService): The autoscale service this information is about
            information (str): Information message to handle.
        """
        # Accumulate messages to send later.
        service_name = autoscale_service.get_service_name()
        if service_name not in self._messages_to_send:
            self._messages_to_send[service_name] = {}
        if "information" not in self._messages_to_send[service_name]:
            self._messages_to_send[service_name]["information"] = []
        self._add_service_name(service_name)
        self._messages_to_send[service_name]["information"].append(information)


    def handle_verbose_info(self, verbose_info, autoscale_service):
        """
        Handles verbose information.

        Accumulates messages to send later.

        Args:
            autoscale_service (AutoScaleService): The autoscale service this information is about
            verbose_info (str): Verbose info message to handle.
        """
        # Accumulate messages to send later.
        service_name = autoscale_service.get_service_name()
        if service_name not in self._messages_to_send:
            self._messages_to_send[service_name] = {}
        if "verbose" not in self._messages_to_send[service_name]:
            self._messages_to_send[service_name]["verbose"] = []
        self._add_service_name(service_name)
        self._messages_to_send[service_name]["verbose"].append(verbose_info)


    def _test_smtp_login(self, sender):
        try:
            server = smtplib.SMTP_SSL(sender["host"], sender["port"])
            server.starttls()
            server.login(sender["user"], sender["password)"])
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

        server = smtplib.SMTP_SSL(sender["host"], sender["port"])
        server.starttls()
        server.login(sender["user"], sender["password)"])

        # Add message body.
        msg.attach(MIMEText(message, 'plain'))

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
        for recipient_email, additional_recipients in self._additional_recipients_important.items():
            if recipient_email not in recipients:
                recipients[recipient_email] = {service: LogLevel.IMPORTANT_ONLY for service in self._services}
            else:
                for service in additional_recipients:
                    if service not in recipients[recipient_email]:
                        recipients[recipient_email][service] = LogLevel.IMPORTANT_ONLY

        for recipient_email, additional_recipients in self._additional_recipients_information.items():
            if recipient_email not in recipients:
                recipients[recipient_email] = {service: LogLevel.INFO for service in self._services}
            else:
                for service in additional_recipients:
                    if service not in recipients[recipient_email] or recipients[recipient_email][service] == LogLevel.IMPORTANT_ONLY:
                        recipients[recipient_email][service] = LogLevel.INFO

        for recipient_email, additional_recipients in self._additional_recipients_verbose.items():
            if recipient_email not in recipients:
                recipients[recipient_email] = {service: LogLevel.VERBOSE for service in self._services}
            else:
                for service in additional_recipients:
                    recipients[recipient_email][service] = LogLevel.VERBOSE
                        
        return recipients
    

    def send_all_accumulated_messages(self):
        """
        Send all accumulated messages via email to respective recipients.
        """
        if not self._email_enabled:
            return

        # # Prepare a message for every recipient.
        # recipients = self._get_all_recipients()
        # for recipient_mail in recipients:
        #     msg_to_send = ""
        #     subject = "Autoscaler info: "
        #     # What services is the recipient subscribed to?
        #     for service_name in recipients[recipient_mail]:

        #         # Add service to subject.
        #         subject += service_name + ", "
        #         # Prepare message based on info level.
        #         msg_to_send += f"Service <EMPHASIZE_STRING_START_TAG>{service_name}</EMPHASIZE_STRING_END_TAG>"

        #         # Important messages.
        #         if self._messages_to_send[service_name]["important"]:
        #             msg_to_send += f"\nImportant\n"
        #             # Add each message from the array.
        #             for message in self._messages_to_send[service_name]["important"]:
        #                 msg_to_send += f"- {message}\n"

        #         # Error messages.
        #         if self._messages_to_send[service_name]["error"]:
        #             msg_to_send += f"\nErrors\n"
        #             # Add each message from the array.
        #             for message in self._messages_to_send[service_name]["error"]:
        #                 msg_to_send += f"- {message}\n"

        #         # Warning messages.
        #         if self._messages_to_send[service_name]["warning"]:
        #             msg_to_send += f"\nWarnings\n"
        #             # Add each message from the array.
        #             for message in self._messages_to_send[service_name]["warning"]:
        #                 msg_to_send += f"- {message}\n"

                
        #         # Is recipient subscribed for informataion level?
        #         if recipients[recipient_mail][service_name] == LogLevel.VERBOSE or recipients[recipient_mail][service_name] == LogLevel.INFO:

        #             # Information messages.
        #             if self._messages_to_send[service_name]["information"]:
        #                 msg_to_send += f"\nInformation\n"
        #                 # Add each message from the array.
        #                 for message in self._messages_to_send[service_name]["information"]:
        #                     msg_to_send += f"- {message}\n"

        #         # Is recipient subscribed for verbose level?
        #         if recipients[recipient_mail][service_name] == LogLevel.VERBOSE:

        #             # Verbose messages.
        #             if self._messages_to_send[service_name]["verbose"]:
        #                 msg_to_send += f"\nVerbose\n"
        #                 # Add each message from the array.
        #                 for message in self._messages_to_send[service_name]["verbose"]:
        #                     msg_to_send += f"- {message}\n"

                
        #         msg_to_send += "\n\n"

            
        #     # Remove the last comma.
        #     subject = subject[:-2]

        #     # Finally send the email.
        #     self._send_email(self._sender, recipient_mail, subject, msg_to_send)
