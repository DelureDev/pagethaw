# Editable Word conversion

Owner requested implementation after feedback that positioned text boxes are
unsuitable for normal editing. Build a second conversion mode using flowing Word
paragraphs, runs and tables. Retain fixed-layout mode with an explicit trade-off.

Scope: selectable horizontal text, existing font-consent rules, local processing,
English/Russian UI, original files unchanged. No OCR or promise of pixel identity.
Private samples and fonts stay outside Git and release assets.

- [x] Evaluate a paragraph converter on three structurally different forms.
- [x] Preserve source content, emphasis, graphics and form fields in normal Word structures.
- [x] Verify content completeness, absence of text boxes and usable paragraph boundaries.
- [x] Render every sample page and test sentence insertion, deletion and field entry.
- [x] Integrate the mode in GUI/CLI with clear EN/RU descriptions and safe retry.
- [x] Run a wider supported corpus, regression tests and independent review.
- [ ] Build and verify portable artifacts, update documentation and deliver one update.

Acceptance: body text is in ordinary paragraphs, never line/word boxes; fields
remain usable; paragraphs and subsequent content reflow after edits; images are
embedded; source text/emphasis is preserved; no clipping or overlaps. Page breaks
may change as a consequence of actual editing. Fail explicitly on unsupported
structures rather than silently emitting a damaged document.

Lead is sole writer. Native routing_architect requested gpt-6-astra/low for bounded
read-only conversion architecture advice; role accepted by runtime. Exact backend
identity is not separately verified. No fallback requested.

The generic pdf2docx prototype joined some Cyrillic words, fused fields/captions,
and added page/column sections. An owned, bounded emitter was chosen after the
architect reviewed that evidence. No new runtime dependency was added.

Current checks: 97 tests passed after the final field-grouping repair.
Three private forms rendered in desktop Word with 2, 3 and 3 output pages (source:
2, 2 and 3). A wider 35-file corpus produced 14 content-verified conversions and
21 explicit unsupported-layout results. All 27 converted pages passed independent
visual review. All eight pages of the three proof documents and nine pages after
long-title, multiline-field, paragraph insertion/deletion edits passed lead review.
Narrow fields wrap long entries vertically; they do not widen automatically.
Final portable checks and release are still pending. These are current-run
results, not inferred from the historical 1.0 gate.

Native routing_reviewer requested gpt-6.1-sol/high for independent read-only
review. It found dropped vertical strokes, a two-column rejection bypass, a
caption-order issue and field groups split at page boundaries. All were repaired
with synthetic regression tests; code and visual rereviews passed. Role
accepted by runtime; exact backend identity not independently inspected.
