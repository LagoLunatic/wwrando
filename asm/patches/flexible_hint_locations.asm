
; This patch modifies places in the game's code to work better with randomized hints.


; Make the Big Octo Great Fairy always give an item hint.
; In vanilla she hinted about Fire & Ice Arrows, so she didn't give the hint if your current bow was anything but Hero's Bow.
.open "files/rels/d_a_bigelf.rel" ; Great Fairy
.org 0x22A4 ; In getMsg__10daBigelf_cFv
  ; Remove the conditional branch for if your current bow is not the Hero's Bow and just always show the hint.
  nop
.close
