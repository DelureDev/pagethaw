# Project state

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
