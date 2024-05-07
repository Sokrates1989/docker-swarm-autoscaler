# Conversion.
import converterUtils

# Definitions.
from label_definitions import cpu_labels, memory_labels
from valid_values import ScalingConflictResolution

class AutoScaleService:
    def __init__(self, service_name, autoscale_labels):
        self._service_name = service_name
        self._autoscale_labels = autoscale_labels
    
    # Service name.
    def get_service_name(self):
        return self._service_name
    
    # Replica.
    def get_minimum_replicas(self):
        return int(self._autoscale_labels.get("autoscale.minimum_replicas", 1))
    
    def get_maximum_replicas(self):
        return int(self._autoscale_labels.get("autoscale.maximum_replicas", 3))
    
    # Scaling Conflict Resolution.
    def get_scaling_conflict_resolution(self):
        return self._autoscale_labels.get("autoscale.scaling_conflict_resolution", ScalingConflictResolution.SCALE_UP)
    
    # LogLevel.
    def get_service_log_level(self):
        return self._autoscale_labels.get("autoscale.log_level", None)
    
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
    