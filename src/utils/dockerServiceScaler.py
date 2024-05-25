# Connect to docker via python api.
import docker

# Own class to get autoscale services from labels.
import dockerServiceAutoscalerLabelHandler as DockerServiceAutoscalerLabelHandler

# For retrieving container/ service metrics via prometheus.
import prometheusConnector as PrometheusConnector
prometheusConnector = PrometheusConnector.PrometheusConnector()

# Definitions.
from valid_values import ScalingConflictResolution, ScalingSuggestion, ScalingMetricName, MessagingPlatforms

# Custom Scaling Metrics class.
import scalingMetrics as ScalingMetrics

# Logger.
import messagePlatformHandler as MessagePlatformHandler

# Conversion.
import converterUtils

class DockerServiceScaler:
    """
    A class for scaling Docker services.

    This class provides methods to scale Docker services to a specified number of replicas
    and retrieve the current number of replicas for a given service.
    """

    def __init__(self):
        self.client = docker.from_env()
        self._messagePlatformHandler = MessagePlatformHandler.MessagePlatformHandler()

    def auto_scale_services(self):
        """
        Look for services with autoscale enabled and then scale based on prometheus metrics.
        """
        # Loop through all autoscale services.
        autoscale_services = self._get_autoscale_services()
        for autoscale_service in autoscale_services:

            # Add additional recipients for the service.
            self._messagePlatformHandler.add_additional_recipients(autoscale_service)

            # Get individual metric's suggestions.
            cpu_scale_metrics = self._get_cpu_scale_metrics(autoscale_service)
            memory_scale_metrics = self._get_memory_scale_metrics(autoscale_service)
            allScalingMetrics=[cpu_scale_metrics, memory_scale_metrics]

            # Get final scaling suggestion based on conflict resolution settings.
            scaling_suggestion=self._get_final_scale_suggestion(autoscale_service, cpu_scale_metrics.get_scaling_suggestion(), memory_scale_metrics.get_scaling_suggestion())
            
            # Rescale service based on scaling suggestion.
            self._handle_scaling_suggestion(autoscale_service, scaling_suggestion, allScalingMetrics)

        # Send all accumulated messages.
        self._messagePlatformHandler.send_all_accumulated_messages()


    def _scale_service(self, autoscale_service, replicas, scaling_metrics=[]):
        """
        Scale the specified service to the given number of replicas.

        Parameters:
            autoscale_service (AutoScaleService): An AutoScaleService object.
            replicas (int): The desired number of replicas for the service.
        """
        try:
            # Get the service.
            service = self.client.services.get(autoscale_service.get_service_name())
            
            # Update the service with the new number of replicas.
            success_scaling = service.scale(replicas)

            # Evaluate sclaing success and return state of scaling attempt.    
            if success_scaling:
                successMsg = f"Successfully scaled service <EMPHASIZE_STRING_START_TAG>{autoscale_service.get_service_name()}</EMPHASIZE_STRING_END_TAG> to <EMPHASIZE_STRING_START_TAG>{replicas}</EMPHASIZE_STRING_END_TAG> replicas."
                self._messagePlatformHandler.handle_important_info(successMsg, autoscale_service, scaling_metrics)
            else:
                # Print, log and return error message.
                errorMsg=f"Unknown issue: Could not change service <EMPHASIZE_STRING_START_TAG>{autoscale_service.get_service_name()}</EMPHASIZE_STRING_END_TAG> to <EMPHASIZE_STRING_START_TAG>{replicas}</EMPHASIZE_STRING_END_TAG> replicas."
                self._messagePlatformHandler.handle_error(errorMsg, autoscale_service)
        # Service not found error.
        except docker.errors.NotFound:
            # Print, log and return error message.
            errorMsg=f"Service {autoscale_service.get_service_name()} not found."
            self._messagePlatformHandler.handle_error(errorMsg, autoscale_service)
        # Other error.
        except docker.errors.APIError as e:
            # Print, log and return error message.
            errorMsg=f"Error occurred while scaling service <EMPHASIZE_STRING_START_TAG>{autoscale_service.get_service_name()}</EMPHASIZE_STRING_END_TAG>: <EMPHASIZE_STRING_START_TAG>{e}</EMPHASIZE_STRING_END_TAG>"
            self._messagePlatformHandler.handle_error(errorMsg, autoscale_service)


    def _get_current_replicas(self, service_name):
        """
        Retrieve the current number of replicas for the specified service.

        Parameters:
            service_name (str): The name of the service to query.

        Returns: Amount of replicas.
        """
        # Get the service.
        service = self.client.services.get(service_name)
        
        # Access the replicas attribute of the service.
        current_replicas = service.attrs['Spec']['Mode']['Replicated']['Replicas']
        return int(current_replicas)



    def _get_autoscale_services(self):
        """
        Retrieve all services with autoscale enabled.

        Returns:
            list: A list of dictionaries containing information about autoscale-enabled services.
                Each dictionary contains keys: "name", "minimum_replicas", "maximum_replicas".
        """
        autoscale_services = []
        try:
            services = self.client.services.list()
            for service in services:

                # Check if the label "autoscale" is set to "true"
                serviceLabelHandler = DockerServiceAutoscalerLabelHandler.DockerServiceAutoscalerLabelHandler(service)
                if serviceLabelHandler.is_autoscale_service():
                    isValidAutoscaleService, autoScaleServiceOrErrorMsgArray, verficationWarnings = serviceLabelHandler.get_autoscale_service()
                    if isValidAutoscaleService:
                        autoscale_services.append(autoScaleServiceOrErrorMsgArray)
                    else:
                        # Prepare Error message for invalid autoscale labels.
                        allVerficationWarningString = " ,  ".join(autoScaleServiceOrErrorMsgArray)
                        service_name=service.attrs["Spec"]["Name"]
                        invalidAutoScaleLabelMsg = f"Invalid autoscale labels for service <EMPHASIZE_STRING_START_TAG>{service_name}</EMPHASIZE_STRING_END_TAG>: "
                        invalidAutoScaleLabelMsg += allVerficationWarningString
                        
                        # Log Error.
                        self._messagePlatformHandler.handle_error(invalidAutoScaleLabelMsg)

                    # Are there any warnings?
                    if len(verficationWarnings) > 0:
                    # Prepare Warning message for autoscale labels.
                        allVerficationWarningString = " ,  ".join(verficationWarnings)
                        service_name=service.attrs["Spec"]["Name"]
                        combinedWarningMessage = f"Warnings concerning autoscale labels for service <EMPHASIZE_STRING_START_TAG>{service_name}</EMPHASIZE_STRING_END_TAG>: "
                        combinedWarningMessage += allVerficationWarningString

                        # Log warning.
                        self._messagePlatformHandler.handle_warning(combinedWarningMessage)

            return autoscale_services
        except docker.errors.APIError as e:
            errorMsg=f"Error occurred while fetching autoscale services: <EMPHASIZE_STRING_START_TAG>{e}</EMPHASIZE_STRING_END_TAG>"
            self._messagePlatformHandler.handle_error(errorMsg)
            return autoscale_services


    def _get_cpu_scale_metrics(self, autoscale_service):
        """
        Gets the scaling suggestion based on cpu thresholds, settings and values.

        Returns:
            ScalingMetrics.
        """
        # Defaults.
        cpu_scale_suggestion = ScalingSuggestion.KEEP_REPLICAS
        scaling_conflict_resolution=autoscale_service.get_scaling_conflict_resolution()

        # Prepare return class.
        cpuScalingMetrics = ScalingMetrics.ScalingMetrics(autoscale_service, ScalingMetricName.CPU, autoscale_service.is_scaling_based_on_cpu_enabled())

        # Cpu based scaling enabled?
        if autoscale_service.is_scaling_based_on_cpu_enabled():

            # CPU Upscale.
            current_cpu_upscale_value=prometheusConnector.get_custom_cpu_metric(autoscale_service.get_service_name(), autoscale_service.get_cpu_upscale_time_duration())
            verboseInfo = f"<EMPHASIZE_STRING_START_TAG>{autoscale_service.get_service_name()}</EMPHASIZE_STRING_END_TAG> current_cpu_upscale_value: <EMPHASIZE_STRING_START_TAG>{current_cpu_upscale_value}</EMPHASIZE_STRING_END_TAG> (<EMPHASIZE_STRING_START_TAG>{converterUtils.float_to_percentage(current_cpu_upscale_value)}</EMPHASIZE_STRING_END_TAG>), using time_duration:  <EMPHASIZE_STRING_START_TAG>{autoscale_service.get_cpu_upscale_time_duration()}</EMPHASIZE_STRING_END_TAG>"
            self._messagePlatformHandler.handle_verbose_info(verboseInfo, autoscale_service)

            # Upscaling based on CPU?
            if current_cpu_upscale_value > autoscale_service.get_cpu_upscale_threshold():
                cpu_scale_suggestion = ScalingSuggestion.SCALE_UP
            
            # Upscale suggestion verbose info.
            verboseInfo = f"<EMPHASIZE_STRING_START_TAG>{autoscale_service.get_service_name()}</EMPHASIZE_STRING_END_TAG> cpu upscale threshold: <EMPHASIZE_STRING_START_TAG>{autoscale_service.get_cpu_upscale_threshold()}</EMPHASIZE_STRING_END_TAG> (<EMPHASIZE_STRING_START_TAG>{converterUtils.float_to_percentage(autoscale_service.get_cpu_upscale_threshold())}</EMPHASIZE_STRING_END_TAG>), cpu upscale suggestion: <EMPHASIZE_STRING_START_TAG>{cpu_scale_suggestion}</EMPHASIZE_STRING_END_TAG>"
            self._messagePlatformHandler.handle_verbose_info(verboseInfo, autoscale_service)

            # CPU Downscale.
            current_cpu_downscale_value=prometheusConnector.get_custom_cpu_metric(autoscale_service.get_service_name(), autoscale_service.get_cpu_downscale_time_duration())
            verboseInfo = f"<EMPHASIZE_STRING_START_TAG>{autoscale_service.get_service_name()}</EMPHASIZE_STRING_END_TAG> current_cpu_downscale_value: <EMPHASIZE_STRING_START_TAG>{current_cpu_downscale_value}</EMPHASIZE_STRING_END_TAG> (<EMPHASIZE_STRING_START_TAG>{converterUtils.float_to_percentage(current_cpu_downscale_value)}</EMPHASIZE_STRING_END_TAG>), using time_duration:  <EMPHASIZE_STRING_START_TAG>{autoscale_service.get_cpu_downscale_time_duration()}</EMPHASIZE_STRING_END_TAG>"
            self._messagePlatformHandler.handle_verbose_info(verboseInfo, autoscale_service)

            verboseInfo = f"<EMPHASIZE_STRING_START_TAG>{autoscale_service.get_service_name()}</EMPHASIZE_STRING_END_TAG> cpu downscale threshold: <EMPHASIZE_STRING_START_TAG>{autoscale_service.get_cpu_downscale_threshold()}</EMPHASIZE_STRING_END_TAG> (<EMPHASIZE_STRING_START_TAG>{converterUtils.float_to_percentage(autoscale_service.get_cpu_downscale_threshold())}</EMPHASIZE_STRING_END_TAG>)"
            self._messagePlatformHandler.handle_verbose_info(verboseInfo, autoscale_service)
            
            # Downscaling based on CPU?
            if current_cpu_downscale_value < autoscale_service.get_cpu_downscale_threshold():

                if cpu_scale_suggestion == ScalingSuggestion.KEEP_REPLICAS:
                    cpu_scale_suggestion = ScalingSuggestion.SCALE_DOWN
                    # Downscale verbse info.
                    verboseInfo = f"<EMPHASIZE_STRING_START_TAG>{autoscale_service.get_service_name()}</EMPHASIZE_STRING_END_TAG> cpu downscale suggestion: <EMPHASIZE_STRING_START_TAG>{cpu_scale_suggestion}</EMPHASIZE_STRING_END_TAG>"
                    self._messagePlatformHandler.handle_verbose_info(verboseInfo, autoscale_service)
                else:
                    # Conflict resolution.
                    if scaling_conflict_resolution == ScalingConflictResolution.KEEP_REPLICAS:
                        cpu_scale_suggestion = ScalingSuggestion.KEEP_REPLICAS
                    elif scaling_conflict_resolution == ScalingConflictResolution.SCALE_DOWN:
                        cpu_scale_suggestion = ScalingSuggestion.SCALE_DOWN
                    elif scaling_conflict_resolution == ScalingConflictResolution.SCALE_UP:
                        cpu_scale_suggestion = ScalingSuggestion.SCALE_UP
                    else:
                        cpu_scale_suggestion = ScalingSuggestion.KEEP_REPLICAS
                    
                    # Conflict resolution verbse info.
                    verboseInfo = f"<EMPHASIZE_STRING_START_TAG>{autoscale_service.get_service_name()}</EMPHASIZE_STRING_END_TAG> ScalingConflictResolution: <EMPHASIZE_STRING_START_TAG>{scaling_conflict_resolution}</EMPHASIZE_STRING_END_TAG>"
                    self._messagePlatformHandler.handle_verbose_info(verboseInfo, autoscale_service)

            # Final cpu decision verbose info.
            verboseInfo = f"<EMPHASIZE_STRING_START_TAG>{autoscale_service.get_service_name()}</EMPHASIZE_STRING_END_TAG> Final CPU Scaling Suggestion: <EMPHASIZE_STRING_START_TAG>{cpu_scale_suggestion}</EMPHASIZE_STRING_END_TAG>"
            self._messagePlatformHandler.handle_verbose_info(verboseInfo, autoscale_service)

            # Setting values to return class.
            cpuScalingMetrics.set_upscale_threshold(autoscale_service.get_cpu_upscale_threshold())
            cpuScalingMetrics.set_upscale_value(current_cpu_upscale_value)
            cpuScalingMetrics.set_downscale_threshold(autoscale_service.get_cpu_downscale_threshold())
            cpuScalingMetrics.set_downscale_value(current_cpu_downscale_value)
            cpuScalingMetrics.set_conflict_resolution(scaling_conflict_resolution)
            cpuScalingMetrics.set_scaling_suggestion(cpu_scale_suggestion)
            
        else:
            # Verbose info cpu based scaling not enabled.
            verboseInfo = f"<EMPHASIZE_STRING_START_TAG>{autoscale_service.get_service_name()}</EMPHASIZE_STRING_END_TAG> CPU based scaling not enabled"
            self._messagePlatformHandler.handle_verbose_info(verboseInfo, autoscale_service)
        
        # Return scaling suggestion.
        return cpuScalingMetrics
    

    def _get_memory_scale_metrics(self, autoscale_service):
        """
        Gets the scaling suggestion based on memory thresholds, settings and values.

        Returns:
            ScalingMetrics.
        """
        # Defaults.
        memory_scale_suggestion = ScalingSuggestion.KEEP_REPLICAS
        scaling_conflict_resolution=autoscale_service.get_scaling_conflict_resolution()

        # Prepare return class.
        memoryScalingMetrics = ScalingMetrics.ScalingMetrics(autoscale_service, ScalingMetricName.MEMORY, autoscale_service.is_scaling_based_on_memory_enabled())

        # Is memory based scaling enabled?
        if autoscale_service.is_scaling_based_on_memory_enabled():

            # Get current value.
            current_memory_value=prometheusConnector.get_custom_memory_metric(autoscale_service.get_service_name())
            verboseInfo = f"<EMPHASIZE_STRING_START_TAG>{autoscale_service.get_service_name()}</EMPHASIZE_STRING_END_TAG> current_memory_value: <EMPHASIZE_STRING_START_TAG>{current_memory_value}</EMPHASIZE_STRING_END_TAG> (<EMPHASIZE_STRING_START_TAG>{converterUtils.bytes_to_human_readable_storage(current_memory_value)}</EMPHASIZE_STRING_END_TAG>)"
            self._messagePlatformHandler.handle_verbose_info(verboseInfo, autoscale_service)

            # Upscaling based on Memory?
            if current_memory_value > autoscale_service.get_memory_upscale_threshold():
                memory_scale_suggestion = ScalingSuggestion.SCALE_UP

            # Upscale suggestion verbose info.
            verboseInfo = f"<EMPHASIZE_STRING_START_TAG>{autoscale_service.get_service_name()}</EMPHASIZE_STRING_END_TAG> memory upscale threshold: <EMPHASIZE_STRING_START_TAG>{autoscale_service.get_memory_upscale_threshold()}</EMPHASIZE_STRING_END_TAG> (<EMPHASIZE_STRING_START_TAG>{converterUtils.bytes_to_human_readable_storage(autoscale_service.get_memory_upscale_threshold())}</EMPHASIZE_STRING_END_TAG>), memory upscale suggestion: <EMPHASIZE_STRING_START_TAG>{memory_scale_suggestion}</EMPHASIZE_STRING_END_TAG>"
            self._messagePlatformHandler.handle_verbose_info(verboseInfo, autoscale_service)

            # Downscale threshold verbose info.
            verboseInfo = f"<EMPHASIZE_STRING_START_TAG>{autoscale_service.get_service_name()}</EMPHASIZE_STRING_END_TAG> memory downscale threshold: <EMPHASIZE_STRING_START_TAG>{autoscale_service.get_memory_downscale_threshold()}</EMPHASIZE_STRING_END_TAG> (<EMPHASIZE_STRING_START_TAG>{converterUtils.bytes_to_human_readable_storage(autoscale_service.get_memory_downscale_threshold())}</EMPHASIZE_STRING_END_TAG>)"
            self._messagePlatformHandler.handle_verbose_info(verboseInfo, autoscale_service)
            
            # Downscaling based on Memory?
            if current_memory_value < autoscale_service.get_memory_downscale_threshold():
                if memory_scale_suggestion == ScalingSuggestion.KEEP_REPLICAS:
                    memory_scale_suggestion = ScalingSuggestion.SCALE_DOWN

                    # Downscale verbse info.
                    verboseInfo = f"<EMPHASIZE_STRING_START_TAG>{autoscale_service.get_service_name()}</EMPHASIZE_STRING_END_TAG> memory downscale suggestion: <EMPHASIZE_STRING_START_TAG>{memory_scale_suggestion}</EMPHASIZE_STRING_END_TAG>"
                    self._messagePlatformHandler.handle_verbose_info(verboseInfo, autoscale_service)
                else:
                    # Conflict resolution.
                    if scaling_conflict_resolution == ScalingConflictResolution.KEEP_REPLICAS:
                        memory_scale_suggestion = ScalingSuggestion.KEEP_REPLICAS
                    elif scaling_conflict_resolution == ScalingConflictResolution.SCALE_DOWN:
                        memory_scale_suggestion = ScalingSuggestion.SCALE_DOWN
                    elif scaling_conflict_resolution == ScalingConflictResolution.SCALE_UP:
                        memory_scale_suggestion = ScalingSuggestion.SCALE_UP
                    else:
                        memory_scale_suggestion = ScalingSuggestion.KEEP_REPLICAS
                    
                    # Conflict resolution verbse info.
                    verboseInfo = f"<EMPHASIZE_STRING_START_TAG>{autoscale_service.get_service_name()}</EMPHASIZE_STRING_END_TAG> ScalingConflictResolution: <EMPHASIZE_STRING_START_TAG>{scaling_conflict_resolution}</EMPHASIZE_STRING_END_TAG>"
                    self._messagePlatformHandler.handle_verbose_info(verboseInfo, autoscale_service)

            # Final memory decision verbose info.
            verboseInfo = f"<EMPHASIZE_STRING_START_TAG>{autoscale_service.get_service_name()}</EMPHASIZE_STRING_END_TAG> Final Memory Scaling Suggestion: <EMPHASIZE_STRING_START_TAG>{memory_scale_suggestion}</EMPHASIZE_STRING_END_TAG>"
            self._messagePlatformHandler.handle_verbose_info(verboseInfo, autoscale_service)

            # Setting values to return class.
            memoryScalingMetrics.set_upscale_threshold(autoscale_service.get_memory_upscale_threshold())
            memoryScalingMetrics.set_upscale_value(current_memory_value)
            memoryScalingMetrics.set_downscale_threshold(autoscale_service.get_memory_downscale_threshold())
            memoryScalingMetrics.set_downscale_value(current_memory_value)
            memoryScalingMetrics.set_conflict_resolution(scaling_conflict_resolution)
            memoryScalingMetrics.set_scaling_suggestion(memory_scale_suggestion)
        else:
            # Verbose info memory based scaling not enabled.
            verboseInfo = f"<EMPHASIZE_STRING_START_TAG>{autoscale_service.get_service_name()}</EMPHASIZE_STRING_END_TAG> Memory based scaling not enabled"
            self._messagePlatformHandler.handle_verbose_info(verboseInfo, autoscale_service)
        
        # Return scaling suggestion.
        return memoryScalingMetrics
    

    
    def _get_final_scale_suggestion(self, autoscale_service, cpu_scale_suggestion, memory_scale_suggestion):
        """
        Gets the scaling suggestion based on ScalingConflictResolution settings and priorly retrieved individual metric's suggestions.

        Returns:
            ScalingSuggestion.
        """
        # Conflict Resolution setting.
        scaling_conflict_resolution=autoscale_service.get_scaling_conflict_resolution()

        # Logging verbose information about final scaling suggestion.
        verbose_info = f"Calculating final scaling suggestion for service: <EMPHASIZE_STRING_START_TAG>{autoscale_service.get_service_name()}</EMPHASIZE_STRING_END_TAG>, CPU Suggestion: <EMPHASIZE_STRING_START_TAG>{cpu_scale_suggestion}</EMPHASIZE_STRING_END_TAG>, Memory Suggestion: <EMPHASIZE_STRING_START_TAG>{memory_scale_suggestion}</EMPHASIZE_STRING_END_TAG>, Conflict Resolution: <EMPHASIZE_STRING_START_TAG>{scaling_conflict_resolution}</EMPHASIZE_STRING_END_TAG>"
        self._messagePlatformHandler.handle_verbose_info(verbose_info, autoscale_service)

        # Memory and CPU enabled.
        if autoscale_service.is_scaling_based_on_cpu_enabled() and autoscale_service.is_scaling_based_on_memory_enabled():

            # Logging verbose information about final scaling suggestion.
            verbose_info = f"Memory and cpu autoscaling enabled for <EMPHASIZE_STRING_START_TAG>{autoscale_service.get_service_name()}</EMPHASIZE_STRING_END_TAG>"
            self._messagePlatformHandler.handle_verbose_info(verbose_info, autoscale_service)

            if cpu_scale_suggestion == memory_scale_suggestion:
                scaling_suggestion = cpu_scale_suggestion

                # Logging verbose information about final scaling suggestion.
                verbose_info = f"All suggestions are the same for <EMPHASIZE_STRING_START_TAG>{autoscale_service.get_service_name()}</EMPHASIZE_STRING_END_TAG>: using <EMPHASIZE_STRING_START_TAG>{scaling_suggestion}</EMPHASIZE_STRING_END_TAG> as final suggestion"
                self._messagePlatformHandler.handle_verbose_info(verbose_info, autoscale_service)
            else:
                # Conflict resolution.
                if scaling_conflict_resolution == ScalingConflictResolution.KEEP_REPLICAS:
                    scaling_suggestion = ScalingSuggestion.KEEP_REPLICAS
                elif scaling_conflict_resolution == ScalingConflictResolution.SCALE_DOWN:
                    if cpu_scale_suggestion == ScalingSuggestion.SCALE_DOWN or cpu_scale_suggestion == ScalingSuggestion.SCALE_DOWN:
                        scaling_suggestion = ScalingSuggestion.SCALE_DOWN
                    else:
                        scaling_suggestion = ScalingSuggestion.KEEP_REPLICAS
                elif scaling_conflict_resolution == ScalingConflictResolution.SCALE_UP:
                    if cpu_scale_suggestion == ScalingSuggestion.SCALE_UP or cpu_scale_suggestion == ScalingSuggestion.SCALE_UP:
                        scaling_suggestion = ScalingSuggestion.SCALE_UP
                    else:
                        scaling_suggestion = ScalingSuggestion.KEEP_REPLICAS
                elif scaling_conflict_resolution == ScalingConflictResolution.ADHERE_TO_MEMORY:
                    scaling_suggestion = memory_scale_suggestion
                elif scaling_conflict_resolution == ScalingConflictResolution.ADHERE_TO_CPU:
                    scaling_suggestion = cpu_scale_suggestion
                else:
                    scaling_suggestion = ScalingSuggestion.KEEP_REPLICAS

                    
                # Logging verbose information about final scaling suggestion.
                verbose_info = f"Result of conflict resolution for <EMPHASIZE_STRING_START_TAG>{autoscale_service.get_service_name()}</EMPHASIZE_STRING_END_TAG>: using <EMPHASIZE_STRING_START_TAG>{scaling_suggestion}</EMPHASIZE_STRING_END_TAG> as final suggestion"
                self._messagePlatformHandler.handle_verbose_info(verbose_info, autoscale_service)

        # Just CPU enabled.
        elif autoscale_service.is_scaling_based_on_cpu_enabled() and not autoscale_service.is_scaling_based_on_memory_enabled():
                scaling_suggestion = cpu_scale_suggestion
                
                # Logging verbose information about final scaling suggestion.
                verbose_info = f"Only cpu autoscaling enabled for <EMPHASIZE_STRING_START_TAG>{autoscale_service.get_service_name()}</EMPHASIZE_STRING_END_TAG>, Using cpu suggestion: <EMPHASIZE_STRING_START_TAG>{scaling_suggestion}</EMPHASIZE_STRING_END_TAG> as final suggestion"
                self._messagePlatformHandler.handle_verbose_info(verbose_info, autoscale_service)
                
        # Just Memory enabled.
        elif not autoscale_service.is_scaling_based_on_cpu_enabled() and autoscale_service.is_scaling_based_on_memory_enabled():
                scaling_suggestion = memory_scale_suggestion
                
                # Logging verbose information about final scaling suggestion.
                verbose_info = f"Only memory autoscaling enabled for <EMPHASIZE_STRING_START_TAG>{autoscale_service.get_service_name()}</EMPHASIZE_STRING_END_TAG>, Using memory suggestion: <EMPHASIZE_STRING_START_TAG>{scaling_suggestion}</EMPHASIZE_STRING_END_TAG> as final suggestion"
                self._messagePlatformHandler.handle_verbose_info(verbose_info, autoscale_service)
        
        # Return scaling suggestion.
        return scaling_suggestion
    
    
    def _handle_scaling_suggestion(self, autoscale_service, scaling_suggestion, scaling_metrics=[]):
        """
        Scales the service based on the scaling suggestion.

        Checks if within min and max replicas.

        """
        # Current amount of replicas already running.
        current_amount_replicas = self._get_current_replicas(autoscale_service.get_service_name())
        verboseInfo = f"<EMPHASIZE_STRING_START_TAG>{autoscale_service.get_service_name()}</EMPHASIZE_STRING_END_TAG> Before rescaling amount of replicas: <EMPHASIZE_STRING_START_TAG>{current_amount_replicas}</EMPHASIZE_STRING_END_TAG>"
        self._messagePlatformHandler.handle_verbose_info(verboseInfo, autoscale_service)

        # Min and max amount of replicas.
        min_replicas = autoscale_service.get_minimum_replicas()
        max_replicas = autoscale_service.get_maximum_replicas()
        verboseInfo = f"<EMPHASIZE_STRING_START_TAG>{autoscale_service.get_service_name()}</EMPHASIZE_STRING_END_TAG> Minimum replicas: <EMPHASIZE_STRING_START_TAG>{min_replicas}</EMPHASIZE_STRING_END_TAG>, Maximum replicas: <EMPHASIZE_STRING_START_TAG>{max_replicas}</EMPHASIZE_STRING_END_TAG>"
        self._messagePlatformHandler.handle_verbose_info(verboseInfo, autoscale_service)

        # Unchecked incrementation or decrementation of service.
        new_amount_replicas = current_amount_replicas
        if scaling_suggestion == ScalingSuggestion.SCALE_DOWN:
            new_amount_replicas = current_amount_replicas - 1
        elif scaling_suggestion == ScalingSuggestion.SCALE_UP:
            new_amount_replicas = current_amount_replicas + 1
        verboseInfo = f"<EMPHASIZE_STRING_START_TAG>{autoscale_service.get_service_name()}</EMPHASIZE_STRING_END_TAG> Unchecked new replicas based on scaling suggestion: <EMPHASIZE_STRING_START_TAG>{new_amount_replicas}</EMPHASIZE_STRING_END_TAG>"
        self._messagePlatformHandler.handle_verbose_info(verboseInfo, autoscale_service)
        
        # Ensure scaling is within limits.
        if new_amount_replicas < min_replicas:
            new_amount_replicas = min_replicas
        if new_amount_replicas > max_replicas:
            new_amount_replicas = max_replicas
        verboseInfo = f"<EMPHASIZE_STRING_START_TAG>{autoscale_service.get_service_name()}</EMPHASIZE_STRING_END_TAG> New replicas after adhering to min and max replica thresholds: <EMPHASIZE_STRING_START_TAG>{new_amount_replicas}</EMPHASIZE_STRING_END_TAG>"
        self._messagePlatformHandler.handle_verbose_info(verboseInfo, autoscale_service)

        # Does amount of replicas have to be changed?
        if new_amount_replicas != current_amount_replicas:
            self._scale_service(autoscale_service, new_amount_replicas, scaling_metrics)
        else:
            # Info about keeping replicas.
            keeping_replica_msg = f"Keeping replicas of service <EMPHASIZE_STRING_START_TAG>{autoscale_service.get_service_name()}</EMPHASIZE_STRING_END_TAG> at <EMPHASIZE_STRING_START_TAG>{current_amount_replicas}</EMPHASIZE_STRING_END_TAG>"
            self._messagePlatformHandler.handle_information(keeping_replica_msg, autoscale_service)
