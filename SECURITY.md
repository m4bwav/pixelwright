# Security

`pxw.py` reads local images, JSON and palette files, writes images, JSON and `.gpl` palettes to the folder you
name, and `pxw.py review` serves a page on `127.0.0.1` only. It makes no network calls. The PixelLab fallback is run by the agent, with the key read
from the `PIXELLAB_API_KEY` environment variable; never write a key into a brief or any file in a repository.

Report a vulnerability privately through the repository's GitHub security advisories, or to the author's GitHub
profile contact.
