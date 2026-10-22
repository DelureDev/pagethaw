# Reconstruction and portability improvements

Owner authorized work on PageThaw after the 1.1 editable-mode release. Keep the
existing two modes, explicit font choices, offline conversion, DOCX-only outputs
and private samples/fonts outside Git and releases. Lead is the sole writer.

- [x] Classify previously rejected PDFs; select bounded, general reconstruction rules.
- [x] Support simple ruled tables as editable Word tables, with safe rejection of ambiguity.
- [x] Improve paragraph indentation/alignment and spacing without fixed text boxes.
- [x] Add optional permitted font embedding with clear EN/RU portability feedback.
- [x] Strengthen structural checks, regression tests and actual Word/editing review.
- [x] Build/test one consolidated portable update, publish and verify downloads.

Acceptance: preserve source wording/emphasis and every accounted graphic; real
paragraphs and expanding cells; reject unsupported/ambiguous layouts before output;
never silently replace fonts or override embedding restrictions. Preserve layout
must retain its prior output when font embedding is off. Exact pagination for all
PDFs and OCR are outside this mission.

Native routing_scout (requested Luna/high) performs read-only corpus classification;
native routing_architect (requested Astra/low) advises on font portability. Both
roles were accepted by runtime; exact backend identities not separately verified.
No fallback. Independent code/visual review follows implementation.

PageThaw 1.2 is published. Current checks: 120 tests
passed; 35 layout outputs match published baseline by every uncompressed DOCX
part; 14 editable files/27 rendered pages passed independent review. Another
8 proof pages, 9 heavily edited pages and 3 table images passed visual review.
The same 21 complex corpus documents remain explicitly unsupported in editable
mode; complete synthetic grids cover the new bounded table support.

Independent native routing_reviewer roles (requested Sol/high; runtime accepted)
reviewed code and all final images. Fixed unrepresentable border widths, Word cell
property ordering and a wrapped separator. Final code and visual verdicts passed.
Initial font portability proof was inadequate: its new Cyrillic character used
a fallback. Corrected proof uses the actual converter emitter, an uninstalled
synthetic font and checks every non-space glyph's rendered font and metrics after
Word editing/save/reopen. It passed independent recheck. Font bytes in PageThaw
output match the original; Word rewrites internal name/checksum on resave while
retaining all outlines, metrics, characters and permissions.

Native Russian UI screenshot inspected and saved to `docs/images/app-ru.png`.
SHA256 `47ac7120c854d3db6d9c03b36d52294fefc309762b3bd8eedc46b5856ec93c0f`;
source is the empty native 1.2 preview, consumed by both READMEs, no Figma mapping.
English/Russian state and switching pass automated widget checks. A further native
click was stopped when the helper detected user input; the owned preview was
closed. No user Word windows, font installations or other apps were changed.
Private evidence remains under `.private/editable/reconstruction-*`, `grid-proof`
and `font-portability-g`.

**Passed:** [hosted Windows tests](https://github.com/DelureDev/pagethaw/actions/runs/39827355699)
and [build/fresh-VM checks](https://github.com/DelureDev/pagethaw/actions/runs/39827355708).
The exact downloaded EXE/ZIP passed local relocation with clean preferences,
Windows-only PATH, Cyrillic paths and synthetic font/table smoke checks. Release
EXE output matches all 14 reviewed editable documents and all 35 layout baseline
documents by every internal DOCX part. Original input hashes stayed unchanged.

Implementation `0dcb8b52193902f4b70741c33f7d87e7b612619d` was fast-forwarded into
main and published as [v1.2.0](https://github.com/DelureDev/pagethaw/releases/tag/v1.2.0).
Public EXE, ZIP and checksums were downloaded again and match the exact tested
assets. Private proof: `reconstruction-public-download/verification.json` under
`.private/editable`; hashes and limits are in [verification](VERIFICATION.md).
No private fonts/documents were published. No remaining work in this mission.
