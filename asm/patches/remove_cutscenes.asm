
; This patch removes various hardcoded cutscenes from the game.


; nop out a couple lines so the long intro movie is skipped.
.open "sys/main.dol"
.org 0x80232C78
  nop
.org 0x80232C88
  nop
.close




; This makes the warps out of boss rooms always skip the cutscene usually shown the first time you beat the boss and warp out.
.open "files/rels/d_a_warpf.rel" ; Warp out of boss object
.org 0xC3C
  ; Function C3C of d_a_warpf.rel is checking if the post-boss cutscene for this dungeon has been viewed yet or not.
  ; Change it to simply always return true, so that it acts like it has been viewed from the start.
  li r3, 1
  blr
.close




; Remove the cutscene where the Tower of the Gods rises out of the sea.
; To do this we modify the goddess statue's code to skip starting the raising cutscene.
; Instead we branch to code that ends the current pearl-placing event after the tower raised event bit is set.
.open "files/rels/d_a_obj_doguu.rel" ; Goddess statues
.org 0x267C
  b 0x26A0
.close




; In order to get rid of the cutscene where the player warps down to Hyrule 3, we set the HYRULE_3_WARP_CUTSCENE event bit in the custom function for initializing a new game.
; But then that results in the warp appearing even before the player should unlock it.
; So we replace a couple places that check that event bit to instead call a custom function that returns whether the warp should be unlocked or not.
.open "files/rels/d_a_warpdm20.rel" ; Hyrule warp object
.org 0x634
  bl check_hyrule_warp_unlocked
.org 0xB50
  bl check_hyrule_warp_unlocked
.close




; Change the conditions that cause certain letters to be sent to Link so they don't depend on seeing cutscenes.
.open "files/rels/d_a_obj_toripost.rel" ; Mailbox
.org 0x1B0C
  ; In vanilla, Orca's letter is sent when you watch a cutscene on Greatfish Isle.
  ; That cutscene is removed, so change it to be sent when you kill Kalle Demos.
  li r3, 4
.org 0x1B10
  bl dComIfGs_isStageBossEnemy__Fi
.close
.open "sys/main.dol"
.org 0x80197ADC
  ; In vanilla, Aryll's letter is sent after watching a cutscene in Hyrule 2.
  ; That cutscene is removed, so change it to be after killing Helmaroc King.
  li r3, 2
  bl dComIfGs_isStageBossEnemy__Fi
.org 0x80197AFC
  ; In vanilla, Tingle's letter is sent after watching a cutscene in Hyrule 2 and rescuing Tingle.
  ; That cutscene is removed, so change it to be after killing Helmaroc King and rescuing Tingle.
  ; Change when Tingle's letter is sent.
  li r3, 2
  bl dComIfGs_isStageBossEnemy__Fi
.close




; Modify the code for warping with the Ballad of Gales to get rid of the cutscene that accompanies it.
.open "files/rels/d_a_ship.rel"
.org 0x7A10
  ; Get rid of the line that checks if KoRL has reached a high enough Y pos to start the warp yet.
  nop
.org 0x7680
  ; Get rid of the line that plays the warping music, since it would continue playing after the warp has happened.
  nop
.close




; Remove song replays, where Link plays a fancy animation to conduct the song after the player plays it.
.open "sys/main.dol"
.org 0x8014ECE0
  ; Originally checked if the "You conducted..." text box has disappeared.
  ; Remove that check.
  nop
.org 0x8014EF28
  ; Originally checked if Link's conducting animation has finished playing.
  ; Remove that check.
  nop
.close




; Change Tott to only dance once to teach you the Song of Passing, instead of twice.
.open "files/rels/d_a_npc_tt.rel"
.org 0xC68
  li r0, 1 ; Number of full dance repetitions to do
.close




; Change the NPC version of Makar that spawns when you kill Kalle Demos to not initiate the event where he talks to you and thanks you for saving him.
; In addition to being unnecessary, that cutscene has an extremely small chance of softlocking the game even in vanilla.
.open "files/rels/d_a_npc_cb1.rel" ; Makar
.org 0x80B8
  ; This line originally called isStageBossEnemy to see if he's being spawned during Kalle Demos's death or afterwards.
  ; Change it to always be true, which tricks Makar into thinking he's being spawned after Kalle Demos's death in both instances.
  li r3, 1
.close




; Modify the item get funcs for the 3 pearls to call custom functions that automatically place the pearls as soon as you get them.
.open "sys/main.dol"
.org 0x800C43F4 ; In item_func_pearl1__Fv
  bl give_pearl_and_raise_totg_if_necessary
.org 0x800C4424 ; In item_func_pearl2__Fv
  bl give_pearl_and_raise_totg_if_necessary
.org 0x800C4454 ; In item_func_pearl3__Fv
  bl give_pearl_and_raise_totg_if_necessary
.close




; After you kill Puppet Ganon, he would normally respawn you in his room but override the layer to be layer 9 for the cutscene there.
; We set the switch for having already seen that cutscene in the new game initialization code, but then the rope you need to climb doesn't appear because the layer is wrong.
; We remove the layer override from Puppet Ganon's call to setNextStage.
.open "files/rels/d_a_bgn.rel" ; Puppet Ganon
.org 0xB1E0
  li r6, -1 ; No layer override
.close




; Change all treasure chests to open quickly.
; Removes the build up music, uses the short opening event instead of the long dark room event, and use the short chest opening animation.
; This change also fixes the bug where the player can duplicate items by using storage on the non-wooden chests.
.open "files/rels/d_a_tbox.rel" ; Treasure chests
.org 0x279C ; In actionOpenWait__8daTbox_cFv
  b 0x2800
.org 0x2870 ; In actionOpenWait__8daTbox_cFv
  nop
.org 0x3D2E ; File ID of the bck animation to use for chest type 1
  .short 9 ; Was originally 8 (long chest opening anim)
.org 0x3D3A ; File ID of the bck animation to use for chest type 2
  .short 9 ; Was originally 8 (long chest opening anim)
.org 0x3D46 ; File ID of the bck animation to use for chest type 3
  .short 9 ; Was originally 8 (long chest opening anim)
.close




; Change the item get sound used when opening a wooden chest to the good item sound instead of the bad item sound.
; Because of the above change where all chests were given the wooden chest event, this also affects non-wooden chests too.
; To do this we change the code that decides what item get sound to play to ignore prm0 to Link's 010open_treasure.
.open "sys/main.dol"
.org 0x8012E3A4 ; In setGetItemSound__9daPy_lk_cFUsi
  b 0x8012E3E8
.close




; Prevent Ivan from automatically triggering the cutscene where the Killer Bees tell you about Mrs. Marie's birthday and the Joy Pendant in the tree.
; (It can still be manually triggered by talking to any of the Killer Bees, in case you actually want to activate the Joy Pendant in the tree.)
.open "files/rels/d_a_npc_mk.rel" ; Ivan
.org 0x2F80
  b 0x2FD8
.close
