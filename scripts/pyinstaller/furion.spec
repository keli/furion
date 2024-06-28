# -*- mode: python -*-
a = Analysis(['..\\..\\app.py'],
             pathex=['.'],
             hiddenimports=[],
             hookspath=None)
a.datas += [('furion.ico', '.\\furion.ico', 'DATA')]
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name=os.path.join('dist', 'furion.exe'),
          debug=False,
          strip=None,
          upx=True,
          console=False , icon='furion.ico')
app = BUNDLE(exe,
             name=os.path.join('dist', 'furion.exe.app'))
