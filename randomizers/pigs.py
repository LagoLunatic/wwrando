
from gclib import fs_helpers as fs

from randomizers.base_randomizer import BaseRandomizer

class PigsRandomizer(BaseRandomizer):
  captured_pigs_bitfield: int = 0x04
  
  def _randomize(self):
    # Randomize the color of the big pig on Outset by setting the bitfield of which pigs were captured in the prologue.
    self.captured_pigs_bitfield = self.rng.choice([
      0x01, # Pink only
      0x02, # Speckled only
      0x04, # Black only
    ])
  
  def _save(self):
    captured_prologue_pigs_bitfield_address = self.rando.main_custom_symbols["captured_prologue_pigs_bitfield"]
    self.rando.dol.write_data(fs.write_u8, captured_prologue_pigs_bitfield_address, self.captured_pigs_bitfield)
