"""Package the canonical handbook and portable skill (standard library only)."""
import argparse
import json
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SECTIONS = ("guide", "rules", "engraving", "history")
SKILL_FILES = ("SKILL.md", "AGENTS.md", "LICENSE", "VERSION")
SKILL_DIRS = ("docs", "profiles", "layouts", "pieces", "tools", "plugins", "examples", "agents")
EXCLUDED = {"dist", "node_modules", ".git", ".openai", "__pycache__", ".DS_Store"}
OWNERSHIP = ".harpscore-package.json"


def included(path):
    return not any(part in EXCLUDED for part in path.parts) and not path.name.endswith((".pyc", ".autosave", "~"))


def files_in(folder):
    return sorted(p for p in (ROOT / folder).rglob("*") if p.is_file() and included(p.relative_to(ROOT)))


def doc_manifest():
    """Read the deliberately small YAML frontmatter schema without dependencies."""
    records = []
    for path in files_in("docs"):
        if path.suffix != ".md":
            continue
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n") or "\n---\n" not in text[4:]:
            raise ValueError(f"Missing frontmatter: {path.relative_to(ROOT)}")
        header = text[4:].split("\n---\n", 1)[0]
        fields = dict(line.split(":", 1) for line in header.splitlines() if line.strip())
        fields = {key: value.strip() for key, value in fields.items()}
        relative = path.relative_to(ROOT)
        section = relative.parts[1] if len(relative.parts) > 2 else ""
        records.append({"path": relative.as_posix(), "section": section,
                        "title": fields["title"], "order": int(fields["order"]),
                        "summary": fields["summary"]})
    return sorted(records, key=lambda r: (
        SECTIONS.index(r["section"]) if r["section"] in SECTIONS else len(SECTIONS),
        r["order"], r["path"]))


def archive(path, files):
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as target:
        for name, data in sorted(files.items()):
            item = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            item.compress_type = zipfile.ZIP_DEFLATED
            item.create_system = 3
            item.external_attr = 0o100644 << 16
            target.writestr(item, data)


def source_files(target):
    names = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    result = {}
    for name in sorted(set(names) - {""}):
        relative = Path(name)
        path = ROOT / relative
        if included(relative) and path.is_file() and not path.resolve().is_relative_to(target.resolve()):
            result[relative.as_posix()] = path.read_bytes()
    return result


def build(out=None):
    target = Path(out) if out is not None else ROOT / "dist"
    target = target.resolve()
    if target == ROOT or ROOT.is_relative_to(target):
        raise ValueError("Output must not contain the repository")
    # site/dist is the Astro build output; packages are added next to its pages.
    for folder in SKILL_DIRS + ("scripts", "tests", "site", ".git"):
        if target.is_relative_to(ROOT / folder) and not target.is_relative_to(ROOT / "site" / "dist"):
            raise ValueError(f"Output must not overwrite {folder}")
    target.mkdir(parents=True, exist_ok=True)
    docs = doc_manifest()
    kit = {name: (ROOT / name).read_bytes() for name in SKILL_FILES}
    for folder in SKILL_DIRS:
        kit.update({p.relative_to(ROOT).as_posix(): p.read_bytes() for p in files_in(folder)})
    canonical = ["SKILL.md", "AGENTS.md"] + [r["path"] for r in docs]
    canonical += [p.relative_to(ROOT).as_posix() for p in files_in("profiles")]
    generated = {
        **kit,
        "llms.txt": ("# HarpScore " + kit["VERSION"].decode().strip() + "\n\n"
                     "An agent-readable harmonica arranging and Jianpu skill.\n\n"
                     "Agent entrypoint: SKILL.md\nContract: docs/guide/agent-contract.md\n"
                     "Full rules and decisions: llms-full.txt\n"
                     "Summer layout validation: docs/guide/tryout.md\n"
                     "Profile: profiles/skyhong.json\n"
                     "Repository: https://github.com/skyhong2002/harpscore\n"
                     "Download: downloads/harpscore-skill.zip\n").encode(),
        "llms-full.txt": "\n\n".join(f"# FILE: {name}\n{kit[name].decode()}" for name in canonical).encode(),
    }
    downloads = {
        "harpscore-skill.zip": {"harpscore/" + name: data for name, data in kit.items()},
        "agent-kit.zip": kit,
        "harpscore-musescore-templates.zip": {
            name: data for name, data in kit.items()
            if name == "LICENSE" or name.startswith("layouts/") or
            (name.startswith("pieces/") and (Path(name).parts[2] in {"scores", "events"} or
                                              Path(name).parts[2:] in [("piece.json",), ("README.md",)]))},
        "source.zip": source_files(target),
    }
    owned = set(generated) | {"downloads/" + name for name in downloads}
    journal = target / OWNERSHIP
    if journal.exists():
        for name in set(json.loads(journal.read_text())) - owned:
            stale = target / name
            if stale.resolve().is_relative_to(target) and stale.is_file():
                stale.unlink()
    for name, data in sorted(generated.items()):
        path = target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    for name, files in downloads.items():
        archive(target / "downloads" / name, files)
    journal.write_text(json.dumps(sorted(owned), indent=2) + "\n")
    print(f"Packaged {len(docs)} chapters and 4 reproducible downloads in {target}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "dist")
    parser.add_argument("--manifest", action="store_true", help="Print the documentation manifest as JSON")
    args = parser.parse_args()
    if args.manifest:
        print(json.dumps(doc_manifest(), ensure_ascii=False, indent=2))
    else:
        build(args.out)
