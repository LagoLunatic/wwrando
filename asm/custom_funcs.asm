
.open "sys/main.dol"
.org 0x803FCFA8

.global init_save_with_tweaks
init_save_with_tweaks:
; Function start stuff
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)


bl init__10dSv_save_cFv ; To call this custom func we overwrote a call to init__10dSv_save_cFv, so call that now.


lis r5, sword_mode@ha
addi r5, r5, sword_mode@l
lbz r5, 0 (r5)
cmpwi r5, 0 ; Start with Sword
beq start_with_sword
cmpwi r5, 2 ; Swordless
beq break_barrier_for_swordless
b after_sword_mode_initialization

start_with_sword:
bl item_func_sword__Fv
b after_sword_mode_initialization

break_barrier_for_swordless:
lis r3, 0x803C522C@ha
addi r3, r3, 0x803C522C@l
li r4, 0x2C02 ; BARRIER_DOWN
bl onEventBit__11dSv_event_cFUs
li r4, 0x3B08 ; Another event flag set by the barrier. This one seems to have no effect, but set it anyway just to be safe.
bl onEventBit__11dSv_event_cFUs

after_sword_mode_initialization:


bl item_func_shield__Fv
bl item_func_normal_sail__Fv
bl item_func_wind_tact__Fv ; Wind Waker
bl item_func_tact_song1__Fv ; Wind's Requiem
bl item_func_tact_song2__Fv ; Ballad of Gales
bl item_func_tact_song6__Fv ; Song of Passing
bl item_func_pirates_omamori__Fv ; Pirate's Charm


lis r3, 0x803C522C@ha
addi r3, r3, 0x803C522C@l
li r4, 0x3510 ; HAS_SEEN_INTRO
bl onEventBit__11dSv_event_cFUs
li r4, 0x0520 ; GOSSIP_STONE_AT_FF1 (Causes Aryll and the pirates to disappear from Outset)
bl onEventBit__11dSv_event_cFUs
li r4, 0x2E01 ; WATCHED_MEETING_KORL_CUTSCENE (Necessary for Windfall music to play when warping there)
bl onEventBit__11dSv_event_cFUs
li r4, 0x0F80 ; KORL_UNLOCKED_AND_SPAWN_ON_WINDFALL
bl onEventBit__11dSv_event_cFUs
li r4, 0x0908 ; SAIL_INTRODUCTION_TEXT_AND_MAP_UNLOCKED
bl onEventBit__11dSv_event_cFUs
li r4, 0x2A08 ; ENTER_KORL_FOR_THE_FIRST_TIME_AND_SPAWN_ANYWHERE
bl onEventBit__11dSv_event_cFUs
li r4, 0x0902 ; SAW_DRAGON_ROOST_ISLAND_INTRO
bl onEventBit__11dSv_event_cFUs
li r4, 0x1F40 ; SAW_QUILL_CUTSCENE_ON_DRI
bl onEventBit__11dSv_event_cFUs
li r4, 0x0A80 ; KORL_DINS_PEARL_TEXT_ALLOWING_YOU_TO_ENTER_HIM
bl onEventBit__11dSv_event_cFUs
li r4, 0x0901 ; TRIGGERED_MAP_FISH
bl onEventBit__11dSv_event_cFUs
li r4, 0x0A20 ; WATCHED_FOREST_HAVEN_INTRO_CUTSCENE
bl onEventBit__11dSv_event_cFUs
li r4, 0x1801 ; WATCHED_DEKU_TREE_CUTSCENE
bl onEventBit__11dSv_event_cFUs
li r4, 0x0A08 ; TALKED_TO_KORL_AFTER_LEAVING_FH
bl onEventBit__11dSv_event_cFUs
li r4, 0x0808 ; Needed so that exiting the pirate ship takes you to Windfall instead of the tutorial
bl onEventBit__11dSv_event_cFUs
li r4, 0x1F02 ; TALKED_TO_KORL_AFTER_GETTING_BOMBS
bl onEventBit__11dSv_event_cFUs
li r4, 0x2F20 ; Talked to KoRL after getting Nayru's Pearl
bl onEventBit__11dSv_event_cFUs
li r4, 0x3840 ; TALKED_TO_KORL_POST_TOWER_CUTSCENE
bl onEventBit__11dSv_event_cFUs
li r4, 0x2D04 ; MASTER_SWORD_CUTSCENE
bl onEventBit__11dSv_event_cFUs
li r4, 0x3802 ; COLORS_IN_HYRULE
bl onEventBit__11dSv_event_cFUs
li r4, 0x2D01 ; Saw cutscene before Helmaroc King where Aryll is rescued
bl onEventBit__11dSv_event_cFUs
li r4, 0x2D02 ; TETRA_TO_ZELDA_CUTSCENE
bl onEventBit__11dSv_event_cFUs
li r4, 0x3201 ; KoRL told you about the sages
bl onEventBit__11dSv_event_cFUs
li r4, 0x3380 ; KoRL told you about the Triforce shards
bl onEventBit__11dSv_event_cFUs
li r4, 0x1001 ; WATCHED_FIRE_AND_ICE_ARROWS_CUTSCENE
bl onEventBit__11dSv_event_cFUs
li r4, 0x2E04 ; MEDLI_IN_EARTH_TEMPLE_ENTRANCE
bl onEventBit__11dSv_event_cFUs
li r4, 0x2920 ; MEDLI_IN_EARTH_TEMPLE
bl onEventBit__11dSv_event_cFUs
li r4, 0x1620 ; Medli is in dungeon mode and can be lifted/called
bl onEventBit__11dSv_event_cFUs
li r4, 0x2910 ; MAKAR_IN_WIND_TEMPLE
bl onEventBit__11dSv_event_cFUs
li r4, 0x1610 ; Makar is in dungeon mode and can be lifted/called
bl onEventBit__11dSv_event_cFUs
li r4, 0x3A20 ; Fishman and KoRL talked about Forsaken Fortress after you beat Molgera
bl onEventBit__11dSv_event_cFUs
li r4, 0x2D08 ; HYRULE_3_WARP_CUTSCENE
bl onEventBit__11dSv_event_cFUs
li r4, 0x3980 ; HYRULE_3_ELECTRICAL_BARRIER_CUTSCENE_1
bl onEventBit__11dSv_event_cFUs
li r4, 0x3B02 ; Saw cutscene before Puppet Ganon fight
bl onEventBit__11dSv_event_cFUs
li r4, 0x4002 ; Saw cutscene before Ganondorf fight
bl onEventBit__11dSv_event_cFUs

lis r3, 0x803C5D60@ha
addi r3, r3, 0x803C5D60@l
li r4, 0x0310 ; Saw event where Grandma gives you the Hero's Clothes
bl onEventBit__11dSv_event_cFUs


; Set four switch bits (0, 1, 3, 7) for several events that happen in the Fairy Woods on Outset.
; Setting these switches causes the Tetra hanging from a tree and rescuing her from Bokoblins events to be marked as finished.
; Also set the switch (9) for having seen the event where you enter the Rito Aerie for the first time and get the Delivery Bag.
; Also set the switch (8) for having unclogged the pond, since that boulder doesn't respond to normal bombs which would be odd.
; Also set the the switch (1E) for having seen the intro to the interior of the Forest Haven, where the camera pans up.
; Also set the the switch (13) for having seen the camera panning towards the treasure chest in Windfall Town Jail.
lis r3, 0x803C5114@ha
addi r3, r3, 0x803C5114@l
lis r4, 0x4008
addi r4, r4, 0x038B
stw r4, 4 (r3)

; Set two switch bits (3E and 3F) for having unlocked the song tablets in the Earth and Wind Temple entrances.
lis r4, 0xC000
stw r4, 8 (r3)

; Set a switch bit (19) for the event on Greatfish Isle so that the endless night never starts.
lis r3, 0x803C4F88@ha
addi r3, r3, 0x803C4F88@l
lis r4, 0x0200
stw r4, 4 (r3)
; Also set a switch bit (3F) for having seen the Windfall Island intro scene.
lis r4, 0x8000
stw r4, 8 (r3)
; Also set a switch bit (58) for having seen the short event when you enter Forsaken Fortress 2 for the first time.
lis r4, 0x0100
stw r4, 0xC (r3)

; If the player does the early part of Dragon Roost Cavern backwards, they can walk through a door while it's still blocked off by a boulder. This softlocks the game as Link will just walk into the boulder infinitely.
; Set a switch (5) for having destroyed the boulder in front of the door so that doesn't happen.
lis r3, 0x803C4FF4@ha ; Dragon Roost Cavern stage info.
addi r3, r3, 0x803C4FF4@l
li r4, 0x0020
stw r4, 4 (r3)
; Also set a switch (21) for having seen the gossip stone event where KoRL tells you about giving bait to rats.
li r4, 0x0002
stw r4, 8 (r3)

; Set a switch (2A) for having seen the gossip stone event where KoRL tells you Medli shows up on the compass.
lis r3, 0x803C5060@ha ; Earth Temple stage info.
addi r3, r3, 0x803C5060@l
li r4, 0x0400
stw r4, 8 (r3)

; Set a switch (12) for having seen the camera moving around event when you first enter Hyrule.
; Also set a switch (6) for having completed the Triforce pushable blocks puzzle.
lis r3, 0x803C50CC@ha ; Hyrule stage info.
addi r3, r3, 0x803C50CC@l
lis r4, 0x0004
addi r4, r4, 0x0040
stw r4, 4 (r3)

; Set a switch (0D) for having seen the camera panning around when you first enter Ganon's Tower.
; Also set a switch (1C) for having seen the camera panning around looking at the 4 lights in the room where you can drop down to the maze.
; Also set a switch (1D) for having seen the camera panning around looking at the 4 boomerang switches in the room with the warp up to Forsaken Fortress.
; Also set a switch (1E) for having seen the cutscene before the Puppet Ganon fight.
; Also set a switch (12) for having seen the cutscene after the Puppet Ganon fight.
; Also set a switch (1F) for having seen the cutscene before the Ganondorf fight.
lis r3, 0x803C50A8@ha ; Ganon's Tower stage info.
addi r3, r3, 0x803C50A8@l
lis r4, 0xF004
addi r4, r4, 0x2000
stw r4, 4 (r3)


li r3, 3 ; DRC stage ID
li r4, 5 ; Seen the boss intro bit index
bl generic_on_dungeon_bit
li r3, 4 ; FW stage ID
li r4, 5 ; Seen the boss intro bit index
bl generic_on_dungeon_bit
li r3, 5 ; TotG stage ID
li r4, 5 ; Seen the boss intro bit index
bl generic_on_dungeon_bit
li r3, 6 ; ET stage ID
li r4, 5 ; Seen the boss intro bit index
bl generic_on_dungeon_bit
li r3, 7 ; WT stage ID
li r4, 5 ; Seen the boss intro bit index
bl generic_on_dungeon_bit


; Start the player with 30 bombs and arrows. (But not the ability to actually use them.)
; This change is so we can remove the code that sets your current bombs/arrows to 30 when you first get the bombs/bow.
; That code would be bad if the player got a bomb bag/quiver upgrade beforehand, as then that code would reduce the max.
lis r3, 0x803C
addi r3, r3, 0x4C71
li r4, 30
stb r4, 0 (r3) ; Current arrows
stb r4, 1 (r3) ; Current bombs
stb r4, 6 (r3) ; Max arrows
stb r4, 7 (r3) ; Max bombs

; Start the player with a magic meter so items that use it work correctly.
lis r3, 0x803C
addi r3, r3, 0x4C1B
li r4, 16 ; 16 is the normal starting size of the magic meter.
stb r4, 0 (r3) ; Max magic meter
stb r4, 1 (r3) ; Current magic meter

; Make the game think the player has previously owned every type of spoil and bait so they don't get the item get animation the first time they pick each type up.
lis r3, 0x803C4C9C@ha
addi r3, r3, 0x803C4C9C@l
li r4, 0xFF
stb r4, 0 (r3) ; 803C4C9C, bitfield of what spoils bag items you've ever owned
stb r4, 1 (r3) ; 803C4C9D, bitfield of what bait bag items you've ever owned

; Give the player the number of Triforce Shards they want to start with.
lis r5, num_triforce_shards_to_start_with@ha
addi r5, r5, num_triforce_shards_to_start_with@l
lbz r5, 0 (r5) ; Load number of Triforce Shards to start with
lis r3, 0x803C4CC6@ha ; Bitfield of Triforce Shards the player owns
addi r3, r3, 0x803C4CC6@l
; Convert the number of shards to a bitfield with that many bits set.
; e.g. For 5 shards, ((1 << 5) - 1) results in 0x1F (binary 00011111).
li r0, 1
slw r4, r0, r5
subi r4, r4, 1
stb r4, 0 (r3) ; Store the bitfield of shards back
; If the number of starting shards is 8, also set the event flag for seeing the Triforce refuse together.
cmpwi r5, 8
blt after_starting_triforce_shards
lis r3, 0x803C522C@ha
addi r3, r3, 0x803C522C@l
li r4, 0x3D04 ; Saw the Triforce refuse
bl onEventBit__11dSv_event_cFUs
after_starting_triforce_shards:


lis r5, should_start_with_heros_clothes@ha
addi r5, r5, should_start_with_heros_clothes@l
lbz r5, 0 (r5) ; Load bool of whether player should start with Hero's clothes
cmpwi r5, 1
bne after_starting_heros_clothes
lis r3, 0x803C522C@ha
addi r3, r3, 0x803C522C@l
li r4, 0x2A80 ; HAS_HEROS_CLOTHES
bl onEventBit__11dSv_event_cFUs
after_starting_heros_clothes:


lis r5, skip_rematch_bosses@ha
addi r5, r5, skip_rematch_bosses@l
lbz r5, 0 (r5) ; Load bool of whether rematch bosses should be skipped
cmpwi r5, 1
bne after_skipping_rematch_bosses
lis r3, 0x803C522C@ha
addi r3, r3, 0x803C522C@l
li r4, 0x3904 ; Recollection Gohma defeated
bl onEventBit__11dSv_event_cFUs
li r4, 0x3902 ; Recollection Kalle Demos defeated
bl onEventBit__11dSv_event_cFUs
li r4, 0x3901 ; Recollection Jalhalla defeated
bl onEventBit__11dSv_event_cFUs
li r4, 0x3A80 ; Recollection Molgera defeated
bl onEventBit__11dSv_event_cFUs
after_skipping_rematch_bosses:


; Function end stuff
lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr


.global num_triforce_shards_to_start_with
num_triforce_shards_to_start_with:
.byte 0 ; By default start with no Triforce Shards
.global should_start_with_heros_clothes
should_start_with_heros_clothes:
.byte 1 ; By default start with the Hero's Clothes
.global sword_mode
sword_mode:
.byte 0 ; By default Start with Sword
.global skip_rematch_bosses
skip_rematch_bosses:
.byte 1 ; By default skip them
.align 2 ; Align to the next 4 bytes




.global convert_progressive_item_id
convert_progressive_item_id:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

cmpwi r3, 0x38
beq convert_progressive_sword_id
cmpwi r3, 0x39
beq convert_progressive_sword_id
cmpwi r3, 0x3A
beq convert_progressive_sword_id
cmpwi r3, 0x3D
beq convert_progressive_sword_id
cmpwi r3, 0x3E
beq convert_progressive_sword_id

cmpwi r3, 0x27
beq convert_progressive_bow_id
cmpwi r3, 0x35
beq convert_progressive_bow_id
cmpwi r3, 0x36
beq convert_progressive_bow_id

cmpwi r3, 0xAB
beq convert_progressive_wallet_id
cmpwi r3, 0xAC
beq convert_progressive_wallet_id

cmpwi r3, 0xAD
beq convert_progressive_bomb_bag_id
cmpwi r3, 0xAE
beq convert_progressive_bomb_bag_id

cmpwi r3, 0xAF
beq convert_progressive_quiver_id
cmpwi r3, 0xB0
beq convert_progressive_quiver_id

cmpwi r3, 0x23
beq convert_progressive_picto_box_id
cmpwi r3, 0x26
beq convert_progressive_picto_box_id

b convert_progressive_item_id_func_end


