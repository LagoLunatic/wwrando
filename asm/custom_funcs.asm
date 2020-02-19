
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

; Start the player with 30 bombs and arrows. (But not the ability to actually use them.)
; This change is so we can remove the code that sets your current bombs/arrows to 30 when you first get the bombs/bow.
; That code would be bad if the player got a bomb bag/quiver upgrade beforehand, as then that code would reduce the max.
lis r3, 0x803C4C71@ha
addi r3, r3, 0x803C4C71@l
li r4, 30
stb r4, 0 (r3) ; Current arrows
stb r4, 1 (r3) ; Current bombs
stb r4, 6 (r3) ; Max arrows
stb r4, 7 (r3) ; Max bombs

; Start the player with a magic meter so items that use it work correctly.
lis r3, 0x803C4C1B@ha
addi r3, r3, 0x803C4C1B@l
lis r4, starting_magic@ha 
addi r4, r4, starting_magic@l
lbz r4, 0 (r4) ; Load starting magic address into r4, then load byte at address into r4
stb r4, 0 (r3) ; Max magic meter
stb r4, 1 (r3) ; Current magic meter

; Give user-selected custom starting items
bl init_starting_gear


lis r3, 0x803C522C@ha
addi r3, r3, 0x803C522C@l
li r4, 0x3510 ; HAS_SEEN_INTRO
bl onEventBit__11dSv_event_cFUs
li r4, 0x2A80 ; HAS_HEROS_CLOTHES (This should be set even if the player wants to wear casual clothes, it's overridden elsewhere)
bl onEventBit__11dSv_event_cFUs
li r4, 0x0280 ; SAW_TETRA_IN_FOREST_OF_FAIRIES
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
li r4, 0x2D01 ; ANIMATION_SET_2 (Saw cutscene before Helmaroc King where Aryll is rescued)
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
li r4, 0x3304 ; Saw event where Medli calls to you from within jail
bl onEventBit__11dSv_event_cFUs
li r4, 0x2910 ; MAKAR_IN_WIND_TEMPLE
bl onEventBit__11dSv_event_cFUs
li r4, 0x1610 ; Makar is in dungeon mode and can be lifted/called
bl onEventBit__11dSv_event_cFUs
li r4, 0x3440 ; Saw event where Makar calls to you from within jail
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
lis r3, 0x803C4F88@ha ; Sea stage info.
addi r3, r3, 0x803C4F88@l
lis r4, 0x0200
stw r4, 4 (r3)
; Also set a switch bit (3F) for having seen the Windfall Island intro scene.
lis r4, 0x8000
stw r4, 8 (r3)
; Also set a switch bit (58) for having seen the short event when you enter Forsaken Fortress 2 for the first time.
; Also set a switch (0x50) for having seen the event where the camera pans around the Flight Control Platform.
lis r4, 0x0101
stw r4, 0xC (r3)

; Set a switch (21) for having seen the gossip stone event in DRC where KoRL tells you about giving bait to rats.
; Also set a switch (09) for having seen the event where the camera pans up to Valoo when you go outside.
; Also set a switch (46) for having seen the event where the camera pans around when you first enter DRC.
lis r3, 0x803C4FF4@ha ; Dragon Roost Cavern stage info.
addi r3, r3, 0x803C4FF4@l
li r4, 0x0200
stw r4, 4 (r3)
li r4, 0x0002
stw r4, 8 (r3)
li r4, 0x0040
stw r4, 0xC (r3)

; Set a switch (36) for having seen the event where the camera pans around the first room when you first enter FW.
lis r3, 0x803C5018@ha ; Forbidden Woods stage info.
addi r3, r3, 0x803C5018@l
lis r4, 0x0040
stw r4, 8 (r3)

; Set a switch (2D) for having seen the event where the camera pans around when you go outside at the top of TotG.
; Also set a switch (63) for having seen the event where the camera pans around the first room when you first enter TotG.
lis r3, 0x803C503C@ha ; Tower of the Gods stage info.
addi r3, r3, 0x803C503C@l
li r4, 0x2000
stw r4, 8 (r3)
li r4, 0x0008
stw r4, 0x10 (r3)

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


; This function reads from an array of user-selected starting item IDs and adds them to your inventory.
.global init_starting_gear
init_starting_gear:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)
stw r31, 0xC (sp)

lis r31, starting_gear@ha
addi r31, r31, starting_gear@l
lbz r3, 0 (r31)
b init_starting_gear_check_continue_loop

init_starting_gear_begin_loop:
bl convert_progressive_item_id
bl execItemGet__FUc
lbzu r3, 1(r31)
init_starting_gear_check_continue_loop:
cmplwi r3, 255
bne+ init_starting_gear_begin_loop

end_init_starting_gear:
lwz r31, 0xC (sp)
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

