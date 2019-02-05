
; 8005D618 is where the game calls the new game save init function.
; We replace this call with a call to our custom save init function.
.open "sys/main.dol"
.org 0x8005D618
  bl init_save_with_tweaks
.close




; nop out a couple lines so the long intro movie is skipped.
.open "sys/main.dol"
.org 0x80232C78
  nop
.org 0x80232C88
  nop
.close




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




; Normally the Great Fairies will give you the next tier max-up upgrade, depending on what you currently have.
; So if you already got the 1000 Rupee Wallet from one Great Fairy, the second one will give you the 5000 Rupee Wallet, regardless of the order you reach them in.
; This patch changes it so they always give a constant item even if you already have it, so that the item can be randomized safely.
.open "files/rels/d_a_bigelf.rel" ; Great Fairy
.org 0x217C
  ; Check this Great Fairy's index to determine what item to give.
  cmpwi r0, 1
  blt 0x21B8 ; 0, Northern Fairy Island Great Fairy. Give 1000 Rupee Wallet.
  beq 0x21C4 ; 1, Outset Island Great Fairy. Give 5000 Rupee Wallet.
  cmpwi r0, 3
  blt 0x21E4 ; 2, Eastern Fairy Island Great Fairy. Give 60 Bomb Bomb Bag.
  beq 0x21F0 ; 3, Southern Fairy Island Great Fairy. Give 99 Bomb Bomb Bag.
  cmpwi r0, 5
  blt 0x2210 ; 4, Western Fairy Island Great Fairy. Give 60 Arrow Quiver.
  beq 0x221C ; 5, Thorned Fairy Island Great Fairy. Give 99 Arrow Quiver.
  b 0x2228 ; Failsafe code in case the index was invalid (give a red rupee instead)
.close




; Fishmen usually won't appear until Gohma is dead. This removes that check from their code so they appear from the start.
.open "files/rels/d_a_npc_so.rel" ; Fishman
.org 0x3FD8
  ; Change the conditional branch to an unconditional branch.
  b 0x3FE4
.close




; The event where the player gets the Wind's Requiem actually gives that song to the player twice.
; The first one is hardcoded into Zephos's AI and only gives the song.
; The second is part of the event, and also handles the text, model, animation, etc, of getting the song.
; Getting the same item twice is a problem for some items, such as rupees. So we remove the first one.
.open "files/rels/d_a_npc_hr.rel" ; Zephos
.org 0x1164
  ; Branch to skip over the line of code where Zephos gives the Wind's Requiem.
  b 0x116C
.close




; The 6 Heart Containers that appear after you kill a boss are all created by the function createItemForBoss.
; createItemForBoss hardcodes the item ID 8, and doesn't care which boss was just killed. This makes it hard to randomize boss drops without changing all 6 in sync.
; So we make some changes to createItemForBoss and the places that call it so that each boss can give a different item.
.open "sys/main.dol"
; First we modify the createItemForBoss function itself to not hardcode the item ID as 8 (Heart Container).
; We nop out the two instructions that load 8 into r4. This way it simply passes whatever it got as argument r4 into the next function call to createItem.
.org 0x80026A90
  nop
.org 0x80026AB0
  nop
; Second we modify the code for the "disappear" cloud of smoke when the boss dies.
; This cloud of smoke is what spawns the item when Gohma, Kalle Demos, Helmaroc King, and Jalhalla die.
; So we need a way to pass the item ID from the boss's code to the disappear cloud's parameters and store them there.
; We do this by hijacking argument r7 when the boss calls createDisappear.
; Normally argument r7 is a byte, and gets stored to the disappear's params with mask 00FF0000.
; We change it to be a halfword and stored with the mask FFFF0000.
; The lower byte is unchanged from vanilla, it's still whatever argument r7 used to be for.
; But the upper byte, which used to be unused, now has the item ID in it.
.org 0x80027AC4
  rlwimi r4, r7, 16, 0, 15
; Then we need to read the item ID parameter when the cloud is about to call createItemForBoss.
.org 0x800E7A1C
  lbz r4, 0x00B0(r7)
.close
; Third we change how the boss item ACTR calls createItemForBoss.
; (This is the ACTR that appears if the player skips getting the boss item after killing the boss, and instead comes back and does the whole dungeon again.)
; Normally it sets argument r4 to 1, but createItemForBoss doesn't even use argument r4.
; So we change it to load one of its params (mask: 0000FF00) and use that as argument r4.
; This param was unused and just 00 in the original game, but the randomizer will set it to the item ID it randomizes to that location.
; Then we will be calling createItemForBoss with the item ID to spawn in argument r4. Which due to the above change, will be used correctly now.
.open "files/rels/d_a_boss_item.rel"
.org 0x1C4
  lbz r4, 0x00B2(r30)
