
from io import BytesIO
import os
import glob
from collections import OrderedDict

from fs_helpers import *

from gclib.bti import BTI
from gclib.j3d import J3DChunk

IMPLEMENTED_CHUNK_TYPES = [
  "BSP1",
  "SSP1",
  "TDB1",
  "TEX1",
]

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
    for particle_index in range(self.num_particles):
      particle = Particle(data, offset)
      self.particles.append(particle)
      
      if particle.particle_id in self.particles_by_id:
        raise Exception("Duplicate particle ID: %04X" % particle.particle_id)
      self.particles_by_id[particle.particle_id] = particle
      
      # The particle's size field is inaccurate in some rare cases.
      # So we instead add the size of the particle's header and each invididual chunk's size because those are accurate.
      offset += 0x20 # Particle header
      for chunk in particle.chunks:
        offset += chunk.size
    
    self.textures = []
    self.textures_by_filename = {}
    for texture_index in range(self.num_textures):
      chunk_magic = read_str(data, offset, 4)
      assert chunk_magic == "TEX1"
      texture = TEX1()
      texture.read(data, offset)
      self.textures.append(texture)
      
      if texture.filename in self.textures_by_filename:
        raise Exception("Duplicate texture filename: %s" % texture.filename)
      self.textures_by_filename[texture.filename] = texture
      
      offset += texture.size
    
    # Populate the particle TDB1 texture filename lists.
    for particle in self.particles:
      for texture_id in particle.tdb1.texture_ids:
        texture = self.textures[texture_id]
        particle.tdb1.texture_filenames.append(texture.filename)
  
  def add_particle(self, particle):
    if particle.particle_id in self.particles_by_id:
      raise Exception("Cannot add a particle with the same name as an existing one: %04X" % particle.particle_id)
    self.particles.append(particle)
    self.particles_by_id[particle.particle_id] = particle
  
  def replace_particle(self, particle):
    if particle.particle_id not in self.particles_by_id:
      raise Exception("Cannot replace a particle that does not already exist: %04X" % particle.particle_id)
    existing_particle = self.particles_by_id[particle.particle_id]
    particle_index = self.particles.index(existing_particle)
    self.particles[particle_index] = particle
    self.particles_by_id[particle.particle_id] = particle
  
  def add_texture(self, texture):
    if texture.filename in self.textures_by_filename:
      raise Exception("Cannot add a texture with the same name as an existing one: %s" % texture.filename)
    self.textures.append(texture)
    self.textures_by_filename[texture.filename] = texture
  
  def replace_texture(self, texture):
    if texture.filename not in self.textures_by_filename:
      raise Exception("Cannot replace a texture that does not already exist: %s" % texture.filename)
    existing_texture = self.textures_by_filename[texture.filename]
    texture_id = self.textures.index(existing_texture)
    self.textures[texture_id] = texture
    self.textures_by_filename[texture.filename] = texture
  
  def extract_all_particles_to_disk(self, output_directory):
    if not os.path.isdir(output_directory):
      os.mkdir(output_directory)
    
    for particle in self.particles:
      file_name = "%04X.jpa" % particle.particle_id
      particle_path = os.path.join(output_directory, file_name)
      with open(particle_path, "wb") as f:
        particle.data.seek(0)
        f.write(particle.data.read())
        
        for texture_id in particle.tdb1.texture_ids:
          texture = self.textures[texture_id]
          texture.data.seek(0)
          f.write(texture.data.read())
  
  def import_particles_from_disk(self, input_directory):
    all_jpa_file_paths = glob.glob(glob.escape(input_directory) + "/*.jpa")
    new_particles = []
    new_textures = []
    new_textures_for_particle_id = OrderedDict()
    for jpa_path in all_jpa_file_paths:
      # Read the particle itself.
      with open(jpa_path, "rb") as f:
        data = BytesIO(f.read())
      particle = Particle(data, 0)
      new_particles.append(particle)
      new_textures_for_particle_id[particle.particle_id] = []
      
      # Read the textures.
      offset = data_len(particle.data)
      while True:
        if offset == data_len(data):
          break
        texture = TEX1()
        texture.read(data, offset)
        new_textures.append(texture)
        new_textures_for_particle_id[particle.particle_id].append(texture)
        offset += texture.size
    
    num_particles_added = 0
    num_particles_overwritten = 0
    num_textures_added = 0
    num_textures_overwritten = 0
    
    for particle in new_particles:
      if particle.particle_id in self.particles_by_id:
        self.replace_particle(particle)
        num_particles_overwritten += 1
      else:
        num_particles_added += 1
        self.add_particle(particle)
      
      # Populate the particle's TDB1 texture filename list.
      particle.tdb1.texture_filenames = []
      for texture in new_textures_for_particle_id[particle.particle_id]:
        particle.tdb1.texture_filenames.append(texture.filename)
    
    for texture in new_textures:
      if texture.filename in self.textures_by_filename:
        self.replace_texture(texture)
        num_textures_overwritten += 1
      else:
        self.add_texture(texture)
        num_textures_added += 1
    
    return (num_particles_added, num_particles_overwritten, num_textures_added, num_textures_overwritten)
  
  def save_changes(self):
    self.num_particles = len(self.particles)
    self.num_textures = len(self.textures)
    write_magic_str(self.data, 0, self.magic, 8)
    write_u16(self.data, 8, self.num_particles)
    write_u16(self.data, 0xA, self.num_textures)
    
    # Cut off the particle list and texture list since we're replacing this data entirely.
    self.data.truncate(0x20)
    self.data.seek(0x20)
    
    for particle in self.particles:
      # First regenerate this particle's TDB1 texture ID list based off the filenames.
      particle.tdb1.texture_ids = []
      for texture_filename in particle.tdb1.texture_filenames:
        texture = self.textures_by_filename[texture_filename]
        texture_id = self.textures.index(texture)
        particle.tdb1.texture_ids.append(texture_id)
      
      particle.save_changes()
      
      particle.data.seek(0)
      particle_data = particle.data.read()
      self.data.write(particle_data)
    
    for texture in self.textures:
      texture.save_changes()
      
      texture.data.seek(0)
      texture_data = texture.data.read()
      self.data.write(texture_data)

