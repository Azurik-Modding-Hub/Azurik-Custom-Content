# Booblord's sounds

**Origin and licence:** the owner's own sounds, used with the owner's
permission, 2026-10-21 (D405: "i am allowed to use them, they can go into
the repo and will go into our custom assets repo later"); to move to
Azurik-Modding-Hub/Azurik-Custom-Content (D392-D396). They are not game
data, and this repository's MIT grant doesn't cover them (`NOTICE.md`).

Booblord's recipe (`azurik_mod/assets/variants.json`: its `wavs` and its
`shouts`) plays them (Step 2.144; D405-D408); every attack of her own spins
plays a synthesized whoosh (her finishers' `finisher` shouts went with Step
2.180, D699) and her death stays silent. With any other weapon than her
spins her `shouts` (`attack1.wav`, `attack2.wav`, `shout.wav`: `shout` ..
`shout_b`, one at random) play as each attack starts where Garret shouts
(Step 2.183, D705). Each file is
the owner's as given (sha-checked copies; the three long names
shortened), mono 16-bit PCM at 44.1 kHz; the build makes each a mono
22050 Hz Xbox ADPCM wave under `fx/sound/v/booblord/` and its log names
each file's sha256.

| File | Plays | sha256 | The owner's file |
|---|---|---|---|
| `hit.wav` | `hurt`, take 1: a hit (the 6 hurt slots) | `4c7f4ef7fd86f051098330c33886d4c337fa7b4033ce4122ef7e35921e660d43` | `hit.wav` |
| `attack1.wav` | `hurt`, take 2 (one plays at random); with another weapon `shout`, take 1 | `c12307a2c7c0759ba1e9e005c86e6f272e29162d93302161f234058227429b17` | `attack1.wav` |
| `roll.wav` | `roll`: the roll | `353b09e9fa256668dfd7cd8f4ed42d06b4467f82b6c554cbc51a7193f45fe40c` | `roll.wav` |
| `hup.wav` | `jump`: a jump (the wing flap keeps Garret's) | `44ccda1eb27bb6d14ed6f7039679f9cfb41df187cddcbda393bd7b4c77038dfc` | `woman-30-year-old-non-native-english-speaker-czech-fight-vocalization-attacking-panting-very-short-breathing-3.wav` |
| `fall.wav` | `fall`: a long fall's landing (the fall damage) | `495c8f7976c00f01c483d6df515266ecc8f539bc86aa16592838b3ce534cab0c` | `fall.wav` |
| `grunt.wav` | `climb`: the ledge hoist and the climb over a ladder's top | `b2a5414fefeddb5e724d81e5e58160f14b8bb9fcd6b2747ffd6db581c1001b0c` | `woman-30-year-old-non-native-english-speaker-czech-fight-vocalization-attacking-panting-very-short-breathing-12.wav` |
| `attack2.wav` | with another weapon `shout`, take 2 | `48a7724da6646ee105afb663c92b0f7be711416fdddf1b5382f9525cdb4f92ed` | `attack2.wav` |
| `shout.wav` | with another weapon `shout`, take 3 (one plays at random) | `971d18a88af243a817932f462a372c73c137afa958f421823b7150e12817d29c` | `woman-30-year-old-non-native-english-speaker-czech-fight-vocalization-attacking-shouting-short-sporty-7.wav` |
