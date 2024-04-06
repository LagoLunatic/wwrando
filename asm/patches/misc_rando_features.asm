
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
; Sets both maximum and active health, and rounds down active health to 4 so that you don't start a new file with 11 and a quarter hearts.
.org @NextFreeSpace
.global set_starting_health
set_starting_health:
  ; Base address to write health to is still stored in r3 from init__10dSv_save_cFv
  lis r4, starting_quarter_hearts@ha
  addi r4, r4, starting_quarter_hearts@l
  lhz r0, 0 (r4)
  sth r0, 0 (r3) ; Store maximum HP (including unfinished heart pieces)
  rlwinm r0,r0,0,0,29
  sth r0, 2 (r3) ; Store current HP (not including unfinished heart pieces)
  
  b 0x800589B4
.close




; Fixes a bug related to changing starting health where blank save files on the file select screen would show the number of hearts the player started with on the ISO where the save file was deleted, instead of on the current ISO.
.open "sys/main.dol"
.org 0x80182504 ; In makeRecInfo
  b get_current_health_for_file_select_screen
.org @NextFreeSpace
.global get_current_health_for_file_select_screen
get_current_health_for_file_select_screen:
  ; Read the first character of the player's name on this save file.
  ; If it's null, the save file does not exist. (This is how the vanilla code detected nonexistent save files as well.)
  lbz r0, 0x157 (r29)
  cmpwi r0, 0
  beq get_current_health_for_file_select_screen_for_blank_save_file
  
  get_current_health_for_file_select_screen_for_existing_save_file:
  ; For existing save files, we want to read the amount of health in the save.
  ; Just replace the line of code we overwrote to jump here and then return.
  lhz r3, 2 (r29)
  b get_current_health_for_file_select_screen_end
  
  get_current_health_for_file_select_screen_for_blank_save_file:
  ; For blank save files, read the initial HP instead of the wrong HP value saved to the deleted save file.
  lis r4, starting_quarter_hearts@ha
  addi r4, r4, starting_quarter_hearts@l
  lhz r3, 0 (r4)
  rlwinm r3,r3,0,0,29 ; Round down initial max HP to 4 to get rid of unfinished heart pieces
  
  get_current_health_for_file_select_screen_end:
  b 0x80182508
.org 0x80182544 ; In makeRecInfo
  b get_max_health_for_file_select_screen
.org @NextFreeSpace
.global get_max_health_for_file_select_screen
get_max_health_for_file_select_screen:
  ; Read the first character of the player's name on this save file.
  ; If it's null, the save file does not exist. (This is how the vanilla code detected nonexistent save files as well.)
  lbz r0, 0x157 (r29)
  cmpwi r0, 0
  beq get_max_health_for_file_select_screen_for_blank_save_file
  
  get_max_health_for_file_select_screen_for_existing_save_file:
  ; For existing save files, we want to read the amount of health in the save.
  ; Just replace the line of code we overwrote to jump here and then return.
  lhz r0, 0 (r29)
  b get_max_health_for_file_select_screen_end
  
  get_max_health_for_file_select_screen_for_blank_save_file:
  ; For blank save files, read the initial HP instead of the wrong HP value saved to the deleted save file.
  lis r4, starting_quarter_hearts@ha
  addi r4, r4, starting_quarter_hearts@l
  lhz r0, 0 (r4)
  
  get_max_health_for_file_select_screen_end:
  b 0x80182548
.close




; Refill the player's magic meter to full when they load a save, and cap health when starting with fewer than 3 hearts.
.open "sys/main.dol"
.org 0x80231B08 ; In FileSelectMainNormal__10dScnName_cFv right after calling card_to_memory__10dSv_info_cFPci
  b fully_refill_magic_meter_and_cap_health_on_load_save