class Particle:
  def __init__(self, jpc_data, particle_offset):
    self.magic = read_str(jpc_data, particle_offset, 8)
    assert self.magic == "JEFFjpa1"
    
    self.unknown_1 = read_u32(jpc_data, particle_offset+8)
    self.num_chunks = read_u32(jpc_data, particle_offset+0xC)
    self.size = read_u32(jpc_data, particle_offset+0x10) # Not accurate in some rare cases
    
    self.num_kfa1_chunks = read_u8(jpc_data, particle_offset+0x14)
    self.num_fld1_chunks = read_u8(jpc_data, particle_offset+0x15)
    self.num_textures = read_u8(jpc_data, particle_offset+0x16)
    self.unknown_5 = read_u8(jpc_data, particle_offset+0x17)
    
    self.particle_id = read_u16(jpc_data, particle_offset+0x18)
    
    self.unknown_6 = read_bytes(jpc_data, particle_offset+0x1A, 6)
    
    self.chunks = []
    self.chunk_by_type = {}
    chunk_offset = particle_offset + 0x20
    for chunk_index in range(0, self.num_chunks):
      chunk_magic = read_str(jpc_data, chunk_offset, 4)
      if chunk_magic in IMPLEMENTED_CHUNK_TYPES:
        chunk_class = globals().get(chunk_magic, None)
      else:
        chunk_class = J3DChunk
      chunk = chunk_class()
      chunk.read(jpc_data, chunk_offset)
      self.chunks.append(chunk)
      self.chunk_by_type[chunk.magic] = chunk
      
      if chunk.magic in IMPLEMENTED_CHUNK_TYPES:
        setattr(self, chunk.magic.lower(), chunk)
      
      chunk_offset += chunk.size
    
    self.tdb1.read_texture_ids(self.num_textures)
    
    true_size = (chunk_offset - particle_offset)
    jpc_data.seek(particle_offset)
    self.data = BytesIO(jpc_data.read(true_size))
  
  def save_changes(self):
    # Cut off the chunk data first since we're replacing this data entirely.
    self.data.truncate(0x20)
    self.data.seek(0x20)
    
    self.num_textures = len(self.tdb1.texture_ids)
    
    for chunk in self.chunks:
      chunk.save_changes()
      
      chunk.data.seek(0)
      chunk_data = chunk.data.read()
      self.data.write(chunk_data)
    
    # We don't recalculate this size field, since this is inaccurate anyway. It's probably not even used.
    #self.size = data_len(self.data)
    
    write_magic_str(self.data, 0, self.magic, 8)
    write_u32(self.data, 0x10, self.size)

