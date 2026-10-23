# PageThaw 1.2.1 — closer spacing in editable Word files

- Fixes excessive vertical spacing with fonts whose natural line height exceeds
  the PDF's spacing. Font sizes remain unchanged.
- Removes unnecessary gaps between form rows and gives empty caption cells the
  correct font metrics. Fields still expand when you type.
- Uses responsive spacing where the PDF and font provide reliable measurements;
  uncertain text keeps expanding minimum spacing.

Tested with desktop Word, larger text, long field entries and save/reopen.
The reported form's section 4 now fits on the first page again. Editable output
can still have different page breaks; this is not an exact-layout guarantee.
Preserve layout output is unchanged. No private PDFs or fonts are included.

## По-русски

- Исправлены лишние интервалы, из-за которых текст уходил на следующую страницу.
  Размер шрифта не уменьшается.
- Убраны лишние промежутки между строками бланка. Поля продолжают расти при вводе.
- Проверены длинные записи, увеличение текста и повторное открытие в Word.

В проверенном бланке раздел 4 снова помещается на первой странице. В режиме
редактирования отдельные переносы между страницами всё ещё могут отличаться от
PDF. Режим сохранения макета не изменён. Личные документы и шрифты в релиз не входят.
