# PageThaw 1.2 — editable tables and portable fonts

- Editable text now reconstructs simple tables with complete row/column borders.
  Cells expand as you type, and text keeps its original cell order and emphasis.
- Better paragraph indents, hanging indents, alignment and line spacing.
- Optional **Include fonts in Word files** embeds permitted full static TrueType
  faces. Recipients can edit with those fonts without installing them. Restricted
  or unsupported faces are skipped with a visible notice and a reason in Details.
- Font permissions remain unchanged. No fonts or private PDFs ship with the app.
- Both interfaces, the single EXE, safe repeated conversion and DOCX-only output
  remain available. Preserve layout is unchanged when embedding is off.

Tested locally with 120 automated checks, desktop Word exports and editing,
independent code/visual review, and a font that was not installed on the test PC.
See [verification details](VERIFICATION.md) for release validation.

Complex/merged tables, overlapping graphics and scans remain outside editable
mode's supported scope. Spacing and page counts can change; review the result.

## По-русски

- Простые таблицы с полной сеткой теперь становятся обычными таблицами Word.
  Ячейки растут при вводе текста.
- Улучшены отступы, выравнивание и интервалы абзацев.
- Можно включить разрешённые TrueType-шрифты в DOCX. Получателям не придётся их
  устанавливать. Если шрифт нельзя включить, приложение покажет причину.
- Ограничения шрифтов не обходятся. Личные PDF и шрифты не входят в релиз.

Сложные таблицы и сканы по-прежнему требуют другого способа обработки.
Интервалы и число страниц могут измениться — проверяйте полученный Word-файл.
