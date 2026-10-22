# Detailed guide

[← Quick start](../README.md) · [Русский](../README.ru.md)

## What it preserves

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
preferences are stored separately in your Windows account, not beside the EXE.

The optional ZIP contains a folder edition with the same features. Extract it
fully and keep `_internal` beside `PageThaw.exe`. Both builds omit optional AI
layout models, ONNX Runtime and NumPy; the converter uses PDF text coordinates.
This packaging does not add OCR or AI-based table reconstruction.

Add PDFs to scan automatically. **Fonts…** shows the mappings and rescan button;
the font panel opens automatically when a font needs your choice. **Options…**
contains the form-line option, graphics resolution and optional Word comparison.

## Font handling

PageThaw reads the font names used in the PDF and compares them with locally
registered individual font faces. An unambiguous full-face identity can be matched
automatically; a name match does not prove that two versions have identical metrics.
Family names alone are not enough to select a weight.

If a font is missing, the app stops for your choice. It does **not** silently
replace it, extract embedded PDF fonts, download fonts, or upload your documents.
You can select an installed substitute and explicitly approve the changed mapping.
The app checks that the chosen face contains the required characters. Substitutes
can still change line lengths, positioning or appearance.

Adding a font asks before installing an unchanged copy for the current Windows
account. Fonts are never embedded in the DOCX or included with the app. Recipients
need the same font faces installed. Variable fonts and `.ttc` collections are not
supported in this release; use individual static faces.

## Comparing with the PDF

If desktop Microsoft Word is installed, **Options… → Compare pages (Word)**
exports the latest completed conversion through a separate Word instance and
opens original/export page pairs in a separate temporary folder. This explicit
diagnostic action does not add images, PDFs or reports to your Word output folder.
Page counts are checked; you inspect the images yourself. Conversion records are
kept for the current app session; convert again after restarting to compare.

The exporter has a 60-second deadline per document and only cleans up a process
whose identity it recorded. It does not attach to your existing Word session.
An export failure stops that comparison run and leaves a report. Conversion still
works without Word; the comparison button needs Word.

Word's screen text can look heavier than its PDF export. Compare both PDFs at the
same scale before changing fonts merely to compensate for screen rendering.

## Limits to know before converting

- Text boxes preserve layout but do **not** reflow like normal paragraphs. Longer
  edits may need manual resizing/repositioning. Tables are not reconstructed as
  native Word tables; graphic backgrounds are not individually editable.
- Scans, hidden OCR layers, transparent/outlined text, right-to-left text, rotated
  text/pages, mixed page sizes and interactive PDF form fields are rejected.
- Unusual stretch/spacing detected with matching fonts is rejected. Font
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
python -m pagethaw --convert "C:\Documents\form.pdf" --output "C:\Documents\converted" --font-map "font-map.json"
```

Example `font-map.json` (use the **actual font names reported by --inspect**):

```json
{
  "Helvetica": "C:/Windows/Fonts/arial.ttf",
  "Helvetica-Bold": "C:/Windows/Fonts/arialbd.ttf"
}
```

Providing this map explicitly approves those substitutions. Mapped font files
must already be registered with Windows. Add `--rules` for form blank lines or
`--dpi 192` for higher-resolution backgrounds. The GUI is the easiest path for
adding fonts and creating Word comparison images.

The command line also produces only DOCX files by default. Add `--report` only if
you want `pagethaw-report.json` for automation; this optional mode requires a folder
without an existing report. The GUI never enables report files.

## Build and test

```powershell
python -m pytest -q
python scripts/build_portable.py
```

The build creates a single EXE and a folder ZIP under `dist/<version>/`, plus
checksums. Both formats share one PyInstaller dependency analysis. Dependency
notices and source references are embedded in both, and exposed beside the
launcher in the ZIP. To extract them from the single EXE:

```powershell
.\PageThaw-0.3.0-windows-x64.exe --export-notices ".\PageThaw-notices"
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
