
.open "files/rels/d_a_ship.rel"

; Make the wind always be at the players back as long as the sail is out.
.org 0xB9FC
  bl set_wind_dir_to_ship_dir

; Increase deceleration when the player holds A to stop the ship.
.org 0x3A74
  bl slow_down_ship_when_stopping
; Increase deceleration when the player is knocked out of the ship while it's moving.
.org 0x3BC8
  bl slow_down_ship_when_idle

; Increase maximum cruising velocity.
.org 0x3A7C
  ; Read 30.0 from 0xDB44 instead of reading 10.0 from 0xDC54.
  lfs f1, 0x44 (r31)

; Increase ship acceleration when cruising.
; In daShip_c::decrementShipSpeed(float)
.org 0x2DD0
  ; Read 0.2 from 0xDCA4 instead of reading 0.1 from 0xDBEC.
  lfs f3, 0x1A4 (r4)
.org 0xDC28
  ; Change 0.015 to 0.03. This is read at 0x2DD4 and nowhere else so we can change it directly.
  .float 0.03
; In daShip_c::firstDecrementShipSpeed(float)
.org 0x2E18
  ; Read 10.0 from 0xDB08 instead of reading 5.0 from 0xDB80.
  lfs f3, 0x08 (r31)
.org 0x2E1C
  ; Read 2.0 from 0xDB24 instead of reading 1.0 from 0xDB88.
  lfs f4, 0x08 (r31)

.close
