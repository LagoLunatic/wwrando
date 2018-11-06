
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
.org 0x8023607C ; In phase_4__FP13dScnPly_ply_c
  b give_temporary_sword_in_orcas_house_in_swordless
.org 0x80236084 ; In phase_4__FP13dScnPly_ply_c
  b remove_temporary_sword_when_loading_stage_in_swordless
.close
