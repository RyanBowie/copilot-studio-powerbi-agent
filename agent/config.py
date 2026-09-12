"""Local deployment configuration; the committed example contains placeholders only."""
import json
from pathlib import Path
from uuid import UUID

ROOT = Path(__file__).resolve().parent

def load_config():
    path = ROOT / "resources.json"
    if not path.exists():
        path = ROOT / "resources.example.json"
    return json.loads(path.read_text(encoding="utf-8"))

def validate_config(config):
    if any("__" in str(value) for value in config.values()):
        raise ValueError("Copy resources.example.json to resources.json and configure your own resources first.")
    for key in ("tenantId", "environmentId", "agentId", "workspaceId", "datasetId", "reportId"):
        UUID(config[key])
    if not config["dataverseUrl"].startswith("https://"):
        raise ValueError("Dataverse must use HTTPS.")
