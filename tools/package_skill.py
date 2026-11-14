"""Crea archivio della skill portabile per la Release GitHub."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parent.parent
INCLUDE = ["SKILL.md", "LICENSE", "README.md", "pyproject.toml", "CONTRIBUTING.md", "SECURITY.md", "CODE_OF_CONDUCT.md"]
FOLDERS = ["references", "assets", "schemas", "docs", "examples", "src", "demo"]


def main():
    output = ROOT / "dist" / "verbalia-open-skill.zip"
    output.parent.mkdir(exist_ok=True)
    with ZipFile(output, "w", ZIP_DEFLATED) as zf:
        for rel in INCLUDE:
            zf.write(ROOT / rel, f"verbalia-open/{rel}")
        for folder in FOLDERS:
            for path in sorted((ROOT / folder).rglob("*")):
                if path.is_file() and "__pycache__" not in path.parts and path.suffix not in {".pyc", ".pyo"}:
                    relative = path.relative_to(ROOT)
                    if any(part.startswith(".") or part.endswith(".egg-info") for part in relative.parts):
                        continue
                    zf.write(path, f"verbalia-open/{relative.as_posix()}")
    print(output)


if __name__ == "__main__":
    main()
