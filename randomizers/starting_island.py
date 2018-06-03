
import tweaks

def randomize_starting_island(self):
  possible_starting_islands = list(range(1, 49+1))
  
  # Don't allow Forsaken Fortress to be the starting island.
  # It wouldn't really cause problems, but it would be weird because you normally need bombs to get in, and you would need to use Ballad of Gales to get out.
  possible_starting_islands.remove(1)
  
  starting_island_room_index = self.rng.choice(possible_starting_islands)
  tweaks.set_new_game_starting_room_index(self, starting_island_room_index)
  tweaks.change_ship_starting_island(self, starting_island_room_index)
  
  self.starting_island_index = starting_island_room_index
