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

# Define what labels can be set to set service based email settings.
email_labels = [
    {
        "label": "autoscale.additional_email_recipients_important_msgs",
        "value_type": "email_list",
        "required": False
    },
    {
        "label": "autoscale.additional_email_recipients_information_msgs",
        "value_type": "email_list",
        "required": False
    },
    {
        "label": "autoscale.additional_email_recipients_verbose_msgs",
        "value_type": "email_list",
        "required": False
    }
]

# Define what labels can be set to set service based telegram settings.
telegram_labels = [
    {
        "label": "autoscale.additional_telegram_recipients_important_msgs",
        "value_type": "telegram_chat_id_list",
        "required": False
    },
    {
        "label": "autoscale.additional_telegram_recipients_information_msgs",
        "value_type": "telegram_chat_id_list",
        "required": False
    },
    {
        "label": "autoscale.additional_telegram_recipients_verbose_msgs",
        "value_type": "telegram_chat_id_list",
        "required": False
    }
]
