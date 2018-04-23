
import os
from io import BytesIO
import re

from fs_helpers import *

def modify_new_game_start_code(self):
  original_free_space_ram_address = 0x803FCFA8
  
  dol_data = self.get_raw_file("sys/main.dol")
  
  patch_path = os.path.join(".", "asm", "init_save_with_tweaks.bin")
  with open(patch_path, "rb") as f:
    patch_data = f.read()
  
  # First write our custom code to the end of the dol file.
  original_dol_size = 0x3A52C0
  patch_length = len(patch_data)
  write_bytes(dol_data, original_dol_size, patch_data)
  
  # Next add a new text section to the dol (Text2).
  write_u32(dol_data, 0x08, original_dol_size) # Write file offset of new Text2 section (which will be the original end of the file, where we put the patch)
  write_u32(dol_data, 0x50, original_free_space_ram_address) # Write loading address of the new Text2 section
  write_u32(dol_data, 0x98, patch_length) # Write length of the new Text2 section
  
  # Next we need to change a hardcoded pointer to where free space begins. Otherwise the game will overwrite the custom code.
  padded_patch_length = ((patch_length + 3) & ~3) # Pad length of patch to next 4 just in case
  new_start_pointer_for_default_thread = original_free_space_ram_address + padded_patch_length # New free space pointer after our custom code
  high_halfword = (new_start_pointer_for_default_thread & 0xFFFF0000) >> 16
  low_halfword = new_start_pointer_for_default_thread & 0xFFFF
  if low_halfword >= 0x8000:
    # If the low halfword has the highest bit set, it will be considered a negative number.
    # Therefore we need to add 1 to the high halfword (equivalent to adding 0x10000) to compensate for the low halfword being negated.
    high_halfword = high_halfword+1
  # Now update the asm instructions that load this hardcoded pointer.
  write_u32(dol_data, 0x304894, 0x3C600000 | high_halfword)
  write_u32(dol_data, 0x30489C, 0x38030000 | low_halfword)
  # Note: There's another hardcoded pointer near here, which points to 0x10000 later in RAM (0x8040CFA8).
  # Does this need to be updated as well? Seems to work fine without updating it.
  
  
  # 8005D618 is where the game calls the new game save init function.
  # We replace this call with a call to our custom save init function.
  address_of_save_init_call_to_replace = 0x8005D618
  offset_of_call = original_free_space_ram_address - address_of_save_init_call_to_replace
  offset_of_call &= 0x03FFFFFC
  write_u32(dol_data, 0x5A558, 0x48000001 | offset_of_call) # 5A558 in the dol file is equivalent to 8005D618 in RAM
  
  # nop out a couple lines so the long intro movie is skipped.
  write_u32(dol_data, 0x22FBB8, 0x60000000) # 0x80232C78 in RAM
  write_u32(dol_data, 0x22FBC8, 0x60000000) # 0x80232C88 in RAM

def remove_story_railroading(self):
  # Modify King of Red Lions's code so he doesn't stop you when you veer off the path he wants you to go on.
  
  ship_data = self.get_raw_file("files/rels/d_a_ship.rel")
  
  # We need to change some of the conditions in his checkOutRange function so he still prevents you from leaving the bounds of the map, but doesn't railroad you based on your story progress.
  # First is the check for before you've reached Dragon Roost Island. Make this branch unconditional so it considers you to have seen Dragon Roost's intro whether you have or not.
  write_u32(ship_data, 0x29EC, 0x48000064) # b 0x2A50
  # Second is the check for whether you've gotten Farore's Pearl. Make this branch unconditional too.
  write_u32(ship_data, 0x2A08, 0x48000048) # b 0x2A50
  # Third is the check for whether you have the Master Sword. Again make the branch unconditional.
  write_u32(ship_data, 0x2A24, 0x48000010) # b 0x2A34
  
  # Skip the check for if you've seen the Dragon Roost Island intro which prevents you from getting in the King of Red Lions.
  # Make this branch unconditional as well.
  write_u32(ship_data, 0xB2D8, 0x48000018) # b 0xB2F0

def skip_wakeup_intro_and_start_at_dock(self):
  # When the player starts a new game they usually start at spawn ID 206, which plays the wakeup event and puts the player on Aryll's lookout.
  # We change the starting spawn ID to 0, which does not play the wakeup event and puts the player on the dock next to the ship.
  dol_data = self.get_raw_file("sys/main.dol")
  spawn_id = 0
  write_u8(dol_data, 0x055AEF, spawn_id)

