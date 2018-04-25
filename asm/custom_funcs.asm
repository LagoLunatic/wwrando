
.org 0x803FCFA8

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
li r4, 0x2D01 ; Saw cutscene before Helmaroc King where Aryll is rescued
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


; Function end stuff
lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr
