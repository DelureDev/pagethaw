# Release verification

## 1.2.1 — editable line spacing

Local checks on Windows, 2026-10-23:

- **Passed:** 126 tests, including responsive leading without changing type size,
  irregular/mixed-size/legacy-font fallbacks, local evidence isolation, growing
  fields and correctly formatted empty caption cells.
- **Passed:** all 35 Preserve layout outputs match the published baseline by every
  uncompressed DOCX part. Original PDF hashes remain unchanged.
- **Passed:** 14 editable corpus documents rendered to 22 Word pages; all reviewed
  independently against their 21 source pages. The same 21 complex inputs remain
  explicitly rejected. Reflow can change page counts.
- **Passed:** 8 representative pages, 9 long-edit pages and 9 enlarged-text pages
  reviewed independently. Tests include 15 pt body text, a 22 pt mixed run, accents,
  descenders and narrow 15/20 pt fields growing across pages. Actual Word save/reopen
  preserved all edited text without fixed row heights or positioned text boxes.
- **Passed:** independent code review. No dependencies or public/private font
  permissions changed; no private fonts or PDFs are bundled.
- **Passed:** [hosted Windows tests](https://github.com/DelureDev/pagethaw/actions/runs/39922446099)
  and [build/fresh Windows VM](https://github.com/DelureDev/pagethaw/actions/runs/39922445844)
  from `0059081eca5625ee78969e2abe97306045fe4f2b`. Both portable formats also
  passed local relocation into a Cyrillic path, clean preferences, Windows-only
  PATH, bundled runtime, repeat conversion and EN/RU widget checks.
- **Passed:** exact EXE output matches every source-converter DOCX part for all 14
  editable files and the baseline for all 35 layout files. Editable artifact tests
  use registered original-font aliases; normalizing just those family names gives
  equality to every part of the visually reviewed files. No system font changes
  were made for these tests.
- **Passed:** [published 1.2.1](https://github.com/DelureDev/pagethaw/releases/tag/v1.2.1)
  EXE, ZIP and checksums downloaded again and matched the tested hosted bytes.

Release SHA256:

- EXE (46,298,572 bytes): `9d06ceea7c27ab92534e4d93c7efe58712f6fa7806c51021e722f79c606a208d`
- ZIP (46,555,066 bytes): `5f6f6a13db7a80a31a7d0bbf5d8475d37500cbbf6c8018bf734c857c226cdb5f`

The reported form's section 4 now fits page 1 at the original font size. Two tail
lines from source page 2 still flow onto page 3. Older fonts without explicit
typographic metrics keep their prior minimum spacing. Pixel-identical pagination,
physical printing and other Word versions/viewers are not verified.

## 1.2 — reconstruction and font portability

Current local checks on Windows, 2026-10-22:

- **Passed:** 120 automated tests and synthetic application smoke, including
  complete ruled grids, cell order, expanding rows, unsupported path rejection,
  paragraph indents and permissions/OPC/hash checks for embedded fonts.
- **Passed:** all 35 Preserve layout documents match the published baseline by
  every uncompressed DOCX part when embedding is off; source hashes unchanged.
- **Passed:** independent review of 27 pages from 14 editable corpus documents,
  eight representative proof pages, nine edited pages and three table images.
  The same 21 complex corpus documents remain explicitly rejected. This release
  does not claim broader arbitrary-PDF success from synthetic table tests.
- **Passed:** an uninstalled synthetic font used by the actual converter rendered
  in desktop Word. A newly typed Cyrillic glyph used that same embedded face after
  save/reopen, verified by font identity and glyph metrics. Full outlines, glyph
  coverage, metrics and permissions survived; Word changed internal naming/checksum.
- **Passed:** independent code review after border width/schema fixes; final visual
  recheck after repairing a separator wrap. Russian native UI inspected and captured;
  EN/RU widget switching/persistence passed. Further native input stopped when user
  activity was detected.
- **Passed:** [hosted Windows tests](https://github.com/DelureDev/pagethaw/actions/runs/39827355699)
  and [build / fresh Windows VM](https://github.com/DelureDev/pagethaw/actions/runs/39827355708)
  from commit `0dcb8b52193902f4b70741c33f7d87e7b612619d`. Both formats passed on a
  separate runner without Word/private fonts or external Python on PATH. Bundled
  runtime imports were checked; developer tools remain installed on the hosted image.
- **Passed:** exact downloaded EXE/ZIP relocated locally with clean preferences,
  Windows-only PATH and a Cyrillic path. Both modes, repeated conversion, DOCX-only
  output, notices, EN/RU widgets, font embedding and ruled tables passed smoke checks.
- **Passed:** exact release EXE reproduces every uncompressed DOCX part of all 14
  reviewed editable documents and all 35 layout baseline documents. Source hashes
  stayed unchanged.

Release artifact SHA256:

- EXE: `6ad44c60bc477e8843626b39286cc38ee9bfef2767d1d4dccce94ec1b14a721c`
- ZIP: `578442fa63879d6a1fa1e1c6d2739cb301f3637f9c589fc7d788595df2269dc5`

**Passed:** [published v1.2.0](https://github.com/DelureDev/pagethaw/releases/tag/v1.2.0)
EXE, ZIP and checksums downloaded after publication and matched the tested hosted
artifacts. EXE: 46,288,554 bytes; ZIP: 46,541,393 bytes. No private fonts or PDFs
were committed or bundled.

Fonts are optional and only eligible static TrueType faces are embedded. The
private original Sirius faces are skipped because they allow preview/print only.
Other Word versions/viewers, physical printing and organization font policies
remain unverified. No dependencies were added.

## 1.1 — editable paragraphs

Current local checks on Windows, 2026-10-22:

- **Passed:** 97 automated tests, including no positioned text in editable mode,
  Cyrillic wrapping, inline emphasis, column/grid rejection, source reading order,
  field/caption grouping, cancellation, safe repeated output, mode persistence and
  extra-page comparisons without weakening layout-mode page-count checks.
- **Passed:** three representative forms exported in desktop Word, eight pages
  inspected. Long titles, two multiline fields, substantial paragraph insertion
  and paragraph deletion were applied and exported again: all nine edited pages
  inspected without clipping or overlap. Narrow cells wrap vertically rather than
  automatically widening. One source form grows from two to three pages.
- **Passed:** 35 previously convertible files exercised in editable mode. Fourteen
  produced 27 pages; an independent reviewer inspected all pages. Twenty-one
  complex layouts were explicitly rejected. Original input hashes stayed unchanged.
  Independent non-whitespace character, reading-order and face/emphasis checks
  run before accepting output; they are not a visual-quality guarantee.
- **Passed:** independent code and visual review after fixes for dropped vertical
  strokes, column detection, caption ordering and page breaks splitting fields.
- **Passed:** portable English/Russian interface visually inspected; the public
  screenshot contains an empty Russian interface with both conversion modes.
- **Passed:** [hosted Windows tests](https://github.com/DelureDev/pagethaw/actions/runs/39817967540)
  and [build / fresh Windows VM](https://github.com/DelureDev/pagethaw/actions/runs/39817967666)
  from source commit `a0220c5b2790721314c219d2a02416584e9124d0`. The fresh VM has no
  Word/private fonts and no external Python on PATH; bundled imports are verified.
- **Passed:** downloaded hosted EXE/ZIP relocated locally into a path with spaces
  and Cyrillic, clean preferences, Windows-only PATH, both conversion modes,
  repeated conversion, DOCX-only output, notices and EN/RU widget smoke.
- **Passed:** the exact hosted EXE reproduces every internal DOCX part of all 14
  independently reviewed editable documents. All 35 layout regression documents
  match the published 1.0 output. Private originals and fonts remain unchanged.

Release artifact SHA256:

- EXE: `41bd73b18d4e3474e69e91f9f165aabc132bb4de090216e75d0e9ef95fa2033e`
- ZIP: `a5297a4be19a8f6e450534084d6998a9cf3fc1da98e158ee47a2a32f546ac707`

**Passed:** [published v1.1.0](https://github.com/DelureDev/pagethaw/releases/tag/v1.1.0)
EXE, ZIP and checksum file downloaded again after publication. All bytes match the
tested hosted artifacts. The EXE is 46,223,459 bytes; the ZIP is 46,461,669 bytes.

**Not run:** physical printing, Word web/mobile, LibreOffice or Windows Sandbox.
Editable mode does not reconstruct native footnotes, automatic lists or complex
grids. It allows reflow and changed page counts. Private fonts are never embedded
or published. Preserve layout remains available; no new dependencies were added.

## 1.0 — consolidated reliability checks

Current local checks on Windows, 2026-10-22:

- **Passed:** 79 automated tests, including saved-font invalidation, language and
  output preferences, subset retry, cancelled rescans, changed font bytes,
  readable missing/damaged-file errors and whitespace-only PDF font runs.
- **Passed:** source/portable geometry diagnosis. Optional PyMuPDF helper imports
  changed a global metric setting in the development environment. The converter
  now explicitly uses core metric corrections; a fresh-process regression covers
  both prior settings. The unused helper is excluded from portable packages.
- **Passed:** 68 SHA256-distinct local PDFs exercised. 50 passed preflight;
  36 converted into 49 pages. Fourteen needed unavailable font faces and were
  not silently substituted; 18 had unsupported scans/OCR layers, rotation,
  interactive fields or unmapped characters. This is a mixed-corpus workflow
  test, not a 100% conversion-success claim.
- **Passed:** all 49 converted pages exported through isolated desktop Word
  instances and inspected against the original at the same scale. Page counts,
  wrapping, form blanks, bold, tables/borders and graphics stayed consistent.
  Small baseline/glyph-rendering differences remain. After the metric-setting
  fix, 14 affected portable outputs were re-exported and independently reviewed.
  Every uncompressed DOCX part from the final release EXE matches the reviewed
  outputs for all 36 documents (49 pages).
- **Passed:** source hashes unchanged for all 68 inputs. The final output folder
  contains only 36 DOCX files. No private sources, fonts or comparisons are public.
- **Passed:** real Windows input-file lock, damaged/missing input, blocked output
  path, continuing after per-file failures, and cancellation of a 50-item batch
  with 49 items correctly cancelled and no partial documents left behind.
- **Passed:** independent code review after retry/cancel fixes and standalone
  regression-fixture correction. Independent visual review covered 47 pages;
  the lead reviewed the other two, plus representative spot checks. The final
  14-page portable comparison also passed independent visual review.
- **Passed:** local single EXE and folder ZIP outside the source tree, Windows-only
  PATH, no Python environment variables, repeat conversion and preservation of
  existing files, DOCX-only output, notices export, bundled-runtime import paths,
  and packaged EN/RU widget smoke. The native app was also visually checked in
  both languages; the public screenshot is the empty 1.0 Russian interface.
- **Passed:** [final build and fresh-VM binary jobs](https://github.com/DelureDev/pagethaw/actions/runs/39796148192)
  and [79 hosted Windows tests](https://github.com/DelureDev/pagethaw/actions/runs/39796147864).
  A separate Windows Server 2025 VM tested both artifacts without Word or private
  fonts, using a clean preference directory, external Python unavailable on PATH,
  and imports verified inside the frozen runtime. The hosted image still contains
  developer tools; this is not a claim that Python was uninstalled from the VM.
- **Passed:** [published v1.0.0](https://github.com/DelureDev/pagethaw/releases/tag/v1.0.0)
  EXE, ZIP and checksum file downloaded again after publication; all bytes match
  the tested artifacts from source commit `bcea798`. Checksums are in the release.

**Not run:** physical printing, Windows Sandbox, Word web/mobile or LibreOffice.
The app remains unsigned. Review your real output; passing this corpus does not
guarantee every PDF or pixel-identical rendering.

## v0.3.1 — justified spacing and visible font choices

Checks performed on Windows on 2026-10-22:

- **Passed:** 62 tests, including justified spaces/NBSP/repeated spaces, exact
  source text and word origins, optional form lines, and rejection of genuinely
  stretched text even when it consists of short words.
- **Passed:** embedded subset/full-font glyph verification, rejection of same-name
  modified metrics, unverified font warnings and explicit replacement consent in
  English/Russian. Conflicting Windows family/style versions are rejected by both
  automatic and explicit CLI mapping; nonconflicting replacements still work.
- **Passed:** reported two-page form converted and exported through a separate
  desktop Word instance. Both original/export pairs were inspected: justification,
  form blanks, borders and bold text were preserved, with small rendering/baseline
  differences. The private source and font files are not distributed.
- **Passed:** native Russian app shows the font section and missing/unverified
  warning without opening a panel. English/Russian widget state and consent flows
  are covered by tests. The public preview contains no selected documents.
- **Passed:** independent read-only review after fixing the explicit CLI mapping
  conflict bypass. Final portable checks and hosted CI accompany the release.

**Not run:** clean Windows VM, physical printing, Word web/mobile or LibreOffice.
Glyph matching is conservative: unsupported/absent embedded data or ambiguous
identities require manual choice. It does not prove every typography feature or
the appearance of future edits. Final EXE/ZIP relocation and checksum evidence is
retained with the release; conversion output remains DOCX-only by default.

## v0.3.0 — single executable and simpler conversion

Checks performed on Windows on 2026-10-22:

- **Passed:** 46 tests, including repeat conversions into the same folder,
  preservation of existing documents and legacy reports, numbered duplicate
  filenames, no report files by default, and comparison of every duplicate output.
- **Passed:** actual Tk app workflow adds a synthetic PDF, scans fonts, converts
  twice and leaves only two DOCX files in the chosen folder. Language switching
  retains panel state, selections, options and conversion records.
- **Passed:** standalone EXE and extracted ZIP copied outside the repository to
  a path with spaces and Cyrillic. Each completed a two-page conversion and a
  repeated conversion with developer Python variables removed and PATH restricted
  to Windows directories. Existing outputs remained unchanged; no report files
  were created in the conversion folder.
- **Passed:** single-EXE Word comparison using the absolute Windows PowerShell
  path. Both original/export image pairs were visually inspected; page counts,
  text, rules and borders were preserved, with minor baseline differences.
- **Passed:** compact native app displayed in English and Russian. Missing fonts
  remain an explicit user decision; optional panels retain the same controls.
- **Passed:** embedded notices extracted from the single EXE. Both payloads were
  audited for private documents/fonts and excluded AI modules/models. No NumPy,
  ONNX Runtime or PyMuPDF layout-model payload is bundled.
- **Passed:** independent read-only review after fixing duplicate-source comparison
  selection. Full build and upload evidence is retained with the release process.

**Not run:** clean Windows VM, physical printing, Word web/mobile or LibreOffice.
The app remains unsigned. Restricted-PATH relocation is not a clean-machine test.

The GUI writes only DOCX files to the selected output folder. Optional comparison
creates diagnostics in a separate temporary folder. CLI `--report` remains an
explicit opt-in for automation; it is not enabled by the GUI.

## v0.2.0 — English / Russian interface

Checks performed on Windows on 2026-10-22:

- **Passed:** 39 tests, including all conversion regressions, EN/RU consent
  prompts, translated diagnostics, language preference persistence and fallback.
- **Passed:** actual Tk widget tests preserve selected files, font mappings,
  settings, output folder, selections and results across language changes. The
  switch is disabled during a job and stale fonts are cleared after file changes.
- **Passed:** native portable app opened in Russian; its top-right switch changed
  the interface to English. Both layouts were visually inspected, with no clipped
  main controls at the default window size.
- **Passed:** independent read-only review after fixing a page-count translation
  collision and a missing portable documentation link target.
- **Not rerun:** Word rendering comparison; the conversion engine and Word
  exporter are unchanged. The v0.1.0 evidence below remains historical evidence.
- **Passed:** portable ZIP extracted outside the project and its two-page
  synthetic conversion completed with developer Python variables removed and
  PATH limited to Windows directories. This is not a clean-machine test.
- **Passed:** portable documentation links and archive privacy audit; both
  READMEs, the app preview and detailed guides are included. No private documents
  or user font files are bundled.
- **Passed:** both READMEs rendered on GitHub; language navigation, headings,
  quick-start lists and feature tables were inspected in the browser.
- **Passed:** GitHub Windows runner tests and synthetic conversion.
  [Implementation CI run](https://github.com/DelureDev/pagethaw/actions/runs/39776189166).

The UI translates application messages and known converter errors. Windows dialogs
follow Windows' language; unknown OS/library diagnostics and JSON report keys
remain in their original language. The CLI remains English.

## v0.1.0 — initial converter

Verification for v0.1.0, performed on Windows on 2026-10-22:

- **Passed:** 27 tests covering content, literal underscores, optional form lines,
  regular/bold/italic faces, Cyrillic, rejection of unsupported inputs, changed
  inputs, cancellation, output preservation and write-failure cleanup.
- **Passed:** GUI decision-handler tests require positive consent for replacement
  fonts and prevent installation when consent is declined.
- **Passed:** final portable ZIP extracted outside the repository and its two-page
  synthetic conversion executed with developer Python environment variables
  removed and PATH limited to Windows directories. Exit code 0; content checks
  passed. This is a relocation test, not a clean-machine test.
- **Passed:** native executable launch and visual layout inspection; the PDF picker
  opened and closed. **Not run:** complete automated mouse-driven GUI journey;
  the available UI automation could not reliably focus the native file dialog.
- **Passed:** current converter's two-page synthetic document exported through
  desktop Word. Both original/export pairs were inspected. Regular, bold, italic,
  Cyrillic, accented Latin, underscores and graphic borders remained visible;
  minor baseline/spacing differences remain. Page counts matched.
- **Passed:** independent read-only review after fixes for hidden-text handling,
  underscore preservation, unusual spacing, output cleanup and comparison cancel.
- **Passed:** portable archive audit excludes private PDFs, outputs and font files.
  The sole bundled DOCX is python-docx's upstream blank template, verified by hash.
- **Passed:** public Git source audit (24 text/source files; no private inputs,
  documents, machine paths, credentials or font binaries).
- **Passed:** GitHub Windows runner installed the public source, ran all 27 tests
  without skips and completed the two-page synthetic conversion.
  [Implementation CI run](https://github.com/DelureDev/pagethaw/actions/runs/39772534789).
- **Passed:** uploaded ZIP downloaded back from GitHub and its SHA-256 matched
  the locally tested artifact and attached checksum file.

**Not run:** clean Windows VM, physical printing, LibreOffice, Word web/mobile.
Desktop Windows x64 is the supported build. Source tests use locally installed Arial,
including regular, bold and italic faces; no system font bytes are distributed.
