# Editable page fidelity

The owner requested analysis, a plan and implementation toward a complete match
with the reported three-page PDF. Preserve ordinary editable paragraphs, growing
form cells, source wording/emphasis and original type sizes. Keep private samples
and fonts out of Git. The lead is the sole writer.

- [x] Reproduce remaining overflow and locate merged paragraphs and fallback leading.
- [x] Measure source and desktop Word line/page positions, wrapping and form geometry.
- [x] Correct paragraph boundaries and local spacing using general source evidence.
- [ ] Resolve remaining page/field placement differences without shrinking text or flattening it.
- [x] Compare every affected page and exercise longer edits, larger text and save/reopen.
- [x] Run focused regressions, the supported corpus and Preserve layout equivalence.
- [x] Independently review the current algorithm changes, fix findings and verify again.
- [x] Deliver a separately named corrected example with the measured limits.
- [x] Deliver one tested portable update after the release gates.

Acceptance records content, font/size, line wrapping, page boundaries and geometric
differences separately. Do not describe approximate rendering as a 100% pixel
match. A matching page count alone is insufficient. Word rendering may round
coordinates differently; any unresolved difference remains explicit. Existing
editable-mode limitations and safe rejection rules must not be weakened.

Read-only routing_reviewer requested Sol/high for bounded spacing analysis and
independent review. Astra is unavailable on this account; no Astra request is
made in this continuation. Native role selection was accepted; actual backend
identity is not independently established. No subagent writes.

## 1.3.0 result — 2026-10-23, published with fidelity limits

The shared algorithm has no sample-name, wording or Sirius-specific conditions.
It uses measured baselines, local paragraph cues and the selected font's metrics.
An optional setting retains PDF soft line breaks inside ordinary paragraphs;
it is off by default. Both modes of editable text retain growing form cells.
No text boxes, per-line frames, glyph scaling or fixed text heights were added.

**Passed:** 141 tests; all 80 measured narrative paragraphs in the reported
three-page form have the source wrapping and page assignment in desktop Word.
The final DOCX has identical uncompressed parts to that reviewed result.
The 35-PDF corpus still accepts 14 editable inputs and rejects the same 21 complex
inputs. Both default and retained-line outputs total 21 Word pages, matching
source page counts, but not all page boundaries. All affected pages were reviewed.
Large-text and long-field edits survived native Word save/reopen with all text;
very long text in a narrow date cell remains awkward to edit.

**Failed — complete fidelity:** some forms move source-page-1 tail text to page 2;
one form moves a source-page-2 bullet after the preceding page's footnote.
Some receipt/form geometry differs. Matching page totals and the main sample's
80 paragraph checks do not establish a universal or pixel-identical match.
Forcing every source page break was tested and rejected because it added pages.

**Passed — release gates:** source and hosted EXE EN/RU visual checks; local
build/relocation; hosted tests and fresh-VM portable tests; source/EXE corpus
part comparisons under identical registered aliases; a nonzero exact-name Arial
tracking fixture; independent review; public-download checksums. Release 1.3.0 is
published from `6473e9ae6a9289dde451f4c639d31aeab3008777`.
**Not run:** original-Sirius-mapped frozen Word rendering due to the local font
inventory conflict, physical printing and other Word versions. See verification
for the distinction between original-font visual proof and alias-based binary QA.

Next work: measure the first/last body baseline and expanding-cell geometry at
the remaining mismatched page boundaries, then change only rules supported by
multiple inputs. Preserve normal editing and the existing rejection boundary;
do not force a fit with smaller type, fixed rows or sample-specific offsets.
The 1.3.0 release process is complete; remaining fidelity work is not a claim
of a complete match. Private evidence: `.private/editable/page-fidelity`.