def start_ship_at_outset(self):
  # Change the King of Red Lion's default position so that he appears on Outset at the start of the game.
  dzx = self.get_arc("files/res/Stage/sea/Stage.arc").dzx_files[0]
  sea_actors = dzx.entries_by_type("ACTR")
  ship_actor = next(x for x in sea_actors if x.name == "Ship")
  ship_actor.x_pos = -202000.0
  ship_actor.y_pos = 0.0
  ship_actor.z_pos = 312200.0
  ship_actor.x_rot = 0
  ship_actor.y_rot = 0x7555
  ship_actor.save_changes()
  
def make_all_text_instant(self):
  bmg = self.get_arc("files/res/Msg/bmgres.arc").bmg_files[0]
  for msg in bmg.messages:
    msg.initial_draw_type = 1 # Instant draw
    msg.save_changes()

def make_fairy_upgrades_unconditional(self):
  # Makes the items given by Great Fairies always the same so they can be randomized, as opposed to changing depending on what wall/bomb bag/quiver upgrades you already have.
  
  great_fairy_rel_data = self.get_raw_file("files/rels/d_a_bigelf.rel")
  
  patch_path = os.path.join(".", "asm", "unconditional_fairy_upgrades.bin")
  with open(patch_path, "rb") as f:
    patch_data = f.read()
  
  write_bytes(great_fairy_rel_data, 0x217C, patch_data)

def make_fishmen_active_before_gohma(self):
  # Fishmen usually won't appear until Gohma is dead. This removes that check from their code so they appear from the start.
  
  fishman_rel_data = self.get_raw_file("files/rels/d_a_npc_so.rel")
  
  write_u32(fishman_rel_data, 0x3FD8, 0x4800000C) # Change conditional branch to unconditional branch.

def fix_zephos_double_item(self):
  # The event where the player gets the Wind's Requiem actually gives that song to the player twice.
  # The first one is hardcoded into Zephos's AI and only gives the song.
  # The second is part of the event, and also handles the text, model, animation, etc, of getting the song.
  # Getting the same item twice is a problem for some items, such as rupees. So we remove the first one.
  
  zephos_rel_data = self.get_raw_file("files/rels/d_a_npc_hr.rel")
  
  write_u32(zephos_rel_data, 0x1164, 0x48000008) # Branch to skip over the line of code where Zephos gives the Wind's Requiem.

def fix_deku_leaf_model(self):
  # The Deku Leaf is a unique object not used for other items. It's easy to change what item it gives you, but the visual model cannot be changed.
  # So instead we replace the unique Deku Leaf actor ("itemDek") with a more general actor that can be for any field item ("item").
  
  dzx = self.get_arc("files/res/Stage/Omori/Room0.arc").dzx_files[0]
  deku_leaf_actors = [actor for actor in dzx.entries_by_type("ACTR") if actor.name == "itemDek"]
  for actor in deku_leaf_actors:
    actor.name = "item"
    actor.params = 0x01FF0000 # Unknown params. TODO?
    actor.item_id = 0x34 # Deku Leaf
    actor.item_flag = 2 # This is the same item pickup flag that itemDek originally had in its params.
    actor.set_flag = 0xFF # Unknown what this is, but might need to be FF for the player to pick up the item sometimes?
    actor.save_changes()

