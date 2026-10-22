"""Local English/Russian UI text; document content and report data stay unchanged."""
from pathlib import Path
import json
import locale
import os
import re
import string
import tempfile


RU = {
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
    return face.full_name + (' [Полужирный]' if face.bold else '') + (' [Курсив]' if face.italic else '')


def preference_path():
    return Path(os.environ.get('LOCALAPPDATA', Path.home()/'.config'))/'PageThaw'/'settings.json'


def load_language():
    try:
        saved = json.loads(preference_path().read_text(encoding='utf-8'))
        if isinstance(saved, dict) and saved.get('language') in ('en', 'ru'):
            return saved['language']
    except (OSError, ValueError):
        pass
    try:
        return 'ru' if (locale.getlocale()[0] or '').lower().startswith('ru') else 'en'
    except ValueError:
        return 'en'


def save_language(language):
    if language not in ('en', 'ru'):
        raise ValueError('Unsupported interface language')
    temporary = None
    try:
        path = preference_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            json.dump({'language': language}, stream)
        temporary.replace(path)
        return True
    except OSError:
        return False
    finally:
        if temporary:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
