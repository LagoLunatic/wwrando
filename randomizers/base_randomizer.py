
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING: from randomizer import WWRandomizer

class BaseRandomizer:
  def __init__(self, rando: WWRandomizer):
    self.rando = rando
    self.logic = rando.logic
    self.options = rando.options
    self.rng = None
    self.made_any_changes = False
  
  def reset_rng(self):
    self.rng = self.rando.get_new_rng()
  
  def randomize(self):
    self.reset_rng()
    self._randomize()
    self.made_any_changes = True
  
  def _randomize(self):
    raise NotImplementedError()
  
  def save(self):
    if self.made_any_changes:
      self._save()
  
  def _save(self):
    raise NotImplementedError()
  
  def write_to_spoiler_log(self) -> str:
    return ""
