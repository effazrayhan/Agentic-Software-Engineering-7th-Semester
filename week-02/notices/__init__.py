import json
from pathlib import Path

ROOT = Path(__file__).parent
SCHEMA_VERSION = "1.0"
_TYPES = {"string": str, "null": type(None)}


def load_corpus():
    return json.loads((ROOT / "corpus.json").read_text(encoding="utf-8"))


def load_schema():
    return json.loads((ROOT / "schema_v1.json").read_text(encoding="utf-8"))


def validate_notice(record):
    schema = load_schema()
    if not isinstance(record, dict) or any(k not in record for k in schema["required"]):
        return False
    for name, rule in schema["properties"].items():
        value = record[name]
        allowed = rule["type"]
        allowed = allowed if isinstance(allowed, list) else [allowed]
        if not any(isinstance(value, _TYPES[t]) for t in allowed):
            return False
        if "const" in rule and value != rule["const"]:
            return False
        if "enum" in rule and value not in rule["enum"]:
            return False
    return True
