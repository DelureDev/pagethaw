# One dependency analysis feeds both formats, so they have the same runtime.
import sys
sys.path.insert(0, SPECPATH)
from build_portable import ROOT, VERSION, EXCLUDES
from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('docx') + [
    (str(ROOT/'src/pagethaw/word_worker.ps1'), 'pagethaw'),
    (str(ROOT/'src/pagethaw/stop_owned_word.ps1'), 'pagethaw'),
    (str(ROOT/'build'/VERSION/'notices'), 'pagethaw_notices'),
]
a = Analysis([str(ROOT/'scripts/launch.py')], pathex=[str(ROOT/'src')],
             binaries=[], datas=datas, hiddenimports=[], hookspath=[],
             runtime_hooks=[], excludes=list(EXCLUDES), noarchive=False)
pyz = PYZ(a.pure)
folder_exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='PageThaw',
                 debug=False, strip=False, upx=False, console=False)
folder = COLLECT(folder_exe, a.binaries, a.datas, strip=False, upx=False, name='PageThaw')
single_exe = EXE(pyz, a.scripts, a.binaries, a.datas, [],
                 name=f'PageThaw-{VERSION}-windows-x64', debug=False,
                 strip=False, upx=False, console=False)
