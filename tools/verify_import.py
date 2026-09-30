"""Verify preserved file bytes; does not run experiments or model APIs."""
from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / "provenance/import-manifest.json").read_text(encoding="utf-8"))
failed = []
for item in manifest["files"]:
    path = root / item["path"]
    actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    if actual != item["sha256"]:
        failed.append(item["path"])
print(json.dumps({"checked_files": len(manifest["files"]), "mismatches": failed}, ensure_ascii=False, indent=2))
raise SystemExit(1 if failed else 0)
