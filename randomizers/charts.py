
import copy

def randomize_charts(self):
  # Shuffles around which chart points to each sector.
  
  randomizable_charts = [chart for chart in self.chart_list.charts if chart.type in [0, 1, 2, 6]]
  
  original_charts = copy.deepcopy(randomizable_charts)
  # Sort the charts by their texture ID so we get the same results even if we randomize them multiple times.
  original_charts.sort(key=lambda chart: chart.texture_id)
  self.rng.shuffle(original_charts)
  
  for chart in randomizable_charts:
    chart_to_copy_from = original_charts.pop()
    
    chart.texture_id = chart_to_copy_from.texture_id
    chart.sector_x = chart_to_copy_from.sector_x
    chart.sector_y = chart_to_copy_from.sector_y
    
    for random_pos_index in range(4):
      possible_pos = chart.possible_random_positions[random_pos_index]
      possible_pos_to_copy_from = chart_to_copy_from.possible_random_positions[random_pos_index]
      
      possible_pos.chart_texture_x_offset = possible_pos_to_copy_from.chart_texture_x_offset
      possible_pos.chart_texture_y_offset = possible_pos_to_copy_from.chart_texture_y_offset
      possible_pos.salvage_x_pos = possible_pos_to_copy_from.salvage_x_pos
      possible_pos.salvage_y_pos = possible_pos_to_copy_from.salvage_y_pos
    
    chart.save_changes()
    
    # Then update the salvage object on the sea so it knows what chart corresponds to it now.
    dzx = self.get_arc("files/res/Stage/sea/Room%d.arc" % chart.island_number).get_file("room.dzr")
    for scob in dzx.entries_by_type("SCOB"):
      if scob.actor_class_name == "d_a_salvage" and scob.salvage_type == 0:
        scob.chart_index_plus_1 = chart.owned_chart_index_plus_1
        scob.save_changes()
    
    self.island_number_to_chart_name[chart_to_copy_from.island_number] = chart.item_name
  
  self.logic.update_chart_macros()
