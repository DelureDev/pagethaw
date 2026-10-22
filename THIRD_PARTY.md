# Third-party components

PageThaw uses PyMuPDF/MuPDF under AGPL-3.0, python-docx under MIT, fontTools under
MIT, Pillow under MIT-CMU, and Python/Tcl/Tk under their respective licenses.
PyInstaller's bootloader exception permits distribution of the generated bundle
under the application's license. The ZIP includes dependency notices in its
`licenses/` folder. The single EXE embeds the same notices; extract them with
`--export-notices NEW_FOLDER` (see [the guide](docs/USAGE.md)).

Exact installed versions and corresponding source-download URLs are written into
`DEPENDENCY_SOURCES.json` during the build. Source distributions are available at
the recorded PyPI URLs. PyMuPDF's source distribution includes/references the MuPDF
source used by its build; retain all upstream notices when rebuilding.

- PageThaw source: https://github.com/DelureDev/pagethaw
- PyMuPDF: https://github.com/pymupdf/PyMuPDF
- MuPDF: https://git.ghostscript.com/?p=mupdf.git
- python-docx: https://github.com/python-openxml/python-docx
- fontTools: https://github.com/fonttools/fonttools
- Pillow: https://github.com/python-pillow/Pillow
- Python: https://www.python.org/downloads/source/
- Tcl/Tk: https://www.tcl.tk/software/tcltk/download.html
- PyInstaller: https://pyinstaller.org/en/stable/license.html

No user-supplied or Windows system fonts are bundled. Fonts selected by end users
remain subject to their own licenses; the app does not modify those permissions.
