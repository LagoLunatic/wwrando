
; Changes how the B button behaves during dialogue.
; Instead of needing to press B to advance each individual line of dialogue, holding down B will advance every line as soon as it can.
.open "sys/main.dol"
.org 0x80212E14 ; In dMsg_continueProc__FP13sub_msg_class
  ; Originally this line read a bitfield of buttons that were just pressed this frame (803A4E23), so that the next line could check if the B button was one of them.
  ; Change it to instead read a bitfield of buttons that are currently down (803A4E21).
  lbz r0, 0x31 (r3)
.org 0x80211EF8 ; In dMsg_stopProc__FP13sub_msg_class
  ; Same as above
  lbz r0, 0x31 (r3)
.org 0x80213858 ; In dMsg_finishProc__FP13sub_msg_class
  ; Same as above
  lbz r0, 0x31 (r3)
.org 0x8021211C ; In dMsg_selectProc__FP13sub_msg_class
  ; Same as above
  lbz r0, 0x31 (r3)
.org 0x80213718 ; In dMsg_closewaitProc__FP13sub_msg_class
  ; Same as above
  lbz r0, 0x31 (r3)
.org 0x801E6BF0 ; In dMesg_closewaitProc__FP14sub_mesg_class
  ; Same as above
  lbz r0, 0x31 (r3)
.org 0x801E6A0C ; In dMesg_outwaitProc__FP14sub_mesg_class
  ; Same as above
  lbz r0, 0x31 (r3)
.close
