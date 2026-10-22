# Arknights Index brand assets

Approved 2026-10-22. These marks belong to the Arknights Index fan project and are not official Arknights emblems. Game-related rights remain with their respective holders; see LICENSE and NOTICE.

- `masters/tower.png`: concept 01, archive tower/book/quotation marks. Use for favicon and compact identity.
- `masters/operator.png`: concept 02, rabbit-eared hood/dialogue. Use above the main search form and in the header.
- Both masters are 1254 × 1254 RGBA PNGs with transparent negative space. Preserve aspect ratio and clear space.
- `../web/brand/`: 16, 24, 32, 48, 64, 96, 128, 180, 192, 256, 512 and 1024px PNG exports of both marks, plus a multi-resolution favicon.ico and a theme-aware favicon.svg wrapper around the 64px raster. This wrapper is not a vector master.
- Regenerate deterministic size exports with `python scripts/export_brand.py`; do not upscale the master or generate each size independently.
- Charcoal/mint is the primary palette. The site uses a white monochrome CSS treatment on dark backgrounds.

The masters were prepared with the built-in image-generation tool from the approved concept sheets. Prompts requested extraction of only the emblem, removal of labels, wordmarks and duplicate marks, actual transparent alpha including interior cutouts, and preservation of the approved silhouette, seams and mint accent. Size exports use Pillow/Lanczos without creative edits.
