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

1. **Download & extract** the `PageThaw-…-windows-x64.zip` from the latest release.
   Extract the whole folder, then open **PageThaw.exe**. Keep `_internal` beside it.
2. **Add your PDFs** and click **Scan files & fonts**.
3. **Check the fonts.** If one is missing, add your own `.ttf` / `.otf` or approve
   an installed replacement. Nothing is silently substituted.
4. **Choose a new output folder** and click **Convert to Word**. Open the `.docx`
   files in desktop Word and review every page.

**No account, Python installation or Word is needed to convert.** All processing
happens on your computer. Use the **Русский / English** button at the top right
to switch the interface; your choice is remembered.

## What you get

| Feature | How it helps |
| :--- | :--- |
| Batch conversion | Convert several PDFs in one run, with a report for each file. |
| Editable page layout | Text stays in positioned boxes; logos and borders stay in place. |
| Font choices | Match regular, bold and italic faces, or approve a substitute. |
| Form blank lines | Optionally turn underscore blanks into continuous lines. |
| Page comparison | With desktop Word installed, generate original/export image pairs. |

<details>
<summary>Preview the Russian interface</summary>

![PageThaw — RU](docs/images/app-ru.jpg)

</details>

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
