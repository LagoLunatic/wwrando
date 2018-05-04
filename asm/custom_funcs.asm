
.org 0x803FCFA8

.global init_save_with_tweaks
init_save_with_tweaks:
; Function start stuff
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)


bl init__10dSv_save_cFv ; To call this custom func we overwrote a call to init__10dSv_save_cFv, so call that now.


bl item_func_sword__Fv
bl item_func_shield__Fv
bl item_func_normal_sail__Fv
bl item_func_wind_tact__Fv ; Wind Waker
bl item_func_tact_song1__Fv ; Wind's Requiem
bl item_func_tact_song2__Fv ; Ballad of Gales


lis r3, 0x803C
addi r3, r3, 0x522C
li r4, 0x3510 ; HAS_SEEN_INTRO
bl onEventBit__11dSv_event_cFUs
li r4, 0x2A80 ; HAS_HEROS_CLOTHES
bl onEventBit__11dSv_event_cFUs
li r4, 0x0520 ; GOSSIP_STONE_AT_FF1 (Causes Aryll and the pirates to disappear from Outset)
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
li r4, 0x1F02 ; TALKED_TO_KORL_AFTER_GETTING_BOMBS
bl onEventBit__11dSv_event_cFUs
li r4, 0x2F20 ; Talked to KoRL after getting Nayru's Pearl
bl onEventBit__11dSv_event_cFUs
li r4, 0x3840 ; TALKED_TO_KORL_POST_TOWER_CUTSCENE
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
li r4, 0x2D08 ; HYRULE_3_WARP_CUTSCENE
bl onEventBit__11dSv_event_cFUs
li r4, 0x3980 ; HYRULE_3_ELECTRICAL_BARRIER_CUTSCENE_1
bl onEventBit__11dSv_event_cFUs

lis r3, 0x803C
addi r3, r3, 0x5D60
li r4, 0x0310 ; Saw event where Grandma gives you the Hero's Clothes
bl onEventBit__11dSv_event_cFUs


; Set four switch bits (0, 1, 3, 7) for several events that happen in the Fairy Woods on Outset.
; Setting these switches causes the Tetra hanging from a tree and rescuing her from Bokoblins events to be marked as finished.
; Also set the switch (9) for having seen the event where you enter the Rito Aerie for the first time and get the Delivery Bag.
; Also set the switch (8) for having unclogged the pond, since that boulder doesn't respond to normal bombs which would be odd.
; Also set the the switch (1E) for having seen the intro to the interior of the Forest Haven, where the camera pans up.
lis r3, 0x803C
addi r3, r3, 0x5118
lis r4, 0x4000
addi r4, r4, 0x038B
stw r4, 0 (r3)

; Set two switch bits (3E and 3F) for having unlocked the song tablets in the Earth and Wind Temple entrances.
lis r4, 0xC000
stw r4, 4 (r3)

; Set a switch bit (19) for the event on Greatfish Isle so that the endless night never starts.
lis r3, 0x803C
addi r3, r3, 0x4F8C
lis r4, 0x0200
stw r4, 0 (r3)
; Also set a switch bit (3F) for having seen the Windfall Island intro scene.
lis r4, 0x8000
stw r4, 4 (r3)
; Also set a switch bit (58) for having seen the short event when you enter Forsaken Fortress 2 for the first time.
lis r4, 0x0100
stw r4, 8 (r3)


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


; Function end stuff
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


lis r3, 0x803C
addi r3, r3, 0x4CBC
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


lis r3, 0x803C
addi r3, r3, 0x4C65
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

lis r3, 0x803C
addi r3, r3, 0x4C1A
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

lis r3, 0x803C
addi r3, r3, 0x4C72
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

lis r3, 0x803C
addi r3, r3, 0x4C71
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




.global hurricane_spin_item_func
hurricane_spin_item_func:
; Function start stuff
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

; Set bit 80 of byte 803C4CBF.
; That bit was unused in the base game, but we repurpose it to keep track of whether you have Hurricane Spin separately from whether you've seen the event where Orca would normally give you Hurricane Spin.
lis r3,0x803C4CBC@h
addi r3,r3,0x803C4CBC@l
li r4,3
li r5,7
bl onCollect__20dSv_player_collect_cFiUc

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

; Set bit 40 of byte 803C4CBF.
; That bit was unused in the base game, but we repurpose it to keep track of whether you've purchased whatever item is in the Bait Bag slot of Beedle's shop.
lis r3,0x803C4CBC@h
addi r3,r3,0x803C4CBC@l
li r4,3
li r5,6
bl onCollect__20dSv_player_collect_cFiUc

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr

.global check_shop_item_in_bait_bag_slot_sold_out
check_shop_item_in_bait_bag_slot_sold_out:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

; Check bit 40 of byte 803C4CBF, which was originally unused but we use it to keep track of whether the item in the Bait Bag slot has been purchased or not.
lis     r3,0x803C4CBC@h
addi    r3,r3,0x803C4CBC@l
li      r4,3
li      r5,6
bl      isCollect__20dSv_player_collect_cFiUc

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr




; This function takes the same arguments as fastCreateItem, but it loads in any unloaded models without crashing like createItem.
; This is so we can replace any randomized item spawns that use fastCreateItem with a call to this new function instead.
.global custom_createItem
custom_createItem:
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)

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

lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr
