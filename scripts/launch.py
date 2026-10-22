"""PyInstaller entry point with visible errors even in a windowed build."""
import sys
import traceback

from pagethaw.__main__ import main

try:
    raise SystemExit(main())
except Exception as exc:
    if '--self-test' in sys.argv:
        from pathlib import Path
        folder = Path(sys.argv[sys.argv.index('--self-test')+1])
        folder.mkdir(parents=True, exist_ok=True)
        (folder/'self-test-error.txt').write_text(traceback.format_exc(), encoding='utf-8')
    elif sys.stderr:
        traceback.print_exc()
    else:
        import tkinter as tk
        from tkinter import messagebox
        from pagethaw.i18n import load_language, translate
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror('PageThaw', translate(load_language(), str(exc)))
        root.destroy()
    raise SystemExit(1)
