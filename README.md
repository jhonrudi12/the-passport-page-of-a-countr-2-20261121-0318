# The Passport Page of a Country That Isn't There

[![make.fun](https://make.fun/badge/the-passport-page-of-a-countr-2-20261121-0318.svg)](https://make.fun/bounty/the-passport-page-of-a-countr-2-20261121-0318)
[![Rank](https://make.fun/badge/the-passport-page-of-a-countr-2-20261121-0318/jhonrudi12/the-passport-page-of-a-countr-2-20261121-0318/rank.svg)](https://make.fun/bounty/the-passport-page-of-a-countr-2-20261121-0318)
[![Reward](https://make.fun/badge/the-passport-page-of-a-countr-2-20261121-0318/jhonrudi12/the-passport-page-of-a-countr-2-20261121-0318/reward.svg)](https://make.fun/bounty/the-passport-page-of-a-countr-2-20261121-0318)

An invented passport spread for the **Republic of Meridia** — an island
republic that does not exist, whose capital is Port Aureline.

## The entry

`main.py` (Python 3.13, standard library only) copies the pre-rendered
spread in `assets/passport.png` to `/output/entry.png`. The image is
1024×1024 PNG, under 1 MiB, deterministic across runs, and needs no network.

The spread is drawn at build time by `tools/render_passport.py` (Pillow):

- **Left page — data page.** Lighthouse-and-compass emblem, "REPUBLIC OF
  MERIDIA / PASSPORT", holder Elara Miren Voss (born 14 Jun 1996 in
  Aureline), a flat-illustration portrait, issue 12 Mar 2024, expiry
  12 Mar 2034, and a machine-readable zone with real ICAO check digits.
- **Right page — visas & stamps.** A Kestrel Isles visitor visa (single
  entry, 30 days, issued 18 Jan 2025) with the condition "NO FISHING IN
  PROTECTED WATERS", six entry/exit stamps that tell one trip in order —
  Dunharrow (Sep 2024), Kestrel Isles (Jan 2025), Port of Sable (Jun
  2025), home to Aureline 25 Jun 2025 — and a harbour-tax stamp (12 AUR).
- **The telling detail.** A printed notice: *"This passport is not valid
  for travel to the Silent Isles. Quarantine in force since 2019."*

Every date agrees: no stamp predates the passport's issue, the visa sits
inside the passport's validity, and the travel history runs in order.

## Reproduce

```sh
python3 tools/render_passport.py   # renders assets/passport.png
python3 main.py                    # writes /output/entry.png
```

## License

MIT — see `LICENSE`.
