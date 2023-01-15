
; This patch changes various things to allow the game to be played nonlinearly.


; Modify King of Red Lions's code so he doesn't stop you when you veer off the path he wants you to go on.
.open "files/rels/d_a_ship.rel"
; We need to change some of the conditions in his checkOutRange function so he still prevents you from leaving the bounds of the map, but doesn't railroad you based on your story progress.
; First is the check for before you've reached Dragon Roost Island. Make this branch unconditional so it considers you to have seen Dragon Roost's intro whether you have or not.
.org 0x29EC
  b 0x2A50
; Second is the check for whether you've gotten Farore's Pearl. Make this branch unconditional too.
.org 0x2A08
  b 0x2A50
; Third is the check for whether you have the Master Sword. Again make the branch unconditional.
.org 0x2A24
  b 0x2A34
; Skip the check for if you've seen the Dragon Roost Island intro which prevents you from getting in the King of Red Lions.
; Make this branch unconditional as well.
.org 0xB2D8
  b 0xB2F0
.close




; Fishmen usually won't appear until Gohma is dead. This removes that check from their code so they appear from the start.
.open "files/rels/d_a_npc_so.rel" ; Fishman
.org 0x3FD8
  ; Change the conditional branch to an unconditional branch.
  b 0x3FE4
.close




; Normally Medli would disappear once you own the Master Sword (Half Power).
; This could make the Earth Temple uncompletable if you get the Master Sword (Half Power) before doing it.
; So we slightly modify Medli's code to not care about your sword.
.open "files/rels/d_a_npc_md.rel" ; Medli
.org 0xA24
  ; Make branch that depends on your sword unconditional instead.
  b 0xA60
.close
; Same for Makar, with the Master Sword (Full Power) instead.
.open "files/rels/d_a_npc_cb1.rel" ; Makar
.org 0x640
  ; Make branch that depends on your sword unconditional instead.
  b 0x658
.close




; Normally Medli and Makar disappear from the dungeon map after you get the half-power or full-power master sword, respectively.
; We remove these checks so they still appear on the map even after that (of course, only if you have the compass).
.open "sys/main.dol"
.org 0x801A9A6C
  li r3, 0
.org 0x801A9AA8
  li r3, 0
.close




; Originally the withered trees and the Koroks next to them only appear after you get Farore's Pearl.
; This gets rid of all those checks so they appear from the start of the game.
.open "files/rels/d_a_obj_ftree.rel" ; Withered Trees
.org 0xA4C
  nop
.close
.open "files/rels/d_a_npc_bj1.rel" ; Koroks
.org 0x784
  li r0, 0x1F
  li r31, 0
.org 0x830
  li r0, 0x1F
  li r30, 0
.org 0x984
  li r0, 0x1F
  li r31, 0
.org 0xA30
  li r0, 0
.org 0x2200
  nop
.close




; The warp object down to Hyrule sets the event bit to change FF2 into FF3 once the event bit for seeing Tetra transform into Zelda is set.
; We want FF2 to stay permanently, so we skip over the line that sets this bit.
.open "files/rels/d_a_warpdm20.rel" ; Hyrule warp object
.org 0x68C
  b 0x694
.close




; Changes the way spoils and bait work from the vanilla game.
; Normally if you encountered spoils or bait as a field item without owning the Bait Bag/Spoils bag, it would turn itself into a single green rupee instead so you can't get the items without a bag to put them in.
; In the randomizer we allow these to drop even without having the bags so you can get these items early.
.open "sys/main.dol"
.org 0x800C7E58 ; In check_itemno
  li r3, 1 ; Bait Bag
.org 0x800C7E84 ; In check_itemno
  li r3, 1 ; Spoils Bag
.close




; Normally the Earth/Wind Temple song tablets rely on whether you have the Earth God's Lyric or Wind God's Aria to tell which version they are.
; For example, the second tablet halfway through Earth Temple will act like the first one at the entrance if you don't own the Earth God's Lyric yet. As a result, it will give you the Earth God's Lyric, and then teleport you back to the entrance for the Zora sage cutscene.
; So we remove the checks for if you have the songs yet, and instead always act as if the player has them.
.open "files/rels/d_a_obj_mknjd.rel" ; Earth/Wind Temple song tablet
.org 0x96C
  b 0x994 ; Make branch unconditional
