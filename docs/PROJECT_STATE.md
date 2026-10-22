# Project state

Public project: PageThaw (pagethaw), an offline Windows PDF-to-Word app.

Owner-approved defaults: preserve page layout with editable text boxes; ask before
substituting a missing font. Public repository and a portable Windows release are
authorized. Original PDFs, converted private documents, font files and machine
profiles must never be committed or included in release assets.

This first release targets selectable, horizontal text on consistent-sized pages.
Word desktop is the reference viewer. OCR, rotated text and interactive PDF forms
are outside the first release. Conversion itself does not require Word.

Status: v0.1.0 implementation, local tests, portable relocation test and independent
review passed. Publishing and hosted CI verification are in progress.

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
