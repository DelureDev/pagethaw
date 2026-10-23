<div align="center">

# PageThaw

### PDF forms → editable Word documents

Choose normal editing or preserve the layout. Convert offline.

**English** · [Русский](README.ru.md)

**[Download for Windows](https://github.com/DelureDev/pagethaw/releases/latest)** · [Report a problem](https://github.com/DelureDev/pagethaw/issues)

Windows 10/11 x64 · Free & open source · English / Русский

</div>

---

## Start in 4 steps

1. **Download and open** `PageThaw-…-windows-x64.exe` from the latest release.
   One file. No installation or unpacking.
2. **Add your PDFs.** PageThaw checks the files and fonts automatically.
3. **Choose a font if asked.** Add your own `.ttf` / `.otf` or approve
   an installed replacement. Nothing is silently substituted.
4. **Choose a mode and output folder**, then click **Convert to Word**. Open the `.docx`
   files in desktop Word and review every page.

Your folder gets **only Word files**. Convert again to the same folder any time;
existing files stay untouched and new copies get names such as `form (2).docx`.
The **Fonts** section stays visible. A warning appears when a matching font is
missing or cannot be verified; use **Choose / install font…** to resolve it.
Extra settings are under **Options…**.

Your output folder and approved font choices are remembered and rechecked.
If a file fails, use **Details** for the full message, fix the problem, then
**Retry failed**. Successfully converted files are left alone.

**No account, Python installation or Word is needed to convert.** All processing
happens on your computer. Use the **Русский / English** button at the top right
to switch the interface; your choice is remembered.

## What you get

**Editable text** creates normal paragraphs and expanding table cells for blanks.
Type in a blank cell; longer entries move the following content down. This mode
supports single-column forms and simple tables with complete row/column borders.
Paragraph indents and alignment are reconstructed. Spacing and page counts can change.

For closer line wrapping, enable **Keep PDF line breaks in normal paragraphs**.
Text stays editable; those line breaks remain when you edit, so longer rewrites
may need some breaks removed. This option is off by default.

**Preserve layout** keeps the original placement with text boxes. Choose it when
appearance matters more than extensive editing. The app never silently switches modes.

| Feature | How it helps |
| :--- | :--- |
| Batch conversion | Convert several PDFs in one run; see their status in the app. |
| Two conversion modes | Flowing paragraphs for editing, or positioned text for layout. |
| Font choices | Match regular, bold and italic faces, or approve a substitute. |
| Optional font embedding | Include permitted TrueType fonts so recipients can edit without installing them. |
| Form blank lines | Optionally turn underscore blanks into continuous lines. |
| Page comparison | With desktop Word installed, generate original/export image pairs. |

<details>
<summary>Preview the Russian interface</summary>

![PageThaw — RU](docs/images/app-ru.png)

</details>

Prefer a folder-based app? The release also includes a ZIP. Extract the
whole folder and keep `_internal` beside its `PageThaw.exe`.

## Before you convert

> **Best for digital forms with selectable text.** Scans need OCR first.
> Conversion is not pixel-perfect: always check the result.

- Editable mode rejects ambiguous columns, complex grids and overlapping graphics.
  Clear bottom-of-page notes become editable Word footnotes; unclear references are
  rejected. Automatic numbered lists are not reconstructed.
- In Preserve layout mode, text boxes **do not reflow**. Long edits may need manual adjustment.
- Missing or different fonts can change spacing. Enable **Include fonts in Word files**
  for permitted static TrueType fonts. Restricted or unsupported fonts are skipped
  with a visible notice; recipients still need those installed. [Font details](docs/FONTS.md).
- Rotated text, mixed page sizes and interactive PDF fields are not supported yet.
- The portable app is unsigned. Follow your organization's software policy if
  Windows blocks it. Checksums are included in each release.

## More information

[Detailed guide & command line](docs/USAGE.md) · [Test coverage](docs/VERIFICATION.md) · [Contributing](CONTRIBUTING.md)

Licensed under [GNU AGPL v3.0](LICENSE). Built with [PyMuPDF and other open-source components](THIRD_PARTY.md).
No uploads, telemetry, private documents or user font files are included.
