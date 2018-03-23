
.text
.globl _start
_start:

# Function start stuff
stwu sp, -0x10 (sp)
mflr r0
stw r0, 0x14 (sp)


bl init__10dSv_save_cFv # To call this custom func we overwrote a call to init__10dSv_save_cFv, so call that now.


bl item_func_sword__Fv
bl item_func_shield__Fv
bl item_func_normal_sail__Fv


lis r3, 0x803C
addi r3, r3, 0x522C
li r4, 0x0F80 # KORL_UNLOCKED_AND_SPAWN_ON_WINDFALL
bl onEventBit__11dSv_event_cFUs
li r4, 0x0908 # SAIL_INTRODUCTION_TEXT_AND_MAP_UNLOCKED
bl onEventBit__11dSv_event_cFUs
li r4, 0x2A08 # ENTER_KORL_FOR_THE_FIRST_TIME_AND_SPAWN_ANYWHERE
bl onEventBit__11dSv_event_cFUs
li r4, 0x2A80 # HAS_HEROS_CLOTHES
bl onEventBit__11dSv_event_cFUs
li r4, 0x3510 # HAS_SEEN_INTRO
bl onEventBit__11dSv_event_cFUs

lis r3, 0x803C
addi r3, r3, 0x5D60
li r4, 0x0310 # Saw event where Grandma gives you the Hero's Clothes
bl onEventBit__11dSv_event_cFUs


# Function end stuff
lwz r0, 0x14 (sp)
mtlr r0
addi sp, sp, 0x10
blr
