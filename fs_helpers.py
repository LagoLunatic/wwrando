
import struct

class InvalidOffsetError(Exception):
  pass

def read_bytes(data, offset, length, format_string):
  data.seek(offset)
  requested_data = data.read(length)
  unpacked_data = struct.unpack(format_string, requested_data)
  return unpacked_data

def write_bytes(data, offset, raw_bytes):
  data.seek(offset)
  data.write(raw_bytes)


def read_str(data, offset, length):
  data_length = data.seek(0, 2)
  if offset+length > data_length:
    raise InvalidOffsetError("Offset %X, length %X is past the end of the data (length %X)." % (offset, length, data_length))
  data.seek(offset)
  string = data.read(length).decode("ascii")
  string = string.rstrip("\0") # Remove trailing null bytes
  return string

def try_read_str(data, offset, length):
  try:
    return read_str(data, offset, length)
  except UnicodeDecodeError:
    return None

def read_str_until_null_character(data, offset):
  data_length = data.seek(0, 2)
  if offset > data_length:
    raise InvalidOffsetError("Offset %X is past the end of the data (length %X)." % (offset, data_length))
  str = ""
  while offset < data_length:
    data.seek(offset)
    char = data.read(1)
    if char == b"\0":
      break
    else:
      str += char.decode("ascii")
    offset += 1
  return str

def write_str(data, offset, new_string, max_length):
  str_len = len(new_string)
  if str_len > max_length:
    raise Exception("String %s is too long (max length %X)" % (new_string, max_length))
  
  padding_length = max_length - str_len
  null_padding = b"\x00"*padding_length
  new_value = new_string.encode("ascii") + null_padding
  
  data.seek(offset)
  data.write(new_value)


def read_u8(data, offset):
  data.seek(offset)
  return struct.unpack(">B", data.read(1))[0]

def read_u16(data, offset):
  data.seek(offset)
  return struct.unpack(">H", data.read(2))[0]

def read_u32(data, offset):
  data.seek(offset)
  return struct.unpack(">I", data.read(4))[0]

def read_float(data, offset):
  data.seek(offset)
  return struct.unpack(">f", data.read(4))[0]


def read_s8(data, offset):
  data.seek(offset)
  return struct.unpack(">b", data.read(1))[0]

def read_s16(data, offset):
  data.seek(offset)
  return struct.unpack(">h", data.read(2))[0]

def read_s32(data, offset):
  data.seek(offset)
  return struct.unpack(">i", data.read(4))[0]


def write_u8(data, offset, new_value):
  new_value = struct.pack(">B", new_value)
  data.seek(offset)
  data.write(new_value)

def write_u16(data, offset, new_value):
  new_value = struct.pack(">H", new_value)
  data.seek(offset)
  data.write(new_value)

def write_u32(data, offset, new_value):
  new_value = struct.pack(">I", new_value)
  data.seek(offset)
  data.write(new_value)

def write_float(data, offset, new_value):
  new_value = struct.pack(">f", new_value)
  data.seek(offset)
  data.write(new_value)
