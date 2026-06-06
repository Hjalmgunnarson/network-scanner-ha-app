import time

from .storage import load_json, save_json


BACKUP_VERSION = 1


def create_backup(names_file, seen_file):
    """
    Maak één export-structuur met alle persistente data.
    """

    names = load_json(names_file)
    seen = load_json(seen_file)

    if not isinstance(names, dict):
        names = {}

    if not isinstance(seen, dict):
        seen = {}

    return {
        "version": BACKUP_VERSION,
        "exported_at": time.time(),
        "names": names,
        "seen_devices": seen,
    }


def validate_backup(data):
    """
    Controleer of een importbestand geldig is.
    """

    if not isinstance(data, dict):
        raise ValueError("Backup is not a JSON object")

    if "names" not in data:
        raise ValueError("Missing 'names'")

    if "seen_devices" not in data:
        raise ValueError("Missing 'seen_devices'")

    if not isinstance(data["names"], dict):
        raise ValueError("'names' must be an object")

    if not isinstance(data["seen_devices"], dict):
        raise ValueError("'seen_devices' must be an object")

    return True


def import_backup(
    data,
    names_file,
    seen_file,
    merge=False,
):
    """
    Importeer backup data.

    merge=False:
        vervangt bestaande data volledig

    merge=True:
        combineert bestaande + nieuwe data
    """

    validate_backup(data)

    new_names = data["names"]
    new_seen = data["seen_devices"]

    if merge:
        existing_names = load_json(names_file)
        existing_seen = load_json(seen_file)

        if not isinstance(existing_names, dict):
            existing_names = {}

        if not isinstance(existing_seen, dict):
            existing_seen = {}

        existing_names.update(new_names)
        existing_seen.update(new_seen)

        save_json(names_file, existing_names)
        save_json(seen_file, existing_seen)

    else:
        save_json(names_file, new_names)
        save_json(seen_file, new_seen)

    return {
        "ok": True,
        "names_count": len(new_names),
        "seen_count": len(new_seen),
    }