.org 0x205C
  nop ; Remove branch
.org 0x20D4
  nop ; Remove branch
.close




; Fixes a bug with the recollection boss fights that can happen if you skip at least one of the original boss fights.
; If you fight a recollection boss without fighting the original form of that boss first, and then you fight a different recollection boss who you did fight the original form of, then when you kill that second boss your entire inventory will be replaced by null items (item ID 00, would be a heart pickup but in your inventory it looks like an empty bottle).
; To fix this we simply remove the feature of resetting the player's inventory to what it was during the original form of the boss fight entirely, so the player's inventory is always left alone.
; Replace all 4 functions related to this with instant returns.
.open "sys/main.dol"
.org 0x80054CC0 ; dComIfGs_copyPlayerRecollectionData__Fv
  blr
.org 0x80054E9C ; dComIfGs_setPlayerRecollectionData__Fv
  blr
.org 0x80055318 ; dComIfGs_revPlayerRecollectionData__Fv
  blr
.org 0x80055580 ; dComIfGs_exchangePlayerRecollectionData__Fv
  blr
.close




; The death zone in between Forest Haven and Forbidden Woods disappears once you have Farore's Pearl.
; This makes it frustrating to make the trip to Forbidden Woods since you have to go all the way through Forest Haven every time you fail.
; So we change this void to always be there, even after you own Farore's Pearl.
.open "files/rels/d_a_tag_ret.rel" ; Void out death zone
.org 0x22C
  ; Change the branch here to be unconditional and always act like you do not have Farore's pearl.
  b 0x238
.close




; In vanilla, the mailbox will not give you any mail until you own Din's Pearl.
; Remove that condition so that only the letter-specific requirements matter.
.open "files/rels/d_a_obj_toripost.rel" ; Mailbox
.org 0x187C
  nop
.close




; When the player enters Wind Temple, reset Makar's position to the starting room, or to near the warp pot the player exited.
; This is to prevent possible softlocks where Makar can teleport to later rooms in the dungeon for seemingly no reason.
.open "files/rels/d_a_npc_cb1.rel" ; Makar
.org 0x7D4
  bl reset_makar_position_to_start_of_dungeon
.org 0x7B4 ; This line originally stopped Makar from spawning if the partner ID number (803C4DC3) was not set to 1.
  ; Remove the line so that Makar spawns in, even after taking an inter-dungeon warp pot.
  nop
.org @NextFreeSpace
.global reset_makar_position_to_start_of_dungeon
reset_makar_position_to_start_of_dungeon:
  stwu sp, -0x10 (sp)
  mflr r0
  stw r0, 0x14 (sp)
  
  lis r8, 0x803C9D44@ha ; Most recent spawn ID the player spawned from
  addi r8, r8, 0x803C9D44@l
  lha r8, 0 (r8)
  
  ; Search through the list of places Makar can spawn from to see which one corresponds to the player's last spawn ID, if any.
  lis r9, makar_possible_wt_spawn_positions@ha
  addi r9, r9, makar_possible_wt_spawn_positions@l
  li r0, 5 ; 5 possible spawn points
  mtctr r0
  makar_spawn_point_search_loop_start:
  lbz r0, 0 (r9) ; Spawn ID
  cmpw r0, r8
  beq reset_makar_found_matching_spawn_point ; Found the array element corresponding to this spawn ID
  addi r9, r9, 0x10 ; Increase pointer to point to next element
  bdnz makar_spawn_point_search_loop_start ; Loop
  
  ; The player came from a spawn that doesn't correspond to any of the elements in the array, don't change Makar's position.
  b after_resetting_makar_position
  
  reset_makar_found_matching_spawn_point:
  lwz r8, 4 (r9) ; X pos
  stw r8, 0 (r5)
  lwz r8, 8 (r9) ; Y pos
  stw r8, 4 (r5)
  lwz r8, 0xC (r9) ; Z pos
  stw r8, 8 (r5)
  
  lha r8, 2 (r9) ; Rotation
  sth r8, 0xC (r5)
  mr r6, r8 ; Argument r6 to setRestartOption needs to be the rotation
  mr r28, r8 ; Also modify the local variable rotation in Makar's code (for when he calls set__19dSv_player_priest)
  
  lbz r8, 1 (r9) ; Room index
  stb r8, 0xE (r5)
  mr r7, r8 ; Argument r7 to setRestartOption needs to be the room index
  mr r29, r8 ; Also modify the local variable room index in Makar's code (for when he calls set__19dSv_player_priest)
  
  after_resetting_makar_position:
  
  bl setRestartOption__13dSv_restart_cFScP4cXyzsSc ; Replace the function call we overwrote to call this custom function
  
  lwz r0, 0x14 (sp)
  mtlr r0
  addi sp, sp, 0x10
  blr

