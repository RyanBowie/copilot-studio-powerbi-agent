"""Direct authorized verification transport, not the agent's Invoker runtime."""
import json
import urllib.error
import urllib.request

from deploy import CONFIG, token


class QueryError(RuntimeError):
    pass


def query_rows(query):
    url = ("https://api.powerbi.com/v1.0/myorg/groups/" + CONFIG["workspaceId"] +
           "/datasets/" + CONFIG["datasetId"] + "/executeQueries")
    request = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + token("https://analysis.windows.net/powerbi/api"),
        "Content-Type": "application/json"},
        data=json.dumps({"queries": [{"query": query}], "serializerSettings": {"includeNulls": True}}).encode())
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as error:
        payload = json.loads(error.read())
        raise QueryError("Power BI HTTP " + str(error.code) + ": " + json.dumps(payload.get("error", {}))[:2500]) from None
    results = payload.get("results", [])
    if payload.get("error") or any(r.get("error") or any(t.get("error") for t in r.get("tables", [])) for r in results):
        raise QueryError("Power BI body error, including HTTP 200; no partial success claimed.")
    if len(results) != 1 or len(results[0].get("tables", [])) != 1:
        raise QueryError("Unexpected single-table response shape.")
    return results[0]["tables"][0].get("rows", [])
