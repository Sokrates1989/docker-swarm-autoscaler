# Connect to docker via python api.
import docker

# String verification.
import re

# Own AutoScaleService class.
import autoScaleService as AutoScaleService

# Conversion.
import converterUtils

# Definitions.
from label_definitions import cpu_labels, memory_labels
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
            tuple: A tuple containing a boolean indicating whether service is a valid AutoScaleService at first position,
                   and either the AutoScaleService or an error message Array at second position.
        """
        if self.is_autoscale_service():
            try:
                autoscale_labels = self._get_all_autoscale_labels()
            
                verification_results = self.verify_autoscale_labels()
                if verification_results == []:
                    return True, AutoScaleService.AutoScaleService(self._service_name, autoscale_labels)
                else:
                    return False, verification_results
            except Exception as e:
                verification_results = []
                verification_results.append(str(e))
                return False, verification_results



    
    def verify_autoscale_labels(self):
        """
        Verify if autoscaling labels are set correctly for the given service.

        Returns:
            list: A list containing verification error messages.
                If labels are set correctly, returns an empty list.
                If labels are missing or have incorrect values, returns a list
                with error messages.
        """
        error_messages = []
        try:
            autoscale_labels = self._get_all_autoscale_labels()

            # Check if autoscale label exists and is set to "true".
            if "autoscale" not in autoscale_labels or autoscale_labels["autoscale"] != "true":
                error_messages.append(f"Label 'autoscale' must be set to 'true'")

            # Check if minimum and maximum replicas autoscale_labels are set and hold valid values.
            if "autoscale.minimum_replicas" not in autoscale_labels:
                error_messages.append(f"Label 'autoscale.minimum_replicas' is missing")
            elif not autoscale_labels["autoscale.minimum_replicas"].isdigit() or int(autoscale_labels["autoscale.minimum_replicas"]) < 1:
                error_messages.append(f"Label 'autoscale.minimum_replicas' must be an integer greater than or equal to 1. Provided invalid value: \"{autoscale_labels['autoscale.minimum_replicas']}\"")

            if "autoscale.maximum_replicas" not in autoscale_labels:
                error_messages.append(f"Label 'autoscale.maximum_replicas' is missing")
            elif not autoscale_labels["autoscale.maximum_replicas"].isdigit() or int(autoscale_labels["autoscale.maximum_replicas"]) <= 0:
                error_messages.append(f"Label 'autoscale.maximum_replicas' must be a positive integer bigger than autoscale.minimum_replicas. Provided invalid value: \"{autoscale_labels['autoscale.maximum_replicas']}\"")

            # Minimum smaller than maximum?
            if "autoscale.minimum_replicas" in autoscale_labels and "autoscale.maximum_replicas" in autoscale_labels and autoscale_labels["autoscale.minimum_replicas"].isdigit() and autoscale_labels["autoscale.maximum_replicas"].isdigit():
                if int(autoscale_labels["autoscale.maximum_replicas"]) <= int(autoscale_labels["autoscale.minimum_replicas"]):
                    error_messages.append(f"Label 'autoscale.maximum_replicas'(Provided: \"{autoscale_labels['autoscale.maximum_replicas']}\") must be greater than Label 'autoscale.minimum_replicas'(Provided: \"{autoscale_labels['autoscale.maximum_replicas']}\")")


            # Check if autoscale.scaling_conflict_resolution holds valid value.
            if "autoscale.scaling_conflict_resolution" in autoscale_labels:
                value = autoscale_labels["autoscale.scaling_conflict_resolution"]
                if value not in [item.value for item in ScalingConflictResolution]:
                    valid_values_str = ", ".join([item.value for item in ScalingConflictResolution])
                    error_messages.append(f"Label 'autoscale.scaling_conflict_resolution' must be one of: {valid_values_str}. Provided invalid value: \"{value}\"")

            # Check if autoscale.log_level holds valid value.
            if "autoscale.log_level" in autoscale_labels:
                value = autoscale_labels["autoscale.log_level"]
                if value not in [item.value for item in LogLevel]:
                    valid_values_str = ", ".join([item.value for item in LogLevel])
                    error_messages.append(f"Label 'autoscale.log_level' must be one of: {valid_values_str}. Provided invalid value: {value}")

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

        return error_messages
    
    
    
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
                        error_messages.append(f"Label '{missing_required_label}' is missing")
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
                        error_messages.append(f"Label '{missing_required_label}' is missing")
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
        provided_invalid_value_message_addendum=f". Provided invalid value: \"{value}\""

        if value_type == "percentage":
            try:
                converterUtils.percentage_to_float(value)
            except Exception as e:
                error_messages.append(f"Label '{label}' {str(e)}{provided_invalid_value_message_addendum}")
        elif value_type == "valid time_duration":
            if not re.match(r'^\d+[smhdwy]$', value):
                error_messages.append(f"Label '{label}' must be a valid time_duration (https://prometheus.io/docs/prometheus/latest/querying/basics/#time-durations){provided_invalid_value_message_addendum}")
        elif value_type == "byte":
            try:
                converterUtils.human_readable_storage_to_bytes(value)
            except Exception as e:
                error_messages.append(f"Label '{label}' {str(e)}{provided_invalid_value_message_addendum}")

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
            if "autoscale" in self._labels:
                autoscale_labels["autoscale"] = self._labels["autoscale"]
            if "autoscale.minimum_replicas" in self._labels:
                autoscale_labels["autoscale.minimum_replicas"] = self._labels["autoscale.minimum_replicas"]
            if "autoscale.maximum_replicas" in self._labels:
                autoscale_labels["autoscale.maximum_replicas"] = self._labels["autoscale.maximum_replicas"]
            if "autoscale.cpu_upscale_threshold" in self._labels:
                autoscale_labels["autoscale.cpu_upscale_threshold"] = self._labels["autoscale.cpu_upscale_threshold"]
            if "autoscale.cpu_upscale_time_duration" in self._labels:
                autoscale_labels["autoscale.cpu_upscale_time_duration"] = self._labels["autoscale.cpu_upscale_time_duration"]
            if "autoscale.cpu_downscale_threshold" in self._labels:
                autoscale_labels["autoscale.cpu_downscale_threshold"] = self._labels["autoscale.cpu_downscale_threshold"]
            if "autoscale.cpu_downscale_time_duration" in self._labels:
                autoscale_labels["autoscale.cpu_downscale_time_duration"] = self._labels["autoscale.cpu_downscale_time_duration"]
            if "autoscale.memory_upscale_threshold" in self._labels:
                autoscale_labels["autoscale.memory_upscale_threshold"] = self._labels["autoscale.memory_upscale_threshold"]
            if "autoscale.memory_downscale_threshold" in self._labels:
                autoscale_labels["autoscale.memory_downscale_threshold"] = self._labels["autoscale.memory_downscale_threshold"]
            if "autoscale.scaling_conflict_resolution" in self._labels:
                autoscale_labels["autoscale.scaling_conflict_resolution"] = self._labels["autoscale.scaling_conflict_resolution"]
            if "autoscale.log_level" in self._labels:
                autoscale_labels["autoscale.log_level"] = self._labels["autoscale.log_level"]
            return autoscale_labels
        else:
            return {}
