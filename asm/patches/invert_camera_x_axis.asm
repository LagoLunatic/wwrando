
; Inverts camera horizontal movement.
.open "sys/main.dol"
.org 0x80162488 ; In updatePad__9dCamera_cFv
  b invert_camera_horizontal_axis
.close
