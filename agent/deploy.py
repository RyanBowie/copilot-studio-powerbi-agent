"""Deploy only this PoC's components; never stores authentication tokens."""
import json
from pathlib import Path
import subprocess
import urllib.error
import urllib.parse
import urllib.request

import yaml

ROOT = Path(__file__).resolve().parent
from config import load_config, validate_config
CONFIG = load_config()


def token(resource):
    return subprocess.check_output(
        ["az.cmd", "account", "get-access-token", "--resource", resource,
         "--tenant", CONFIG["tenantId"], "--query", "accessToken", "-o", "tsv"],
        text=True,
    ).strip()


def main():
    validate_config(CONFIG)
    access_token = token(CONFIG["dataverseUrl"])
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "MSCRM.SolutionUniqueName": CONFIG["solutionName"],
        "Prefer": "return=representation",
    }

    def request(path, method="GET", data=None, etag=None):
        url = CONFIG["dataverseUrl"] + "/api/data/v9.2/" + path
        body = None if data is None else json.dumps(data).encode()
        call_headers = dict(headers)
        if etag:
            call_headers["If-Match"] = etag
        req = urllib.request.Request(url, data=body, headers=call_headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                payload = response.read()
                return json.loads(payload) if payload else {}
        except urllib.error.HTTPError as error:
            detail = json.loads(error.read()).get("error", {})
            raise RuntimeError(f"Dataverse {method} HTTP {error.code}: {detail.get('message')}") from None

    bot_id = CONFIG["agentId"]
    bot = request(f"bots({bot_id})?$select=schemaname,configuration,authenticationmode,authenticationtrigger,accesscontrolpolicy")
    if bot["schemaname"] != CONFIG["schemaName"]:
        raise RuntimeError("Refusing to modify an unexpected agent.")
    if (bot["authenticationmode"], bot["authenticationtrigger"], bot["accesscontrolpolicy"]) != (2, 1, 2):
        raise RuntimeError("Live authentication changed; review it rather than overwrite it.")
    name = CONFIG["connectionReference"]
    query = urllib.parse.urlencode({"$filter": f"connectionreferencelogicalname eq '{name}'"})
    refs = request("connectionreferences?" + query)["value"]
    if not refs:
        reference = request("connectionreferences", "POST", {
            "connectionreferencelogicalname": name,
            "connectionreferencedisplayname": "Power BI Query PoC - end-user Power BI",
            "connectorid": CONFIG["connectorId"],
        })
        print("Created connection reference:", reference["connectionreferenceid"])
        reference_id = reference["connectionreferenceid"]
    else:
        if len(refs) != 1 or refs[0]["connectorid"] != CONFIG["connectorId"]:
            raise RuntimeError("Unexpected connection reference; refusing to modify it.")
        print("Connection reference:", refs[0]["connectionreferenceid"])
        reference_id = refs[0]["connectionreferenceid"]

    settings = yaml.safe_load((ROOT / "settings.mcs.yml").read_text(encoding="utf-8"))
    configuration = json.loads(bot["configuration"] or "{}")
    for key, value in settings["configuration"].items():
        if isinstance(value, dict):
            configuration.setdefault(key, {}).update(value)
        else:
            configuration[key] = value
    configuration["$kind"] = "BotConfiguration"
    configuration["recognizer"] = {"$kind": "GenerativeAIRecognizer"}
    configuration["gPTSettings"]["$kind"] = "GPTSettings"
    configuration["aISettings"]["$kind"] = "AISettings"
    request(f"bots({bot_id})", "PATCH", {
        "configuration": json.dumps(configuration),
    }, etag=bot["@odata.etag"])
    components = [
        ("agent.mcs.yml", "gpt.default", "Power BI Query PoC", 15),
        (r"actions\PowerBISmokeTest.mcs.yml", "action.PowerBISmokeTest", "Power BI smoke test", 9),
        (r"actions\PowerBIGovernanceCounts.mcs.yml", "action.PowerBIGovernanceCounts", "Power BI governance counts", 9),
        (r"actions\PowerBITopAgentsByUsage.mcs.yml", "action.PowerBITopAgentsByUsage", "Power BI top 100 agents by usage", 9),
        (r"topics\ModelAnalytics.mcs.yml", "topic.ModelAnalytics", "Model analytics", 9),
        (r"topics\ModelDaxAdvice.mcs.yml", "topic.ModelDaxAdvice", "Model DAX advice", 9),
        (r"topics\ModelQuestionClarification.mcs.yml", "topic.ModelQuestionClarification", "Model question clarification", 9),
    ]
    for relative, suffix, display_name, component_type in components:
        schema_name = CONFIG["schemaName"] + "." + suffix
        data = (ROOT / Path(relative)).read_text(encoding="utf-8")
        query = urllib.parse.urlencode({
            "$filter": f"_parentbotid_value eq {bot_id} and schemaname eq '{schema_name}'",
            "$select": "botcomponentid,data",
        })
        existing = request("botcomponents?" + query)["value"]
        payload = {
            "name": display_name,
            "schemaname": schema_name,
            "componenttype": component_type,
            "data": data,
            "language": 1033,
            "parentbotid@odata.bind": f"/bots({bot_id})",
        }
        if existing:
            component_id = existing[0]["botcomponentid"]
            if suffix in ("action.PowerBISmokeTest", "action.PowerBIGovernanceCounts", "action.PowerBITopAgentsByUsage") and existing[0]["data"] != data:
                raise RuntimeError(f"Protected live tool changed: {schema_name}. Pull and review it; do not overwrite portal changes.")
            if existing[0]["data"] != data:
                request(f"botcomponents({component_id})", "PATCH", payload, etag=existing[0]["@odata.etag"])
        else:
            result = request("botcomponents", "POST", payload)
            component_id = result["botcomponentid"]
        verified = request(f"botcomponents({component_id})?$select=data")
        if verified["data"] != data:
            raise RuntimeError(f"Component readback mismatch: {schema_name}")
        if component_type == 9 and "connectionReference:" in data:
            relationship = f"botcomponents({component_id})/botcomponent_connectionreference"
            links = request(relationship + "?$select=connectionreferenceid")["value"]
            if not any(link["connectionreferenceid"] == reference_id for link in links):
                request(relationship + "/$ref", "POST", {
                    "@odata.id": CONFIG["dataverseUrl"] + f"/api/data/v9.2/connectionreferences({reference_id})"
                })
        print("Verified component:", schema_name, component_id)
    print("Deployment persisted; existing connection binding preserved. Verify runtime access through chat.")


if __name__ == "__main__":
    main()
