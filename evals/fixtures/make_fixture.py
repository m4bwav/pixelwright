"""Draw the eval fixture: a 48x48 machine with a furnace mouth, a cyan screen and a vent with sky above.

python evals/fixtures/make_fixture.py <out.png>
"""
import sys

import numpy as np
from PIL import Image

a = np.zeros((48, 48, 4), dtype=np.uint8)
a[18:48, 6:42] = [105, 105, 115, 255]          # body
a[18:48, 6:42:4] = [70, 70, 80, 255]           # panel seams
a[30:38, 16:28] = [40, 30, 30, 255]            # furnace mouth frame
a[31:37, 17:27] = [220, 110, 30, 255]          # embers
a[32:36, 19:25] = [250, 170, 60, 255]          # hot core
a[22:27, 32:39] = [40, 180, 220, 255]          # screen
a[10:18, 10:14] = [80, 80, 90, 255]            # vent pipe, sky above
Image.fromarray(a, "RGBA").save(sys.argv[1] if len(sys.argv) > 1 else "machine.png")
