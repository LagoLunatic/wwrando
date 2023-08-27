
; Makes functions that play music just return instantly instead.
.open "sys/main.dol"
.org 0x802A34A4 ; bgmStart__11JAIZelBasicFUlUll
  ; Remove background music and boss music
  blr
.org 0x802A4EB8 ; bgmNowBattle__11JAIZelBasicFf
  ; Remove combat music
  blr
.org 0x802A47B8 ; subBgmStart__11JAIZelBasicFUl
  ; Remove miniboss music and item get jingles
  blr
.org 0x802A33D0 ; bgmStreamPlay__11JAIZelBasicFv
  ; Remove boss defeat fanfare
  blr
; (Puzzle solved jingles are considered to be sound effects, and are not removed.)
.close
