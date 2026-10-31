"""Check Azurik-Custom-Content: the manifest, every file it lists, and that
no game image (or a part of one) and nothing holding console keys is here.

Stdlib only (Python 3.10 or later)::

    python3 -I scripts/check.py            # exit 0, or 1 with one line per fault
    python3 -I scripts/check.py --write    # first fill in each listed file's sha256 and size

The manifest (``manifest.json``) is ``{"format": "azurik-custom-content",
"schema_version": 1, "entries": [...]}``; each entry is ``{"id", "kind"
("variant" or "pack"), "title", "author", "licence", "version" (a whole
number, bumped by any change to its files), "files": [{"path", "sha256",
"size"[, "licence"]}], "requires": [ids]}``. A file's path is the same here
and in the player's content folder, under ``variants/``, ``clips/``,
``sounds/``, ``fx/`` or ``packs/``, with a suffix its folder takes
(:data:`SUFFIXES`: no page, script or document a browser renders), and no
``:`` or name Windows keeps for a device (``CON``, ``NUL.json``); a variant
entry lists ``variants/<id>/variant.json`` (an object of recipes, ``{name:
recipe}``), a pack entry ``packs/<id>/pack.json``. A manifest holds at most
1,000 entries and 10,000 files, an entry's files at most 256 MiB. These are
AzurKit's own rules (its ``content.check``): the two change together.

Refused anywhere in the tree (as AzurKit's own leak guard): a game image or
a part of one (``MICROSOFT*XBOX*MEDIA`` at 0x10000, or an ``.iso``,
``.xiso`` or ``.iso.NNN`` name), an xemu HDD image (qcow2), an EEPROM dump,
a guest RAM snapshot or a private key, also inside a gzip file. Game bytes
inside a clip or another asset are allowed; the whole image is not.

Nothing here prints a file's bytes: only paths, sizes and sha256[:12].
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import zlib
from pathlib import Path, PurePosixPath

FORMAT = "azurik-custom-content"
SCHEMA_VERSION = 1
KINDS = {"variant": "variants/{id}/variant.json", "pack": "packs/{id}/pack.json"}
SUFFIXES = {"variants": (".json", ".glb", ".gltf", ".bin", ".png", ".md", ".azkp"),
            "clips": (".glb", ".gltf", ".bin", ".md"), "sounds": (".wav", ".md"),
            "fx": (".glb", ".gltf", ".bin", ".png", ".md"), "packs": (".json", ".md")}
"""The suffixes each folder's files may have (any letter case): a variant's recipe and the files AzurKit reads
beside it (glTF clips and meshes, PNG pictures) and its shipped answers (.azkp: AzurKit's recorded build of it at
the defaults, read only when AzurKit's own table lists its size and sha256), clips, sounds, effects' files, a pack's
JSON, and a note (.md)."""
TOPS = tuple(SUFFIXES)
ENTRY_KEYS = ("id", "kind", "title", "author", "licence", "version", "files", "requires")
FILE_KEYS = ("path", "sha256", "size")
MAX_MANIFEST = 1 << 20
MAX_FILE = 64 << 20
MAX_ENTRIES, MAX_FILES, MAX_ENTRY = 1000, 10000, 256 << 20
MAGIC_SPAN = 0x10020
ID = re.compile(r"[a-z][a-z0-9_]*")
SHA256 = re.compile(r"[0-9a-f]{64}")
ISO_NAME = re.compile(r"\.x?iso(\.\d+)?$")
PRIVATE_KEY = re.compile(rb"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----\r?\n")
DEVICE = re.compile(r"(con|prn|aux|nul|com[1-9¹²³]|lpt[1-9¹²³]) *(\..*)?", re.IGNORECASE)


def refused(rel: str, head: bytes) -> str | None:
    """Why a file ``rel`` whose first :data:`MAGIC_SPAN` bytes are ``head``
    can't be here, or ``None``."""
    name = rel.lower().rsplit("/", 1)[-1]
    if head[0x10000:0x10014] == b"MICROSOFT*XBOX*MEDIA":
        return "a game image (XISO volume descriptor at 0x10000)"
    if ISO_NAME.search(name):
        return "a game image or a part of one (.iso/.xiso/.iso.NNN name)"
    if head[:4] == b"QFI\xfb":
        return "a qcow2 disk image (an xemu HDD) at 0"
    if "eeprom" in name and name.endswith(".bin"):
        return "an EEPROM dump (eeprom*.bin name)"
    if head[:8] == b"AZL3SNAP":
        return "a guest RAM snapshot (console keys) at 0"
    if PRIVATE_KEY.match(head):
        return "a private key at 0"
    if head[:2] == b"\x1f\x8b":
        try:
            inner = zlib.decompressobj(31).decompress(head, MAGIC_SPAN)
        except zlib.error:
            return None
        if why := refused(re.sub(r"\.gz\Z", "", rel, flags=re.I), inner):
            return f"inside its gzip: {why}"
    return None


def _head(path: Path) -> bytes:
    with open(path, "rb") as f:
        head = f.read(MAGIC_SPAN)
        return head + f.read() if head[:2] == b"\x1f\x8b" else head


def tree(root: Path) -> list[str]:
    """Every file below ``root`` (POSIX paths, sorted), ``.git`` left out."""
    out = []
    for folder, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d != ".git"]
        out += [(Path(folder) / f).relative_to(root).as_posix() for f in files]
    return sorted(out)