def allow_all_items_to_be_field_items(self):
  # Most items cannot be field items (items that appear freely floating on the ground) because they don't have a field model defined.
  # Here we copy the regular item get model to the field model so that any item can be a field item.
  # We also change the code run when you touch the item so that these items play out the full item get animation with text, instead of merely popping up above the player's head like a rupee.
  # And we change the Y offsets so the items don't appear lodged inside the floor, and can be picked up easily.
  
  item_resources_list_start = 0x3812B0 # 803842B0 in RAM
  field_item_resources_list_start = 0x3836B0 # 803866B0 in RAM
  itemGetExecute_switch_statement_entries_list_start = 0x389A6C # 8038CA6C in RAM
  
  dol_data = self.get_raw_file("sys/main.dol")
  
  arc_name_pointers = {}
  with open("./data/item_resource_arc_name_pointers.txt", "r") as f:
    matches = re.findall(r"^([0-9a-f]{2}) ([0-9a-f]{8}) ", f.read(), re.IGNORECASE | re.MULTILINE)
  for item_id, arc_name_pointer in matches:
    item_id = int(item_id, 16)
    arc_name_pointer = int(arc_name_pointer, 16)
    arc_name_pointers[item_id] = arc_name_pointer
  
  for item_id in self.item_ids_without_a_field_model:
    if item_id in [0x39, 0x3A, 0x3E]:
      # Master Swords don't have a proper item get model defined, so we need to use the Hero's Sword instead.
      item_id_to_copy_from = 0x38
      # We also change the item get model too, not just the field model.
      item_resources_offset_to_fix = item_resources_list_start + item_id*0x24
    elif item_id in [0x6D, 0x6E, 0x6F, 0x70, 0x71, 0x72]:
      # Songs use the Pirate's Charm model by default, so we change it to use the Wind Waker model instead.
      item_id_to_copy_from = 0x22
      # We also change the item get model too, not just the field model.
      item_resources_offset_to_fix = item_resources_list_start + item_id*0x24
    elif item_id == 0xB2:
      # The Magic Meter Upgrade has no model, so we have to copy the Large Magic Jar model.
      # TODO: This could look confusing as a field item, the player might think that it's literally just a Large Magic Jar.
      item_id_to_copy_from = 0x0A
      # We also change the item get model too, not just the field model.
      item_resources_offset_to_fix = item_resources_list_start + item_id*0x24
    else:
      item_id_to_copy_from = item_id
      item_resources_offset_to_fix = None
    
    item_resources_offset_to_copy_from = item_resources_list_start + item_id_to_copy_from*0x24
    field_item_resources_offset = field_item_resources_list_start + item_id*0x1C
    
    arc_name_pointer = arc_name_pointers[item_id_to_copy_from]
    
    write_u32(dol_data, field_item_resources_offset, arc_name_pointer)
    if item_resources_offset_to_fix:
      write_u32(dol_data, item_resources_offset_to_fix, arc_name_pointer)
    
    data1 = read_bytes(dol_data, item_resources_offset_to_copy_from+8, 0xD)
    data2 = read_bytes(dol_data, item_resources_offset_to_copy_from+0x1C, 4)
    write_bytes(dol_data, field_item_resources_offset+4, data1)
    write_bytes(dol_data, field_item_resources_offset+0x14, data2)
    if item_resources_offset_to_fix:
      write_bytes(dol_data, item_resources_offset_to_fix+8, data1)
      write_bytes(dol_data, item_resources_offset_to_fix+0x1C, data2)
  
  # Also nop out the 6 lines of code that initialize the arc filename pointer for the 6 songs.
  # These lines would overwrite the change we made from the Pirate's Charm model to the Wind Waker model for songs.
  for offset in [0xBE8B0, 0xBE8B8, 0xBE8C0, 0xBE8C8, 0xBE8D0, 0xBE8D8]: # First is at 800C1970 in RAM
    write_u32(dol_data, offset, 0x60000000) # nop
  
  
  # Fix which code runs when the player touches the field item to pick the item up.
  for item_id in range(0, 0x83+1):
    # Update the switch statement cases in function itemGetExecute for items that originally used the default case (0x800F6C8C).
    # This default case wouldn't give the player the item. It would just appear above the player's head for a moment like a Rupee and not be added to the player's inventory.
    # We switch it to case 0x800F675C, which will use the proper item get event with all the animations, text, etc.
    location_of_items_switch_statement_case = itemGetExecute_switch_statement_entries_list_start + item_id*4
    original_switch_case = read_u32(dol_data, location_of_items_switch_statement_case)
    if original_switch_case == 0x800F6C8C:
      write_u32(dol_data, location_of_items_switch_statement_case, 0x800F675C)
  
  # Also change the switch case in itemGetExecute used by items with IDs 0x84+ to go to 800F675C as well.
  write_u32(dol_data, 0xF33A8, 0x418102F4) # 800F6468 in RAM
  
  
  # Update the visual Y offsets so the item doesn't look like it's halfway inside the floor and difficult to see.
  # First update the default case of the switch statement in the function getYOffset so that it reads from 803F9E84 (value: 23.0), instead of 803F9E80 (value: 0.0).
  write_u32(dol_data, 0xF1C10, 0xC022A184) # lfs f1, -0x5E7C(rtoc) (at 800F4CD0 in RAM)
  # And fix then Big Key so it uses the default case with the 23.0 offset, instead of using the 0.0 offset. (Other items already use the default case, so we don't need to fix any besides Big Key.)
  write_u32(dol_data, 0x3898B8 + 0x4E*4, 0x800F4CD0)
  
  
  # We also change the Y offset of the hitbox for any items that have 0 for the Y offset.
  # Without this change the item would be very difficult to pick up, the only way would be to stand on top of it and do a spin attack.
  extra_item_data_list_start = 0x3852B0 # 803882B0 in RAM
  for item_id in range(0, 0xFF+1):
    item_extra_data_entry_offset = extra_item_data_list_start+4*item_id
    original_y_offset = read_u8(dol_data, item_extra_data_entry_offset+1)
    if original_y_offset == 0:
      write_u8(dol_data, item_extra_data_entry_offset+1, 0x28) # Y offset of 0x28

