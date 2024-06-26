import pytest
from pathlib import Path

def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]):
  for item in items:
    if Path(item.fspath).parts[-1] == "test_save.py":
      mark = pytest.mark.saving
      item.add_marker(mark)
