
import struct

class InvalidOffsetError(Exception):
  pass

def read_bytes(data, offset, length, format_string):
  requested_data = data[offset:offset+length]
  unpacked_data = struct.unpack(format_string, requested_data)
  return unpacked_data

def read_str(data, offset, length):
  if offset+length > len(data):
    raise InvalidOffsetError("Offset %X, length %X is past the end of the data (length %X)." % (offset, length, len(data)))
  string = data[offset:offset+length].decode("ascii")
  string = string.rstrip("\0") # Remove trailing null bytes
  return string

def read_str_until_null_character(data, offset):
  if offset > len(data):
    raise InvalidOffsetError("Offset %X is past the end of the data (length %X)." % (offset, len(data)))
  str = ""
  while offset < len(data):
    char = data[offset:offset+1]
    if char == b"\0":
      break
    else:
      str += char.decode("ascii")
    offset += 1
  return str

def read_u8(data, offset):
  return struct.unpack(">B", data[offset:offset+1])[0]

def read_u16(data, offset):
  return struct.unpack(">H", data[offset:offset+2])[0]

def read_u32(data, offset):
  return struct.unpack(">I", data[offset:offset+4])[0]

def read_s8(data, offset):
  return struct.unpack(">b", data[offset:offset+1])[0]

def read_s16(data, offset):
  return struct.unpack(">h", data[offset:offset+2])[0]

def read_s32(data, offset):
  return struct.unpack(">i", data[offset:offset+4])[0]
