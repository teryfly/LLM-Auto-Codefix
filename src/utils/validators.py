from typing import Any, Dict

def is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())

def is_positive_int(value: Any) -> bool:
    try:
        return int(value) > 0
    except (ValueError, TypeError):
        return False

def is_valid_url(url: str) -> bool:
    if not isinstance(url, str):
        return False
    return url.startswith("http://") or url.startswith("https://")

def validate_dict_keys(d: Dict[str, Any], required_keys: set) -> bool:
    return required_keys.issubset(d.keys())