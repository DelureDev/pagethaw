# Release process

Develop and verify a group of changes on a release branch. Do not publish a new
release for each small task.

1. Run `python -m pytest -q` on Windows and inspect the English/Russian app.
2. Build with `python scripts/build_portable.py`. The build audits both formats
   for unexpected documents, fonts and unused runtime payloads.
3. Run `scripts/verify_portable.ps1 -Release dist/VERSION -Results NEW_FOLDER`.
   It tests both formats outside the repository with external Python removed from
   PATH, verifies the bundled runtime, GUI, repeat conversion and DOCX-only output.
4. Run the **Portable release candidate** GitHub workflow. Its second job uses a
   fresh Windows VM, checks that Word/private fonts are absent, and repeats the
   binary-only tests without setting up Python. Hosted images may contain Python;
   this test makes it unavailable on PATH and verifies imports come from the EXE.
5. Locally compare supported real PDFs against desktop Word exports. Record the
   coverage and limitations. Keep all originals, fonts and comparisons private.
6. Complete independent review, update `VERIFICATION.md`, and confirm the tested
   source commit and asset hashes before publishing a tag/release. Download the
   uploaded assets and verify their checksums afterwards.

Publish the standalone EXE, optional folder ZIP and `SHA256SUMS.txt`. Include
known limitations in release notes. The workflow produces candidates; it does
not automatically publish them. Private documents or fonts must never be used
as hosted CI fixtures or included in source, screenshots or assets.
