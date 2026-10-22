# Release verification

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
- Public source audit and hosted CI: recorded in the release/project state.

**Not run:** clean Windows VM, physical printing, LibreOffice, Word web/mobile.
Desktop Windows x64 is the supported build. Source tests use locally installed Arial,
including regular, bold and italic faces; no system font bytes are distributed.
