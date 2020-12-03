# -*- mode: python -*-
a = Analysis(['..\\cli.py'],
             pathex=['C:\\furion\\pyinstaller'],
             hiddenimports=[],
             hookspath=None)
a.datas += [('furion.ico', '.\\furion.ico', 'DATA')]
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name=os.path.join('dist', 'furion-cli.exe'),
          debug=False,
          strip=None,
          upx=True,
          console=True , icon='furion.ico')
app = BUNDLE(exe,
             name=os.path.join('dist', 'furion-cli.exe.app'))
