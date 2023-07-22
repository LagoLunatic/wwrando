
import os
import re

from wwrando_paths import RANDO_ROOT_PATH, IS_RUNNING_FROM_SOURCE

with open(os.path.join(RANDO_ROOT_PATH, "version.txt"), "r") as f:
  VERSION = f.read().strip()

VERSION_WITHOUT_COMMIT = VERSION

# Try to add the git commit hash to the version number if running from source.
if IS_RUNNING_FROM_SOURCE:
  version_suffix = "_NOGIT"
  
  git_commit_head_file = os.path.join(RANDO_ROOT_PATH, ".git", "HEAD")
  if os.path.isfile(git_commit_head_file):
    with open(git_commit_head_file, "r") as f:
      head_file_contents = f.read().strip()
    if head_file_contents.startswith("ref: "):
      # Normal head, HEAD file has a reference to a branch which contains the commit hash
      relative_path_to_hash_file = head_file_contents[len("ref: "):]
      path_to_hash_file = os.path.join(RANDO_ROOT_PATH, ".git", relative_path_to_hash_file)
      path_to_info_refs = os.path.join(RANDO_ROOT_PATH, ".git", "info/refs")
      if os.path.isfile(path_to_hash_file):
        with open(path_to_hash_file, "r") as f:
          hash_file_contents = f.read()
        version_suffix = "_" + hash_file_contents[:7]
      elif os.path.isfile(path_to_info_refs):
        with open(path_to_info_refs, "r") as f:
          for line in f.readlines():
            ref_hash, ref_path = line.strip().split('\t', 1)
            if ref_path == relative_path_to_hash_file:
              version_suffix = "_" + ref_hash[:7]
              break
    elif re.search(r"^[0-9a-f]{40}$", head_file_contents):
      # Detached head, commit hash directly in the HEAD file
      version_suffix = "_" + head_file_contents[:7]
  
  VERSION += version_suffix
