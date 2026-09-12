"""Remove only the three reviewed, inactive legacy tools; never delete their connection."""
import argparse
import json
from pathlib import Path
import time
import urllib.parse

from deploy import CONFIG, Dataverse, ensure_unchanged

ROOT = Path(__file__).resolve().parent
SUFFIXES = {
    "action.PowerBISmokeTest",
    "action.PowerBIGovernanceCounts",
    "action.PowerBITopAgentsByUsage",
}


def targets(snapshot):
    schemas = {CONFIG["schemaName"] + "." + suffix for suffix in SUFFIXES}
    return [c for c in snapshot["components"] if c["schemaname"] in schemas]


def preflight(api, snapshot, reviewed):
    ensure_unchanged(reviewed, snapshot)
    selected = targets(snapshot)
    if len(selected) != 3:
        raise RuntimeError("Expected exactly the three obsolete fixed tools; stopped.")
    for tool in selected:
        if (tool["statecode"], tool["statuscode"]) != (1, 2):
            raise RuntimeError("A reviewed obsolete tool is no longer inactive; stopped.")
        cid = tool["botcomponentid"]
        if any(
            other["botcomponentid"] != cid
            and any(value in other.get("data", "") for value in (cid, tool["schemaname"]))
            for other in snapshot["components"]
        ):
            raise RuntimeError("A component references the obsolete tool; stopped.")
        query = urllib.parse.urlencode({
            "$filter": "_parentbotcomponentid_value eq " + cid,
            "$select": "botcomponentid",
        })
        if api.request("botcomponents?" + query)["value"]:
            raise RuntimeError("Tool has child components; no cascade deletion allowed.")
        bots = api.request("botcomponents(" + cid + ")/bot_botcomponent?$select=botid")["value"]
        if any(bot["botid"] != CONFIG["agentId"] for bot in bots):
            raise RuntimeError("Tool is associated with another agent; stopped.")
        query = urllib.parse.urlencode({
            "$filter": "objectid eq " + cid, "$select": "componenttype",
        })
        types = {r["componenttype"] for r in api.request("solutioncomponents?" + query)["value"]}
        if len(types) != 1:
            raise RuntimeError("Cannot determine unique solution component type.")
        dependencies = api.request(
            "RetrieveDependenciesForDelete(ObjectId=@id,ComponentType=@type)?@id="
            + cid + "&@type=" + str(next(iter(types)))
        )["value"]
        if dependencies:
            raise RuntimeError("Platform reports deletion dependencies; stopped.")
    return selected


def verify_remaining(before, after, removed):
    expected = dict(before)
    expected["components"] = [
        c for c in before["components"] if c["botcomponentid"] not in removed
    ]
    ensure_unchanged(expected, after)
    if before["reference"] != after["reference"]:
        raise RuntimeError("Connection reference changed; inspect before continuing.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reviewed-backup", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    api = Dataverse()
    reviewed = json.loads(Path(args.reviewed_backup).read_text(encoding="utf-8"))
    before = api.snapshot()
    selected = preflight(api, before, reviewed)
    print("Preflight passed:", len(selected), "inactive, unreferenced tools; no child/other-agent dependencies.")
    if not args.apply:
        return
    evidence_path = ROOT / "fixed-tool-cleanup.private.json"
    if evidence_path.exists():
        raise RuntimeError("Existing cleanup evidence must not be overwritten.")
    evidence = {
        "removed": [], "backup": args.reviewed_backup, "published": False,
        "effectiveModelVerified": False, "chatEndToEndPass": False,
    }
    for tool in selected:
        api.request("botcomponents(" + tool["botcomponentid"] + ")", "DELETE",
                    etag=tool["@odata.etag"])
        evidence["removed"].append({
            "id": tool["botcomponentid"], "schema": tool["schemaname"],
        })
        evidence_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8", newline="\n")
    removed = {item["id"] for item in evidence["removed"]}
    verify_remaining(before, api.snapshot(), removed)
    if args.publish:
        api.request("bots(" + CONFIG["agentId"] + ")/Microsoft.Dynamics.CRM.PvaPublish", "POST", {})
        for _ in range(36):
            time.sleep(5)
            current = api.snapshot()
            state = json.loads(current["bot"]["synchronizationstatus"])
            if current["bot"]["publishedon"] == before["bot"]["publishedon"]:
                continue
            if state.get("lastFinishedPublishOperation", {}).get("status") == "Failed":
                raise RuntimeError("Cleanup publication failed; inspect the agent.")
            if (state.get("lastFinishedPublishOperation", {}).get("status") == "Succeeded"
                    and state["currentSynchronizationState"]["state"] == "Synchronized"):
                evidence["published"] = True
                evidence["publishedAtUtc"] = current["bot"]["publishedon"]
                break
        else:
            raise RuntimeError("Cleanup publication completion not verified.")
    after = api.snapshot()
    verify_remaining(before, after, removed)
    evidence["remainingComponentsAndAuthAndBindingUnchanged"] = True
    evidence_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8", newline="\n")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
