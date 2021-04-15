
.open "files/rels/d_a_ship.rel"

; Double the ship's sailing speed.
.org 0xDBE8
  .float 110.0 ; Sailing speed, 55.0 in vanilla
.org 0xDBC0
  .float 160.0 ; Initial speed, 80.0 in vanilla

; Make the wind always be at the players back as long as the sail is out.
.org 0xB9FC
  bl set_wind_dir_to_ship_dir

; Updates the current wind direction to match KoRL's direction.
.org @NextFreeSpace
.global set_wind_dir_to_ship_dir
set_wind_dir_to_ship_dir:
  stwu sp, -0x10 (sp)
  mflr r0
  stw r0, 0x14 (sp)
  
  ; First call setShipSailState since we overwrote a call to this in KoRL's code in order to call this custom function.
  bl setShipSailState__11JAIZelBasicFl
  
  lis r3,0x803CA75C@ha
  addi r3,r3,0x803CA75C@l
  lwz r3, 0 (r3) ; Read the pointer to KoRL's entity
  lha r3, 0x206 (r3) ; Read KoRL's Y rotation
  neg r3, r3 ; Negate his Y rotation since it's backwards
  addi r4, r3, 0x4000 ; Add 90 degrees to get the diretion KoRL is actually facing
  addi r4, r4, 0x1000 ; Add another 22.5 degrees in order to help round to the closest 45 degrees.
  rlwinm r4,r4,0,0,18 ; Now AND with 0xFFFFE000 in order to round down to the nearest 0x2000 (45 degrees). Because we added 22.5 degrees first, this accomplishes rounding either up or down to the nearest 45 degrees, whichever is closer.
  
  li r3, 0
  bl dKyw_tact_wind_set__Fss ; Pass the new angle as argument r4 to the function that changes wind direction
  
  lwz r0, 0x14 (sp)
  mtlr r0
  addi sp, sp, 0x10
  blr

; Increase deceleration when the player holds A to stop the ship.
.org 0x3A74
  bl slow_down_ship_when_stopping
.org @NextFreeSpace
.global slow_down_ship_when_stopping
slow_down_ship_when_stopping:
  stwu sp, -0x10 (sp)
  mflr r0
  stw r0, 0x14 (sp)
  
  lis r4, ship_stopping_deceleration@ha
  addi r4, r4, ship_stopping_deceleration@l
  lfs f3, 0 (r4) ; Max deceleration per frame
  lfs f4, 4 (r4) ; Min deceleration per frame
  
  bl cLib_addCalc__FPfffff
  
  lwz r0, 0x14 (sp)
  mtlr r0
  addi sp, sp, 0x10
  blr

.global ship_stopping_deceleration
ship_stopping_deceleration:
  .float 2.0 ; Max deceleration, 1.0 in vanilla
  .float 0.2 ; Min deceleration, 0.1 in vanilla

; Increase deceleration when the player is knocked out of the ship while it's moving.
.org 0x3BC8
  bl slow_down_ship_when_idle
.org @NextFreeSpace
.global slow_down_ship_when_idle
slow_down_ship_when_idle:
  stwu sp, -0x10 (sp)
  mflr r0
  stw r0, 0x14 (sp)
  
  lis r4, ship_idle_deceleration@ha
  addi r4, r4, ship_idle_deceleration@l
  lfs f3, 0 (r4) ; Max deceleration per frame
  lfs f4, 4 (r4) ; Min deceleration per frame
  
  bl cLib_addCalc__FPfffff
  
  lwz r0, 0x14 (sp)
  mtlr r0
  addi sp, sp, 0x10
  blr

.global ship_idle_deceleration
ship_idle_deceleration:
  .float 2.0 ; Max deceleration, 1.0 in vanilla
  .float 0.1 ; Min deceleration, 0.05 in vanilla

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
