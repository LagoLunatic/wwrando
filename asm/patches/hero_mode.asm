
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

.close
