# Project state

1.0 release preparation on `release/1.0.0`: owner authorized autonomous completion,
local corpus testing and one consolidated public release. Current checks: 79 tests
passed locally (78 in the previous hosted build); 68 distinct local documents exercised, 36 converted
into 49 pages. All 49 Word-export comparisons were visually reviewed. Fourteen
inputs need unavailable fonts; 18 are unsupported by preflight. A whitespace-only
font preflight defect was fixed. All original hashes are unchanged. Private evidence
is under `.private/v1.0.0`; no private material is included in Git or releases.

New preferences revalidate saved font-file hashes and source identity (or fresh
glyph proof). Fonts remain visible; output stays DOCX-only. Retry preserves
successful files. Independent review passed after fixing unused-font retry,
cancelled-rescan state and a test fixture's order dependency.

No usable local Sandbox/VM was found by the read-only audit. Fresh hosted Windows
VM testing passed for both portable formats: no Word/private fonts, clean settings,
external Python unavailable on PATH, bundled module locations verified. The hosted
image still has developer tools installed; no claim of uninstalling Python is made.
Real Windows locks and mixed failures, blocked folders and 50-item cancellation
also passed. Physical printing/alternate Word viewers remain outside release scope.

Delegation: native routing_scout roles requested gpt-6-luna/high for bounded PDF
and Windows-environment inventories; both completed without file mutations.
Native routing_reviewer requested gpt-6.1-sol/high for independent code and
separate corpus visual checks; both passed, lead is sole writer. Role selections
were accepted by the runtime; no fallback used. The final release build is pending
artifact download, local equivalence verification, publication and checksum readback.

Final artifact comparison caught optional PyMuPDF helper startup changing the
development environment's global text metrics. Source CLI/API agreed, but 14
portable outputs had sub-point vertical changes. An explicit core-metric setting
now removes this dependency on import side effects; an isolated-process regression
passes. The actual portable outputs are undergoing another Word visual review,
and a final build is required before publication. This is a bounded release fix.

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
