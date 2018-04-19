
import os
from io import BytesIO

from fs_helpers import *

class ChartList:
  def __init__(self, file_entry):
    self.file_entry = file_entry
    self.file_entry.decompress_data_if_necessary()
    data = self.file_entry.data
    
    self.num_charts = read_u32(data, 0)
    
    self.charts = []
    offset = 4
    for chart_index in range(self.num_charts):
      chart = Chart(self.file_entry, offset)
      self.charts.append(chart)
      offset += Chart.DATA_SIZE
  
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
    
    self.texture_id = read_u8(data, self.offset)
    self.owned_chart_index_plus_1 = read_u8(data, self.offset+1)
    self.number = read_u8(data, self.offset+2)
    self.type = read_u8(data, self.offset+3)
    
    self.sector_x = read_s8(data, self.offset+4)
    self.sector_y = read_s8(data, self.offset+5)
    
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
    assert 1 <= island_number <= 49
    island_index = island_number - 1
    self.sector_x = (island_index % 7) - 3
    self.sector_y = (island_index // 7) - 3
  
  def save_changes(self):
    data = self.file_entry.data
    
    write_u8(data, self.offset, self.texture_id)
    write_u8(data, self.offset+1, self.owned_chart_index_plus_1)
    write_u8(data, self.offset+2, self.number)
    write_u8(data, self.offset+3, self.type)
    
    write_s8(data, self.offset+4, self.sector_x)
    write_s8(data, self.offset+5, self.sector_y)
    
    for possible_pos in self.possible_random_positions:
      possible_pos.save_changes()

class ChartPossibleRandomPosition:
  DATA_SIZE = 8
  
  def __init__(self, file_entry, offset):
    self.file_entry = file_entry
    data = self.file_entry.data
    self.offset = offset
    
    self.chart_texture_x_offset = read_u16(data, offset)
    self.chart_texture_y_offset = read_u16(data, offset+2)
    self.salvage_x_pos = read_u16(data, offset+4)
    self.salvage_y_pos = read_u16(data, offset+6)
  
  def save_changes(self):
    data = self.file_entry.data
    
    write_u16(data, self.offset, self.chart_texture_x_offset)
    write_u16(data, self.offset+2, self.chart_texture_y_offset)
    write_u16(data, self.offset+4, self.salvage_x_pos)
    write_u16(data, self.offset+6, self.salvage_y_pos)
