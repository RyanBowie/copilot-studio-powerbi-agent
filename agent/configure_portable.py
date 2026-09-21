"""Owner-run configuration only. No topic, connection, authentication or publish writes.

prepare is entirely offline. check performs explicit-target reads. apply updates only
current environment-variable values in one Dataverse changeset, and never publishes.
"""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from uuid import uuid4

from portable_runtime import (
    CONTRACT, UNCONFIGURED, canonical_guid, decode_configuration, environment_names,
    make_configuration, validate_names,
)

GDS = "https://globaldisco.crm.dynamics.com"
REPO = Path(__file__).resolve().parent.parent
TARGET_KEYS = {
    "tenantId", "environmentId", "dataverseUrl", "agentId", "schemaName",
    "environmentPrefix", "connectionReference", "workspaceId", "datasetId",
}


def https_origin(value):
    parts = urllib.parse.urlsplit(value)
    if (parts.scheme != "https" or not parts.hostname or parts.username or parts.password or
            parts.port or parts.query or parts.fragment or parts.path not in ("", "/")):
        raise ValueError("Specify an HTTPS Dataverse origin without credentials, port, path or query.")
    if not parts.hostname.endswith(".dynamics.com"):
        raise ValueError("This helper supports commercial-cloud Dataverse only.")
    return "https://" + parts.hostname.lower()


def target_config(value):
    if not isinstance(value, dict) or set(value) != TARGET_KEYS:
        raise ValueError("All explicit portable target properties are required; no resources.json/auth defaults are used.")
    for name in ("tenantId", "environmentId", "agentId", "workspaceId", "datasetId"):
        canonical_guid(value[name])
    validate_names(value["schemaName"], value["environmentPrefix"], value["connectionReference"])
    if https_origin(value["dataverseUrl"]) != value["dataverseUrl"]:
        raise ValueError("Use a normalized Dataverse HTTPS origin.")
    return value


def private_output(path):
    path = Path(path).expanduser().resolve()
    if path.is_relative_to(REPO):
        raise ValueError("Configuration output must be outside this repository, including worktree content.")
    if path.exists():
        raise ValueError("Refusing to overwrite an existing private configuration; choose a new filename.")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def prepare(snapshot, target, revision):
    target = target_config(target)
    if snapshot.get("sourceBinding", {}).get("tenantId") != target["tenantId"]:
        raise ValueError("CONFIG_SOURCE_TENANT_MISMATCH: prepare/review metadata from the selected tenant.")
    values = make_configuration(
        snapshot, environment_id=target["environmentId"], workspace_id=target["workspaceId"],
        dataset_id=target["datasetId"], revision=revision, prefix=target["environmentPrefix"])
    return {"contract": CONTRACT, "destination": target, "values": values}


def validate_package(package, *, environment_id, dataverse_url, tenant_id, agent_id):
    if set(package) != {"contract", "destination", "values"} or package["contract"] != CONTRACT:
        raise ValueError("Unsupported configuration package.")
    target = target_config(package["destination"])
    explicit = {"environmentId": environment_id, "dataverseUrl": dataverse_url,
                "tenantId": tenant_id, "agentId": agent_id}
    if any(target[key] != value for key, value in explicit.items()):
        raise ValueError("EXPLICIT_DESTINATION_MISMATCH: stopped before authentication or network access.")
    document = decode_configuration(package["values"], target["environmentPrefix"], environment_id)
    if (document["workspaceId"] != target["workspaceId"] or document["datasetId"] != target["datasetId"] or
            document["snapshot"]["sourceBinding"]["tenantId"] != target["tenantId"]):
        raise ValueError("CONFIG_MODEL_OR_TENANT_MISMATCH")
    return target


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError("Unexpected HTTP redirect; stopped without forwarding credentials.")


