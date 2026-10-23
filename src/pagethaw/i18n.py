"""Local English/Russian UI text; document content and report data stay unchanged."""
from pathlib import Path
import json
import locale
import os
import re
import string
import tempfile


RU = {
    'Converted; some fonts still need installing — Details': 'Готово; часть шрифтов нужно установить — «Подробнее»',
    'Normal paragraphs, expanding fields and simple ruled tables. Spacing and page count may change.': 'Обычные абзацы, поля с изменяемой высотой и простые таблицы. Интервалы и число страниц могут измениться.',
    'Include fonts in Word files when editing is permitted': 'Включать шрифты в Word, если разрешено редактирование',
    'Keep PDF line breaks in normal paragraphs': 'Сохранять переносы строк PDF внутри обычных абзацев',
    'Normal editable paragraphs with PDF line breaks. These breaks remain when you edit the text.': 'Обычные редактируемые абзацы с переносами строк из PDF. Переносы сохраняются при правке текста.',
    'Fonts included: {count}': 'Включено шрифтов: {count}',
    'Recipients still need the fonts listed above installed. No font was replaced.': 'Получателям нужно установить перечисленные выше шрифты. Шрифты не заменялись.',
    '{passed} converted; {failed} failed; {cancelled} cancelled. Review the Word files. Some fonts could not be included. Select a file and open Details.': 'Готово: {passed}; ошибок: {failed}; отменено: {cancelled}. Проверьте файлы Word. Часть шрифтов не удалось включить: выберите файл и откройте «Подробнее».',
    'Font has no embedding permission information.': 'В шрифте нет сведений о разрешении на встраивание.',
    'Font allows bitmap embedding only.': 'Шрифт разрешает встраивать только растровые символы.',
    'Font has ambiguous embedding permissions.': 'Разрешения на встраивание шрифта неоднозначны.',
    'Font restricts embedding.': 'Шрифт запрещает встраивание.',
    'Font permits preview and printing only, not editing.': 'Шрифт разрешает только просмотр и печать, без редактирования.',
    'Embedding currently supports static TrueType outlines only.': 'Пока поддерживается встраивание только статических шрифтов с контурами TrueType.',
    'Font embedding information could not be read.': 'Не удалось прочитать сведения о встраивании шрифта.',
    'Conflicting faces use the same family and style.': 'Разные файлы используют одинаковые семейство и начертание.',
    'Font file changed; choose the font again: {font}': 'Файл шрифта изменился; выберите его заново: {font}',
    'Install {font} for your Windows account?\n\nWord needs it installed for conversion checks. Optional embedding only includes fonts that permit editing. Nothing is uploaded. Use a font you have permission to install.': 'Установить {font} для вашей учётной записи Windows?\n\nОн нужен Word для проверки конвертации. При встраивании включаются только шрифты, разрешающие редактирование. Ничего не загружается в интернет. Устанавливайте шрифты, на которые у вас есть разрешение.',
    'text crosses a ruled table boundary.': 'текст пересекает границу таблицы.',
    'text crosses a ruled table cell.': 'текст пересекает границу ячейки таблицы.',
    'a ruled table contains unsupported graphics.': 'внутри таблицы есть неподдерживаемая графика.',
    'text beside a ruled table needs manual reconstruction.': 'текст рядом с таблицей нужно восстановить вручную.',
    'Conversion': 'Режим',
    'Editable text': 'Редактировать текст',
    'Preserve layout': 'Сохранить макет',
    'Normal paragraphs and expanding fields. Single-column forms; spacing and page count may change.': 'Обычные абзацы и поля с изменяемой высотой. Бланки в одну колонку; интервалы и число страниц могут измениться.',
    'Choose Editable text or Preserve layout.': 'Выберите режим «Редактировать текст» или «Сохранить макет».',
    'Conversion cancelled.': 'Конвертация отменена.',
    'Editable mode: {reason} Use Preserve layout for this PDF.': 'Режим редактирования: {reason} Для этого PDF выберите «Сохранить макет».',
    'multiple body columns are not supported.': 'несколько колонок текста не поддерживаются.',
    'nested or overlapping table borders are not supported.': 'вложенные или пересекающиеся рамки не поддерживаются.',
    'a table grid or graphics inside a bordered form need manual reconstruction.': 'сетку таблицы или графику внутри рамки нужно восстановить вручную.',
    'text crosses a form border.': 'текст пересекает рамку бланка.',
    'footnote references are ambiguous.': 'не удалось однозначно связать сноску с её знаком в тексте.',
    'vertical or degenerate drawing paths are not supported.': 'вертикальные линии или вырожденные контуры не поддерживаются.',
    'graphics overlap selectable text.': 'графика пересекается с текстом.',
    'a large graphic needs manual placement.': 'крупную графику нужно разместить вручную.',
    'a form row has insufficient space for editable values.': 'в строке бланка недостаточно места для редактируемых значений.',
    'form captions cannot be assigned to distinct fields.': 'не удалось однозначно сопоставить подписи и поля.',
    'an empty drawn box is not a supported editable field.': 'пустая нарисованная рамка не поддерживается как редактируемое поле.',
    'a drawn line crosses text.': 'нарисованная линия пересекает текст.',
    'Editable conversion did not account for every source character.': 'Не пройдена проверка полноты исходного текста. Результат не сохранён.',
    'Editable output unexpectedly contains positioned text.': 'В результате обнаружены текстовые блоки. Проверка не пройдена.',
    'Editable output contains text without an approved font.': 'В результате есть текст без подтверждённого шрифта. Проверка не пройдена.',
    'Editable output text, reading order or emphasis verification failed.': 'Не пройдена проверка текста, порядка чтения или начертаний. Результат не сохранён.',
    'Editable footnote relationship verification failed.': 'Не пройдена проверка связи сносок с документом. Результат не сохранён.',
    'Editable footnote reference verification failed.': 'Не пройдена проверка ссылок на сноски. Результат не сохранён.',
    'Editable footnote separator verification failed.': 'Не пройдена проверка разделителя сносок. Результат не сохранён.',
    'Editable footnote identity verification failed.': 'Не пройдена проверка соответствия сносок. Результат не сохранён.',
    'Editable footnote content or reference verification failed.': 'Не пройдена проверка текста сносок или ссылок на них. Результат не сохранён.',
    'Installed fonts changed. Scan files & fonts again before converting.': 'Установленные шрифты изменились. Повторите проверку файлов и шрифтов перед конвертацией.',
    'Cancelled before saving the document.': 'Операция отменена перед сохранением документа.',
    'Details': 'Подробности',
    'File details': 'Сведения о файле',
    'Retry failed': 'Повторить ошибки',
    'Font preference': 'Выбор шрифта',
    'This font choice applies now, but could not be saved for next time.': 'Шрифт выбран, но сохранить этот выбор на будущее не удалось.',
    'Scan cancelled. Scan again before converting.': 'Проверка отменена. Повторите её перед конвертацией.',
    'Scanning {number}/{total}: {file}': 'Проверка {number}/{total}: {file}',
    'Cannot access this file or folder. Close it in other apps or choose a writable folder, then retry.': 'Нет доступа к файлу или папке. Закройте файл в других приложениях или выберите доступную папку и повторите.',
    'File or folder not found. Check that it still exists, then scan again.': 'Файл или папка не найдены. Проверьте путь и повторите проверку.',
    'This path has the wrong type. Choose a PDF file and a separate output folder.': 'Неверный тип пути. Выберите PDF-файл и отдельную папку для результата.',
    'This PDF is damaged or unreadable. Try opening it in a PDF viewer and saving a new copy.': 'PDF повреждён или не читается. Попробуйте открыть его в программе просмотра и сохранить новую копию.',
    'Fonts': 'Шрифты',
    'Choose / install font…': 'Выбрать / установить шрифт…',
    'Verified glyph match': 'Символы совпадают',
    'Choice required': 'Нужен выбор',
    'Choose fonts below': 'Выберите шрифты ниже',
    '{count} font(s) need your choice. An exact match is missing, different or unverified. Choose an installed font or add a font file.': 'Требуют выбора: {count}. Точное совпадение не найдено или не подтверждено. Выберите установленный шрифт или добавьте файл шрифта.',
    'Fonts are ready. Approved replacements can change spacing.': 'Шрифты выбраны. Подтверждённая замена может изменить интервалы.',
    'PDF fonts appear here after adding files. Replacements always need your approval.': 'Шрифты PDF появятся здесь после добавления файлов. Замена — только с вашего согласия.',
    'Conflicting font versions': 'Конфликт версий шрифта',
    'Windows has multiple versions of {font}. Remove duplicate versions in Windows Fonts and rescan, or choose a different font family.': 'В Windows установлено несколько версий {font}. Удалите дубликаты в настройках шрифтов Windows и повторите проверку или выберите другое семейство.',
    'An exact match for {source} could not be verified. Use {font} instead?\n\nLetter shapes and spacing may change. Review the converted pages.': 'Точное совпадение с {source} не подтверждено. Использовать {font}?\n\nФорма букв и интервалы могут измениться. Проверьте страницы после конвертации.',
    'Windows PowerShell is unavailable. Conversion works without Word comparison.': 'Windows PowerShell недоступен. Конвертация работает без сравнения через Word.',
    'Fonts…': 'Шрифты…',
    'Options…': 'Настройки…',
    'Save Word files to': 'Сохранить файлы Word в',
    'Browse…': 'Выбрать…',
    '{passed} converted; {failed} failed; {cancelled} cancelled. Review the Word files.': 'Готово: {passed}; ошибок: {failed}; отменено: {cancelled}. Проверьте файлы Word.',
    'PageThaw — PDF to Word': 'PageThaw — PDF в Word',
    'PDF forms → editable Word documents': 'PDF-бланки → редактируемые документы Word',
    'Preserve the page. Choose the fonts. Convert locally.': 'Сохраняйте макет. Выбирайте шрифты. Конвертируйте на своём компьютере.',
    '1  Choose PDFs': '1  Выберите PDF',
    'Add PDFs…': 'Добавить PDF…',
    'Remove selected': 'Убрать выбранные',
    'Scan files & fonts': 'Проверить файлы и шрифты',
    'Pages': 'Страниц',
    'Status': 'Статус',
    'PDF file': 'PDF-файл',
    '2  Check fonts': '2  Проверьте шрифты',
    'Missing fonts require your choice. Replacements can change spacing.': 'Укажите недостающие шрифты. Замена может изменить интервалы.',
    'Choose font…': 'Выбрать шрифт…',
    'Word font': 'Шрифт в Word',
    'Match': 'Соответствие',
    'Font used in PDF': 'Шрифт в PDF',
    '3  Convert': '3  Конвертируйте',
    'Output folder…': 'Папка результата…',
    'Turn standalone underscore blanks into lines': 'Заменять прочерки из подчёркиваний линиями',
    'Graphics DPI': 'DPI графики',
    'Text stays in positioned boxes. Long edits do not reflow the page. Open results in desktop Word.': 'Текст остаётся в блоках. Длинные правки могут выйти за границы. Открывайте результат в настольном Word.',
    'Convert to Word': 'Конвертировать в Word',
    'Cancel': 'Отмена',
    'Open output': 'Открыть папку',
    'Compare pages (Word)…': 'Сравнить страницы (Word)…',
    'v{version}  ·  Open source / AGPL-3.0  ·  No uploads': 'v{version}  ·  Открытый код / AGPL-3.0  ·  Без загрузки в интернет',
    'Choose your PDFs to begin. Files stay on your computer.': 'Добавьте PDF для начала. Файлы остаются на вашем компьютере.',
    'Select PDFs': 'Выберите PDF',
    'PDF documents': 'Документы PDF',
    'Scan files & fonts before converting.': 'Перед конвертацией проверьте файлы и шрифты.',
    'Ready': 'Готов к конвертации',
    'Not scanned': 'Не проверен',
    'Choose PDFs': 'Выберите PDF',
    'Add one or more PDFs first.': 'Сначала добавьте один или несколько PDF.',
    'Scanning PDFs and installed font faces…': 'Проверяем PDF и установленные шрифты…',
    'Scan complete. {missing} font choice(s) needed; {unsupported} unsupported file(s).': 'Проверка завершена. Шрифтов на выбор: {missing}; неподдерживаемых файлов: {unsupported}.',
    'Choose a font…': 'Выберите шрифт…',
    'Identity match': 'Совпадает название',
    'Replacement approved': 'Замена подтверждена',
    'Missing / ambiguous': 'Не найден / неоднозначен',
    'Choose a PDF font': 'Выберите шрифт PDF',
    'Select a row in the font list first.': 'Сначала выберите строку в списке шрифтов.',
    'Choose an output folder': 'Выберите папку для результата',
    'Scan first': 'Сначала выполните проверку',
    'Fonts need your choice': 'Выберите недостающие шрифты',
    'Choose a font for: {fonts}': 'Укажите шрифт для: {fonts}',
    'Converting locally…': 'Конвертируем на вашем компьютере…',
    '{done}/{total}: {file} — {status}': '{done}/{total}: {file} — {status}',
    '{passed} converted; {failed} failed; {cancelled} cancelled. Review every page in Word. Details: pagethaw-report.json': 'Готово: {passed}; ошибок: {failed}; отменено: {cancelled}. Проверьте все страницы в Word. Отчёт: pagethaw-report.json',
    'Convert first': 'Сначала выполните конвертацию',
    'Convert a batch first, then create a comparison using installed desktop Microsoft Word.': 'Сначала конвертируйте файлы, затем сравните их с помощью установленного настольного Microsoft Word.',
    'Scan originals': 'Проверьте исходные PDF',
    'Add and scan the original PDFs before comparing this output folder.': 'Перед сравнением добавьте и проверьте исходные PDF.',
    'Exporting through desktop Word; a separate instance is used…': 'Экспортируем через отдельный экземпляр настольного Word…',
    'Cancelling safely. Wait for the current page/export to finish, then close.': 'Отменяем операцию. Дождитесь завершения текущей страницы или экспорта, затем закройте окно.',
    'Choose font for {source}': 'Выберите шрифт для {source}',
    'Choose an installed face, or add your own font file. Nothing is downloaded.': 'Выберите установленное начертание или добавьте свой файл шрифта. Загрузки из интернета нет.',
    'Add font file…': 'Добавить файл шрифта…',
    'Use selected font': 'Использовать выбранный',
    'Choose the correct regular / bold / italic face. Replacement fonts can change spacing.': 'Выберите нужное начертание: обычное, полужирное или курсивное. Замена может изменить интервалы.',
    'Choose a static font face': 'Выберите файл обычного (не вариативного) шрифта',
    'Font files': 'Файлы шрифтов',
    'This font lacks required characters: {chars}': 'В шрифте нет нужных символов: {chars}',
    'Install this font?': 'Установить шрифт?',
    'Install {font} for your Windows account?\n\nWord needs it installed to display the result. The font is not embedded or uploaded. Use a font you have permission to install.': 'Установить {font} для вашей учётной записи Windows?\n\nШрифт нужен Word для отображения результата. Он не встраивается в документ и не отправляется в интернет. Устанавливайте только шрифты, на которые у вас есть разрешение.',
    'Font could not be added': 'Не удалось добавить шрифт',
    'Missing characters': 'Не хватает символов',
    'Choose another font. Missing: {chars}': 'Выберите другой шрифт. Не хватает: {chars}',
    'Use this replacement?': 'Подтвердить замену?',
    'Replace {source} with {font}?\n\nLetter widths and spacing may change. Review the converted pages before using them.': 'Заменить {source} на {font}?\n\nШирина букв и интервалы могут измениться. Проверьте страницы после конвертации.',
    'Language preference': 'Язык интерфейса',
    'The language changed for this session, but the preference could not be saved.': 'Язык изменён для этого сеанса, но сохранить настройку не удалось.',
    'converted; visual review required': 'готово; нужна проверка страниц',
    'failed': 'ошибка',
    'cancelled': 'отменено',
    # Known engine messages are localized only for display; JSON reports remain stable.
    'Use an unlocked PDF file.': 'Используйте PDF без пароля.',
    'The PDF has no pages.': 'В PDF нет страниц.',
    'Pages larger than 22 inches are outside Word page-size limits.': 'Размер страницы превышает ограничение Word (22 дюйма).',
    'Mixed page sizes are not supported yet.': 'Разные размеры страниц в одном PDF пока не поддерживаются.',
    'Page {page}: {reason}': 'Страница {page}: {reason}',
    'rotated pages are not supported yet.': 'повёрнутые страницы пока не поддерживаются.',
    'interactive form fields are not supported yet.': 'интерактивные поля PDF пока не поддерживаются.',
    'hidden, transparent or outlined text is not supported (including OCR layers).': 'скрытый, прозрачный или контурный текст не поддерживается (включая слои OCR).',
    'rotated/vertical text is not supported yet.': 'повёрнутый или вертикальный текст пока не поддерживается.',
    'unmapped PDF characters need a different extraction workflow.': 'для символов без корректной кодировки нужен другой способ извлечения.',
    'right-to-left text is not supported yet.': 'текст справа налево пока не поддерживается.',
    'unsupported control characters.': 'неподдерживаемые управляющие символы.',
    'no selectable text; scanned pages need OCR first.': 'нет выделяемого текста; скан сначала нужно распознать (OCR).',
    'stretched or unusually spaced text needs manual conversion.': 'растянутый текст или необычные интервалы требуют ручной конвертации.',
    'The source PDF changed after scanning. Scan it again before conversion.': 'PDF изменился после проверки. Проверьте его заново.',
    'Choose a font for {font}. No substitution was applied.': 'Выберите шрифт для {font}. Замена не выполнялась.',
    'Install {font} before conversion so Word can use it.': 'Установите {font} перед конвертацией, чтобы Word мог его использовать.',
    '{font} lacks characters: {chars}': 'В шрифте {font} нет символов: {chars}',
    'Output already exists: {file}': 'Результат уже существует: {file}',
    'Choose 96, 144 or 192 DPI for graphics.': 'Выберите 96, 144 или 192 DPI для графики.',
    'Cancelled before the next page.': 'Операция отменена перед следующей страницей.',
    'A partial conversion already exists: {file}': 'Уже существует незавершённый результат: {file}',
    'DOCX page-anchor verification failed.': 'Не пройдена проверка расположения страниц DOCX.',
    'DOCX text/rule verification failed. No output was accepted.': 'Не пройдена проверка текста или линий DOCX. Результат не сохранён.',
    'Choose a new output folder; this folder already contains a PageThaw report.': 'Выберите новую папку: в этой уже есть отчёт PageThaw.',
    'Duplicate or existing output name: {file}. Choose separate output folders.': 'Повторяющееся или существующее имя: {file}. Выберите отдельные папки результата.',
    'Choose an individual .ttf or .otf face. Font collections are not supported yet.': 'Выберите отдельный файл .ttf или .otf. Коллекции шрифтов пока не поддерживаются.',
    'Variable fonts are not supported yet; use a static font face.': 'Вариативные шрифты пока не поддерживаются. Используйте обычный шрифт.',
    'Font does not contain a usable family and PostScript identity.': 'В файле нет корректных названий семейства и PostScript.',
    'Install this font using your operating system, then rescan fonts.': 'Установите шрифт средствами ОС, затем повторите проверку.',
    'Windows could not activate this font. Install it with Windows Font Viewer.': 'Windows не удалось активировать шрифт. Установите его через средство просмотра шрифтов Windows.',
    'Word comparison requires Windows and desktop Microsoft Word.': 'Для сравнения нужны Windows и настольный Microsoft Word.',
    'Comparison already exists. Choose a new output batch.': 'Сравнение уже существует. Выберите новую папку результата.',
    'Word export timed out after {seconds} seconds.': 'Word не завершил экспорт за {seconds} сек.',
    'Word export failed. See worker.log.': 'Ошибка экспорта Word. Подробности в worker.log.',
    'Word returned an instance containing documents.': 'Word вернул экземпляр с уже открытыми документами. Экспорт остановлен.',
    'Word returned an existing process; refusing to take ownership.': 'Word вернул уже существующий процесс. Он оставлен без изменений.',
    'Word export timed out after {seconds} seconds. Owned-process cleanup failed; inspect worker.json.': 'Word не завершил экспорт за {seconds} сек. Не удалось закрыть процесс экспорта; см. worker.json.',
    'Word export timed out after {seconds} seconds. Owned-process cleanup timed out; inspect worker.json.': 'Word не завершил экспорт за {seconds} сек. Превышено время закрытия процесса экспорта; см. worker.json.',
    'Word export timed out after {seconds} seconds. No confirmed process identity; no Word process was terminated.': 'Word не завершил экспорт за {seconds} сек. Процесс не удалось однозначно определить; процессы Word не завершались.',
    'This batch already has a comparison report. Preserve it and choose a new batch.': 'Для этой папки уже есть отчёт сравнения. Сохраните его и выберите новую папку.',
    'No successfully converted documents are available for comparison.': 'Нет успешно сконвертированных документов для сравнения.',
    'Comparison cancelled: {done} of {total} documents exported. Remaining comparisons were not run.': 'Сравнение отменено. Экспортировано документов: {done} из {total}. Остальные не сравнивались.',
    'Source or DOCX changed since conversion. Convert a fresh batch before comparing.': 'Исходный PDF или DOCX изменился после конвертации. Сначала конвертируйте заново.',
    'Word comparison: {file}': 'Сравнение через Word: {file}',
    'Page count changed: {before} → {after}': 'Изменилось число страниц: {before} → {after}',
    'Comparison stopped: {reason} See comparison-report.json.': 'Сравнение остановлено: {reason} См. comparison-report.json.',
    'Comparison images are ready in the comparisons folder. Inspect every page; visual review is not automatic.': 'Изображения для сравнения готовы в папке comparisons. Проверьте каждую страницу — визуальная проверка не автоматическая.',
}