convert_progressive_sword_id:
lis r3, 0x803C4CBC@ha
addi r3, r3, 0x803C4CBC@l
lbz r4, 0 (r3) ; Bitfield of swords you own
cmpwi r4, 0
beq convert_progressive_sword_id_to_normal_sword
cmpwi r4, 1
beq convert_progressive_sword_id_to_powerless_master_sword
cmpwi r4, 3
beq convert_progressive_sword_id_to_half_power_master_sword
cmpwi r4, 7
beq convert_progressive_sword_id_to_full_power_master_sword
li r3, 0x38 ; Invalid sword state; this shouldn't happen so just return the base sword ID
b convert_progressive_item_id_func_end

convert_progressive_sword_id_to_normal_sword:
li r3, 0x38
b convert_progressive_item_id_func_end
convert_progressive_sword_id_to_powerless_master_sword:
li r3, 0x39
b convert_progressive_item_id_func_end
convert_progressive_sword_id_to_half_power_master_sword:
li r3, 0x3A
b convert_progressive_item_id_func_end
convert_progressive_sword_id_to_full_power_master_sword:
li r3, 0x3E
b convert_progressive_item_id_func_end


convert_progressive_bow_id:
lis r3, 0x803C4C65@ha
addi r3, r3, 0x803C4C65@l
lbz r4, 0 (r3) ; Bitfield of arrow types you own
cmpwi r4, 0
beq convert_progressive_bow_id_to_heros_bow
cmpwi r4, 1
beq convert_progressive_bow_id_to_fire_and_ice_arrows
cmpwi r4, 3
beq convert_progressive_bow_id_to_light_arrows
li r3, 0x27 ; Invalid bow state; this shouldn't happen so just return the base bow ID
b convert_progressive_item_id_func_end

convert_progressive_bow_id_to_heros_bow:
li r3, 0x27
b convert_progressive_item_id_func_end
convert_progressive_bow_id_to_fire_and_ice_arrows:
li r3, 0x35
b convert_progressive_item_id_func_end
convert_progressive_bow_id_to_light_arrows:
li r3, 0x36
b convert_progressive_item_id_func_end


convert_progressive_wallet_id:
lis r3, 0x803C4C1A@ha
addi r3, r3, 0x803C4C1A@l
lbz r4, 0 (r3) ; Which wallet you have
cmpwi r4, 0
beq convert_progressive_wallet_id_to_1000_rupee_wallet
cmpwi r4, 1
beq convert_progressive_wallet_id_to_5000_rupee_wallet
li r3, 0xAB ; Invalid wallet state; this shouldn't happen so just return the base wallet ID
b convert_progressive_item_id_func_end

convert_progressive_wallet_id_to_1000_rupee_wallet:
li r3, 0xAB
b convert_progressive_item_id_func_end
convert_progressive_wallet_id_to_5000_rupee_wallet:
li r3, 0xAC
b convert_progressive_item_id_func_end


convert_progressive_bomb_bag_id:
lis r3, 0x803C4C72@ha
addi r3, r3, 0x803C4C72@l
lbz r4, 6 (r3) ; Max number of bombs the player can currently hold
cmpwi r4, 30
beq convert_progressive_bomb_bag_id_to_60_bomb_bomb_bag
cmpwi r4, 60
beq convert_progressive_bomb_bag_id_to_99_bomb_bomb_bag
li r3, 0xAD ; Invalid bomb bag state; this shouldn't happen so just return the base bomb bag ID
b convert_progressive_item_id_func_end

convert_progressive_bomb_bag_id_to_60_bomb_bomb_bag:
li r3, 0xAD
b convert_progressive_item_id_func_end
convert_progressive_bomb_bag_id_to_99_bomb_bomb_bag:
li r3, 0xAE
b convert_progressive_item_id_func_end


convert_progressive_quiver_id:
lis r3, 0x803C4C71@ha
addi r3, r3, 0x803C4C71@l
lbz r4, 6 (r3) ; Max number of arrows the player can currently hold
cmpwi r4, 30
beq convert_progressive_quiver_id_to_60_arrow_quiver
cmpwi r4, 60
beq convert_progressive_quiver_id_to_99_arrow_quiver
li r3, 0xAF ; Invalid bomb bag state; this shouldn't happen so just return the base bomb bag ID
b convert_progressive_item_id_func_end

convert_progressive_quiver_id_to_60_arrow_quiver:
li r3, 0xAF
b convert_progressive_item_id_func_end
convert_progressive_quiver_id_to_99_arrow_quiver:
li r3, 0xB0
b convert_progressive_item_id_func_end


convert_progressive_picto_box_id:
lis r3, 0x803C4C61@ha
addi r3, r3, 0x803C4C61@l
lbz r4, 0 (r3) ; Bitfield of picto boxes you own
cmpwi r4, 0
beq convert_progressive_picto_box_id_to_normal_picto_box
cmpwi r4, 1
beq convert_progressive_picto_box_id_to_deluxe_picto_box
li r3, 0x23 ; Invalid bomb bag state; this shouldn't happen so just return the base bomb bag ID
b convert_progressive_item_id_func_end

convert_progressive_picto_box_id_to_normal_picto_box:
li r3, 0x23
b convert_progressive_item_id_func_end
convert_progressive_picto_box_id_to_deluxe_picto_box:
li r3, 0x26
b convert_progressive_item_id_func_end


convert_progressive_item_id_func_end:
lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




.global convert_progressive_item_id_for_createDemoItem
convert_progressive_item_id_for_createDemoItem:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

mr r3, r26 ; createDemoItem keeps the item ID in r26
bl convert_progressive_item_id ; Get the correct item ID
mr r26, r3 ; Put it back where createDemoItem expects it, in r26

li r3, 259 ; And then simply replace the line of code in createDemoItem that we overwrote to call this function

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




.global convert_progressive_item_id_for_daItem_create
convert_progressive_item_id_for_daItem_create:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

lbz r3, 0xB3 (r31) ; Read this field item's item ID from its params (params are at 0xB0, the item ID is has the mask 0x000000FF)
bl convert_progressive_item_id ; Get the correct item ID
stb r3, 0xB3 (r31) ; Store the corrected item ID back into the field item's params

; Then we return the item ID in r0 so that the next few lines in daItem_create can use it.
mr r0, r3

lwz r3, 0x14 (sp)
mtlr r3
addi sp, sp, 0x10
blr




.global convert_progressive_item_id_for_dProcGetItem_init_1
convert_progressive_item_id_for_dProcGetItem_init_1:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

lwz r3, 0x30C (r28) ; Read the item ID property for this event action
bl convert_progressive_item_id ; Get the correct item ID

; Then we return the item ID in r0 so that the next few lines in dProcGetItem_init can use it.
mr r0, r3

lwz r3, 0x14 (sp)
mtlr r3
addi sp, sp, 0x10
blr




.global convert_progressive_item_id_for_dProcGetItem_init_2
convert_progressive_item_id_for_dProcGetItem_init_2:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

lbz r3, 0x52AC (r3) ; Read the item ID from 803C9EB4
bl convert_progressive_item_id ; Get the correct item ID

; Then we return the item ID in r27 so that the next few lines in dProcGetItem_init can use it.
mr r27, r3

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




.global convert_progressive_item_id_for_shop_item
convert_progressive_item_id_for_shop_item:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

; Replace the call to savegpr we overwrote to call this custom function
bl _savegpr_28
mr r30, r3 ; Preserve the shop item entity pointer

lbz r3, 0xB3 (r30)
bl convert_progressive_item_id ; Get the correct item ID
stb r3, 0x63A (r30) ; Store the item ID to shop item entity+0x63A

mr r3, r30 ; Put the shop item entity pointer back into r3, because that's where the function that called this one expects it to be

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




; Acts as a replacement to getSelectItemNo, but should only be called when the shopkeeper is checking if the item get animation should play or not, in order to have that properly show for progressive items past the first tier.
; If this was used all the time as a replacement for getSelectItemNo it would cause the shop to be buggy since it uses the item ID to know what slot it's on.
.global custom_getSelectItemNo_progressive
custom_getSelectItemNo_progressive:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

bl getSelectItemNo__11ShopItems_cFv
bl convert_progressive_item_id

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




.global progressive_sword_item_func
progressive_sword_item_func:
; Function start stuff
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

