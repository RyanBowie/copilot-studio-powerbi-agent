"""Deploy native generated-DAX topics to this existing private agent; preserve cloud model/auth."""
import argparse
import json
from pathlib import Path
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

import yaml
from studio_yaml import dumps
from studio_authoring import read_components, verify_components

ROOT = Path(__file__).resolve().parent
from config import load_config, validate_config
CONFIG = load_config()
BASELINE = ROOT / "deployment-baseline.private.json"
LEGACY = {
    "action.PowerBISmokeTest", "action.PowerBIGovernanceCounts", "action.PowerBITopAgentsByUsage",
    "topic.ModelAnalytics", "topic.ModelDaxAdvice", "topic.ModelQuestionClarification",
}


def token(resource):
    validate_config(CONFIG)
    return subprocess.check_output(
        ["az.cmd", "account", "get-access-token", "--resource", resource,
         "--tenant", CONFIG["tenantId"], "--query", "accessToken", "-o", "tsv"], text=True,
    ).strip()


class Dataverse:
    def __init__(self):
        self.headers = {"Authorization": "Bearer " + token(CONFIG["dataverseUrl"]),
                        "Content-Type": "application/json", "Prefer": "return=representation",
                        "MSCRM.SolutionUniqueName": CONFIG["solutionName"]}

    def request(self, path, method="GET", body=None, etag=None):
        headers = dict(self.headers)
        if etag:
            headers["If-Match"] = etag
        req = urllib.request.Request(CONFIG["dataverseUrl"] + "/api/data/v9.2/" + path, headers=headers,
                                     method=method, data=None if body is None else json.dumps(body).encode())
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                data = response.read()
                return json.loads(data) if data else {}
        except urllib.error.HTTPError as error:
            message = json.loads(error.read()).get("error", {}).get("message", "")
            raise RuntimeError(f"Dataverse {method} HTTP {error.code}: {message}") from None

    def snapshot(self):
        bot = self.request("bots(" + CONFIG["agentId"] + ")?$select=schemaname,configuration,authenticationmode,authenticationtrigger,accesscontrolpolicy,publishedon,synchronizationstatus")
        if bot["schemaname"] != CONFIG["schemaName"]:
            raise RuntimeError("Unexpected agent; no writes allowed.")
        if [bot[k] for k in ("authenticationmode", "authenticationtrigger", "accesscontrolpolicy")] != [2, 1, 2]:
            raise RuntimeError("Live privacy/auth settings differ; review instead of overwriting.")
        query = urllib.parse.urlencode({"$filter": "_parentbotid_value eq " + CONFIG["agentId"],
                                       "$select": "botcomponentid,schemaname,data,statecode,statuscode,componenttype"})
        components = self.request("botcomponents?" + query)["value"]
        query = urllib.parse.urlencode({"$filter": "connectionreferencelogicalname eq '" + CONFIG["connectionReference"] + "'",
                                       "$select": "connectionreferenceid,connectionid,connectorid"})
        references = self.request("connectionreferences?" + query)["value"]
        if len(references) != 1 or not references[0].get("connectionid") or references[0]["connectorid"] != CONFIG["connectorId"]:
            raise RuntimeError("Existing approved Power BI connection binding is required; no connection is created/replaced.")
        return {"bot": bot, "components": components, "reference": references[0]}


def ensure_unchanged(before, after):
    for key in ("configuration", "authenticationmode", "authenticationtrigger", "accesscontrolpolicy"):
        if before["bot"][key] != after["bot"][key]:
            raise RuntimeError("Concurrent cloud configuration/auth change; stopped.")
    if before["reference"]["connectionid"] != after["reference"]["connectionid"]:
        raise RuntimeError("Concurrent connection-binding change; stopped.")
    index = {c["botcomponentid"]: c for c in after["components"]}
    if set(index) != {c["botcomponentid"] for c in before["components"]}:
        raise RuntimeError("Component inventory changed after capture; review and recapture.")
    for old in before["components"]:
        new = index[old["botcomponentid"]]
        if any(old[k] != new[k] for k in ("data", "statecode", "statuscode", "schemaname")):
            raise RuntimeError("Concurrent portal component edit; stopped: " + old["schemaname"])