; Refills the player's magic meter when loading a save.
.org @NextFreeSpace
.global fully_refill_magic_meter_and_cap_health_on_load_save
fully_refill_magic_meter_and_cap_health_on_load_save:
  lis r3, g_dComIfG_gameInfo@ha
  addi r3, r3, g_dComIfG_gameInfo@l
  lbz r4, 0x13 (r3) ; Load max magic meter
  stb r4, 0x14 (r3) ; Store to current magic meter
  
  cap_health:
  lhz r4, 0 (r3) ; Load max health
  rlwinm r4,r4,0,0,29 ; round max health to the full heart below
  lhz r0, 2 (r3) ; Load current health
  cmpw r0, r4
  ble already_lower
  sth r4, 2 (r3) ; Store max health to current health
  
  already_lower:
  lwz r3, 0x428 (r22) ; Replace the line we overwrote to branch here
  b 0x80231B0C ; Return
.close




; Allow turning while swinging on ropes.
.open "sys/main.dol" ; In procRopeSwing__9daPy_lk_cFv
.org 0x80145648
  b turn_while_swinging
; Borrows logic used for vanilla rope hang turning and injects some of the rotation logic into the rope swinging function.
; The main difference between the way the vanilla rope hanging function turns the player and this custom function is that the vanilla function uses a maximum rotational velocity per frame of 0x200, and a rotational acceleration of 0x40.
; But 0x200 units of rotation per frame would be far too fast to control when the player is swinging, and they could clip through walls very easily.
; So instead we just use the rotational acceleration as a constant rotational velocity instead, with no acceleration or deceleration.
.org @NextFreeSpace
.global turn_while_swinging
turn_while_swinging:
  lis r3, 0x803A4DF0@ha
  addi r3, r3, 0x803A4DF0@l
  lfs f0, 0 (r3) ; Control stick horizontal axis (from -1.0 to 1.0)
  lfs f1, -0x5B24 (rtoc) ; Load the float constant at 803FA1DC for the base amount of rotational velocity to use (100.0)
  fmuls f0, f1, f0 ; Get the current amount of rotational velocity to use this frame after adjusting for the control stick amount
  
  ; Convert current rotational velocity to an integer.
  ; (sp+0x68 was used earlier on in procRopeSwing__9daPy_lk_cFv for float conversion so we just reuse this same space.)
  fctiwz  f0, f0
  stfd f0, 0x68 (sp)
  lwz r0, 0x6C (sp)
  
  ; Convert base rotational velocity to an integer.
  fctiwz  f1, f1
  stfd f1, 0x68 (sp)
  lwz r3, 0x6C (sp)
  
  ; If the player isn't moving the control stick horizontally very much (less than 25%), don't turn the player at all.
  rlwinm r3, r3, 30, 2, 31 ; Divide the base rotational velocity by 4 to figure out what the threshold should be for 25% on the control stick.
  cmpw r0, r3
  bge turn_while_swinging_update_angle ; Control stick is >=25%
  neg r3, r3
  cmpw r0, r3
  ble turn_while_swinging_update_angle ; Control stick is <=-25%
  b turn_while_swinging_return
  
  turn_while_swinging_update_angle:
  ; Subtract rotational velocity from the player's rotation. (Both player_entity+20E and +206 have the player's rotation.)
  lha r3, 0x020E (r31)
  sub r0, r3, r0
  sth r0, 0x020E (r31)
  sth r0, 0x0206 (r31)
  
  turn_while_swinging_return:
  lfs f0, -0x5BA8 (rtoc) ; Replace line we overwrote to branch here
  b 0x8014564C ; Return
.close




; Animate the 500 rupee to be a rainbow rupee that animates between the colors of all other rupees.
.open "sys/main.dol"
.org 0x800F93F4
  b check_animate_rainbow_rupee_color
