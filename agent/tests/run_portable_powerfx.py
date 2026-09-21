"""Run synthetic portable cases against already-installed Microsoft Power Fx DLLs."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from test_portable_runtime import native_portable_cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library-directory", required=True,
                        help="Local directory containing Power Fx Core, Interpreter, Json and Bcl.AsyncInterfaces DLLs.")
    args = parser.parse_args()
    library = Path(args.library_directory).resolve()
    for name in ("Microsoft.PowerFx.Core", "Microsoft.PowerFx.Interpreter", "Microsoft.PowerFx.Json",
                 "Microsoft.Bcl.AsyncInterfaces"):
        if not (library / (name + ".dll")).is_file():
            raise SystemExit("Missing local test assembly: " + name)
    with tempfile.TemporaryDirectory(prefix="portable-powerfx-offline-") as temp:
        cases, results = Path(temp) / "cases.json", Path(temp) / "results.json"
        cases.write_text(json.dumps(native_portable_cases(), ensure_ascii=True), encoding="utf-8")
        code = subprocess.call([
            "dotnet", "run", "--project", str(ROOT / "tests/powerfx-contract/PowerFxContract.csproj"),
            "-p:PowerFxLibraryDirectory=" + str(library), "--", str(cases), str(results),
        ])
        if results.exists():
            evidence = json.loads(results.read_text(encoding="utf-8"))
            print(f"Offline Power Fx: {evidence['passed']} passed; {evidence['failed']} failed. No cloud calls.")
        raise SystemExit(code)


if __name__ == "__main__":
    main()
