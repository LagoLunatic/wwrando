; Play the low health beep only if health is actually missing
; Specifically when starting with a maximum of 1 heart, there shouldn't be beeping at full health
.open "sys/main.dol"
.org 0x802A2FA0 ; in processHeartGaugeSound__11JAIZelBasicFv
  ; after the function setup, on checking for <0.5 heart
  check_half:
  cmpwi   r4, 2
  bgt     check_one
  li      r4, 210
  b       call_sestart
  nop
  nop
  nop
  nop
  nop
  nop
  nop
  nop
  nop
  
  check_one:
  cmpwi   r4, 4
  bgt     check_one_and_a_half
  li      r4, 209

  ; Ignore beep if max hearts == 1
  lis     r5, g_dComIfG_gameInfo@ha
  addi    r5, r5, g_dComIfG_gameInfo@l
  lhz     r6, 0 (r5)
  cmpwi   r6, 8
  blt     after_sestart           ; Don't need to check 1.5 hearts since max is 1
  b       call_sestart
  nop
  nop
  nop
  nop

  check_one_and_a_half:
  cmpwi   r4,6
  bgt     after_sestart
  li      r4,208
  
  ; add a symbol to deduplicate the preamble and call to JAIZelBasic::seStart
  ; this gives us 9 additional instructions after each previous comparison to patch in logic
  call_sestart:
  li      r5, 0
  li      r6, 0
  li      r7, 0
  lfs     f1, -14560(r2)      ; 803FC420      @4002
  fmr     f2, f1
  lfs     f3, -14464(r2)      ; 803FC480      @4357
  fmr     f4, f3
  li      r8, 0
  bl      seStart__11JAIZelBasicFUlP3VecUlScffffUc          ; 802A6720    seStart__11JAIZelBasicFUlP3VecUlScffffUc
  ; resume function epilogue. Should align to 0x802A3038 (uncomment .global to check the offset if unsure)
  ;.global after_sestart
  after_sestart:
.close

