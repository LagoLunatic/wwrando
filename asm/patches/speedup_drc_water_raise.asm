; The puzzle at DRC entrance where the pond fills up with water is very slow
; (~20s from the boulder breaking to the water reaching max level)
; This speeds it up by a factor of 5 by modifying the speeds of various animations
.open "files/rels/d_a_obj_gryw00.rel"

.org 0x10C4
.float -0.5263158, 0.5263158 ; Water spread speed
.org 0x10D4
.float 8.388704              ; Water rise speed


.org 0x0BA0 ; in daObjGryw00_c::switch_wait_act_proc
  lfs f0, 0x2C (r31)         ; change arg to mBtk/mBck.setPlaySpeed from 1.0f to 5.0f
.org 0x0BDC
  li r0, 62                  ; Shorten geyser sound effect length
.close