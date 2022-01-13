
; Inverts camera horizontal movement.
.open "sys/main.dol"
.org 0x80162488 ; In dCamera_c::updatePad(void)
  b invert_camera_horizontal_axis
; Read the C-stick's horizontal axis and negate the value in order to invert the camera's movement.
.org @NextFreeSpace
.global invert_camera_horizontal_axis
invert_camera_horizontal_axis:
  lfs f1, 0x10 (r3) ; Load the C-stick's horizontal axis for controlling the camera (same as the line we're replacing)
  fneg f1, f1 ; Negate the horizontal axis
  
  b 0x8016248C ; Return
.close
