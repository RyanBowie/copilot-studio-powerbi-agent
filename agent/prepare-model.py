"""Owner-run metadata refresh. Existing Fabric read+write rights are required; no rights are granted."""
import base64
import datetime as dt
import json
from pathlib import Path
import time
import urllib.request
from uuid import UUID

from deploy import CONFIG, token

BASE = "https://api.fabric.microsoft.com/v1"

def has_linguistic_metadata(value):
    if isinstance(value, dict):
        return any((key == "linguisticMetadata" and bool(child)) or has_linguistic_metadata(child)
                   for key, child in value.items())
    return isinstance(value, list) and any(has_linguistic_metadata(child) for child in value)


def main():
    headers = {"Authorization": "Bearer " + token("https://api.fabric.microsoft.com"), "Content-Type": "application/json"}
    url = BASE + "/workspaces/" + CONFIG["workspaceId"] + "/semanticModels/" + CONFIG["datasetId"] + "/getDefinition?format=TMSL"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers, method="POST", data=b"{}"), timeout=120) as response:
        status, payload = response.status, response.read()
        operation = response.headers.get("x-ms-operation-id")
    if status == 202:
        operation = str(UUID(operation))
        # Use the documented API host, not a region-specific redirect supplied in Location.
        operation_url = BASE + "/operations/" + operation
        for _ in range(60):
            time.sleep(2)
            with urllib.request.urlopen(urllib.request.Request(operation_url, headers=headers), timeout=60) as response:
                state = json.load(response)
            if state["status"] == "Succeeded":
                break
            if state["status"] == "Failed":
                raise RuntimeError("Model definition preparation failed; no snapshot replaced.")
        else:
            raise RuntimeError("Definition operation still pending; no snapshot replaced.")
        with urllib.request.urlopen(urllib.request.Request(operation_url + "/result", headers=headers), timeout=120) as response:
            payload = response.read()
    result = json.loads(payload)
    part = next(p for p in result["definition"]["parts"] if p["path"].endswith(".bim"))
    model = json.loads(base64.b64decode(part["payload"]))["model"]
    snapshot = {
        "modelAlias": "primary",
        "source": "Fabric semantic model getDefinition TMSL",
        "retrievedAtUtc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "sourcePermission": "Existing owner read+write; runtime users are not granted write.",
        "tables": [{
            "name": t["name"], "description": t.get("description", ""), "hidden": t.get("isHidden", False),
            "columns": [{"name": c["name"], "type": c.get("dataType", "unknown"), "description": c.get("description", ""),
                         "hidden": c.get("isHidden", False)} for c in t.get("columns", [])],
            "measures": [{"name": m["name"], "description": m.get("description", ""),
                          "formatString": m.get("formatString", ""), "expressionAvailable": False}
                         for m in t.get("measures", [])],
        } for t in model.get("tables", [])],
        "relationships": [{k: r[k] for k in ("name", "fromTable", "fromColumn", "toTable", "toColumn",
                                               "fromCardinality", "toCardinality", "crossFilteringBehavior", "isActive") if k in r}
                          for r in model.get("relationships", [])],
        "guidance": {"authoredInstructions": "Not verified", "verifiedAnswers": "Not verified",
                     "linguisticMetadataPresent": has_linguistic_metadata(model),
                     "measureExpressions": "Not published: definition/source sensitivity review is separate from name discovery."},
    }
    path = Path(__file__).with_name("model-schema.private.json")
    path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8", newline="\n")
    print("Prepared analytical metadata only:", len(snapshot["tables"]), "tables;",
          sum(len(t["columns"]) for t in snapshot["tables"]), "columns;",
          sum(len(t["measures"]) for t in snapshot["tables"]), "measure names.")
    print("Raw definitions, partitions, connections, roles, source expressions and credentials were not persisted.")
    print("Review the private snapshot, generate topics, then deploy/publish the same agent to refresh runtime metadata.")


if __name__ == "__main__":
    main()
