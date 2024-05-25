# Connect to docker via python api.
import docker

# String verification.
import re

# Own AutoScaleService class.
import autoScaleService as AutoScaleService

# Conversion.
import converterUtils

# Validation.
import validationUtils

# Definitions.
from label_definitions import cpu_labels, memory_labels, email_labels, telegram_labels
from valid_values import ScalingConflictResolution, LogLevel

class DockerServiceAutoscalerLabelHandler:
    """
    A class for checking if autoscale labels are set and if those labels hold valid values

        Parameters:
            service (docker.models.services.Service): Docker service object.
    """
    def __init__(self, service):
        # Labels of service.
        if "Labels" in service.attrs["Spec"]:
            self._labels = service.attrs["Spec"]["Labels"]
        else:
            self._labels = {}

        # Name of service.
        if "Name" in service.attrs["Spec"]:
            self._service_name = service.attrs["Spec"]["Name"]
        else:
            self._service_name = {}

            

    def is_autoscale_service(self):
        """
        Test if the passed service has the labels set, that enable autoscaling.

        Returns:
            bool: True or False
        """
        return "autoscale" in self._labels and self._labels["autoscale"] == "true"
    
    
    
    def get_autoscale_service(self):
        """
        Get AutoScaleService, if lables are valid.
        
        Returns:
            tuple: A tuple containing:
            - A boolean indicating whether service is a valid AutoScaleService (True) or not (False) at first position.
            - Either the AutoScaleService object if valid, or an error message array if not.
            - An array of verification warnings.
        """
        if self.is_autoscale_service():
            try:
                autoscale_labels = self._get_all_autoscale_labels()
                verification_errors, verification_warnings = self.verify_autoscale_labels()
                if verification_errors == []:
                    return True, AutoScaleService.AutoScaleService(self._service_name, autoscale_labels), verification_warnings
                else:
                    return False, verification_errors, verification_warnings
            except Exception as e:
                verification_errors = []
                verification_errors.append(str(e))
                return False, verification_errors, []



    
    def verify_autoscale_labels(self):
        """
        Verify if autoscaling labels are set correctly for the given service.

        Returns:
            tuple: A tuple containing two lists:
                - error_messages: A list containing verification error messages.
                    If labels are set correctly, returns an empty list.
                    If labels are missing or have incorrect values, returns a list
                    with error messages.
                - warning_messages: A list containing warning messages.
                    If no warnings are present, returns an empty list.
        """
        error_messages = []
        warning_messages = []
        try:
            autoscale_labels = self._get_all_autoscale_labels()

            ### Common required settings ###

            # Check if autoscale label exists and is set to "true".
            if "autoscale" not in autoscale_labels or autoscale_labels["autoscale"] != "true":
                error_messages.append(f"Label <EMPHASIZE_STRING_START_TAG>autoscale</EMPHASIZE_STRING_END_TAG> must be set to <EMPHASIZE_STRING_START_TAG>true</EMPHASIZE_STRING_END_TAG>")

            # Check if minimum and maximum replicas autoscale_labels are set and hold valid values.
            if "autoscale.minimum_replicas" not in autoscale_labels:
                error_messages.append(f"Label <EMPHASIZE_STRING_START_TAG>autoscale.minimum_replicas</EMPHASIZE_STRING_END_TAG> is missing")
            elif not autoscale_labels["autoscale.minimum_replicas"].isdigit() or int(autoscale_labels["autoscale.minimum_replicas"]) < 1:
                error_messages.append(f"Label <EMPHASIZE_STRING_START_TAG>autoscale.minimum_replicas</EMPHASIZE_STRING_END_TAG> must be an integer greater than or equal to 1. Provided invalid value: <EMPHASIZE_STRING_START_TAG>{autoscale_labels['autoscale.minimum_replicas']}</EMPHASIZE_STRING_END_TAG>")

            if "autoscale.maximum_replicas" not in autoscale_labels:
                error_messages.append(f"Label <EMPHASIZE_STRING_START_TAG>autoscale.maximum_replicas</EMPHASIZE_STRING_END_TAG> is missing")
            elif not autoscale_labels["autoscale.maximum_replicas"].isdigit() or int(autoscale_labels["autoscale.maximum_replicas"]) <= 0:
                error_messages.append(f"Label <EMPHASIZE_STRING_START_TAG>autoscale.maximum_replicas</EMPHASIZE_STRING_END_TAG> must be a positive integer bigger than autoscale.minimum_replicas. Provided invalid value: <EMPHASIZE_STRING_START_TAG>{autoscale_labels['autoscale.maximum_replicas']}</EMPHASIZE_STRING_END_TAG>")

            # Minimum smaller than maximum?
            if "autoscale.minimum_replicas" in autoscale_labels and "autoscale.maximum_replicas" in autoscale_labels and autoscale_labels["autoscale.minimum_replicas"].isdigit() and autoscale_labels["autoscale.maximum_replicas"].isdigit():
                if int(autoscale_labels["autoscale.maximum_replicas"]) <= int(autoscale_labels["autoscale.minimum_replicas"]):
                    error_messages.append(f"Label <EMPHASIZE_STRING_START_TAG>autoscale.maximum_replicas</EMPHASIZE_STRING_END_TAG>(Provided: <EMPHASIZE_STRING_START_TAG>{autoscale_labels['autoscale.maximum_replicas']}</EMPHASIZE_STRING_END_TAG>) must be greater than Label <EMPHASIZE_STRING_START_TAG>autoscale.minimum_replicas</EMPHASIZE_STRING_END_TAG>(Provided: <EMPHASIZE_STRING_START_TAG>{autoscale_labels['autoscale.maximum_replicas']}</EMPHASIZE_STRING_END_TAG>)")


            ### Optional settings ###

            # Check if autoscale.scaling_conflict_resolution holds valid value.
            if "autoscale.scaling_conflict_resolution" in autoscale_labels:
                value = autoscale_labels["autoscale.scaling_conflict_resolution"]
                if value not in [item.value for item in ScalingConflictResolution]:
                    valid_values_str = ", ".join([item.value for item in ScalingConflictResolution])
                    warning_messages.append(f"Label <EMPHASIZE_STRING_START_TAG>autoscale.scaling_conflict_resolution</EMPHASIZE_STRING_END_TAG> must be one of: {valid_values_str}. Provided invalid value: <EMPHASIZE_STRING_START_TAG>{value}</EMPHASIZE_STRING_END_TAG>")

            # Check if autoscale.log_level holds valid value.
            if "autoscale.log_level" in autoscale_labels:
                value = autoscale_labels["autoscale.log_level"]
                if value not in [item.value for item in LogLevel]:
                    valid_values_str = ", ".join([item.value for item in LogLevel])
                    warning_messages.append(f"Label <EMPHASIZE_STRING_START_TAG>autoscale.log_level</EMPHASIZE_STRING_END_TAG> must be one of: {valid_values_str}. Provided invalid value: <EMPHASIZE_STRING_START_TAG>{value}</EMPHASIZE_STRING_END_TAG>")


            # Email related labels.
            warning_messages += self._verify_email_labels(autoscale_labels)

            # Email related labels.
            warning_messages += self._verify_telegram_labels(autoscale_labels)


            # CPU.
            error_messages += self._verify_cpu_labels(autoscale_labels)

            # Memory.
            error_messages += self._verify_memory_labels(autoscale_labels)

            # Is any metric set?
            any_metric_is_set = self._is_any_cpu_label_set(autoscale_labels) or self._is_any_memory_label_set(autoscale_labels)
            if not any_metric_is_set:
                error_messages.append(f"At least one metric to base autoscaling on has to be set (cpu, memory, ...). https://github.com/Sokrates1989/swarm-monitoring-autoscaler?tab=readme-ov-file#autoscaler")
        except Exception as e:
            error_messages.append(str(e))

        return error_messages, warning_messages
    

    def _verify_email_labels(self, autoscale_labels):
        """
        Verify if email autoscaling labels are set correctly for the given service.

        Args:
            autoscale_labels (dict): A dictionary containing autoscale labels.

        Returns:
            tuple: A tuple containing two lists:
                - error_messages: A list containing verification error messages.
                    If labels are set correctly, returns an empty list.
                    If labels are missing or have incorrect values, returns a list
                    with error messages.
                - warning_messages: A list containing warning messages.
                    If no warnings are present, returns an empty list.
        """
        error_messages = []

        # Is any email label set?
        if self._is_any_email_label_set(autoscale_labels):
            # Verify each label.
            for email_label_obj in email_labels:
                if email_label_obj["label"] not in autoscale_labels:
                    # If one label is set, all required have them need to be.
                    if email_label_obj["required"]:
                        missing_required_label=email_label_obj["label"]
                        error_messages.append(f"Label <EMPHASIZE_STRING_START_TAG>{missing_required_label}</EMPHASIZE_STRING_END_TAG> is missing")
                else:
                    error_messages += self._verify_label(email_label_obj["label"], autoscale_labels[email_label_obj["label"]], email_label_obj["value_type"])

        return error_messages
    
    
    def _is_any_email_label_set(self, autoscale_labels):
        """
        Check if any Email-related autoscale label is set.

        Args:
            autoscale_labels (dict): Dictionary containing autoscale labels and their values.

        Returns:
            bool: True if any Email-related label is set, False otherwise.
        """
        email_label_names = [email_label_obj["label"] for email_label_obj in email_labels]
        for label in autoscale_labels:
            if label in email_label_names:
                return True
        return False
    

    
    def _verify_telegram_labels(self, autoscale_labels):
        """
        Verify if telegram autoscaling labels are set correctly for the given service.

        Returns:
            list: A list containing verification error messages.
                If labels are set correctly, returns an empty list.
                If labels are missing or have incorrect values, returns a list
                with error messages.
        """
        error_messages = []

        # Is any telegram label set?
        if self._is_any_telegram_label_set(autoscale_labels):
            # Verify each label.
            for telegram_label_obj in telegram_labels:
                if telegram_label_obj["label"] not in autoscale_labels:
                    # If one label is set, all required have them need to be.
                    if telegram_label_obj["required"]:
                        missing_required_label=telegram_label_obj["label"]
                        error_messages.append(f"Label <EMPHASIZE_STRING_START_TAG>{missing_required_label}</EMPHASIZE_STRING_END_TAG> is missing")
                else:
                    error_messages += self._verify_label(telegram_label_obj["label"], autoscale_labels[telegram_label_obj["label"]], telegram_label_obj["value_type"])

        return error_messages
    
    
    
    def _is_any_telegram_label_set(self, autoscale_labels):
        """
        Check if any Telegram-related autoscale label is set.

        Args:
            autoscale_labels (dict): Dictionary containing autoscale labels and their values.

        Returns:
            bool: True if any Telegram-related label is set, False otherwise.
        """
        telegram_label_names = [telegram_label_obj["label"] for telegram_label_obj in telegram_labels]
        for label in autoscale_labels:
            if label in telegram_label_names:
                return True
        return False

    
    
    
    def _verify_cpu_labels(self, autoscale_labels):
        """
        Verify if cpu autoscaling labels are set correctly for the given service.

        Returns:
            list: A list containing verification error messages.
                If labels are set correctly, returns an empty list.
                If labels are missing or have incorrect values, returns a list
                with error messages.
        """
        error_messages = []

        # Is any cpu label set?
        if self._is_any_cpu_label_set(autoscale_labels):
            # Verify each label.
            for cpu_label_obj in cpu_labels:
                if cpu_label_obj["label"] not in autoscale_labels:
                    # If one label is set, all required have them need to be.
                    if cpu_label_obj["required"]:
                        missing_required_label=cpu_label_obj["label"]
                        error_messages.append(f"Label <EMPHASIZE_STRING_START_TAG>{missing_required_label}</EMPHASIZE_STRING_END_TAG> is missing")
                else:
                    error_messages += self._verify_label(cpu_label_obj["label"], autoscale_labels[cpu_label_obj["label"]], cpu_label_obj["value_type"])

        return error_messages
    

    
    def _is_any_cpu_label_set(self, autoscale_labels):
        """
        Check if any CPU-related autoscale label is set.

        Args:
            autoscale_labels (dict): Dictionary containing autoscale labels and their values.

        Returns:
            bool: True if any CPU-related label is set, False otherwise.
        """
        cpu_label_names = [cpu_label_obj["label"] for cpu_label_obj in cpu_labels]
        for label in autoscale_labels:
            if label in cpu_label_names:
                return True
        return False
    

    
    def _verify_memory_labels(self, autoscale_labels):
        """
        Verify if memory autoscaling labels are set correctly for the given service.

        Returns:
            list: A list containing verification error messages.
                If labels are set correctly, returns an empty list.
                If labels are missing or have incorrect values, returns a list
                with error messages.
        """
        error_messages = []

        # Is any memory label set?
        if self._is_any_memory_label_set(autoscale_labels):
            # Verify each label.
            for memory_label_obj in memory_labels:
                if memory_label_obj["label"] not in autoscale_labels:
                    # If one label is set, all have them need to be.
                    if memory_label_obj["required"]:
                        missing_required_label=memory_label_obj["label"]
                        error_messages.append(f"Label <EMPHASIZE_STRING_START_TAG>{missing_required_label}</EMPHASIZE_STRING_END_TAG> is missing")
                else:
                    error_messages += self._verify_label(memory_label_obj["label"], autoscale_labels[memory_label_obj["label"]], memory_label_obj["value_type"])

        return error_messages
    

    
    def _is_any_memory_label_set(self, autoscale_labels):
        """
        Check if any memory-related autoscale label is set.

        Args:
            autoscale_labels (dict): Dictionary containing autoscale labels and their values.

        Returns:
            bool: True if any memory-related label is set, False otherwise.
        """
        memory_label_names = [memory_label_obj["label"] for memory_label_obj in memory_labels]
        for label in autoscale_labels:
            if label in memory_label_names:
                return True
        return False
    

        
    def _verify_label(self, label, value, value_type):
        """
        Verify if a specific autoscale label is set correctly for the given service.

        Args:
            label_name (str): The name of the autoscale label to verify.
            value: The value of the autoscale label to verify
            value_type (str): The type of value expected for the label.

        Returns:
            list: A list containing verification error message.
        """
        error_messages = []
        provided_invalid_value_message_addendum=f". Provided invalid value: <EMPHASIZE_STRING_START_TAG>{value}</EMPHASIZE_STRING_END_TAG>"

        if value_type == "percentage":
            try:
                converterUtils.percentage_to_float(value)
            except Exception as e:
                error_messages.append(f"Label <EMPHASIZE_STRING_START_TAG>{label}</EMPHASIZE_STRING_END_TAG> {str(e)}{provided_invalid_value_message_addendum}")
        elif value_type == "valid time_duration":
            if not re.match(r'^\d+[smhdwy]$', value):
                error_messages.append(f"Label <EMPHASIZE_STRING_START_TAG>{label}</EMPHASIZE_STRING_END_TAG> must be a valid time_duration (https://prometheus.io/docs/prometheus/latest/querying/basics/#time-durations){provided_invalid_value_message_addendum}")
        elif value_type == "byte":
            try:
                converterUtils.human_readable_storage_to_bytes(value)
            except Exception as e:
                error_messages.append(f"Label <EMPHASIZE_STRING_START_TAG>{label}</EMPHASIZE_STRING_END_TAG> {str(e)}{provided_invalid_value_message_addendum}")
        elif value_type == "email_list":
            # Get warnings from converter utils.
            valid_emails, warnings = converterUtils.get_email_array_from_emails_list_string(value)
            # Append custom label to each warning.
            warnings = [f"Label <EMPHASIZE_STRING_START_TAG>{label}</EMPHASIZE_STRING_END_TAG>: {warning}{provided_invalid_value_message_addendum}" for warning in warnings]
            # Merge warnings with errors.
            error_messages.extend(warnings)
        elif value_type == "telegram_chat_id_list":
            # Get warnings from converter utils.
            valid_chat_ids, warnings = converterUtils.get_telegram_array_from_telegram_chats_list_string(value)
            # Append custom label to each warning.
            warnings = [f"Label <EMPHASIZE_STRING_START_TAG>{label}</EMPHASIZE_STRING_END_TAG>: {warning}{provided_invalid_value_message_addendum}" for warning in warnings]
            # Merge warnings with errors.
            error_messages.extend(warnings)

        else: 
            error_messages.append(f"DockerServiceAutoscalerLabelHandler._verify_label(): Unknown value type <EMPHASIZE_STRING_START_TAG>{value_type}</EMPHASIZE_STRING_END_TAG> for label <EMPHASIZE_STRING_START_TAG>{label}</EMPHASIZE_STRING_END_TAG>")

        return error_messages
        
    

    def _get_all_autoscale_labels(self):
        """
        Gets all autoscale relevant labels with their values without checking value validity.

        ! Does not verify, if those labels hold valid values !

        Returns:
            Dict of unchecked autoscale labels of the passed service.
        """
        autoscale_labels = {}
        if self.is_autoscale_service():

            # Required common settings.
            if "autoscale" in self._labels:
                autoscale_labels["autoscale"] = self._labels["autoscale"]
            if "autoscale.minimum_replicas" in self._labels:
                autoscale_labels["autoscale.minimum_replicas"] = self._labels["autoscale.minimum_replicas"]
            if "autoscale.maximum_replicas" in self._labels:
                autoscale_labels["autoscale.maximum_replicas"] = self._labels["autoscale.maximum_replicas"]
            
            # Cpu Metrics.
            if "autoscale.cpu_upscale_threshold" in self._labels:
                autoscale_labels["autoscale.cpu_upscale_threshold"] = self._labels["autoscale.cpu_upscale_threshold"]
            if "autoscale.cpu_upscale_time_duration" in self._labels:
                autoscale_labels["autoscale.cpu_upscale_time_duration"] = self._labels["autoscale.cpu_upscale_time_duration"]
            if "autoscale.cpu_downscale_threshold" in self._labels:
                autoscale_labels["autoscale.cpu_downscale_threshold"] = self._labels["autoscale.cpu_downscale_threshold"]
            if "autoscale.cpu_downscale_time_duration" in self._labels:
                autoscale_labels["autoscale.cpu_downscale_time_duration"] = self._labels["autoscale.cpu_downscale_time_duration"]

            # Memory metrics.
            if "autoscale.memory_upscale_threshold" in self._labels:
                autoscale_labels["autoscale.memory_upscale_threshold"] = self._labels["autoscale.memory_upscale_threshold"]
            if "autoscale.memory_downscale_threshold" in self._labels:
                autoscale_labels["autoscale.memory_downscale_threshold"] = self._labels["autoscale.memory_downscale_threshold"]

            # Optional settings.
            if "autoscale.scaling_conflict_resolution" in self._labels:
                autoscale_labels["autoscale.scaling_conflict_resolution"] = self._labels["autoscale.scaling_conflict_resolution"]
            if "autoscale.log_level" in self._labels:
                autoscale_labels["autoscale.log_level"] = self._labels["autoscale.log_level"]

            # Email related labels.
            if "autoscale.additional_email_recipients_important_msgs" in self._labels:
                autoscale_labels["autoscale.additional_email_recipients_important_msgs"] = self._labels["autoscale.additional_email_recipients_important_msgs"]
            if "autoscale.additional_email_recipients_information_msgs" in self._labels:
                autoscale_labels["autoscale.additional_email_recipients_information_msgs"] = self._labels["autoscale.additional_email_recipients_information_msgs"]
            if "autoscale.additional_email_recipients_verbose_msgs" in self._labels:
                autoscale_labels["autoscale.additional_email_recipients_verbose_msgs"] = self._labels["autoscale.additional_email_recipients_verbose_msgs"]
            
            # Telegram related labels.
            if "autoscale.additional_telegram_recipients_important_msgs" in self._labels:
                autoscale_labels["autoscale.additional_telegram_recipients_important_msgs"] = self._labels["autoscale.additional_telegram_recipients_important_msgs"]
            if "autoscale.additional_telegram_recipients_information_msgs" in self._labels:
                autoscale_labels["autoscale.additional_telegram_recipients_information_msgs"] = self._labels["autoscale.additional_telegram_recipients_information_msgs"]
            if "autoscale.additional_telegram_recipients_verbose_msgs" in self._labels:
                autoscale_labels["autoscale.additional_telegram_recipients_verbose_msgs"] = self._labels["autoscale.additional_telegram_recipients_verbose_msgs"]

            return autoscale_labels
        else:
            return {}
