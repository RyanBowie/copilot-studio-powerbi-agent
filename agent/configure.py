"""Render source templates for your own existing agent; makes no remote changes."""
import json
from pathlib import Path
from config import load_config, validate_config

ROOT = Path(__file__).resolve().parent
config = load_config()
validate_config(config)
example = json.loads((ROOT / "resources.example.json").read_text(encoding="utf-8"))
for source in (ROOT / "templates").rglob("*"):
    if not source.is_file():
        continue
    content = source.read_text(encoding="utf-8")
    for key, marker in example.items():
        if key != "connectorId":
            content = content.replace(marker, config[key])
    target = ROOT / source.relative_to(ROOT / "templates")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
from analytics import build_topic, build_advice_topic, build_clarification_topic
import yaml
for name, topic in [("ModelAnalytics", build_topic()), ("ModelDaxAdvice", build_advice_topic()), ("ModelQuestionClarification", build_clarification_topic())]:
    target = ROOT / "topics" / (name + ".mcs.yml")
    target.write_text(yaml.safe_dump(topic, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8")
print("Configured local source. Review it and run tests before deploying.")
