from enum import Enum

class GXAttr(Enum): 
  PositionMatrixIndex   = 0x00
  Tex0MatrixIndex       = 0x01
  Tex1MatrixIndex       = 0x02
  Tex2MatrixIndex       = 0x03
  Tex3MatrixIndex       = 0x04
  Tex4MatrixIndex       = 0x05
  Tex5MatrixIndex       = 0x06
  Tex6MatrixIndex       = 0x07
  Tex7MatrixIndex       = 0x08
  Position              = 0x09
  Normal                = 0x0A
  Color0                = 0x0B
  Color1                = 0x0C
  Tex0                  = 0x0D
  Tex1                  = 0x0E
  Tex2                  = 0x0F
  Tex3                  = 0x10
  Tex4                  = 0x11
  Tex5                  = 0x12
  Tex6                  = 0x13
  Tex7                  = 0x14
  PositionMatrixArray   = 0x15
  NormalMatrixArray     = 0x16
  TextureMatrixArray    = 0x17
  LitMatrixArray        = 0x18
  NormalBinormalTangent = 0x19
  NULL                  = 0xFF

class GXComponentCount(Enum):
  Position_XY  = 0x00
  Position_XYZ = 0x01

  Normal_XYZ  = 0x00
  Normal_NBT  = 0x01
  Normal_NBT3 = 0x02

  Color_RGB  = 0x00
  Color_RGBA = 0x01

  TexCoord_S  = 0x00
  TexCoord_ST = 0x01

class GXCompType(Enum):
  pass

class GXCompTypeNumber(GXCompType):
  Unsigned8  = 0x00
  Signed8    = 0x01
  Unsigned16 = 0x02
  Signed16   = 0x03
  Float32    = 0x04
  
class GXCompTypeColor(GXCompType):
  RGB565 = 0x00
  RGB8   = 0x01
  RGBX8  = 0x02
  RGBA4  = 0x03
  RGBA6  = 0x04
  RGBA8  = 0x05
