# Azurik-Custom-Content

Community characters and patch packs for AzurKit, the modding toolkit for
*Azurik: Rise of Perathia*. AzurKit lists each entry here beside its own,
marked community: variants in its Characters pickers (packs in its Patches
tab are to come). **Install** and **Update** there fetch them, on the
website and in the app.

| Entry | Kind | What it is |
|---|---|---|
| `booblord` | variant | Booblord, a townswoman who carries Garret's staff, in four looks (Booblord, Booblord High, Booblord Human, Booblord High Human), with her own moves and idles (Blender clips) and voice (WAVs) |
| `beamlord` | variant | Beamlord, Balthazar gone mad with his lightning: his recipe alone (his moves, sounds and effects are made at build time from the game's own) |

A recipe rebuilds everything from the player's own copy of the game. There
is no game image here, and no patched game file.

## How AzurKit installs from it

- **Content from:** a setting in the Characters tab. It defaults to
  `https://raw.githubusercontent.com/Azurik-Modding-Hub/Azurik-Custom-Content/main/`;
  the app also takes a folder, such as a clone of this repository.
- **Install** reads `manifest.json`, then fetches each file of the entry and
  of the entries it `requires`. It checks every file's size and sha256 before
  it writes anything: one that differs fails the install, naming the file,
  and nothing is written. The files go into the content folder under the
  same paths as here, and `installed.json` is written last.
  - The app's content folder is `content` in AzurKit's user data folder, or
    the folder `AZURKIT_CONTENT` names.
  - The website keeps the files in the browser's storage (IndexedDB).
- **Update:** an installed entry stays at its version, even when a newer one
  is here, until you press Update. Update installs the new version the same
  way and removes the files it no longer lists.

## Layout

A file has the same path here and in the player's content folder.

```text
manifest.json                 the entries and every file's sha256 and size
variants/<id>/variant.json    a variant's recipes, {name: recipe}
clips/<name>/*.glb            clips the engine reads at its own paths (booblord's moves and idles)
sounds/<name>/*.wav           sounds the engine reads at its own paths (booblord's voice)
fx/<name>/...                 effects' files, likewise
packs/<id>/pack.json          a pack: an AzurKit mods file (none yet)
scripts/check.py              the check below
```

## The manifest

```json
{"format": "azurik-custom-content", "schema_version": 1,
 "entries": [{"id": "booblord", "kind": "variant", "title": "Booblord",
              "author": "Azurik-Modding-Hub", "licence": "MIT", "version": 1,
              "files": [{"path": "clips/booblord/moves.glb", "sha256": "...", "size": 588416}],
              "requires": []}]}
```

- `id`: lowercase letters, digits and `_`, starting with a letter; unique.
- `kind`: `variant` (it lists `variants/<id>/variant.json`) or `pack` (it
  lists `packs/<id>/pack.json`). A variant entry's recipe names are its rows
  in the pickers.
- `version`: a whole number, bumped by any change to the entry's files.
- `files`: each one's path, sha256 and size. A file's own `licence` takes the
  place of the entry's.
- `requires`: other entries' ids, installed with it.

## Checking

```bash
python3 -I scripts/check.py           # exit 0, or 1 with one line per fault
python3 -I scripts/check.py --write   # first fill in each listed file's sha256 and size
```

It checks the manifest's shape, every listed file's size and sha256, that
every file under the content folders is listed, and that nothing here is a
game image or a part of one, a disk image, an EEPROM dump, a RAM snapshot or
a private key. Python 3.10 or later, no packages.

## Licences

- Our own work (the recipes, booblord's clips, the docs and the script) is
  under the MIT licence ([`LICENSE`](LICENSE)).
- Booblord's eight WAVs (`sounds/booblord/*.wav`) are the repository owner's
  own sounds, used with the owner's permission, and are not under the MIT
  licence ([`sounds/booblord/README.md`](sounds/booblord/README.md)).
- Any bytes of *Azurik: Rise of Perathia* inside a file belong to the game's
  rights holders and are not under the MIT licence.

[`NOTICE.md`](NOTICE.md) says the same, file by file. To add your own, see
[`CONTRIBUTING.md`](CONTRIBUTING.md).
