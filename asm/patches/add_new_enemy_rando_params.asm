
; This patch adds brand new parameters to certain enemies in order to increase their flexibility.
; This increases enemy variety in enemy randomizer.


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
  
  lis r3, g_dComIfG_gameInfo@ha
  addi r3, r3, g_dComIfG_gameInfo@l
  lbz r5, 0x20A (r31) ; Current room number
  bl onSwitch__10dSv_info_cFii
  
redead_set_death_switch_return:
  li r0, 3 ; Replace line we overwrote to jump here
  b 0x1FC0 ; Return

.close
