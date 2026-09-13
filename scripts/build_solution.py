"""Build a separate, fail-closed unmanaged starter; never read a live solution export."""
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "agent"))
import yaml
from general_runtime import build_error_topic, build_metadata_topic, build_query_topic, set_value
from studio_yaml import dumps

NAME = "poc_PowerBIQueryStarter"
REFERENCE = NAME + "_PowerBI"
NOTICE = (
    "This imported starter is not configured for a semantic model. No Power BI query was run. "
    "The owner must bind an end-user Power BI connection, prepare the target model metadata "
    "and regenerate/deploy the topics using the repository setup instructions before publishing."
)
ARCHIVE = ROOT / "solution" / "PowerBIQueryStarter_unmanaged.zip"


def blocked_actions():
    return [
        {"kind": "SendActivity", "id": "ExplainRequiredConfiguration", "activity": NOTICE},
        {"kind": "CancelAllDialogs", "id": "StopUnconfiguredStarter", "activityProcessed": True},
    ]


def definitions():
    # No demo schema or synthetic business entities enter the importable package.
    snapshot = {"tables": [], "relationships": [], "retrievedAtUtc": "NOT_CONFIGURED"}
    config = {"workspaceId": "__WORKSPACE_ID__", "datasetId": "__DATASET_ID__",
              "connectionReference": REFERENCE}
    metadata = build_metadata_topic(config, snapshot)
    metadata["beginDialog"]["actions"] = [
        {"kind": "SetVariable", "id": "ClearSchemaSnapshot",
         "variable": "Global.SchemaSnapshot", "value": ""},
        {"kind": "SetVariable", "id": "ClearSchemaTurn",
         "variable": "Global.SchemaTurn", "value": ""},
        {"kind": "SetVariable", "id": "ClearSchemaUser",
         "variable": "Global.SchemaUser", "value": ""},
        *[set_value(key, False if value["type"] == "Boolean" else "")
          for key, value in metadata["outputType"]["properties"].items()],
        set_value("status", "stopped"),
        set_value("stage", "configuration_required"),
        set_value("error", NOTICE),
        *blocked_actions(),
    ]
    topics = {"ModelMetadata": metadata,
              "GeneratedDaxQuery": build_query_topic(config, snapshot),
              "GeneratedDaxAdvice": build_query_topic(config, snapshot, advice=True),
              "GeneratedQueryError": build_error_topic()}
    for name in ("GeneratedDaxQuery", "GeneratedDaxAdvice"):
        topics[name]["beginDialog"]["actions"][:0] = blocked_actions()
    gpt = yaml.safe_load((ROOT / "agent" / "agent.mcs.yml").read_text(encoding="utf-8"))
    gpt["instructions"] = (
        "DEPLOYMENT STATE: UNCONFIGURED STARTER. Do not answer model-specific questions, invent "
        "a schema, or execute queries. Explain the required owner configuration. This notice must "
        "be replaced by the real source deployment after model preparation.\n\n" + gpt["instructions"])
    gpt["conversationStarters"] = [
        {"title": "Explore model structure",
         "text": "What tables, measures and relationships are available in this model?"},
        {"title": "Analyze model data",
         "text": "Review the configured semantic model and suggest useful analyses."},
        {"title": "Recommend DAX",
         "text": "Recommend DAX for a model-specific calculation without executing it."},
    ]
    # Model availability is tenant-specific; do not force the demonstration's preview model.
    gpt.get("aISettings", {}).pop("model", None)
    return topics, gpt


def xml_text(element):
    ET.indent(element, space="  ")
    return ET.tostring(element, encoding="unicode") + "\n"


def fields(element, values):
    for name, value in values.items():
        ET.SubElement(element, name).text = str(value)
    return element


