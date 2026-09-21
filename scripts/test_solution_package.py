"""Package content and download checks; these do not claim a native import or runtime pass."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import io
import json
from pathlib import Path
from threading import Thread
import unittest
from urllib.request import urlopen
import xml.etree.ElementTree as ET
import zipfile

import build_solution
import validate_publication


def nodes(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from nodes(child)


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


class SolutionPackageTests(unittest.TestCase):
    def test_runtime_is_present_not_unconditional_stops(self):
        topics, _ = build_solution.definitions()
        for name in ("ModelMetadata", "GeneratedDaxQuery", "GeneratedDaxAdvice"):
            actions = topics[name]["beginDialog"]["actions"]
            self.assertNotIn("CancelAllDialogs", [a["kind"] for a in actions])
            self.assertNotIn("StopUnconfiguredStarter", str(topics[name]))
            self.assertIn("NOT_CONFIGURED", str(topics[name]))
        for name, expected in (("ModelMetadata", 1), ("GeneratedDaxQuery", 1),
                               ("GeneratedDaxAdvice", 0)):
            connectors = [node for node in nodes(topics[name])
                          if node.get("kind") == "InvokeConnectorAction"]
            self.assertEqual(expected, len(connectors), name)
            for connector in connectors:
                self.assertEqual("Invoker", connector["connectionProperties"]["mode"])
                self.assertEqual("ExecuteDatasetQuery", connector["operationId"])
                self.assertEqual(build_solution.REFERENCE, connector["connectionReference"])

    def test_configuration_is_unpublished_and_tenant_neutral(self):
        files = build_solution.source_files()
        config = json.loads(files[Path("bots") / build_solution.NAME / "configuration.json"])
        self.assertFalse(config["publishOnImport"])
        self.assertEqual([], config["channels"])
        _, gpt = build_solution.definitions()
        self.assertNotIn("model", gpt["aISettings"])
        self.assertNotIn("UNCONFIGURED STARTER", gpt["instructions"])
        self.assertGreater(len([p for p in files if p.name == "botcomponent.xml"]), 5)
        self.assertNotIn("<connectionid>", files[Path("Other") / "Customizations.xml"])
        definitions = [path for path in files if path.name == "environmentvariabledefinition.xml"]
        self.assertTrue(definitions, "Trusted model configuration must travel with the solution.")
        for path in definitions:
            definition = ET.fromstring(files[path])
            self.assertTrue(definition.attrib["schemaname"].startswith(build_solution.NAME))
            self.assertEqual([], list(definition.iter("environmentvariablevalue")))
        self.assertNotIn("'Entity'", "\n".join(files.values()))
        self.assertNotIn("'Event'", "\n".join(files.values()))

    def test_tracked_source_matches_generator(self):
        for relative, expected in build_solution.source_files().items():
            actual = (build_solution.ROOT / "solution" / "src" / relative).read_text(encoding="utf-8")
            self.assertEqual(expected, actual, str(relative))

    def test_every_zip_entry_is_inspected(self):
        texts = validate_publication.solution_texts(build_solution.ARCHIVE, require_import=False)
        manifest = json.loads((build_solution.ARCHIVE.parent / "package-manifest.json").read_text())
        self.assertEqual(set(manifest["entries"]), {name.split("::", 1)[1] for name, _ in texts})

    def test_native_dependencies_and_element_first_entity_fragments(self):
        runtime = build_solution.bundle()
        with zipfile.ZipFile(build_solution.ARCHIVE) as archive:
            for name in archive.namelist():
                if name.startswith(("bots/", "botcomponents/", "environmentvariabledefinitions/")) and name.endswith(".xml"):
                    self.assertFalse(archive.read(name).lstrip().startswith(b"<?xml"), name)
            env_paths = [name for name in archive.namelist()
                         if name.endswith("/environmentvariabledefinition.xml")]
            self.assertEqual(129, len(env_paths))
            definitions = {}
            for name in env_paths:
                definition = ET.fromstring(archive.read(name))
                definitions[definition.attrib["schemaname"]] = definition.findtext("defaultvalue")
                self.assertEqual("100000000", definition.findtext("type"))
            self.assertEqual({item["schemaName"]: item["defaultValue"]
                              for item in runtime["environmentVariables"]}, definitions)
            links = ET.fromstring(archive.read("Assets/botcomponent_environmentvariabledefinitionset.xml"))
            self.assertEqual(387, len(links))
            expected = {(item["botcomponentid.schemaname"], item["environmentvariabledefinitionid.schemaname"])
                        for item in runtime["environmentVariableLinks"]}
            self.assertEqual(expected, {(item.attrib["botcomponentid.schemaname"],
                                         item.attrib["environmentvariabledefinitionid.schemaname"])
                                        for item in links})
            bot = ET.fromstring(archive.read(f"bots/{build_solution.NAME}/bot.xml"))
            self.assertEqual(["2", "1", "2"], [bot.findtext(name) for name in
                                             ("authenticationmode", "authenticationtrigger", "accesscontrolpolicy")])

    def test_same_origin_http_download_is_the_importable_zip(self):
        handler = partial(QuietHandler, directory=str(build_solution.ROOT / "docs"))
        with ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                address = f"http://127.0.0.1:{server.server_port}/downloads/{build_solution.ARCHIVE.name}"
                with urlopen(address, timeout=10) as response:
                    self.assertEqual(200, response.status)
                    self.assertIn(response.headers.get_content_type(),
                                  {"application/zip", "application/x-zip-compressed"})
                    data = response.read()
                self.assertEqual(build_solution.ARCHIVE.read_bytes(), data)
                with zipfile.ZipFile(io.BytesIO(data)) as archive:
                    self.assertIsNone(archive.testzip())
                    self.assertIn("solution.xml", archive.namelist())
                    self.assertNotIn(build_solution.ARCHIVE.name, archive.namelist())
            finally:
                server.shutdown()
                thread.join(timeout=10)


if __name__ == "__main__":
    unittest.main()
