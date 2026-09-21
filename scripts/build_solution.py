"""Package the retained native runtime with public defaults, never a private tenant export."""
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "agent"))
from portable_runtime import build_portable_bundle, build_portable_instructions
from studio_yaml import dumps

NAME = "poc_PowerBIQueryRuntime"
DISPLAY_NAME = "Power BI Query Runtime"
VERSION = "1.0.0.0"
REFERENCE = NAME + "_PowerBI"
CONFIG_PREFIX = NAME + "_Config"
ARCHIVE = ROOT / "solution" / "PowerBIQueryRuntime_unmanaged.zip"
BASELINE_COMMIT = "9f7355b68eea69c26e5ae5bb289579177c3c1982"
SOURCE_PATHS = [
    "scripts/build_solution.py", "agent/agent.mcs.yml", "agent/general_runtime.py",
    "agent/generated_dax.py", "agent/query_transport.py", "agent/studio_yaml.py",
    "agent/portable_runtime.py", "agent/configure_portable.py", "agent/prepare-model.py",
]


def bundle():
    return build_portable_bundle(schema_name=NAME, environment_prefix=CONFIG_PREFIX,
                                 connection_reference=REFERENCE)


def definitions():
    return bundle()["topics"], build_portable_instructions()


def xml_text(element):
    ET.indent(element, space="  ")
    return ET.tostring(element, encoding="unicode") + "\n"


def fields(element, values):
    for name, value in values.items():
        ET.SubElement(element, name).text = str(value)
    return element


def localized(element, name, text):
    node = ET.SubElement(element, name, default=text)
    ET.SubElement(node, "label", description=text, languagecode="1033")


