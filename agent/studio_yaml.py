"""Emit the YAML subset accepted by the Copilot Studio native authoring parser."""
import yaml


class StudioDumper(yaml.SafeDumper):
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


def represent_string(dumper, value):
    return dumper.represent_scalar(
        "tag:yaml.org,2002:str", value, style="|" if "\n" in value else None
    )


StudioDumper.add_representer(str, represent_string)


def dumps(value):
    return yaml.dump(value, Dumper=StudioDumper, sort_keys=False,
                     allow_unicode=True, width=1000000)