def apply(api, before, publish):
    from general_runtime import generate
    snapshot = json.loads((ROOT / "model-schema.private.json").read_text(encoding="utf-8"))
    if snapshot.get("example"):
        raise RuntimeError("Example metadata is for offline tests only. Prepare the authorized real model first.")
    generated = generate(CONFIG, snapshot)
    live = api.snapshot()
    ensure_unchanged(before, live)
    by_schema = {c["schemaname"]: c for c in live["components"]}
    gpt = by_schema[CONFIG["schemaName"] + ".gpt.default"]
    old_gpt = yaml.safe_load(gpt["data"])
    source = yaml.safe_load((ROOT / "agent.mcs.yml").read_text(encoding="utf-8"))
    wanted = dict(old_gpt)
    wanted["instructions"] = source["instructions"]
    wanted["conversationStarters"] = source["conversationStarters"]
    if len(wanted["instructions"]) > 8000:
        raise RuntimeError("Instruction budget exceeded.")
    # Never apply settings.mcs.yml or replace the user's aISettings/model/capabilities.
    gpt_data = dumps(wanted)
    component_ids = {}
    for name, body in generated.items():
        schema = CONFIG["schemaName"] + ".topic." + name
        data = dumps(body)
        existing = by_schema.get(schema)
        payload = {"data": data, "name": body.get("modelDisplayName", "Generated query error"),
                   "schemaname": schema, "componenttype": 9, "language": 1033,
                   "parentbotid@odata.bind": "/bots(" + CONFIG["agentId"] + ")"}
        if existing:
            cid = existing["botcomponentid"]
            api.request("botcomponents(" + cid + ")", "PATCH", payload, existing["@odata.etag"])
        else:
            created = api.request("botcomponents", "POST", payload)
            cid = created["botcomponentid"]
        if "connectionReference:" in data:
            relationship = "botcomponents(" + cid + ")/botcomponent_connectionreference"
            links = api.request(relationship + "?$select=connectionreferenceid")["value"]
            reference_id = live["reference"]["connectionreferenceid"]
            if not any(link["connectionreferenceid"] == reference_id for link in links):
                api.request(relationship + "/$ref", "POST", {"@odata.id": CONFIG["dataverseUrl"] + "/api/data/v9.2/connectionreferences(" + reference_id + ")"})
        assert api.request("botcomponents(" + cid + ")?$select=data")["data"] == data
        component_ids[name] = cid
        print("Verified new runtime component:", name, cid)
    api.request("botcomponents(" + gpt["botcomponentid"] + ")", "PATCH", {"data": gpt_data}, gpt["@odata.etag"])
    retired = []
    for suffix in LEGACY:
        old = by_schema.get(CONFIG["schemaName"] + "." + suffix)
        if old and old["statecode"] == 0:
            api.request("botcomponents(" + old["botcomponentid"] + ")", "PATCH",
                        {"statecode": 1, "statuscode": 2}, old["@odata.etag"])
            retired.append(suffix)
    native = verify_components(read_components(CONFIG, token("https://api.powerplatform.com")),
                               CONFIG["schemaName"], wanted, generated)
    if publish:
        previous_operation = json.loads(live["bot"]["synchronizationstatus"]).get("lastFinishedPublishOperation")
        api.request("bots(" + CONFIG["agentId"] + ")/Microsoft.Dynamics.CRM.PvaPublish", "POST", {})
        for _ in range(36):
            time.sleep(5)
            bot = api.request("bots(" + CONFIG["agentId"] + ")?$select=publishedon,synchronizationstatus")
            state = json.loads(bot["synchronizationstatus"])
            if state.get("lastFinishedPublishOperation") == previous_operation:
                continue
            if state.get("lastFinishedPublishOperation", {}).get("status") == "Failed":
                (ROOT / "native-publish-diagnostics.private.json").write_text(
                    json.dumps(state, indent=2), encoding="utf-8", newline="\n")
                raise RuntimeError("Native compilation failed; inspect native-publish-diagnostics.private.json.")
            if bot["publishedon"] != live["bot"]["publishedon"] and state.get("lastFinishedPublishOperation", {}).get("status") == "Succeeded" and state["currentSynchronizationState"]["state"] == "Synchronized":
                break
        else:
            raise RuntimeError("Publish completion not verified.")
        native = verify_components(read_components(CONFIG, token("https://api.powerplatform.com")),
                                   CONFIG["schemaName"], wanted, generated)
    after = api.snapshot()
    assert all(after["bot"][k] == live["bot"][k] for k in ("configuration", "authenticationmode", "authenticationtrigger", "accesscontrolpolicy"))
    assert after["reference"]["connectionid"] == live["reference"]["connectionid"]
    current_gpt = yaml.safe_load(next(c["data"] for c in after["components"] if c["schemaname"].endswith(".gpt.default")))
    for key in set(old_gpt) - {"instructions", "conversationStarters"}:
        assert current_gpt[key] == old_gpt[key]
    for c in after["components"]:
        if c["schemaname"].removeprefix(CONFIG["schemaName"] + ".") in LEGACY:
            assert c["statecode"] == 1
    evidence = {"publishedAtUtc": after["bot"]["publishedon"], "publishedAndSynchronized": publish,
                "aISettingsBefore": old_gpt["aISettings"], "aISettingsAfter": current_gpt["aISettings"],
                "configurationAuthAndBindingUnchanged": True, "retired": sorted(retired), "components": component_ids,
                "modelAliases": ["primary"], "chatEndToEndPass": False, **native}
    (ROOT / "deployment-general.private.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8", newline="\n")
    print(json.dumps(evidence, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", action="store_true", help="Capture private current live state for review, without writes.")
    parser.add_argument("--apply", action="store_true", help="Apply reviewed source only if live state still matches capture.")
    parser.add_argument("--publish", action="store_true", help="Publish and verify synchronization after apply.")
    args = parser.parse_args()
    api = Dataverse()
    if args.capture:
        BASELINE.write_text(json.dumps(api.snapshot(), indent=2), encoding="utf-8", newline="\n")
        print("Captured current private baseline. Review cloud/source differences before --apply.")
    elif args.apply:
        if not BASELINE.exists():
            raise RuntimeError("Run --capture and review current cloud edits first.")
        apply(api, json.loads(BASELINE.read_text(encoding="utf-8")), args.publish)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
