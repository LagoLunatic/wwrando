
; This patch modifies various enemies to increase their flexibility, allowing more enemy variety in enemy randomizer.


; Give ReDeads a new "Disable spawn on death switch" parameter (params & 0x00FF0000).
.open "files/rels/d_a_rd.rel" ; ReDead

.org 0x4874 ; In daRd_c::_create(void)
  b redead_check_disable_spawn_switch

.org @NextFreeSpace
.global redead_check_disable_spawn_switch
redead_check_disable_spawn_switch:
  lwz r4, 0xB0 (r30) ; Parameters bitfield
  rlwinm r4, r4, 16, 24, 31 ; Extract byte 0x00FF0000 from the parameters (unused in vanilla)
  cmplwi r4, 0xFF
  beq redead_check_disable_spawn_switch_return ; Return if the switch parameter is null
  cmplwi r4, 0x00
  beq redead_check_disable_spawn_switch_return ; Return if the switch parameter is zero
  
  ; Store the disable spawn on death switch to the ReDead's enemyice's death switch.
  ; This is necessary so that the enemy_ice function knows what switch to set when the enemy dies to Light Arrows.
  stb r4, 0x891 (r30) ; The enemyice is at 6E0 in the ReDead struct, and the switch is at 1B1 in the enemyice struct.
  
  lis r3, g_dComIfG_gameInfo@ha
  addi r3, r3, g_dComIfG_gameInfo@l
  lbz r5, 0x20A (r30) ; Current room number
  bl isSwitch__10dSv_info_cFii
  
  cmpwi r3, 0
  beq redead_check_disable_spawn_switch_return
  b 0x4890 ; Return to where the ReDead will cancel its initialization and despawn itself
  
redead_check_disable_spawn_switch_return:
  mr r3, r30 ; Replace line we overwrote to jump here
  b 0x4878 ; Return to where the ReDead will continue its initialization as normal

.org 0x1FBC ; In daRd_c::modeDeath(void)
  b redead_set_death_switch

.org @NextFreeSpace
.global redead_set_death_switch
redead_set_death_switch:
  lwz r4, 0xB0 (r31) ; Parameters bitfield
  rlwinm r4, r4, 16, 24, 31 ; Extract byte 0x00FF0000 from the parameters (unused in vanilla)
  cmplwi r4, 0xFF
  beq redead_set_death_switch_return ; Return if the switch parameter is null
  cmplwi r4, 0x00
  beq redead_set_death_switch_return ; Return if the switch parameter is zero
  
  lis r3, g_dComIfG_gameInfo@ha
  addi r3, r3, g_dComIfG_gameInfo@l
  lbz r5, 0x20A (r31) ; Current room number
  bl onSwitch__10dSv_info_cFii
  
redead_set_death_switch_return:
  li r0, 3 ; Replace line we overwrote to jump here
  b 0x1FC0 ; Return

.close




; Give Peahats a new "Disable spawn on death switch" parameter (x_rot & 0x00FF).
.open "files/rels/d_a_ph.rel" ; Peahats and Seahats

.org 0x68B0 ; In daPH_Create(fopAc_ac_c *)
  b peahat_check_disable_spawn_switch

.org @NextFreeSpace
.global peahat_check_disable_spawn_switch
peahat_check_disable_spawn_switch:
  lha r4, 0x20C (r29) ; X rotation
  rlwinm r4, r4, 0, 24, 31 ; Extract byte 0x00FF from the X rotation (unused in vanilla)
  
  ; Zero out the X rotation field, as this will be used by the Peahat for rotation when executing.
  li r0, 0
  sth r0, 0x20C (r29)
  
  cmplwi r4, 0xFF
  beq peahat_check_disable_spawn_switch_return ; Return if the switch parameter is null
  cmplwi r4, 0x00
  beq peahat_check_disable_spawn_switch_return ; Return if the switch parameter is zero
  
  ; Store the disable spawn on death switch to the Peahat's enemyice's death switch.
  ; This is necessary so that the enemy_ice function knows what switch to set when the enemy dies to Light Arrows.
  ; Also, we use this to store the switch even for non-enemyice-related deaths, as the X rotation field is used for rotation.
  stb r4, 0xB49 (r29) ; The enemyice is at 998 in the Peahat struct, and the switch is at 1B1 in the enemyice struct.
  
  lis r3, g_dComIfG_gameInfo@ha
  addi r3, r3, g_dComIfG_gameInfo@l
  lbz r5, 0x20A (r29) ; Current room number
  bl isSwitch__10dSv_info_cFii
  
  cmpwi r3, 0
  beq peahat_check_disable_spawn_switch_return
  b 0x68CC ; Return to where the Peahat will cancel its initialization and despawn itself
  