def allow_changing_boss_drop_items(self):
  # The 6 Heart Containers that appear after you kill a boss are all created by the function createItemForBoss.
  # createItemForBoss hardcodes the item ID 8, and doesn't care which boss was just killed. This makes it hard to randomize boss drops without changing all 6 in sync.
  # So we make some changes to createItemForBoss and the places that call it so that each boss can give a different item.
  
  # First we modify the createItemForBoss function itself to not hardcode the item ID as 8 (Heart Container).
  # We nop out the two instructions that load 8 into r4. This way it simply passes whatever it got as argument r4 into the next function call to createItem.
  dol_data = self.get_raw_file("sys/main.dol")
  write_u32(dol_data, 0x239D0, 0x60000000) # nop (at 80026A90 in RAM)
  write_u32(dol_data, 0x239F0, 0x60000000) # nop (at 80026AB0 in RAM)
  
  # Second we modify the code for the "disappear" cloud of smoke when the boss dies.
  # This cloud of smoke is what spawns the item when Gohma, Kalle Demos, Helmaroc King, and Jalhalla die.
  # So we need a way to pass the item ID from the boss's code to the disappear cloud's parameters and store them there.
  # We do this by hijacking argument r7 when the boss calls createDisappear.
  # Normally argument r7 is a byte, and gets stored to the disappear's params with mask 00FF0000.
  # We change it to be a halfword and stored with the mask FFFF0000.
  # The lower byte is unchanged from vanilla, it's still whatever argument r7 used to be for.
  # But the upper byte, which used to be unused, now has the item ID in it.
  write_u32(dol_data, 0x24A04, 0x50E4801E) # rlwimi r4, r7, 16, 0, 15 (at 80027AC4 in RAM)
  # Then we need to read the item ID parameter when the cloud is about to call createItemForBoss.
  write_u32(dol_data, 0xE495C, 0x888700B0) # lbz r4, 0x00B0(r7) (at 800E7A1C in RAM)
  
  # Third we change how the boss item ACTR calls createItemForBoss.
  # (This is the ACTR that appears if the player skips getting the boss item after killing the boss, and instead comes back and does the whole dungeon again.)
  # Normally it sets argument r4 to 1, but createItemForBoss doesn't even use argument r4.
  # So we change it to load one of its params (mask: 0000FF00) and use that as argument r4.
  # This param was unused and just 00 in the original game, but the randomizer will set it to the item ID it randomizes to that location.
  # Then we will be calling createItemForBoss with the item ID to spawn in argument r4. Which due to the above change, will be used correctly now.
  bossitem_rel_data = self.get_raw_file("files/rels/d_a_boss_item.rel")
  write_u32(bossitem_rel_data, 0x1C4, 0x889E00B2) # lbz r4, 0x00B2(r30)
  
  # The third change necessary is for all 6 boss's code to be modified so that they pass the item ID to spawn to a function call.
  # For Gohdan and Molgera, the call is to createItemForBoss directly, so argument r4 needs to be the item ID.
  # For Gohma, Kalle Demos, Helmaroc King, and Jalhalla, they instead call createDisappear, so we need to upper byte of argument r7 to have the item ID.
  # But the randomizer itself handles all 6 of these changes when randomizing, since these locations are all listed in the "Paths" of each item location. So no need to do anything here.

def skip_post_boss_warp_cutscenes(self):
  # This makes the warps out of boss rooms always skip the cutscene usually shown the first time you beat the boss and warp out.
  
  # Function C3C of d_a_warpf.rel is checking if the post-boss cutscene for this dungeon has been viewed yet or not.
  # Change it to simply always return true, that it has been viewed.
  warpf_rel_data = self.get_raw_file("files/rels/d_a_warpf.rel")
  write_u32(warpf_rel_data, 0xC3C, 0x38600001) # li r3, 1
  write_u32(warpf_rel_data, 0xC40, 0x4E800020) # blr

