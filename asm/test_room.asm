
.open "sys/main.dol"
.org 0x8022CF78 ; In dvdWaitDraw
  ; This code runs after the Nintendo and Dolby logos are done being shown.
  ; Normally it would switch to the title screen after 31 things finish loading in.
  ; We want to first load a save file, then switch to the ingame state after those 31 things finish loading.
  ; In order to make room for our new code, we first shorten the vanilla code that checks those things.
  ; The first 30 of them are sequential so we just change that into a loop.
  ; Then the 31st one we check the same as normal.
  
  mr r4, r13
  subi r4, r4, 0x6EC0 ; Put the address of the first thing to check (803F7220) in r4
  li r0, 30 ; Number of sequential things to check
  mtctr r0
  
  dvdWaitDraw_loop_start:
  lwz r3, 0 (r4)
  lbz r0, 0xC(r3)
  cmpwi r0, 0
  beq 0x8022D174 ; This thing hasn't finished loading yet, so don't switch the game state yet
  addi r4, r4, 4
  bdnz dvdWaitDraw_loop_start
  
  ; Check the 31st thing
  lwz r3, -0x7778 (r13)
  lwz r0, 0(r3)
  cmpwi r0, 0
  bne 0x8022D174
  
  
  ; Now we want to load the save file, but the issue is that this code gets runs 28 times or so, and we only want it run once.
  ; So we check the max HP in the loaded save file. If it's 0, the save file has not been initialized, so run the custom code.
  ; If it's not 0, this code has already run, so just skip to the end of the function.
  lis r3, 0x803C4C08@ha
  addi r3, r3, 0x803C4C08@l
  lha r4, 0 (r3) ; Read max HP
  cmpwi r4, 0
  bne 0x8022D174
  
  
  ; Load the save data into memory
  lis r3, 0x803B39A0@ha
  addi r3, r3, 0x803B39A0@l
  bl restore__15mDoMemCd_Ctrl_cFv
  
  ; Load a specific save file
  li r3, 0 ; This arg isn't read, doesn't matter what we put in it
  lis r4, 0x803B39A0@ha
  addi r4, r4, 0x803B39A0@l
  li r5, 0 ; Save file 0
  bl card_to_memory__10dSv_info_cFPci
  
  lis r3, 0x803C4C08@ha
  addi r3, r3, 0x803C4C08@l
  lha r4, 0 (r3) ; Read max HP
  cmpwi r4, 0
  bne dvdWaitDraw_after_save_init
  ; If max HP is zero this must be an uninitialized save file, so initialize it to avoid the player dying on load.
  bl init__10dSv_info_cFv
  dvdWaitDraw_after_save_init:
  
  ; Change the game state to ingame after the boot up logos are done being shown
  mr r3, r31
  li r4, 7
  bl dComIfG_changeOpeningScene__FP11scene_classs
  
  ; Finally jump to the end part of the function.
  ; This is needed since we created so much free space with that loop that there's a hundred lines of now-unused code left here.
  b 0x8022D174
  
  ; And in the remaining free space, we put the stage name to load into.
  ; In vanilla the stage name for the title screen, "sea_T", was at 8034F5A1.
  ; That space is only 5 charcacters long though, and some stage names are as long as 7 characters.
  .global test_room_stage_name
  test_room_stage_name:
  .space 8, 0x00

.org 0x800531D4
  ; Update the hardcoded pointer to the stage name
  lis r3, test_room_stage_name@ha
  addi r3, r3, test_room_stage_name@l
  nop

.org 0x80053290 ; In dComIfG_resetToOpening
  ; Change the game state to ingame when the player resets the game
  li r4, 7

; Set the default values for where the player will be loaded in.
.org test_room_stage_name
  ; Stage name
  .string "sea"
.org 0x800531E3
  ; Spawn ID
  .global test_room_spawn_id
  test_room_spawn_id:
  .byte 0
.org 0x800531E7
  ; Room index
  .global test_room_room_index
  test_room_room_index:
  .byte 44
.org 0x800531EB
  ; Override layer number (or 0xFF for no override)
  .global test_room_override_layer_num
  test_room_override_layer_num:
  .byte 0xFF
.close