peahat_check_disable_spawn_switch_return:
  mr r3, r29 ; Replace line we overwrote to jump here
  b 0x68B4 ; Return to where the Peahat will continue its initialization as normal

.org 0x4118 ; In dead_item(ph_class *)
  b peahat_set_death_switch

.org @NextFreeSpace
.global peahat_set_death_switch
peahat_set_death_switch:
  lbz r4, 0xB49 (r30) ; Load the death switch from the enemyice struct (998 + 1B1)
  cmplwi r4, 0xFF
  beq peahat_set_death_switch_return ; Return if the switch parameter is null
  cmplwi r4, 0x00
  beq peahat_set_death_switch_return ; Return if the switch parameter is zero
  
  lis r3, g_dComIfG_gameInfo@ha
  addi r3, r3, g_dComIfG_gameInfo@l
  lbz r5, 0x20A (r30) ; Current room number
  bl onSwitch__10dSv_info_cFii
  
peahat_set_death_switch_return:
  mr r3, r30 ; Replace line we overwrote to jump here
  b 0x411C ; Return

.close




; Give Peahats a new "Enable spawn switch" parameter (params & 0xFF000000).
.open "files/rels/d_a_ph.rel" ; Peahats and Seahats

.org 0x5B2C ; In daPH_Execute(ph_class *)
  b peahat_check_enable_spawn_switch

.org @NextFreeSpace
.global peahat_check_enable_spawn_switch
peahat_check_enable_spawn_switch:
  lwz r4, 0xB0 (r30) ; Parameters bitfield
  rlwinm r4, r4, 8, 24, 31 ; Extract byte 0xFF000000 from the parameters (unused in vanilla)
  cmplwi r4, 0xFF
  beq peahat_check_enable_spawn_switch_return ; Return if the switch parameter is null
  cmplwi r4, 0x00
  beq peahat_check_enable_spawn_switch_return ; Return if the switch parameter is zero
  
  lis r3, g_dComIfG_gameInfo@ha
  addi r3, r3, g_dComIfG_gameInfo@l
  lbz r5, 0x20A (r30) ; Current room number
  bl isSwitch__10dSv_info_cFii
  
  cmpwi r3, 0
  bne peahat_check_enable_spawn_switch_return
  
  ; Clear the actor's attention flags. This removes the lockon target and enemy music.
  li r0, 0
  stw r0, 0x280 (r30)
  
  b 0x625C ; Return to where the Peahat will skip the rest of its execute code for this frame
  
peahat_check_enable_spawn_switch_return:
  ; Set the actor's attention flags to 4 (LockOn_Enemy).
  li r0, 4
  stw r0, 0x280 (r30)
  
  ; Set the switch parameter to 0xFF so that the draw function knows the actor should be enabled now.
  lwz r4, 0xB0 (r30) ; Parameters bitfield
  oris r4, r4, 0xFF00 ; OR with 0xFF000000
  stw r4, 0xB0 (r30)
  
  lfs f0, 0x2C0 (r30) ; Replace line we overwrote to jump here
  b 0x5B30 ; Return

.org 0x358 ; daPH_Draw(ph_class *)
  b peahat_check_enable_spawn_switch_for_draw

.org @NextFreeSpace
.global peahat_check_enable_spawn_switch_for_draw
peahat_check_enable_spawn_switch_for_draw:
  lwz r4, 0xB0 (r31) ; Parameters bitfield
  rlwinm r4, r4, 8, 24, 31 ; Extract byte 0xFF000000 from the parameters (unused in vanilla)
  cmplwi r4, 0xFF
  beq peahat_check_enable_spawn_switch_for_draw_return ; Return if the switch parameter is null
  cmplwi r4, 0x00
  beq peahat_check_enable_spawn_switch_for_draw_return ; Return if the switch parameter is zero
  
  ; We don't need to check the switch here because the execute function will have set it to 0xFF once the switch is set.
  
  b 0x4BC ; Return to where the Peahat will skip the rest of its draw code for this frame

peahat_check_enable_spawn_switch_for_draw_return:
  lwz r3, 0x2BC (r31) ; Replace line we overwrote to jump here
  b 0x35C ; Return

.close
