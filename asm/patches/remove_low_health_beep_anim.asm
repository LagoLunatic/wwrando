; Play the low health beep only if health is actually missing
; Specifically when starting with a maximum of 1 heart, there shouldn't be beeping at full health
.open "sys/main.dol"
.org 0x802A2FA0, .area 0x98 ; in processHeartGaugeSound__11JAIZelBasicFv
  ; after the function setup, on checking for <0.5 heart
  processHeartGaugeSound__check_half:
  cmpwi   r4, 2
  bgt     processHeartGaugeSound__check_one
  li      r4, 0x00D2 ; JA_SE_ALMOST_DIE_ALERM_3
  b       processHeartGaugeSound__call_seStart
  
  processHeartGaugeSound__check_one:
  cmpwi   r4, 4
  bgt     processHeartGaugeSound__check_one_and_a_half
  li      r4, 0x00D1 ; JA_SE_ALMOST_DIE_ALERM_2

  ; Ignore beep if max hearts == 1
  lis     r5, g_dComIfG_gameInfo@ha
  addi    r5, r5, g_dComIfG_gameInfo@l
  lha     r6, 0 (r5) ; Load max health
  cmpwi   r6, 8
  blt     processHeartGaugeSound__after_seStart ; Don't need to check 1.5 hearts since max is 1
  b       processHeartGaugeSound__call_seStart

  processHeartGaugeSound__check_one_and_a_half:
  cmpwi   r4, 6
  bgt     processHeartGaugeSound__after_seStart
  li      r4, 0x00D0 ; JA_SE_ALMOST_DIE_ALERM_1
  
  ; add a symbol to deduplicate the preamble and call to JAIZelBasic::seStart
  ; this gives us 9 additional instructions after each previous comparison to patch in logic
  processHeartGaugeSound__call_seStart:
  li      r5, 0
  li      r6, 0
  li      r7, 0
  lfs     f1, -0x38E0 (r2)    ; 803FC420      @4002
  fmr     f2, f1
  lfs     f3, -0x3880 (r2)    ; 803FC480      @4357
  fmr     f4, f3
  li      r8, 0
  bl      seStart__11JAIZelBasicFUlP3VecUlScffffUc
  
  ; Skip over the rest of the area we didn't use and jump to the "field_0x0040--;" decrement right before the epilogue.
  processHeartGaugeSound__after_seStart:
  b 0x802A3038
.close


; Remove the low health animation at full health
.open "sys/main.dol"
.org 0x80111EE0 ; in daPy_lk_c::checkRestHPAnime
  ; After all checks, when ready to return, in the branch returning true
  b remove_low_health_anim_at_full_health
.org @NextFreeSpace
.global remove_low_health_anim_at_full_health
remove_low_health_anim_at_full_health:
  ; r3 contains function return value (1 when jumping here)
  ; r4 contains current health
  lis     r5, g_dComIfG_gameInfo@ha
  addi    r5, r5, g_dComIfG_gameInfo@l
  lha     r6, 0 (r5) ; Load max health
  rlwinm  r6, r6, 0, 0, 29 ; r6 &= ~0x3 (round max HP down to a full heart to exclude unfinished heart pieces)
  subfc   r6, r4, r6
  cmpwi   r6, 2 ; Check if 2 quarter hearts of health have been removed
  bge     remove_low_health_anim_at_full_health__return
  li      r3, 0
  remove_low_health_anim_at_full_health__return:
  ; resume function epilogue, jumping over the branch returning 0
  b 0x80111EE8
.close
