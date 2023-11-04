# -*- mode: python -*-

with open("./keys/build_key.txt") as f:
  cipher_key = f.read().strip()

block_cipher = pyi_crypto.PyiBlockCipher(key=cipher_key)

with open("./version.txt") as f:
  randomizer_version = f.read().strip()

import os
import glob
def build_datas_recursive(paths):
  datas = []
  
  for path in paths:
    for filename in glob.iglob(path, recursive=True):
      dest_dirname = os.path.dirname(filename)
      if dest_dirname == "":
        dest_dirname = "."
      
      data_entry = (filename, dest_dirname)
      datas.append(data_entry)
      #print(data_entry)
  
  return datas

import sys
def get_hidden_imports():
  import_modules = []
  
  sys.path.insert(0, "./gclib")
  import gclib
  for module_name in gclib.__all__:
    import_modules.append(f"gclib.{module_name}")
  for module_name in gclib.j3d_chunks.__all__:
    import_modules.append(f"gclib.j3d_chunks.{module_name}")
  
  import wwlib
  for module_name in wwlib.__all__:
    import_modules.append(f"wwlib.{module_name}")
  
  return import_modules

a = Analysis(['wwrando.py'],
             pathex=[],
             binaries=[],
             datas=build_datas_recursive([
               'asm/*.txt',
               'asm/*.rel',
               'asm/*.plf',
               'asm/patch_diffs/*.txt',
               'assets/**/*.*',
               'data/*.txt',
               'logic/*.txt',
               'seedgen/*.txt',
               'version.txt',
             ]),
             hiddenimports=get_hidden_imports(),
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
          name='Wind Waker Randomizer',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False,
          icon="assets/icon.ico" )

app = BUNDLE(exe,
          name='Wind Waker Randomizer.app',
          icon="assets/icon.icns",
          bundle_identifier=None,
          info_plist={
              "LSBackgroundOnly": False,
              "CFBundleDisplayName": "Wind Waker Randomizer",
              "CFBundleName": "WW Randomizer", # 15 character maximum
              "CFBundleShortVersionString": randomizer_version,
          }
          )
