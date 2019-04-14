
class PackedBitsWriter:
  def __init__(self):
    self.r = 8
    self.current_byte = 0;
    self.bytes = []
  
  # Writes a value `v` that is `l` bits long
  def write(self, v, l):
    while l:
      left = self.r if l >= self.r else l
      m = (1 << left) - 1
      self.current_byte |= (v & m) << (8 - self.r)
      self.r -= left
      l -= left
      v >>= left
      if self.r:
        continue
      self.flush()
  
  def flush(self):
    self.bytes.append(self.current_byte)
    self.current_byte = 0
    self.r = 8

class PackedBitsReader:
  def __init__(self, buf):
    self.bytes = buf
    self.current_byte = 0;
    self.idx = 0
  
  # Reads `s` bits
  def read(self, s):
    l = 0;
    v = 0;
    left = s
    while l != s:
      cons = 8 if left > 8 else left
      if (cons + self.idx > 8):
          cons = 8 - self.idx;
      m = ((1 << cons) - 1) << self.idx
      v = ((self.bytes[self.current_byte] & m) >> self.idx) << l | v
      self.idx += cons
      self.current_byte += self.idx >> 3
      self.idx %= 8
      left -= cons
      l += cons
    return v
