"""Small native Windows GUI; no web server, account or network dependency."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import os
import queue
import threading
import tempfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from . import __version__
from .engine import inspect_pdf, convert_batch
from .fonts import installed_fonts, read_font, install_for_current_user, missing_glyphs
from .font_match import automatic_mapping, match_status, family_conflicts
from .i18n import translate, font_label, load_language, save_language
from . import preferences
from .engine import error_message


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.language = tk.StringVar(value=load_language())
        self.title(self.t('PageThaw — PDF to Word'))
        self.geometry(f'920x{min(760, self.winfo_screenheight()-80)}')
        self.minsize(780, 500)
        self.configure(background='#f1f5f9')
        self.paths = []
        self.infos = []
        self.faces = []
        self.mapping = {}
        self.font_chars = {}
        self.file_results = {}
        self.options_expanded = False
        self.last_conversion = None
        self.busy = False
        self.cancel = threading.Event()
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.events = queue.Queue()
        settings = preferences.load()
        saved_output = settings.get('output', '')
        self.mode = tk.StringVar(value=settings.get('mode') if settings.get('mode') in ('layout', 'editable') else 'editable')
        self.output = tk.StringVar(value=saved_output if isinstance(saved_output, str) else '')
        self.status = tk.StringVar()
        self.font_status = tk.StringVar()
        self.set_status('Choose your PDFs to begin. Files stay on your computer.')
        self.rules = tk.BooleanVar(value=False)
        self.dpi = tk.StringVar(value='144')
        self.buttons = []
        self.make_ui()
        self.protocol('WM_DELETE_WINDOW', self.close)
        self.after(100, self.poll)

    def t(self, message, **values):
        return translate(self.language.get(), message, **values)

    def set_status(self, message, **values):
        self.status_message = (message, values)
        self.status.set(self.t(message, **values))

    def switch_language(self):
        if self.busy:
            return
        files, fonts = self.file_tree.selection(), self.font_tree.selection()
        self.language.set('ru' if self.language.get() == 'en' else 'en')
        saved = save_language(self.language.get())
        # The widgets are rebuilt, but the selected files, options and results live
        # in the model/StringVars and survive the language switch.
        for child in self.winfo_children():
            child.destroy()
        self.buttons = []
        self.title(self.t('PageThaw — PDF to Word'))
        self.make_ui()
        self.refresh_files()
        self.refresh_fonts()
        self.file_tree.selection_set([key for key in files if self.file_tree.exists(key)])
        self.font_tree.selection_set([key for key in fonts if self.font_tree.exists(key)])
        message, values = self.status_message
        self.set_status(message, **values)
        if not saved:
            messagebox.showwarning(self.t('Language preference'), self.t('The language changed for this session, but the preference could not be saved.'))

    def make_ui(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('.', font=('Segoe UI', 10))
        style.configure('TFrame', background='#f1f5f9')
        style.configure('TLabel', background='#f1f5f9', foreground='#1e293b')
        style.configure('TButton', padding=(10, 6))
        style.configure('Accent.TButton', background='#087f8c', foreground='white')
        style.map('Accent.TButton', background=[('active', '#065f6a'), ('disabled', '#94a3b8')])
        style.configure('Treeview', rowheight=28, fieldbackground='white', background='white')
        style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'), padding=5)
        canvas = tk.Canvas(self, background='#f1f5f9', highlightthickness=0)
        self.canvas = canvas
        page_scroll = ttk.Scrollbar(self, orient='vertical', command=canvas.yview)
        page_scroll.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)
        canvas.configure(yscrollcommand=page_scroll.set)
        wrap = ttk.Frame(canvas, padding=18)
        window = canvas.create_window((0, 0), window=wrap, anchor='nw')
        wrap.bind('<Configure>', lambda _: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>', lambda event: canvas.itemconfigure(window, width=event.width))
        wrap.columnconfigure(0, weight=1)
        header = ttk.Frame(wrap)
        header.grid(row=0, column=0, sticky='ew')
        ttk.Label(header, text='PageThaw', font=('Segoe UI', 23, 'bold')).pack(side='left')
        self.language_button = self.button(header, 'Русский' if self.language.get() == 'en' else 'English', self.switch_language)
        self.language_button.pack(side='right')
        ttk.Label(wrap, text=self.t('PDF forms → editable Word documents'), foreground='#64748b').grid(row=1, column=0, sticky='w', pady=(2, 16))
        toolbar = ttk.Frame(wrap)
        toolbar.grid(row=2, column=0, sticky='ew', pady=(0, 7))
        self.button(toolbar, 'Add PDFs…', self.add_files).pack(side='left')
        self.button(toolbar, 'Remove selected', self.remove_files).pack(side='left', padx=6)
        self.button(toolbar, 'Details', self.file_details).pack(side='right')
        files = ttk.Frame(wrap)
        files.grid(row=3, column=0, sticky='ew')
        self.file_tree = self.tree(files, ('pages', 'status'), ('Pages', 'Status'), height=3)
        self.file_tree.heading('#0', text=self.t('PDF file'))
        self.file_tree.column('#0', width=330)
        self.file_tree.column('pages', width=75, stretch=False)
        self.file_tree.column('status', width=350)
        self.file_tree.bind('<Double-1>', lambda _: self.file_details())
        self.file_tree.bind('<Return>', lambda _: self.file_details())
        self.font_frame = ttk.Frame(wrap, padding=(0, 10, 0, 5))
        self.font_frame.grid(row=4, column=0, sticky='ew')
        font_row = ttk.Frame(self.font_frame)
        font_row.pack(fill='x', pady=(0, 6))
        ttk.Label(font_row, text=self.t('Fonts'), font=('Segoe UI', 10, 'bold')).pack(side='left')
        self.button(font_row, 'Scan files & fonts', self.scan).pack(side='right')
        self.button(font_row, 'Choose / install font…', self.choose_font).pack(side='right', padx=6)
        self.font_warning = ttk.Label(self.font_frame, textvariable=self.font_status)
        self.font_warning.pack(fill='x', pady=(0, 7))
        self.font_warning.bind('<Configure>', lambda event: self.font_warning.configure(wraplength=max(200, event.width)))
        self.font_tree = self.tree(self.font_frame, ('target', 'status'), ('Word font', 'Match'), height=2)
        self.font_tree.heading('#0', text=self.t('Font used in PDF'))
        self.font_tree.column('#0', width=240)
        self.font_tree.column('target', width=270)
        self.font_tree.column('status', width=240)
        self.font_tree.bind('<Double-1>', lambda _: self.choose_font())
        self.font_tree.tag_configure('warning', foreground='#92400e')
        self.refresh_font_status()
        mode_row = ttk.Frame(self.font_frame, padding=(0, 12, 0, 0))
        mode_row.pack(fill='x')
        ttk.Label(mode_row, text=self.t('Conversion'), font=('Segoe UI', 10, 'bold')).pack(side='left', padx=(0, 12))
        for value, label in (('editable', 'Editable text'), ('layout', 'Preserve layout')):
            radio = ttk.Radiobutton(mode_row, text=self.t(label), variable=self.mode, value=value, command=self.mode_changed)
            radio.pack(side='left', padx=(0, 16))
            self.buttons.append(radio)
        self.mode_help = ttk.Label(self.font_frame, foreground='#64748b')
        self.mode_help.pack(fill='x', pady=(5, 0))
        self.mode_help.bind('<Configure>', lambda event: self.mode_help.configure(wraplength=max(200, event.width)))
        ttk.Label(wrap, text=self.t('Save Word files to'), font=('Segoe UI', 10, 'bold')).grid(row=5, column=0, sticky='w', pady=(16, 5))
        output_row = ttk.Frame(wrap)
        output_row.grid(row=6, column=0, sticky='ew')
        ttk.Entry(output_row, textvariable=self.output).pack(side='left', fill='x', expand=True)
        self.button(output_row, 'Browse…', self.choose_output).pack(side='right', padx=(8, 0))
        actions = ttk.Frame(wrap)
        actions.grid(row=7, column=0, sticky='ew', pady=(15, 0))
        self.button(actions, 'Convert to Word', self.convert, 'Accent.TButton').pack(side='left')
        self.cancel_button = ttk.Button(actions, text=self.t('Cancel'), command=self.cancel.set, state='disabled')
        self.cancel_button.pack(side='left', padx=7)
        self.button(actions, 'Open output', self.open_output).pack(side='left')
        self.retry_button = self.button(actions, 'Retry failed', lambda: self.convert(retry=True))
        self.retry_button.pack(side='left', padx=7)
        self.refresh_retry()
        self.button(actions, 'Options…', self.toggle_options).pack(side='right')
        self.options_frame = ttk.Frame(wrap, padding=(0, 12, 0, 0))
        self.options_frame.grid(row=8, column=0, sticky='ew')
        self.rules_option = ttk.Checkbutton(self.options_frame, text=self.t('Turn standalone underscore blanks into lines'), variable=self.rules)
        self.rules_option.pack(anchor='w')
        row = ttk.Frame(self.options_frame)
        row.pack(fill='x', pady=(7, 0))
        ttk.Label(row, text=self.t('Graphics DPI')).pack(side='left')
        ttk.Combobox(row, values=('96', '144', '192'), textvariable=self.dpi, state='readonly', width=6).pack(side='left', padx=8)
        self.button(row, 'Compare pages (Word)…', self.review).pack(side='right')
        if not self.options_expanded:
            self.options_frame.grid_remove()
        self.progress = ttk.Progressbar(wrap, mode='indeterminate')
        self.progress.grid(row=9, column=0, sticky='ew', pady=(14, 7))
        status_label = ttk.Label(wrap, textvariable=self.status)
        status_label.grid(row=10, column=0, sticky='ew')
        status_label.bind('<Configure>', lambda event: status_label.configure(wraplength=max(200, event.width)))
        ttk.Label(wrap, text=self.t('v{version}  ·  Open source / AGPL-3.0  ·  No uploads', version=__version__), foreground='#64748b').grid(row=11, column=0, sticky='e', pady=(10, 0))
        self.refresh_mode()

    def refresh_mode(self):
        editable = self.mode.get() == 'editable'
        self.mode_help.configure(text=self.t('Normal paragraphs and expanding fields. Single-column forms; spacing and page count may change.' if editable else
            'Text stays in positioned boxes. Long edits do not reflow the page. Open results in desktop Word.'))
        self.rules_option.configure(state='disabled' if editable else 'normal')

    def mode_changed(self):
        self.refresh_mode()
        self.file_results.clear()
        self.refresh_files()
        preferences.save({'mode': self.mode.get()})

    def toggle_options(self):
        self.options_expanded = not self.options_expanded
        self.options_frame.grid() if self.options_expanded else self.options_frame.grid_remove()
        self.fit_panels()

    def fit_panels(self):
        # Keep the convert controls visible when optional details are expanded.
        height = min(760 + 95*self.options_expanded,
                     self.winfo_screenheight()-80)
        width = self.winfo_width() if self.winfo_width() > 1 else 880
        self.geometry(f'{width}x{height}')

    def tree(self, parent, columns, headings, height):
        holder = ttk.Frame(parent)
        holder.pack(fill='both', expand=True)
        tree = ttk.Treeview(holder, columns=columns, height=height)
        for name, heading in zip(columns, headings):
            tree.heading(name, text=self.t(heading))
        tree.pack(side='left', fill='both', expand=True)
        scroll = ttk.Scrollbar(holder, orient='vertical', command=tree.yview)
        scroll.pack(side='right', fill='y')
        tree.configure(yscrollcommand=scroll.set)
        return tree

    def button(self, parent, label, command, style='TButton'):
        button = ttk.Button(parent, text=self.t(label), command=command, style=style)
        self.buttons.append(button)
        return button

    def add_files(self):
        values = filedialog.askopenfilenames(title=self.t('Select PDFs'), filetypes=[(self.t('PDF documents'), '*.pdf')])
        for value in values:
            path = Path(value).resolve()
            if path not in self.paths:
                self.paths.append(path)
        if values:
            self.infos = []
            self.file_results.clear()
            self.mapping.clear()
            self.font_chars.clear()
            self.faces = []
            self.refresh_files()
            self.font_tree.delete(*self.font_tree.get_children())
            self.refresh_font_status()
            if not self.output.get():
                self.output.set(str(self.paths[0].parent / 'PageThaw-output'))
            self.set_status('Scan files & fonts before converting.')
            self.scan()

    def refresh_files(self):
        self.file_tree.delete(*self.file_tree.get_children())
        index = {info.path: info for info in self.infos}
        for n, path in enumerate(self.paths):
            info = index.get(path)
            record = self.file_results.get(path)
            status = record.get('error', record['status']) if record else ((info.error or 'Ready') if info else 'Not scanned')
            if not record and info and not info.error and set(info.fonts)-self.mapping.keys():
                status = 'Choose fonts below'
            self.file_tree.insert('', 'end', iid=str(n), text=path.name,
                values=(info.pages if info else '—', self.t(status)))
        self.refresh_retry()

    def refresh_retry(self):
        if hasattr(self, 'retry_button'):
            retry = any(r['status'] in ('failed', 'cancelled') for r in self.file_results.values())
            self.retry_button.configure(state='normal' if retry and not self.busy else 'disabled')

    def file_details(self):
        selected = self.file_tree.selection()
        if not selected:
            return
        path = self.paths[int(selected[0])]
        info = next((i for i in self.infos if i.path == path), None)
        record = self.file_results.get(path, {})
        status = record.get('error') or record.get('status') or (info.error if info else '') or 'Ready'
        text = str(path)+'\n\n'+self.t(status)
        detail = record.get('detail')
        if detail and detail != status:
            text += '\n\n'+detail
        messagebox.showinfo(self.t('File details'), text)

    def remove_files(self):
        chosen = {int(n) for n in self.file_tree.selection()}
        self.paths = [p for n, p in enumerate(self.paths) if n not in chosen]
        self.infos = []
        self.file_results.clear()
        self.mapping.clear()
        self.font_chars.clear()
        self.faces = []
        self.font_tree.delete(*self.font_tree.get_children())
        self.refresh_font_status()
        self.refresh_files()
        if self.paths:
            self.scan()

    def scan(self):
        if not self.paths:
            messagebox.showinfo(self.t('Choose PDFs'), self.t('Add one or more PDFs first.'))
            return
        paths = list(self.paths)
        language = self.language.get()
        self.infos = []
        self.mapping.clear()
        self.font_chars.clear()
        self.file_results.clear()
        self.refresh_files()
        self.refresh_fonts()
        def inspect():
            infos = []
            for n, path in enumerate(paths, 1):
                if self.cancel.is_set():
                    raise InterruptedError('Scan cancelled. Scan again before converting.')
                self.events.put(('progress', translate(language, 'Scanning {number}/{total}: {file}', number=n, total=len(paths), file=path.name)))
                infos.append(inspect_pdf(path, cancel=self.cancel))
            if self.cancel.is_set():
                raise InterruptedError('Scan cancelled. Scan again before converting.')
            faces = installed_fonts(cancel=self.cancel)
            mapping = automatic_mapping(infos, faces, cancel=self.cancel)
            mapping.update(preferences.restore_fonts(infos, faces))
            if self.cancel.is_set():
                raise InterruptedError('Scan cancelled. Scan again before converting.')
            return infos, faces, mapping
        self.run_job(inspect, self.scanned, 'Scanning PDFs and installed font faces…')

    def scanned(self, value):
        self.infos, self.faces = value[:2]
        self.file_results.clear()
        self.mapping.clear()
        self.font_chars = {}
        for info in self.infos:
            if not info.error:
                for name, chars in info.fonts.items():
                    self.font_chars[name] = self.font_chars.get(name, '')+chars
        self.mapping = value[2] if len(value) > 2 else automatic_mapping(self.infos, self.faces)
        self.refresh_files()
        self.refresh_fonts()
        missing = len(self.font_chars)-len(self.mapping)
        self.set_status('Scan complete. {missing} font choice(s) needed; {unsupported} unsupported file(s).', missing=missing, unsupported=sum(bool(i.error) for i in self.infos))

    def refresh_fonts(self):
        self.font_tree.delete(*self.font_tree.get_children())
        for name in sorted(self.font_chars):
            face = self.mapping.get(name)
            self.font_tree.insert('', 'end', iid=name, text=name, values=(font_label(face, self.language.get()) if face else self.t('Choose a font…'),
                (self.t('Verified glyph match') if match_status(self.infos, name, face) == 'verified' else self.t('Replacement approved')) if face else self.t('Choice required')),
                tags=() if face else ('warning',))
        missing = [n for n in sorted(self.font_chars) if n not in self.mapping]
        if missing:
            self.font_tree.selection_set(missing[0])
        self.refresh_font_status()

    def refresh_font_status(self):
        missing = len(set(self.font_chars)-self.mapping.keys())
        if missing:
            text = self.t('{count} font(s) need your choice. An exact match is missing, different or unverified. Choose an installed font or add a font file.', count=missing)
        elif self.font_chars:
            text = self.t('Fonts are ready. Approved replacements can change spacing.')
        else:
            text = self.t('PDF fonts appear here after adding files. Replacements always need your approval.')
        self.font_status.set(text)
        self.font_warning.configure(foreground='#92400e' if missing else '#64748b')

    def choose_font(self):
        if self.busy:
            return
        selected = self.font_tree.selection()
        if not selected:
            messagebox.showinfo(self.t('Choose a PDF font'), self.t('Select a row in the font list first.'))
            return
        FontDialog(self, selected[0])

    def choose_output(self):
        path = filedialog.askdirectory(title=self.t('Choose an output folder'))
        if path:
            self.output.set(path)
            preferences.save({'output': path})

    def convert(self, retry=False):
        if not self.infos:
            messagebox.showinfo(self.t('Scan first'), self.t('Scan files & fonts before converting.'))
            return
        infos = [i for i in self.infos if not retry or self.file_results.get(i.path, {}).get('status') in ('failed', 'cancelled')]
        if not infos:
            return
        required = {name for i in infos if not i.error for name in i.fonts}
        missing = required-self.mapping.keys()
        if missing:
            messagebox.showwarning(self.t('Fonts need your choice'), self.t('Choose a font for: {fonts}', fonts=', '.join(sorted(missing))))
            return
        if not self.output.get().strip():
            self.choose_output()
            return
        mapping = {name: self.mapping[name] for name in required}
        output, rules, dpi, mode = Path(self.output.get()).resolve(), self.rules.get(), int(self.dpi.get()), self.mode.get()
        preferences.save({'output': str(output), 'mode': mode})
        def finished(records):
            self.last_conversion = (output, infos, records)
            self.converted(records, infos)
        def convert():
            current = installed_fonts(cancel=self.cancel)
            paths = {face.path for face in current}
            for face in mapping.values():
                if face.path not in paths or family_conflicts(face, current):
                    raise ValueError('Installed fonts changed. Scan files & fonts again before converting.')
            return convert_batch(infos, output, mapping, rules=rules, dpi=dpi, mode=mode, cancel=self.cancel,
                progress=lambda n, total, r: self.events.put(('progress', f'{n}/{total}: {r["input"]} — {r["status"]}')))
        self.run_job(convert, finished, 'Converting locally…')

    def converted(self, records, infos=None):
        self.file_results.update({info.path: record for info, record in zip(self.infos if infos is None else infos, records)})
        records = list(self.file_results.values())
        passed = sum(r.get('content_check') == 'passed' for r in records)
        failed = sum(r['status'] == 'failed' for r in records)
        self.set_status('{passed} converted; {failed} failed; {cancelled} cancelled. Review the Word files.', passed=passed, failed=failed, cancelled=len(records)-passed-failed)
        self.refresh_files()

    def review(self):
        if not self.last_conversion:
            messagebox.showinfo(self.t('Convert first'), self.t('Convert a batch first, then create a comparison using installed desktop Microsoft Word.'))
            return
        from .word_review import review_batch
        output, infos, records = self.last_conversion
        def compare():
            folder = Path(tempfile.mkdtemp(prefix='PageThaw-comparison-'))
            result = review_batch(infos, output, records=records, review_output=folder, cancel=self.cancel,
                progress=lambda text: self.events.put(('progress', text)))
            return result, folder
        def finished(value):
            message, folder = value
            self.set_status(message)
            os.startfile(str(folder))
        self.run_job(compare, finished, 'Exporting through desktop Word; a separate instance is used…')

    def open_output(self):
        path = Path(self.output.get()) if self.output.get() else None
        if path and path.is_dir():
            os.startfile(str(path))

    def run_job(self, action, callback, message):
        self.busy = True
        self.cancel.clear()
        self.set_status(message)
        self.progress.start()
        for button in self.buttons:
            button.configure(state='disabled')
        self.cancel_button.configure(state='normal')
        future = self.executor.submit(action)
        future.add_done_callback(lambda f: self.events.put(('done', (f, callback))))

    def poll(self):
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == 'progress':
                    self.set_status(value)
                else:
                    future, callback = value
                    self.busy = False
                    self.progress.stop()
                    for button in self.buttons:
                        button.configure(state='normal')
                    self.cancel_button.configure(state='disabled')
                    try:
                        callback(future.result())
                    except InterruptedError as exc:
                        self.set_status(str(exc))
                    except Exception as exc:
                        self.set_status(error_message(exc))
                        messagebox.showerror('PageThaw', self.t(error_message(exc)))
                    self.refresh_retry()
        except queue.Empty:
            pass
        self.after(100, self.poll)

    def close(self):
        if self.busy:
            self.cancel.set()
            self.set_status('Cancelling safely. Wait for the current page/export to finish, then close.')
            return
        self.executor.shutdown(wait=False)
        self.destroy()


class FontDialog(tk.Toplevel):
    def __init__(self, app, source):
        super().__init__(app)
        self.app, self.source = app, source
        self.t = app.t
        self.title(self.t('Choose font for {source}', source=source))
        self.geometry('780x580')
        self.minsize(650, 450)
        self.transient(app)
        self.grab_set()
        self.search = tk.StringVar()
        self.search.trace_add('write', lambda *_: self.refresh())
        body = ttk.Frame(self, padding=18)
        body.pack(fill='both', expand=True)
        ttk.Label(body, text=source, font=('Segoe UI', 16, 'bold')).pack(anchor='w')
        hint = ttk.Label(body, text=self.t('Choose an installed face, or add your own font file. Nothing is downloaded.'))
        hint.pack(fill='x', pady=8)
        hint.bind('<Configure>', lambda event: hint.configure(wraplength=max(200, event.width)))
        ttk.Entry(body, textvariable=self.search).pack(fill='x')
        self.list = tk.Listbox(body, font=('Segoe UI', 11), exportselection=False)
        self.list.pack(fill='both', expand=True, pady=10)
        row = ttk.Frame(body)
        row.pack(fill='x')
        ttk.Button(row, text=self.t('Add font file…'), command=self.add).pack(side='left')
        ttk.Button(row, text=self.t('Use selected font'), command=self.accept).pack(side='right')
        ttk.Label(body, text=self.t('Choose the correct regular / bold / italic face. Replacement fonts can change spacing.'), wraplength=660).pack(anchor='w', pady=(12, 0))
        self.refresh()

    def refresh(self):
        query = self.search.get().casefold()
        self.visible = [f for f in self.app.faces if query in font_label(f, self.app.language.get()).casefold()]
        self.list.delete(0, 'end')
        for face in self.visible:
            self.list.insert('end', font_label(face, self.app.language.get()))

    def add(self):
        selected = filedialog.askopenfilename(parent=self, title=self.t('Choose a static font face'), filetypes=[(self.t('Font files'), '*.ttf *.otf')])
        if not selected:
            return
        try:
            face = read_font(Path(selected))
            missing = missing_glyphs(face, self.app.font_chars[self.source])
            if missing:
                raise ValueError(self.t('This font lacks required characters: {chars}', chars=repr(''.join(missing[:24]))))
            if family_conflicts(face, self.app.faces):
                messagebox.showwarning(self.t('Conflicting font versions'), self.t('Windows has multiple versions of {font}. Remove duplicate versions in Windows Fonts and rescan, or choose a different font family.', font=face.family), parent=self)
                return
            if not messagebox.askyesno(self.t('Install this font?'), self.t('Install {font} for your Windows account?\n\nWord needs it installed to display the result. The font is not embedded or uploaded. Use a font you have permission to install.', font=face.full_name), parent=self):
                return
            face = install_for_current_user(Path(selected))
            self.app.faces.append(face)
            self.app.faces.sort(key=lambda f: f.label.casefold())
            self.search.set(face.full_name)
            self.refresh()
            for i, candidate in enumerate(self.visible):
                if candidate.path == face.path:
                    self.list.selection_set(i)
        except Exception as exc:
            messagebox.showerror(self.t('Font could not be added'), self.t(str(exc)), parent=self)

    def accept(self):
        selection = self.list.curselection()
        if not selection:
            return
        face = self.visible[selection[0]]
        missing = missing_glyphs(face, self.app.font_chars[self.source])
        if missing:
            messagebox.showerror(self.t('Missing characters'), self.t('Choose another font. Missing: {chars}', chars=repr(''.join(missing[:24]))), parent=self)
            return
        if family_conflicts(face, self.app.faces):
            messagebox.showwarning(self.t('Conflicting font versions'), self.t('Windows has multiple versions of {font}. Remove duplicate versions in Windows Fonts and rescan, or choose a different font family.', font=face.family), parent=self)
            return
        if match_status(self.app.infos, self.source, face) != 'verified' and not messagebox.askyesno(self.t('Use this replacement?'), self.t('An exact match for {source} could not be verified. Use {font} instead?\n\nLetter shapes and spacing may change. Review the converted pages.', source=self.source, font=font_label(face, self.app.language.get())), parent=self):
            return
        self.app.mapping[self.source] = face
        if not preferences.remember_font(self.source, face, self.app.infos):
            messagebox.showwarning(self.t('Font preference'), self.t('This font choice applies now, but could not be saved for next time.'), parent=self)
        self.app.refresh_fonts()
        self.app.refresh_files()
        self.destroy()


def launch():
    App().mainloop()
