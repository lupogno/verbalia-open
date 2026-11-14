"""Controlli statici leggeri prima della pubblicazione."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = ["SKILL.md", "README.md", "LICENSE", "SECURITY.md", ".github/workflows/ci.yml", ".github/workflows/release.yml", "schemas/meeting.schema.json"]


def main():
    for name in REQUIRED:
        assert (ROOT / name).is_file(), f"Manca {name}"
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert skill.startswith("---\n"), "SKILL.md senza frontmatter"
    assert "name: verbalia-open" in skill
    assert "description:" in skill
    json.loads((ROOT / "schemas/meeting.schema.json").read_text(encoding="utf-8"))
    for item in (ROOT / "examples").glob("*.json"):
        json.loads(item.read_text(encoding="utf-8"))
    print("Check repository OK")


if __name__ == "__main__":
    main()