lis r3, 0x803C4CBC@ha
addi r3, r3, 0x803C4CBC@l
lbz r4, 0 (r3) ; Bitfield of swords you own
cmpwi r4, 0
beq get_normal_sword
cmpwi r4, 1
beq get_powerless_master_sword
cmpwi r4, 3
beq get_half_power_master_sword
cmpwi r4, 7
beq get_full_power_master_sword
b sword_func_end

get_normal_sword:
bl item_func_sword__Fv
b sword_func_end

get_powerless_master_sword:
bl item_func_master_sword__Fv
b sword_func_end

get_half_power_master_sword:
bl item_func_lv3_sword__Fv
b sword_func_end

get_full_power_master_sword:
bl item_func_master_sword_ex__Fv


sword_func_end:
; Function end stuff
lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




.global progressive_bow_func
progressive_bow_func:
; Function start stuff
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)


lis r3, 0x803C4C65@ha
addi r3, r3, 0x803C4C65@l
lbz r4, 0 (r3) ; Bitfield of arrow types you own
cmpwi r4, 0
beq get_heros_bow
cmpwi r4, 1
beq get_fire_and_ice_arrows
cmpwi r4, 3
beq get_light_arrows
b bow_func_end

get_heros_bow:
bl item_func_bow__Fv
b bow_func_end

get_fire_and_ice_arrows:
bl item_func_magic_arrow__Fv
b bow_func_end

get_light_arrows:
bl item_func_light_arrow__Fv


bow_func_end:
; Function end stuff
lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




.global progressive_wallet_item_func
progressive_wallet_item_func:

lis r3, 0x803C4C1A@ha
addi r3, r3, 0x803C4C1A@l
lbz r4, 0 (r3) ; Which wallet you have
cmpwi r4, 0
beq get_1000_rupee_wallet
cmpwi r4, 1
beq get_5000_rupee_wallet
b wallet_func_end

get_1000_rupee_wallet:
li r4, 1
stb r4, 0 (r3) ; Which wallet you have
b wallet_func_end

get_5000_rupee_wallet:
li r4, 2
stb r4, 0 (r3) ; Which wallet you have

wallet_func_end:
blr




.global progressive_bomb_bag_item_func
progressive_bomb_bag_item_func:

lis r3, 0x803C4C72@ha
addi r3, r3, 0x803C4C72@l
lbz r4, 6 (r3) ; Max number of bombs the player can currently hold
cmpwi r4, 30
beq get_60_bomb_bomb_bag
cmpwi r4, 60
beq get_99_bomb_bomb_bag
b bomb_bag_func_end

get_60_bomb_bomb_bag:
li r4, 60
stb r4, 0 (r3) ; Current num bombs
stb r4, 6 (r3) ; Max num bombs
b bomb_bag_func_end

get_99_bomb_bomb_bag:
li r4, 99
stb r4, 0 (r3) ; Current num bombs
stb r4, 6 (r3) ; Max num bombs

bomb_bag_func_end:
blr




.global progressive_quiver_item_func
progressive_quiver_item_func:

lis r3, 0x803C4C71@ha
addi r3, r3, 0x803C4C71@l
lbz r4, 6 (r3) ; Max number of arrows the player can currently hold
cmpwi r4, 30
beq get_60_arrow_quiver
cmpwi r4, 60
beq get_99_arrow_quiver
b quiver_func_end

get_60_arrow_quiver:
li r4, 60
stb r4, 0 (r3) ; Current num arrows
stb r4, 6 (r3) ; Max num arrows
b quiver_func_end

get_99_arrow_quiver:
li r4, 99
stb r4, 0 (r3) ; Current num arrows
stb r4, 6 (r3) ; Max num arrows

quiver_func_end:
blr




.global progressive_picto_box_item_func
progressive_picto_box_item_func:
; Function start stuff
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)


lis r3, 0x803C4C61@ha
addi r3, r3, 0x803C4C61@l
lbz r4, 0 (r3) ; Bitfield of picto boxes you own
cmpwi r4, 0
beq get_normal_picto_box
cmpwi r4, 1
beq get_deluxe_picto_box
b picto_box_func_end

get_normal_picto_box:
bl item_func_camera__Fv
b picto_box_func_end

get_deluxe_picto_box:
bl item_func_camera2__Fv


picto_box_func_end:
; Function end stuff
lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




.global hurricane_spin_item_func
hurricane_spin_item_func:
; Function start stuff
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

; Set event bit 6901 (bit 01 of byte 803C5295).
; This bit was unused in the base game, but we repurpose it to keep track of whether you have Hurricane Spin separately from whether you've seen the event where Orca would normally give you Hurricane Spin.
lis r3, 0x803C522C@ha
addi r3, r3, 0x803C522C@l
li r4, 0x6901 ; Unused event bit
bl onEventBit__11dSv_event_cFUs

; Function end stuff
lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




.global set_shop_item_in_bait_bag_slot_sold_out
set_shop_item_in_bait_bag_slot_sold_out:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

; First call the regular SoldOutItem function with the given arguments since we overwrote a call to that in order to call this custom function.
bl SoldOutItem__11ShopItems_cFi

; Set event bit 6902 (bit 02 of byte 803C5295).
; This bit was unused in the base game, but we repurpose it to keep track of whether you've purchased whatever item is in the Bait Bag slot of Beedle's shop.
lis r3, 0x803C522C@ha
addi r3, r3, 0x803C522C@l
li r4, 0x6902 ; Unused event bit
bl onEventBit__11dSv_event_cFUs

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr

.global check_shop_item_in_bait_bag_slot_sold_out
check_shop_item_in_bait_bag_slot_sold_out:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

; Check event bit 6902 (bit 02 of byte 803C5295), which was originally unused but we use it to keep track of whether the item in the Bait Bag slot has been purchased or not.
lis r3, 0x803C522C@ha
addi r3, r3, 0x803C522C@l
li r4, 0x6902 ; Unused event bit
bl isEventBit__11dSv_event_cFUs

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




; This function takes the same arguments as fastCreateItem, but it loads in any unloaded models without crashing like createItem.
; This is so we can replace any randomized item spawns that use fastCreateItem with a call to this new function instead.
; Note: One part of fastCreateItem that this custom function cannot emulate is giving the item a starting velocity.
; fastCreateItem can do that because the item subentity is created instantly, but when slow-loading the model for the item, the subentity is created asynchronously later on, so there's no way for us to store the velocity to it.
; The proper way to store a velocity to a slow-loaded item is for the object that created this item to check if the item is loaded every frame, and once it is it then stores the velocity to it. But this would be too complex to implement via ASM.
.global custom_createItem
custom_createItem:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

; If the item ID is FF, no item will be spawned.
; In order to avoid crashes we need to return a null pointer.
; Also don't bother even trying to spawn the item - it wouldn't do anything.
cmpwi r4, 0xFF
beq custom_createItem_invalid_item_id

; Create the item by calling createItem, which will load the item's model if necessary.
mr r9, r5
mr r5, r8
mr r8, r6
mr r6, r9
mr r10, r7
li r7, 3 ; Don't fade out
li r9, 5 ; Item action, how it behaves. 5 causes it to make a ding sound so that it's more obvious.
bl fopAcM_createItem__FP4cXyziiiiP5csXyziP4cXyz

; We need to return a pointer to the item entity to match fastCreateItem.
; But createItem only returns the entity ID.
; However, the entity pointer is still conveniently leftover in r5, so we just return that.
mr r3, r5
b custom_createItem_func_end

custom_createItem_invalid_item_id:
li r3, 0

custom_createItem_func_end:
lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




; When creating the item for the withered trees, offset the position it spawns at to be right in front of the player.
; Normally it would spawn at the top and then shoot out with momentum until it's in front of the player.
; But because of the way custom_createItem works, adding momentum is impossible.
; So instead just change the position to be in front of the player (but still up in the tree, so it falls down with gravity).
.global create_item_for_withered_trees
create_item_for_withered_trees:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

lis r10, withered_tree_item_spawn_offset@ha
addi r10, r10, withered_tree_item_spawn_offset@l

; Offset X pos
lfs f0, 0 (r3)
lfs f4, 0 (r10) ; Read the X offset
fadds f0,f4,f0
stfs f0, 0 (r3)

