# -*- mode: python -*-
a = Analysis(['..\\furion.py'],
             pathex=['C:\\furion\\pyinstaller'],
             hiddenimports=[],
             hookspath=None)
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
          console=True , icon='furion.ico')
