"""Deterministic check for outcome-1: python evals/check_outcome.py <run folder>. Prints JSON; exit 1 on failure."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

run = Path(sys.argv[1])
still = np.array(Image.open(run / "machine.png").convert("RGBA"))
sheets = list(run.rglob("machine-use-10f.png"))
res = {"sheet_found": bool(sheets)}
if sheets:
    s = np.array(Image.open(sheets[0]).convert("RGBA"))
    res["size"] = [s.shape[1], s.shape[0]]
    ok_size = s.shape[:2] == (48, 480)
    frames = [s[:, i * 48:(i + 1) * 48] for i in range(10)] if ok_size else []
    inside = np.zeros((48, 48), dtype=bool)
    inside[30:38, 16:28] = True
    res["frame0_equals_still"] = bool(frames and (frames[0] == still).all())
    res["changed_outside"] = int(sum(((f != still).any(-1) & ~inside).sum() for f in frames)) if frames else None
    res["moves_inside"] = bool(frames and any(((f != still).any(-1) & inside).any() for f in frames))
    res["pass"] = bool(ok_size and res["frame0_equals_still"] and res["changed_outside"] == 0 and res["moves_inside"])
else:
    res["pass"] = False
print(json.dumps(res))
sys.exit(0 if res["pass"] else 1)