def source_files():
    runtime = bundle()
    solution = ET.Element("ImportExportXml", version="9.2", SolutionPackageVersion="9.2",
                          languagecode="1033", generatedBy="CrmLive")
    manifest = ET.SubElement(solution, "SolutionManifest")
    fields(manifest, {"UniqueName": NAME})
    ET.SubElement(ET.SubElement(manifest, "LocalizedNames"), "LocalizedName",
                  description=DISPLAY_NAME, languagecode="1033")
    ET.SubElement(manifest, "Descriptions")
    fields(manifest, {"Version": VERSION, "Managed": "0"})
    publisher = ET.SubElement(manifest, "Publisher")
    fields(publisher, {"UniqueName": "PowerBIQueryRuntime"})
    ET.SubElement(ET.SubElement(publisher, "LocalizedNames"), "LocalizedName",
                  description=DISPLAY_NAME, languagecode="1033")
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
    fields(reference, {"connectionreferencedisplayname": DISPLAY_NAME + " - end-user Power BI",
                       "connectorid": "/providers/Microsoft.PowerApps/apis/shared_powerbi",
                       "iscustomizable": "1", "promptingbehavior": "0",
                       "statecode": "0", "statuscode": "1"})
    ET.SubElement(ET.SubElement(customizations, "Languages"), "Language").text = "1033"
    bot = fields(ET.Element("bot", schemaname=NAME), {
        "authenticationmode": "2", "authenticationtrigger": "1", "accesscontrolpolicy": "2",
        "iscustomizable": "1", "language": "1033", "name": DISPLAY_NAME, "runtimeprovider": "0",
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
    components = runtime["botcomponents"] + [{
        "schemaname": NAME + ".gpt.default", "componenttype": 15,
        "name": DISPLAY_NAME + " instructions", "data": build_portable_instructions(),
    }]
    for item in components:
        schema = item["schemaname"]
        component = fields(ET.Element("botcomponent", schemaname=schema), {
            "componenttype": item["componenttype"], "iscustomizable": 1,
            "language": 1033, "name": item["name"]})
        fields(ET.SubElement(component, "parentbotid"), {"schemaname": NAME})
        fields(component, {"statecode": 0, "statuscode": 1})
        base = Path("botcomponents") / schema
        files[base / "botcomponent.xml"] = xml_text(component)
        files[base / "data"] = dumps(item["data"])
    for item in runtime["environmentVariables"]:
        definition = ET.Element("environmentvariabledefinition", schemaname=item["schemaName"])
        fields(definition, {"defaultvalue": item["defaultValue"]})
        localized(definition, "displayname", item["displayName"])
        localized(definition, "description",
                  "Owner configuration; leave NOT_CONFIGURED during import. Use the private setup helper.")
        fields(definition, {"introducedversion": VERSION, "iscustomizable": 1, "isrequired": 0,
                            "secretstore": 0, "type": 100000000})
        files[Path("environmentvariabledefinitions") / item["schemaName"]
              / "environmentvariabledefinition.xml"] = xml_text(definition)
    links = ET.Element("botcomponent_environmentvariabledefinitionset")
    for item in runtime["environmentVariableLinks"]:
        link = ET.SubElement(links, "botcomponent_environmentvariabledefinition", {
            key: item[key] for key in ("botcomponentid.schemaname",
                                      "environmentvariabledefinitionid.schemaname")})
        fields(link, {"iscustomizable": item["iscustomizable"]})
    files[Path("Assets") / "botcomponent_environmentvariabledefinitionset.xml"] = xml_text(links)
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
    with tempfile.TemporaryDirectory(prefix="powerbi-runtime-pack-") as directory:
        output = Path(directory) / ARCHIVE.name
        subprocess.run([pac, "solution", "pack", "--zipfile", str(output), "--folder", str(source),
                        "--packagetype", "Unmanaged", "--errorlevel", "Warning"], check=True)
        with zipfile.ZipFile(output) as packed:
            if packed.testzip() is not None:
                raise RuntimeError("SolutionPackager produced a corrupt archive.")
            payloads = {item.filename: packed.read(item) for item in packed.infolist()}
    # Normalize ZIP headers only. Entity XML fragments and aggregate XML retain PAC's bytes.
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as normalized:
        for name, data in sorted(payloads.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 0
            info.external_attr = 0x20
            normalized.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    data = buffer.getvalue()
    digest = hashlib.sha256(data).hexdigest()
    observation_path = ARCHIVE.parent / "import-verification.json"
    if observation_path.exists():
        observation = json.loads(observation_path.read_text(encoding="utf-8"))
        if observation.get("importSucceeded") is True and observation["sha256"] != digest:
            raise RuntimeError("New ZIP differs from the import-verified artifact. Preserve its observation "
                               "and arrange a new native import before replacing the evidence.")
    entries = {name: {"sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)}
               for name, content in sorted(payloads.items())}
    manifest = {"solution": NAME, "version": VERSION, "managed": False, "kind": "functional-runtime",
                "configured": False, "publishOnImport": False,
                "sha256": digest, "configurationContract": bundle()["contract"],
                "sourceLineage": {"genericRuntimeCommit": BASELINE_COMMIT,
                                  "nativeSourceComparedOn": "2026-09-21",
                                  "rawTenantExportIncluded": False,
                                  "adaptation": "Trusted configuration boundary; retained native runtime."},
                "sourceSha256": {path: hashlib.sha256((ROOT / path).read_text(
                    encoding="utf-8").replace("\r\n", "\n").encode("utf-8")).hexdigest()
                    for path in SOURCE_PATHS},
                "entries": entries}
    ARCHIVE.write_bytes(data)
    (ARCHIVE.parent / "package-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    if not observation_path.exists() or observation.get("sha256") != digest:
        observation_path.write_text(json.dumps({
            "artifact": ARCHIVE.name, "sha256": digest, "importSucceeded": None,
            "configuredBusinessQueryTested": False, "crossTenantImportTested": False,
            "caveat": "Source-built candidate. Native import/readback and configured runtime are separate gates.",
        }, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("Built disabled-by-default native runtime:", ARCHIVE.name)
    print("SHA-256:", digest)


if __name__ == "__main__":
    main()
