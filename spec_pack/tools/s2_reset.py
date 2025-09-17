#!/usr/bin/env python
import os, shutil
for p in ["spec_pack/s2/retro_rules.jsonl","spec_pack/s2/contested.jsonl"]:
    try: os.remove(p)
    except FileNotFoundError: pass
print("S2 artifacts reset.")
