
.open "files/rels/d_a_ship.rel"
; Increase deceleration when the player holds A to stop the ship.
.org 0x1068C ; Relocation for line 0x3A74
  .int slow_down_ship_when_stopping
; Increase deceleration when the player is knocked out of the ship while it's moving.
.org 0x106B4 ; Relocation for line 0x3BC8
  .int slow_down_ship_when_idle
.close