; Offset Y pos
lfs f0, 4 (r3)
lfs f4, 4 (r10) ; Read the Y offset
fadds f0,f4,f0
stfs f0, 4 (r3)

; Offset Z pos
lfs f0, 8 (r3)
lfs f4, 8 (r10) ; Read the Z offset
fadds f0,f4,f0
stfs f0, 8 (r3)

bl custom_createItem

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr


.global withered_tree_item_spawn_offset
withered_tree_item_spawn_offset:
.float -245.0 ; X offset
.float 0.0 ; Y offset
.float -135.0 ; Z offset




; Custom function that checks if the warp down to Hyrule should be unlocked.
; Requirements: Must have Full Power Master Sword equipped, and must have all 8 pieces of the Triforce.
.global check_hyrule_warp_unlocked
check_hyrule_warp_unlocked:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

lis     r3,0x803C4C08@ha
addi    r3,r3,0x803C4C08@l

; If in swordless mode, skip checking the master sword.
lis r4, sword_mode@ha
addi r4, r4, sword_mode@l
lbz r4, 0 (r4)
cmpwi r4, 2 ; Swordless
beq check_has_full_triforce_for_hyrule_warp_unlocked

lbz     r0,0xE(r3)
cmplwi  r0,0x3E ; Check if currently equipped sword is Full Power Master Sword
bne     hyrule_warp_not_unlocked

check_has_full_triforce_for_hyrule_warp_unlocked:
addi    r3,r3,180
bl      getTriforceNum__20dSv_player_collect_cFv
cmpwi   r3,8
bge     hyrule_warp_unlocked

hyrule_warp_not_unlocked:
li r3,0
b hyrule_warp_end

hyrule_warp_unlocked:
li r3,1

hyrule_warp_end:
lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




; Updates the current wind direction to match KoRL's direction.
.global set_wind_dir_to_ship_dir
set_wind_dir_to_ship_dir:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

; First call setShipSailState since we overwrote a call to this in KoRL's code in order to call this custom function.
bl setShipSailState__11JAIZelBasicFl

lis r3,0x803CA75C@ha
addi r3,r3,0x803CA75C@l
lwz r3, 0 (r3) ; Read the pointer to KoRL's entity
lha r3, 0x206 (r3) ; Read KoRL's Y rotation
neg r3, r3 ; Negate his Y rotation since it's backwards
addi r4, r3, 0x4000 ; Add 90 degrees to get the diretion KoRL is actually facing
addi r4, r4, 0x1000 ; Add another 22.5 degrees in order to help round to the closest 45 degrees.
rlwinm r4,r4,0,0,18 ; Now AND with 0xFFFFE000 in order to round down to the nearest 0x2000 (45 degrees). Because we added 22.5 degrees first, this accomplishes rounding either up or down to the nearest 45 degrees, whichever is closer.

li r3, 0
bl dKyw_tact_wind_set__Fss ; Pass the new angle as argument r4 to the function that changes wind direction

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




; Custom function that checks if the treasure chest in Ganon's Tower (that originally had the Light Arrows) has been opened.
; This is to make the Phantom Ganon that appears in the maze still work if you got Light Arrows beforehand.
.global check_ganons_tower_chest_opened
check_ganons_tower_chest_opened:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

li r3, 8 ; Stage ID for Ganon's Tower.
li r4, 0 ; Chest open flag for the Light Arrows chest. Just 0 since this is the only chest in the whole dungeon.
bl dComIfGs_isStageTbox__Fii

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




; Custom function that creates an item given by a Windfall townsperson, and also sets an event bit to keep track of the item being given.
.global create_item_and_set_event_bit_for_townsperson
create_item_and_set_event_bit_for_townsperson:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)
stw r31, 0xC (sp)
mr r31, r4 ; Preserve argument r4, which has both the item ID and the event bit to set.

clrlwi r4,r4,24 ; Get the lowest byte (0x000000FF), which has the item ID
bl fopAcM_createItemForPresentDemo__FP4cXyziUciiP5csXyzP4cXyz


rlwinm. r4,r31,16,16,31 ; Get the upper halfword (0xFFFF0000), which has the event bit to set
beq create_item_and_set_event_bit_for_townsperson_end ; If the event bit specified is 0000, skip to the end of the function instead
mr r31, r3 ; Preserve the return value from createItemForPresentDemo so we can still return that
lis r3, 0x803C522C@ha
addi r3, r3, 0x803C522C@l
bl onEventBit__11dSv_event_cFUs ; Otherwise, set that event bit
mr r3, r31

create_item_and_set_event_bit_for_townsperson_end:
lwz r31, 0xC (sp)
lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




; Lenzo normally won't let you start his assistant quest if he detects you already have the Deluxe Picto Box, which is bad when that's randomized.
; So we need to set a custom event bit to keep track of whether you've gotten whatever item is in the Deluxe Picto Box slot.
.global lenzo_set_deluxe_picto_box_event_bit
lenzo_set_deluxe_picto_box_event_bit:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

; First replace the function call we overwrote to call this custom function.
bl setEquipBottleItemEmpty__17dSv_player_item_cFv

; Next set an originally-unused event bit to keep track of whether the player got the item that was the Deluxe Picto Box in vanilla.
lis r3, 0x803C522C@ha
addi r3, r3, 0x803C522C@l
li r4, 0x6920
bl onEventBit__11dSv_event_cFUs

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




; Zunari usually checks if he gave you the Magic Armor by calling checkGetItem on the Magic Armor item ID. This doesn't work properly when the item he gives is randomized.
; So we need to set a custom event bit to keep track of whether you've gotten whatever item is in the Magic Armor slot.
.global zunari_give_item_and_set_magic_armor_event_bit
zunari_give_item_and_set_magic_armor_event_bit:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)
stw r31, 0xC (sp)
mr r31, r4 ; Preserve argument r4, which has the item ID

bl fopAcM_createItemForPresentDemo__FP4cXyziUciiP5csXyzP4cXyz


lis r4, zunari_magic_armor_slot_item_id@ha
addi r4, r4, zunari_magic_armor_slot_item_id@l
lbz r4, 0 (r4) ; Load what item ID is in the Magic Armor slot. This value is updated by the randomizer when it randomizes that item.

cmpw r31, r4 ; Check if the item ID given is the same one from the Magic Armor slot.
bne zunari_give_item_and_set_magic_armor_event_bit_end ; If it's not the item in the Magic Armor slot, skip to the end of the function
mr r31, r3 ; Preserve the return value from createItemForPresentDemo so we can still return that
lis r3, 0x803C522C@ha
addi r3, r3, 0x803C522C@l
li r4, 0x6940 ; Unused event bit that we use to keep track of whether Zunari has given the Magic Armor item
bl onEventBit__11dSv_event_cFUs
mr r3, r31

zunari_give_item_and_set_magic_armor_event_bit_end:
lwz r31, 0xC (sp)
lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr


.global zunari_magic_armor_slot_item_id
zunari_magic_armor_slot_item_id:
.byte 0x2A ; Default item ID is Magic Armor. This value is updated by the randomizer when this item is randomized.
.align 2 ; Align to the next 4 bytes




; Salvage Corp usually check if they gave you their item by calling checkGetItem. This doesn't work properly when the item is randomized.
; So we need to set a custom event bit to keep track of whether you've gotten whatever item they give you.
.global salvage_corp_give_item_and_set_event_bit
salvage_corp_give_item_and_set_event_bit:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)
stw r31, 0xC (sp)

bl fopAcM_createItemForPresentDemo__FP4cXyziUciiP5csXyzP4cXyz


mr r31, r3 ; Preserve the return value from createItemForPresentDemo so we can still return that
lis r3, 0x803C522C@ha
addi r3, r3, 0x803C522C@l
li r4, 0x6980 ; Unused event bit that we use to keep track of whether the Salvage Corp has given you their item yet or not
bl onEventBit__11dSv_event_cFUs
mr r3, r31


lwz r31, 0xC (sp)
lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




; Maggie usually checks if she's given you her letter by calling isReserve. That doesn't work well when the item is randomized.
; So we use this function to give her item and then set a custom event bit to keep track of it (6A01).
.global maggie_give_item_and_set_event_bit
maggie_give_item_and_set_event_bit:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)
stw r31, 0xC (sp)

