
; This patch modifies places in the game's code that don't work well when the item given by certain item locations is changed in order to allow these locations to be randomized.


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
.org 0x80026A90 ; In fopAcM_createItemForBoss
  nop
.org 0x80026AB0 ; In fopAcM_createItemForBoss
  nop
; Second we modify the code for the "disappear" cloud of smoke when the boss dies.
; This cloud of smoke is what spawns the item when Gohma, Kalle Demos, Helmaroc King, and Jalhalla die.
; So we need a way to pass the item ID from the boss's code to the disappear cloud's parameters and store them there.
; We do this by hijacking argument r7 when the boss calls createDisappear.
; Normally argument r7 is a byte, and gets stored to the disappear's params with mask 00FF0000.
; We change it to be a halfword and stored with the mask FFFF0000.
; The lower byte is unchanged from vanilla, it's still whatever argument r7 used to be for.
; But the upper byte, which used to be unused, now has the item ID in it.
.org 0x80027AC4 ; In fopAcM_createDisappear
  rlwimi r4, r7, 16, 0, 15
; Then we need to read the item ID parameter when the cloud is about to call createItemForBoss.
.org 0x800E7A1C ; In daDisappear_Execute
  lbz r4, 0x00B0(r7)
.close
; Third we change how the boss item ACTR calls createItemForBoss.
; (This is the ACTR that appears if the player skips getting the boss item after killing the boss, and instead comes back and does the whole dungeon again.)
; Normally it sets argument r4 to 1, but createItemForBoss doesn't even use argument r4.
; So we change it to load one of its params (mask: 0000FF00) and use that as argument r4.
; This param was unused and just 00 in the original game, but the randomizer will set it to the item ID it randomizes to that location.
; Then we will be calling createItemForBoss with the item ID to spawn in argument r4. Which due to the above change, will be used correctly now.
.open "files/rels/d_a_boss_item.rel"
.org 0x1C4 ; In daBossItem_Create
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
.org 0x1CE8
  ; Originally called SoldOutItem
  bl set_shop_item_in_bait_bag_slot_sold_out
.org 0x2DC4
  ; Originally called checkGetItem.
  bl check_shop_item_in_bait_bag_slot_sold_out
.org @NextFreeSpace
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
.close




; Three items are spawned by a call to fastCreateItem:
; * The item buried under black soil that you need the pig to dig up.
; * The item given by the withered trees.
; * The item hidden in a tree on Windfall. (Not modified here since its item is not randomized.)
; This is bad since fastCreateItem doesn't load the field item model in. If the model isn't already loaded the game will crash.
; So we add a new custom function to create an item and load the model, and replace the relevant calls so they call the new function.
; Buried item
.open "sys/main.dol"
.org 0x80056C0C ; In dig_main__13daTagKbItem_cFv
  ; Replace fastCreateItem call
  bl custom_createItem
  ; Then remove the code that sets bit 0x4000 of the bitfield at item_entity+0x1C4.
  ; This bit just seems to offset the item or something, but custom_createItem's item action does this anyway.
  ; Furthermore, it's not possible to set that bit until after the item actor has been created, which doesn't happen until later with custom_createItem unlike fastCreateItem.
  nop
  nop
  nop
  nop
  nop
.close
; Withered trees
.open "files/rels/d_a_obj_ftree.rel" ; Withered Trees
; In launch_heart_part (for creating the heart piece when the player waters the final tree)
.org 0x25C
  bl custom_createItem
