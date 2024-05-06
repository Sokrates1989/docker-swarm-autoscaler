# Connect to docker via python api.
import docker

# Own class to get autoscale services from labels.
import dockerServiceAutoscalerLabelHandler as DockerServiceAutoscalerLabelHandler

# For retrieving container/ service metrics via prometheus.
import prometheusConnector as PrometheusConnector
prometheusConnector = PrometheusConnector.PrometheusConnector()

# Label definitions.
from label_definitions import ScalingConflictResolution, ScalingSuggestion

# Logger.
import logger as Logger
logger = Logger.Logger()

# Conversion.
import converterUtils

class DockerServiceScaler:
    """
    A class for scaling Docker services and retrieving their current replicas.

    This class provides methods to scale Docker services to a specified number of replicas
    and retrieve the current number of replicas for a given service.

    Methods:
        scale_service: Scale the specified service to the given number of replicas.
        get_current_replicas: Retrieve the current number of replicas for the specified service.
    """

    def __init__(self):
        self.client = docker.from_env()

    def _scale_service(self, autoscale_service, replicas):
        """
        Scale the specified service to the given number of replicas.

        Parameters:
            autoscale_service (AutoScaleService): An AutoScaleService object.
            replicas (int): The desired number of replicas for the service.

        Returns:
            None
        """
        try:
            # Get the service.
            service = self.client.services.get(autoscale_service.get_service_name())
            
            # Update the service with the new number of replicas.
            success_scaling = service.scale(replicas)

            # Evaluate sclaing success and return state of scaling attempt.    
            if success_scaling:
                successMsg = f"Successfully scaled service \"{autoscale_service.get_service_name()}\" to \"{replicas}\" replicas."
                logger.information(successMsg, autoscale_service.get_service_log_level())
                return True
            else:
                # Print, log and return error message.
                errorMsg=f"Unknown issue: Could not change service \"{autoscale_service.get_service_name()}\" to \"{replicas}\" replicas."
                logger.error(errorMsg, autoscale_service.get_service_log_level())
                return errorMsg
        # Service not found error.
        except docker.errors.NotFound:
            # Print, log and return error message.
            errorMsg=f"Service {autoscale_service.get_service_name()} not found."
            logger.error(errorMsg, autoscale_service.get_service_log_level())
            return errorMsg
        # Other error.
        except docker.errors.APIError as e:
            # Print, log and return error message.
            errorMsg=f"Error occurred while scaling service \"{autoscale_service.get_service_name()}\": {e}"
            logger.error(errorMsg, autoscale_service.get_service_log_level())
            return errorMsg

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
                    isValidAutoscaleService, autoScaleServiceOrErrorMsgArray = serviceLabelHandler.get_autoscale_service()
                    if isValidAutoscaleService:
                        autoscale_services.append(autoScaleServiceOrErrorMsgArray)
                    else:
                        # Prepare Error message for invalid autoscale labels.
                        allVerficationErrorString = " ,  ".join(autoScaleServiceOrErrorMsgArray)
                        service_name=service.attrs["Spec"]["Name"]
                        invalidAutoScaleLabelMsg = f"Invalid autoscale labels for service {service_name}: "
                        invalidAutoScaleLabelMsg += allVerficationErrorString
                        
                        # Log Error.
                        logger.error(invalidAutoScaleLabelMsg)
            return autoscale_services
        except docker.errors.APIError as e:
            errorMsg=f"Error occurred while fetching autoscale services: {e}"
            logger.error(errorMsg)
            return autoscale_services
        

    def auto_scale_services(self):
        """
        Look for services with autoscale enabled and then scale based on prometheus metrics.
        """
        # Loop through all autoscale services.
        autoscale_services = self._get_autoscale_services()
        for autoscale_service in autoscale_services:

            # Get individual metric's suggestions.
            cpu_scale_suggestion = self._get_cpu_scale_suggestion(autoscale_service)
            memory_scale_suggestion = self._get_memory_scale_suggestion(autoscale_service)

            # Get final scaling suggestion based on conflict resolution settings.
            scaling_suggestion=self._get_final_scale_suggestion(autoscale_service, cpu_scale_suggestion, memory_scale_suggestion)
            
            # Rescale service based on scaling suggestion.
            self._handle_scaling_suggestion(autoscale_service, scaling_suggestion)


    def _get_cpu_scale_suggestion(self, autoscale_service):
        """
        Gets the scaling suggestion based on cpu thresholds, settings and values.

        Returns:
            ScalingSuggestion.
        """
        # Defaults.
        cpu_scale_suggestion = ScalingSuggestion.KEEP_REPLICAS
        scaling_conflict_resolution=autoscale_service.get_scaling_conflict_resolution()

        # Cpu based scaling enabled?
        if autoscale_service.is_scaling_based_on_cpu_enabled():

            # CPU Upscale.
            current_cpu_upscale_value=prometheusConnector.get_custom_cpu_metric(autoscale_service.get_service_name(), autoscale_service.get_cpu_upscale_time_duration())
            verboseInfo = f"\"{autoscale_service.get_service_name()}\" current_cpu_upscale_value: \"{current_cpu_upscale_value}\"(\"{converterUtils.float_to_percentage(current_cpu_upscale_value)}\"), using time_duration:  \"{autoscale_service.get_cpu_upscale_time_duration()}\""
            logger.verboseInfo(verboseInfo, autoscale_service.get_service_log_level())

            # Upscaling based on CPU?
            if current_cpu_upscale_value > autoscale_service.get_cpu_upscale_threshold():
                cpu_scale_suggestion = ScalingSuggestion.SCALE_UP
            
            # Upscale suggestion verbose info.
            verboseInfo = f"\"{autoscale_service.get_service_name()}\" cpu upscale threshold: \"{autoscale_service.get_cpu_upscale_threshold()}\"(\"{converterUtils.float_to_percentage(autoscale_service.get_cpu_upscale_threshold())}\"), cpu upscale suggestion: \"{cpu_scale_suggestion}\""
            logger.verboseInfo(verboseInfo, autoscale_service.get_service_log_level())

            # CPU Downscale.
            current_cpu_downscale_value=prometheusConnector.get_custom_cpu_metric(autoscale_service.get_service_name(), autoscale_service.get_cpu_downscale_time_duration())
            verboseInfo = f"\"{autoscale_service.get_service_name()}\" current_cpu_downscale_value: \"{current_cpu_downscale_value}\"(\"{converterUtils.float_to_percentage(current_cpu_downscale_value)}\"), using time_duration:  \"{autoscale_service.get_cpu_downscale_time_duration()}\""
            logger.verboseInfo(verboseInfo, autoscale_service.get_service_log_level())

            verboseInfo = f"\"{autoscale_service.get_service_name()}\" cpu downscale threshold: \"{autoscale_service.get_cpu_downscale_threshold()}\"(\"{converterUtils.float_to_percentage(autoscale_service.get_cpu_downscale_threshold())}\")"
            logger.verboseInfo(verboseInfo, autoscale_service.get_service_log_level())
            
            # Downscaling based on CPU?
            if current_cpu_downscale_value < autoscale_service.get_cpu_downscale_threshold():

                if cpu_scale_suggestion == ScalingSuggestion.KEEP_REPLICAS:
                    cpu_scale_suggestion = ScalingSuggestion.SCALE_DOWN
                    # Downscale verbse info.
                    verboseInfo = f"\"{autoscale_service.get_service_name()}\" cpu downscale suggestion: \"{cpu_scale_suggestion}\""
                    logger.verboseInfo(verboseInfo, autoscale_service.get_service_log_level())
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
                    verboseInfo = f"\"{autoscale_service.get_service_name()}\" ScalingConflictResolution: \"{scaling_conflict_resolution}\""
                    logger.verboseInfo(verboseInfo, autoscale_service.get_service_log_level())

            # Final cpu dcision verbose info.
            verboseInfo = f"\"{autoscale_service.get_service_name()}\" Final CPU Scaling Suggestion: \"{cpu_scale_suggestion}\""
            logger.verboseInfo(verboseInfo, autoscale_service.get_service_log_level())
        else:
            # Verbose info cpu based scaling not enabled.
            verboseInfo = f"\"{autoscale_service.get_service_name()}\" CPU based scaling not enabled"
            logger.verboseInfo(verboseInfo, autoscale_service.get_service_log_level())
        
        # Return scaling suggestion.
        return cpu_scale_suggestion
    

    def _get_memory_scale_suggestion(self, autoscale_service):
        """
        Gets the scaling suggestion based on memory thresholds, settings and values.

        Returns:
            ScalingSuggestion.
        """
        # Defaults.
        memory_scale_suggestion = ScalingSuggestion.KEEP_REPLICAS
        scaling_conflict_resolution=autoscale_service.get_scaling_conflict_resolution()

        # Is memory based scaling enabled?
        if autoscale_service.is_scaling_based_on_memory_enabled():

            # Get current value.
            current_memory_value=prometheusConnector.get_custom_memory_metric(autoscale_service.get_service_name())
            verboseInfo = f"\"{autoscale_service.get_service_name()}\" current_memory_value: \"{current_memory_value}\"(\"{converterUtils.bytes_to_human_readable_storage(current_memory_value)}\")"
            logger.verboseInfo(verboseInfo, autoscale_service.get_service_log_level())

            # Upscaling based on Memory?
            if current_memory_value > autoscale_service.get_memory_upscale_threshold():
                memory_scale_suggestion = ScalingSuggestion.SCALE_UP

            # Upscale suggestion verbose info.
            verboseInfo = f"\"{autoscale_service.get_service_name()}\" memory upscale threshold: \"{autoscale_service.get_memory_upscale_threshold()}\"(\"{converterUtils.bytes_to_human_readable_storage(autoscale_service.get_memory_upscale_threshold())}\"), memory upscale suggestion: \"{memory_scale_suggestion}\""
            logger.verboseInfo(verboseInfo, autoscale_service.get_service_log_level())

            # Downscale threshold verbose info.
            verboseInfo = f"\"{autoscale_service.get_service_name()}\" memory downscale threshold: \"{autoscale_service.get_memory_downscale_threshold()}\"(\"{converterUtils.bytes_to_human_readable_storage(autoscale_service.get_memory_downscale_threshold())}\")"
            logger.verboseInfo(verboseInfo, autoscale_service.get_service_log_level())
            
            # Downscaling based on Memory?
            if current_memory_value < autoscale_service.get_memory_downscale_threshold():
                if memory_scale_suggestion == ScalingSuggestion.KEEP_REPLICAS:
                    memory_scale_suggestion = ScalingSuggestion.SCALE_DOWN

                    # Downscale verbse info.
                    verboseInfo = f"\"{autoscale_service.get_service_name()}\" memory downscale suggestion: \"{memory_scale_suggestion}\""
                    logger.verboseInfo(verboseInfo, autoscale_service.get_service_log_level())
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
                    verboseInfo = f"\"{autoscale_service.get_service_name()}\" ScalingConflictResolution: \"{scaling_conflict_resolution}\""
                    logger.verboseInfo(verboseInfo, autoscale_service.get_service_log_level())

            # Final memory decision verbose info.
            verboseInfo = f"\"{autoscale_service.get_service_name()}\" Final Memory Scaling Suggestion: \"{memory_scale_suggestion}\""
            logger.verboseInfo(verboseInfo, autoscale_service.get_service_log_level())
        else:
            # Verbose info memory based scaling not enabled.
            verboseInfo = f"\"{autoscale_service.get_service_name()}\" Memory based scaling not enabled"
            logger.verboseInfo(verboseInfo, autoscale_service.get_service_log_level())
        
        # Return scaling suggestion.
        return memory_scale_suggestion
    

    
    def _get_final_scale_suggestion(self, autoscale_service, cpu_scale_suggestion, memory_scale_suggestion):
        """
        Gets the scaling suggestion based on ScalingConflictResolution settings and priorly retrieved individual metric's suggestions.

        Returns:
            ScalingSuggestion.
        """
        # Conflict Resolution setting.
        scaling_conflict_resolution=autoscale_service.get_scaling_conflict_resolution()

        # Logging verbose information about final scaling suggestion.
        verbose_info = f"Calculating final scaling suggestion for service: \"{autoscale_service.get_service_name()}\", CPU Suggestion: \"{cpu_scale_suggestion}\", Memory Suggestion: \"{memory_scale_suggestion}\", Conflict Resolution: \"{scaling_conflict_resolution}\""
        logger.verboseInfo(verbose_info, autoscale_service.get_service_log_level())

        # Memory and CPU enabled.
        if autoscale_service.is_scaling_based_on_cpu_enabled() and autoscale_service.is_scaling_based_on_memory_enabled():

            # Logging verbose information about final scaling suggestion.
            verbose_info = f"Memory and cpu autoscaling enabled for \"{autoscale_service.get_service_name()}\""
            logger.verboseInfo(verbose_info, autoscale_service.get_service_log_level())

            if cpu_scale_suggestion == memory_scale_suggestion:
                scaling_suggestion = cpu_scale_suggestion

                # Logging verbose information about final scaling suggestion.
                verbose_info = f"All suggestions are the same for \"{autoscale_service.get_service_name()}\": using \"{scaling_suggestion}\" as final suggestion"
                logger.verboseInfo(verbose_info, autoscale_service.get_service_log_level())
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
                verbose_info = f"Result of conflict resolution for \"{autoscale_service.get_service_name()}\": using \"{scaling_suggestion}\" as final suggestion"
                logger.verboseInfo(verbose_info, autoscale_service.get_service_log_level())

        # Just CPU enabled.
        elif autoscale_service.is_scaling_based_on_cpu_enabled() and not autoscale_service.is_scaling_based_on_memory_enabled():
                scaling_suggestion = cpu_scale_suggestion
                
                # Logging verbose information about final scaling suggestion.
                verbose_info = f"Only cpu autoscaling enabled for \"{autoscale_service.get_service_name()}\", Using cpu suggestion: \"{scaling_suggestion}\" as final suggestion"
                logger.verboseInfo(verbose_info, autoscale_service.get_service_log_level())
                
        # Just Memory enabled.
        elif not autoscale_service.is_scaling_based_on_cpu_enabled() and autoscale_service.is_scaling_based_on_memory_enabled():
                scaling_suggestion = memory_scale_suggestion
                
                # Logging verbose information about final scaling suggestion.
                verbose_info = f"Only memory autoscaling enabled for \"{autoscale_service.get_service_name()}\", Using memory suggestion: \"{scaling_suggestion}\" as final suggestion"
                logger.verboseInfo(verbose_info, autoscale_service.get_service_log_level())
        
        # Return scaling suggestion.
        return scaling_suggestion
    
    
    def _handle_scaling_suggestion(self, autoscale_service, scaling_suggestion):
        """
        Scales the service based on the scaling suggestion.

        Checks if within min and max replicas.

        """
        # Current amount of replicas already running.
        current_amount_replicas = self._get_current_replicas(autoscale_service.get_service_name())
        verboseInfo = f"\"{autoscale_service.get_service_name()}\" Before rescaling amount of replicas: \"{current_amount_replicas}\""
        logger.verboseInfo(verboseInfo, autoscale_service.get_service_log_level())

        # Min and max amount of replicas.
        min_replicas = autoscale_service.get_minimum_replicas()
        max_replicas = autoscale_service.get_maximum_replicas()
        verboseInfo = f"\"{autoscale_service.get_service_name()}\" Minimum replicas: \"{min_replicas}\", Maximum replicas: \"{max_replicas}\""
        logger.verboseInfo(verboseInfo, autoscale_service.get_service_log_level())

        # Unchecked incrementation or decrementation of service.
        new_amount_replicas = current_amount_replicas
        if scaling_suggestion == ScalingSuggestion.SCALE_DOWN:
            new_amount_replicas = current_amount_replicas - 1
        elif scaling_suggestion == ScalingSuggestion.SCALE_UP:
            new_amount_replicas = current_amount_replicas + 1
        verboseInfo = f"\"{autoscale_service.get_service_name()}\" Unchecked new replicas based on scaling suggestion: \"{new_amount_replicas}\""
        logger.verboseInfo(verboseInfo, autoscale_service.get_service_log_level())
        
        # Ensure scaling is within limits.
        if new_amount_replicas < min_replicas:
            new_amount_replicas = min_replicas
        if new_amount_replicas > max_replicas:
            new_amount_replicas = max_replicas
        verboseInfo = f"\"{autoscale_service.get_service_name()}\" New replicas after adhering to min and max replica thresholds: \"{new_amount_replicas}\""
        logger.verboseInfo(verboseInfo, autoscale_service.get_service_log_level())

        # Does amount of replicas have to be changed?
        if new_amount_replicas != current_amount_replicas:
            self._scale_service(autoscale_service, new_amount_replicas)
        else:
            # Info about keeping replicas.
            keeping_replica_msg = f"Keeping replicas of service \"{autoscale_service.get_service_name()}\" at \"{current_amount_replicas}\""
            logger.information(keeping_replica_msg, autoscale_service.get_service_log_level())