.global starting_gear
starting_gear:
.space 47, 0xFF ; Allocate space for up to 47 additional items (when changing this also update the constant in tweaks.py)
.byte 0xFF
.align 1 ; Align to the next 2 bytes
.global starting_quarter_hearts
starting_quarter_hearts:
.short 12 ; By default start with 12 quarter hearts (3 heart containers)
.global starting_magic
starting_magic:
.byte 16 ; By default start with 16 units of magic (small magic meter)

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
li r3, 0xAF ; Invalid quiver state; this shouldn't happen so just return the base quiver ID
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
; fastCreateItem can do that because the item actor is created instantly, but when slow-loading the model for the item, the actor is created asynchronously later on, so there's no way for us to store the velocity to it.
; The proper way to store a velocity to a slow-loaded item is for the object that created this item to check if the item is loaded every frame, and once it is it then stores the velocity to it. But this would be too complex to implement via ASM.
; Another note: This function cannot accurately emulate the return value of fastCreateItem, which is a pointer to the created actor, because as mentioned above, the actor doesn't exist yet at the moment after createItem is called. Therefore, it has to return the item actor's unique ID instead, like createItem does. This means that any code calling this custom function will need to have any code after the call that handles the return value changed or else it will crash because it will treat the actor unique ID as a pointer.
.global custom_createItem
custom_createItem:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

; If the item ID is FF, no item will be spawned.
; In order to avoid issues we need to return -1.
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

; Return the actor's unique ID that createItem returned.
b custom_createItem_func_end

custom_createItem_invalid_item_id:
li r3, -1 ; Return -1 to indicate no actor was created.

custom_createItem_func_end:
lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




.global withered_tree_item_try_give_momentum
withered_tree_item_try_give_momentum:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

; First replace the function call we overwrote to call this custom function.
bl fopAcM_SearchByID__FUiPP10fopAc_ac_c

cmpwi r3, 0
beq withered_tree_item_try_give_momentum_end ; Item actor has already been picked up

