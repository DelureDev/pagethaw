# Project state

## 1.2.1 spacing correction — published and verified

2026-10-23: the owner's latest DOCX still overflowed after fixing fonts. Direct
GDI readback confirms the active ALS Sirius regular/bold faces are original
1.006. Old PDF Sirius aliases remain in registry inventory but are not active;
the initial alias-based experiment was invalid and discarded. No fonts or user
documents were changed by this work.

Implemented responsive leading for uniform measured text with explicit OpenType
typographic metrics. Single rows use only repeated tight adjacent-row evidence
within the same flow container, taking the roomier advance at transitions. This
is a tested approximation of row spacing, not recovery of invisible PDF paragraph
semantics. Legacy/ambiguous metrics retain expanding minimum spacing. Empty table
separators occupy one twip; caption paragraph marks carry their own font metrics.
Text sizes, content checks and growing fields remain intact.

**Passed:** 126 tests; source hashes unchanged; all 35 Preserve layout DOCX files
match the published baseline by every uncompressed part. The editable corpus
still accepts 14 and rejects 21; all 22 current Word pages independently reviewed.
Three representative forms (8 pages), 9 ordinary edited pages and 9 enlarged-text
stress pages passed independent visual review. The latter survived actual Word
save/reopen with exact text preservation and no fixed row heights/text boxes.
The reported form's whole section 4 fits page 1 again; two source-page-2 tail lines
still appear on page 3. Do not claim identical pagination or universal Word metrics.

Private evidence: `.private/editable/spacing-fix` (`implementation-2`, `edits-2`,
`tall-edit-2`, `corpus-2`, `layout-regression-2-verification.json`). Initial
prototype and historical alias renders are not release evidence. Native roles
`routing_architect` (requested Astra/low) and `routing_reviewer` (requested
Sol/high) were accepted; exact backend settings were not separately verified.
Architect advised conservative evidence and warned about paragraph-gap ambiguity;
lead selected the documented local approximation after real Word testing. Reviewer
passed code and all affected renders. No fallback, no subagent writes.

**Passed:** hosted tests `39922446099` and build/fresh-VM `39922445844`, both
portable formats relocated locally with clean preferences, Cyrillic paths and
no external Python on PATH. Exact EXE output matches all source-converter DOCX
parts for 14 editable files and the published baseline for all 35 layout files.
Editable artifact tests used the registered original-font aliases; after only
normalizing those family names, every part matches the visually reviewed files.
No fonts were activated/reinstalled to make a test pass.