.global makar_possible_wt_spawn_positions
makar_possible_wt_spawn_positions:
  ; Spawn ID, room index, rotation, X pos, Y pos, Z pos
  ; WT entrance
  .byte 15, 0xF
  .short 0x94A0
  .float -3651.02, 1557.67, 13235.2
  ; First WT warp pot
  .byte 22, 0
  .short 0x4000
  .float -4196.33, 754.518, 7448.5
  ; Second WT warp pot
  .byte 23, 2
  .short 0xB000
  .float 668.107, 1550, 2298.75
  ; Third WT warp pot
  .byte 24, 12
  .short 0xC000
  .float 14203.1, -5062.49, 8948.05
  ; Inter-dungeon warp pot in WT
  .byte 69, 3
  .short 0x4000
  .float -4146.65, 1100, 47.88
.close




; When the player enters Earth Temple, reset Medli's position to the starting room, or to near the warp pot the player exited.
; This is to prevent an issue where the player can't get past the first room without Medli unless they have Deku Leaf.
.open "files/rels/d_a_npc_md.rel" ; Medli
.org 0xDB4
  bl reset_medli_position_to_start_of_dungeon
.org 0xD94 ; This line originally stopped Medli from spawning if the partner ID number (803C4DC3) was not set to 2.
  ; Remove the line so that Medli spawns in, even after taking an inter-dungeon warp pot.
  nop
.org @NextFreeSpace
.global reset_medli_position_to_start_of_dungeon
reset_medli_position_to_start_of_dungeon:
  stwu sp, -0x10 (sp)
  mflr r0
  stw r0, 0x14 (sp)
  
  lis r8, 0x803C9D44@ha ; Most recent spawn ID the player spawned from
  addi r8, r8, 0x803C9D44@l
  lha r8, 0 (r8)
  
  ; Search through the list of places Medli can spawn from to see which one corresponds to the player's last spawn ID, if any.
  lis r9, medli_possible_et_spawn_positions@ha
  addi r9, r9, medli_possible_et_spawn_positions@l
  li r0, 5 ; 5 possible spawn points
  mtctr r0
  medli_spawn_point_search_loop_start:
  lbz r0, 0 (r9) ; Spawn ID
  cmpw r0, r8
  beq reset_medli_found_matching_spawn_point ; Found the array element corresponding to this spawn ID
  addi r9, r9, 0x10 ; Increase pointer to point to next element
  bdnz medli_spawn_point_search_loop_start ; Loop
  
  ; The player came from a spawn that doesn't correspond to any of the elements in the array, don't change Medli's position.
  b after_resetting_medli_position
  
  reset_medli_found_matching_spawn_point:
  lwz r8, 4 (r9) ; X pos
  stw r8, 0 (r5)
  lwz r8, 8 (r9) ; Y pos
  stw r8, 4 (r5)
  lwz r8, 0xC (r9) ; Z pos
  stw r8, 8 (r5)
  
  lha r8, 2 (r9) ; Rotation
  sth r8, 0xC (r5)
  mr r6, r8 ; Argument r6 to setRestartOption needs to be the rotation
  mr r31, r8 ; Also modify the local variable rotation in Medli's code (for when she calls set__19dSv_player_priest)
  
  lbz r8, 1 (r9) ; Room index
  stb r8, 0xE (r5)
  mr r7, r8 ; Argument r7 to setRestartOption needs to be the room index
  mr r30, r8 ; Also modify the local variable room index in Medli's code (for when she calls set__19dSv_player_priest)
  
  after_resetting_medli_position:
  
  bl setRestartOption__13dSv_restart_cFScP4cXyzsSc ; Replace the function call we overwrote to call this custom function
  
  lwz r0, 0x14 (sp)
  mtlr r0
  addi sp, sp, 0x10
  blr

