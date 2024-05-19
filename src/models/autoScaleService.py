# Conversion.
import converterUtils

# Validation.
import validationUtils

# Definitions.
from label_definitions import cpu_labels, memory_labels
from valid_values import ScalingConflictResolution, LogLevel

class AutoScaleService:
    def __init__(self, service_name, autoscale_labels):
        self._service_name = service_name
        self._autoscale_labels = autoscale_labels


    ### Common required labels ###
    
    # Service name.
    def get_service_name(self):
        return self._service_name
    
    # Replica.
    def get_minimum_replicas(self):
        return int(self._autoscale_labels.get("autoscale.minimum_replicas", 1))
    
    def get_maximum_replicas(self):
        return int(self._autoscale_labels.get("autoscale.maximum_replicas", 3))
    

    ### Optional settings ###
    
    # Scaling Conflict Resolution.
    def get_scaling_conflict_resolution(self):
        value = self._autoscale_labels.get("autoscale.scaling_conflict_resolution", None)
        if value is not None and value in [item.value for item in ScalingConflictResolution]:
            return value
        return ScalingConflictResolution.SCALE_UP
    
    # LogLevel.
    def get_service_log_level(self):
        value = self._autoscale_labels.get("autoscale.log_level", None)
        if value is not None and value in [item.value for item in LogLevel]:
            return value
        return None
    

    ### Message Platforms ###

    ## Email ##
    def get_additional_email_recipients_important_msgs(self):
        """
        Get additional email recipients for important messages.

        Returns:
            list: List of valid email addresses for important messages.
        """
        return self._get_additional_email_recipients("autoscale.additional_email_recipients_important_msgs")


    def get_additional_email_recipients_information_msgs(self):
        """
        Get additional email recipients for information messages.

        Returns:
            list: List of valid email addresses for information messages.
        """
        return self._get_additional_email_recipients("autoscale.additional_email_recipients_information_msgs")


    def get_additional_email_recipients_verbose_msgs(self):
        """
        Get additional email recipients for verbose messages.

        Returns:
            list: List of valid email addresses for verbose messages.
        """
        return self._get_additional_email_recipients("autoscale.additional_email_recipients_verbose_msgs")


    def _get_additional_email_recipients(self, label_key):
        """
        Internal method to retrieve additional email recipients based on label key.

        Args:
            label_key (str): Key to retrieve the email list from autoscale labels.

        Returns:
            list: List of valid email addresses based on the label key.
        """
        valid_emails, warnings = converterUtils.get_email_array_from_emails_list_string(self._autoscale_labels.get(label_key, None))
        return valid_emails
    
    

    ## Telegram ##
    def get_additional_telegram_recipients_important_msgs(self):
        """
        Get additional telegram recipients for important messages.

        Returns:
            list: List of valid telegram chat IDs for important messages.
        """
        return self._get_additional_telegram_recipients("autoscale.additional_telegram_recipients_important_msgs")


    def get_additional_telegram_recipients_information_msgs(self):
        """
        Get additional telegram recipients for information messages.

        Returns:
            list: List of valid telegram chat IDs for information messages.
        """
        return self._get_additional_telegram_recipients("autoscale.additional_telegram_recipients_information_msgs")


    def get_additional_telegram_recipients_verbose_msgs(self):
        """
        Get additional telegram recipients for verbose messages.

        Returns:
            list: List of valid telegram chat IDs for verbose messages.
        """
        return self._get_additional_telegram_recipients("autoscale.additional_telegram_recipients_verbose_msgs")


    def _get_additional_telegram_recipients(self, label_key):
        """
        Internal method to retrieve additional telegram recipients based on label key.

        Args:
            label_key (str): Key to retrieve the telegram list from autoscale labels.

        Returns:
            list: List of valid telegram chat IDs based on the label key.
        """
        valid_recipients = []
        try:
            # Retrieve the telegram list string from autoscale labels.
            telegram_list_string = self._autoscale_labels.get(label_key, None)
            
            # Check if the telegram list is not empty or 'none'.
            if telegram_list_string and telegram_list_string.lower() != "none":
                # Split the string by commas and strip any whitespace.
                telegram_array = [telegram.strip() for telegram in telegram_list_string.split(',')]

                # Verify every telegram is of a valid format.
                for telegram_chat_id in telegram_array:
                    if validationUtils.is_telegram_chat_id_valid(telegram_chat_id):
                        valid_recipients.append(telegram_chat_id)
                    
        except Exception as e:
            # Return valid recipients in case of any exceptions.
            return valid_recipients

        # Return the list of valid recipients.
        return valid_recipients



    ### Metrics ###

    # Cpu.
    def is_scaling_based_on_cpu_enabled(self):
        # Are required labels set?
        for cpu_label_obj in cpu_labels:
            if cpu_label_obj["required"] == True and cpu_label_obj["label"] not in self._autoscale_labels:
                return False
        return True
    
    def get_cpu_upscale_threshold(self):
        return converterUtils.percentage_to_float(self._autoscale_labels.get("autoscale.cpu_upscale_threshold"))
    
    def get_cpu_upscale_time_duration(self):
        return self._autoscale_labels.get("autoscale.cpu_upscale_time_duration", "2m")
    
    def get_cpu_downscale_threshold(self):
        return converterUtils.percentage_to_float(self._autoscale_labels.get("autoscale.cpu_downscale_threshold"))
    
    def get_cpu_downscale_time_duration(self):
        return self._autoscale_labels.get("autoscale.cpu_downscale_time_duration", "5m")

    # Memory.
    def is_scaling_based_on_memory_enabled(self):
        # Are required labels set?
        for memory_label_obj in memory_labels:
            if memory_label_obj["required"] == True and memory_label_obj["label"] not in self._autoscale_labels:
                return False
        return True
    
    def get_memory_upscale_threshold(self):
        return converterUtils.human_readable_storage_to_bytes(self._autoscale_labels.get("autoscale.memory_upscale_threshold", None))
    
    def get_memory_downscale_threshold(self):
        return converterUtils.human_readable_storage_to_bytes(self._autoscale_labels.get("autoscale.memory_downscale_threshold", None))
    