def _templates():
    for source, target in RU.items():
        if '{' in source:
            pattern = ''
            for literal, field, _, _ in string.Formatter().parse(source):
                pattern += re.escape(literal)
                if field:
                    # "Page count changed" must not be mistaken for "Page 2: ...".
                    content = r'\d+' if field == 'page' else '.+?'
                    pattern += f'(?P<{field}>{content})'
            yield re.compile(pattern, re.DOTALL), target


TEMPLATES = list(_templates())


def translate(language, message, **values):
    if language != 'ru':
        return message.format(**values) if values else message
    if message in RU:
        result = RU[message]
        return result.format(**values) if values else result
    for pattern, target in TEMPLATES:
        match = pattern.fullmatch(message)
        if match:
            parts = match.groupdict()
            for key in ('reason', 'status'):
                if key in parts:
                    parts[key] = translate(language, parts[key])
            return target.format(**parts)
    # Preserve unknown OS/library diagnostics verbatim, including paths and codes.
    return message.format(**values) if values else message


def font_label(face, language):
    if language != 'ru':
        return face.label
    return face.full_name + (' [Полужирный]' if face.bold else '') + (' [Курсив]' if face.italic else '') + (f' · {face.version}' if face.version else '')


def preference_path():
    return Path(os.environ.get('LOCALAPPDATA', Path.home()/'.config'))/'PageThaw'/'settings.json'


def load_language():
    from .preferences import load
    saved = load(preference_path())
    if saved.get('language') in ('en', 'ru'):
        return saved['language']
    try:
        return 'ru' if (locale.getlocale()[0] or '').lower().startswith('ru') else 'en'
    except ValueError:
        return 'en'


def save_language(language):
    from .preferences import save
    if language not in ('en', 'ru'):
        raise ValueError('Unsupported interface language')
    return save({'language': language}, preference_path())
