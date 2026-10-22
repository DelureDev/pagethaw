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
from .i18n import translate, font_label, load_language, save_language


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.language = tk.StringVar(value=load_language())
        self.title(self.t('PageThaw — PDF to Word'))
        self.geometry(f'880x{min(600, self.winfo_screenheight()-80)}')
        self.minsize(780, 500)
        self.configure(background='#f1f5f9')
        self.paths = []
        self.infos = []
        self.faces = []
        self.mapping = {}
        self.font_chars = {}
        self.file_results = {}
        self.fonts_expanded = False
        self.options_expanded = False
        self.last_conversion = None
        self.busy = False
        self.cancel = threading.Event()
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.events = queue.Queue()
        self.output = tk.StringVar()
        self.status = tk.StringVar()
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
        self.font_toggle = self.button(toolbar, 'Fonts…', self.toggle_fonts)
        self.font_toggle.pack(side='right')
        files = ttk.Frame(wrap)
        files.grid(row=3, column=0, sticky='ew')
        self.file_tree = self.tree(files, ('pages', 'status'), ('Pages', 'Status'), height=4)
        self.file_tree.heading('#0', text=self.t('PDF file'))
        self.file_tree.column('#0', width=330)
        self.file_tree.column('pages', width=75, stretch=False)
        self.file_tree.column('status', width=350)
        self.font_frame = ttk.Frame(wrap, padding=(0, 10, 0, 5))
        self.font_frame.grid(row=4, column=0, sticky='ew')
        font_row = ttk.Frame(self.font_frame)
        font_row.pack(fill='x', pady=(0, 6))
        self.button(font_row, 'Choose font…', self.choose_font).pack(side='left')
        self.button(font_row, 'Scan files & fonts', self.scan).pack(side='right')
        self.font_tree = self.tree(self.font_frame, ('target', 'status'), ('Word font', 'Match'), height=3)
        self.font_tree.heading('#0', text=self.t('Font used in PDF'))
        self.font_tree.column('#0', width=240)
        self.font_tree.column('target', width=270)
        self.font_tree.column('status', width=240)
        self.font_tree.bind('<Double-1>', lambda _: self.choose_font())
        if not self.fonts_expanded:
            self.font_frame.grid_remove()
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
        self.button(actions, 'Options…', self.toggle_options).pack(side='right')
        self.options_frame = ttk.Frame(wrap, padding=(0, 12, 0, 0))
        self.options_frame.grid(row=8, column=0, sticky='ew')
        ttk.Checkbutton(self.options_frame, text=self.t('Turn standalone underscore blanks into lines'), variable=self.rules).pack(anchor='w')
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

    def toggle_fonts(self):
        self.fonts_expanded = not self.fonts_expanded
        self.font_frame.grid() if self.fonts_expanded else self.font_frame.grid_remove()
        self.fit_panels()

    def toggle_options(self):
        self.options_expanded = not self.options_expanded
        self.options_frame.grid() if self.options_expanded else self.options_frame.grid_remove()
        self.fit_panels()

    def fit_panels(self):
        # Keep the convert controls visible when optional details are expanded.
        height = min(600 + 175*self.fonts_expanded + 95*self.options_expanded,
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
            self.file_tree.insert('', 'end', iid=str(n), text=path.name,
                values=(info.pages if info else '—', self.t(status)))

    def remove_files(self):
        chosen = {int(n) for n in self.file_tree.selection()}
        self.paths = [p for n, p in enumerate(self.paths) if n not in chosen]
        self.infos = []
        self.file_results.clear()
        self.mapping.clear()
        self.font_chars.clear()
        self.faces = []
        self.font_tree.delete(*self.font_tree.get_children())
        self.refresh_files()
        if self.paths:
            self.scan()

    def scan(self):
        if not self.paths:
            messagebox.showinfo(self.t('Choose PDFs'), self.t('Add one or more PDFs first.'))
            return
        paths = list(self.paths)
        self.run_job(lambda: ([inspect_pdf(p) for p in paths], installed_fonts()), self.scanned, 'Scanning PDFs and installed font faces…')

    def scanned(self, value):
        self.infos, self.faces = value
        self.file_results.clear()
        self.mapping.clear()
        self.font_chars = {}
        for info in self.infos:
            if not info.error:
                for name, chars in info.fonts.items():
                    self.font_chars[name] = self.font_chars.get(name, '')+chars
        for name, chars in self.font_chars.items():
            matches = [f for f in self.faces if f.matches(name) and not missing_glyphs(f, chars)]
            # Ambiguous faces/versions require an explicit choice as well.
            if len(matches) == 1:
                self.mapping[name] = matches[0]
        self.refresh_files()
        self.refresh_fonts()
        if set(self.font_chars)-self.mapping.keys() and not self.fonts_expanded:
            self.toggle_fonts()
        missing = len(self.font_chars)-len(self.mapping)
        self.set_status('Scan complete. {missing} font choice(s) needed; {unsupported} unsupported file(s).', missing=missing, unsupported=sum(bool(i.error) for i in self.infos))

    def refresh_fonts(self):
        self.font_tree.delete(*self.font_tree.get_children())
        for name in sorted(self.font_chars):
            face = self.mapping.get(name)
            self.font_tree.insert('', 'end', iid=name, text=name, values=(font_label(face, self.language.get()) if face else self.t('Choose a font…'),
                (self.t('Identity match') if face.matches(name) else self.t('Replacement approved')) if face else self.t('Missing / ambiguous')))

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

    def convert(self):
        if not self.infos:
            messagebox.showinfo(self.t('Scan first'), self.t('Scan files & fonts before converting.'))
            return
        missing = set(self.font_chars)-self.mapping.keys()
        if missing:
            messagebox.showwarning(self.t('Fonts need your choice'), self.t('Choose a font for: {fonts}', fonts=', '.join(sorted(missing))))
            return
        if not self.output.get().strip():
            self.choose_output()
            return
        infos, mapping = list(self.infos), dict(self.mapping)
        output, rules, dpi = Path(self.output.get()).resolve(), self.rules.get(), int(self.dpi.get())
        def finished(records):
            self.last_conversion = (output, infos, records)
            self.converted(records)
        self.run_job(lambda: convert_batch(infos, output, mapping, rules=rules, dpi=dpi, cancel=self.cancel,
            progress=lambda n, total, r: self.events.put(('progress', f'{n}/{total}: {r["input"]} — {r["status"]}'))),
            finished, 'Converting locally…')

    def converted(self, records):
        passed = sum(r.get('content_check') == 'passed' for r in records)
        failed = sum(r['status'] == 'failed' for r in records)
        self.set_status('{passed} converted; {failed} failed; {cancelled} cancelled. Review the Word files.', passed=passed, failed=failed, cancelled=len(records)-passed-failed)
        self.file_results = {info.path: record for info, record in zip(self.infos, records)}
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
                    except Exception as exc:
                        self.set_status(str(exc))
                        messagebox.showerror('PageThaw', self.t(str(exc)))
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
        if not face.matches(self.source) and not messagebox.askyesno(self.t('Use this replacement?'), self.t('Replace {source} with {font}?\n\nLetter widths and spacing may change. Review the converted pages before using them.', source=self.source, font=font_label(face, self.app.language.get())), parent=self):
            return
        self.app.mapping[self.source] = face
        self.app.refresh_fonts()
        self.destroy()


def launch():
    App().mainloop()
