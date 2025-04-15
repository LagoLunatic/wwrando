
.open "sys/main.dol"
.org 0x801102D0 ; In daPy_lk_c::setDamagePoint
  b multiply_damage_amount

.org @NextFreeSpace
.global multiply_damage_amount
multiply_damage_amount:
  lfs f0, -0x5C04 (r2) ; Load 0.0f into f0
  fcmpo cr0, f1, f0 ; Compare the amount of damage (f1) to 0.0f (f0)
  bge multiply_damage_amount_return ; Don't multiply the amount if it's not negative
  
  ; Multiply the amount of damage in f1 by the damage multiplier value set by the randomizer.
  lis r4, damage_multiplier@ha
  addi r4, r4, damage_multiplier@l
  lfs f0, 0 (r4)
  fmuls f1, f1, f0
  
multiply_damage_amount_return:
  ; Replace the line we overwrote to jump here
  lis r4, g_dComIfG_gameInfo@ha
  ; Return
  b 0x801102D4

.global damage_multiplier
damage_multiplier:
  .float 1.0

.org 0x800C7D4C ; In getItemNoByLife
  ; Remove the branch that skips switching hearts out for rupees when the player's health is not 100% full.
  nop

; Prevent the disappear clouds of smoke from dropping hearts (e.g. the Keese in Puppet Ganon's fight).
.org 0x8038B0C0 ; In ki_item_d$4029 (table used in daDisappear_Execute)
  .int 0x01 ; Green Rupee

.close

; Just changing the item table used by Puppet Ganon's Keese creates an issue due to them always
; prioritizing the heart drop in the table if you have 2 or less hearts. This means they'll never
; drop arrows or magic if your health is too low, which can result in you being softlocked due to
; Light Arrows being needed to defeat Puppet Ganon.
; So we also change the Keese's logic to skip this check entirely so the other checks still run.
.open "files/rels/d_a_ki.rel" ; Keese
.org 0x326C ; In ki_fail_move
  ; Always take the branch for if your health is above 2 hearts.
  b 0x3278

.close

; Prevent the skulls in Jalhalla's fight (which are really Bubbles) from dropping hearts.
.open "files/rels/d_a_bl.rel" ; Bubbles
.org 0x50C4 ; In action_normal_skull
  li r4, 0x01 ; Green Rupee
.close
