# Contributing

Use a new branch and synthetic test inputs. Keep conversion conservative: an
unsupported-feature message is preferable to silently losing or revealing text.

Run `python -m pytest -q`. For changes affecting layout or fonts, export synthetic
results through desktop Word and review every page. Record the Word/version and
coverage; passing XML checks alone does not establish visual parity.

Never add personal PDFs, converted client documents, licensed font files, machine
profiles, credentials or output folders. Font tests should use an installed
system face or a clearly licensed fixture with attribution. Keep replacements
explicit, and never alter a font's embedding-permission flags.

Submit focused pull requests with the problem, behavior change and validation.
Please discuss OCR, paragraph reflow or new platform support before large changes.
