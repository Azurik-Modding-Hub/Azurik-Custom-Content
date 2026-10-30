# Contributing

Thank you for adding to Azurik-Custom-Content. Everything here is
installed by AzurKit's players, so each entry is checked file by file.

## What can go in

- Recipes (`variants/<id>/variant.json`) and pack definitions
  (`packs/<id>/pack.json`, an AzurKit mods file).
- The scripts and docs that make your assets.
- Your own original files: Blender clips (`.glb`), WAVs you hold the rights
  to, PNGs. Some of the game's bytes inside one are fine (a clip made on the
  game's skeleton, a texture painted over the game's).

## What never goes in

- The game's image (an ISO or XISO), whole or in parts that rebuild it.
- A patched game file (a built `default.xbe` or `.xbr`): a recipe rebuilds
  it from the player's own copy.
- Private keys, EEPROM dumps, xemu HDD (qcow2) images and RAM snapshots:
  they can hold console keys.
- Anything you don't hold the rights to.

`scripts/check.py` refuses the image, its parts and the key-holding files
anywhere in the tree; the rest is for the review.

## Adding or changing an entry

1. Put the files under `variants/<id>/`, `clips/`, `sounds/`, `fx/` or
   `packs/<id>/`. A path is where AzurKit installs the file in the player's
   content folder.
2. Add the entry to `manifest.json`, or change it (see the README's
   manifest). List every file; leave `sha256` and `size` to the check.
3. Bump the entry's `version` on any change to its files: AzurKit offers
   Update when it is higher than the player's copy.
4. Run `python3 -I scripts/check.py --write`: it fills in each listed
   file's sha256 and size, then checks everything. It must say `ok`.
5. Open a pull request.

Booblord's and Beamlord's recipes match AzurKit's own copies, which it
checks on Install: a change to one is made in AzurKit at the same time.

## Licence

Your contribution is under the MIT licence ([`LICENSE`](LICENSE)) unless a
file's `licence` in `manifest.json` says otherwise. Say whose a file is
there and in [`NOTICE.md`](NOTICE.md).