.global medli_possible_et_spawn_positions
medli_possible_et_spawn_positions:
  ; Spawn ID, room index, rotation, X pos, Y pos, Z pos
  ; ET entrance
  .byte 0, 0
  .short 0x8000
  .float -7215.21, -200, 5258.79
  ; First ET warp pot
  .byte 22, 2
  .short 0xE000
  .float -2013.11, 200, -1262.97
  ; Second ET warp pot
  .byte 23, 6
  .short 0x8000
  .float 4750, 350, -2251.06
  ; Third ET warp pot
  .byte 24, 15
  .short 0xE000
  .float -2371.38, -2000, 8471.54
  ; Inter-dungeon warp pot in ET
  .byte 69, 1
  .short 0
  .float -8010, 1000, -1508.94
.close




; If a Moblin sees you when you have no sword equipped, it will catch you and bring you to the jail cell in FF1.
; Skip all the sword checks and pretend the player does have a sword so that this doesn't happen.
.open "files/rels/d_a_mo2.rel" ; Moblin
.org 0xBF2C ; Start of sword checks in daMo2_Create__FP10fopAc_ac_c
  b 0xBF8C ; Skip all 4 sword checks
.org 0xAD70 ; Start of sword checks in daMo2_Execute__FP9mo2_class
  b 0xADD0 ; Skip all 4 sword checks
.close




; Make invisible walls that appear only when you have no sword never appear so swordless works better.
.open "files/rels/d_a_obj_akabe.rel" ; Invisible wall
.org 0x650 ; In chk_appear__Q210daObjAkabe5Act_cFv
  ; This code is run for invisible walls that have their switch index set to FF - an invalid switch used to indicate that the player's sword should be checked instead.
  ; We make chk_appear always return false.
  li r3, 0
.close




; Allow pigs to be enraged when the player has no sword equipped.
.open "files/rels/d_a_kb.rel" ; Pigs
.org 0x1460 ; In pl_attack_hit_check__FP8kb_class
  ; Make branch for having a sword unconditional
  b 0x146C
.org 0x3C1C ; In carry_move__FP8kb_class
  ; Remove branch for if you have no sword
  nop
.close




; Hide the blue main quest markers from the sea chart.
.open "sys/main.dol"
.org 0x801B14C4 ; checkMarkCheck1__12dMenu_Fmap_cFv
  ; Make the function that handles early-game quest markers return instantly.
  blr
.org 0x801B1684 ; checkMarkCheck2__12dMenu_Fmap_cFv
  ; Make the function that handles late-game quest markers return instantly.
  blr
.close




