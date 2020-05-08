
; This patch contains fixes to various bugs present in vanilla Wind Waker.


; If the player heals grandma but doesn't have an empty bottle for her to put soup in because they swapped their equipped item out too fast, grandma will crash the game because she tries to say a message that doesn't exist in the game's script.
; Change grandma to say the same message regardless of whether you have an empty bottle or not.
.open "files/rels/d_a_npc_ba1.rel" ; Grandma
.org 0x16DC
  ; This line originally hardcoded message ID 2041, which would be the message grandma says when you heal her without an empty bottle.
  ; Change it to 2037, which is the normal message ID when you do have an empty bottle.
  li r0, 2037
.close




; Fix a crash when you look at the broken shards of Helmaroc King's mask with the hookshot.
.open "sys/main.dol"
.org 0x800F13A8 ; In daHookshot_rockLineCallback
  b hookshot_sight_failsafe_check
.close




; If you try to challenge Orca when you have no sword equipped, the game will crash.
; This is because he tries to create the counter in the lower left corner of the screen for how many hits you've gotten, but that counter needs a sword icon, and the sword icon texture is not loaded in when you have no sword equipped.
; So change it so he doesn't create a counter at all when you have no sword.
.open "files/rels/d_a_npc_ji1.rel" ; Orca
.org 0xC914
  cmpwi r0, 0x38 ; Hero's Sword
  beq 0xC938 ; Use Hero's Sword icon for the counter (icon 1)
  cmpwi r0, 0xFF ; No sword
  beq 0xC96C ; Skip past the code to create the counter entirely
  b 0xC948 ; Use Master Sword icon for the counter (icon 2)
.close




; Don't allow Beedle to buy Blue Chu Jelly, as selling that can make getting the Blue Potion from Doc Bandam impossible.
.open "files/rels/d_a_npc_bs1.rel" ; Beedle
.org 0x214C
  b 0x21DC ; Make Beedle not consider Blue Chu Jelly to be a spoil
.close




; Auto-equip the Deluxe Picto Box when obtaining it.
.open "sys/main.dol"
.org 0x800C3420 ; In item_func_camera2__Fv (Deluxe Picto Box item get func)
  b deluxe_picto_box_item_func_fix_equipped_picto_box
.close




; Delete Morths that fall out-of-bounds.
.open "files/rels/d_a_ks.rel" ; Morth
.org 0x678 ; In naraku_check__FP8ks_class
  ; This function was originally intended to delete Morths that fall into pits that cause Link to void out.
  ; We tweak it so that, instead of ignoring when the Morth has no collision below it, it runs the same deletion code in that case as when it has void-out-collision under it.
  beq 0x6b0
.close




; Fix a vanilla bug where cutting Stalfos in half and then hitting the upper body with light arrows would make the lower body permanently unkillable.
.open "files/rels/d_a_st.rel" ; Stalfos
.org 0x85CC
  bl stalfos_kill_lower_body_when_upper_body_light_arrowed
.close




; Fix a vanilla bug where Miniblins killed with light arrows will not set their death switch.
; (Note: This fix still does not fix the case where the Miniblin is supposed to set switch index 0 on death, but there are no Miniblins in the game that are supposed to set that, so it doesn't matter.)
.open "files/rels/d_a_pt.rel" ; Miniblin
.org 0x4B44
  bl miniblin_set_death_switch_when_light_arrowed
.close




; Fix a vanilla bug where Jalhalla's child Poes would not tell Jalhalla they died when hit by light arrows.
.open "files/rels/d_a_pw.rel" ; Poe
.org 0x8CC
  ; Remove a check that the Poe's HP must be <= 0 for it to be considered dead by Jalhalla.
  ; We're going to add this back in our custom code, we just need to remove it here so the original code reaches the function call we hijack to insert custom code, so that we can have it check (HP <= 0 || isDyingToLightArrows).
  b 0x8D8
.org 0x900
  bl poe_fix_light_arrows_bug
.org 0x904
  ; Our custom function replaces the entire rest of this function, so just return after the custom function finished.
  lwz r31, 0x1C (r1)
  lwz r0, 0x24 (r1)
  mtlr r0
  addi r1, r1, 0x20
  blr
.close




; Fix a vanilla bug where respawning Magtails would not respawn if you shoot their head with Light Arrows.
.open "files/rels/d_a_mt.rel" ; Magtail
.org 0x6000
  bl magtail_respawn_when_head_light_arrowed
.org 0x6004
  ; Then remove some lines of code after the function call we had to move into the custom function.
  nop
  nop
  nop
  nop
  nop
.close




; Fixes Phantom Ganon 1's hardcoded fight trigger region in FF2 to check Link's Y position.
; This is so it doesn't trigger when the player is much higher than Phantom Ganon, and is trying to go fight Helmaroc.
.open "files/rels/d_a_fganon.rel"
.org 0x4F50
  b phantom_ganon_check_link_within_y_diff

.org @NextFreeSpace
.global phantom_ganon_check_link_within_y_diff
phantom_ganon_check_link_within_y_diff:
  lfs f4, 0x1C (sp) ; Read the Y difference between Link and Phantom Ganon
  lfs f3, 0x88 (r31) ; Read the float constant 1000.0 from 0xA918
  
  ; If the Link is 1000.0 units or more higher than PG, do not trigger the fight.
  ; (Does not account for negative difference. Still extends infinitely downwards.)
  fcmpo cr0, f4, f3
  bge phantom_ganon_check_link_within_y_diff_outside_range
  
  ; Otherwise, go on to check the X and Z difference as usual.
  fmuls f1, f1, f1 ; Replace the line of code we overwrote to jump here
  b 0x4F54

phantom_ganon_check_link_within_y_diff_outside_range:
  b 0x5204
.close




; Reduce Game heap memory fragmentation on the sea by giving a maximum memory estimate for island LoD models.
.open "files/rels/d_a_lod_bg.rel" ; Background island LoD model actor
.org 0xDCC
  ;li r5, 0x4B0 ; For most islands
  ;li r5, 0x970 ; Forsaken Fortress (before it's destroyed - afterwards it uses 0x4B0)
  li r5, 0xEF0 ; Windfall
; Fix useless warnings in the console caused by trying to call JKRHeap::free on a solid heap
.org 0x478
  nop
.org 0x4D0
  nop
.close