def access_token(resource, tenant):
    # Reads existing Azure CLI authentication. Never login, account set, PAC auth select or default changes.
    result = subprocess.run(
        ["az.cmd", "account", "get-access-token", "--resource", resource, "--tenant", tenant,
         "--query", "accessToken", "-o", "tsv"],
        text=True, capture_output=True, check=False,
    )
    if result.returncode:
        raise RuntimeError("Token acquisition failed for the explicit tenant/resource. Sign in separately, then retry.") from None
    token = result.stdout.strip()
    try:
        encoded = token.split(".")[1]
        claims = json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))
        if claims["tid"].lower() != tenant:
            raise ValueError()
    except (ValueError, KeyError, IndexError):
        raise RuntimeError("Token tenant mismatch; no request sent.") from None
    return token


def http(url, token, method="GET", body=None, content_type="application/json"):
    request = urllib.request.Request(
        url, method=method, data=body, headers={
            "Authorization": "Bearer " + token, "Content-Type": content_type,
            "Accept": "application/json", "OData-Version": "4.0", "OData-MaxVersion": "4.0",
        })
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=120) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        # Server messages can include submitted configuration. Do not print them.
        raise RuntimeError(f"Explicit-target request failed: HTTP {error.code}. No publication was requested.") from None


class Destination:
    def __init__(self, target):
        self.target = target
        query = urllib.parse.urlencode({
            "$select": "Id,EnvironmentId,TenantId,Url,ApiUrl,State",
            "$filter": "EnvironmentId eq '" + target["environmentId"] + "'",
        })
        discovery = json.loads(http(GDS + "/api/discovery/v2.0/Instances?" + query,
                                    access_token(GDS, target["tenantId"])))["value"]
        if len(discovery) != 1:
            raise RuntimeError("Explicit environment could not be uniquely resolved; no writes allowed.")
        self.verify_discovery(target, discovery[0])
        self.origin = target["dataverseUrl"]
        self.token = access_token(self.origin, target["tenantId"])
        identity = self.get("WhoAmI")
        if identity["OrganizationId"].lower() != discovery[0]["Id"].lower():
            raise RuntimeError("Dataverse organization mismatch; no writes allowed.")

    @staticmethod
    def verify_discovery(target, instance):
        origins = [https_origin(instance[k]) for k in ("Url", "ApiUrl") if instance.get(k)]
        if (instance.get("EnvironmentId") != target["environmentId"] or
                instance.get("TenantId", "").lower() != target["tenantId"] or instance.get("State") != 0 or
                target["dataverseUrl"] not in origins):
            raise RuntimeError("Discovery environment/tenant/URL/state mismatch; no writes allowed.")

    def get(self, path):
        return json.loads(http(self.origin + "/api/data/v9.2/" + path, self.token))

    def preflight(self):
        target = self.target
        bot = self.get("bots(" + target["agentId"] + ")?$select=schemaname,authenticationmode,authenticationtrigger,accesscontrolpolicy")
        if bot["schemaname"] != target["schemaName"] or [bot[k] for k in (
                "authenticationmode", "authenticationtrigger", "accesscontrolpolicy")] != [2, 1, 2]:
            raise RuntimeError("Explicit agent identity/auth/privacy mismatch; configure in Studio, not this helper.")
        refs = self.get("connectionreferences?" + urllib.parse.urlencode({
            "$filter": "connectionreferencelogicalname eq '" + target["connectionReference"] + "'",
            "$select": "connectionreferenceid,connectionid,connectorid", "$top": "2",
        }))["value"]
        if (len(refs) != 1 or not refs[0].get("connectionid") or
                refs[0]["connectorid"] != "/providers/Microsoft.PowerApps/apis/shared_powerbi"):
            raise RuntimeError("Bind the imported Power BI connection reference first; this helper will not change it.")
        # A prefix alone is insufficient proof that this is the intended native runtime.
        import yaml
        from portable_runtime import build_portable_bundle
        bundle = build_portable_bundle(schema_name=target["schemaName"],
            environment_prefix=target["environmentPrefix"], connection_reference=target["connectionReference"])
        components = self.get("botcomponents?" + urllib.parse.urlencode({
            "$filter": "_parentbotid_value eq " + target["agentId"] + " and statecode eq 0",
            "$select": "botcomponentid,schemaname,data,componenttype", "$top": "250",
        }))
        if "@odata.nextLink" in components:
            raise RuntimeError("Unexpected component inventory; review the explicit destination.")
        by_name = {c["schemaname"]: c for c in components["value"]}
        if len(by_name) != len(components["value"]):
            raise RuntimeError("Duplicate active component schema names; no writes.")
        expected_names = {c["schemaname"] for c in bundle["botcomponents"]}
        if any(c["componenttype"] in (9, 12) and c["schemaname"] not in expected_names
               for c in components["value"]):
            raise RuntimeError("Unexpected active topic/variable components; review the imported runtime before configuring.")
        for declaration in bundle["botcomponents"]:
            live = by_name.get(declaration["schemaname"])
            if (not live or live["componenttype"] != declaration["componenttype"] or
                    yaml.safe_load(live["data"]) != declaration["data"]):
                raise RuntimeError("Imported runtime does not match this configuration contract; no writes.")
        for name in bundle["topics"]:
            component_schema = target["schemaName"] + ".topic." + name
            expected = {link["environmentvariabledefinitionid.schemaname"] for link in bundle["environmentVariableLinks"]
                        if link["botcomponentid.schemaname"] == component_schema}
            if not expected:
                continue
            component_id = canonical_guid(by_name[component_schema]["botcomponentid"])
            linked = self.get("botcomponents(" + component_id + ")/botcomponent_environmentvariabledefinition?"
                              "$select=schemaname&$top=250")
            if "@odata.nextLink" in linked or {v["schemaname"] for v in linked["value"]} != expected:
                raise RuntimeError("Imported topic environment-variable relationships differ; no writes.")
        definitions = {}
        for name in environment_names(target["environmentPrefix"]):
            rows = self.get("environmentvariabledefinitions?" + urllib.parse.urlencode({
                "$filter": "schemaname eq '" + name + "'",
                "$select": "environmentvariabledefinitionid,schemaname,type,defaultvalue",
                "$expand": "environmentvariabledefinition_environmentvariablevalue($select=environmentvariablevalueid,value)",
                "$top": "2",
            }))["value"]
            if len(rows) != 1 or rows[0]["type"] != 100000000:
                raise RuntimeError("Missing/ambiguous/non-Text imported configuration definition; no writes.")
            row = rows[0]
            if row.get("defaultvalue") != UNCONFIGURED:
                raise RuntimeError("Imported configuration must have explicit NOT_CONFIGURED defaults; no writes.")
            values = row["environmentvariabledefinition_environmentvariablevalue"]
            if len(values) > 1:
                raise RuntimeError("Ambiguous current environment-variable values; no writes.")
            if values and not values[0].get("@odata.etag"):
                raise RuntimeError("Current value has no concurrency token; no writes.")
            definitions[name] = row
        return definitions

    def apply(self, values, definitions):
        body, content_type = changeset(self.origin, values, definitions)
        response = http(self.origin + "/api/data/v9.2/$batch", self.token, "POST", body, content_type)
        # Dataverse can report a failed operation inside an HTTP-200 batch response.
        import re
        statuses = re.findall(rb"HTTP/1\.[01] (\d{3})", response)
        if len(statuses) != len(values) or any(not 200 <= int(s) < 300 for s in statuses):
            raise RuntimeError("Configuration transaction not verified. Do not publish; rerun check and review.")
        after = self.preflight()
        for name, wanted in values.items():
            current = after[name]["environmentvariabledefinition_environmentvariablevalue"]
            if len(current) != 1 or current[0]["value"] != wanted:
                raise RuntimeError("Configuration read-back mismatch. Do not publish; investigate concurrent changes.")


