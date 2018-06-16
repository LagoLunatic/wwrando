# -*- mode: python -*-

block_cipher = None

with open("./version.txt") as f:
  randomizer_version = f.read().strip()

a = Analysis(['wwrando.py'],
             pathex=[],
             binaries=[],
             datas=[
               ('asm/*.txt', 'asm'),
               ('assets/*.*', 'assets'),
               ('data/*.txt', 'data'),
               ('logic/*.txt', 'logic'),
               ('seedgen/*.txt', 'seedgen'),
               ('version.txt', '.'),
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
          name='Wind Waker Randomizer ' + randomizer_version,
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False,
          icon="assets/icon.ico" )
