"""PyInstaller entry point with visible errors even in a windowed build."""
import sys
import traceback

from pagethaw.__main__ import main

try:
    raise SystemExit(main())
except Exception as exc:
    if sys.stderr:
        traceback.print_exc()
    else:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror('PageThaw', str(exc))
        root.destroy()
    raise SystemExit(1)
