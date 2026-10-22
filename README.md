<div align="center">

# PageThaw

### PDF forms → editable Word documents

Keep the page layout. Choose your fonts. Convert offline.

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
4. **Choose an output folder** and click **Convert to Word**. Open the `.docx`
   files in desktop Word and review every page.

Your folder gets **only Word files**. Convert again to the same folder any time;
existing files stay untouched and new copies get names such as `form (2).docx`.
The **Fonts** section stays visible. A warning appears when a matching font is
missing or cannot be verified; use **Choose / install font…** to resolve it.
Extra settings are under **Options…**.

**No account, Python installation or Word is needed to convert.** All processing
happens on your computer. Use the **Русский / English** button at the top right
to switch the interface; your choice is remembered.

## What you get

| Feature | How it helps |
| :--- | :--- |
| Batch conversion | Convert several PDFs in one run; see their status in the app. |
| Editable page layout | Text stays in positioned boxes; logos and borders stay in place. |
| Font choices | Match regular, bold and italic faces, or approve a substitute. |
| Form blank lines | Optionally turn underscore blanks into continuous lines. |
| Page comparison | With desktop Word installed, generate original/export image pairs. |

<details>
<summary>Preview the Russian interface</summary>

![PageThaw — RU](docs/images/app-ru.jpg)

</details>

Prefer a folder-based app? The release also includes a ZIP. Extract the
whole folder and keep `_internal` beside its `PageThaw.exe`.

## Before you convert

> **Best for digital forms with selectable text.** Scans need OCR first.
> Conversion is not pixel-perfect: always check the result.

- Text boxes preserve placement but **do not reflow** like normal paragraphs.
  Long edits may need manual adjustment.
- Missing or different fonts can change spacing. Fonts are not bundled or embedded;
  someone opening your DOCX needs the same fonts installed.
- Rotated text, mixed page sizes and interactive PDF fields are not supported yet.
- The portable app is unsigned. Follow your organization's software policy if
  Windows blocks it. Checksums are included in each release.

## More information

[Detailed guide & command line](docs/USAGE.md) · [Test coverage](docs/VERIFICATION.md) · [Contributing](CONTRIBUTING.md)

Licensed under [GNU AGPL v3.0](LICENSE). Built with [PyMuPDF and other open-source components](THIRD_PARTY.md).
No uploads, telemetry, private documents or user font files are included.