lwz r4, 0x18 (sp) ; Read the item actor pointer (original code used sp+8 but this function's stack offset is +0x10)
cmpwi r4, 0
beq withered_tree_item_try_give_momentum_end ; Item actor was just created a few frames ago and hasn't actually been properly spawned yet

; Now that we have the item actor pointer in r4, we need to check if the actor was just created this frame or not.
; To do that we store a custom flag to an unused byte in the withered tree actor struct.
lbz r5, 0x212 (r31) ; (Bytes +0x212 and +0x213 were originally just padding)
cmpwi r5, 0
bne withered_tree_item_try_give_momentum_end ; Already set the flag, so this isn't the first frame it spawned on.

; Since this is the first frame since the item actor was properly created, we can set its momentum.
lis r10, withered_tree_item_speeds@ha
addi r10, r10, withered_tree_item_speeds@l
lfs f0, 0 (r10) ; Read forward velocity
stfs f0, 0x254 (r4)
lfs f0, 4 (r10) ; Read the Y velocity
stfs f0, 0x224 (r4)
lfs f0, 8 (r10) ; Read gravity
stfs f0, 0x258 (r4)

; Also set bit 0x40 in some bitfield for the item actor.
; Apparently this bit is for allowing the actor to still move while events are going on. It doesn't seem to really matter in this specific case, but set it just to be completely safe.
lwz r5, 0x1C4 (r4)
ori r5, r5, 0x40
stw r5, 0x1C4 (r4)

; Now store the custom flag meaning that we've already set the item actor's momentum so we don't do it again.
li r5, 1
stb r5, 0x212 (r31)

withered_tree_item_try_give_momentum_end:
lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr


.global withered_tree_item_speeds
withered_tree_item_speeds:
.float 1.75 ; Initial forward velocity
.float 30 ; Initial Y velocity
.float -2.1 ; Gravity (Y acceleration)




.global create_item_for_withered_trees_without_setting_speeds
create_item_for_withered_trees_without_setting_speeds:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

bl custom_createItem

; We need to set our custom flag at withered_tree_entity+0x212 to 1 to prevent withered_tree_item_try_give_momentum from setting the speeds for this item actor.
li r5, 1
stb r5, 0x212 (r31)

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




; Custom function that checks if the warp down to Hyrule should be unlocked.
; Requirements: Must have all 8 pieces of the Triforce.
.global check_hyrule_warp_unlocked
check_hyrule_warp_unlocked:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

lis r3, 0x803C4C08@ha
addi r3, r3, 0x803C4C08@l

addi r3, r3, 180
bl getTriforceNum__20dSv_player_collect_cFv
cmpwi r3, 8
bge hyrule_warp_unlocked

hyrule_warp_not_unlocked:
li r3, 0
b hyrule_warp_end

hyrule_warp_unlocked:
li r3, 1

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
.byte 69, 3
.short 0x4000
.float -256.939, 0, -778




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




; Add a check right before playing the item get music to handle playing special item get music (pearls and songs).
; The vanilla game played the pearl music as part of the .stb cutscenes where you get the pearls, so the regular item get code had no reason to check for pearls originally.
; In the vanilla game Link only gets songs via 059get_dance actions, so that action would play the song get music, but the 011get_item action had no reason to check for songs.
.global check_play_special_item_get_music
check_play_special_item_get_music:

lwz r3, -0x69D0 (r13) ; Replace the line we overwrote to jump here

; Check if the item ID (in r0) matches any of the items with special music.
cmplwi r0, 0x69 ; Nayru's Pearl
beq play_pearl_item_get_music
cmplwi r0, 0x6A ; Din's Pearl
beq play_pearl_item_get_music
cmplwi r0, 0x6B ; Farore's Pearl
beq play_pearl_item_get_music
cmplwi r0, 0x6D ; Wind's Requiem
beq play_song_get_music
cmplwi r0, 0x6E ; Ballad of Gales
beq play_song_get_music
cmplwi r0, 0x6F ; Command Melody
beq play_song_get_music
cmplwi r0, 0x70 ; Earth God's Lyric
beq play_song_get_music
cmplwi r0, 0x71 ; Wind God's Aria
beq play_song_get_music
cmplwi r0, 0x72 ; Song of Passing
beq play_song_get_music
b 0x8012E3EC ; If not, return to the code that plays the normal item get music

play_pearl_item_get_music:
lis r4, 0x8000004F@ha ; BGM ID for the pearl item get music
addi r4, r4, 0x8000004F@l
b 0x8012E3F4 ; Jump to the code that plays the normal item get music

play_song_get_music:
lis r4, 0x80000027@ha ; BGM ID for the song get music
addi r4, r4, 0x80000027@l
b 0x8012E3F4 ; Jump to the code that plays the normal item get music




; Check the ID of the upcoming text command to see if it's a custom one, and runs custom code for it if so.
.global check_run_new_text_commands
check_run_new_text_commands:
clrlwi. r6,r0,24
bne check_run_new_text_commands_check_failed

lbz r6,3(r3)
cmplwi r6,0
bne check_run_new_text_commands_check_failed

lbz r6,4(r3)
cmplwi r6, 0x4B ; Lowest key counter text command ID
blt check_run_new_text_commands_check_failed
cmplwi r6, 0x4F ; Highest key counter text command ID
bgt check_run_new_text_commands_check_failed

mr r3,r31
mr r4, r6
bl exec_curr_num_keys_text_command
b 0x80034D34 ; Return (to after a text command has been successfully executed)


check_run_new_text_commands_check_failed:
clrlwi. r6,r0,24 ; Replace the line we overwrote to jump here
b 0x80033E78 ; Return (to back inside the code to check what text command should be run)




; Updates the current message string with the number of keys for a certain dungeon.
.global exec_curr_num_keys_text_command
exec_curr_num_keys_text_command:
stwu sp, -0x50 (sp)
mflr r0
stw r0, 0x54 (sp)
stw r31, 0xC (sp)
stw r30, 8 (sp)
mr r31, r3

; Convert the text command ID to the dungeon stage ID.
; The text command ID ranges from 0x4B-0x4F, for DRC, FW, TotG, ET, and WT.
; The the dungeon stage IDs for those same 5 dungeons range from 3-7.
; So just subtract 0x48 to get the right stage ID.
addi r4, r4, -0x48


lis r3, 0x803C53A4@ha ; This value is the stage ID of the current stage
addi r3, r3, 0x803C53A4@l
lbz r5, 0 (r3)
cmpw r5, r4 ; Check if we're currently in the right dungeon for this key
beq exec_curr_num_keys_text_command_in_correct_dungeon

exec_curr_num_keys_text_command_not_in_correct_dungeon:
; Read the current number of small keys from that dungeon's stage info.
lis r3, 0x803C4F88@ha ; List of all stage info
addi r3, r3, 0x803C4F88@l
mulli r4, r4, 0x24 ; Use stage ID of the dungeon as the index, each entry in the list is 0x24 bytes long
add r3, r3, r4
lbz r4, 0x20 (r3) ; Current number of keys for the correct dungeon
mr r30, r3 ; Remember the correct stage info pointer for later when we check the big key
b exec_curr_num_keys_text_command_after_reading_num_keys

exec_curr_num_keys_text_command_in_correct_dungeon:
; Read the current number of small keys from the currently loaded dungeon info.
lis r3, 0x803C5380@ha ; Currently loaded stage info
addi r3, r3, 0x803C5380@l
lbz r4, 0x20 (r3) ; Current number of keys for the current dungeon
mr r30, r3 ; Remember the correct stage info pointer for later when we check the big key


exec_curr_num_keys_text_command_after_reading_num_keys:
; Convert int to string
addi r3, sp, 0x1C
li r5, 0
bl fopMsgM_int_to_char__FPcib

; Check whether the player has the big key or not.
lbz r4, 0x21 (r30) ; Bitfield of dungeon-specific flags in the appropriate stage info
rlwinm. r4, r4, 0, 29, 29 ; Extract the has big key bit
beq exec_curr_num_keys_text_command_does_not_have_big_key

exec_curr_num_keys_text_command_has_big_key:
; Append the " +Big" text
addi r3, sp, 0x1C
lis r4, key_text_command_has_big_key_text@ha
addi r4, r4, key_text_command_has_big_key_text@l
bl strcat
b exec_curr_num_keys_text_command_after_appending_big_key_text

exec_curr_num_keys_text_command_does_not_have_big_key:
; Append some whitespace so that the text stays in the same spot regardless of whether you have the big key or not
addi r3, sp, 0x1C
lis r4, key_text_command_does_not_have_big_key_text@ha
addi r4, r4, key_text_command_does_not_have_big_key_text@l
bl strcat

exec_curr_num_keys_text_command_after_appending_big_key_text:


; Concatenate to one of the main strings
lwz r3, 0x60(r31)
addi r4, sp, 0x1C
bl strcat

; Concatenate to one of the main strings
lwz r3, 0x68(r31)
addi r4, sp, 0x1C
bl strcat

; Increase the offset within the encoded message string to be past the end of this text command
lwz r4, 0x118(r31)
addi r4, r4, 5 ; Note that technically, this command length value should be dynamically read from [cmd+1]. But because it's always 5 for the custom commands it doesn't matter and it can be hardcoded instead.
stw r4, 0x118(r31)

; Note: There are some other things that the vanilla text commands did that are currently not implemented for these custom ones. Such as what appears to be keeping track of the current line length, possibly for word wrapping or text alignment purposes (which aren't necessary for the Key Bag).

lwz r30, 8 (sp)
lwz r31, 0xC (sp)
lwz r0, 0x54 (sp)
mtlr r0
addi sp, sp, 0x50
blr

key_text_command_has_big_key_text:
.string " +Big"
key_text_command_does_not_have_big_key_text:
.string "     "




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
lbz r0, 9 (r3) ; Read the byte containing the stage ID+is dungeon bit
rlwinm. r0, r0, 0, 31, 31 ; Extract the is dungeon bit
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




.global dragon_tingle_statue_item_get_func
dragon_tingle_statue_item_get_func:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

lis r3, 0x803C522C@ha
addi r3, r3, 0x803C522C@l
li r4, 0x6A04 ; Unused event bit we use for Dragon Tingle Statue
bl onEventBit__11dSv_event_cFUs

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr


.global forbidden_tingle_statue_item_get_func
forbidden_tingle_statue_item_get_func:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

lis r3, 0x803C522C@ha
addi r3, r3, 0x803C522C@l
li r4, 0x6A08 ; Unused event bit we use for Forbidden Tingle Statue
bl onEventBit__11dSv_event_cFUs

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr


.global goddess_tingle_statue_item_get_func
goddess_tingle_statue_item_get_func:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

lis r3, 0x803C522C@ha
addi r3, r3, 0x803C522C@l
li r4, 0x6A10 ; Unused event bit we use for Goddess Tingle Statue
bl onEventBit__11dSv_event_cFUs

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr


.global earth_tingle_statue_item_get_func
earth_tingle_statue_item_get_func:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

lis r3, 0x803C522C@ha
addi r3, r3, 0x803C522C@l
li r4, 0x6A20 ; Unused event bit we use for Earth Tingle Statue
bl onEventBit__11dSv_event_cFUs

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr


.global wind_tingle_statue_item_get_func
wind_tingle_statue_item_get_func:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

lis r3, 0x803C522C@ha
addi r3, r3, 0x803C522C@l
li r4, 0x6A40 ; Unused event bit we use for Wind Tingle Statue
bl onEventBit__11dSv_event_cFUs

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr


; This function checks if you own a certain Tingle Statue.
; It's designed to replace the original calls to dComIfGs_isStageTbox__Fii, so it takes the same arguments as that function.
; Argument r3 - the stage ID of the stage info to check a chest in.
; Argument r4 - the opened flag index of the chest to check.
; This function, instead of checking if certain chests are open, checks if the unused event bits we use for certain Tingle Statues have been set.
.global check_tingle_statue_owned
check_tingle_statue_owned:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

cmpwi r4, 0xF ; The opened flag index (argument r4) for tingle statue chests should always be 0xF.
bne check_tingle_statue_owned_invalid

; The stage ID (argument r3) determines which dungeon it's checking.
cmpwi r3, 3
beq check_dragon_tingle_statue_owned
cmpwi r3, 4
beq check_forbidden_tingle_statue_owned
cmpwi r3, 5
beq check_goddess_tingle_statue_owned
cmpwi r3, 6
beq check_earth_tingle_statue_owned
cmpwi r3, 7
beq check_wind_tingle_statue_owned
b check_tingle_statue_owned_invalid

check_dragon_tingle_statue_owned:
li r4, 0x6A04 ; Unused event bit
b check_tingle_statue_owned_event_bit

check_forbidden_tingle_statue_owned:
li r4, 0x6A08 ; Unused event bit
b check_tingle_statue_owned_event_bit

check_goddess_tingle_statue_owned:
li r4, 0x6A10 ; Unused event bit
b check_tingle_statue_owned_event_bit

check_earth_tingle_statue_owned:
li r4, 0x6A20 ; Unused event bit
b check_tingle_statue_owned_event_bit

check_wind_tingle_statue_owned:
li r4, 0x6A40 ; Unused event bit

check_tingle_statue_owned_event_bit:
lis r3, 0x803C522C@ha
addi r3, r3, 0x803C522C@l
bl isEventBit__11dSv_event_cFUs
b check_tingle_statue_owned_end

check_tingle_statue_owned_invalid:
; If the function call was somehow invalid, return false.
li r3, 0

check_tingle_statue_owned_end:
lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




; Manually animate rainbow rupees to cycle through all other rupee colors.
; In order to avoid an abrupt change from silver to green when it loops, we make the animation play forward and then backwards before looping, so it's always a smooth transition.
.global check_animate_rainbow_rupee_color
check_animate_rainbow_rupee_color:

; Check if the color for this rupee specified in the item resources is 7 (originally unused, we use it as a marker to separate the rainbow rupee from other color rupees).
cmpwi r0, 7
beq animate_rainbow_rupee_color

; If it's not the rainbow rupee, replace the line of code we overwrote to jump here, and then return to the regular code for normal rupees.
lfd f1, -0x5DF0 (rtoc)
b 0x800F93F8

animate_rainbow_rupee_color:

; If it is the rainbow rupee, we need to increment the current keyframe (a float) by certain value every frame.
; (Note: The way this is coded would increase it by this value multiplied by the number of rainbow rupees being drawn. This is fine since there's only one rainbow rupee but would cause issues if we placed multiple of them. Would need to find a different place to increment the keyframe in that case, somewhere only called once per frame.)
lis r5, rainbow_rupee_keyframe@ha
addi r5, r5, rainbow_rupee_keyframe@l
lfs f1, 0 (r5) ; Read current keyframe
lfs f0, 4 (r5) ; Read amount to add to keyframe per frame
fadds f1, f1, f0 ; Increase the keyframe value

lfs f0, 8 (r5) ; Read the maximum keyframe value
fcmpo cr0,f1,f0
; If we're less than the max we don't need to reset the value
blt store_rainbow_rupee_keyframe_value

; If we're greater than the max, reset the current keyframe to the minimum.
; The minimum is actually the maximum negated. This is to signify that we're playing the animation backwards.
lfs f1, 0xC (r5)

store_rainbow_rupee_keyframe_value:
stfs f1, 0 (r5) ; Store the new keyframe value back

; Take the absolute value of the keyframe. So instead of going from -6 to +6, the value we pass as the actual keyframe goes from 6 to 0 to 6.
fabs f1, f1

b 0x800F9410

.global rainbow_rupee_keyframe
rainbow_rupee_keyframe:
.float 0.0 ; Current keyframe, acts as a global variable modified every frame
.float 0.15 ; Amount to increment keyframe by every frame a rainbow rupee is being drawn
.float 6.0 ; Max keyframe, when it should loop
.float -6.0 ; Minimum keyframe




; Handle giving the two randomized items when Doc Bandam makes Green/Blue Potions for the first time.
.global doc_bandam_check_new_potion_and_give_free_item
doc_bandam_check_new_potion_and_give_free_item:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

lwz r0, 0x7C4 (r28) ; Read the current message ID Doc Bandam is on (r28 has the Doc Bandam entity)
cmpwi r0, 7627 ; This message ID means he just made a brand new potion for the first time
; Any other message ID means he's either giving you or selling you a type he already made before.
; So do not give a randomized item in those cases.
bne doc_bandam_give_item

; If we're on a newly made potion we need to change the item ID in r4 to be the randomized item
cmpwi r4, 0x52 ; Green Potion item ID
beq doc_bandam_set_randomized_green_potion_item_id
cmpwi r4, 0x53 ; Blue Potion item ID
beq doc_bandam_set_randomized_blue_potion_item_id
; If it's not either of those something unexpected happened, so just give whatever item ID it was originally supposed to give
b doc_bandam_give_item

doc_bandam_set_randomized_green_potion_item_id:
lis r4, doc_bandam_green_potion_slot_item_id@ha
addi r4, r4, doc_bandam_green_potion_slot_item_id@l
lbz r4, 0 (r4) ; Load what item ID is in the this slot. This value is updated by the randomizer when it randomizes that item.
b doc_bandam_give_item

doc_bandam_set_randomized_blue_potion_item_id:
lis r4, doc_bandam_blue_potion_slot_item_id@ha
addi r4, r4, doc_bandam_blue_potion_slot_item_id@l
lbz r4, 0 (r4) ; Load what item ID is in the this slot. This value is updated by the randomizer when it randomizes that item.

doc_bandam_give_item:
bl fopAcM_createItemForPresentDemo__FP4cXyziUciiP5csXyzP4cXyz

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr


.global doc_bandam_green_potion_slot_item_id
doc_bandam_green_potion_slot_item_id:
.byte 0x52 ; Default item ID is Green Potion. This value is updated by the randomizer when this item is randomized.
.global doc_bandam_blue_potion_slot_item_id
doc_bandam_blue_potion_slot_item_id:
.byte 0x53 ; Default item ID is Blue Potion. This value is updated by the randomizer when this item is randomized.
.align 2 ; Align to the next 4 bytes




.global hurricane_spin_item_resource_arc_name
hurricane_spin_item_resource_arc_name:
.string "Vscroll"
.align 2 ; Align to the next 4 bytes




; In vanilla, the Deluxe Picto Box item get func doesn't update the Picto Box equipped on the X/Y/Z button.
; This causes it to not work correctly until the equipped item is fixed (by reloading the area or manually re-equipping it).
; This custom code adds a check to fix it automatically into the item get func.
.global deluxe_picto_box_item_func_fix_equipped_picto_box
deluxe_picto_box_item_func_fix_equipped_picto_box:
stb r0, 0x44 (r3) ; Replace the line of code we overwrote to jump heree

li r4, 0 ; The offset for which button to check next (0/1/2 for X/Y/Z)
li r0, 3 ; How many times to loop (3 buttons)
mtctr r0

deluxe_picto_box_item_func_fix_equipped_picto_box_loop_start:
add r5, r3, r4 ; Add the current button offset for this loop to the pointer
lbz r0, 0x5BD3 (r5) ; Read the item ID on the current button
; (Note: r3 starts with 803C4C08 in it, so offset 5BD3 is used to get the list of items on the X/Y/Z buttons, at 803CA7DB.)
cmplwi r0, 0x23 ; Normal Picto Box ID
; If this button doesn't have the normal Picto Box equipped, continue the loop.
bne deluxe_picto_box_item_func_fix_equipped_picto_box_continue_loop

; If this button does have the normal Picto Box equipped, replace it with the Deluxe Picto Box.
li r0, 0x26 ; Deluxe Picto Box ID
stb r0, 0x5BD3 (r5)

deluxe_picto_box_item_func_fix_equipped_picto_box_continue_loop:
addi r4, r4, 1
bdnz deluxe_picto_box_item_func_fix_equipped_picto_box_loop_start

b 0x800C3424 ; Return




.global ballad_of_gales_warp_table
ballad_of_gales_warp_table:
; For reference, here is the original table from vanilla:
;.byte -2, -2,  0, -1,  1, -1,  7
;.byte  0, -2,  1,  0,  2, -1,  7
;.byte  2, -2,  2,  1, -1,  0,  7
;.byte -2,  0,  3, -1,  4,  7,  8
;.byte  1,  0,  4,  3, -1,  7,  8
;.byte  2,  2,  5,  8, -1,  4,  6
;.byte -2,  3,  6,  5, -1,  8, -1
;.byte -1, -1,  7, -1, -1,  0,  3
;.byte  0,  2,  8, -1,  5,  3,  6

; Custom table:
.byte -2, -2,  0,  9,  1,  9,  7
.byte  0, -2,  1,  0,  2, -1,  7
.byte  2, -2,  2,  1, -1,  0,  7
.byte -2,  0,  3, -1,  4,  7,  8
.byte  1,  0,  4,  3, -1,  7,  8
.byte  2,  2,  5,  8, -1,  4,  6
.byte -2,  3,  6,  5, -1,  8, -1
.byte -1, -1,  7, -1, -1,  0,  3
.byte  0,  2,  8, -1,  5,  3,  6
.byte -3, -3,  9, -1,  0, -1,  0

.align 2 ; Align to the next 4 bytes

.global ballad_of_gales_warp_float_bank
ballad_of_gales_warp_float_bank:
; X positions for each warp
.float -193, -82, 30, -193, -26, 30, -193, -137, -83, -249
; Y positions for each warp
.float -137, -137, -137, -25, -25, 86, 145, -80, 86, -193
; Not sure what these are, but they need to be here because the code reads them from the same symbol as the X/Y positions
.float 1.6, 0.75




; Since we couldn't put the new message ID for the custom warp's confirmation dialog text right after the original ones, we need custom code to return the custom message ID.
.global set_warp_confirm_dialog_message_id_for_custom_warps
set_warp_confirm_dialog_message_id_for_custom_warps:
cmpwi r31, 9 ; Forsaken Fortress Warp index
bne set_warp_confirm_dialog_message_id_for_custom_warps_not_custom

li r10, 848 ; Custom message ID
b 0x801B80F8 ; Return to normal code after deciding message ID

set_warp_confirm_dialog_message_id_for_custom_warps_not_custom:
addi r10, r31, 69 ; Replace the line we overwrote to jump here
b 0x801B80F8 ; Return to normal code after deciding message ID




; Fix the lower body of a Stalfos not dying when the upper body dies to light arrows.
.global stalfos_kill_lower_body_when_upper_body_light_arrowed
stalfos_kill_lower_body_when_upper_body_light_arrowed:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

bl fopAcIt_Judge__FPFPvPv_PvPv ; Get upper body entity
cmplwi r3, 0
beq stalfos_kill_lower_body_when_upper_body_light_arrowed_end

lbz r0, 0x1FAE (r3) ; Counter for how many frames the upper body has been dying to light arrows
cmpwi r0, 0
beq stalfos_kill_lower_body_when_upper_body_light_arrowed_end ; The upper body hasn't been hit with light arrows, so don't kill the lower body either

lbz r0, 0x1FAE (r31) ; Counter for how many frames the lower body has been dying to light arrows
cmpwi r0, 0
bne stalfos_kill_lower_body_when_upper_body_light_arrowed_end ; The lower body is already dying to light arrows, so don't reset its counter

li r0, 1
stb r0, 0x1FAE (r31) ; Start the lower body's counter for dying to light arrows at 1

stalfos_kill_lower_body_when_upper_body_light_arrowed_end:
lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




; Fix Miniblins not setting a switch on death if killed with Light Arrows.
.global miniblin_set_death_switch_when_light_arrowed
miniblin_set_death_switch_when_light_arrowed:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

bl Set__8dCcD_SphFRC11dCcD_SrcSph ; Replace the function call we overwrote to call this custom function

lbz r0, 0x2B4 (r29) ; Read the behavior type param for the Miniblin
cmpwi r0, 0 ; Behavior type 0 is a respawning Miniblin
beq miniblin_set_death_switch_when_light_arrowed_end ; Respawning Miniblins should not set a switch when they die, so don't do anything

; Otherwise it's a single Miniblin, so it should set a switch when it dies.
lbz r0, 0x2B8 (r29) ; Read the switch index param the non-respawning Miniblin should set on death
stb r0, 0x995 (r29) ; Store it into the Miniblin's enemyice struct as the switch index it should set when it dies to Light Arrows.
; Note: The enemy_ice function does not set the switch specified here in the case that it's switch index 0, but the Miniblin itself would even for index 0. This doesn't matter in practice because no Miniblins placed in the game are supposed to set switch index 0 on death.

miniblin_set_death_switch_when_light_arrowed_end:
lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




; Fix child Poes not telling Jalhalla they died when hit with light arrows.
.global poe_fix_light_arrows_bug
poe_fix_light_arrows_bug:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

lbz r0, 0x285 (r31) ; Read the Poe's current HP
extsb. r0,r0
ble poe_fix_light_arrows_bug_poe_is_dead ; Consider the Poe dead if its HP is <= 0

lbz r0, 0x88A (r31) ; Read the Poe's dying to light arrows counter
cmpwi r0, 0
bgt poe_fix_light_arrows_bug_poe_is_dead ; Consider the Poe dead if it was hit with light arrows, even if its HP isn't 0 yet

b poe_fix_light_arrows_bug_return_false ; Otherwise consider the Poe alive

poe_fix_light_arrows_bug_poe_is_dead:
bl fopAcM_SearchByID__FUiPP10fopAc_ac_c ; Replace the function call we overwrote to call this custom function

; Then we need to reproduce most of the rest of the original Big_pow_down_check function.
; The reason for this is a weird quirk Poes in the Jalhalla fight have where if they're killed in the last 4 frames before Jalhalla reforms, they will "unkill" themselves so they can join back up with Jalhalla.
; We need to unset the dying to light arrows counter in that case as well.

cmpwi r3, 0
beq poe_fix_light_arrows_bug_return_false
lwz r4, 0x18 (sp) ; Read Jalhalla entity pointer (original code used sp+8 but this function's stack offset is +0x10)
cmplwi r4, 0
beq poe_fix_light_arrows_bug_return_false
lha r0, 8 (r4)
cmpwi r0, 0xD4 ; Check to be sure the supposed Jalhalla entity is actually an instance of bpw_class.
bne poe_fix_light_arrows_bug_return_false
lha r0, 0x446 (r4)
cmpwi r0, 0x6F ; Check Jalhalla's state or something, 0x6F is for when the child Poes are running around
bne poe_fix_light_arrows_bug_unkill_poe
lha r0, 0x44E (r4) ; Read number of frames left until Jalhalla reforms
cmpwi r0, 3 ; Poes killed within the last 4 frames before Jalhalla reforms shouldn't actually die
ble poe_fix_light_arrows_bug_unkill_poe
lbz r3, 0x285 (r4)
addi r0, r3, -1 ; Decrement Jalhalla's HP
stb r0, 0x285 (r4)
lwz r3, 0x18 (sp) ; Read Jalhalla entity pointer again
lbz r0, 0x285 (r3) ; Check if Jalhalla's HP is zero, meaning this Poe that just died was the last one
extsb. r0,r0
bgt poe_fix_light_arrows_bug_not_the_last_poe
li r0, 1
stb r0, 0x344 (r31)
poe_fix_light_arrows_bug_not_the_last_poe:
li r0, 1
stb r0, 0x345 (r31)
b poe_fix_light_arrows_bug_return_false

poe_fix_light_arrows_bug_unkill_poe:
li r0,4
stb r0, 0x285 (r31)

; These 2 lines are the new code:
li r0, 0
stb r0, 0x88A (r31) ; Set the Poe's dying to light arrows counter to zero to stop it from dying

li r3, 1
b poe_fix_light_arrows_bug_end

poe_fix_light_arrows_bug_return_false:
li r3, 0

poe_fix_light_arrows_bug_end:
lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




.global magtail_respawn_when_head_light_arrowed
magtail_respawn_when_head_light_arrowed:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

bl GetTgHitObj__12dCcD_GObjInfFv ; Replace the function call we overwrote to call this custom function

; Then we need to reproduce a few lines of code from the original
stw r3, 0x30 (r1)
addi r0, r30, 0x1874
stw r0, 0x44 (r1)
lwz r0, 0x10 (r3) ; Read the bitfield of damage types done by the actor that just damaged this Magtail
rlwinm. r0, r0, 0, 11, 11 ; Check the Light Arrows damage type

; Then if the Light Arrows bit was set, we store true to magtail_entity+0x1CBC to signify that the Magtail should respawn.
; (We can't use the original branch on the Light Arrows bit because it's inside the REL.)
beq magtail_respawn_when_head_light_arrowed_end
li r0, 1
stb r0, 0x1CBC (r30)

magtail_respawn_when_head_light_arrowed_end:
lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




.global set_next_stage_and_stop_sub_bgm
set_next_stage_and_stop_sub_bgm:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

; First replace the function call we overwrote to call this custom function.
bl dComIfGp_setNextStage__FPCcsScScfUliSc

; Then stop the music.
lis r3, 0x803F7710@ha
addi r3, r3, 0x803F7710@l
lwz r3, 0 (r3)
bl subBgmStop__11JAIZelBasicFv

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




; Sets both maximum and active health, and rounds down active health to 4 so that you don't start a new file with 11 and a quarter hearts.
.global set_starting_health
set_starting_health:

; Base address to write health to is still stored in r3 from init__10dSv_save_cFv
lis r4, starting_quarter_hearts@ha
addi r4, r4, starting_quarter_hearts@l
lhz r0, 0 (r4)
sth r0, 0 (r3) ; Store maximum HP (including unfinished heart pieces)
rlwinm r0,r0,0,0,29
sth r0, 2 (r3) ; Store current HP (not including unfinished heart pieces)

b 0x800589B4




.global get_current_health_for_file_select_screen
get_current_health_for_file_select_screen:

; Read the first character of the player's name on this save file.
; If it's null, the save file does not exist. (This is how the vanilla code detected nonexistent save files as well.)
lbz r0, 0x157 (r29)
cmpwi r0, 0
beq get_current_health_for_file_select_screen_for_blank_save_file

get_current_health_for_file_select_screen_for_existing_save_file:
; For existing save files, we want to read the amount of health in the save.
; Just replace the line of code we overwrote to jump here and then return.
lhz r3, 2 (r29)
b get_current_health_for_file_select_screen_end

get_current_health_for_file_select_screen_for_blank_save_file:
; For blank save files, read the initial HP instead of the wrong HP value saved to the deleted save file.
lis r4, starting_quarter_hearts@ha
addi r4, r4, starting_quarter_hearts@l
lhz r3, 0 (r4)
rlwinm r3,r3,0,0,29 ; Round down initial max HP to 4 to get rid of unfinished heart pieces

get_current_health_for_file_select_screen_end:
b 0x80182508




.global get_max_health_for_file_select_screen
get_max_health_for_file_select_screen:

; Read the first character of the player's name on this save file.
; If it's null, the save file does not exist. (This is how the vanilla code detected nonexistent save files as well.)
lbz r0, 0x157 (r29)
cmpwi r0, 0
beq get_max_health_for_file_select_screen_for_blank_save_file

get_max_health_for_file_select_screen_for_existing_save_file:
; For existing save files, we want to read the amount of health in the save.
; Just replace the line of code we overwrote to jump here and then return.
lhz r0, 0 (r29)
b get_max_health_for_file_select_screen_end

get_max_health_for_file_select_screen_for_blank_save_file:
; For blank save files, read the initial HP instead of the wrong HP value saved to the deleted save file.
lis r4, starting_quarter_hearts@ha
addi r4, r4, starting_quarter_hearts@l
lhz r0, 0 (r4)

get_max_health_for_file_select_screen_end:
b 0x80182548




.global check_player_in_casual_clothes
check_player_in_casual_clothes:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

lis r3, should_start_with_heros_clothes@ha
addi r3, r3, should_start_with_heros_clothes@l
lbz r3, 0 (r3) ; Load bool of whether player should start with Hero's clothes
cmpwi r3, 1
beq check_player_in_casual_clothes_hero

check_player_in_casual_clothes_casual:
li r3, 1
b check_player_in_casual_clothes_end

check_player_in_casual_clothes_hero:
li r3, 0

check_player_in_casual_clothes_end:
lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




.global change_game_state_check_enter_debug_map_select
change_game_state_check_enter_debug_map_select:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

lis r7, mPadButton__10JUTGamePad@ha ; Bitfield of currently pressed buttons
addi r7, r7, mPadButton__10JUTGamePad@l
lwz r0, 0 (r7)
rlwinm. r0, r0, 0, 20, 20 ; AND with 0x800 to check if the Y button is held down

; If Y is not down, just change to whatever game state the original code was going to (in r4)
beq change_game_state_check_enter_debug_map_select_change_game_state

; If Y is down, change to game state 6 (map select) instead.
li r4, 6

change_game_state_check_enter_debug_map_select_change_game_state:
; Change the game state (replacing the call we overwrote to call this custom function).
bl fopScnM_ChangeReq__FP11scene_classssUs

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




.close
