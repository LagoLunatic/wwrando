
import urllib.request
import ssl
import certifi
import json
import traceback
from distutils.version import LooseVersion

from randomizer import VERSION

LATEST_RELEASE_DOWNLOAD_PAGE_URL = "https://github.com/LagoLunatic/wwrando/releases/latest"
LATEST_RELEASE_API_URL = "https://api.github.com/repos/lagolunatic/wwrando/releases/latest"

def check_for_updates():
  try:
    with urllib.request.urlopen(LATEST_RELEASE_API_URL, context=ssl.create_default_context(cafile=certifi.where())) as page:
      data = json.loads(page.read().decode())
      
      latest_version_name = data["tag_name"]
      if latest_version_name[0] == "v":
        latest_version_name = latest_version_name[1:]
      
      if "-BETA" in VERSION:
        version_without_beta = VERSION.split("-BETA")[0]
        if LooseVersion(latest_version_name) >= LooseVersion(version_without_beta):
          return latest_version_name
        else:
          return None
      else:
        if LooseVersion(latest_version_name) > LooseVersion(VERSION):
          return latest_version_name
        else:
          return None
  except Exception as e:
    stack_trace = traceback.format_exc()
    error_message = "Error when checking for updates:\n" + str(e) + "\n\n" + stack_trace
    print(error_message)
    return "error"
