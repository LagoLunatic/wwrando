
from gclib import fs_helpers as fs

class ChartList:
  def __init__(self, file_entry):
    self.file_entry = file_entry
    self.file_entry.decompress_data_if_necessary()
    data = self.file_entry.data
    
    self.num_charts = fs.read_u32(data, 0)
    
    self.charts = []
    offset = 4
    for chart_index in range(self.num_charts):
      chart = Chart(self.file_entry, offset)
      self.charts.append(chart)
      offset += Chart.DATA_SIZE
  
  def find_chart_by_chart_number(self, chart_number):
    return next(
      chart for chart in self.charts
      if chart.number == chart_number
    )
  
  def find_chart_for_island_number(self, island_number):
    return next(
      chart for chart in self.charts
      if chart.island_number == island_number
      and chart.type in [0, 1, 2, 6]
    )

class Chart:
  DATA_SIZE = 0x26
  
  def __init__(self, file_entry, offset):
    self.file_entry = file_entry
    data = self.file_entry.data
    self.offset = offset
    
    self.texture_id = fs.read_u8(data, self.offset)
    self.owned_chart_index_plus_1 = fs.read_u8(data, self.offset+1)
    self.number = fs.read_u8(data, self.offset+2)
    self.type = fs.read_u8(data, self.offset+3)
    
    self.sector_x = fs.read_s8(data, self.offset+4)
    self.sector_y = fs.read_s8(data, self.offset+5)
    
    offset = self.offset + 6
    self.possible_random_positions = []
    for random_pos_index in range(4):
      possible_pos = ChartPossibleRandomPosition(self.file_entry, offset)
      self.possible_random_positions.append(possible_pos)
      offset += ChartPossibleRandomPosition.DATA_SIZE
  
  @property
  def island_number(self):
    return self.sector_x+3 + (self.sector_y+3)*7 + 1
  
  @island_number.setter
  def island_number(self, value):
    assert 1 <= value <= 49
    island_index = value - 1
    self.sector_x = (island_index % 7) - 3
    self.sector_y = (island_index // 7) - 3
  
  @property
  def item_name(self):
    assert 1 <= self.number <= 49
    if self.number <= 8:
      return "Triforce Chart " + str(self.number)
    else:
      return "Treasure Chart " + str(self.number-8)
  
  def save_changes(self):
    data = self.file_entry.data
    
    fs.write_u8(data, self.offset, self.texture_id)
    fs.write_u8(data, self.offset+1, self.owned_chart_index_plus_1)
    fs.write_u8(data, self.offset+2, self.number)
    fs.write_u8(data, self.offset+3, self.type)
    
    fs.write_s8(data, self.offset+4, self.sector_x)
    fs.write_s8(data, self.offset+5, self.sector_y)
    
    for possible_pos in self.possible_random_positions:
      possible_pos.save_changes()

class ChartPossibleRandomPosition:
  DATA_SIZE = 8
  
  def __init__(self, file_entry, offset):
    self.file_entry = file_entry
    data = self.file_entry.data
    self.offset = offset
    
    self.chart_texture_x_offset = fs.read_u16(data, offset)
    self.chart_texture_y_offset = fs.read_u16(data, offset+2)
    self.salvage_x_pos = fs.read_u16(data, offset+4)
    self.salvage_y_pos = fs.read_u16(data, offset+6)
  
  def save_changes(self):
    data = self.file_entry.data
    
    fs.write_u16(data, self.offset, self.chart_texture_x_offset)
    fs.write_u16(data, self.offset+2, self.chart_texture_y_offset)
    fs.write_u16(data, self.offset+4, self.salvage_x_pos)
    fs.write_u16(data, self.offset+6, self.salvage_y_pos)
