# Release verification

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
