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
- [ ] Deliver one tested portable update after the remaining release gates.

Acceptance records content, font/size, line wrapping, page boundaries and geometric
differences separately. Do not describe approximate rendering as a 100% pixel
match. A matching page count alone is insufficient. Word rendering may round
coordinates differently; any unresolved difference remains explicit. Existing
editable-mode limitations and safe rejection rules must not be weakened.

Read-only routing_reviewer requested Sol/high for bounded spacing analysis and
independent review. Astra is unavailable on this account; no Astra request is
made in this continuation. Native role selection was accepted; actual backend
identity is not independently established. No subagent writes.

## Current result — 2026-10-23, not released

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

**Blocked — native UI visual check:** the desktop was in use; UI automation
stopped without taking focus. EN/RU state, persistence and mode tests passed.
**Not run:** candidate build, relocation, fresh-VM checks, publication, physical
printing and other Word versions for this branch. Published 1.2.1 is unchanged.

Next work: measure the first/last body baseline and expanding-cell geometry at
the remaining mismatched page boundaries, then change only rules supported by
multiple inputs. Preserve normal editing and the existing rejection boundary;
do not force a fit with smaller type, fixed rows or sample-specific offsets.
Complete the release process only after native EN/RU visual inspection and the
candidate gates. Private evidence: `.private/editable/page-fidelity`.
