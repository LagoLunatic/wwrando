
; Inverts the X-Axis of the sea compass
.open "sys/main.dol"
.org 0x801FD37C ; In dMeter_compassGetOnProc
  nop ; remove neg instruction when calculating compass rotation from current angle
.close
