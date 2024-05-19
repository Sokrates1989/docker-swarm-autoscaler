# Conversion utilities.
import converterUtils

# Definitions.
from valid_values import ScalingConflictResolution, ScalingSuggestion, ScalingMetricName, MessagingPlatforms

# MessagePlatformHandler.
import messagePlatformHandler as MessagePlatformHandler

class ScalingMetrics:
    """Model of scaling metrics for autoscaling service."""

    def __init__(
        self, 
        autoscale_service,
        metric_name: ScalingMetricName, 
        is_metric_based_scaling_enabled=False,
        upscale_threshold=None, 
        upscale_value=None, 
        downscale_threshold=None, 
        downscale_value=None, 
        conflict_resolution: ScalingConflictResolution = ScalingConflictResolution.SCALE_UP, 
        scaling_suggestion: ScalingSuggestion = ScalingSuggestion.KEEP_REPLICAS
    ):
        """
        Initialize ScalingMetrics object.

        Args:
            autoscale_service: The autoscaling service.
            metric_name (ScalingMetricName): The name of the scaling metric.
            is_metric_based_scaling_enabled (bool): Flag to enable metric-based scaling.
            upscale_threshold: The threshold for upscaling.
            upscale_value: The value for upscaling.
            downscale_threshold: The threshold for downscaling.
            downscale_value: The value for downscaling.
            conflict_resolution (ScalingConflictResolution): The conflict resolution strategy.
            scaling_suggestion (ScalingSuggestion): The scaling suggestion.
        """
        
        # MessagePlatformHandler.
        self._messagePlatformHandler = MessagePlatformHandler.MessagePlatformHandler()

        # Value instantiation.
        self._autoscale_service = autoscale_service
        
        # Verify if the provided metric_name is valid.
        if not isinstance(metric_name, ScalingMetricName):
            valid_metric_names = [member.value for member in ScalingMetricName]        
            error_message=f"<EMPHASIZE_STRING_START_TAG>{self._autoscale_service.get_service_name()}</EMPHASIZE_STRING_END_TAG>: ScalingMetrics: Invalid metric_name: <EMPHASIZE_STRING_START_TAG>{str(metric_name)}</EMPHASIZE_STRING_END_TAG>. Must be one of ScalingMetricName enum values: {', '.join(valid_metric_names)}."
            self._messagePlatformHandler.handle_error(error_message, self._autoscale_service)
            self._messagePlatformHandler.send_all_accumulated_messages()
            raise ValueError(error_message)

        self._metric_name = metric_name
        self._is_metric_based_scaling_enabled = is_metric_based_scaling_enabled
        self._upscale_threshold = upscale_threshold
        self._upscale_value = upscale_value
        self._downscale_threshold = downscale_threshold
        self._downscale_value = downscale_value
        self._conflict_resolution = conflict_resolution
        self._scaling_suggestion = scaling_suggestion
    

    ### Setter methods for parameters with default values ###

    def set_is_metric_based_scaling_enabled(self, is_metric_based_scaling_enabled):
        """Set flag to enable/disable metric-based scaling."""
        self._is_metric_based_scaling_enabled = is_metric_based_scaling_enabled
    
    def set_upscale_threshold(self, upscale_threshold):
        """Set the threshold for upscaling."""
        self._upscale_threshold = upscale_threshold
    
    def set_upscale_value(self, upscale_value):
        """Set the value for upscaling."""
        self._upscale_value = upscale_value
    
    def set_downscale_threshold(self, downscale_threshold):
        """Set the threshold for downscaling."""
        self._downscale_threshold = downscale_threshold
    
    def set_downscale_value(self, downscale_value):
        """Set the value for downscaling."""
        self._downscale_value = downscale_value
    
    def set_conflict_resolution(self, conflict_resolution):
        """Set the conflict resolution strategy."""
        self._conflict_resolution = conflict_resolution
    
    def set_scaling_suggestion(self, scaling_suggestion):
        """Set the scaling suggestion."""
        self._scaling_suggestion = scaling_suggestion


    ## Getter methods ##
    
    def get_metric_name(self):
        """Get the name of the scaling metric."""
        return self._metric_name
    
    def get_scaling_suggestion(self):
        """Get the scaling suggestion."""
        return self._scaling_suggestion
    

    def as_string(self, messagingPlatform: MessagingPlatforms = MessagingPlatforms.LOGGING):
        """
        Get string representation of this object.

        Args:
            messagingPlatform (MessagingPlatforms): The messaging platform for representation.

        Returns:
            str: String representation of this object.
        """

        # Message Platform specific strings.
        default_divider=", "
        metric_specific_icon=""
        if messagingPlatform == MessagingPlatforms.EMAIL:
            default_divider="\n"
            if self._metric_name == ScalingMetricName.CPU:
                metric_specific_icon="💻🕐⚙️💡🏁 "
            elif self._metric_name == ScalingMetricName.MEMORY:
                metric_specific_icon="⏳💾 "
        elif messagingPlatform == MessagingPlatforms.TELEGRAM:
            default_divider="\n"
            if self._metric_name == ScalingMetricName.CPU:
                metric_specific_icon="💻🕐⚙️💡🏁 "
            elif self._metric_name == ScalingMetricName.MEMORY:
                metric_specific_icon="⏳💾 "
            
        
        object_string = f"{metric_specific_icon}ScalingMetric: <EMPHASIZE_STRING_START_TAG>{self.get_metric_name()}</EMPHASIZE_STRING_END_TAG>"
        if self._is_metric_based_scaling_enabled:
            object_string += f"{default_divider}upscale threshold: {self._get_human_readable_upscale_threshold_string()}"
            object_string += f"{default_divider}upscale value: {self._get_human_readable_upscale_value_string()}"
            object_string += f"{default_divider}downscale threshold: {self._get_human_readable_downscale_threshold_string()}"
            object_string += f"{default_divider}downscale value: {self._get_human_readable_downscale_value_string()}"
            object_string += f"{default_divider}conflict resolution: <EMPHASIZE_STRING_START_TAG>{self._get_visualized_conflict_resolution_string(messagingPlatform)}</EMPHASIZE_STRING_END_TAG>"
            object_string += f"{default_divider}scaling suggestion: <EMPHASIZE_STRING_START_TAG>{self._get_visualized_scaling_suggestion_string(messagingPlatform)}</EMPHASIZE_STRING_END_TAG>"
        else:
            object_string += f"{default_divider}scaling based on this metric is not enabled."

        return object_string
    

    def _get_human_readable_upscale_threshold_string(self):
        """
        Get upscale_threshold as human readable string.

        Returns:
            str: Human readable string for upscale_threshold.
        """
        # Message Platform specific strings.
        human_readable_upscale_threshold_string=""
        if self._metric_name == ScalingMetricName.CPU:
            human_readable_upscale_threshold_string=f"<EMPHASIZE_STRING_START_TAG>{self._upscale_threshold} ({converterUtils.float_to_percentage(self._upscale_threshold)})</EMPHASIZE_STRING_END_TAG>"
        elif self._metric_name == ScalingMetricName.MEMORY:
            human_readable_upscale_threshold_string=f"<EMPHASIZE_STRING_START_TAG>{self._upscale_threshold} ({converterUtils.bytes_to_human_readable_storage(self._upscale_threshold)})</EMPHASIZE_STRING_END_TAG>"
        else:
            human_readable_upscale_threshold_string=f"ScalingMetrics._get_human_readable_upscale_threshold_string(): unimplemented metric_name <EMPHASIZE_STRING_START_TAG>{self._metric_name}</EMPHASIZE_STRING_END_TAG>"
        return human_readable_upscale_threshold_string
    

    def _get_human_readable_upscale_value_string(self):
        """
        Get upscale_value as human readable string.

        Returns:
            str: Human readable string for upscale_value.
        """
        # Message Platform specific strings.
        human_readable_upscale_value_string=""
        if self._metric_name == ScalingMetricName.CPU:
            human_readable_upscale_value_string=f"<EMPHASIZE_STRING_START_TAG>{self._upscale_value} ({converterUtils.float_to_percentage(self._upscale_value)})</EMPHASIZE_STRING_END_TAG>"
        elif self._metric_name == ScalingMetricName.MEMORY:
            human_readable_upscale_value_string=f"<EMPHASIZE_STRING_START_TAG>{self._upscale_value} ({converterUtils.bytes_to_human_readable_storage(self._upscale_value)})</EMPHASIZE_STRING_END_TAG>"
        else:
            human_readable_upscale_value_string=f"ScalingMetrics._get_human_readable_upscale_value_string(): unimplemented metric_name <EMPHASIZE_STRING_START_TAG>{self._metric_name}</EMPHASIZE_STRING_END_TAG>"
        return human_readable_upscale_value_string
    

    def _get_human_readable_downscale_threshold_string(self):
        """
        Get downscale_threshold as human readable string.

        Returns:
            str: Human readable string for downscale_threshold.
        """
        # Message Platform specific strings.
        human_readable_downscale_threshold_string=""
        if self._metric_name == ScalingMetricName.CPU:
            human_readable_downscale_threshold_string=f"<EMPHASIZE_STRING_START_TAG>{self._downscale_threshold} ({converterUtils.float_to_percentage(self._downscale_threshold)})</EMPHASIZE_STRING_END_TAG>"
        elif self._metric_name == ScalingMetricName.MEMORY:
            human_readable_downscale_threshold_string=f"<EMPHASIZE_STRING_START_TAG>{self._downscale_threshold} ({converterUtils.bytes_to_human_readable_storage(self._downscale_threshold)})</EMPHASIZE_STRING_END_TAG>"
        else:
            human_readable_downscale_threshold_string=f"ScalingMetrics._get_human_readable_downscale_threshold_string(): unimplemented metric_name <EMPHASIZE_STRING_START_TAG>{self._metric_name}</EMPHASIZE_STRING_END_TAG>"
        return human_readable_downscale_threshold_string
    
    def _get_human_readable_downscale_value_string(self):
        """
        Get downscale_value as human readable string.

        Returns:
            str: Human readable string for downscale_value.
        """
        # Message Platform specific strings.
        human_readable_downscale_value_string=""
        if self._metric_name == ScalingMetricName.CPU:
            human_readable_downscale_value_string=f"<EMPHASIZE_STRING_START_TAG>{self._downscale_value} ({converterUtils.float_to_percentage(self._downscale_value)})</EMPHASIZE_STRING_END_TAG>"
        elif self._metric_name == ScalingMetricName.MEMORY:
            human_readable_downscale_value_string=f"<EMPHASIZE_STRING_START_TAG>{self._downscale_value} ({converterUtils.bytes_to_human_readable_storage(self._downscale_value)})</EMPHASIZE_STRING_END_TAG>"
        else:
            human_readable_downscale_value_string=f"ScalingMetrics._get_human_readable_downscale_value_string(): unimplemented metric_name <EMPHASIZE_STRING_START_TAG>{self._metric_name}</EMPHASIZE_STRING_END_TAG>"
        return human_readable_downscale_value_string
    
    
    def _get_visualized_conflict_resolution_string(self, messagingPlatform: MessagingPlatforms = MessagingPlatforms.LOGGING):
        """
        Get string for conflict resolution with icons optimized for Messaging Platform.

        Args:
            messagingPlatform (MessagingPlatforms): The messaging platform for representation.

        Returns:
            str: String representation of conflict resolution with icons.
        """
        # Message Platform specific strings.
        visualized_conflict_resolution_string=f"{self._conflict_resolution}"
        if messagingPlatform == MessagingPlatforms.EMAIL:
            if self._conflict_resolution == ScalingConflictResolution.SCALE_UP:
                visualized_conflict_resolution_string+=" ↕️❓ 🟰 ↗️"
            elif self._conflict_resolution == ScalingConflictResolution.SCALE_DOWN:
                visualized_conflict_resolution_string+=" ↕️❓ 🟰 ↘️"
            elif self._conflict_resolution == ScalingConflictResolution.KEEP_REPLICAS:
                visualized_conflict_resolution_string+=" ↕️❓ 🟰 ➡️"
            elif self._conflict_resolution == ScalingConflictResolution.ADHERE_TO_MEMORY:
                visualized_conflict_resolution_string+=" ↕️❓ 🟰 ⏳💾"
            elif self._conflict_resolution == ScalingConflictResolution.ADHERE_TO_CPU:
                visualized_conflict_resolution_string+=" ↕️❓ 🟰 💻🕐⚙️💡🏁"
        elif messagingPlatform == MessagingPlatforms.TELEGRAM:
            if self._conflict_resolution == ScalingConflictResolution.SCALE_UP:
                visualized_conflict_resolution_string+=" ↕️❓ 🟰 ↗️"
            elif self._conflict_resolution == ScalingConflictResolution.SCALE_DOWN:
                visualized_conflict_resolution_string+=" ↕️❓ 🟰 ↘️"
            elif self._conflict_resolution == ScalingConflictResolution.KEEP_REPLICAS:
                visualized_conflict_resolution_string+=" ↕️❓ 🟰 ➡️"
            elif self._conflict_resolution == ScalingConflictResolution.ADHERE_TO_MEMORY:
                visualized_conflict_resolution_string+=" ↕️❓ 🟰 ⏳💾"
            elif self._conflict_resolution == ScalingConflictResolution.ADHERE_TO_CPU:
                visualized_conflict_resolution_string+=" ↕️❓ 🟰 💻🕐⚙️💡🏁"
        return visualized_conflict_resolution_string
    
    def _get_visualized_scaling_suggestion_string(self, messagingPlatform: MessagingPlatforms = MessagingPlatforms.LOGGING):
        """
        Get string for scaling suggestion with icons optimized for Messaging Platform.

        Args:
            messagingPlatform (MessagingPlatforms): The messaging platform for representation.

        Returns:
            str: String representation of scaling suggestion with icons.
        """
        # Message Platform specific strings.
        visualized_scaling_suggestion_string=f"{self._scaling_suggestion}"
        if messagingPlatform == MessagingPlatforms.EMAIL:
            if self._scaling_suggestion == ScalingSuggestion.SCALE_UP:
                visualized_scaling_suggestion_string+=" ↗️"
            elif self._scaling_suggestion == ScalingSuggestion.SCALE_DOWN:
                visualized_scaling_suggestion_string+=" ↘️"
            elif self._scaling_suggestion == ScalingSuggestion.KEEP_REPLICAS:
                visualized_scaling_suggestion_string+=" ➡️"
        elif messagingPlatform == MessagingPlatforms.TELEGRAM:
            if self._scaling_suggestion == ScalingSuggestion.SCALE_UP:
                visualized_scaling_suggestion_string+=" ↗️"
            elif self._scaling_suggestion == ScalingSuggestion.SCALE_DOWN:
                visualized_scaling_suggestion_string+=" ↘️"
            elif self._scaling_suggestion == ScalingSuggestion.KEEP_REPLICAS:
                visualized_scaling_suggestion_string+=" ➡️"
        return visualized_scaling_suggestion_string