def changeset(origin, values, definitions):
    """One transactional changeset. Only value rows; no definitions, topics or bot actions."""
    batch, change = "batch_" + uuid4().hex, "changeset_" + uuid4().hex
    lines = [f"--{batch}", f"Content-Type: multipart/mixed; boundary={change}", ""]
    for number, (name, value) in enumerate(values.items(), 1):
        definition = definitions[name]
        current = definition["environmentvariabledefinition_environmentvariablevalue"]
        headers = []
        payload = {"value": value}
        if current:
            row = current[0]
            record_id = canonical_guid(row["environmentvariablevalueid"])
            method, path = "PATCH", "environmentvariablevalues(" + record_id + ")"
            etag = row["@odata.etag"]
            if not isinstance(etag, str) or not __import__("re").fullmatch(r'W/"[0-9]+"', etag):
                raise ValueError("Invalid concurrency token.")
            headers.append("If-Match: " + etag)
        else:
            method, path = "POST", "environmentvariablevalues"
            definition_id = canonical_guid(definition["environmentvariabledefinitionid"])
            payload["EnvironmentVariableDefinitionId@odata.bind"] = "/environmentvariabledefinitions(" + definition_id + ")"
        lines += [f"--{change}", "Content-Type: application/http", "Content-Transfer-Encoding: binary",
                  f"Content-ID: {number}", "", f"{method} {origin}/api/data/v9.2/{path} HTTP/1.1",
                  "Content-Type: application/json", *headers, "", json.dumps(payload, ensure_ascii=True)]
    lines += [f"--{change}--", f"--{batch}--", ""]
    return "\r\n".join(lines).encode("utf-8"), "multipart/mixed; boundary=" + batch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    offline = sub.add_parser("prepare", help="Offline: bind reviewed snapshot and create a new private config file.")
    offline.add_argument("--snapshot", required=True)
    offline.add_argument("--target-config", required=True)
    offline.add_argument("--out", required=True)
    offline.add_argument("--revision", default=None, help="Canonical UUID; otherwise generates a new revision.")
    for command in ("check", "apply"):
        online = sub.add_parser(command, help="Explicit-target reads" if command == "check" else "CONFIGURATION VALUE WRITES ONLY; never publishes.")
        online.add_argument("--configuration", required=True)
        for key in ("environment-id", "dataverse-url", "tenant-id", "agent-id"):
            online.add_argument("--" + key, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        output = private_output(args.out)
        package = prepare(json.loads(Path(args.snapshot).read_text(encoding="utf-8")),
                          json.loads(Path(args.target_config).read_text(encoding="utf-8")), args.revision or str(uuid4()))
        output.write_text(json.dumps(package, indent=2, ensure_ascii=True), encoding="utf-8", newline="\n")
        manifest = json.loads(next(iter(package["values"].values())))
        print(f"Private configuration prepared: {manifest['chunkCount']}/{len(package['values']) - 1} chunks, "
              f"{manifest['payloadLength']} characters. No cloud calls. Review privately; do not commit.")
        return
    package = json.loads(Path(args.configuration).read_text(encoding="utf-8"))
    target = validate_package(package, environment_id=args.environment_id, dataverse_url=args.dataverse_url,
                              tenant_id=args.tenant_id, agent_id=args.agent_id)
    destination = Destination(target)
    definitions = destination.preflight()
    if args.command == "apply":
        destination.apply(package["values"], definitions)
        print("Configuration current values written and read-back verified. Runtime topics/auth/connections unchanged.")
        print("NOT PUBLISHED. Explicitly publish in Copilot Studio, start a new conversation, then run approved tests.")
    else:
        print("Explicit destination/runtime/definitions verified. No writes or publication.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, KeyError, TypeError):
        # Deliberately don't dump parsed/private payloads or HTTP response bodies.
        raise SystemExit("Configuration operation stopped. Validate the explicit target, reviewed snapshot, "
                         "runtime contract, connection binding and environment-value uniqueness; do not publish.") from None
