#!/usr/bin/env python3
"""Passport of the Republic of Meridia — make.fun entry (Python 3.13, stdlib only).

The program writes one image to /output/entry.png: an invented passport
spread for a country that isn't there. The image is pre-rendered by
tools/render_passport.py (Pillow, build time only) and shipped in
assets/passport.png; this entry program only copies it, so it runs in the
sandbox with no network, no clock and no randomness, and is byte-identical
on every run.
"""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "assets", "passport.png")
OUT = os.path.join(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"), "entry.png")

os.makedirs(os.path.dirname(OUT), exist_ok=True)
shutil.copyfile(SRC, OUT)
print("wrote", OUT)
