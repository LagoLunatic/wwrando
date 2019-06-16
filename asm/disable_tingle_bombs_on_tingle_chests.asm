
; This patch stops Tingle Bombs from revealing Tingle Chests.
; It should be applied *after* tingle_chests_without_tuner.asm.

.open "files/rels/d_a_agbsw0.rel"
.org 0x1D0C ; In ExeSubT__10daAgbsw0_cFv
  ; This line was originally beq 0x1D7C, we reverse the condition so normal bombs still work but Tingle Bombs don't.
  bne 0x1D7C
.close
