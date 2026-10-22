# PageThaw — PDF to Word

**An offline Windows app for turning PDF forms into editable Word documents while keeping their page layout.**

Select PDFs, check their fonts, and convert a batch to `.docx`. PageThaw keeps text
in positioned, editable boxes and retains graphics behind it. Nothing is uploaded.
No account, Python installation or Microsoft Word is needed to **convert**.

**[Download the portable Windows app →](https://github.com/DelureDev/pagethaw/releases/latest)**

Early release: best for digital forms with selectable, horizontal text. Conversion
is not pixel-perfect. Review each result before relying on it.

## Quick start

1. Open **Releases** and download `PageThaw-0.1.0-windows-x64.zip`.
2. Extract the **entire folder**. Open `PageThaw.exe` inside it; keep `_internal`
   alongside the executable. There is no installer and no administrator step.
3. Click **Add PDFs**, then **Scan files & fonts**.
4. Resolve each missing or ambiguous font. Choose an installed face, or **Add font
   file** to install your own static `.ttf` / `.otf` for your Windows account.
5. Choose a new output folder and click **Convert to Word**.
6. Open the results in **desktop Microsoft Word** and compare every page.

The release is unsigned. A managed Windows environment may block unsigned apps;
follow your organization's software policy, or build the reviewed source yourself.
SHA-256 checksums are attached to each release.

## What it preserves

- Text content, approximate positions, font sizes, selected font faces and styles.
- Separate regular, bold and italic face mappings; Unicode character checks.
- Page size and explicit page breaks.
- Logos, borders and graphics as a graphics-only background at selectable DPI.
- Literal underscores by default. An optional setting turns standalone runs of
  three or more underscores into continuous lines; identifiers such as `account_id`
  and `a___b` stay editable text.

The app checks the generated DOCX text before accepting it. Each batch includes
`pagethaw-report.json` with conversion outcomes and failures. A content check is
**not** a visual-quality guarantee.

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

If desktop Microsoft Word is installed, **Compare pages (Word)** exports the DOCX
through a separate Word instance and creates original/export page pairs under
`comparisons/`. Page counts are checked; you inspect the images yourself.

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
  must be converted to separate output folders.
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

## Build and test

```powershell
python -m pytest -q
python scripts/build_portable.py
```

The build creates a portable folder and ZIP under `dist/`, plus dependency notices
and source references. The executable bundles its Python runtime. Release binaries
are assets on GitHub Releases, not files in Git history. Only synthetic fixtures
are used in the public tests; Windows Arial is read from the test machine and is
never bundled.

See [verification notes](docs/VERIFICATION.md) and [contributing](CONTRIBUTING.md).

## License and privacy

PageThaw is licensed under **GNU AGPL v3.0**, using the AGPL edition of
[PyMuPDF/MuPDF](https://pymupdf.readthedocs.io/en/latest/about.html).
See [LICENSE](LICENSE) and [THIRD_PARTY.md](THIRD_PARTY.md).

No original documents, private conversion outputs or third-party font files are
distributed in this repository. The app has no telemetry or automatic network
requests. Reports and generated documents stay in the output folder you choose.

When reporting a bug, use a synthetic or redacted example. Do not upload private
documents or fonts you do not have permission to redistribute.
