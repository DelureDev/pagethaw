# Reconstruction and portability improvements

Owner authorized work on PageThaw after the 1.1 editable-mode release. Keep the
existing two modes, explicit font choices, offline conversion, DOCX-only outputs
and private samples/fonts outside Git and releases. Lead is the sole writer.

- [x] Classify previously rejected PDFs; select bounded, general reconstruction rules.
- [x] Support simple ruled tables as editable Word tables, with safe rejection of ambiguity.
- [x] Improve paragraph indentation/alignment and spacing without fixed text boxes.
- [x] Add optional permitted font embedding with clear EN/RU portability feedback.
- [x] Strengthen structural checks, regression tests and actual Word/editing review.
- [ ] Build/test one consolidated portable update, publish and verify downloads.

Acceptance: preserve source wording/emphasis and every accounted graphic; real
paragraphs and expanding cells; reject unsupported/ambiguous layouts before output;
never silently replace fonts or override embedding restrictions. Preserve layout
must retain its prior output when font embedding is off. Exact pagination for all
PDFs and OCR are outside this mission.

Native routing_scout (requested Luna/high) performs read-only corpus classification;
native routing_architect (requested Astra/low) advises on font portability. Both
roles were accepted by runtime; exact backend identities not separately verified.
No fallback. Independent code/visual review follows implementation.

Implementation is ready for the 1.2 release candidate. Current checks: 120 tests
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
and `font-portability-g`. CI/package/publication checks are pending.
