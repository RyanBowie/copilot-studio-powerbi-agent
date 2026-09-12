"""Verify only the deployed fixed queries; never prints individual agent ranking rows."""
import json
import urllib.request

import yaml

from deploy import CONFIG, ROOT, token


def query_rows(query):
    url = (f"https://api.powerbi.com/v1.0/myorg/groups/{CONFIG['workspaceId']}"
           f"/datasets/{CONFIG['datasetId']}/executeQueries")
    request = urllib.request.Request(
        url,
        data=json.dumps({"queries": [{"query": query}], "serializerSettings": {"includeNulls": True}}).encode(),
        headers={
            "Authorization": "Bearer " + token("https://analysis.windows.net/powerbi/api"),
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        payload = json.load(response)
    if payload.get("error") or any(result.get("error") for result in payload.get("results", [])):
        raise RuntimeError("Power BI returned a query error, possibly inside HTTP 200; no success claimed.")
    results = payload.get("results", [])
    if len(results) != 1 or len(results[0].get("tables", [])) != 1:
        raise RuntimeError("Unexpected Power BI response shape.")
    return results[0]["tables"][0].get("rows", [])


def main():
    for file in sorted((ROOT / "actions").glob("*.mcs.yml")):
        tool = yaml.safe_load(file.read_text())
        query = next(i["value"] for i in tool["inputs"] if i["propertyName"] == "query")
        rows = query_rows(query)
        result = {"tool": tool["modelDisplayName"], "rowCount": len(rows)}
        if file.name == "PowerBISmokeTest.mcs.yml":
            assert rows == [{"[SmokeTest]": 1}], "Unexpected smoke result."
        elif file.name == "PowerBIGovernanceCounts.mcs.yml":
            assert len(rows) == 1 and set(rows[0]) == {"[AgentCount]", "[EnvironmentCount]"}
            assert all(isinstance(value, (int, float)) and value >= 0 for value in rows[0].values())
        else:
            assert len(rows) <= 100
            keys = [row["[AgentKey]"] for row in rows]
            counts = [row["[Interactions]"] for row in rows]
            assert len(keys) == len(set(keys)), "Duplicate ranked agents."
            assert counts == sorted(counts, reverse=True) and all(count > 0 for count in counts)
            allowed = {"[AgentKey]", "[AgentName]", "[Interactions]", "[WindowStart]", "[WindowEnd]"}
            assert all(set(row) == allowed for row in rows), "Unapproved output fields."
            if rows:
                result.update(windowStart=rows[0]["[WindowStart]"], windowEnd=rows[0]["[WindowEnd]"])
        print(json.dumps({**result, "directQuery": "PASS", "agentEndToEnd": "NOT_TESTED_BY_THIS_SCRIPT"}))


if __name__ == "__main__":
    main()
