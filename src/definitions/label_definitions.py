from enum import Enum

# Define what labels define cpu scaling and what type of they should be.
cpu_labels = [
    {
        "label": "autoscale.cpu_upscale_threshold",
        "value_type": "percentage",
        "required": True
    },
    {
        "label": "autoscale.cpu_upscale_time_duration",
        "value_type": "valid time_duration",
        "required": False
    },
    {
        "label": "autoscale.cpu_downscale_threshold",
        "value_type": "percentage",
        "required": True
    },
    {
        "label": "autoscale.cpu_downscale_time_duration",
        "value_type": "valid time_duration",
        "required": False
    }
]

# Define what labels define memory scaling and what type of they should be.
memory_labels = [
    {
        "label": "autoscale.memory_upscale_threshold",
        "value_type": "byte",
        "required": True
    },
    {
        "label": "autoscale.memory_downscale_threshold",
        "value_type": "byte",
        "required": True
    }
]

class ScalingConflictResolution(Enum):
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    KEEP_REPLICAS = "keep_replicas"
    ADHERE_TO_MEMORY = "adhere_to_memory"
    ADHERE_TO_CPU = "adhere_to_cpu"


class ScalingSuggestion(Enum):
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    KEEP_REPLICAS = "keep_replicas"

class LogLevel(Enum):
    INFO = "INFO"
    VERBOSE = "VERBOSE"
    WARNING_AND_ERRORS_ONLY = "WARNING_AND_ERRORS_ONLY"