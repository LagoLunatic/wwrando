
; Make Phantom Ganon take damage from the Skull Hammer instead of the Master Sword.
.open "files/rels/d_a_fganon.rel" ; Phantom Ganon
.org 0x5EE0 ; In damage_check__FP12fganon_class
  ; Checks the damage type bit. Change it from checking bit 00000002 (sword damage) to bit 00010000 (hammer damage).
  rlwinm. r0, r0, 0, 15, 15
.org 0x5EF0 ; In damage_check__FP12fganon_class
  ; Skip the code that checks that you have a master sword equipped.
  b 0x5F0C
.close




; Temporarily give the player the Hero's Sword during the Ganondorf fight by hijacking the code that temporarily removes your bow.
; And do the same while in Orca's house so you can get his two items.
.open "sys/main.dol"
.org 0x80235F10 ; In phase_4__FP13dScnPly_ply_c
  b give_temporary_sword_during_ganondorf_fight_in_swordless
.org @NextFreeSpace
.global give_temporary_sword_during_ganondorf_fight_in_swordless
give_temporary_sword_during_ganondorf_fight_in_swordless:
  stb r0, 0x48 (r4) ; Replace the line we overwrote to jump here (which removed the bow from your inventory)
  
  lbz r0, 0xE (r4) ; Read the player's currently equipped sword ID
  cmpwi r0, 0xFF
  ; If the player has any sword equipped, don't replace it with the Hero's Sword
  bne give_temporary_sword_during_ganondorf_fight_in_swordless_end
  
  li r0, 0x38
  stb r0, 0xE (r4) ; Set the player's currently equipped sword ID to the regular Hero's Sword
  
give_temporary_sword_during_ganondorf_fight_in_swordless_end:
  b 0x80235F14 ; Return

.org 0x8023607C ; In phase_4__FP13dScnPly_ply_c
  b give_temporary_sword_in_orcas_house_in_swordless
.org @NextFreeSpace
.global give_temporary_sword_in_orcas_house_in_swordless
give_temporary_sword_in_orcas_house_in_swordless:
  lis r3, 0x803C9D3C@ha ; Current stage name
  addi r3, r3, 0x803C9D3C@l
  lis r4, 0x8036A948@ha ; Pointer to the string "Ojhous", the stage for Orca's house
  addi r4, r4, 0x8036A948@l
  bl strcmp
  cmpwi r3, 0
  ; If the player did not just enter Orca's house, skip giving a temporary sword
  bne give_temporary_sword_in_orcas_house_in_swordless_end
  
  lis r3, 0x803C4C08@ha
  addi r3, r3, 0x803C4C08@l
  lbz r0, 0xE (r3) ; Read the player's currently equipped sword ID
  cmpwi r0, 0xFF
  ; If the player has any sword equipped, don't replace it with the Hero's Sword
  bne give_temporary_sword_in_orcas_house_in_swordless_end
  
  li r0, 0x38
  stb r0, 0xE (r3) ; Set the player's currently equipped sword ID to the regular Hero's Sword
  
  ; Then, in order to prevent this temporary sword from being removed by remove_temporary_sword_when_loading_stage_in_swordless, we need to return differently to skip that code.
  mr r29, r3 ; r29 needs to have 0x803C4C08 in it
  b 0x80236088
  
give_temporary_sword_in_orcas_house_in_swordless_end:
  lis r3, 0x803C ; Replace the line we overwrote to branch here
  b 0x80236080 ; Return

.org 0x80236084 ; In phase_4__FP13dScnPly_ply_c
  b remove_temporary_sword_when_loading_stage_in_swordless
.org @NextFreeSpace
.global remove_temporary_sword_when_loading_stage_in_swordless
remove_temporary_sword_when_loading_stage_in_swordless:
  lbz r0, 0xB4 (r29) ; Read the player's owned swords bitfield
  cmpwi r0, 0
  ; If the player owns any sword, don't remove their equipped sword since it's not temporary
  bne remove_temporary_sword_when_loading_stage_in_swordless_end
  
  li r0, 0xFF
  stb r0, 0xE (r29) ; Set the player's currently equipped sword ID to no sword
  
remove_temporary_sword_when_loading_stage_in_swordless_end:
  lbz r0, 0x48 (r29) ; Replace the line we overwrote to jump here
  b 0x80236088 ; Return
.close
