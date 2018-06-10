# -*- mode: python -*-

block_cipher = None


a = Analysis(['wwrando.py'],
             pathex=[],
             binaries=[],
             datas=[
               ('asm/*.txt', 'asm'),
               ('assets/*.*', 'assets'),
               ('data/*.txt', 'data'),
               ('logic/*.txt', 'logic'),
               ('seedgen/*.txt', 'seedgen'),
             ],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='Wind Waker Randomizer 0.6.0',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True,
          icon="assets/icon.ico" )