class BSP1(J3DChunk):
  def read_chunk_specific_data(self):
    self.color_flags = read_u8(self.data, 0xC + 0x1B)
    
    r = read_u8(self.data, 0xC + 0x20)
    g = read_u8(self.data, 0xC + 0x21)
    b = read_u8(self.data, 0xC + 0x22)
    a = read_u8(self.data, 0xC + 0x23)
    self.color_prm = (r, g, b, a)
    r = read_u8(self.data, 0xC + 0x24)
    g = read_u8(self.data, 0xC + 0x25)
    b = read_u8(self.data, 0xC + 0x26)
    a = read_u8(self.data, 0xC + 0x27)
    self.color_env = (r, g, b, a)
    
    self.color_prm_anm_data_count = 0
    self.color_prm_anm_table = []
    if self.color_flags & 0x02 != 0:
      self.color_prm_anm_data_offset = read_u16(self.data, 0xC + 0x4)
      self.color_prm_anm_data_count = read_u8(self.data, 0xC + 0x1C)
      self.color_prm_anm_table = self.read_color_table(self.color_prm_anm_data_offset, self.color_prm_anm_data_count)
    
    self.color_env_anm_data_count = 0
    self.color_env_anm_table = []
    if self.color_flags & 0x08 != 0:
      self.color_env_anm_data_offset = read_u16(self.data, 0xC + 0x6)
      self.color_env_anm_data_count = read_u8(self.data, 0xC + 0x1D)
      self.color_env_anm_table = self.read_color_table(self.color_env_anm_data_offset, self.color_env_anm_data_count)
  
  def save_chunk_specific_data(self):
    write_u8(self.data, 0xC + 0x1B, self.color_flags)
    
    r, g, b, a = self.color_prm
    write_u8(self.data, 0xC + 0x20, r)
    write_u8(self.data, 0xC + 0x21, g)
    write_u8(self.data, 0xC + 0x22, b)
    write_u8(self.data, 0xC + 0x23, a)
    r, g, b, a = self.color_env
    write_u8(self.data, 0xC + 0x24, r)
    write_u8(self.data, 0xC + 0x25, g)
    write_u8(self.data, 0xC + 0x26, b)
    write_u8(self.data, 0xC + 0x27, a)
    
    if self.color_flags & 0x02 != 0:
      # Changing size not implemented.
      assert len(self.color_prm_anm_table) == self.color_prm_anm_data_count
      self.save_color_table(self.color_prm_anm_table, self.color_prm_anm_data_offset)
    
    if self.color_flags & 0x08 != 0:
      # Changing size not implemented.
      assert len(self.color_env_anm_table) == self.color_env_anm_data_count
      self.save_color_table(self.color_env_anm_table, self.color_env_anm_data_offset)
  
  def read_color_table(self, color_data_offset, color_data_count):
    color_table = []
    for i in range(color_data_count):
      keyframe_time = read_u16(self.data, color_data_offset+i*6 + 0)
      r = read_u8(self.data, color_data_offset+i*6 + 2)
      g = read_u8(self.data, color_data_offset+i*6 + 3)
      b = read_u8(self.data, color_data_offset+i*6 + 4)
      a = read_u8(self.data, color_data_offset+i*6 + 5)
      color_table.append(ColorAnimationKeyframe(keyframe_time, (r, g, b, a)))
    
    return color_table
  
  def save_color_table(self, color_table, color_data_offset):
    for i, keyframe in enumerate(color_table):
      r, g, b, a = keyframe.color
      write_u16(self.data, color_data_offset+i*6 + 0, keyframe.time)
      write_u8(self.data, color_data_offset+i*6 + 2, r)
      write_u8(self.data, color_data_offset+i*6 + 3, g)
      write_u8(self.data, color_data_offset+i*6 + 4, b)
      write_u8(self.data, color_data_offset+i*6 + 5, a)

