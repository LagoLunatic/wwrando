# -*- mode: python -*-

block_cipher = None

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

a = Analysis(['wwrando.py'],
             pathex=["./gclib", "./gclib/gclib"],
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
               'wwr_ui/*.ui',
             ]),
             hiddenimports=[
               "wwr_ui.cosmetic_tab",
             ],
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
