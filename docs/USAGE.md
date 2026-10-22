# Detailed guide

[← Quick start](../README.md) · [Русский](../README.ru.md)

## Choose a conversion mode

**Editable text** (the initial GUI choice) builds ordinary flowing paragraphs and
expanding table cells for standalone underscore blanks. Click in a blank cell to
type. Body edits, long titles and multiline entries move following content instead
of overflowing a text box. Font choices and emphasis remain explicit. Logos are
embedded inline images. Pagination and spacing can differ from the PDF.

This is a conservative reconstruction for single-column forms, with an optional
logo/title header, simple outer form borders and complete ruled tables. Table cells
grow with editing; merged cells, partial grids and graphics inside tables remain
unsupported. Paragraph indents, hanging indents, alignment and leading are inferred
from source geometry. Ambiguous columns, complex grids,
overlapping graphics and unsupported drawing paths fail with a reason. There is
no automatic fallback to the other mode. Footnotes and list numbers remain ordinary
text, not native Word footnote/list fields. Source page boundaries may be removed
when body text continues; new title/graphic headers retain a page boundary.

**Preserve layout** retains the existing positioned-text converter. It preserves:

- Text content, approximate positions, font sizes, selected font faces and styles.
- Separate regular, bold and italic face mappings; Unicode character checks.
- Page size and explicit page breaks.
- Logos, borders and graphics as a graphics-only background at selectable DPI.
- Literal underscores by default. An optional setting turns standalone runs of
  three or more underscores into continuous lines; identifiers such as `account_id`
  and `a___b` stay editable text.

The app checks the generated DOCX text before accepting it. The selected output
folder receives only Word files; progress and failures appear in the app. Reusing
a folder is supported: existing files stay untouched and additional copies get
numbered names such as `form (2).docx`. A content check is **not** a visual-quality
guarantee.

## Download and run

Open the single `PageThaw-…-windows-x64.exe` from the latest release. It includes
its runtime and needs no installer or adjacent support folder. Startup extracts
runtime files to Windows' temporary directory and can take a few seconds. Language
and output-folder preferences are stored separately in your Windows account,
not beside the EXE, in `%LOCALAPPDATA%/PageThaw/settings.json`.

The optional ZIP contains a folder edition with the same features. Extract it
fully and keep `_internal` beside `PageThaw.exe`. Both builds omit optional AI
layout models, ONNX Runtime and NumPy; the converter uses PDF text coordinates.
This packaging does not add OCR or AI-based table reconstruction.

Add PDFs to scan automatically. The **Fonts** section always shows the mappings,
warnings and rescan button. **Choose / install font…** opens the font picker. **Options…**
contains the form-line option, graphics resolution and optional Word comparison.

Select a file and use **Details** (or double-click it) to read its full status.
After resolving a temporary file-access problem, **Retry failed** converts only
failed or cancelled items. Earlier successes remain untouched. If an input PDF
changed, scan again first. Cancelling a scan requires a completed rescan.

## Font handling

PageThaw reads the font names used in the PDF and compares them with locally
registered individual font faces. Automatic selection requires an unambiguous name
match and matching outlines/advance widths for the glyphs used in the PDF. These
are checked against embedded font data in memory; no font file is saved or installed
from the PDF. Unsupported or absent embedded data requires your explicit choice.
This checks used glyphs, not every aspect of typography or future edits.

If a font is missing, the app stops for your choice. It does **not** silently
replace it, install embedded PDF fonts, download fonts, or upload your documents.
You can select an installed substitute and explicitly approve the changed mapping.
The app checks that the chosen face contains the required characters. Substitutes
can still change line lengths, positioning or appearance.

The picker shows font versions. Different files registered under the same Windows
family/style can make Word choose the wrong version, so remove conflicting versions
in Windows Fonts and rescan, or choose a different family. PageThaw does not remove
or rename your fonts. Name matches with unverified/different glyphs still require
replacement approval.

Approved choices are remembered locally. A saved choice is reused only while its
font file is still installed, unchanged, conflict-free and covers the characters.
Substitutes are limited to the same PDF contents you approved; other documents
need a new choice unless their glyphs can be verified against the saved font.
Deleting `settings.json` resets these preferences; it does not delete documents
or uninstall fonts.

Adding a font asks before installing an unchanged copy for the current Windows
account. Fonts are never included with the app. **Include fonts in Word files when
editing is permitted** optionally embeds the full used static TrueType faces in
each DOCX. A visible notice and file **Details** identify skipped faces; recipients
still need those installed. This option is off initially and remembered. It never
changes your font choices or licensing flags. [Permissions and compatibility](FONTS.md).
Variable fonts and `.ttc` collections are not supported; use individual static faces.

## Comparing with the PDF

If desktop Microsoft Word is installed, **Options… → Compare pages (Word)**
exports the latest completed conversion through a separate Word instance and
opens original/export page pairs in a separate temporary folder. This explicit
diagnostic action does not add images, PDFs or reports to your Word output folder.
Page counts must match in Preserve layout mode. Editable mode renders every page,
including additional pages, and labels the Word side as reflowed. Matching page
numbers do not imply matching content positions. You inspect the images yourself. Conversion records are
kept for the current app session; convert again after restarting to compare.