bl fopAcM_createItemForPresentDemo__FP4cXyziUciiP5csXyzP4cXyz


mr r31, r3 ; Preserve the return value from createItemForPresentDemo so we can still return that
lis r3, 0x803C522C@ha
addi r3, r3, 0x803C522C@l
li r4, 0x6A01 ; Unused event bit
bl onEventBit__11dSv_event_cFUs
mr r3, r31


lwz r31, 0xC (sp)
lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




; The Rito postman in the Windfall cafe usually checks if he's given you Moe's letter by calling isReserve. That doesn't work well when the item is randomized.
; So we use this function to start his item give event and then set a custom event bit to keep track of it (6A02).
.global rito_cafe_postman_start_event_and_set_event_bit
rito_cafe_postman_start_event_and_set_event_bit:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)
stw r31, 0xC (sp)
mr r31, r3 ; Preserve argument r3, which has the Rito postman entity

bl fopAcM_orderOtherEventId__FP10fopAc_ac_csUcUsUsUs


lha r31, 0x86A(r31) ; Load the index of this Rito postman from the Rito postman entity
cmpwi r31, 0 ; 0 is the one in the Windfall cafe. If it's not that one, we don't want to set the event bit.
bne rito_cafe_postman_start_event_and_set_event_bit_end

mr r31, r3 ; Preserve the return value from orderOtherEventId so we can still return that (not sure if necessary, but just to be safe)
lis r3, 0x803C522C@ha
addi r3, r3, 0x803C522C@l
li r4, 0x6A02 ; Unused event bit
bl onEventBit__11dSv_event_cFUs
mr r3, r31


rito_cafe_postman_start_event_and_set_event_bit_end:
lwz r31, 0xC (sp)
lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




.global reset_makar_position_to_start_of_dungeon
reset_makar_position_to_start_of_dungeon:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

lis r8, 0x803C9D44@ha ; Most recent spawn ID the player spawned from
addi r8, r8, 0x803C9D44@l
lha r8, 0 (r8)
; Check if the player's last spawn ID was the one at the very start of the dungeon.
cmpwi r8, 15
; If not, skip resetting the position since the player did not actually leave and re-enter the dungeon.
bne after_resetting_makar_position

lis r8, 0xC5643065@ha ; Makar's starting X pos, -3651.02
addi r8, r8, 0xC5643065@l
stw r8, 0 (r5)
lis r8, 0x44C2B54F@ha ; Makar's starting Y pos, 1557.67
addi r8, r8, 0x44C2B54F@l
stw r8, 4 (r5)
lis r8, 0x464ECCA7@ha ; Makar's starting Z pos, 13235.2
addi r8, r8, 0x464ECCA7@l
stw r8, 8 (r5)

li r8, -0x6B60 ; Makar's starting rotation (0x94A0)
sth r8, 0xC (r5)
mr r6, r8 ; Argument r6 to setRestartOption needs to be the rotation
mr r28, r8 ; Also modify the local variable rotation in Makar's code (for when he calls set__19dSv_player_priest)

li r8, 0xF ; Makar's starting room index
stb r8, 0xE (r5)
mr r7, r8 ; Argument r7 to setRestartOption needs to be the room index
mr r29, r8 ; Also modify the local variable room index in Makar's code (for when he calls set__19dSv_player_priest)

after_resetting_makar_position:

bl setRestartOption__13dSv_restart_cFScP4cXyzsSc ; Replace the function call we overwrote to call this custom function

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




.global reset_medli_position_to_start_of_dungeon
reset_medli_position_to_start_of_dungeon:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

lis r8, 0x803C9D44@ha ; Most recent spawn ID the player spawned from
addi r8, r8, 0x803C9D44@l
lha r8, 0 (r8)
; Check if the player's last spawn ID was the one at the very start of the dungeon.
cmpwi r8, 0
; If not, skip resetting the position since the player did not actually leave and re-enter the dungeon.
bne after_resetting_medli_position

lis r8, 0xC5E179B6@ha ; Medli's starting X pos, -7215.21
addi r8, r8, 0xC5E179B6@l
stw r8, 0 (r5)
lis r8, 0xC3480000@ha ; Medli's starting Y pos, -200
addi r8, r8, 0xC3480000@l
stw r8, 4 (r5)
lis r8, 0x45A4564F@ha ; Medli's starting Z pos, 5258.79
addi r8, r8, 0x45A4564F@l
stw r8, 8 (r5)

li r8, 0x7FFF ; Medli's starting rotation (0x8000)
addi r8, r8, 1 ; (Can't put 0x8000 in a single li instruction so we need to add 1 afterwards)
sth r8, 0xC (r5)
mr r6, r8 ; Argument r6 to setRestartOption needs to be the rotation
mr r31, r8 ; Also modify the local variable rotation in Medli's code (for when she calls set__19dSv_player_priest)

li r8, 0 ; Medli's starting room index
stb r8, 0xE (r5)
mr r7, r8 ; Argument r7 to setRestartOption needs to be the room index
mr r30, r8 ; Also modify the local variable room index in Medli's code (for when she calls set__19dSv_player_priest)

after_resetting_medli_position:

bl setRestartOption__13dSv_restart_cFScP4cXyzsSc ; Replace the function call we overwrote to call this custom function

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




; Custom function that gives a goddess pearl and also places it in the statue's hands automatically, and raises TotG if the player has all 3 pearls.
.global give_pearl_and_raise_totg_if_necessary
give_pearl_and_raise_totg_if_necessary:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)
stw r31, 0xC (sp)
mr r31, r4 ; Preserve argument r4, which has the pearl index to give

bl onSymbol__20dSv_player_collect_cFUc ; Replace the call we overwrote to jump here, which gives the player a specific pearl

lis r3, 0x803C522C@ha ; Event flag bitfield, will be needed several times
addi r3, r3, 0x803C522C@l

; Check the pearl index to know which event flag to set for the pearl being placed
cmpwi r31, 0
beq place_nayrus_pearl
cmpwi r31, 1
beq place_dins_pearl
cmpwi r31, 2
beq place_farores_pearl
b check_should_raise_totg

place_nayrus_pearl:
li r4, 0x1410 ; Placed Nayru's Pearl
bl onEventBit__11dSv_event_cFUs
b check_should_raise_totg

place_dins_pearl:
li r4, 0x1480 ; Placed Din's Pearl
bl onEventBit__11dSv_event_cFUs
b check_should_raise_totg

place_farores_pearl:
li r4, 0x1440 ; Placed Farore's Pearl
bl onEventBit__11dSv_event_cFUs

check_should_raise_totg:
lis r5, 0x803C4CC7@ha ; Bitfield of the player's currently owned pearls
addi r5, r5, 0x803C4CC7@l
lbz r4, 0 (r5)
cmpwi r4, 7
bne after_raising_totg ; Only raise TotG if the player owns all 3 pearls

li r4, 0x1E40 ; TOWER_OF_THE_GODS_RAISED
bl onEventBit__11dSv_event_cFUs
li r4, 0x2E80 ; PEARL_TOWER_CUTSCENE
bl onEventBit__11dSv_event_cFUs
after_raising_totg:

lwz r31, 0xC (sp)
lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




.global slow_down_ship_when_stopping
slow_down_ship_when_stopping:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

lis r4, ship_stopping_deceleration@ha
addi r4, r4, ship_stopping_deceleration@l
lfs f3, 0 (r4) ; Max deceleration per frame
lfs f4, 4 (r4) ; Min deceleration per frame

bl cLib_addCalc__FPfffff

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr

ship_stopping_deceleration:
.float 2.0 ; Max deceleration, 1.0 in vanilla
.float 0.2 ; Min deceleration, 0.1 in vanilla




.global slow_down_ship_when_idle
slow_down_ship_when_idle:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

lis r4, ship_idle_deceleration@ha
addi r4, r4, ship_idle_deceleration@l
lfs f3, 0 (r4) ; Max deceleration per frame
lfs f4, 4 (r4) ; Min deceleration per frame

bl cLib_addCalc__FPfffff

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr

ship_idle_deceleration:
.float 2.0 ; Max deceleration, 1.0 in vanilla
.float 0.1 ; Min deceleration, 0.05 in vanilla