**Published:** [1.2.1](https://github.com/DelureDev/pagethaw/releases/tag/v1.2.1)
from source commit `0059081eca5625ee78969e2abe97306045fe4f2b`, integrated into
local/public main. All three public downloads match the tested hosted bytes.
The verified EXE is copied to the user's Downloads folder. A separately named
corrected DOCX is in their PageThaw-output folder; originals remain untouched.
The exact destination/hash is recorded privately in `spacing-fix/delivery.json`.
This spacing mission is complete; no further tasks are queued. **Not run:**
physical printing and other Word versions. The historical reports below are not
current evidence, and old registered font aliases may still need user cleanup.

**PageThaw 1.2 is published:** [release and downloads](https://github.com/DelureDev/pagethaw/releases/tag/v1.2.0).
It improves paragraph/table reconstruction and adds optional permitted font
embedding. Implementation commit `0dcb8b52193902f4b70741c33f7d87e7b612619d`
is integrated into local/public main. All 120 tests, independent code review,
27-page corpus review and editing stress checks passed. Font portability was
verified in Word with an uninstalled synthetic font, including a newly typed
Cyrillic glyph after save/reopen. Hosted build/fresh-VM and both portable-format
relocation checks passed. The exact release EXE matches all 14 reviewed editable
documents and all 35 layout baseline documents by every uncompressed DOCX part.
Public EXE, ZIP and checksums were downloaded again and match the tested bytes.
This mission is complete. See [completed plan](RECONSTRUCTION_PLAN.md) and
[verification](VERIFICATION.md). Private evidence is under `.private/editable`;
use `.private/editable/reconstruction-public-download` for the verified local app.
Three reviewed sample DOCX files are in `output/editable-reviewed-1.2`; prior
samples and all originals remain unchanged.
The 1.1 results below are historical baseline.

## Post-release typography report — diagnosed, not fixed

On 2026-10-22 the owner supplied an original PDF and its actual 1.2 DOCX for
comparison. All three pages of each were inspected after isolated desktop Word
export at equal scale. **Passed:** source sizes (7.5 pt body / 10 pt heading),
source-file hash preservation, and document/style XML equality to the reviewed
fixture after normalizing font names. **Failed:** font identity and spacing fidelity.
The supplied DOCX's regular family resolves locally to Sirius 0.950 rather than
the verified 1.006 outlines; its bold family has both versions installed.
No font installation or original document was changed.

Independent read-only `routing_reviewer` (requested Sol/high; runtime accepted,
backend identity not separately verified) confirmed that measured paragraph
leading remains `AT_LEAST` in `Writer.text`. Word expands it to the chosen font's
natural height. Thirty-four multiline paragraphs specify 8.7–9.2 pt leading;
rendering with verified original fonts still drifts vertically, and drifts more
than with the older font. A font-only fix is insufficient. Earlier editability
checks did not establish source-spacing fidelity.

Next: validate a bounded leading correction for reliably measured narrative
paragraphs against tall glyphs, descenders, inserted sentences and enlarged text.
Do not globally force exact line heights or constrain expanding form/table rows.
No grouping defect was established. This turn is diagnostic: **not run** a fix,
new test suite or release. Private evidence and both sets of three-page renders
are in `.private/editable/user-miniphlebectomy-12`. Preserve layout is unaffected
by this diagnosis; it was not rerun for this report.

**PageThaw 1.1 is published:** [release and downloads](https://github.com/DelureDev/pagethaw/releases/tag/v1.1.0).
Normal paragraph-based Word editing after feedback
about floating text boxes. Local implementation, 97 tests, independent code review,
27-page corpus review and three edited-document stress checks passed.
See [completed editable conversion plan](EDITABLE_PLAN.md). Implementation commit
`a0220c5b2790721314c219d2a02416584e9124d0` is integrated into local/public main.
Hosted portable build/fresh-VM and local relocation checks passed. Exact EXE output
matches all 14 reviewed editable documents; all 35 layout regression outputs match
the published 1.0 output. Public EXE, ZIP and checksum downloads match the tested
bytes. This mission is complete. Private evidence is in `.private/editable`;
three reviewed samples are in `output/editable-reviewed-1.1`.

The public release is built by CI, not the earlier local `dist/1.1.0` prototype.
Use the release assets (or `.private/editable/published-download`). No private
documents or font files were published. Native EN/RU screenshots were inspected;
further mode-click checks were stopped when the helper reported user input.
Mode switching/persistence is covered by tests. The initial empty local preview
window may remain open; do not confuse it with the final downloaded build.

## Product decisions

- Offline Windows app; single EXE is the main download, folder ZIP is optional.
- GUI defaults to Editable text: ordinary paragraphs and expanding form cells.
  Preserve layout retains positioned text boxes. Mode choice is explicit and saved.
  Fonts remain visible; missing or
  unverified fonts require an explicit choice. Never silently substitute.
- Remember language, output folder and approved fonts; revalidate file hashes,
  PDF identity or fresh glyph proof, coverage and installed-family conflicts.
- Output folders contain only DOCX files. Repeated conversion preserves existing
  files with numbered names. Retry targets failed/cancelled files only.
- English and Russian interface, clear details for errors and optional Word comparison.
- Optional font embedding is off by default. Only eligible static TrueType faces
  are included; skipped faces get a visible notice. Original Sirius fonts remain
  private and require installation because their permissions allow preview/print only.

Selectable horizontal text and consistent-sized pages are supported. Scans/OCR,
rotated text and interactive PDF fields remain outside scope. Conversion does not
require Word; desktop Word is the reference viewer. Text boxes do not reflow like
ordinary paragraphs, and pixel-identical rendering is not guaranteed.

## Historical 1.0 verification

- 79 local tests passed, as did hosted Windows tests and independent code review.
- 68 distinct local PDFs exercised: 50 passed preflight, 36 converted into 49 pages,
  14 needed unavailable fonts, and 18 were unsupported. All original hashes stayed
  unchanged. All 49 converted pages were visually reviewed against the original.
- Final EXE output matches every uncompressed DOCX part of all 36 reviewed files.
  Source/portable metric differences caused by optional helper startup were fixed
  with an explicit core setting and a meaningful regression test.
- Real file locks, damaged/missing inputs, mixed batch continuation, blocked output
  paths and 50-item cancellation passed. No partial outputs remained.
- Native EN/RU UI inspected. The public preview is an empty Russian 1.0 app window.
- Both portable formats passed relocation tests and a separate hosted Windows VM
  test without Word/private fonts, external Python on PATH or existing settings.
  The hosted image still has developer tools installed; this is not a claim that
  Python was uninstalled. Bundled runtime imports were checked.
- Release EXE, ZIP and checksums were downloaded after publication and matched the
  tested files. Package audits exclude private documents/fonts and unused AI modules.

[Build and portable job evidence](https://github.com/DelureDev/pagethaw/actions/runs/39796148192)
and [Windows test evidence](https://github.com/DelureDev/pagethaw/actions/runs/39796147864).
See [verification details](VERIFICATION.md) for coverage and limits.

**Not run:** physical printing, Windows Sandbox, Word web/mobile or LibreOffice.
The executable remains unsigned. These limits are documented, not release blockers
for the agreed scope.

## Handoff and privacy

The owner authorized autonomous local corpus testing and this public release.
Private PDFs, licensed fonts, generated documents and machine-specific evidence
remain ignored under `.private/v1.0.0`; none were committed or uploaded. Original
files and the user's open Word/app sessions were preserved. Existing test app
windows may still be open; do not overwrite their executable files.

Native `routing_scout` roles requested gpt-6-luna/high for bounded corpus and
Windows-environment inventories. Native `routing_reviewer` roles requested
gpt-6.1-sol/high for independent code review, metric diagnosis and visual review.
The runtime accepted those roles; exact backend identities were not separately
inspected. Reviews passed after fixes; no fallback was used. The lead was the sole
writer and integrated the verified branch into main.

For 1.1, native `routing_architect` (requested Astra/low) advised on the bounded
conversion approach and `routing_reviewer` (requested Sol/high) independently
reviewed code and all 27 corpus pages. Both roles were runtime-accepted; exact
backend identities were not separately verified. Findings were fixed/retested,
final reviews passed, and no routing fallback was used. The lead remained sole writer.

For 1.2, native `routing_scout` (requested Luna/high) classified the corpus,
`routing_architect` (requested Astra/low) advised on font portability, and two
`routing_reviewer` agents (requested Sol/high) independently reviewed code and
rendered pages. Runtime accepted these roles; exact backend identities were not
separately verified. Border width/schema issues, a wrapped separator and an
inadequate initial font proof were fixed and rechecked. Final reviews passed;
no fallback. The lead was the sole writer. The native Russian preview was
inspected; further native interaction stopped on detected user input. EN/RU
switching/persistence passed automated widget checks. User apps stayed untouched.