.org 0x260
  ; Change the check on the return value from fastCreateItem being 0 (meaning no item actor was created) to instead check if the return value from custom_createItem is -1 (also meaning no item actor was created).
  mr r31, r3
  cmpwi r31, -1
  beq 0x2B8 ; (We overwrite a single line of code here which was a pointless branch that would never execute.)
  ; Then change the line of code that read the actor's unique ID from actor+4. Since the unique ID was already returned by custom_createItem directly, we don't need to read it, we can just move it from r31.
  mr r0, r31
  ; (After this, the withered tree will store the actor's unique ID to tree_actor+0x64C as normal.)
.org 0x2A4
  ; Then remove a line of code where it set the bitfield at the item actor+0x1C4 to 0x00004040.
  ; Since the actor doesn't exist yet we can't set this yet.
  ; Bit 0x4000 gets set by custom_createItem's item action, so that doesn't matter anyway.
  ; Bit 0x40 we will set on the frame that the item actor properly spawns as part of withered_tree_item_try_give_momentum.
  nop
; In place_heart_part (for recreating the heart piece if the player watered all the trees and then reloaded the stage)
.org 0x418
  ; Instead of simply calling custom_createItem, we have to call a wrapper function that both calls custom_createItem and sets our custom flag at withered_tree_entity+0x212 on in order to avoid our custom withered tree code setting the speeds to launch the item into the air.
  bl create_item_for_withered_trees_without_setting_speeds
.org @NextFreeSpace
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
.org 0x41C
  ; Again, like above we change the check on the return value to check -1 instead of 0.
  cmpwi r3, -1
  beq 0x45C
  nop ; (We overwrite a single line of code here which was a pointless branch that would never execute.)
  ; And again change the line of code that read the actor's unique ID to just move the register it's in.
  mr r0, r3
  ; (After this, the withered tree will store the actor's unique ID to tree_actor+0x64C as normal.)
; In search_heart_part (for detecting if the player has picked up the heart piece yet)
.org 0x184
  ; The way this function was originally coded already handled its job of detecting if the item was picked up appropriately, even in cases where the item is delayed spawned and doesn't exist for the first few frames. We don't need to modify anything to fix that.
  ; However, we do hijack this function in order to set some speed variables for the item on the frame it spawns, since custom_createItem wasn't able to do that like fastCreateItem was.
  bl withered_tree_item_try_give_momentum
.org @NextFreeSpace
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
.close




; Fix the Phantom Ganon from Ganon's Tower so he doesn't disappear from the maze when the player gets Light Arrows, but instead when they open the chest at the end of the maze which originally had Light Arrows.
; We replace where he calls dComIfGs_checkGetItem__FUc with a custom function that checks the appropriate treasure chest open flag.
; We only make this change for Phanton Ganon 2 (in the maze) not Phantom Ganon 3 (when you kill him with Light Arrows).
.open "files/rels/d_a_fganon.rel" ; Phantom Ganon
.org 0x4D4C ; In standby__FP12fganon_class
  bl check_ganons_tower_chest_opened
; Custom function that checks if the treasure chest in Ganon's Tower (that originally had the Light Arrows) has been opened.
; This is to make the Phantom Ganon that appears in the maze still work if you got Light Arrows beforehand.
.org @NextFreeSpace
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
.close
; Then there's an issue where killing Phantom Ganon 3 first and using his sword to destroy the door makes the sword dropped by Phantom Ganon 2 also disappear, which is bad because then the player wouldn't know which way to go in the maze.
.open "files/rels/d_a_boko.rel" ; Weapons lying on the ground
.org 0x2A90 ; In execute__8daBoko_cFv
  ; Instead of checking if the event flag for having destroyed the door with Phantom Ganon's sword is set, call a custom function.
  bl check_phantom_ganons_sword_should_disappear
; This function checks if Phantom Ganon's sword should disappear.
; Normally, both Phantom Ganon 2's and Phantom Ganon 3's swords will disappear once you've used Phantom Ganon 3's sword to destroy the door to Puppet Ganon.
; We change it so Phantom Ganon 2's sword remains so it can lead the player through the maze.
.org @NextFreeSpace
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
.org 0x4BEC
  bl create_item_and_set_event_bit_for_townsperson
; Custom function that creates an item given by a Windfall townsperson, and also sets an event bit to keep track of the item being given.
.org @NextFreeSpace
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
; We also need to change the calls to checkGetItem to instead call isEventBit.
.org 0x8D8
  bl dComIfGs_isEventBit__FUs
.org 0x14D0
  bl dComIfGs_isEventBit__FUs
.org 0x1C38
  bl dComIfGs_isEventBit__FUs
.org 0x6174
  bl dComIfGs_isEventBit__FUs
.org 0x6C54
  bl dComIfGs_isEventBit__FUs
.org 0x6CC8
  bl dComIfGs_isEventBit__FUs
.org 0x88A8
  bl dComIfGs_isEventBit__FUs
.org 0x8A60
  bl dComIfGs_isEventBit__FUs
.org 0x91C4
  bl dComIfGs_isEventBit__FUs
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
.org 0x9C8
  bl dComIfGs_isEventBit__FUs
.org 0x9F8
  bl dComIfGs_isEventBit__FUs
.org 0x9C4 ; For Lenzo, checking Pompie and Vera's event bit
  li r3, 0x6904
.org 0x9F4 ; For Lenzo, checking Pompie and Vera's event bit
  li r3, 0x6904
.close

; Fix Lenzo thinking you've completed his research assistant quest if you own the Deluxe Picto Box.
.open "files/rels/d_a_npc_photo.rel" ; Lenzo
; First we need to change a function Lenzo calls when he gives you the item in the Deluxe Picto Box slot to call a custom function.
; This custom function will set an event bit to keep track of whether you've done this independantly of what the item itself is.
.org 0x3BDC
  bl lenzo_set_deluxe_picto_box_event_bit
; Lenzo normally won't let you start his assistant quest if he detects you already have the Deluxe Picto Box, which is bad when that's randomized.
; So we need to set a custom event bit to keep track of whether you've gotten whatever item is in the Deluxe Picto Box slot.
.org @NextFreeSpace
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
; Then we change the calls to checkGetItem to see if the player owns the Deluxe Picto Box to instead check the event bit we just set (6920).
; Change the calls to checkGetItem to instead call isEventBit.
.org 0x3BB4
  bl dComIfGs_isEventBit__FUs
.org 0x3C6C
  bl dComIfGs_isEventBit__FUs
.org 0x4AFC
  bl dComIfGs_isEventBit__FUs
; And change argument r3 passed to isEventBit to be the event bit we set (6920), as opposed to the item ID that it originally was for checkGetItem.
.org 0x3BB0
  li r3, 0x6920
.org 0x3C68
  li r3, 0x6920
.org 0x4AF8
  li r3, 0x6920
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




; Zunari usually checks if he's given you the item in the Magic Armor item slot by calling checkGetItem.
; That doesn't work well when the item is randomized, so we have to replace the code with code to set and check a custom unused event bit.
.open "files/rels/d_a_npc_rsh1.rel" ; Zunari
.org 0x177C ; Where he checks if you have own the Magic Armor by calling checkItemGet.
  ; We replace this with a call to isEventBit checking our custom event bit.
  li r3, 0x6940
  nop
.org 0x1784
  bl dComIfGs_isEventBit__FUs
.org 0x32E8
  ; Change the call to createItemForPresentDemo to instead call our custom function so that it can set the custom event bit if necessary.
  bl zunari_give_item_and_set_magic_armor_event_bit
; Zunari usually checks if he gave you the Magic Armor by calling checkGetItem on the Magic Armor item ID. This doesn't work properly when the item he gives is randomized.
; So we need to set a custom event bit to keep track of whether you've gotten whatever item is in the Magic Armor slot.
.org @NextFreeSpace
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
.close




; Salvage Corp usually check if they gave you their item by calling checkGetItem. That doesn't work well when it's randomized.
; We replace the code so that it sets and checks a custom unused event bit.
.open "files/rels/d_a_npc_sv.rel" ; Salvage Corp
.org 0x2C8
  li r3, 0x6980
.org 0x2CC
  bl dComIfGs_isEventBit__FUs
.org 0x19A8
  ; Change the call to createItemForPresentDemo to instead call our custom function so that it can set the custom event bit if necessary.
  bl salvage_corp_give_item_and_set_event_bit
; Salvage Corp usually check if they gave you their item by calling checkGetItem. This doesn't work properly when the item is randomized.
; So we need to set a custom event bit to keep track of whether you've gotten whatever item they give you.
.org @NextFreeSpace
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
.close




; Maggie usually checks if she's given you her letter by calling isReserve. That doesn't work well when the item is randomized.
; So we change her to set and check a custom event bit (6A01).
.open "files/rels/d_a_npc_kp1.rel" ; Maggie
; Change how she checks if she's given you her first item yet.
.org 0x1214
  li r3, 0x6A01
.org 0x1218
  bl dComIfGs_isEventBit__FUs
; Change the function call when she gives you her first item to a custom function that will set the custom event bit.
.org 0x17EC
  bl maggie_give_item_and_set_event_bit
; Maggie usually checks if she's given you her letter by calling isReserve. That doesn't work well when the item is randomized.
; So we use this function to give her item and then set a custom event bit to keep track of it (6A01).
.org @NextFreeSpace
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
.org 0x1024
  bl dComIfGs_isEventBit__FUs
; Change how he checks if he's given you his item yet when you talk to him.
.org 0x3178
  li r3, 0x6A02
.org 0x317C
  bl dComIfGs_isEventBit__FUs
; Change the function call when he starts the event that gives you his item to instead call a custom function that will set a custom event bit.
.org 0x225C
  bl rito_cafe_postman_start_event_and_set_event_bit
; The Rito postman in the Windfall cafe usually checks if he's given you Moe's letter by calling isReserve. That doesn't work well when the item is randomized.
; So we use this function to start his item give event and then set a custom event bit to keep track of it (6A02).
.org @NextFreeSpace
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
.close




; Removes a couple lines of code that initialize the arc name pointers for the field models of Fire & Ice and Light arrow.
; These lines of code would overwrite any changes we made to those pointers and cause the game to crash.
; (Specifically, they modified 0x80386C7C and 0x80386C98, which are both in the list of field item resources.)
.open "sys/main.dol"
.org 0x800C1EF8
  nop
  nop
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




; Fix the wrong item get music playing when you get certain items.
.open "sys/main.dol"
.org 0x8012E3E8 ; In setGetItemSound__9daPy_lk_cFUsi
  b check_play_special_item_get_music
; Add a check right before playing the item get music to handle playing special item get music (pearls and songs).
; The vanilla game played the pearl music as part of the .stb cutscenes where you get the pearls, so the regular item get code had no reason to check for pearls originally.
; In the vanilla game Link only gets songs via 059get_dance actions, so that action would play the song get music, but the 011get_item action had no reason to check for songs.
.org @NextFreeSpace
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
.close




; Recode how the statues and brothers on Tingle Island check if you own the Tingle Statues.
; Originally they checked if you opened the dungeon chest that had the Tingle Statue in the vanilla game.
; But that wouldn't work correctly when Tingle Statues are randomized.
; The Tingle Statue item get functions are changed to set certain event bits, so we change the code here to check those same event bits.
.open "files/rels/d_a_obj_vtil.rel" ; Physical Tingle Statues on Tingle Island
.org 0x820
  bl check_tingle_statue_owned
.close
.open "files/rels/d_a_npc_tc.rel" ; Tingle and brothers
.org 0x2F8
  bl check_tingle_statue_owned
.org 0x308
  bl check_tingle_statue_owned
.org 0x318
  bl check_tingle_statue_owned
.org 0x328
  bl check_tingle_statue_owned
.org 0x338
  bl check_tingle_statue_owned
.org 0x1578
  bl check_tingle_statue_owned
.org 0x158C
  bl check_tingle_statue_owned
.org 0x15A0
  bl check_tingle_statue_owned
.org 0x15B4
  bl check_tingle_statue_owned
.org 0x15C8
  bl check_tingle_statue_owned
.org 0x193C
  bl check_tingle_statue_owned
.org 0x1950
  bl check_tingle_statue_owned
.org 0x1964
  bl check_tingle_statue_owned
.org 0x1978
  bl check_tingle_statue_owned
.org 0x198C
  bl check_tingle_statue_owned
.org 0x58CC
  bl check_tingle_statue_owned
.org 0x58FC
  bl check_tingle_statue_owned
.org 0x592C
  bl check_tingle_statue_owned
.org 0x595C
  bl check_tingle_statue_owned
.org 0x598C
  bl check_tingle_statue_owned
.org 0x5A54
  bl check_tingle_statue_owned
.org 0x5C50
  bl check_tingle_statue_owned
.close
; Also fix Tingle Tuner related things to check if you own the Tingle Statues correctly.
.open "sys/main.dol"
; Handles telling the GBA which Tingle Statues you own.
.org 0x800D14D8 ; In daAgb_c::FlagsSend(unsigned long)
  bl check_tingle_statue_owned
.org 0x800D1504 ; In daAgb_c::FlagsSend(unsigned long)
  bl check_tingle_statue_owned
.org 0x800D1528 ; In daAgb_c::FlagsSend(unsigned long)
  bl check_tingle_statue_owned
.org 0x800D154C ; In daAgb_c::FlagsSend(unsigned long)
  bl check_tingle_statue_owned
.org 0x800D1570 ; In daAgb_c::FlagsSend(unsigned long)
  bl check_tingle_statue_owned
.close
.open "files/rels/d_a_agbsw0.rel" ; Tingle Tuner region
; Handles checking various spawn conditions for Tingle Tuner hint regions to appear after a specific Tingle Statue is owned.
; (I think these conditions are probably unused in the vanilla game, but update them anyway in case they're used for mods.)
.org 0x359C ; In daAgbsw0_c::MoveCheck(short), condition 9
  bl check_tingle_statue_owned
.org 0x35B8 ; In daAgbsw0_c::MoveCheck(short), condition A
  bl check_tingle_statue_owned
.org 0x35D4 ; In daAgbsw0_c::MoveCheck(short), condition B
  bl check_tingle_statue_owned
.org 0x35F0 ; In daAgbsw0_c::MoveCheck(short), condition C
  bl check_tingle_statue_owned
.org 0x360C ; In daAgbsw0_c::MoveCheck(short), condition D
  bl check_tingle_statue_owned
.close




; Allow randomizing the first Green/Blue Potions Doc Bandam makes when you give him 15 jelly separately from the subsequent ones when you give him 5 jelly.
.open "files/rels/d_a_npc_ds1.rel"
.org 0x2940
  ; Originally called fopAcM_createItemForPresentDemo__FP4cXyziUciiP5csXyzP4cXyz
  bl doc_bandam_check_new_potion_and_give_free_item

.org @NextFreeSpace
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

.org 0x1550 ; When Doc Bandam just made a new potion, this is where it checks if you have an empty bottle
  nop ; Remove the branch here that skips giving the item in this case so the player can't miss this item.
.close




; Make the Big Octo Great Fairy always give an item hint.
; In vanilla she hinted about Fire & Ice Arrows, so she didn't give the hint if your current bow was anything but Hero's Bow.
.open "files/rels/d_a_bigelf.rel" ; Great Fairy
.org 0x22A4 ; In getMsg__10daBigelf_cFv
  ; Remove the conditional branch for if your current bow is not the Hero's Bow and just always show the hint.
  nop
.close




; Prevent Mighty Darknuts from respawning after you've beaten them once and the chest added by the randomizer appears.
.open "files/rels/d_a_obj_firewall.rel" ; Fire wall that handles spawning the Mighty Darknuts
.org 0x1240
  ; Normally this code would check event bit 3520 (MIGHTY_DARKNUTS_SPAWNED) to decide if it should play the long version of the intro event or the short one after you've seen the long one once.
  ; We change it to check switch 5 (set when the Mighty Darknuts die) to decide if it should play the short version of the intro event, or if it shouldn't play any event at all once you've defeated the Darknuts.
  li r4, 5
  li r5, 0
.org 0x1248
  bl isSwitch__10dSv_info_cFii
.org 0x1250
  beq 0x12C4 ; If the Darknuts are defeated, destroy this firewall object so it doesn't play any intro event.
  ; Otherwise continue on with the normal code to initialize the short intro event.
.close
