; Prevent the lava outside the entrance to DRC from solidifying once you own Din's Pearl.
; This is so the puzzle with throwing the bomb flowers doesn't become pointless.
.open "files/rels/d_a_obj_eayogn.rel" ; Solidified lava object
.org 0x40C ; Start of check_ev_bit__13daObjEayogn_cCFv
  ; Always return false
  li r3, 0
  blr
.close