class SSP1(J3DChunk):
  def read_chunk_specific_data(self):
    r = read_u8(self.data, 0xC + 0x3C)
    g = read_u8(self.data, 0xC + 0x3D)
    b = read_u8(self.data, 0xC + 0x3E)
    a = read_u8(self.data, 0xC + 0x3F)
    self.color_prm = (r, g, b, a)
    r = read_u8(self.data, 0xC + 0x40)
    g = read_u8(self.data, 0xC + 0x41)
    b = read_u8(self.data, 0xC + 0x42)
    a = read_u8(self.data, 0xC + 0x43)
    self.color_env = (r, g, b, a)
  
  def save_chunk_specific_data(self):
    r, g, b, a = self.color_prm
    write_u8(self.data, 0xC + 0x3C, r)
    write_u8(self.data, 0xC + 0x3D, g)
    write_u8(self.data, 0xC + 0x3E, b)
    write_u8(self.data, 0xC + 0x3F, a)
    r, g, b, a = self.color_env
    write_u8(self.data, 0xC + 0x40, r)
    write_u8(self.data, 0xC + 0x41, g)
    write_u8(self.data, 0xC + 0x42, b)
    write_u8(self.data, 0xC + 0x43, a)
  
class TDB1(J3DChunk):
  # Texture ID database (list of texture IDs in this JPC file used by this particle)
  
  def read_chunk_specific_data(self):
    self.texture_ids = None # Can't read these yet, we need the number of textures from the particle header.
    self.texture_filenames = [] # Leave this list empty for now, it will be populated after the texture list is read.
  
  def read_texture_ids(self, num_texture_ids):
    self.texture_ids = []
    for texture_id_index in range(num_texture_ids):
      texture_id = read_u16(self.data, 0xC + texture_id_index*2)
      self.texture_ids.append(texture_id)
  
  def save_chunk_specific_data(self):
    # Save the texture IDs (which were updated by the JPC's save_changes function).
    for texture_id_index, texture_id in enumerate(self.texture_ids):
      write_u16(self.data, 0xC + texture_id_index*2, texture_id)

class TEX1(J3DChunk):
  def read_chunk_specific_data(self):
    # This string is 0x14 bytes long, but sometimes there are random garbage bytes after the null byte.
    self.filename = read_str_until_null_character(self.data, 0xC)
    
    bti_data = BytesIO(read_bytes(self.data, 0x20, self.size - 0x20))
    self.bti = BTI(bti_data)
  
  def save_chunk_specific_data(self):
    self.data.seek(0x20)
    self.bti.save_header_changes()
    header_bytes = read_bytes(self.bti.data, self.bti.header_offset, 0x20)
    self.data.write(header_bytes)
    
    self.bti.image_data.seek(0)
    self.data.write(self.bti.image_data.read())
    
    if self.bti.needs_palettes():
      self.bti.palette_data.seek(0)
      self.data.write(self.bti.palette_data.read())

class ColorAnimationKeyframe:
  def __init__(self, time, color):
    self.time = time
    self.color = color
