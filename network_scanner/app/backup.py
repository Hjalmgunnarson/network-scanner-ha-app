import time
import json

from .storage import load_json, save_json

BACKUP_VERSION = 2


def create_backup(user_config_file, seen_file, user_config_lock, seen_lock):
    with user_config_lock:
        with seen_lock:
            user_config = load_json(user_config_file)
            seen = load_json(seen_file)

            if not isinstance(user_config, dict):
                user_config = {}

            if not isinstance(seen, dict):
                seen = {}

            return {
                "version": BACKUP_VERSION,
                "exported_at": time.time(),
                "user_config": user_config,
                "seen_devices": seen,
            }

def validate_backup(data):
    """
    Controleer of een importbestand geldig is.
    """

    if not isinstance(data, dict):
        raise ValueError("Backup is not a JSON object")

    if "names" not in data and "user_config" not in data :
        raise ValueError("Missing 'user_config' or 'names' entry")

    if "seen_devices" not in data:
        raise ValueError("Missing 'seen_devices'")

    user_config = data.get("user_config")

    if user_config is None:
        user_config = data.get("names")

    if not isinstance(user_config, dict):
        raise ValueError("'user_config' or 'names' must be an object")

    if not isinstance(data["seen_devices"], dict):
        raise ValueError("'seen_devices' must be an object")

    return True


def import_backup(
    raw,
    user_config_file,
    seen_file,
    user_config_lock,
    seen_lock,
    merge=False,
):
    """
    Importeer backup data.

    merge=False:
        vervangt bestaande data volledig

    merge=True:
        combineert bestaande + nieuwe data

    Let op lock-volgorde:
        eerst user_config_lock, daarna seen_lock.
    """

    try:
        data = json.loads(raw.decode("utf-8"))

        validate_backup(data)

        
        new_user_config = data.get("user_config")

        if new_user_config is None:
            new_user_config = data.get("names", {})

        new_seen = data["seen_devices"]

        with user_config_lock:
            with seen_lock:
                if merge:
                    existing_user_config = load_json(user_config_file)
                    existing_seen = load_json(seen_file)

                    if not isinstance(existing_user_config, dict):
                        existing_user_config = {}

                    if not isinstance(existing_seen, dict):
                        existing_seen = {}

                    existing_user_config.update(new_user_config)
                    existing_seen.update(new_seen)

                    save_json(user_config_file, existing_user_config)
                    save_json(seen_file, existing_seen)

                else:
                    save_json(user_config_file, new_user_config)
                    save_json(seen_file, new_seen)

        return {
            "ok": True,
            "user_config": len(new_user_config),
            "seen_count": len(new_seen),
        }

    except json.JSONDecodeError as e:
        return {
            "ok": False,
            "error": f"Invalid JSON syntax: {str(e)}",
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }