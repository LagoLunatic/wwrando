
; This patch modifies the code to support various features the randomizer has.


; 8005D618 is where the game calls the new game save init function.
; We replace this call with a call to our custom save init function.
.open "sys/main.dol"
.org 0x8005D618
  bl init_save_with_tweaks
.close




; Set initial HP from a custom symbol and also also allow the initial current HP to be rounded down from the initial max HP (for starting with some heart pieces).
.open "sys/main.dol"
.org 0x800589A8
  b set_starting_health
.close




; Fixes a bug related to changing starting health where blank save files on the file select screen would show the number of hearts the player started with on the ISO where the save file was deleted, instead of on the current ISO.
.open "sys/main.dol"
.org 0x80182504 ; In makeRecInfo
  b get_current_health_for_file_select_screen
.org 0x80182544 ; In makeRecInfo
  b get_max_health_for_file_select_screen
.close




; Refill the player's magic meter to full when they load a save.
.open "sys/main.dol"
.org 0x80231B08 ; In FileSelectMainNormal__10dScnName_cFv right after calling card_to_memory__10dSv_info_cFPci
  b fully_refill_magic_meter_on_load_save
.close




; Allow turning while swinging on ropes.
.open "sys/main.dol" ; In procRopeSwing__9daPy_lk_cFv
.org 0x80145648
  b turn_while_swinging
.close




; Animate the 500 rupee to be a rainbow rupee that animates between the colors of all other rupees.
.open "sys/main.dol"
.org 0x800F93F4
  b check_animate_rainbow_rupee_color
.close




; Checks if the upcoming message text to parse has a custom text command.
.open "sys/main.dol"
.org 0x80033E74
  b check_run_new_text_commands
.close




; Make cannons die in 1 hit from the boomerang instead of 2.
.open "files/rels/d_a_obj_canon.rel" ; Wall-mounted cannon
.org 0x7D0
  addi r0,r3,-2 ; Would normally subtract 1 HP, subtract 2 HP instead
.close




; Display the newly added message for the warp confirmation dialog when selecting a custom warp.
.open "sys/main.dol"
.org 0x801B80EC ; In wrapMove__12dMenu_Fmap_cFv
  b set_warp_confirm_dialog_message_id_for_custom_warps
; Also fix the text color commands to use the proper special colors for this new message.
; The engine hardcodes checks on the message IDs to know what messages should use the special colors.
; We add in a check for the new message, and then simplify the code for the vanilla messages by using a range check to shorten it so we don't need free space.
.org 0x80032590 ; In stringSet__21fopMsgM_msgDataProc_cFv
  cmplwi r0, 848 ; Custom message ID
  beq 0x800325E0 ; Use special colors
  cmplwi r0, 66
  blt 0x80032624 ; Do not use special colors
  cmplwi r0, 75
  bgt 0x80032624 ; Do not use special colors
  b 0x800325E0 ; Use special colors (for messages 66-75, the vanilla warp confirmation messages)
  nop
  nop
  nop
  nop
  nop
  nop
  nop
  nop
  nop
  nop
  nop
  nop
  nop
.close




; Properly force the player model to be either hero's clothes or casual clothes depending on what the user selected, and not whether they're on new game or new game+.
.open "sys/main.dol"
.org 0x80125AD8 ; In daPy_lk_c::playerInit(void)
  bl check_player_in_casual_clothes
  cmplwi r3, 0
  beq 0x80125B04
  b 0x80125AF8
.close




; In order to recolor the particles of globs of jelly coming off Dark ChuChus and then reforming, we need to shuffle around some floats in the ChuChu's float bank.
; This is because the RGB multiplier values for that particle's color are stored as floats, and the red multiplier float constant happens to be used by other things unrelated to color, so we can't simply change it.
.open "files/rels/d_a_cc.rel" ; ChuChu
.org 0x33A4 ; In action_damage_move
  ; Change a line of code that originally read 0x00000000 from 0x7E9C to instead read it from 0x7DE4.
  ; This is so we can repurpose 0x7E9C for a new float.
  lwz r0, 4 (r30)
.org 0x7E9C
  ; Put the R value of the color into the new float constant spot we freed up.
  .float 40.0
.org 0x3B14
  ; Change the line of code that originally read the R multiplier for the color to read from our new spot (0x7E9C) instead of from 0x7E2C.
  lfs f0, 0xBC (r30)
.close




; Modify the warning message that appears on screen in developer mode when a particle is missing to mention what the particle ID is.
.open "sys/main.dol"
.org 0x8025F1FC ; In createSimpleEmitterID
  ; Change the string passed as the format string from the one at 0x80366983 ("%s") to the one at 0x80366986 instead (which wasn't originally a format string, but we will replace it with a custom one.)
  addi r6, r4, 0x6E
  ; Pass the particle ID as a string format argument.
  mr r7, r21
.org 0x80366986
  ; Replace a string with a custom format string to display the missing particle ID in hex.
  ; Note that the string we're replacing was originally 0x23 bytes long, so this string should not be made any longer than that.
  .string "Missing particle with ID: 0x%04X"
.close




; Make Aryll always wear her pirate outfit, not just in Second Quest.
.open "files/rels/d_a_npc_ls1.rel" ; Aryll
.org 0x4F04
  ; Remove branch taken when not in Second Quest.
  nop
.org 0x3E88
  ; Prevent her from using her "looking out of the lookout" animation when event bit 0x2A80 (HAS_HEROS_CLOTHES) is set.
  b 0x3EE8
.close
