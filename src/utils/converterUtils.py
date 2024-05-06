def human_readable_storage_to_bytes(size):
    """
    Convert memory or storage string to bytes.
    """
    size = size.strip().lower()
    try:
        if size.endswith('kib'):
            return int(float(size[:-3]) * 1024)
        elif size.endswith('mib'):
            return int(float(size[:-3]) * 1024 * 1024)
        elif size.endswith('gib'):
            return int(float(size[:-3]) * 1024 * 1024 * 1024)
        elif size.endswith('tib'):
            return int(float(size[:-3]) * 1024 * 1024 * 1024 * 1024)
        elif size.endswith('kb'):
            return int(float(size[:-2]) * 1000)
        elif size.endswith('mb'):
            return int(float(size[:-2]) * 1000 * 1000)
        elif size.endswith('gb'):
            return int(float(size[:-2]) * 1000 * 1000 * 1000)
        elif size.endswith('tb'):
            return int(float(size[:-2]) * 1000 * 1000 * 1000 * 1000)
        elif size.endswith('b'):
            return int(float(size[:-1]))
        else:
            return int(float(size))
    except Exception as e:
        raise ValueError("Invalid size format. Please use B, KiB, MiB, GiB, TiB, KB, MB, GB, TB or any valid float value.")
    
    
def bytes_to_human_readable_storage(bytes_size):
    """
    Convert bytes to memory or storage string.
    """
    try:
        bytes_size = int(bytes_size)
        if bytes_size < 0:
            raise ValueError("Size must be a positive integer.")
        elif bytes_size < 1000:
            return str(bytes_size) + " B"
        elif bytes_size < 1000 * 1000:
            return "{:.2f} KiB".format(bytes_size / 1024)
        elif bytes_size < 1000 * 1000 * 1000:
            return "{:.2f} MiB".format(bytes_size / (1024 * 1024))
        elif bytes_size < 1000 * 1000 * 1000 * 1000:
            return "{:.2f} GiB".format(bytes_size / (1024 * 1024 * 1024))
        else:
            return "{:.2f} TiB".format(bytes_size / (1024 * 1024 * 1024 * 1024))
    except Exception as e:
        raise ValueError("Invalid size format. Please provide a valid positive integer.")


def percentage_to_float(percentage):
    """
    Convert percentage string to float.
    """
    percentage = percentage.strip().lower()
    try:
        if percentage.endswith('%'):
            value = int(percentage[:-1])
        else:
            value = float(percentage)
        
        if 0 <= value <= 100:
            return value
        else:
            raise ValueError("Percentage value must be between 0 and 100.")
    except Exception as e:
        raise ValueError("Invalid percentage format. Please use '%' or any valid float value between 0 and 100.")

def float_to_percentage(float_value):
    """
    Convert float to percentage string.
    """
    try:
        float_value = float(float_value)
        if 0 <= float_value <= 100:
            return "{:.2f}%".format(float_value)
        else:
            raise ValueError("Percentage value must be between 0 and 100.")
    except Exception as e:
        raise ValueError("Invalid float value. Please provide a valid float value between 0 and 100.")

    