; Fixes new game+ so that picto box related things aren't flagged as done already.
; (Note: There are some more things the new game+ initialization function besides these ones that seem like they could potentially cause other issues, but I can't figure out exactly what they're doing, so I'm not removing them for now.)
.open "sys/main.dol"
.org 0x8005D78C ; reinit__10dSv_info_cFv
  ; Don't set Lenzo's event register to 07, causing his assistant quest to be complete.
  nop
.org 0x8005D7A4 ; reinit__10dSv_info_cFv
  ; Don't set the Windfall jail chest open flag, or you wouldn't be able to get the item inside it.
  nop
.org 0x8005D7FC ; reinit__10dSv_info_cFv
  ; Don't put the deluxe picto box in the player's inventory.
  nop
.org 0x8005D81C ; reinit__10dSv_info_cFv
  ; Don't set the bit for owning the regular picto box.
  nop
.org 0x8005D82C ; reinit__10dSv_info_cFv
  ; Don't set the bit for owning the deluxe picto box.
  nop
.close




; Make the stone door and whirlpool blocking Jabun's cave appear even when the Endless Night event bit is not set.
.open "files/rels/d_a_obj_ajav.rel" ; Big stone door blocking the entrance to Jabun's cave
.org 0x1568 ; Branch taken if Endless Night event bit is not set
  nop ; Remove it
.close
.open "files/rels/d_a_obj_auzu.rel" ; Whirlpool outside Jabun's cave
.org 0x580 ; In is_exist__Q29daObjAuzu5Act_cCFv
  b 0x5B0 ; Skip over the Endless Night event bit check and just always return true
.close




; Make Komali disappear from his room from the start, instead of waiting until after you own Din's Pearl.
; This is so there aren't two Komali's in the game at the same time.
.open "files/rels/d_a_npc_co1.rel" ; Young Komali
.org 0x498 ; Where he would normally check if you own Din's Pearl to know if he should disappear yet or not
  li r31, 0 ; Set the return value to false
  b 0x4E8 ; Change the conditional branch to unconditional
.close




; Prevent the lava outside the entrance to DRC from solidifying once you own Din's Pearl.
; This is so the puzzle with throwing the bomb flowers doesn't become pointless.
.open "files/rels/d_a_obj_eayogn.rel" ; Solidified lava object
.org 0x40C ; Start of check_ev_bit__13daObjEayogn_cCFv
  ; Always return false
  li r3, 0
  blr
.close




; Always spawn the Moblins and Darknuts inside Hyrule Castle.
.open "sys/main.dol"
.org 0x80052668 ; In getLayerNo
  b 0x80052850 ; Skip checking various event bits and the number of triforce shards owned, just always use the same layer
.close




; Originally the Windfall bomb shop owner only lowers the price of the bombs he sells to be reasonable after you have obtained Nayru's Pearl.
; Remove these checks so he always sells them at the lower prices from the start of the game.
; Note: Technically this shop owner is not properly coded to refuse to sell bombs to the player if they don't own the bombs upgrade yet.
; However, this doesn't matter in practice because he will only sell you bombs if you have less than your maximum, and there is no way to use them up and get less than your maximum until you own the bombs upgrade.
; The only side effect of this is that his purchase error message will be the same as if you were simply full on bombs ("you just can't carry that much"), but that accurate enough that it's fine.
.open "files/rels/d_a_npc_bms1.rel" ; Bomb-Master Cannon (Windfall bomb shop owner)
.org 0x1B9C ; In daNpc_Bms1_c::shop_talk(void)
  li r3, 1
.org 0x2064 ; In daNpc_Bms1_c::CreateInit(void)
  li r3, 1
.org 0x20B4 ; In daNpc_Bms1_c::CreateInit(void)
  li r3, 1
.org 0x36A0 ; In daNpc_Bms1_c::_create(void)
  li r3, 1
.org 0x36EC ; In daNpc_Bms1_c::_create(void)
  li r3, 1
.org 0x3E3C ; In daNpc_Bms1_c::CreateHeap(void)
  li r3, 1
.close




; Make it easier to have the Great Deku Tree mark the Koroks on your sea chart.
; In vanilla you would have to exit Forest Haven while you own Farore's Pearl, then re-enter and
; talk to the Deku Tree, specifically choosing the option to ask about the Island Koroks.
; We skip a couple of checks and go straight to the dialogue tree so that just talking to the Deku
; Tree and asking about the Island Koroks is enough.
.open "files/rels/d_a_npc_de1.rel" ; Great Deku Tree
.org 0xDB0 ; In daNpc_De1_c::getMsg
  b 0xE18
.close
