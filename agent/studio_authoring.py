"""Read the same parsed component contract consumed by the Studio authoring client."""
import json
import time
import urllib.request


def read_components(config, access_token):
    url = ("https://powerva.microsoft.com/api/botmanagement/v1/environments/"
           + config["environmentId"] + "/bots/" + config["agentId"] + "/content/botcomponents")
    headers = {"Authorization": "Bearer " + access_token,
               "X-CCI-TenantId": config["tenantId"], "x-ms-aad-auth": "true",
               "Content-Type": "application/json"}
    for attempt in range(2):
        try:
            request = urllib.request.Request(url, data=b"{}", headers=headers, method="POST")
            with urllib.request.urlopen(request, timeout=90) as response:
                return json.load(response)
        except ConnectionResetError:
            if attempt:
                raise
            time.sleep(2)


def verify_components(parsed, schema_name, gpt_source, topics):
    components = {change["component"]["schemaName"]: change["component"]
                  for change in parsed["botComponentChanges"] if "component" in change}
    metadata = components[schema_name + ".gpt.default"]["metadata"]
    expected_model = gpt_source.get("aISettings", {}).get("model")
    actual_model = metadata.get("aISettings", {}).get("model")
    expected_native_model = None if expected_model is None else {
        ("$kind" if key == "kind" else key): value for key, value in expected_model.items()
    }
    if actual_model != expected_native_model:
        raise RuntimeError("Native model-selector backend differs from the stored YAML. Do not publish.")
    instructions = metadata.get("instructions", {})
    segments = instructions.get("segments", []) if isinstance(instructions, dict) else []
    if any(segment.get("$kind") != "TextSegment" for segment in segments):
        raise RuntimeError("Unexpected native instruction interpolation; review the cloud edit.")
    text = "".join(segment.get("value", "") for segment in segments)
    if text != gpt_source["instructions"]:
        raise RuntimeError("Native parser changed instruction text. Do not publish.")
    if len(metadata.get("conversationStarters", [])) != len(gpt_source.get("conversationStarters", [])):
        raise RuntimeError("Native parser dropped conversation starters. Do not publish.")
    capabilities = {}
    for name, expected in topics.items():
        dialog = components[schema_name + ".topic." + name]["dialog"]
        begin = dialog.get("beginDialog", {})
        source_begin = expected["beginDialog"]
        if (begin.get("$kind") != source_begin["kind"]
                or len(begin.get("actions", [])) != len(source_begin["actions"])
                or len(dialog.get("inputs", [])) != len(expected.get("inputs", []))):
            raise RuntimeError("Native parser dropped topic inputs, trigger or actions: " + name)
        if source_begin["kind"] == "OnRecognizedIntent" and not begin.get("intent", {}).get("includeInOnSelectIntent"):
            raise RuntimeError("Native topic is not exposed to generative selection: " + name)
        alias_source = next((item for item in expected.get("inputs", [])
                             if item.get("propertyName") == "modelAlias"), None)
        if alias_source and alias_source.get("defaultValue") == "primary":
            alias = next((item for item in dialog.get("inputs", [])
                          if item.get("propertyName") == "modelAlias"), {})
            if (alias.get("$kind") != "AutomaticTaskInput"
                    or alias.get("defaultValue", {}).get("literalValue") != "primary"):
                raise RuntimeError("Native fixed-model alias default was dropped: " + name)
            resolver = next((action for action in begin.get("actions", [])
                             if action.get("id") == "ResolveFixedModelAlias"), {})
            if resolver.get("value", {}).get("expressionText") != 'Coalesce(Topic.modelAlias, "primary")':
                raise RuntimeError("Native blank-alias runtime resolution was dropped: " + name)
            required_outputs = {"stage", "connectorAttempted", "visibilityVerified", "resolvedModelAlias"}
            if not required_outputs.issubset(dialog.get("outputType", {}).get("properties", {})):
                raise RuntimeError("Native error-provenance outputs were dropped: " + name)
        capabilities[name] = {"trigger": begin["$kind"], "actions": len(begin["actions"]),
                              "inputs": len(dialog.get("inputs", []))}
    return {"nativeAuthoringModel": actual_model, "nativeCapabilities": capabilities,
            "nativeInstructionTextVerified": True}
