
; Make Tingle Chests respond to all explosive damage, not just Tingle Bombs.
.open "files/rels/d_a_agbsw0.rel"
.org 0x1CA4 ; In daAgbsw0_c::ExeSubT
  ; Skip some checks to see if the Tingle Tuner GBA link is active.
  b 0x1CC0
.org 0x1CD4 ; In daAgbsw0_c::ExeSubT
  ; After the check on if this trigger just got hit by an explosion succeeds, we skip three more checks:
  ; 1. A check that the actor that hit it isn't null.
  ; 2. A check that the actor is of type 0x128 (non-flower bombs).
  ; 3. A check that the bomb is a Tingle Bomb specifically (not a regular inventory bomb).
  b 0x1D10
.close

; Make Tingle Chests appear on the map once you have the compass even if you haven't made the chest appear yet.
; The way the game knows if a chest is a Tingle Chest is by checking the chest's opened flag.
; The five Tingle Statue Chests all have 0xF for their opened flags.
; The yellow rupee Tingle Chest in DRC has 0x10 for its flag.
; Remove the checks that cause the icon to be hidden if the opened flag is 0xF or 0x10.
.open "sys/main.dol"
.org 0x801A9F8C ; In dMenu_Dmap_c::treasureSet
  ; Skip over the two opened flag checks when drawing the big map.
  b 0x801A9F9C
.org 0x8004C68C ; In dMap_c::drawPointGc
  ; Skip over the two opened flag checks when drawing the minimap.
  b 0x8004C69C
.close