; Part of the code for the hookshot's sight expects entities you look at to have a pointer in a specific place.
; The broken shards of Helmaroc King's mask don't have that pointer so looking at them with hookshot crashes.
.global hookshot_sight_failsafe_check
hookshot_sight_failsafe_check:

cmplwi r30, 0
beq hookshot_sight_failsafe
b hookshot_sight_return

; If r30 is null skip to the code that hides the hookshot sight.
hookshot_sight_failsafe:
b 0x800F13C0

; Otherwise we replace the line of code at 800F13A8 we replaced to jump here, then jump back.
hookshot_sight_return:
lwz r0, 0x01C4 (r30)
b 0x800F13AC




; Refills the player's magic meter when loading a save.
.global fully_refill_magic_meter_on_load_save
fully_refill_magic_meter_on_load_save:

lis r3, 0x803C4C1B@ha
addi r3, r3, 0x803C4C1B@l
lbz r4, 0 (r3) ; Load max magic meter
stb r4, 1 (r3) ; Store to current magic meter

lwz r3, 0x428 (r22) ; Replace the line we overwrote to branch here
b 0x80231B0C ; Return




; Borrows logic used for vanilla rope hang turning and injects some of the rotation logic into the rope swinging function.
; The main difference between the way the vanilla rope hanging function turns the player and this custom function is that the vanilla function uses a maximum rotational velocity per frame of 0x200, and a rotational acceleration of 0x40.
; But 0x200 units of rotation per frame would be far too fast to control when the player is swinging, and they could clip through walls very easily.
; So instead we just use the rotational acceleration as a constant rotational velocity instead, with no acceleration or deceleration.
.global turn_while_swinging
turn_while_swinging:

lis r3, 0x803A4DF0@ha
addi r3, r3, 0x803A4DF0@l
lfs f0, 0 (r3) ; Control stick horizontal axis (from -1.0 to 1.0)
lfs f1, -0x5A18 (r2) ; Load the float constant at 803FA2E8 for the base amount of rotational velocity to use (vanilla value is 0x40, this constant is originally used as rotational acceleration by the rope hanging function)
fmuls f0, f1, f0 ; Get the current amount of rotational velocity to use this frame after adjusting for the control stick amount

; Convert current rotational velocity to an integer.
; (sp+0x68 was used earlier on in procRopeSwing__9daPy_lk_cFv for float conversion so we just reuse this same space.)
fctiwz  f0, f0
stfd f0, 0x68 (sp)
lwz r0, 0x6C (sp)

; Convert base rotational velocity to an integer.
fctiwz  f1, f1
stfd f1, 0x68 (sp)
lwz r3, 0x6C (sp)

; If the player isn't moving the control stick horizontally very much (less than 25%), don't turn the player at all.
rlwinm r3, r3, 30, 2, 31 ; Divide the base rotational velocity by 4 to figure out what the threshold should be for 25% on the control stick.
cmpw r0, r3
bge turn_while_swinging_update_angle ; Control stick is >=25%
neg r3, r3
cmpw r0, r3
ble turn_while_swinging_update_angle ; Control stick is <=-25%
b turn_while_swinging_return

turn_while_swinging_update_angle:
; Subtract rotational velocity from the player's rotation. (Both player_entity+20E and +206 have the player's rotation.)
lha r3, 0x020E (r31)
sub r0, r3, r0
sth r0, 0x020E (r31)
sth r0, 0x0206 (r31)

turn_while_swinging_return:
lfs f0, -0x5BA8 (rtoc) ; Replace line we overwrote to branch here
b 0x8014564C ; Return




; This function checks if Phantom Ganon's sword should disappear.
; Normally, both Phantom Ganon 2's and Phantom Ganon 3's swords will disappear once you've used Phantom Ganon 3's sword to destroy the door to Puppet Ganon.
; We change it so Phantom Ganon 2's sword remains so it can lead the player through the maze.
.global check_phantom_ganons_sword_should_disappear
check_phantom_ganons_sword_should_disappear:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

; First replace the event flag check we overwrote to call this custom function.
bl isEventBit__11dSv_event_cFUs

; If the player hasn't destroyed the door with Phantom Ganon's sword yet, we don't need to do anything different so just return.
cmpwi r3, 0
beq check_phantom_ganons_sword_should_disappear_end

; If the player has destroyed the door, check if the current stage is the Phantom Ganon maze, where Phantom Ganon 2 is fought.
lis r3, 0x803C9D3C@ha ; Current stage name
addi r3, r3, 0x803C9D3C@l
lis r4, phantom_ganon_maze_stage_name@ha
addi r4, r4, phantom_ganon_maze_stage_name@l
bl strcmp
; If the stage is the maze, strcmp will return 0, so we return that to tell Phantom Ganon's sword that it should not disappear.
; If the stage is anything else, strcmp will not return 0, so Phantom Ganon's sword should disappear.

check_phantom_ganons_sword_should_disappear_end:
lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr

.global phantom_ganon_maze_stage_name
phantom_ganon_maze_stage_name:
.string "GanonJ"
.align 2 ; Align to the next 4 bytes




.global give_temporary_sword_during_ganondorf_fight_in_swordless
give_temporary_sword_during_ganondorf_fight_in_swordless:

stb r0, 0x48 (r4) ; Replace the line we overwrote to jump here (which removed the bow from your inventory)

lbz r0, 0xE (r4) ; Read the player's currently equipped sword ID
cmpwi r0, 0xFF
; If the player has any sword equipped, don't replace it with the Hero's Sword
bne give_temporary_sword_during_ganondorf_fight_in_swordless_end

li r0, 0x38
stb r0, 0xE (r4) ; Set the player's currently equipped sword ID to the regular Hero's Sword

give_temporary_sword_during_ganondorf_fight_in_swordless_end:
b 0x80235F14 ; Return




.global give_temporary_sword_in_orcas_house_in_swordless
give_temporary_sword_in_orcas_house_in_swordless:

lis r3, 0x803C9D3C@ha ; Current stage name
addi r3, r3, 0x803C9D3C@l
lis r4, 0x8036A948@ha ; Pointer to the string "Ojhous", the stage for Orca's house
addi r4, r4, 0x8036A948@l
bl strcmp
cmpwi r3, 0
; If the player did not just enter Orca's house, skip giving a temporary sword
bne give_temporary_sword_in_orcas_house_in_swordless_end

lis r3, 0x803C4C08@ha
addi r3, r3, 0x803C4C08@l
lbz r0, 0xE (r3) ; Read the player's currently equipped sword ID
cmpwi r0, 0xFF
; If the player has any sword equipped, don't replace it with the Hero's Sword
bne give_temporary_sword_in_orcas_house_in_swordless_end

li r0, 0x38
stb r0, 0xE (r3) ; Set the player's currently equipped sword ID to the regular Hero's Sword

; Then, in order to prevent this temporary sword from being removed by remove_temporary_sword_when_loading_stage_in_swordless, we need to return differently to skip that code.
mr r29, r3 ; r29 needs to have 0x803C4C08 in it
b 0x80236088

give_temporary_sword_in_orcas_house_in_swordless_end:
lis r3, 0x803C ; Replace the line we overwrote to branch here
b 0x80236080 ; Return




.global remove_temporary_sword_when_loading_stage_in_swordless
remove_temporary_sword_when_loading_stage_in_swordless:

lbz r0, 0xB4 (r29) ; Read the player's owned swords bitfield
cmpwi r0, 0
; If the player owns any sword, don't remove their equipped sword since it's not temporary
bne remove_temporary_sword_when_loading_stage_in_swordless_end

li r0, 0xFF
stb r0, 0xE (r29) ; Set the player's currently equipped sword ID to no sword

remove_temporary_sword_when_loading_stage_in_swordless_end:
lbz r0, 0x48 (r29) ; Replace the line we overwrote to jump here
b 0x80236088 ; Return




; Read the C-stick's horizontal axis and negate the value in order to invert the camera's movement.
.global invert_camera_horizontal_axis
invert_camera_horizontal_axis:

lfs f1, 0x10 (r3) ; Load the C-stick's horizontal axis for controlling the camera (same as the line we're replacing)
fneg f1, f1 ; Negate the horizontal axis

b 0x8016248C ; Return




.global generic_on_dungeon_bit
generic_on_dungeon_bit:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

