
.open "sys/main.dol"
.org @NextFreeSpace

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

bl item_func_normal_sail__Fv
bl item_func_wind_tact__Fv ; Wind Waker
bl item_func_tact_song1__Fv ; Wind's Requiem
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

; Set the player's magic meter size based on the value of a custom symbol.
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

li r4, 0
ori r4, r4, 0xBFFF ; Bitfield of which pigs you brought to Rose during the prologue (Pink, Speckled, Black)
lis r5, captured_prologue_pigs_bitfield@ha 
addi r5, r5, captured_prologue_pigs_bitfield@l
lbz r5, 0 (r5) ; Load the randomized value to set the bitfield to
bl setEventReg__11dSv_event_cFUsUc

lis r4, g_dComIfG_gameInfo@ha
addi r4, r4, g_dComIfG_gameInfo@l
lis r5, option_targeting_mode@ha 
addi r5, r5, option_targeting_mode@l
lbz r5, 0 (r5) ; Load the targeting mode option the player set
stb r5, 0x1A6 (r4) ; 803C4DAE, the current targeting mode

lis r3, 0x803C5D60@ha
addi r3, r3, 0x803C5D60@l
li r4, 0x0310 ; Saw event where Grandma gives you the Hero's Clothes
bl onEventBit__11dSv_event_cFUs


; Set four switch bits (0, 1, 3, 7) for several events that happen in the Fairy Woods on Outset.
; Setting these switches causes the Tetra hanging from a tree and rescuing her from Bokoblins events to be marked as finished.
; Also set the switch (9) for having seen the event where you enter the Rito Aerie for the first time and get the Delivery Bag.
; Also set the switch (8) for having unclogged the pond, since that boulder doesn't respond to normal bombs which would be odd.
; Also set the switch (1E) for having seen the intro to the interior of the Forest Haven, where the camera pans up.
; Also set the switch (13) for having seen the camera panning towards the treasure chest in Windfall Town Jail.
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
; Also set a switch (0x47) for having hit the switch at Forest Haven to open up the hatch to the Nintendo Gallery.
; Also set a switch (0x5E) for the ladder leading up to the Nintendo Gallery being lowered.
lis r4, 0x4101
addi r4, r4, 0x0080
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
.space 103, 0xFF ; Allocate space for up to this many additional items (when changing this also update the constant in tweaks.py)
.byte 0xFF
.align 1 ; Align to the next 2 bytes
.global starting_quarter_hearts
starting_quarter_hearts:
.short 12 ; By default start with 12 quarter hearts (3 heart containers)
.global starting_magic
starting_magic:
.byte 16 ; By default start with 16 units of magic (small magic meter)
.global captured_prologue_pigs_bitfield
captured_prologue_pigs_bitfield:
.byte 0x04 ; By default, only have the black pig captured so that it becomes the big pig
.global option_targeting_mode ; AKA "OptAttentionType"
option_targeting_mode:
.byte 0x00 ; By default, use the "Hold" targeting mode

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

cmpwi r3, 0x3B
beq convert_progressive_shield_id
cmpwi r3, 0x3C
beq convert_progressive_shield_id

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

cmpwi r3, 0xB1
beq convert_progressive_magic_meter_id
cmpwi r3, 0xB2
beq convert_progressive_magic_meter_id

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


convert_progressive_shield_id:
lis r3, 0x803C4CBD@ha
addi r3, r3, 0x803C4CBD@l
lbz r4, 0 (r3) ; Bitfield of shields you own
cmpwi r4, 0
beq convert_progressive_shield_id_to_heros_shield
cmpwi r4, 1
beq convert_progressive_shield_id_to_mirror_shield
li r3, 0x3B ; Invalid shield state; this shouldn't happen so just return the base shield ID
b convert_progressive_item_id_func_end

convert_progressive_shield_id_to_heros_shield:
li r3, 0x3B
b convert_progressive_item_id_func_end
convert_progressive_shield_id_to_mirror_shield:
li r3, 0x3C
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


convert_progressive_magic_meter_id:
lis r3, 0x803C4C1B@ha
addi r3, r3, 0x803C4C1B@l
lbz r4, 0 (r3) ; Max magic meter
cmpwi r4, 0
beq convert_progressive_magic_meter_id_to_normal_magic_meter
cmpwi r4, 16
beq convert_progressive_magic_meter_id_to_magic_meter_upgrade
li r3, 0xB1 ; Invalid magic meter state; this shouldn't happen so just return the base magic meter ID
b convert_progressive_item_id_func_end

convert_progressive_magic_meter_id_to_normal_magic_meter:
li r3, 0xB1
b convert_progressive_item_id_func_end
convert_progressive_magic_meter_id_to_magic_meter_upgrade:
li r3, 0xB2
b convert_progressive_item_id_func_end


convert_progressive_item_id_func_end:
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




.global progressive_shield_item_func
progressive_shield_item_func:
; Function start stuff
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

lis r3, 0x803C4CBD@ha
addi r3, r3, 0x803C4CBD@l
lbz r4, 0 (r3) ; Bitfield of shields you own
cmpwi r4, 0
beq get_heros_shield
cmpwi r4, 1
beq get_mirror_shield
b shield_func_end

get_heros_shield:
bl item_func_shield__Fv
b shield_func_end

get_mirror_shield:
bl item_func_mirror_shield__Fv

shield_func_end:
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




.global progressive_magic_meter_item_func
progressive_magic_meter_item_func:
; Function start stuff
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)


lis r3, 0x803C4C1B@ha
addi r3, r3, 0x803C4C1B@l
lbz r4, 0 (r3) ; Max magic meter
cmpwi r4, 0
beq progressive_magic_meter_item_func_get_normal_magic_meter
cmpwi r4, 16
beq progressive_magic_meter_item_func_get_magic_meter_upgrade
b progressive_magic_meter_item_func_end

progressive_magic_meter_item_func_get_normal_magic_meter:
bl normal_magic_meter_item_func
b progressive_magic_meter_item_func_end

progressive_magic_meter_item_func_get_magic_meter_upgrade:
bl item_func_max_mp_up1__Fv


progressive_magic_meter_item_func_end:
; Function end stuff
lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




; Write our own base magic meter item get function because the vanilla one (item_func_magic_power__Fv) was just a placeholder.
.global normal_magic_meter_item_func
normal_magic_meter_item_func:
lis r3, 0x803C4C08@ha
addi r4, r3, 0x803C4C08@l
li r0, 16
sth r0, 0x5B78 (r4) ;  0x803CA780 (MP to gradually add to the current meter)
sth r0, 0x5B7C (r4) ;  0x803CA784 (MP to gradually add to the max meter)
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




; Custom function to check if a treasure chest open flag in the save file is set.
; This function has the benefit of not crashing like isStageTbox when used with test room.
; The downside is that this function doesn't work right if the player hasn't changed stages in between opening the chest and this check happening, so it should only be used when that is impossible.
; r3 - The stage info ID
; r4 - The treasure chest open flag index to check
.global custom_isTbox_for_unloaded_stage_save_info
custom_isTbox_for_unloaded_stage_save_info:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

mulli r0, r3, 0x24 ; Use stage info ID as the index, each entry in the list is 0x24 bytes long
lis r3, 0x803C4F88@ha ; List of all stage info
addi r3, r3, 0x803C4F88@l
add r3, r3, r0

bl isTbox__12dSv_memBit_cFi

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




.close
