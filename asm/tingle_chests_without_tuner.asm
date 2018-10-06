
; Make Tingle Chests respond to normal bombs as well as Tingle Bombs.
.open "files/rels/d_a_agbsw0.rel"
.org 0x1CA4 ; In ExeSubT__10daAgbsw0_cFv
  ; Skip some checks to see if the Tingle Tuner GBA link is active.
  b 0x1CC0
.org 0x1D0C ; In ExeSubT__10daAgbsw0_cFv
  ; Skip the check that it's a Tingle Bomb specifically.
  nop
.close

; Make Tingle Chests appear on the map once you have the compass even if you haven't made the chest appear yet.
; The way the game knows if a chest is a Tingle Chest is by checking the chest's opened flag.
; The five Tingle Statue Chests all have 0xF for their opened flags.
; The yellow rupee Tingle Chest in DRC has 0x10 for its flag.
; Remove the checks that cause the icon to be hidden if the opened flag is 0xF or 0x10.
.open "sys/main.dol"
.org 0x801A9F8C ; In treasureSet__12dMenu_Dmap_cFv
  ; Skip over the two opened flag checks when drawing the big map.
  b 0x801A9F9C
.org 0x8004C68C ; In drawPointGc__6dMap_cFUcfffScsUcUcUcUc
  ; Skip over the two opened flag checks when drawing the minimap.
  b 0x8004C69C
.close
