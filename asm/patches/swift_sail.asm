
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

.close
