
.org 0x80158BFC

; Normally whether you can use Hurricane Spin or not is determined by if the event bit for the event where Orca teaches it to you is set or not.
; But we want to separate the ability from the event so they can be randomized.
; To do this we change the check for the event bit to instead be a check for bit 80 of byte 803C4CBF.
; The lower bits of byte 803C4CBF are used to keep track of whether you have the Pirate's Charm or not, but bit 80 is unused, so we can safely use it for Hurricane Spin.

lis     r3,0x803C4CBC@h
addi    r3,r3,0x803C4CBC@l
li      r4,3
li      r5,7
bl      isCollect__20dSv_player_collect_cFiUc