.close
; The final change necessary is for all 6 bosses' code to be modified so that they pass the item ID to spawn to a function call.
; For Gohdan and Molgera, the call is to createItemForBoss directly, so argument r4 needs to be the item ID.
; For Gohma, Kalle Demos, Helmaroc King, and Jalhalla, they instead call createDisappear, so we need to upper byte of argument r7 to have the item ID.
; But the randomizer itself handles all 6 of these changes when randomizing, since these locations are all listed in the "Paths" of each item location. So no need to do anything here.




; The heart container item get function (item_func_utuwa_heart) usually handles setting the flag for having taken the current dungeon's boss item.
; But if the player got a heart container somewhere in a dungeon other than from the boss, this could cause the boss's actual item to disappear.
; We modify the code to remove the calls to set the flag.
.open "sys/main.dol"
.org 0x800C2FAC
  nop
.org 0x800C2FC4
  nop
.close




; Normally when the player takes a boss item drop, it would not set the flag for having taken the current dungeon's boss item, since in vanilla that was handled by the heart container's item get function.
; That could allow the player to get the item over and over again since the item never disappears.
; So we modify createItemForBoss to pass an item flag to createItem, so that the item properly keeps track of whether it has been taken.
; We use item flag 15 for all boss items, since that flag is not used by any items in any of the dungeons.
; (Note that since we're just setting an item flag, the special flag for the dungeon's boss item being taken is never set. But I don't believe that should cause any issues.)
.open "sys/main.dol"
.org 0x80026A94
  li r5, 0x15
.org 0x80026AB4
  li r5, 0x15
.close




; This makes the warps out of boss rooms always skip the cutscene usually shown the first time you beat the boss and warp out.
.open "files/rels/d_a_warpf.rel" ; Warp out of boss object
.org 0xC3C
  ; Function C3C of d_a_warpf.rel is checking if the post-boss cutscene for this dungeon has been viewed yet or not.
  ; Change it to simply always return true, so that it acts like it has been viewed from the start.
  li r3, 1
  blr
.close




; The Great Fairy inside the Big Octo is hardcoded to double your max magic meter (and fill up your current magic meter too).
; Since we randomize what item she gives you, we need to remove this code so that she doesn't always give you the increased magic meter.
.open "files/rels/d_a_bigelf.rel" ; Great Fairy
.org 0x7C4
  nop ; For max MP
.org 0x7D0
  nop ; For current MP
.close
; Also, the magic meter upgrade item itself only increases your max MP.
; In the vanilla game, the Great Fairy would also refill your MP for you.
; Therefore we modify the code of the magic meter upgrade to also refill your MP.
.open "sys/main.dol"
.org 0x800C4D14
  ; Instead of adding 32 to the player's previous max MP, simply set both the current and max MP to 32.
  li r0, 32
  sth r0, 0x5B78 (r4)
.close




; When salvage points decide if they should show their ray of light, they originally only checked if you
; have the appropriate Triforce Chart deciphered if the item there is actually a Triforce Shard.
; We don't want the ray of light to show until the chart is deciphered, so we change the salvage point code
; to check the chart index instead of the item ID when determining if it's a Triforce or not.
.open "files/rels/d_a_salvage.rel" ; Salvage point object
.org 0x10C0
  ; We replace the call to getItemNo, so it instead just adds 0x61 to the chart index.
  ; 0x61 to 0x68 are the Triforce Shard IDs, and 0 to 8 are the Triforce Chart indexes,
  ; so by adding 0x61 we simulate whether the item would be a Triforce Shard or not based on the chart index.
  addi r3, r19, 0x61
  ; Then we branch to skip the line of code that originally called getItemNo.
  ; We can't easily nop the line out, since the REL's relocation would overwrite our nop.
  b 0x10CC
.close




; The first instance of Medli, who gives the letter for Komali, can disappear under certain circumstances.
; For example, owning the half-power Master Sword makes her disappear. Deliving the letter to Komali also makes her disappear.
; So in order to avoid the item she gives being missable, we just remove it entirely.
; To do this we modify the chkLetterPassed function to always return true, so she thinks you've delivered the letter.
.open "sys/main.dol"
.org 0x8021BF80
  li r3, 1
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




; Remove the cutscene where the Tower of the Gods rises out of the sea.
; To do this we modify the goddess statue's code to skip starting the raising cutscene.
; Instead we branch to code that ends the current pearl-placing event after the tower raised event bit is set.
.open "files/rels/d_a_obj_doguu.rel" ; Goddess statues
.org 0x267C
  b 0x26A0
.close




; Normally whether you can use Hurricane Spin or not is determined by if the event bit for the event where Orca teaches it to you is set or not.
; But we want to separate the ability from the event so they can be randomized.
; To do this we change it to check event bit 6901 (bit 01 of byte 803C5295) instead. This bit was originally unused.
.open "sys/main.dol"
.org 0x80158C08
  li r4, 0x6901 ; Unused event bit
; Then change the Hurricane Spin's item get func to our custom function which sets this previously unused bit.
.org 0x80388B70 ; 0x803888C8 + 0xAA*4
  .int hurricane_spin_item_func
.close




; Normally Beedle checks if you've bought the Bait Bag by actually checking if you own the Bait Bag item.
; That method is problematic for many items that can get randomized into that shop slot, including progressive items.
; So we change the functions he calls to set the slot as sold out and check if it's sold out to custom functions.
; These custom functions use bit 40 of byte 803C4CBF, which was originally unused, to keep track of this.
.open "files/rels/d_a_npc_bs1.rel" ; Beedle
.org 0x7834
  ; Change the relocation for line 1CE8, which originally called SoldOutItem.
  .int set_shop_item_in_bait_bag_slot_sold_out
.org 0x7BD4
  ; Change the relocation for line 2DC4, which originally called checkGetItem.
  .int check_shop_item_in_bait_bag_slot_sold_out
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




; Three items are spawned by a call to fastCreateItem:
; * The item buried under black soil that you need the pig to dig up.
; * The item given by the withered trees.
; * The item hidden in a tree on Windfall.
; This is bad since fastCreateItem doesn't load the field item model in. If the model isn't already loaded the game will crash.
; So we add a new custom function to create an item and load the model, and replace the relevant calls so they call the new function.
; Buried item
.open "sys/main.dol"
.org 0x80056C0C ; In dig_main__13daTagKbItem_cFv
  ; Replace fastCreateItem call
  bl custom_createItem
  ; Then remove the code that sets bit 0x4000 of the bitfield at item_entity+0x1C4.
  ; This bit just seems to offset the item or something, but custom_createItem's item action does this anyway.
  ; Furthermore, it's not possible to set that bit until after the item has been fully loaded in, which doesn't happen until later with custom_createItem unlike fastCreateItem.
  nop
  nop
  nop
  nop
  nop
.close
; Withered trees
.open "files/rels/d_a_obj_ftree.rel" ; Withered Trees
.org 0x60E8 ; Relocation for line 0x25C
  .int create_item_for_withered_trees
.org 0x6190 ; Relocation for line 0x418
  .int custom_createItem
; Also change the code that reads the entity ID from subentity+4 to instead read from entity+3C.
; fastCreateItem returns a pointer to the item subentity, but when slow-loading an item, that sub entity doesn't even exist yet.
; But this is mostly fine, since all we need is to read the entity ID - and the exact same ID is at entity+3C.
.org 0x26C
  lwz r0,0x3C(r31)
.org 0x428
  lwz r0,0x3C(r3)
.close
; Item Ivan hid in a tree on Windfall
;.open "files/rels/d_a_tag_mk.rel" ; Item in Windfall tree
;.org 0x1828 ; Relocation for line 0x658
;  .int custom_createItem
;; Again, change the code that reads the entity ID to read from entity+3C instead of subentity+4.
;.org 0x6A4
;  lwz r0,0x3C(r30)
;.close




; In order to get rid of the cutscene where the player warps down to Hyrule 3, we set the HYRULE_3_WARP_CUTSCENE event bit on starting a new game.
; But then that results in the warp appearing even before the player should unlock it.
; So we replace a couple places that check that event bit to instead call a custom function that returns whether the warp should be unlocked or not.
.open "files/rels/d_a_warpdm20.rel" ; Hyrule warp object
; This is a rel, so overwrite the relocation addresses instead of the actual code.
.org 0x2530 ; Relocation for line 634
  .int check_hyrule_warp_unlocked
.org 0x2650 ; Relocation for line B50
  .int check_hyrule_warp_unlocked
.close




; The warp object down to Hyrule sets the event bit to change FF2 into FF3 once the event bit for seeing Tetra transform into Zelda is set.
; We want FF2 to stay permanently, so we skip over the line that sets this bit.
.open "files/rels/d_a_warpdm20.rel" ; Hyrule warp object
.org 0x68C
  b 0x694
.close




; Fix the Phantom Ganon from Ganon's Tower so he doesn't disappear from the maze when the player gets Light Arrows, but instead when they open the chest at the end of the maze which originally had Light Arrows.
; We replace where he calls dComIfGs_checkGetItem__FUc with a custom function that checks the appropriate treasure chest open flag.
; We only make this change for Phanton Ganon 2 (in the maze) not Phantom Ganon 3 (when you kill him with Light Arrows).
.open "files/rels/d_a_fganon.rel" ; Phantom Ganon
; This is a rel, so overwrite the relocation addresses instead of the actual code.
.org 0xDB54 ; Relocation for line 0x4D4C in standby__FP12fganon_class
  .int check_ganons_tower_chest_opened
.close
; Then there's an issue where killing Phantom Ganon 3 first and using his sword to destroy the door makes the sword dropped by Phantom Ganon 2 also disappear, which is bad because then the player wouldn't know which way to go in the maze.
.open "files/rels/d_a_boko.rel" ; Weapons lying on the ground
.org 0x6404 ; Relocation for line 0x2A90 in execute__8daBoko_cFv
  ; Instead of checking if the event flag for having destroyed the door with Phantom Ganon's sword is set, call a custom function.
  .int check_phantom_ganons_sword_should_disappear
.close




; Fix some Windfall townspeople not properly keeping track of whether they've given you their quest reward item yet or not.
; Pompie/Vera, Minenco, and Kamo give you treasure charts in the vanilla game, and they check if they've given you their item by calling checkGetItem.
; But that doesn't work for non-unique items, such as progressive items, rupees, etc.
; So we need to change their code to set and check event bits that were originally unused in the base game.
.open "files/rels/d_a_npc_people.rel" ; Various Windfall Island townspeople
; First we need to specify what event bit each townsperson should set.
; They store their item IDs as a word originally, so we can use the upper halfwords of those words to store the event bits.
; The other townspeople besides these 3 we just leave the upper halfword at 0000.
.org 0xC54C ; For Pompie and Vera
  .short 0x6904 ; Unused event bit
.org 0xC550 ; For Minenco
  .short 0x6908 ; Unused event bit
.org 0xC55C ; For Kamo
  .short 0x6910 ; Unused event bit
; Then change the function call to createItemForPresentDemo to call our own custom function instead.
; This custom function will both call createItemForPresentDemo and set one of the event bits specified above, by extracting the item ID and event bit separately from argument r4.
.org 0xFB34 ; Relocation for line 0x4BEC
  .int create_item_and_set_event_bit_for_townsperson
; We also need to change the calls to checkGetItem to instead call isEventBit.
.org 0xF17C ; Relocation for line 0x8D8
  .int dComIfGs_isEventBit__FUs
.org 0xF40C ; Relocation for line 0x14D0
  .int dComIfGs_isEventBit__FUs
.org 0xF5CC ; Relocation for line 0x1C38
  .int dComIfGs_isEventBit__FUs
.org 0xFFA4 ; Relocation for line 0x6174
  .int dComIfGs_isEventBit__FUs
.org 0x102BC ; Relocation for line 0x6C54
  .int dComIfGs_isEventBit__FUs
.org 0x102DC ; Relocation for line 0x6CC8
  .int dComIfGs_isEventBit__FUs
.org 0x106FC ; Relocation for line 0x88A8
  .int dComIfGs_isEventBit__FUs
.org 0x10744 ; Relocation for line 0x8A60
  .int dComIfGs_isEventBit__FUs
.org 0x10954 ; Relocation for line 0x91C4
  .int dComIfGs_isEventBit__FUs
; And finally, we change argument r3 passed to isEventBit to be the relevant event bit, as opposed to the item ID that it originally was for checkGetItem.
.org 0x08D4 ; For Pompie and Vera
  li r3, 0x6904
.org 0x14CC ; For Kamo
  li r3, 0x6910
.org 0x1C34 ; For Kamo
  li r3, 0x6910
.org 0x6170 ; For Minenco
  li r3, 0x6908
.org 0x6C50 ; For Kamo
  li r3, 0x6910
.org 0x6CC4 ; For Kamo
  li r3, 0x6910
.org 0x88A4 ; For Kamo
  li r3, 0x6910
.org 0x8A5C ; For Kamo
  li r3, 0x6910
.org 0x91C0 ; For Pompie and Vera
  li r3, 0x6904
.close
; Also, we need to change a couple checks Lenzo does, since he also checks if you got the item from Pompie and Vera.
.open "files/rels/d_a_npc_photo.rel" ; Lenzo
.org 0x717C ; Relocation for line 0x9C8
  .int dComIfGs_isEventBit__FUs
.org 0x7194 ; Relocation for line 0x9F8
  .int dComIfGs_isEventBit__FUs
.org 0x9C4 ; For Lenzo, checking Pompie and Vera's event bit
  li r3, 0x6904
.org 0x9F4 ; For Lenzo, checking Pompie and Vera's event bit
  li r3, 0x6904
.close

; Fix Lenzo thinking you've completed his research assistant quest if you own the Deluxe Picto Box.
.open "files/rels/d_a_npc_photo.rel" ; Lenzo
; First we need to change a function Lenzo calls when he gives you the item in the Deluxe Picto Box slot to call a custom function.
; This custom function will set an event bit to keep track of whether you've done this independantly of what the item itself is.
.org 0x7B04 ; Relocation for line 0x3BDC
  .int lenzo_set_deluxe_picto_box_event_bit
; Then we change the calls to checkGetItem to see if the player owns the Deluxe Picto Box to instead check the event bit we just set (6920).
; Change the calls to checkGetItem to instead call isEventBit.
.org 0x7AEC ; Relocation for line 0x3BB4
  .int dComIfGs_isEventBit__FUs
.org 0x7B14 ; Relocation for line 0x3C6C
  .int dComIfGs_isEventBit__FUs
.org 0x7D6C ; Relocation for line 0x4AFC
  .int dComIfGs_isEventBit__FUs
; And change argument r3 passed to isEventBit to be the event bit we set (6920), as opposed to the item ID that it originally was for checkGetItem.
.org 0x3BB0
  li r3, 0x6920
.org 0x3C68
  li r3, 0x6920
.org 0x4AF8
  li r3, 0x6920
.close




; Changes the way spoils and bait work from the vanilla game.
; Normally if you encountered spoils or bait as a field item without owning the Bait Bag/Spoils bag, it would turn itself into a single green rupee instead so you can't get the items without a bag to put them in.
; In the randomizer we allow these to drop even without having the bags so you can get these items early.
.open "sys/main.dol"
.org 0x800C7E58
  li r3, 1 ; Bait Bag
.org 0x800C7E84
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




; Rock Spire Shop Ship Beedle's code checks the item IDs using some unnecessary greater than or equal checks.
; This is a problem when the item IDs are randomized because which ones are greater than which other ones is not the same as vanilla.
; We remove a couple of lines here so that it only checks equality, not greater than or equal.
.open "files/rels/d_a_npc_bs1.rel" ; Beedle
.org 0x1ED8
  nop
.org 0x1EE4
  nop
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




; Zunari usually checks if he's given you the item in the Magic Armor item slot by calling checkGetItem.
; That doesn't work well when the item is randomized, so we have to replace the code with code to set and check a custom unused event bit.
.open "files/rels/d_a_npc_rsh1.rel" ; Zunari
.org 0x177C ; Where he checks if you have own the Magic Armor by calling checkItemGet.
  ; We replace this with a call to isEventBit checking our custom event bit.
  li r3, 0x6940
  nop
.org 0x71B4 ; Relocation for line 0x1784
  .int dComIfGs_isEventBit__FUs
.org 0x75F4 ; Relocation for line 0x32E8
  ; Change the call to createItemForPresentDemo to instead call our custom function so that it can set the custom event bit if necessary.
  .int zunari_give_item_and_set_magic_armor_event_bit
.close




; Salvage Corp usually check if they gave you their item by calling checkGetItem. That doesn't work well when it's randomized.
; We replace the code so that it sets and checks a custom unused event bit.
.open "files/rels/d_a_npc_sv.rel" ; Salvage Corp
.org 0x2C8
  li r3, 0x6980
.org 0x3DFC ; Relocation for line 0x2CC
  .int dComIfGs_isEventBit__FUs
.org 0x41CC ; Relocation for line 0x19A8
  ; Change the call to createItemForPresentDemo to instead call our custom function so that it can set the custom event bit if necessary.
  .int salvage_corp_give_item_and_set_event_bit
.close




; The death zone in between Forest Haven and Forbidden Woods disappears once you have Farore's Pearl.
; This makes it frustrating to make the trip to Forbidden Woods since you have to go all the way through Forest Haven every time you fail.
; So we change this void to always be there, even after you own Farore's Pearl.
.open "files/rels/d_a_tag_ret.rel" ; Void out death zone
.org 0x22C
  ; Change the branch here to be unconditional and always act like you do not have Farore's pearl.
  b 0x238
.close




; Maggie usually checks if she's given you her letter by calling isReserve. That doesn't work well when the item is randomized.
; So we change her to set and check a custom event bit (6A01).
.open "files/rels/d_a_npc_kp1.rel" ; Maggie
; Change how she checks if she's given you her first item yet.
.org 0x1214
  li r3, 0x6A01
.org 0x40A8 ; Relocation for line 0x1218
  .int dComIfGs_isEventBit__FUs
; Change the function call when she gives you her first item to a custom function that will set the custom event bit.
.org 0x4190 ; Relocation for line 0x17EC
  .int maggie_give_item_and_set_event_bit
; Also, normally if you finished her quest and get her second item, it locks you out from ever getting her first item.
; So we change it so she never acts like the quest is complete (she thinks you still have Moe's Letter in your inventory).
.org 0x11D8
  b 0x1210 ; Change conditional branch to unconditional
.close




; The Rito postman in the Windfall cafe usually checks if he's given you Moe's letter by calling isReserve. That doesn't work well when the item is randomized.
; So we change him to set and check a custom event bit (6A02).
.open "files/rels/d_a_npc_bm1.rel" ; Rito postman
; Change how he checks if he's given you his item yet when he's initializing.
.org 0x1020
  li r3, 0x6A02
.org 0xD06C ; Relocation for line 0x1024
  .int dComIfGs_isEventBit__FUs
; Change how he checks if he's given you his item yet when you talk to him.
.org 0x3178
  li r3, 0x6A02
.org 0xD5A4 ; Relocation for line 0x317C
  .int dComIfGs_isEventBit__FUs
; Change the function call when he starts the event that gives you his item to instead call a custom function that will set a custom event bit.
.org 0xD384 ; Relocation for line 0x225C
  .int rito_cafe_postman_start_event_and_set_event_bit
.close




; Change the conditions that cause letters to be sent to Link so that they work better in the randomizer.
.open "files/rels/d_a_obj_toripost.rel" ; Mailbox
.org 0x187C
  ; In vanilla, the mailbox will not give you any mail until you own Din's Pearl.
  ; Remove that condition so that only the letter-specific requirements matter.
  nop
.org 0x1B0C
  ; In vanilla, Orca's letter is sent when you watch a cutscene on Greatfish Isle.
  ; That cutscene is removed, so change it to be sent when you kill Kalle Demos.
  li r3, 4
.org 0x385C ; Relocation for line 0x1B10
  .int dComIfGs_isStageBossEnemy__Fi
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




; Swap out the item ID of progressive items for item get events as well as for field items so that their model and item get text change depending on what the next progressive tier of that item you should get is.
.open "sys/main.dol"
.org 0x80026A24 ; In createDemoItem (for item get events)
  ; Convert progressive item ID before storing in params
  bl convert_progressive_item_id_for_createDemoItem
.org 0x800F5550 ; In daItem_create
  ; Read params, convert progressive item ID, and store back
  bl convert_progressive_item_id_for_daItem_create
.org 0x8012E7B8 ; In dProcGetItem_init__9daPy_lk_cFv
  ; Read item ID property for this event action and convert progressive item ID
  bl convert_progressive_item_id_for_dProcGetItem_init_1
.org 0x8012E7DC ; In dProcGetItem_init__9daPy_lk_cFv
  bl convert_progressive_item_id_for_dProcGetItem_init_2
.close
.open "files/rels/d_a_shop_item.rel"
.org 0x9C0
  ; This is where the shop item would originally read its item ID from its params & 0x000000FF and store them to shop item entity+0x63A.
  ; We need to call a custom function to make the item look progressive, but because this is in a relocatable object file, we can't easily add a new function call to the main executable where there was no function call originally.
  ; So instead we first remove this original code.
  nop
  nop
.org 0x1698 ; Relocation for line 0x8B8
  ; Then we go up a bit to the start of the function, and replace the function call to _savegpr_28 with a call to our custom function, getting around the need to add a new relocation.
  .int convert_progressive_item_id_for_shop_item
.close




; Fix a big where buying a progressive item from the shop would not show the item get animation if it's the tier 2+ item.
.open "files/rels/d_a_npc_bs1.rel"
.org 0x783C ; Relocation for line 0x1D00
  ; For the Bait Bag slot.
  .int custom_getSelectItemNo_progressive
.org 0x792C ; Relocation for line 0x1F3C
  ; For the 3 Rock Spire Shop Ship slots.
  .int custom_getSelectItemNo_progressive
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




; Removes a couple lines of code that initialize the arc name pointers for the field models of Fire & Ice and Light arrow.
; These lines of code would overwrite any changes we made to those pointers and cause the game to crash.
.open "sys/main.dol"
.org 0x800C1EF8
  nop
  nop
.close




; Change Stalfos to be immune to Light Arrows.
; This is because if you cut the Stalfos in half and then kill the upper body with Light Arrows, the lower body will never die, which can softlock the player in the room.
.open "files/rels/d_a_st.rel"
.org 0x5AC0
  ; Make this branch unconditional so the code to die to Light Arrows is never run.
  b 0x5AFC
.close




; When the player enters Wind Temple, reset Makar's position to the starting room, or to near the warp pot the player exited.
; This is to prevent possible softlocks where Makar can teleport to later rooms in the dungeon for seemingly no reason.
.open "files/rels/d_a_npc_cb1.rel" ; Makar
.org 0xD740 ; Relocation for line 0x7D4
  .int reset_makar_position_to_start_of_dungeon
.org 0x7B4 ; This line originally stopped Makar from spawning if the partner ID number (803C4DC3) was not set to 1.
  ; Remove the line so that Makar spawns in, even after taking an inter-dungeon warp pot.
  nop
.close




; When the player enters Earth Temple, reset Medli's position to the starting room, or to near the warp pot the player exited.
; This is to prevent an issue where the player can't get past the first room without Medli unless they have Deku Leaf.
.open "files/rels/d_a_npc_md.rel" ; Medli
.org 0x19D34 ; Relocation for line 0xDB4
  .int reset_medli_position_to_start_of_dungeon
.org 0xD94 ; This line originally stopped Medli from spawning if the partner ID number (803C4DC3) was not set to 2.
  ; Remove the line so that Medli spawns in, even after taking an inter-dungeon warp pot.
  nop
.close




; If the player heals grandma but doesn't have an empty bottle for her to put soup in because they swapped their equipped item out too fast, grandma will crash the game because she tries to say a message that doesn't exist in the game's script.
; Change grandma to say the same message regardless of whether you have an empty bottle or not.
.open "files/rels/d_a_npc_ba1.rel" ; Grandma
.org 0x16DC
  ; This line originally hardcoded message ID 2041, which would be the message grandma says when you heal her without an empty bottle.
  ; Change it to 2037, which is the normal message ID when you do have an empty bottle.
  li r0, 2037
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




; Remove some dialogue the Killer Bees have hinting at where the Picto Box is after you've talked to Lenzo without it.
; Not only is this hint inaccurate in the randomizer, but this dialogue overrides the hide and seek event until you own Picto Box, which would result in a softlock if hide and seek was randomized to give Picto Box for example.
; To do this we simply override the four checks on event flag 1208 (for having talked to Lenzo without the Picto Box).
.open "files/rels/d_a_npc_mk.rel" ; Ivan
.org 0x2C2C ; In visitTalkInit__10daNpc_Mk_cFv
  b 0x2C7C
.org 0x2D0C ; In visitSetEvent__10daNpc_Mk_cFv
  b 0x2D48
.close
.open "files/rels/d_a_npc_uk.rel" ; The other Killer Bees besides Ivan
.org 0x29B4 ; In visitTalkInit__10daNpc_Uk_cFv
  b 0x2A38
.org 0x2AC8 ; In visitSetEvent__10daNpc_Uk_cFv
  b 0x2B04
.close




; Fix a crash when you look at the broken shards of Helmaroc King's mask with the hookshot.
.open "sys/main.dol"
.org 0x800F13A8 ; In daHookshot_rockLineCallback
  b hookshot_sight_failsafe_check
.close




; After you kill Puppet Ganon, he would normally respawn you in his room but override the layer to be layer 9 for the cutscene there.
; We set the switch for having already seen that cutscene in the new game initialization code, but then the rope you need to climb doesn't appear because the layer is wrong.
; We remove the layer override from Puppet Ganon's call to setNextStage.
.open "files/rels/d_a_bgn.rel" ; Puppet Ganon
.org 0xB1E0
  li r6, -1 ; No layer override
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




; Refill the player's magic meter to full when they load a save.
.open "sys/main.dol"
.org 0x80231B08 ; In FileSelectMainNormal__10dScnName_cFv right after calling card_to_memory__10dSv_info_cFPci
  b fully_refill_magic_meter_on_load_save
.close




; Allow turning while swinging on ropes.
.open "sys/main.dol" ; In procRopeSwing__9daPy_lk_cFv
.org 0x80145648
  b turn_while_swinging
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




; Fix the wrong item get music playing when you get certain items.
.open "sys/main.dol"
.org 0x8012E3E8 ; In setGetItemSound__9daPy_lk_cFUsi
  b check_play_special_item_get_music
.close




; Recode how the statues and brothers on Tingle Island check if you own the Tingle Statues.
; Originally they checked if you opened the dungeon chest that had the Tingle Statue in the vanilla game.
; But that wouldn't work correctly when Tingle Statues are randomized.
; The Tingle Statue item get functions are changed to set certain event bits, so we change the code here to check those same event bits.
.open "files/rels/d_a_obj_vtil.rel" ; Physical Tingle Statues on Tingle Island
.org 0x269C ; Relocation for line 0x820
  .int check_tingle_statue_owned
.close
.open "files/rels/d_a_npc_tc.rel" ; Tingle and brothers
.org 0x858C ; Relocation for line 0x2F8
  .int check_tingle_statue_owned
.org 0x8594 ; Relocation for line 0x308
  .int check_tingle_statue_owned
.org 0x859C ; Relocation for line 0x318
  .int check_tingle_statue_owned
.org 0x85A4 ; Relocation for line 0x328
  .int check_tingle_statue_owned
.org 0x85AC ; Relocation for line 0x338
  .int check_tingle_statue_owned
.org 0x88AC ; Relocation for line 0x1578
  .int check_tingle_statue_owned
.org 0x88B4 ; Relocation for line 0x158C
  .int check_tingle_statue_owned
.org 0x88BC ; Relocation for line 0x15A0
  .int check_tingle_statue_owned
.org 0x88C4 ; Relocation for line 0x15B4
  .int check_tingle_statue_owned
.org 0x88CC ; Relocation for line 0x15C8
  .int check_tingle_statue_owned
.org 0x8964 ; Relocation for line 0x193C
  .int check_tingle_statue_owned
.org 0x896C ; Relocation for line 0x1950
  .int check_tingle_statue_owned
.org 0x8974 ; Relocation for line 0x1964
  .int check_tingle_statue_owned
.org 0x897C ; Relocation for line 0x1978
  .int check_tingle_statue_owned
.org 0x8984 ; Relocation for line 0x198C
  .int check_tingle_statue_owned
.org 0x934C ; Relocation for line 0x58CC
  .int check_tingle_statue_owned
.org 0x935C ; Relocation for line 0x58FC
  .int check_tingle_statue_owned
.org 0x936C ; Relocation for line 0x592C
  .int check_tingle_statue_owned
.org 0x937C ; Relocation for line 0x595C
  .int check_tingle_statue_owned
.org 0x938C ; Relocation for line 0x598C
  .int check_tingle_statue_owned
.org 0x93B4 ; Relocation for line 0x5A54
  .int check_tingle_statue_owned
.org 0x93F4 ; Relocation for line 0x5C50
  .int check_tingle_statue_owned
.close




; Animate the 500 rupee to be a rainbow rupee that animates between the colors of all other rupees.
.open "sys/main.dol"
.org 0x800F93F4
  b check_animate_rainbow_rupee_color
.close




; Checks if the upcoming message text to parse has a custom text command.
.open "sys/main.dol"
.org 0x80033E74
  b check_run_new_text_commands
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




; Don't allow Beedle to buy Blue Chu Jelly, as selling that can make getting the Blue Potion from Doc Bandam impossible.
.open "files/rels/d_a_npc_bs1.rel" ; Beedle
.org 0x214C
  b 0x21DC ; Make Beedle not consider Blue Chu Jelly to be a spoil
.close




; Allow randomizing the first Green/Blue Potions Doc Bandam makes when you give him 15 jelly separately from the subsequent ones when you give him 5 jelly.
.open "files/rels/d_a_npc_ds1.rel"
.org 0x7B24 ; Relocation for line 0x2940, originally called fopAcM_createItemForPresentDemo__FP4cXyziUciiP5csXyzP4cXyz
  .int doc_bandam_check_new_potion_and_give_free_item
.org 0x1550 ; When Doc Bandam just made a new potion, this is where it checks if you have an empty bottle
  nop ; Remove the branch here that skips giving the item in this case so the player can't miss this item.
.close
