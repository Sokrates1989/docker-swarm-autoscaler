from enum import Enum

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
    IMPORTANT_ONLY = "IMPORTANT_ONLY"

class MessageLevel(Enum):
    IMPORTANT = ("IMPORTANT", "‼️")
    ERROR = ("ERROR", "🛑")
    WARNING = ("WARNING", "⚠️")
    INFO = ("INFO", "ℹ️")
    VERBOSE = ("VERBOSE", "🔍")
    
    def __init__(self, level, icon):
        self.level = level
        self.icon = icon

    def __str__(self):
        return f'{self.icon} {self.level}'
    
    def get_lowercase_representation_with_icon(self):
        return f'{self.icon} {str(self.level).lower()}'

class ScalingMetricName(Enum):
    CPU = "CPU"
    MEMORY = "MEMORY"

class MessagingPlatforms(Enum):
    LOGGING = "LOGGING"
    EMAIL = "EMAIL"
    TELEGRAM = "TELEGRAM"


VALID_SMTP_PORTS = (25, 587, 465)