def _path_fault(path) -> str | None:
    if not isinstance(path, str) or not path:
        return "is not a path"
    if "\\" in path or path.startswith("/") or ":" in path:
        return "is not a relative POSIX path"
    parts = path.split("/")
    if any(p in ("", ".", "..") for p in parts):
        return "has an empty, '.' or '..' part"
    if parts[0] not in TOPS or len(parts) < 2:
        return f"is not under {', '.join(t + '/' for t in TOPS)}"
    if device := next((p for p in parts if DEVICE.fullmatch(p)), None):
        return f"has {device!r}, a name Windows keeps for a device"
    suffix = PurePosixPath(path).suffix.lower()
    if suffix not in SUFFIXES[parts[0]]:
        return (f"is {f'a {suffix}' if suffix else 'a suffix-less'} file: {parts[0]}/ holds only "
                f"{', '.join(SUFFIXES[parts[0]])} files")
    return None


def _whole(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def check_manifest(doc) -> list[str]:
    """The manifest's own faults (its shape, ids, kinds, requires, paths),
    each naming where it is."""
    if not isinstance(doc, dict):
        return ["manifest.json: not a JSON object"]
    faults = []
    if doc.get("format") != FORMAT:
        faults.append(f"manifest.json: format {doc.get('format')!r} is not {FORMAT!r}")
    if doc.get("schema_version") != SCHEMA_VERSION:
        return faults + [f"manifest.json: schema_version {doc.get('schema_version')!r} is unknown "
                         f"(this check reads {SCHEMA_VERSION})"]
    faults += [f"manifest.json: unknown key {k!r}" for k in doc if k not in ("format", "schema_version", "entries")]
    entries = doc.get("entries")
    if not isinstance(entries, list):
        return faults + ["manifest.json: entries is not a list"]
    if len(entries) > MAX_ENTRIES:
        return faults + [f"manifest.json: {len(entries)} entries, over the {MAX_ENTRIES} a manifest may hold"]
    if (count := sum(len(e["files"]) for e in entries if isinstance(e, dict) and isinstance(e.get("files"), list))) \
            > MAX_FILES:
        return faults + [f"manifest.json: {count} files, over the {MAX_FILES} a manifest may list"]
    ids, claimed = {}, {}
    for i, entry in enumerate(entries):
        at = f"manifest.json: entries[{i}]"
        if not isinstance(entry, dict):
            faults.append(f"{at}: not an object")
            continue
        eid = entry.get("id")
        if isinstance(eid, str) and ID.fullmatch(eid):
            at = f"manifest.json: entry {eid!r}"
            if eid in ids:
                faults.append(f"{at}: the id is taken by entries[{ids[eid]}]")
            ids.setdefault(eid, i)
        else:
            faults.append(f"{at}: id {eid!r} is not [a-z][a-z0-9_]*")
        faults += [f"{at}: no {k!r}" for k in ENTRY_KEYS if k not in entry]
        faults += [f"{at}: unknown key {k!r}" for k in entry if k not in ENTRY_KEYS]
        faults += [f"{at}: {k} is not a non-empty string" for k in ("title", "author", "licence")
                   if k in entry and not (isinstance(entry[k], str) and entry[k].strip())]
        if "version" in entry and not (_whole(entry["version"]) and entry["version"] >= 1):
            faults.append(f"{at}: version {entry['version']!r} is not a whole number from 1")
        kind = entry.get("kind")
        if "kind" in entry and kind not in KINDS:
            faults.append(f"{at}: kind {kind!r} is not one of {', '.join(KINDS)}")
        files = entry.get("files")
        if "files" in entry and not (isinstance(files, list) and files):
            faults.append(f"{at}: files is not a non-empty list")
            files = []
        for j, f in enumerate(files or ()):
            where = f"{at}: files[{j}]"
            if not isinstance(f, dict):
                faults.append(f"{where}: not an object")
                continue
            faults += [f"{where}: no {k!r}" for k in FILE_KEYS if k not in f]
            faults += [f"{where}: unknown key {k!r}" for k in f if k not in (*FILE_KEYS, "licence")]
            if why := _path_fault(f.get("path")):
                faults.append(f"{where}: path {f.get('path')!r} {why}")
            else:
                where = f"{at}: {f['path']}"
                if (key := f["path"].lower()) in claimed:
                    faults.append(f"{where}: also listed by {claimed[key]}")
                claimed.setdefault(key, at.removeprefix("manifest.json: "))
            if "sha256" in f and not (isinstance(f["sha256"], str) and SHA256.fullmatch(f["sha256"])):
                faults.append(f"{where}: sha256 is not 64 lowercase hex digits")
            if "size" in f and not (_whole(f["size"]) and 0 <= f["size"] <= MAX_FILE):
                faults.append(f"{where}: size {f['size']!r} is not a whole number up to {MAX_FILE}")
            if "licence" in f and not (isinstance(f["licence"], str) and f["licence"].strip()):
                faults.append(f"{where}: licence is not a non-empty string")
        if (size := sum(f["size"] for f in files or () if isinstance(f, dict) and _whole(f.get("size")))) > MAX_ENTRY:
            faults.append(f"{at}: its files are {size} bytes, over the {MAX_ENTRY} an entry may hold")
        if kind in KINDS and isinstance(eid, str) and isinstance(files, list):
            own = KINDS[kind].format(id=eid)
            if own not in {f.get("path") for f in files if isinstance(f, dict)}:
                faults.append(f"{at}: a {kind} entry lists {own}")
        requires = entry.get("requires")
        if "requires" in entry and not (isinstance(requires, list) and all(isinstance(r, str) for r in requires)):
            faults.append(f"{at}: requires is not a list of ids")
    graph = {e["id"]: e["requires"] for e in entries if isinstance(e, dict) and e.get("id") in ids
             and isinstance(e.get("requires"), list)}
    for eid, requires in graph.items():
        faults += [f"manifest.json: entry {eid!r}: requires {r!r}, which no entry is" for r in requires
                   if isinstance(r, str) and r not in ids]
    faults += [f"manifest.json: entry {eid!r}: requires itself, through {' -> '.join(loop)}"
               for eid, loop in _loops(graph)]
    return faults


def _loops(graph: dict[str, list]) -> list[tuple[str, list[str]]]:
    """Each id whose requires lead back to it, with the way round."""
    out = []
    for start in graph:
        stack, seen = [(start, [start])], set()
        while stack:
            node, way = stack.pop()
            for nxt in graph.get(node, ()):
                if nxt == start:
                    out.append((start, [*way, start]))
                    stack = []
                    break
                if nxt in graph and nxt not in seen:
                    seen.add(nxt)
                    stack.append((nxt, [*way, nxt]))
    return out


def _listed(doc) -> list[tuple[str, dict]]:
    """``(entry id, file record)`` for every well-formed file record."""
    return [(e.get("id"), f) for e in doc.get("entries", ()) if isinstance(e, dict)
            for f in (e.get("files") if isinstance(e.get("files"), list) else ())
            if isinstance(f, dict) and _path_fault(f.get("path")) is None]


def check_files(root: Path, doc) -> list[str]:
    """Each listed file against its size and sha256, a variant's or pack's
    own file read as JSON, and every file in the tree: refused images and
    keys, and files under the content folders no entry lists."""
    faults, listed = [], {}
    for eid, f in _listed(doc):
        rel = f["path"]
        listed[rel] = eid
        path = root / rel
        if path.is_symlink() or not path.is_file():
            faults.append(f"{rel}: listed by {eid!r} but {'a link' if path.is_symlink() else 'missing'}")
            continue
        size = path.stat().st_size
        if size > MAX_FILE:
            faults.append(f"{rel}: {size} bytes, over the {MAX_FILE} a file may hold")
            continue
        data = path.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        if f.get("size") != size:
            faults.append(f"{rel}: {size} bytes, the manifest says {f.get('size')!r}")
        if f.get("sha256") != sha:
            faults.append(f"{rel}: sha256 {sha[:12]}, the manifest says {str(f.get('sha256'))[:12]}")
        if rel.endswith(("/variant.json", "/pack.json")) and rel.startswith(("variants/", "packs/")):
            try:
                own = json.loads(data.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                faults.append(f"{rel}: not UTF-8 JSON ({type(exc).__name__})")
                continue
            if not isinstance(own, dict) or (rel.startswith("variants/")
                                             and not all(isinstance(r, dict) for r in own.values())):
                faults.append(f"{rel}: not an object{' of recipes' if rel.startswith('variants/') else ''}")
    names: dict[str, str] = {}
    for rel, eid in listed.items():   # a recipe name is a picker row: one entry holds it
        if rel.startswith("variants/") and rel.endswith("/variant.json") and (root / rel).is_file():
            try:
                own = json.loads((root / rel).read_text(encoding="utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            for name in own if isinstance(own, dict) else ():
                if name in names and names[name] != eid:
                    faults.append(f"{rel}: recipe {name!r} is also entry {names[name]!r}'s")
                names.setdefault(name, eid)
    for rel in tree(root):
        path = root / rel
        if path.is_symlink() or not path.is_file():
            continue
        if why := refused(rel, _head(path)):
            faults.append(f"{rel}: refused: {why}")
        elif rel.split("/", 1)[0] in TOPS and rel not in listed:
            faults.append(f"{rel}: under {rel.split('/', 1)[0]}/ but no entry lists it")
    return faults


def write(root: Path, doc) -> None:
    """Fill in each listed file's sha256 and size from the file here, and
    rewrite manifest.json (two-space JSON, keys in place)."""
    for _, f in _listed(doc):
        path = root / f["path"]
        if path.is_file() and not path.is_symlink():
            data = path.read_bytes()
            f["sha256"], f["size"] = hashlib.sha256(data).hexdigest(), len(data)
    text = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    (root / "manifest.json").write_text(text, encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parent.parent,
                        help="the repository (default: this script's)")
    parser.add_argument("--write", action="store_true", help="fill in each listed file's sha256 and size first")
    args = parser.parse_args(argv)
    manifest = args.root / "manifest.json"
    if not manifest.is_file():
        print(f"manifest.json: missing in {args.root}")
        return 1
    if manifest.stat().st_size > MAX_MANIFEST:
        print(f"manifest.json: {manifest.stat().st_size} bytes, over {MAX_MANIFEST}")
        return 1
    try:
        doc = json.loads(manifest.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"manifest.json: not UTF-8 JSON: {exc}")
        return 1
    except RecursionError:
        print("manifest.json: not UTF-8 JSON: nested too deep")
        return 1
    if args.write and isinstance(doc, dict):
        write(args.root, doc)
    faults = check_manifest(doc)
    faults += check_files(args.root, doc) if isinstance(doc, dict) else []
    for fault in faults:
        print(fault)
    if faults:
        print(f"{len(faults)} fault(s)")
        return 1
    listed = _listed(doc)
    print(f"ok: {len(doc['entries'])} entries, {len(listed)} files ({sum(f['size'] for _, f in listed)} bytes) "
          f"match their size and sha256; {len(tree(args.root))} files hold no image, disk, EEPROM dump, "
          "RAM snapshot or key")
    return 0


if __name__ == "__main__":
    sys.exit(main())