The exporter has a 60-second deadline per document and only cleans up a process
whose identity it recorded. It does not attach to your existing Word session.
An export failure stops that comparison run and leaves a report. Conversion still
works without Word; the comparison button needs Word.

Word's screen text can look heavier than its PDF export. Compare both PDFs at the
same scale before changing fonts merely to compensate for screen rendering.

## Limits to know before converting

- In Preserve layout mode, text boxes do **not** reflow like normal paragraphs. Longer
  edits may need manual resizing/repositioning. Tables are not reconstructed as
  native Word tables; graphic backgrounds are not individually editable.
- Scans, hidden OCR layers, transparent/outlined text, right-to-left text, rotated
  text/pages, mixed page sizes and interactive PDF form fields are rejected.
- In Preserve layout mode, justified word spacing uses additional positioned text boxes.
  Unusual letter stretch/spacing is rejected. Font
  substitutions and complex PDF drawing/clipping can still need manual repair.
- Desktop Word is the reference viewer. Word for the web, mobile apps and
  LibreOffice have not been verified for this positioned layout.
- A failed file is reported separately; other supported files can still convert.
  Existing output files are never intentionally overwritten. Duplicate filenames
  receive numbered suffixes automatically.
- Cancel is cooperative between pages/files. Word comparison may take up to its
  timeout to finish the current export.

## Run from source / command line

Windows 10/11 x64 and Python 3.11+ (the release is built with Python 3.12):

```powershell
git clone https://github.com/DelureDev/pagethaw.git
cd pagethaw
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pagethaw
```

Inspect fonts and unsupported features:

```powershell
python -m pagethaw --inspect "C:\Documents\form.pdf"
```

Convert with installed identity matches, or supply an explicit font mapping:

```powershell
python -m pagethaw --convert "C:\Documents\form.pdf" --mode editable --output "C:\Documents\converted" --font-map "font-map.json"
```

Add `--embed-fonts` to include permitted full TrueType faces. CLI results list
`embedded_fonts` and `font_embedding_skipped`; a skipped font does not fail an
otherwise valid conversion. No extra report files are created unless requested.

Example `font-map.json` (use the **actual font names reported by --inspect**):

```json
{
  "Helvetica": "C:/Windows/Fonts/arial.ttf",
  "Helvetica-Bold": "C:/Windows/Fonts/arialbd.ttf"
}
```

The CLI defaults to `--mode layout` for compatibility with existing scripts.
Use `--mode editable` for normal paragraphs. The `--rules` option applies only to
layout mode; editable mode always reconstructs standalone blanks as expanding cells.

Providing this map explicitly approves those substitutions. Mapped font files
must already be registered with Windows. Add `--rules` for form blank lines or
`--dpi 192` for higher-resolution backgrounds. The GUI is the easiest path for
adding fonts and creating Word comparison images.

The command line also produces only DOCX files by default. Add `--report` only if
you want `pagethaw-report.json` for automation; this optional mode requires a folder
without an existing report. The GUI never enables report files.

## Build and test

For candidate builds and release gates, see [Release process](RELEASING.md).

```powershell
python -m pytest -q
python scripts/build_portable.py
```

The build creates a single EXE and a folder ZIP under `dist/<version>/`, plus
checksums. Both formats share one PyInstaller dependency analysis. Dependency
notices and source references are embedded in both, and exposed beside the
launcher in the ZIP. To extract them from the single EXE:

```powershell
.\PageThaw-0.3.1-windows-x64.exe --export-notices ".\PageThaw-notices"
```

Choose a new destination; existing files are never replaced. The build audits
both payloads for private fonts/documents and excluded AI dependencies.
Release binaries
are assets on GitHub Releases, not files in Git history. Only synthetic fixtures
are used in the public tests; Windows Arial is read from the test machine and is
never bundled.

See [verification notes](VERIFICATION.md) and [contributing](../CONTRIBUTING.md).

## License and privacy

PageThaw is licensed under **GNU AGPL v3.0**, using the AGPL edition of
[PyMuPDF/MuPDF](https://pymupdf.readthedocs.io/en/latest/about.html).
See [LICENSE](../LICENSE) and [THIRD_PARTY.md](../THIRD_PARTY.md).

No original documents, private conversion outputs or third-party font files are
distributed in this repository. The app has no telemetry or automatic network
requests. Generated Word documents stay in the output folder you choose.

When reporting a bug, use a synthetic or redacted example. Do not upload private
documents or fonts you do not have permission to redistribute.

## Interface language

Use the **Русский / English** button at the top right. Switching preserves your selected files, font mappings, output folder, options and results. It is disabled while a job runs. On first launch, PageThaw uses Russian for a Russian system locale, otherwise English. The choice is remembered in `%LOCALAPPDATA%/PageThaw/settings.json`.

Application prompts, progress and known conversion errors are translated. Windows file dialogs follow the Windows display language. Font names, document text, JSON report keys and unknown OS/library diagnostics keep their original spelling. The command-line interface remains English.
