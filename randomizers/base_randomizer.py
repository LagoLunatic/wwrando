from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
  from randomizer import WWRandomizer

class BaseRandomizer:
  """Base class for individual randomization features.
  
  Acts as an interface that allows randomizing a particular feature in a deterministic way
  independent of other features, while also allowing the randomized changes to be saved to the
  game's files and written to text file logs, or only written to logs but not the game's files.
  
  Subclasses should implement at least is_enabled, _randomize, and _save.
  They can also optionally implement write_to_non_spoiler_log and/or write_to_spoiler_log.
  """
  
  def __init__(self, rando: WWRandomizer):
    self.rando = rando
    self.logic = rando.logic
    self.options = rando.options
    self.rng = None
    self.made_any_changes = False
  
  def is_enabled(self) -> bool:
    raise NotImplementedError()
  
  @property
  def progress_randomize_duration_weight(self) -> int:
    """Gives a rough estimate of the duration that the randomization step will take relative to other randomizers.
    
    Can be approximately measured with: (time.perf_counter_ns() - start) // 1_000_000"""
    return 0
  
  @property
  def progress_save_duration_weight(self) -> int:
    """Gives a rough estimate of the duration that the save step will take relative to other randomizers.
    
    Can be approximately measured with: (time.perf_counter_ns() - start) // 1_000_000"""
    return 50
  
  @property
  def progress_randomize_text(self) -> str:
    """The message displayed to the user during the randomization step."""
    return "Randomizing..."
  
  @property
  def progress_save_text(self) -> str:
    """The message displayed to the user during the save step."""
    return "Applying changes..."
  
  def reset_rng(self):
    self.rng = self.rando.get_new_rng()
  
  def randomize(self):
    self.reset_rng()
    self._randomize()
    self.rng = None
    self.made_any_changes = True
  
  def _randomize(self):
    """Decide on what specific randomizations to make on this seed and store the results in instance
    variables for later use.
    
    Should not read from or write to any of the game's files."""
    raise NotImplementedError()
  
  def save(self):
    if self.made_any_changes:
      self._save()
  
  def _save(self):
    """Deterministically store the random decisions made by _randomize to the game's files.
    
    Should not make use of any RNG calls."""
    raise NotImplementedError()
  
  def write_to_non_spoiler_log(self) -> str:
    """Return a string based on the chosen options to be added to the non-spoiler log."""
    return ""
  
  def write_to_spoiler_log(self) -> str:
    """Return a string describing _randomize's random decisions to be added to the spoiler log."""
    return ""
