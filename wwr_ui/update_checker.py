
import urllib.request
import ssl
import certifi
import json
import traceback

from version import VERSION

LATEST_RELEASE_DOWNLOAD_PAGE_URL = "https://github.com/LagoLunatic/wwrando/releases/latest"
LATEST_RELEASE_API_URL = "https://api.github.com/repos/lagolunatic/wwrando/releases/latest"

def string_to_version(string: str):
  string = string.removeprefix('v')
  if "-BETA" in string:
    string = string.split("-BETA")[0]
  if "_" in string:
    string = string.split("_")[0]
  version = tuple(int(e) for e in string.split('.'))
  return version

def check_for_updates():
  try:
    with urllib.request.urlopen(LATEST_RELEASE_API_URL, context=ssl.create_default_context(cafile=certifi.where())) as page:
      data = json.loads(page.read().decode())
      
      curr_version = string_to_version(VERSION)
      latest_version = string_to_version(data["tag_name"])
      
      if "-BETA" in VERSION:
        print(latest_version >= curr_version)
        if latest_version >= curr_version:
          return '.'.join(str(e) for e in latest_version)
        else:
          return None
      else:
        if latest_version > curr_version:
          return '.'.join(str(e) for e in latest_version)
        else:
          return None
  except Exception as e:
    stack_trace = traceback.format_exc()
    error_message = "Error when checking for updates:\n" + str(e) + "\n\n" + stack_trace
    print(error_message)
    return "error"
