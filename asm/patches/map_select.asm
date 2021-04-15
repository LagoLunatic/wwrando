
; Enter the debug map select game mode if the player is holding down a certain button combination at any point that Link is loaded.
.open "sys/main.dol"
.org 0x80234BF8 ; In dScnPly_Draw
  b check_open_map_select

; Checks if the player is holding down a certain button combination and opens map select if so.
; (Note: This function is coded specifically to avoid use of relative branches so that it can still function when converted to be a Gecko cheat code. This is why bctrl is used in place of bl and b.)
.org @NextFreeSpace
.global check_open_map_select
check_open_map_select:
  lis r3, mPadButton__10JUTGamePad@ha ; Bitfield of currently pressed buttons
  addi r3, r3, mPadButton__10JUTGamePad@l
  lwz r0, 0 (r3)
  li r3, 0x0814 ; Custom button combo. Y, Z, and D-pad down.
  and r0, r0, r3 ; AND to get which buttons in the combo are currently being pressed
  cmpw r0, r3 ; Check to make sure all of the buttons in the combo are pressed
  bne check_open_map_select_do_not_open
  
  ; Change the game state to map select.
  mr r3, r27
  li r4, 6 ; Map select game state
  li r5, 0 ; Fade to white
  li r6, 5
  lis r7, fopScnM_ChangeReq__FP11scene_classssUs@ha
  addi r7, r7, fopScnM_ChangeReq__FP11scene_classssUs@l
  mtctr r7
  bctrl
  
  ; Return to normal code (skipping the part where Link would trigger a stage transition/cutscene, since that would crash if it happened at the same time as map select opening)
  lis r3, 0x80234DE4@ha
  addi r3, r3, 0x80234DE4@l
  mtctr r3
  bctrl
  
  check_open_map_select_do_not_open:
  lha r0, 8 (r27) ; Replace a line of code we overwrote to jump here
  ; Return to normal code
  lis r3, 0x80234BFC@ha
  addi r3, r3, 0x80234BFC@l
  mtctr r3
  bctrl

.close
