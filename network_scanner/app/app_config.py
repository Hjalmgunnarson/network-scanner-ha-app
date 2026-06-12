import json
import ipaddress
import logging

OPTIONS_FILE = "/data/options.json"
DEFAULT_TARGET_IP = "192.168.0.0/24"
DEFAULT_SCAN_INTERVAL = 30  # seconds
DEFAULT_OFFLINE_INTERVAL = 600 # seconds
DEFAULT_FORGET_INTERVAL = 2880 #seconds
DEFAULT_lOG_LEVEL = "warning"

logger = logging.getLogger(__name__)

def get_option(option_name, default_value):

    try:
        with open(OPTIONS_FILE, "r") as f:
            options = json.load(f)

        option_value = options.get(option_name, default_value)
        logger.debug(f"Succesfully read {option_value} for {option_name}")
        return option_value

    except Exception as e:
        logger.warning(f"Could not read {option_name} from {OPTIONS_FILE}: {e}")
        logger.warning(f"Falling back to default value: {default_value}")
        return default_value

def get_target_ip():

    target_ip = get_option("target_ip", DEFAULT_TARGET_IP)

    # Valideer CIDR, bijvoorbeeld 192.168.0.0/24
    ipaddress.ip_network(target_ip, strict=False)

    return target_ip

def get_scan_interval():
    
    interval = int(get_option("scan_interval", DEFAULT_SCAN_INTERVAL))

    # Extra veiligheid naast config.yaml schema
    if interval < 5:
        interval = 5

    if interval > 3600:
        interval = 3600

    return interval

def get_offline_interval():
    
    interval = int(get_option("offline_interval", DEFAULT_OFFLINE_INTERVAL))

    # Extra veiligheid naast config.yaml schema
    if interval < 5:
        interval = 5

    if interval > 3600:
        interval = 3600

    return interval

def get_forget_interval():
    
    interval = int(get_option("forget_interval", DEFAULT_FORGET_INTERVAL))

    # Extra veiligheid naast config.yaml schema
    if interval < 60:
        interval = 60

    if interval > 7200:
        interval = 7200

    return interval

def get_log_level():
    value = get_option("log_level", DEFAULT_lOG_LEVEL)
    return str(value).upper()    