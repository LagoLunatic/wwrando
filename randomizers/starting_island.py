
from randomizers.base_randomizer import BaseRandomizer
import tweaks

class StartingIslandRandomizer(BaseRandomizer):
  def __init__(self, rando):
    super().__init__(rando)
    
    # Default starting island (Outset Island) if the starting island randomizer is not on.
    self.room_number = 44
  
  def is_enabled(self) -> bool:
    return bool(self.options.get("randomize_starting_island"))
  
  def _randomize(self):
    possible_starting_islands = list(range(1, 49+1))
    
    # Don't allow Forsaken Fortress to be the starting island.
    # It wouldn't really cause problems, but it would be weird because you normally need bombs to get in, and you would need to use Ballad of Gales to get out.
    possible_starting_islands.remove(1)
    
    self.room_number = self.rng.choice(possible_starting_islands)
  
  def _save(self):
    tweaks.set_new_game_starting_spawn_id(self.rando, 0)
    tweaks.set_new_game_starting_room(self.rando, self.room_number)
    tweaks.change_ship_starting_island(self.rando, self.room_number)
  
  def write_to_spoiler_log(self) -> str:
    spoiler_log = "Starting island: "
    spoiler_log += self.rando.island_number_to_name[self.room_number]
    spoiler_log += "\n"
    
    spoiler_log += "\n\n\n"
    
    return spoiler_log
