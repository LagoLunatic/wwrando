
; Make Phantom Ganon take damage from the Skull Hammer instead of the Master Sword.
.open "files/rels/d_a_fganon.rel" ; Phantom Ganon
.org 0x5EE0 ; In damage_check__FP12fganon_class
  ; Checks the damage type bit. Change it from checking bit 00000002 (sword damage) to bit 00010000 (hammer damage).
  rlwinm. r0, r0, 0, 15, 15
.org 0x5EF0 ; In damage_check__FP12fganon_class
  ; Skip the code that checks that you have a master sword equipped.
  b 0x5F0C
.close
