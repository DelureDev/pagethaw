# Project state

Public project: PageThaw (pagethaw), an offline Windows PDF-to-Word app.

Owner-approved defaults: preserve page layout with editable text boxes; ask before
substituting a missing font. Public repository and a portable Windows release are
authorized. Original PDFs, converted private documents, font files and machine
profiles must never be committed or included in release assets.

This first release targets selectable, horizontal text on consistent-sized pages.
Word desktop is the reference viewer. OCR, rotated text and interactive PDF forms
are outside the first release. Conversion itself does not require Word.

Status: v0.3.1 implementation and local verification complete. Owner approved a single EXE as the main
download with a lean ZIP alternative, removing unused AI layout/ONNX/NumPy payloads.
Latest clarification: selected output folder must contain only Word files, no
automatic reports or batch subfolders; repeat conversion should work with numbered
filenames that preserve existing files. Fonts must always be visible, with a warning
and explicit choice/install flow for missing or unverified matches. Only extra
options collapse; comparison remains explicit in a separate temporary folder.
Local tests pass (62). Justified word spacing is now preserved instead of being
mistaken for stretched letters. Used-glyph outlines/advances verify automatic
font matches; names alone do not. Windows family/style version conflicts require
resolution in both GUI and CLI. Private two-page Word export was visually checked.
Independent review passed after fixing the CLI conflict bypass. Final release
asset checks and hosted CI are recorded with the release.

Repository: https://github.com/DelureDev/pagethaw
Release: https://github.com/DelureDev/pagethaw/releases/latest

Public deliverables: source, README, AGPL license, Windows checks workflow and
single EXE plus optional portable ZIP, embedded dependency licenses/source references
and checksums. Binaries belong in Releases rather than Git source history.

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

v0.3.0 review used routing_reviewer (native role configured gpt-6.1-sol/high),
read-only; lead remained the only writer, with no fallback. The preview was replaced
with the empty compact v0.3.0 Russian interface. Original/private user documents,
fonts and open Word sessions were not changed. The single-file build embeds notices
accessible with --export-notices; both formats share the same dependency analysis.

v0.3.1 reused a native routing_reviewer role (configured gpt-6.1-sol/high) for
read-only spacing diagnosis and independent review. Lead remained the sole writer;
no fallback. Review passed after one finding was fixed and retested. The screenshot
is the empty v0.3.1 Russian interface, with fonts always visible. No user documents
or font binaries are included. Native warning was inspected; the user's subsequent
interaction with the test window was left undisturbed. Private evidence is retained
locally under .private/v0.3.1; final assets are built separately if that test EXE is open.
