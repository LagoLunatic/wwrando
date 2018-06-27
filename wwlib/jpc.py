
from io import BytesIO

from fs_helpers import *

from wwlib.bti import BTI

class JPC:
  def __init__(self, data):
    self.data = data
    
    self.magic = read_str(data, 0, 8)
    assert self.magic == "JPAC1-00"
    self.num_particles = read_u16(data, 8)
    self.num_textures = read_u16(data, 0xA)
    
    self.particles = []
    self.particles_by_id = {}
    offset = 0x20
    for particle_index in range(0, self.num_particles):
      particle = Particle(data, offset)
      self.particles.append(particle)
      self.particles_by_id[particle.particle_id] = particle
      
      offset += particle.size
    
    self.textures = []
    for texture_index in range(0, self.num_textures):
      texture = ParticleSection(data, offset)
      self.textures.append(texture)
      
      offset += texture.size

class Particle:
  def __init__(self, jpc_data, particle_offset):
    self.magic = read_str(jpc_data, particle_offset, 8)
    assert self.magic == "JEFFjpa1"
    
    self.unknown_1 = read_u32(jpc_data, particle_offset+8)
    self.num_sections = read_u32(jpc_data, particle_offset+0xC)
    self.size = read_u32(jpc_data, particle_offset+0x10)
    
    self.unknown_2 = read_u8(jpc_data, particle_offset+0x14)
    self.unknown_3 = read_u8(jpc_data, particle_offset+0x15)
    self.unknown_4 = read_u8(jpc_data, particle_offset+0x16)
    self.unknown_5 = read_u8(jpc_data, particle_offset+0x17)
    
    self.particle_id = read_u16(jpc_data, particle_offset+0x18)
    
    self.unknown_6 = read_bytes(jpc_data, particle_offset+0x1A, 6)
    
    self.sections = []
    section_offset = particle_offset + 0x20
    for section_index in range(0, self.num_sections):
      section = ParticleSection(jpc_data, section_offset)
      self.sections.append(section)
      
      if section.magic == "TDB1":
        self.tdb1 = section
      
      section_offset += section.size

class ParticleSection:
  def __init__(self, jpc_data, section_offset):
    self.magic = read_str(jpc_data, section_offset, 4)
    self.size = read_u32(jpc_data, section_offset+4)
    
    jpc_data.seek(section_offset)
    self.data = BytesIO(jpc_data.read(self.size))
    
    if self.magic == "TEX1":
      self.filename = read_str(self.data, 0xC, 0x14)
      
      bti_data = BytesIO(read_bytes(self.data, 0x20, self.size - 0x20))
      self.bti = BTI(bti_data)
    elif self.magic == "TDB1":
      # Texture ID database (list of texture IDs in this JPC file used by this particle)
      assert self.size == 0x20
      
      self.texture_ids = []
      for texture_id_index in range(0, 0xA):
        texture_id = read_u16(self.data, 0xC + texture_id_index*2)
        if texture_id == 0 and texture_id_index > 0:
          # Texture ID 0 is valid in the first slot, but after that it's just null bytes used for padding, so don't count those.
          break
        self.texture_ids.append(texture_id)