def source_files():
    topics, gpt = definitions()
    solution = ET.Element("ImportExportXml", version="9.2", SolutionPackageVersion="9.2",
                          languagecode="1033", generatedBy="CrmLive")
    manifest = ET.SubElement(solution, "SolutionManifest")
    fields(manifest, {"UniqueName": NAME})
    ET.SubElement(ET.SubElement(manifest, "LocalizedNames"), "LocalizedName",
                  description="Power BI Query Starter", languagecode="1033")
    ET.SubElement(manifest, "Descriptions")
    fields(manifest, {"Version": "1.0.0.0", "Managed": "0"})
    publisher = ET.SubElement(manifest, "Publisher")
    fields(publisher, {"UniqueName": "PowerBIQueryStarter"})
    ET.SubElement(ET.SubElement(publisher, "LocalizedNames"), "LocalizedName",
                  description="Power BI Query Starter", languagecode="1033")
    ET.SubElement(publisher, "Descriptions")
    fields(publisher, {"CustomizationPrefix": "poc", "CustomizationOptionValuePrefix": "89396"})
    ET.SubElement(manifest, "RootComponents")
    ET.SubElement(manifest, "MissingDependencies")

    customizations = ET.Element("ImportExportXml")
    for section in ("Entities", "Roles", "Workflows", "FieldSecurityProfiles", "Templates",
                    "EntityMaps", "EntityRelationships", "OrganizationSettings", "optionsets",
                    "CustomControls", "EntityDataProviders"):
        ET.SubElement(customizations, section)
    reference = ET.SubElement(ET.SubElement(customizations, "connectionreferences"),
                             "connectionreference", connectionreferencelogicalname=REFERENCE)
    fields(reference, {"connectionreferencedisplayname": "Power BI Query Starter - end-user Power BI",
                       "connectorid": "/providers/Microsoft.PowerApps/apis/shared_powerbi",
                       "iscustomizable": "1", "promptingbehavior": "0",
                       "statecode": "0", "statuscode": "1"})
    ET.SubElement(ET.SubElement(customizations, "Languages"), "Language").text = "1033"
    bot = fields(ET.Element("bot", schemaname=NAME), {
        "authenticationmode": "2", "authenticationtrigger": "1", "iscustomizable": "1",
        "language": "1033", "name": "Power BI Query Starter", "runtimeprovider": "0",
        "template": "empty-1.0.0"})
    configuration = {
        "$kind": "BotConfiguration", "channels": [],
        "settings": {"GenerativeActionsEnabled": True}, "publishOnImport": False,
        "gPTSettings": {"$kind": "GPTSettings", "defaultSchemaName": NAME + ".gpt.default"},
        "isLightweightBot": False,
        "aISettings": {"$kind": "AISettings", "useModelKnowledge": False,
                       "isFileAnalysisEnabled": False},
        "recognizer": {"$kind": "GenerativeAIRecognizer"}, "deferredProvisioning": False,
    }
    files = {
        Path("Other") / "Solution.xml": xml_text(solution),
        Path("Other") / "Customizations.xml": xml_text(customizations),
        Path("bots") / NAME / "bot.xml": xml_text(bot),
        Path("bots") / NAME / "configuration.json": json.dumps(configuration, indent=2) + "\n",
    }
    components = [("topic." + name, 9, topic.get("modelDisplayName", "Generated query error"), topic)
                  for name, topic in topics.items()]
    components.append(("gpt.default", 15, "Power BI Query Starter instructions", gpt))
    for suffix, kind, title, data in components:
        schema = NAME + "." + suffix
        component = fields(ET.Element("botcomponent", schemaname=schema), {
            "componenttype": kind, "iscustomizable": 1, "language": 1033, "name": title})
        fields(ET.SubElement(component, "parentbotid"), {"schemaname": NAME})
        fields(component, {"statecode": 0, "statuscode": 1})
        base = Path("botcomponents") / schema
        files[base / "botcomponent.xml"] = xml_text(component)
        files[base / "data"] = dumps(data)
    return files


def main():
    pac = shutil.which("pac")
    if not pac:
        raise RuntimeError("Install the Power Platform CLI before packaging the solution.")
    source = ROOT / "solution" / "src"
    expected = source_files()
    existing = {p.relative_to(source) for p in source.rglob("*") if p.is_file()}
    if existing - set(expected):
        raise RuntimeError("Unexpected files in solution source; review them before packaging.")
    for relative, content in expected.items():
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
    subprocess.run([pac, "solution", "pack", "--zipfile", str(ARCHIVE), "--folder", str(source),
                    "--packagetype", "Unmanaged", "--errorlevel", "Warning"], check=True)
    # Normalize ZIP headers only; retain every SolutionPackager payload byte.
    with zipfile.ZipFile(ARCHIVE) as packed:
        payloads = {item.filename: packed.read(item) for item in packed.infolist()}
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as normalized:
        for name, data in sorted(payloads.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 0
            info.external_attr = 0x20
            normalized.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    ARCHIVE.write_bytes(buffer.getvalue())
    with zipfile.ZipFile(ARCHIVE) as archive:
        entries = {item.filename: {"sha256": hashlib.sha256(archive.read(item)).hexdigest(),
                                   "bytes": item.file_size} for item in archive.infolist()}
    manifest = {"solution": NAME, "version": "1.0.0.0", "managed": False,
                "configured": False, "publishOnImport": False,
                "sha256": hashlib.sha256(ARCHIVE.read_bytes()).hexdigest(), "entries": entries}
    (ARCHIVE.parent / "package-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("Built unconfigured starter:", ARCHIVE.name)


if __name__ == "__main__":
    main()
