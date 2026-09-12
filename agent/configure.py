"""Validate local configuration. This makes no remote changes."""
from pathlib import Path
from config import load_config, validate_config
config = load_config()
validate_config(config)
schema = Path(__file__).with_name("model-schema.private.json")
if schema.exists():
    import json
    from general_runtime import generate
    generate(config, json.loads(schema.read_text(encoding="utf-8")))
    print("Generated private runtime topics; review and test before deploying.")
else:
    print("Configuration valid. Have an already-authorized owner run prepare-model.py, review the private snapshot, then run general_runtime.py.")
