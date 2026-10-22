# Project state

Public project: PageThaw (pagethaw), an offline Windows PDF-to-Word app.

Owner-approved defaults: preserve page layout with editable text boxes; ask before
substituting a missing font. Public repository and a portable Windows release are
authorized. Original PDFs, converted private documents, font files and machine
profiles must never be committed or included in release assets.

This first release targets selectable, horizontal text on consistent-sized pages.
Word desktop is the reference viewer. OCR, rotated text and interactive PDF forms
are outside the first release. Conversion itself does not require Word.

Status: v0.2.0 implementation and verification complete. The portable package
passed its relocation test and hosted Windows CI passed. The English/Russian switch retains
batch state and saves the preference locally. Both READMEs are shorter and linked;
technical documentation is in docs/USAGE.md. Local tests (39), native app language
switch/layout inspection and independent review passed. Converter/exporter code
is unchanged; no new Word rendering comparison was needed. Both published
READMEs were inspected in the browser. Release asset checksums are supplied with
the download; detailed local build and upload evidence stays in the private archive.

Repository: https://github.com/DelureDev/pagethaw
Release: https://github.com/DelureDev/pagethaw/releases/latest

Public deliverables: source, README, AGPL license, Windows checks workflow and
portable ZIP with executable, runtime, dependency licenses/source references and
checksum. The executable belongs in Releases rather than Git source history.

Private working material is archived locally and ignored by Git. The retained
private conversion skill's machine profile was updated to its archive paths.
The final private Word output folder is preserved in place while a document is
open in Word; it is excluded from source and release packaging.

See VERIFICATION.md for passed checks and explicit untested environments. A
content check does not establish visual fidelity; every real output needs review.

Independent review uses the native routing_reviewer role (configured
gpt-6.1-sol/high), selected for generic-conversion correctness and release review.
The lead is the only writer. No fallback model was used.

v0.2.0 reused that reviewer for state retention, font consent and packaging. Review
passed after the two findings were fixed and a stale-font-state regression was
also covered. The native app screenshot in docs/images/app-ru.jpg was captured
from the local v0.2.0 build with an empty file list; it contains no user documents.