mr r5, r3 ; Argument r3 to this func is the stage ID of the dungeon to add this item for
mr r6, r4 ; Argument r4 to this func is the bit index to set

lis r3, 0x803C53A4@ha ; This value is the stage ID of the current stage
addi r3, r3, 0x803C53A4@l
lbz r4, 0 (r3)
cmpw r4, r5 ; Check if we're currently in the right dungeon for this key
beq generic_on_dungeon_bit_in_correct_dungeon

; Not in the correct dungeon for this dungeon bit. We need to set the bit for the correct dungeon's stage info.
lis r3, 0x803C4F88@ha ; List of all stage info
addi r3, r3, 0x803C4F88@l
mulli r4, r5, 0x24 ; Use stage ID of the dungeon as the index, each entry in the list is 0x24 bytes long
add r3, r3, r4
b generic_on_dungeon_bit_func_end

generic_on_dungeon_bit_in_correct_dungeon:
; In the correct dungeon for this dungeon bit.
lis r3, 0x803C5380@ha ; Currently loaded stage info
addi r3, r3, 0x803C5380@l

generic_on_dungeon_bit_func_end:
; Now call onDungeonBit with argument r3 being the stage info that was determined above.
mr r4, r6 ; Argument r4 is the bit index
bl onDungeonItem__12dSv_memBit_cFi

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




.global generic_small_key_item_get_func
generic_small_key_item_get_func:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

mr r5, r3 ; Argument r3 is the stage ID of the dungeon to add this item for

lis r3, 0x803C53A4@ha ; This value is the stage ID of the current stage
addi r3, r3, 0x803C53A4@l
lbz r4, 0 (r3)
cmpw r4, r5 ; Check if we're currently in the right dungeon for this key
bne generic_small_key_item_get_func_not_in_correct_dungeon

; Next we need to check if the current stage has the "is dungeon" bit set in its StagInfo.
; If it doesn't (like if we're in a boss room) then we still can't use the normal key function, since the key counter in the UI is disabled, and that's what adds to your actual number of keys when we use the normal key function.
lis r3, 0x803C4C08@ha
addi r3, r3, 0x803C4C08@l
lwzu r12, 0x5150 (r3)
lwz r12, 0xB0 (r12)
mtctr r12
bctrl
lbz r0, 9 (r3) ; Read the stage ID+is dungeon bit
rlwinm. r0, r0, 0, 31, 31
beq generic_small_key_item_get_func_in_non_dungeon_room_of_correct_dungeon

; If both the stage ID and the is dungeon bit are correct, we can call the normal small key function.
b generic_small_key_item_get_func_in_correct_dungeon

generic_small_key_item_get_func_not_in_correct_dungeon:
; Not in the correct dungeon for this small key.
; We need to bypass the normal small key adding method.
; Instead we add directly to the small key count for the correct dungeon's stage info.
lis r3, 0x803C4F88@ha ; List of all stage info
addi r3, r3, 0x803C4F88@l
mulli r4, r5, 0x24 ; Use stage ID of the dungeon as the index, each entry in the list is 0x24 bytes long
add r3, r3, r4
lbz r4, 0x20 (r3) ; Current number of keys for the correct dungeon
addi r4, r4, 1
stb r4, 0x20 (r3) ; Current number of keys for the correct dungeon
b generic_small_key_item_get_func_end

generic_small_key_item_get_func_in_non_dungeon_room_of_correct_dungeon:
lis r3, 0x803C5380@ha ; Currently loaded stage info
addi r3, r3, 0x803C5380@l
lbz r4, 0x20 (r3) ; Current number of keys for the current dungeon
addi r4, r4, 1
stb r4, 0x20 (r3) ; Current number of keys for the current dungeon
b generic_small_key_item_get_func_end

generic_small_key_item_get_func_in_correct_dungeon:
; In the correct dungeon for this small key.
; Simply call the normal small key func, as it will work correctly in this case.
bl item_func_small_key__Fv

generic_small_key_item_get_func_end:
lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




.global drc_small_key_item_get_func
drc_small_key_item_get_func:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

li r3, 3 ; DRC stage ID
bl generic_small_key_item_get_func

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr


.global fw_small_key_item_get_func
fw_small_key_item_get_func:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

li r3, 4 ; FW stage ID
bl generic_small_key_item_get_func

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr


.global totg_small_key_item_get_func
totg_small_key_item_get_func:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

li r3, 5 ; TotG stage ID
bl generic_small_key_item_get_func

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr


.global et_small_key_item_get_func
et_small_key_item_get_func:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

li r3, 6 ; ET stage ID
bl generic_small_key_item_get_func

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr


.global wt_small_key_item_get_func
wt_small_key_item_get_func:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

li r3, 7 ; WT stage ID
bl generic_small_key_item_get_func

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




.global drc_big_key_item_get_func
drc_big_key_item_get_func:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

li r3, 3 ; DRC stage ID
li r4, 2 ; Big key bit index
bl generic_on_dungeon_bit

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr


.global fw_big_key_item_get_func
fw_big_key_item_get_func:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

li r3, 4 ; FW stage ID
li r4, 2 ; Big key bit index
bl generic_on_dungeon_bit

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr


.global totg_big_key_item_get_func
totg_big_key_item_get_func:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

li r3, 5 ; TotG stage ID
li r4, 2 ; Big key bit index
bl generic_on_dungeon_bit

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr


.global et_big_key_item_get_func
et_big_key_item_get_func:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

li r3, 6 ; ET stage ID
li r4, 2 ; Big key bit index
bl generic_on_dungeon_bit

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr


.global wt_big_key_item_get_func
wt_big_key_item_get_func:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

li r3, 7 ; WT stage ID
li r4, 2 ; Big key bit index
bl generic_on_dungeon_bit

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




.global drc_dungeon_map_item_get_func
drc_dungeon_map_item_get_func:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

li r3, 3 ; DRC stage ID
li r4, 0 ; Dungeon map bit index
bl generic_on_dungeon_bit

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr


.global fw_dungeon_map_item_get_func
fw_dungeon_map_item_get_func:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

li r3, 4 ; FW stage ID
li r4, 0 ; Dungeon map bit index
bl generic_on_dungeon_bit

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr


.global totg_dungeon_map_item_get_func
totg_dungeon_map_item_get_func:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

li r3, 5 ; TotG stage ID
li r4, 0 ; Dungeon map bit index
bl generic_on_dungeon_bit

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr


.global ff_dungeon_map_item_get_func
ff_dungeon_map_item_get_func:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

li r3, 2 ; FF stage ID
li r4, 0 ; Dungeon map bit index
bl generic_on_dungeon_bit

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr


.global et_dungeon_map_item_get_func
et_dungeon_map_item_get_func:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

li r3, 6 ; ET stage ID
li r4, 0 ; Dungeon map bit index
bl generic_on_dungeon_bit

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr


.global wt_dungeon_map_item_get_func
wt_dungeon_map_item_get_func:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

li r3, 7 ; WT stage ID
li r4, 0 ; Dungeon map bit index
bl generic_on_dungeon_bit

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




.global drc_compass_item_get_func
drc_compass_item_get_func:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

li r3, 3 ; DRC stage ID
li r4, 1 ; Compass bit index
bl generic_on_dungeon_bit

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr


.global fw_compass_item_get_func
fw_compass_item_get_func:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

li r3, 4 ; FW stage ID
li r4, 1 ; Compass bit index
bl generic_on_dungeon_bit

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr


.global totg_compass_item_get_func
totg_compass_item_get_func:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

li r3, 5 ; TotG stage ID
li r4, 1 ; Compass bit index
bl generic_on_dungeon_bit

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr


.global ff_compass_item_get_func
ff_compass_item_get_func:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

li r3, 2 ; FF stage ID
li r4, 1 ; Compass bit index
bl generic_on_dungeon_bit

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr


.global et_compass_item_get_func
et_compass_item_get_func:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

li r3, 6 ; ET stage ID
li r4, 1 ; Compass bit index
bl generic_on_dungeon_bit

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr


.global wt_compass_item_get_func
wt_compass_item_get_func:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

li r3, 7 ; WT stage ID
li r4, 1 ; Compass bit index
bl generic_on_dungeon_bit

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




.close