; Manually animate rainbow rupees to cycle through all other rupee colors.
; In order to avoid an abrupt change from silver to green when it loops, we make the animation play forward and then backwards before looping, so it's always a smooth transition.
.org @NextFreeSpace
.global check_animate_rainbow_rupee_color
check_animate_rainbow_rupee_color:
  ; Check if the color for this rupee specified in the item resources is 7 (originally unused, we use it as a marker to separate the rainbow rupee from other color rupees).
  cmpwi r0, 7
  beq animate_rainbow_rupee_color
  
  ; If it's not the rainbow rupee, replace the line of code we overwrote to jump here, and then return to the regular code for normal rupees.
  lfd f1, -0x5DF0 (rtoc)
  b 0x800F93F8
  
  animate_rainbow_rupee_color:
  
  ; If it is the rainbow rupee, we need to increment the current keyframe (a float) by certain value every frame.
  ; (Note: The way this is coded would increase it by this value multiplied by the number of rainbow rupees being drawn. This is fine since there's only one rainbow rupee but would cause issues if we placed multiple of them. Would need to find a different place to increment the keyframe in that case, somewhere only called once per frame.)
  lis r5, rainbow_rupee_keyframe@ha
  addi r5, r5, rainbow_rupee_keyframe@l
  lfs f1, 0 (r5) ; Read current keyframe
  lfs f0, 4 (r5) ; Read amount to add to keyframe per frame
  fadds f1, f1, f0 ; Increase the keyframe value
  
  lfs f0, 8 (r5) ; Read the maximum keyframe value
  fcmpo cr0,f1,f0
  ; If we're less than the max we don't need to reset the value
  blt store_rainbow_rupee_keyframe_value
  
  ; If we're greater than the max, reset the current keyframe to the minimum.
  ; The minimum is actually the maximum negated. This is to signify that we're playing the animation backwards.
  lfs f1, 0xC (r5)
  
  store_rainbow_rupee_keyframe_value:
  stfs f1, 0 (r5) ; Store the new keyframe value back
  
  ; Take the absolute value of the keyframe. So instead of going from -6 to +6, the value we pass as the actual keyframe goes from 6 to 0 to 6.
  fabs f1, f1
  
  b 0x800F9410

.global rainbow_rupee_keyframe
rainbow_rupee_keyframe:
  .float 0.0 ; Current keyframe, acts as a global variable modified every frame
  .float 0.15 ; Amount to increment keyframe by every frame a rainbow rupee is being drawn
  .float 6.0 ; Max keyframe, when it should loop
  .float -6.0 ; Minimum keyframe
.close




; Checks if the upcoming message text to parse has a custom text command.
.open "sys/main.dol"
.org 0x80033E74
  b check_run_new_text_commands

; Check the ID of the upcoming text command to see if it's a custom one, and runs custom code for it if so.
.org @NextFreeSpace
.global check_run_new_text_commands
check_run_new_text_commands:
  clrlwi. r6,r0,24
  bne check_run_new_text_commands_check_failed
  
  lbz r6,3(r3)
  cmplwi r6,0
  bne check_run_new_text_commands_check_failed
  
  lbz r6,4(r3)
  cmplwi r6, 0x4B ; Lowest key counter text command ID
  blt check_run_new_text_commands_check_failed
  cmplwi r6, 0x4F ; Highest key counter text command ID
  bgt check_run_new_text_commands_check_failed
  
  mr r3,r31
  mr r4, r6
  bl exec_curr_num_keys_text_command
  b 0x80034D34 ; Return (to after a text command has been successfully executed)

check_run_new_text_commands_check_failed:
  clrlwi. r6,r0,24 ; Replace the line we overwrote to jump here
  b 0x80033E78 ; Return (to back inside the code to check what text command should be run)


; Updates the current message string with the number of keys for a certain dungeon.
.global exec_curr_num_keys_text_command
exec_curr_num_keys_text_command:
  stwu sp, -0x50 (sp)
  mflr r0
  stw r0, 0x54 (sp)
  stw r31, 0xC (sp)
  stw r30, 8 (sp)
  mr r31, r3
  
  ; Convert the text command ID to the dungeon stage ID.
  ; The text command ID ranges from 0x4B-0x4F, for DRC, FW, TotG, ET, and WT.
  ; The the dungeon stage IDs for those same 5 dungeons range from 3-7.
  ; So just subtract 0x48 to get the right stage ID.
  addi r4, r4, -0x48
  
  lis r3, 0x803C53A4@ha ; This value is the stage ID of the current stage
  addi r3, r3, 0x803C53A4@l
  lbz r5, 0 (r3)
  cmpw r5, r4 ; Check if we're currently in the right dungeon for this key
  beq exec_curr_num_keys_text_command_in_correct_dungeon
  
exec_curr_num_keys_text_command_not_in_correct_dungeon:
  ; Read the current number of small keys from that dungeon's stage info.
  lis r3, 0x803C4F88@ha ; List of all stage info
  addi r3, r3, 0x803C4F88@l
  mulli r4, r4, 0x24 ; Use stage ID of the dungeon as the index, each entry in the list is 0x24 bytes long
  add r3, r3, r4
  lbz r4, 0x20 (r3) ; Current number of keys for the correct dungeon
  mr r30, r3 ; Remember the correct stage info pointer for later when we check the big key
  b exec_curr_num_keys_text_command_after_reading_num_keys
  
exec_curr_num_keys_text_command_in_correct_dungeon:
  ; Read the current number of small keys from the currently loaded dungeon info.
  lis r3, 0x803C5380@ha ; Currently loaded stage info
  addi r3, r3, 0x803C5380@l
  lbz r4, 0x20 (r3) ; Current number of keys for the current dungeon
  mr r30, r3 ; Remember the correct stage info pointer for later when we check the big key
  
exec_curr_num_keys_text_command_after_reading_num_keys:
  ; Convert int to string
  addi r3, sp, 0x1C
  li r5, 0
  bl fopMsgM_int_to_char__FPcib
  
  ; Check whether the player has the big key or not.
  lbz r4, 0x21 (r30) ; Bitfield of dungeon-specific flags in the appropriate stage info
  rlwinm. r4, r4, 0, 29, 29 ; Extract the has big key bit
  beq exec_curr_num_keys_text_command_does_not_have_big_key
  
exec_curr_num_keys_text_command_has_big_key:
  ; Append the " +Big" text
  addi r3, sp, 0x1C
  lis r4, key_text_command_has_big_key_text@ha
  addi r4, r4, key_text_command_has_big_key_text@l
  bl strcat
  b exec_curr_num_keys_text_command_after_appending_big_key_text
  
exec_curr_num_keys_text_command_does_not_have_big_key:
  ; Append some whitespace so that the text stays in the same spot regardless of whether you have the big key or not
  addi r3, sp, 0x1C
  lis r4, key_text_command_does_not_have_big_key_text@ha
  addi r4, r4, key_text_command_does_not_have_big_key_text@l
  bl strcat
  
exec_curr_num_keys_text_command_after_appending_big_key_text:
  ; Concatenate to one of the main strings
  lwz r3, 0x60(r31)
  addi r4, sp, 0x1C
  bl strcat
  
  ; Concatenate to one of the main strings
  lwz r3, 0x68(r31)
  addi r4, sp, 0x1C
  bl strcat
  
  ; Increase the offset within the encoded message string to be past the end of this text command
  lwz r4, 0x118(r31)
  addi r4, r4, 5 ; Note that technically, this command length value should be dynamically read from [cmd+1]. But because it's always 5 for the custom commands it doesn't matter and it can be hardcoded instead.
  stw r4, 0x118(r31)
  
  ; Note: There are some other things that the vanilla text commands did that are currently not implemented for these custom ones. Such as what appears to be keeping track of the current line length, possibly for word wrapping or text alignment purposes (which aren't necessary for the Key Bag).
  
  lwz r30, 8 (sp)
  lwz r31, 0xC (sp)
  lwz r0, 0x54 (sp)
  mtlr r0
  addi sp, sp, 0x50
  blr

key_text_command_has_big_key_text:
  .string " +Big"
key_text_command_does_not_have_big_key_text:
  .string "     "
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

; Since we couldn't put the new message ID for the custom warp's confirmation dialog text right after the original ones, we need custom code to return the custom message ID.
.org @NextFreeSpace
.global set_warp_confirm_dialog_message_id_for_custom_warps
set_warp_confirm_dialog_message_id_for_custom_warps:
  cmpwi r31, 9 ; Forsaken Fortress Warp index
  bne set_warp_confirm_dialog_message_id_for_custom_warps_not_custom
  
  li r10, 848 ; Custom message ID
  b 0x801B80F8 ; Return to normal code after deciding message ID
  
  set_warp_confirm_dialog_message_id_for_custom_warps_not_custom:
  addi r10, r31, 69 ; Replace the line we overwrote to jump here
  b 0x801B80F8 ; Return to normal code after deciding message ID

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
.org @NextFreeSpace
.global check_player_in_casual_clothes
check_player_in_casual_clothes:
  stwu sp, -0x10 (sp)
  mflr r0
  stw r0, 0x14 (sp)
  
  lis r3, should_start_with_heros_clothes@ha
  addi r3, r3, should_start_with_heros_clothes@l
  lbz r3, 0 (r3) ; Load bool of whether player should start with Hero's clothes
  cmpwi r3, 1
  beq check_player_in_casual_clothes_hero
  
  check_player_in_casual_clothes_casual:
  li r3, 1
  b check_player_in_casual_clothes_end
  
  check_player_in_casual_clothes_hero:
  li r3, 0
  
  check_player_in_casual_clothes_end:
  lwz r0, 0x14 (sp)
  mtlr r0
  addi sp, sp, 0x10
  blr
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




; Modify the loops that check the RELs list and actor names list to also check our custom lists, allowing us to add new actors without replacing existing ones.
.open "sys/main.dol"
.org 0x800229AC ; In cCc_Init
  b read_custom_DynamicNameTable_loop
.org @NextFreeSpace
.global read_custom_DynamicNameTable_loop
read_custom_DynamicNameTable_loop:
  ; Index 0x1AE is normally where the loop would end in vanilla.
  ; We have it switch to the custom list at this point.
  cmplwi r28, 0x1AE
  beq read_custom_DynamicNameTable_loop_switch_from_vanilla_to_custom
  
  ; If we're past even the indexes for our custom list, end the loop.
  cmplwi r28, 0x1AE + num_custom_DynamicNameTable_entries ; Num entries in vanilla list + custom list
  bge read_custom_DynamicNameTable_loop_end_loop
  
  ; Otherwise, just continue the loop, since we're on a custom entry that is not the first one.
  blt read_custom_DynamicNameTable_loop_switch_continue
  
  read_custom_DynamicNameTable_loop_switch_from_vanilla_to_custom:
  ; Replace the pointer to the start of the vanilla DynamicNameTable in r31 with a pointer to the start of our custom one.
  lis r31, custom_DynamicNameTable@ha
  addi r31, r31, custom_DynamicNameTable@l
  ; Reset the offset into the list in r26 to 0 since we're now at the start of the custom list instead of the end of the vanilla list.
  li r26, 0
  
  read_custom_DynamicNameTable_loop_switch_continue:
  b 0x8002283C ; Return to the start of the vanilla loop
  
  read_custom_DynamicNameTable_loop_end_loop:
  mr r3, r30 ; Replace a line of code we overwrote to jump here
  b 0x800229B0 ; Return to after the end of the loop

.org 0x80041598 ; In dStage_searchName
  b read_custom_l_objectName_loop_for_dStage_searchName
.org @NextFreeSpace
.global read_custom_l_objectName_loop_for_dStage_searchName
read_custom_l_objectName_loop_for_dStage_searchName:
  ; Index 0x339 is normally where the loop would end in vanilla.
  ; We have it switch to the custom list at this point.
  cmplwi r30, 0x339
  beq read_custom_l_objectName_loop_for_dStage_searchName_switch_from_vanilla_to_custom
  
  ; If we're past even the indexes for our custom list, end the loop.
  cmplwi r30, 0x339 + num_custom_l_objectName_entries ; Num entries in vanilla list + custom list
  bge read_custom_l_objectName_loop_for_dStage_searchName_end_loop
  
  ; Otherwise, just continue the loop, since we're on a custom entry that is not the first one.
  blt read_custom_l_objectName_loop_for_dStage_searchName_continue
  
  read_custom_l_objectName_loop_for_dStage_searchName_switch_from_vanilla_to_custom:
  ; Replace the pointer to the current entry of the vanilla l_objectName in r31 with a pointer to the start of our custom one.
  lis r31, custom_l_objectName@ha
  addi r31, r31, custom_l_objectName@l
  
  read_custom_l_objectName_loop_for_dStage_searchName_continue:
  b 0x8004156C ; Return to the start of the vanilla loop
  
  read_custom_l_objectName_loop_for_dStage_searchName_end_loop:
  li r3, 0 ; Replace a line of code we overwrote to jump here
  b 0x8004159C ; Return to after the end of the loop

.org 0x800415FC ; In dStage_getName
  b read_custom_l_objectName_loop_for_dStage_getName
.org @NextFreeSpace
.global read_custom_l_objectName_loop_for_dStage_getName
read_custom_l_objectName_loop_for_dStage_getName:
  ; Check if the current entry pointer is right after the end of our custom list.
  ; If so, this means we've exhausted both the entire vanilla list and the custom list, so end the loop.
  lis r7, custom_l_objectName_end@ha
  addi r7, r7, custom_l_objectName_end@l
  cmpw r6, r7
  beq read_custom_l_objectName_loop_for_dStage_getName_end_loop
  
  ; Otherwise, we'll only reach this point when exhausting the vanilla list, so switch from the end of the vanilla list to the beginning of the custom list.
  
  read_custom_l_objectName_loop_for_dStage_getName_switch_from_vanilla_to_custom:
  ; Replace the pointer to the current entry of the vanilla l_objectName in r6 with a pointer to the start of our custom one.
  lis r6, custom_l_objectName@ha
  addi r6, r6, custom_l_objectName@l
  ; Then restart the loop counter so it loops for our custom list.
  li r0, num_custom_l_objectName_entries ; Num entries in our custom list
  mtctr r0
  
  read_custom_l_objectName_loop_for_dStage_getName_continue:
  b 0x800415D0 ; Return to the start of the vanilla loop
  
  read_custom_l_objectName_loop_for_dStage_getName_end_loop:
  lis r3, 0x8034EC78@ha ; Replace the line of code we overwrote to jump here
  b 0x80041600 ; Return to after the end of the loop

; Also change references to the original DMC list of all actors to our custom one.
.org 0x80022818
  lis r3, custom_DMC@ha
  addi r3, r3, custom_DMC@l
.org 0x80022898
  lis r3, custom_DMC@ha
  addi r3, r3, custom_DMC@l
.org 0x800228EC
  lis r3, custom_DMC@ha
  addi r24, r3, custom_DMC@l
.org 0x80022930
  lis r3, custom_DMC@ha
  addi r3, r3, custom_DMC@l
.org 0x80022958
  lis r3, custom_DMC@ha
  addi r3, r3, custom_DMC@l
.org 0x80022990
  lis r3, custom_DMC@ha
  addi r3, r3, custom_DMC@l
.org 0x80022A40
  lis r3, custom_DMC@ha
  addi r3, r3, custom_DMC@l
.org 0x80022B24
  lis r3, custom_DMC@ha
  addi r3, r3, custom_DMC@l
.org 0x80022C30
  lis r3, custom_DMC@ha
  addi r3, r3, custom_DMC@l

; Also change references to the original total number of actors (0x1F6) to the number including our custom actors.
.org 0x80022850
  cmplwi r0, 0x1F6 + num_custom_DynamicNameTable_entries
.org 0x80022944
  cmplwi r23, 0x1F6 + num_custom_DynamicNameTable_entries
.org 0x80022ADC
  cmplwi r0, 0x1F6 + num_custom_DynamicNameTable_entries
.org 0x80022BC8
  cmplwi r4, 0x1F6 + num_custom_DynamicNameTable_entries

.close




; Change the condition for Outset switching to its alternate BGM theme from checking event bit 0E20 (PIRATES_ON_OUTSET, for Aryll being kidnapped) to instead check if the Pirate Ship chest has been opened (since Aryll is in the Pirate Ship in the randomizer).
.open "sys/main.dol"
.org 0x802A2BE4 ; In JAIZelBasic::zeldaGFrameWork
  li r3, 13 ; Stage info ID that includes the Pirate Ship.
  li r4, 5 ; Chest open flag for the Pirate Ship chest that originally had Bombs.
  bl custom_isTbox_for_unloaded_stage_save_info
.org 0x802AA2E4 ; In JAIZelBasic::startIsleBgm
  li r3, 13 ; Stage info ID that includes the Pirate Ship.
  li r4, 5 ; Chest open flag for the Pirate Ship chest that originally had Bombs.
  bl custom_isTbox_for_unloaded_stage_save_info
.org 0x802AA4CC ; In JAIZelBasic::setScene
  li r3, 13 ; Stage info ID that includes the Pirate Ship.
  li r4, 5 ; Chest open flag for the Pirate Ship chest that originally had Bombs.
  bl custom_isTbox_for_unloaded_stage_save_info
.org 0x802AA4E8 ; In JAIZelBasic::setScene
  li r3, 13 ; Stage info ID that includes the Pirate Ship.
  li r4, 5 ; Chest open flag for the Pirate Ship chest that originally had Bombs.
  bl custom_isTbox_for_unloaded_stage_save_info
.close




; Replace the calls to getCollectMapNum on the quest status screen with a call to a custom function that checks the number of owned tingle statues.
.open "sys/main.dol"
.org 0x8019CAC0 ; In dMenu_Collect_c::screenSet(void)
  ; Handles the tens digit
  bl get_num_owned_tingle_statues
.org 0x8019CAFC ; In dMenu_Collect_c::screenSet(void)
  ; Handles the ones digit
  bl get_num_owned_tingle_statues
.org @NextFreeSpace
.global get_num_owned_tingle_statues
get_num_owned_tingle_statues:
  stwu sp, -0x10 (sp)
  mflr r0
  stw r0, 0x14 (sp)
  
  li r6, 0
  
  li r3, 3 ; Dragon Tingle Statue
  li r4, 0xF
  bl check_tingle_statue_owned
  add r6, r6, r3
  
  li r3, 4 ; Forbidden Tingle Statue
  li r4, 0xF
  bl check_tingle_statue_owned
  add r6, r6, r3
  
  li r3, 5 ; Goddess Tingle Statue
  li r4, 0xF
  bl check_tingle_statue_owned
  add r6, r6, r3
  
  li r3, 6 ; Earth Tingle Statue
  li r4, 0xF
  bl check_tingle_statue_owned
  add r6, r6, r3
  
  li r3, 7 ; Wind Tingle Statue
  li r4, 0xF
  bl check_tingle_statue_owned
  add r6, r6, r3
  
  mr r3, r6
  
  lwz r0, 0x14 (sp)
  mtlr r0
  addi sp, sp, 0x10
  blr
.close




; Give the inter-dungeon warp pots a different smoke particle color compared to other warp pots to help distinguish them.
.open "files/rels/d_a_obj_warpt.rel" ; Warp pots
.org 0x2050 ; In daObj_Warpt_c::createInit(void), before setting prm_color
  b set_prm_color_for_warp_pot_particles
.org 0x2080 ; In daObj_Warpt_c::createInit(void), before setting env_color
  b set_env_color_for_warp_pot_particles

.org @NextFreeSpace

.global set_prm_color_for_warp_pot_particles
set_prm_color_for_warp_pot_particles:
  add r4, r4, r0 ; Replace line overwrote to jump here
  
  lwz r0, 0x2B8 (r30) ; Event register index. 2 and 5 are for inter-dungeon warp pots.
  cmpwi r0, 2
  beq set_prm_color_for_warp_pot_particles_is_inter_dungeon
  cmpwi r0, 5
  bne set_prm_color_for_warp_pot_particles_is_not_inter_dungeon
  
  set_prm_color_for_warp_pot_particles_is_inter_dungeon:
  lis r4, custom_warp_pot_prm_color@ha
  addi r4, r4, custom_warp_pot_prm_color@l
  b 0x2054 ; Return
  
  set_prm_color_for_warp_pot_particles_is_not_inter_dungeon:
  b 0x2054 ; Return

.global set_env_color_for_warp_pot_particles
set_env_color_for_warp_pot_particles:
  add r4, r4, r0 ; Replace line overwrote to jump here
  
  lwz r0, 0x2B8 (r30) ; Event register index. 2 and 5 are for inter-dungeon warp pots.
  cmpwi r0, 2
  beq set_env_color_for_warp_pot_particles_is_inter_dungeon
  cmpwi r0, 5
  bne set_env_color_for_warp_pot_particles_is_not_inter_dungeon
  
  set_env_color_for_warp_pot_particles_is_inter_dungeon:
  lis r4, custom_warp_pot_env_color@ha
  addi r4, r4, custom_warp_pot_env_color@l
  b 0x2084 ; Return
  
  set_env_color_for_warp_pot_particles_is_not_inter_dungeon:
  b 0x2084 ; Return

.global custom_warp_pot_prm_color ; The main color
custom_warp_pot_prm_color:
  .int 0xE5101B80 ; Bright red
.global custom_warp_pot_env_color ; The outline color
custom_warp_pot_env_color:
  .int 0x3C379D80 ; Dark purple
.close




; Stop Old man Ho-Ho from disappearing under some conditions.
.open "files/rels/d_a_npc_ah.rel" ; Old Man Ho-Ho
.org 0x1044 ; Don't check if Cabana Octo is defeated
  li r3, 0
.org 0x1018 ; Don't check if the stone head above Savage Labyrinth is destroyed
  li r3, 0
.org 0x1078 ; Don't check if the Two-Eye Reef Octo is defeated
  li r3, 0
.org 0x8A8 ; Don't check if Cabana Octo is defeated
  li r3, 0
.org 0x85C ; Don't check if the stone head above Savage Labyrinth is destroyed
  li r3, 0
.org 0x8D8 ; Don't check if the Two-Eye Reef Octo is defeated
  li r3, 0
.close




; Change the Deku Leaf so that you can still fan it to create a gust of air when you have zero magic.
; In vanilla, you needed at least one magic to fan it, but it didn't consume any magic.
; This is done so that the Deku Leaf still has some usefulness when starting without a magic meter.
; It also allows the fan ability (which allows accessing Horseshoe Island's golf) to be separated from the flying ability.
.open "sys/main.dol"
.org 0x8014BDF8 ; In daPy_lk_c::setShapeFanLeaf(void)
  ; Remove branch taken when having less than 1 magic.
  nop
.close




; Allow the player to carry enemy weapons through doors instead of dropping them.
; We also allow enemy weapons to be carried up and down ladders.
; But we don't allow bringing enemy weapons into the water or the ship.
.open "sys/main.dol"
.org 0x80121B18 ; In daPy_lk_c::execute
  ; This runs when the player walks through a door.
  ; It checks if the player is holding an enemy weapon, and if not, skips the code to drop it.
  ; We change it to unconditionally take the branch so that the weapon is not dropped.
  b 0x80121B54
.org 0x8013344C ; In daPy_lk_c::procLadderUpStart_init
  ; This runs when the player starts climbing up a ladder.
  ; We still want the player's sword and shield to be put away if those are out.
  ; But we don't want any enemy weapons to be dropped.
  b ladder_up_check_unequip_held_item
.org 0x8013389C ; In daPy_lk_c::procLadderDownStart_init
  ; This runs when the player starts climbing down a ladder.
  ; Same change as for climbing up the ladder.
  b ladder_down_check_unequip_held_item
.org @NextFreeSpace
.global ladder_up_check_unequip_held_item
ladder_up_check_unequip_held_item:
  cmplwi r0, 0x100 ; No held item
  beq ladder_up_do_not_unequip_held_item
  cmplwi r0, 0x101 ; Held enemy weapon
  beq ladder_up_do_not_unequip_held_item
  b 0x8013347C ; Return to the code that unequips the held item
ladder_up_do_not_unequip_held_item:
  b 0x80133450 ; Return to the code for climbing the ladder without unequipping the held item
.global ladder_down_check_unequip_held_item
ladder_down_check_unequip_held_item:
  cmplwi r0, 0x100 ; No held item
  beq ladder_down_do_not_unequip_held_item
  cmplwi r0, 0x101 ; Held enemy weapon
  beq ladder_down_do_not_unequip_held_item
  b 0x801338CC ; Return to the code that unequips the held item
ladder_down_do_not_unequip_held_item:
  b 0x801338A0 ; Return to the code for climbing the ladder without unequipping the held item
.close
