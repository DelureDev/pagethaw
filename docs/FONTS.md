# Fonts inside Word files

The optional **Include fonts in Word files when editing is permitted** setting
helps a DOCX keep its fonts on another computer. It is off initially, works in
both conversion modes, and adds only the font faces used by that PDF. It increases
the document size. No fonts are downloaded or shipped with PageThaw.

PageThaw includes the complete original font file, so newly typed characters
remain available. It checks the font's OpenType embedding permissions and accepts
only installable or editable embedding. Restricted, preview/print-only, bitmap-only
and ambiguous permissions are skipped. Permission flags are never changed. A
no-subsetting flag is respected by including the whole face.

This version supports individual static fonts with TrueType outlines. CFF-based
OTF fonts, collections and variable fonts are not embedded. A `.ttf` extension
alone does not establish permission or compatibility. The app tells you when a
font was skipped; select that file and open **Details** for the reason. Recipients
still need those fonts installed, or you can explicitly approve a different font
and convert again. There is no silent replacement.

The saved package is reopened and its embedded data checked against the approved
font hash. Original font bytes and documents remain unchanged. Desktop Microsoft
Word is the tested editor; other viewers or organization policies may handle
embedded fonts differently. Word may rewrite internal font names and add fonts
for its own styles when saving a document.

Technical references: [OpenType embedding permissions](https://learn.microsoft.com/en-us/typography/opentype/spec/os2#fstype),
[Word font parts](https://learn.microsoft.com/en-us/openspecs/office_standards/ms-oe376/1663dabc-5d98-463f-889e-bcd9b77c3d34),
[Microsoft's font embedding guide](https://support.microsoft.com/en-gb/office/fonts/benefits-of-embedding-custom-fonts).