def remove_shop_item_forced_uniqueness_bit(self):
  # Some shop items have a bit set that disallows you from buying the item if you already own one of that item.
  # This can be undesirable depending on what we randomize the items to be, so we unset this bit.
  # Also, Beedle doesn't have a message to say when this you try to buy an item with this bit you already own. So the game would just crash if the player tried to buy these items while already owning them.
  
  shop_item_data_list_start = 0x372E1C
  dol_data = self.get_raw_file("sys/main.dol")
  
  for shop_item_index in [0, 0xB, 0xC, 0xD]: # Bait Bag, Empty Bottle, Piece of Heart, and Treasure Chart 4 in Beedle's shops
    shop_item_data_offset = shop_item_data_list_start + shop_item_index*0x10
    buy_requirements_bitfield = read_u8(dol_data, shop_item_data_offset+0xC)
    buy_requirements_bitfield = (buy_requirements_bitfield & (~2)) # Bit 02 specifies that the player must not already own this item
    write_u8(dol_data, shop_item_data_offset+0xC, buy_requirements_bitfield)

def allow_randomizing_magic_meter_upgrade_item(self):
  # The Great Fairy inside the Big Octo is hardcoded to double your max magic meter (and fill up your current magic meter too).
  # Since we randomize what item she gives you, we need to remove this code so that she doesn't always give you the increased magic meter.
  
  great_fairy_rel_data = self.get_raw_file("files/rels/d_a_bigelf.rel")
  
  write_u32(great_fairy_rel_data, 0x7C0, 0x60000000) # nop, for max MP
  write_u32(great_fairy_rel_data, 0x7CC, 0x60000000) # nop, for current MP

def start_with_sea_chart_fully_revealed(self):
  # Changes the function that initializes the sea chart when starting a new game so that the whole chart has been drawn out.
  
  dol_data = self.get_raw_file("sys/main.dol")
  
  write_u32(dol_data, 0x5820C, 0x38800001) # li r4, 1 (at 8005B2CC in RAM)

def fix_triforce_charts_not_needing_to_be_deciphered(self):
  # When salvage points decide if they should show their ray of light, they originally only checked if you
  # have the appropriate Triforce Chart deciphered if the item there is actually a Triforce Shard.
  # We don't want the ray of light to show until the chart is deciphered, so we change the salvage point code
  # to check the chart index instead of the item ID when determining if it's a Triforce or not.
  
  salvage_data = self.get_raw_file("files/rels/d_a_salvage.rel")
  # We replace the call to getItemNo, so it instead just adds 0x61 to the chart index.
  # 0x61 to 0x68 are the Triforce Shard IDs, and 0 to 8 are the Triforce Chart indexes,
  # so by adding 0x61 we simulate whether the item would be a Triforce Shard or not based on the chart index.
  write_u32(salvage_data, 0x10C0, 0x38730061) # addi r3, r19, 0x61
  # Then we branch to skip the line of code that originally called getItemNo.
  # We can't easily nop the line out, since the REL's relocation would overwrite our nop.
  write_u32(salvage_data, 0x10C4, 0x48000008) # b 0x10CC

def remove_forsaken_fortress_2_cutscenes(self):
  # Removes the rescuing-Aryll cutscene played by the spawn when you enter the Forsaken Fortress tower.
  dzx = self.get_arc("files/res/Stage/M2tower/Room0.arc").dzx_files[0]
  spawn = next(spawn for spawn in dzx.entries_by_type("PLYR") if spawn.spawn_id == 16)
  spawn.event_index = 0xFF
  spawn.save_changes()
  
  # Removes the Ganon cutscene by making the door to his room lead back to the start of Forsaken Fortress instead.
  exit = next((exit for exit in dzx.entries_by_type("SCLS") if exit.dest_stage_name == "M2ganon"), None)
  if exit:
    exit.dest_stage_name = "sea"
    exit.room_index = 1
    exit.spawn_id = 0
    exit.save_changes()

def remove_medli_that_gives_fathers_letter(self):
  # The first instance of Medli, who gives the letter for Komali, can disappear under certain circumstances.
  # For example, owning the half-power Master Sword makes her disappear. Deliving the letter to Komali also makes her disappear.
  # So in order to avoid the item she gives being missable, we just remove it entirely.
  # To do this we modify the chkLetterPassed function to always return true, so she thinks you've delivered the letter.
  
  dol_data = self.get_raw_file("sys/main.dol")
  write_u32(dol_data, 0x218EC0, 0x38600001) # li r3, 1 (at 8021BF80 in RAM)
