# Project state

## 1.3.5 — long headings beneath logos (published)

2026-10-28: the shared editable converter now takes only a contiguous prefix of
heading lines beside a left-hand logo. A wider line underneath the logo ends the
prefix; later narrow lines remain in ordinary body paragraphs in source order.
Previously a later narrow line could be pulled ahead of that wider line, correctly
triggering the text/order verification gate. The gate and typography checks are
unchanged. No document names, text or font-specific overrides were added.

**Passed:** 208 tests, source portable smoke, independent code review and all four
native Word comparison pages of the reported form (both editable modes). It stays
two pages with 24 fields and normal editable text; no clipping/overlap observed.
**Passed:** previous 40-file corpus plus the two recently supported forms in each
mode: acceptance unchanged (21 accepted / 21 rejected), and all accepted DOCX
parts identical to 1.3.4. Original inputs unchanged. Private evidence:
`.private/lift-2026-10-28`.
**Passed:** build/package audit, both portable relocations, EN/RU controls,
18 frozen modules and 18 synthetic DOCX files equal the tested source.
Hosted Windows checks `40693567348` and build/fresh-VM `40693604039` passed at
`e36413b61109421fc33ad92f1fc7a31b16d36357`; downloaded hosted evidence confirms
new heading-order smoke. All 208 tests passed after main integration.
[1.3.5](https://github.com/DelureDev/pagethaw/releases/tag/v1.3.5) publishes the
tested local build. Public EXE/ZIP/checksums downloaded again and match local
bytes/hashes. The separate hosted binary was not locally relocated. Verified EXE
is in Downloads; corrected LIFT DOCX is in `PageThaw-output/test-1.3.5`.
Private `release-verification.json` records exact hashes and readback. Complete.
**Limits:** matching fonts required; some spacing/wrapping differs. Other Word
versions and physical printing not run. No font installation or substitution.
Read-only independent reviewer reused routing_reviewer (requested Sol high,
runtime accepted role; backend identity not independently confirmed). Lead writer.

## 1.3.4 — form borders and rectangular text highlights (published)

2026-10-28: preserve source border thickness/color in bordered prose forms. A
continued table uses top/bottom borders only on its actual first/last cells,
leaving page boundaries open while retaining ordinary editable paragraphs.
Plain rectangular PDF Highlight annotations become character-level Word shading.
Annotation quads, isolated appearances, nested blend resources, opacity and actual
compositing are verified before removal from an in-memory copy. Arbitrary graphic
text overlaps, partial glyphs and unsupported custom highlight effects stay blocked.
The original PDF and the caller's in-memory annotations/trailer are unchanged.

**Passed:** 204 tests plus the final source-preservation focused checks; source
portable smoke includes highlights and border styles. Independent code review and
all 16 native Word comparison pages (two reported forms plus a prior reference,
both editable modes) passed.
The forms remain three and two pages, respectively. Text/order/emphasis pass;
no frames, positioned text or fixed row heights. Native Word edit/save/reopen
checks passed for expanding table text and insertion inside highlighted text.
**Passed:** prior 40-file corpus in each mode retains 19 accepted / 21 rejected.
Twelve accepted files change only border size/color XML; seven match every part.
No private PDF/font is public. Evidence: `.private/borders-relatox-2026-10-28`.

**Passed:** local build/package audit, relocation of both portable formats,
EN/RU controls, 18 frozen modules and 16 synthetic DOCX files equal source.
Hosted Windows checks `40689228330` and build/fresh-VM `40689269587` passed at
`a11a872f0f2fb1fd20c055b02e7b92ded697f43d`; hosted evidence was downloaded and
verified. All 204 tests passed after integration into main.
[1.3.4](https://github.com/DelureDev/pagethaw/releases/tag/v1.3.4) publishes the
tested local build. Public assets were downloaded again and match local bytes and
checksums. The separate hosted binary was not locally relocated. Verified EXE is
in Downloads; both corrected DOCX files are in `PageThaw-output/test-1.3.4`.
Hashes and readback: private `release-verification.json`. Original files unchanged.
**Limits:** custom/rounded/skewed/overlapping highlights remain unsupported;
shading preserves the plain visible highlight, not PDF annotation comments.
Matching fonts are still required; installed font conflicts are unchanged.
Some wrapping/page positions can differ. Other Word versions/printing not run.

Read-only review: requested routing_reviewer gpt-6.1-sol/high; runtime accepted
role selection, backend identity not independently confirmed. Lead sole writer.
The reviewer found a custom appearance blend mismatch, fixed and retested before
PASS; final adversarial checks also reject unused or nested custom blend states.

## 1.3.3 — inline squares and continued bordered prose (published)

2026-10-28: the owner's new three-page form adds empty square outlines inside
text and a bordered prose section spanning two PDF pages. The shared editable
converter now recognizes unambiguous squares within whitespace and complementary
three-edge borders near adjacent page edges. Squares become inline outline images,
not clickable controls; prose stays in normal paragraphs in one expanding table.
Paragraph rows let Word paginate that table without moving the entire section.
Marked squares, overlapping graphics and unmatched continuation paths stay guarded.

**Passed:** 196 tests, source smoke, independent code and six-page visual review,
native Word edit/save/reopen with two inline squares retained, and both modes of
the earlier 40-file corpus (unchanged acceptance and all accepted DOCX parts).
The new PDF converts to three pages in both modes with 26 fields, all four squares
and its logo. Some wrapping/border rendering differs; one retained-mode word moves
from the first page to the second. No pixel-identity claim. Original file unchanged.

**Passed:** local portable build and relocation of both formats, EN/RU widgets,
new synthetic inline-square/continuation smoke, 17 frozen modules equal source
and 14 synthetic DOCX outputs equal source by every part.
**Passed:** hosted Windows checks `40684007882` and build/fresh-VM checks
`40684008317`, source `86637d4b9d954065f36c2d8f57d61bb77e76a352`. All 196 tests
passed again after integration into main. [1.3.3](https://github.com/DelureDev/pagethaw/releases/tag/v1.3.3)
is published using the tested local build. Public EXE/ZIP/checksums were downloaded
and equal the tested local bytes. Hosted candidate download stalled and was stopped;
local relocation of that separate hosted build was **not run**. The published local
build passed relocation and source equivalence before upload. Verified EXE is in
Downloads; the reviewed DOCX is in `Downloads/PageThaw-output/test-1.3.3`.
The earlier installed-font alias conflict remains separate: real-file QA used
fresh GDI/glyph verification of the owner's active original font faces, not a
bypass in the app. No font installation, registry change or substitution occurred.
Private evidence: `.private/rrs-2026-10-28`. No private documents/fonts are public.
Exact asset hashes and readback evidence: `release-verification.json` in that folder.
The new-layout adaptation is complete; the existing font-registration issue remains
separate and was disclosed to the owner.

Independent read-only review requested `routing_reviewer` (gpt-6.1-sol/high),
accepted by the runtime; backend identity not independently confirmed. No fallback.
Lead is sole writer. Other Word versions/printing were not run; UI layout unchanged.

## 1.3.2 — editable blank spacing and date rules (published)

2026-10-26: the shared editable converter uses measured PDF field edges instead
of adding font-sized padding to every label. Real whitespace remains outside
blank rules. Date-year underscores following day/month blanks use the same
expanding ruled cells; numeric prefixes, unit suffixes and identifiers stay text.
Body text, font sizes, normal paragraphs and both editable modes are preserved.

**Passed:** 190 tests, source smoke, independent code review, all 50 newly rendered
native Word comparison pages (12 changed documents per editable mode), and a
native Word multiline-field edit/save/reopen test. The reported form stays three
pages. The existing 35-file editable corpus retains its 14 accepted / 21 rejected
split; with five additional supported inputs, each mode accepts 19 of 40. Seven
accepted outputs per mode match 1.3.1 by every DOCX part. All 35 Preserve layout
outputs match 1.3.1. Original PDF/DOCX files remain unchanged.

**Passed:** final local EXE/ZIP build and relocation with EN/RU widget checks, clean
preferences and no external Python on PATH. Frozen smoke verifies all four
synthetic blank-rule edges against PDF coordinates, including the year field.
**Passed:** hosted Windows tests `40291609662` and build/fresh-VM checks
`40291626110`, from `f6b94734d52d35a87d988aac62dd6abc0d2d9bc6`. The exact hosted
EXE/ZIP also pass local relocation. All 16 frozen modules equal tested source;
12 synthetic frozen DOCX outputs equal source by every part. All 190 tests pass
after integration into main. [1.3.2](https://github.com/DelureDev/pagethaw/releases/tag/v1.3.2)
is published; downloaded public EXE/ZIP/checksums equal the tested hosted bytes.
The verified EXE is in Downloads and the corrected three-page DOCX is in
`Downloads/PageThaw-output/test-1.3.2`. Existing user files were preserved.
The two reported field defects are resolved. Detailed release hashes and delivery
checks are in `.private/review-2026-10-26-minifleb6/release-verification.json`.

**Limits:** other corpus documents still have pre-existing paragraph/page-boundary
differences; this is not universal pixel identity. The missing-font form remains
blocked without substitution, as requested. Installed font alias behavior is
unchanged. Other Word versions and physical printing were not run. Private
evidence: `.private/review-2026-10-26-minifleb6/final-audit.json` and adjacent files.

Independent read-only code/natural-mode visual review requested routing_reviewer
gpt-6.1-sol/high, which was unavailable at capacity. The accepted fallback request
was gpt-6-sol/high; backend identity was not independently confirmed. The lead was
the sole writer. Review prompted stronger frozen field-edge coverage; no unresolved
conversion defect remains in the reviewed diff.

## 1.3.1 — editable footnotes and touching blank lines (published)

2026-10-23: [1.3.1](https://github.com/DelureDev/pagethaw/releases/tag/v1.3.1)
is published from `da2ef1666e361595ed96cb644d49a0bf5386a2c0` and integrated into main.
The owner requested fixes for the two six-file test failures below.
Native Word footnotes now retain uniquely matched raised reference marks and
ordinary editable note paragraphs. The following source-page boundary is retained.
An underscore-only blank may graze a horizontal form border by at most 1.5 pt;
real text, deeper intersections and side crossings remain rejected.

**Passed:** 175 tests; independent code review after fixing two recognition edge
cases; all 20 native Word comparison pages for five forms in both editable modes;
two actual Word edit/save/reopen pages; final DOCX parts equal reviewed artifacts.
The previously failing forms each remain two pages with the source content boundary.
All six PDF hashes are unchanged. The missing-font file remains blocked without
substitution, as explicitly requested by the owner.

**Passed:** prior editable corpus still accepts 14/rejects 21; 13 accepted outputs
are unchanged by every DOCX part in each mode, and the one intended footnote change
equals the freshly reviewed output. All 35 Preserve layout outputs equal published
1.3.0 parts. Local build and both relocated portable formats pass, including the
new native-note/border smoke fixture, clean preferences and no Python on PATH.

**Passed:** hosted Windows tests `39952221801`, build/fresh VM `39952223331`, exact
hosted EXE/ZIP relocation locally, all 16 frozen application modules equal tested
source, and 10 synthetic frozen outputs equal source by every DOCX part. A native
Word render confirms custom marker 7 and the following page in the frozen fixture.
All public EXE, ZIP and checksum bytes were downloaded again and equal the tested
hosted candidate. The verified EXE is in Downloads; five reviewed retained-line
DOCX files are in `Downloads/PageThaw-output/test-1.3.1`, with no reports alongside.
All 175 tests also passed after the local integration fast-forward.

The existing
stale-font-alias registry/GDI discrepancy is not changed by this release; correct-font
visual proof uses active faces whose outlines and metrics were read back from GDI.
No font installation, registry edits or guard bypass occurred. Pixel-identical layout,
other Word versions and printing remain unverified. Private evidence is in
`.private/form-boundary-footnotes/final-audit.json` and its neighboring folders.

Independent read-only review: `routing_reviewer`, requested Sol/high, accepted role
request; backend identity not independently confirmed. The lead owned all changes.
The two-defect mission is complete. Release evidence and exact hashes are in
`.private/form-boundary-footnotes/release-verification.json` and `docs/VERIFICATION.md`.
The unrelated installed-font identity issue and missing-font file remain separate
open items; do not describe this release as universal pixel-identical conversion.

## Six additional owner PDFs — test findings, 2026-10-23

Fresh testing of six private two-page forms is **not a full batch PASS**. Product
code and installed fonts/registry were not changed. Detailed file identities,
screenshots, proofs and hashes stay in `.private/user-six-2026-10-23/summary.json`.

**Failed:** the published 1.3.0 EXE accepts explicit mappings to stale registered
font aliases whose files still exist. Native Word substitutes a visibly different
font. Fresh GDI readback confirms those requested aliases resolve to another face;
the original regular/bold families are active. Registry presence alone does not
prove the selected face is usable. Existing original-family registry conflicts
were not bypassed in the released EXE and no fonts were installed or removed.

**Passed, diagnostic scope only:** live GDI CFF/OS2/hmtx/hhea/cmap tables equal the
supplied original fonts, and used PDF glyphs match. The unchanged converter API,
given those verified active faces, produces four documents in both editable modes.
All pass content checks and remain two pages without positioned text or fixed-height
rows. All 16 corrected-font Word pages were inspected. Three documents retain their
source content page boundaries and are usable with small field/label differences;
reviewed retained-line samples were copied to a new owner output subfolder containing
only DOCX files. This does not clear the EXE's font-selection failure.

**Failed:** the fourth document has an in-body footnote that interrupts a risk list;
the first continuation bullet moves from source page 2 to below the note on Word
page 1. A fifth form is rejected in both modes because an underscore-only line's
bounding box overlaps the outer form border (about 0.91 pt). This needs a geometric
rule treatment, not a broad relaxation for real text crossing borders.

**Blocked:** the sixth needs a missing font for five list dashes. The owner explicitly
declined substitution. The EXE correctly refuses conversion and creates no DOCX.
All six originals are hash-unchanged. Other Word versions/printing and a new build
were **not run**; this was a test request, not a new release.

Next: validate active font identity, handle coincident underscore rules, reconstruct
or safely reject footnotes, then repeat this corpus through a rebuilt EXE and affected
regression checks. Do not claim the full batch or released font selection passed.
Independent visual review used `routing_reviewer`, requested Sol/high; the native
role request was accepted, backend identity not independently confirmed. Reviewer
was read-only; the lead wrote private QA evidence and this handoff only.

## 1.3.0 shared editable fidelity — published and verified

2026-10-23: [PageThaw 1.3.0](https://github.com/DelureDev/pagethaw/releases/tag/v1.3.0)
is published from `6473e9ae6a9289dde451f4c639d31aeab3008777`. All public downloads
match the tested hosted bytes; the verified EXE is also in the owner's Downloads
folder. Implementation and release evidence are integrated into main. The release
pipeline is complete; universal pixel/page-boundary fidelity is not achieved.

The owner clarified that text must remain normal editable paragraphs and that
improvements must apply to the algorithm rather than one example. No document-name,
wording or Sirius-specific conditions were introduced. Source fonts/documents and
existing outputs remain private and untouched.

Implemented local paragraph-boundary/spacing inference, responsive dense leading,
bounded font-metric minimum spacing, right-hand-logo headers, trailing-blank-row
handling and optional retained PDF line breaks. Retained lines use ordinary
paragraphs with soft breaks and bounded character spacing; they do not create
text boxes or per-line frames. The option is off by default, remembered, translated
in EN/RU and exposed as `--keep-line-breaks` for editable CLI conversion.

**Passed:** 141 tests; source hashes preserved; 35 Preserve layout outputs match
the baseline by every uncompressed DOCX part. Editable corpus accepts 14 and
rejects the same 21 inputs. Default and retained-line results each total 21 native
Word pages. The main three-page sample matches all 80 measured paragraph wraps
and source-page assignments; final parts equal the reviewed attempt-7 parts.
Independent review found no clipping/lost visual content in all affected corpus,
main-sample and 17 edit-stress pages. Larger text and multiline fields survive
actual Word save/reopen. Native spacing probes include the metric boundary and
mixed-size transitions, with maximum measured advance error 0.10 pt.

**Failed — universal exact fidelity:** some form page boundaries and receipt/field
geometry still differ. Do not describe the main sample's paragraph checks as
100% pixel matching. A long date can expand a narrow cell across many pages;
content survives but that is not comfortable editing. Forced source page breaks
were rejected after adding pages to multiple forms.

**Passed:** native EN/RU source and exact release-EXE visual review; independent
release/code review; local build; both portable formats relocated with clean
preferences and no external Python on PATH; hosted tests `39940283776` and
build/fresh-VM `39940283779`. All 15 bundled application modules equal the tested
source after normalizing compile-time filenames. Both editable modes match source
conversion under the same registered aliases (14 files each), and 35 frozen layout
outputs match baseline. An exact-name Arial fixture verifies nonzero tracking,
retained breaks, expanding minimum spacing and all-part source/EXE equivalence.

**Not run:** exact original-Sirius-mapped frozen Word rendering because local
registry entries still include conflicting versions and a renamed original regular
face. Alias-based binary tests exercise the intended fallback, not original-font
visual identity. The original-font visual checks use the same independently
verified converter code. No font/registry changes or weakened CLI guards were used.
Physical printing and other Word versions remain untested. See the
[plan and remaining fidelity work](PAGE_FIDELITY_PLAN.md) and
[release evidence](VERIFICATION.md#130--shared-editable-fidelity).

Private evidence: `.private/editable/page-fidelity/attempt-final` (same parts as
reviewed `attempt-7`), `corpus-final/qa.json` (per-file final/reused render paths),
`natural-final`, `edit-stress-final`, `dense-edit-stress`,
`minimum-probe-edge-verified`, and `layout-regression-verification.json`.
Early probes with short singleton rows or a mismatched test-page width are not
the accepted metric-boundary evidence. Corpus export 2 initially returned no PDF;
its isolated retry succeeded and is the reviewed render.
The final corrected example was copied without replacement into the owner's
PageThaw-output folder. Its path/hash are in private `page-fidelity/delivery.json`;
it is a normal paragraph DOCX with retained soft line breaks. Release/binary/public
checks are recorded in `release-verification.json`, `release-artifact-verification.json`,
`artifact-tracking/verification.json` and `public-verification.json`. The release
EXE SHA256 is `7c07177f1cf6580fe7f734bd8e7d93f8f864e9fda1719d07a3774b2ec2cb0a67`.

Read-only routing used `routing_reviewer`, requested Sol/high, for independent
code and visual review, and `routing_scout`, requested Luna/high, for the bounded
option inventory. Native role requests were accepted; exact backend identity
was not independently confirmed. No subagent writes. Astra was unavailable on
this account and was not retried in this continuation. Lead remains sole writer.

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
