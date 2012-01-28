# -*- mode: python -*-
a = Analysis([os.path.join(HOMEPATH,'support\\_mountzlib.py'), os.path.join(HOMEPATH,'support\\useUnicode.py'), '..\\furion.py'],
             pathex=['C:\\furion\\windows'])
pyz = PYZ(a.pure)
exe = EXE( pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name=os.path.join('dist', 'furion.exe'),
          debug=True,
          strip=False,
          upx=True,
          console=True , icon='furion.ico')
