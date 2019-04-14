
import re
import yaml
import os
from io import BytesIO
from collections import namedtuple
from collections import OrderedDict
import copy
from random import Random

from fs_helpers import *
from wwlib import texture_utils
from wwlib.rarc import RARC
from paths import ASSETS_PATH, ASM_PATH, SEEDGEN_PATH
import customizer

ORIGINAL_FREE_SPACE_RAM_ADDRESS = 0x803FCFA8
ORIGINAL_DOL_SIZE = 0x3A52C0

# These are from main.dol. Hardcoded since it's easier than reading them from the dol.
DOL_SECTION_OFFSETS = [
  # Text sections
  0x0100,
  0x2620,
  ORIGINAL_DOL_SIZE, # Custom .text2 section
  
  # Data sections
  0x3355C0,
  0x335620,
  0x335680,
  0x335820,
  0x335840,
  0x36E580,
  0x39F960,
  0x3A00A0,
]
DOL_SECTION_ADDRESSES = [
  # Text sections
  0x80003100,
  0x800056E0,
  ORIGINAL_FREE_SPACE_RAM_ADDRESS, # Custom .text2 section
  
  # Data sections
  0x80005620,
  0x80005680,
  0x80338680,
  0x80338820,
  0x80338840,
  0x80371580,
  0x803F60E0,
  0x803F7D00,
]
DOL_SECTION_SIZES = [
  # Text sections
  0x002520,
  0x332FA0,
  -1, # Custom .text2 section. Placeholder since we don't know the size until the patch has been applied.
  
  # Data sections
  0x00060,
  0x00060,
  0x001A0,
  0x00020,
  0x38D40,
  0x313E0,
  0x00740,
  0x05220,
]

MAXIMUM_ADDITIONAL_STARTING_ITEMS = 47

def address_to_offset(address):
  # Takes an address in one of the sections of main.dol and converts it to an offset within main.dol.
  for section_index in range(len(DOL_SECTION_OFFSETS)):
    section_offset = DOL_SECTION_OFFSETS[section_index]
    section_address = DOL_SECTION_ADDRESSES[section_index]
    section_size = DOL_SECTION_SIZES[section_index]
    
    if section_address <= address < section_address+section_size:
      offset = address - section_address + section_offset
      return offset
  
  raise Exception("Unknown address: %08X" % address)

def split_pointer_into_high_and_low_half_for_hardcoding(pointer):
  high_halfword = (pointer & 0xFFFF0000) >> 16
  low_halfword = pointer & 0xFFFF
  
  if low_halfword >= 0x8000:
    # If the low halfword has the highest bit set, it will be considered a negative number.
    # Therefore we need to add 1 to the high halfword (equivalent to adding 0x10000) to compensate for the low halfword being negated.
    high_halfword = high_halfword+1
  
  return high_halfword, low_halfword

def apply_patch(self, patch_name):
  with open(os.path.join(ASM_PATH, patch_name + "_diff.txt")) as f:
    diffs = yaml.safe_load(f)
  
  for file_path, diffs_for_file in diffs.items():
    data = self.get_raw_file(file_path)
    for org_address, new_bytes in diffs_for_file.items():
      if file_path == "sys/main.dol":
        if org_address == ORIGINAL_FREE_SPACE_RAM_ADDRESS:
          add_custom_functions_to_free_space(self, new_bytes)
          continue
        else:
          offset = address_to_offset(org_address)
      else:
        offset = org_address
      
      write_and_pack_bytes(data, offset, new_bytes, "B"*len(new_bytes))

def add_custom_functions_to_free_space(self, new_bytes):
  dol_data = self.get_raw_file("sys/main.dol")
  
  # First write our custom code to the end of the dol file.
  patch_length = len(new_bytes)
  write_and_pack_bytes(dol_data, ORIGINAL_DOL_SIZE, new_bytes, "B"*len(new_bytes))
  
  # Next add a new text section to the dol (Text2).
  write_u32(dol_data, 0x08, ORIGINAL_DOL_SIZE) # Write file offset of new Text2 section (which will be the original end of the file, where we put the patch)
  write_u32(dol_data, 0x50, ORIGINAL_FREE_SPACE_RAM_ADDRESS) # Write loading address of the new Text2 section
  write_u32(dol_data, 0x98, patch_length) # Write length of the new Text2 section
  
  # Update the constant for how large the .text2 section is so that addresses in this section can be converted properly by address_to_offset.
  global DOL_SECTION_SIZES
  DOL_SECTION_SIZES[2] = patch_length
  
  # Next we need to change a hardcoded pointer to where free space begins. Otherwise the game will overwrite the custom code.
  padded_patch_length = ((patch_length + 3) & ~3) # Pad length of patch to next 4 just in case
  new_start_pointer_for_default_thread = ORIGINAL_FREE_SPACE_RAM_ADDRESS + padded_patch_length # New free space pointer after our custom code
  high_halfword, low_halfword = split_pointer_into_high_and_low_half_for_hardcoding(new_start_pointer_for_default_thread)
  # Now update the asm instructions that load this hardcoded pointer.
  write_u32(dol_data, address_to_offset(0x80307954), 0x3C600000 | high_halfword)
  write_u32(dol_data, address_to_offset(0x8030795C), 0x38030000 | low_halfword)
  # We also update another pointer which seems like it should remain at 0x10000 later in RAM from the pointer we updated.
  # (This pointer was originally 0x8040CFA8.)
  # Updating this one may not actually be necessary to update, but this is to be safe.
  new_end_pointer_for_default_thread = new_start_pointer_for_default_thread + 0x10000
  high_halfword, low_halfword = split_pointer_into_high_and_low_half_for_hardcoding(new_end_pointer_for_default_thread)
  write_u32(dol_data, address_to_offset(0x8030794C), 0x3C600000 | high_halfword)
  write_u32(dol_data, address_to_offset(0x80307950), 0x38030000 | low_halfword)
  write_u32(dol_data, address_to_offset(0x80301854), 0x3C600000 | high_halfword)
  write_u32(dol_data, address_to_offset(0x80301858), 0x38630000 | low_halfword)
  high_halfword = (new_end_pointer_for_default_thread & 0xFFFF0000) >> 16
  low_halfword = new_end_pointer_for_default_thread & 0xFFFF
  write_u32(dol_data, address_to_offset(0x80003278), 0x3C200000 | high_halfword)
  write_u32(dol_data, address_to_offset(0x8000327C), 0x60210000 | low_halfword)
  
  # Original thread start pointer: 803FCFA8 (must be updated)
  # Original stack end pointer (r1): 8040CFA8 (must be updated)
  # Original rtoc pointer (r2): 803FFD00 (must NOT be updated)
  # Original read-write small data area pointer (r13): 803FE0E0 (must NOT be updated)

def set_new_game_starting_spawn_id(self, spawn_id):
  dol_data = self.get_raw_file("sys/main.dol")
  write_u8(dol_data, address_to_offset(0x80058BAF), spawn_id)

def set_new_game_starting_room_index(self, room_index):
  dol_data = self.get_raw_file("sys/main.dol")
  write_u8(dol_data, address_to_offset(0x80058BA7), room_index)

def change_ship_starting_island(self, starting_island_room_index):
  island_dzx = self.get_arc("files/res/Stage/sea/Room%d.arc" % starting_island_room_index).get_file("room.dzr")
  ship_spawns = island_dzx.entries_by_type("SHIP")
  island_ship_spawn_0 = next(x for x in ship_spawns if x.ship_id == 0)
  
  sea_dzx = self.get_arc("files/res/Stage/sea/Stage.arc").get_file("stage.dzs")
  sea_actors = sea_dzx.entries_by_type("ACTR")
  ship_actor = next(x for x in sea_actors if x.name == "Ship")
  ship_actor.x_pos = island_ship_spawn_0.x_pos
  ship_actor.y_pos = island_ship_spawn_0.y_pos
  ship_actor.z_pos = island_ship_spawn_0.z_pos
  ship_actor.y_rot = island_ship_spawn_0.y_rot
  ship_actor.save_changes()

def skip_wakeup_intro_and_start_at_dock(self):
  # When the player starts a new game they usually start at spawn ID 206, which plays the wakeup event and puts the player on Aryll's lookout.
  # We change the starting spawn ID to 0, which does not play the wakeup event and puts the player on the dock next to the ship.
  set_new_game_starting_spawn_id(self, 0)

def start_ship_at_outset(self):
  # Change the King of Red Lion's default position so that he appears on Outset at the start of the game.
  change_ship_starting_island(self, 44)
  
def make_all_text_instant(self):
  for msg in self.bmg.messages:
    msg.initial_draw_type = 1 # Instant initial draw type
    
    # Get rid of wait commands
    msg.string = re.sub(
      r"\\\{1A 07 00 00 07 [0-9a-f]{2} [0-9a-f]{2}\}",
      "",
      msg.string, 0, re.IGNORECASE
    )
    
    # Get rid of wait+dismiss commands
    # Exclude message 7726, for Maggie's Father throwing rupees at you. He only spawns the rupees past a certain frame of his animation, so if you skipped past the text too quickly you wouldn't get any rupees.
    # Exclude message 2488, for Orca talking to you after you learn the Hurricane Spin. Without the wait+dismiss he would wind up repeating some of his lines once.
    if msg.message_id != 7726 and msg.message_id != 2488:
      msg.string = re.sub(
        r"\\\{1A 07 00 00 04 [0-9a-f]{2} [0-9a-f]{2}\}",
        "",
        msg.string, 0, re.IGNORECASE
      )
    
    # Get rid of wait+dismiss (prompt) commands
    msg.string = re.sub(
      r"\\\{1A 07 00 00 03 [0-9a-f]{2} [0-9a-f]{2}\}",
      "",
      msg.string, 0, re.IGNORECASE
    )
  
  # Also change the B button to act as a hold-to-skip button during dialogue.
  apply_patch(self, "b_button_skips_text")

def fix_deku_leaf_model(self):
  # The Deku Leaf is a unique object not used for other items. It's easy to change what item it gives you, but the visual model cannot be changed.
  # So instead we replace the unique Deku Leaf actor ("itemDek") with a more general actor that can be for any field item ("item").
  
  dzx = self.get_arc("files/res/Stage/Omori/Room0.arc").get_file("room.dzr")
  deku_leaf_actors = [actor for actor in dzx.entries_by_type("ACTR") if actor.name == "itemDek"]
  for actor in deku_leaf_actors:
    actor.name = "item"
    actor.params = 0x01FF0000 # Misc params, one of which makes the item not fade out over time
    actor.item_id = 0x34 # Deku Leaf
    actor.item_flag = 2 # This is the same item pickup flag that itemDek originally had in its params.
    actor.set_flag = 0xFF # Unknown what this is, but might need to be FF for the player to pick up the item sometimes?
    actor.save_changes()

def allow_all_items_to_be_field_items(self):
  # Most items cannot be field items (items that appear freely floating on the ground) because they don't have a field model defined.
  # Here we copy the regular item get model to the field model so that any item can be a field item.
  # We also change the code run when you touch the item so that these items play out the full item get animation with text, instead of merely popping up above the player's head like a rupee.
  # And we change the Y offsets so the items don't appear lodged inside the floor, and can be picked up easily.
  # And also change the radius for items that had 0 radius so the player doesn't need to be right inside the item to pick it up.
  # Also change the code run by items during the wait state, which affects the physics when shot out of Gohdan's nose for example.
  
  item_resources_list_start = address_to_offset(0x803842B0)
  field_item_resources_list_start = address_to_offset(0x803866B0)
  itemGetExecute_switch_statement_entries_list_start = address_to_offset(0x8038CA6C)
  mode_wait_switch_statement_entries_list_start = address_to_offset(0x8038CC7C)
  
  dol_data = self.get_raw_file("sys/main.dol")
  
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
      # The Magic Meter Upgrade has no model, so we have to copy the Green Potion model.
      item_id_to_copy_from = 0x52
      # We also change the item get model too, not just the field model.
      item_resources_offset_to_fix = item_resources_list_start + item_id*0x24
    else:
      item_id_to_copy_from = item_id
      item_resources_offset_to_fix = None
    
    item_resources_offset_to_copy_from = item_resources_list_start + item_id_to_copy_from*0x24
    field_item_resources_offset = field_item_resources_list_start + item_id*0x1C
    
    arc_name_pointer = self.arc_name_pointers[item_id_to_copy_from]
    
    if item_id == 0xAA:
      # Hurricane Spin, switch it to using the custom scroll model instead of the sword model.
      arc_name_pointer = self.custom_symbols["hurricane_spin_item_resource_arc_name"]
      item_resources_offset_to_fix = item_resources_list_start + item_id*0x24
    
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
  
  # Also nop out the 7 lines of code that initialize the arc filename pointer for the 6 songs and the Hurricane Spin.
  # These lines would overwrite the changes we made to their arc names.
  for address in [0x800C1970, 0x800C1978, 0x800C1980, 0x800C1988, 0x800C1990, 0x800C1998, 0x800C1BA8]:
    write_u32(dol_data, address_to_offset(address), 0x60000000) # nop
  
  
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
  write_u32(dol_data, address_to_offset(0x800F6468), 0x418102F4) # bgt 0x800F675C
  
  
  # Update the visual Y offsets so the item doesn't look like it's halfway inside the floor and difficult to see.
  # First update the default case of the switch statement in the function getYOffset so that it reads from 803F9E84 (value: 23.0), instead of 803F9E80 (value: 0.0).
  write_u32(dol_data, 0xF1C10, 0xC022A184) # lfs f1, -0x5E7C(rtoc) (at 800F4CD0 in RAM)
  # And fix then Big Key so it uses the default case with the 23.0 offset, instead of using the 0.0 offset. (Other items already use the default case, so we don't need to fix any besides Big Key.)
  write_u32(dol_data, 0x3898B8 + 0x4E*4, 0x800F4CD0)
  
  
  # We also change the Y offset of the hitbox for any items that have 0 for the Y offset.
  # Without this change the item would be very difficult to pick up, the only way would be to stand on top of it and do a spin attack.
  # And also change the radius of the hitbox for items that have 0 for the radius.
  extra_item_data_list_start = address_to_offset(0x803882B0)
  for item_id in range(0, 0xFF+1):
    item_extra_data_entry_offset = extra_item_data_list_start+4*item_id
    original_y_offset = read_u8(dol_data, item_extra_data_entry_offset+1)
    if original_y_offset == 0:
      write_u8(dol_data, item_extra_data_entry_offset+1, 0x28) # Y offset of 0x28
    original_radius = read_u8(dol_data, item_extra_data_entry_offset+2)
    if original_radius == 0:
      write_u8(dol_data, item_extra_data_entry_offset+2, 0x28) # Radius of 0x28
  
  
  for item_id in range(0x20, 0x44+1):
    # Update the switch statement cases in function mode_wait for certain items that originally used the default case (0x800F8190 - leads to calling itemActionForRupee).
    # This default case caused items to have the physics of rupees, which causes them to shoot out too far from Gohdan's nose.
    # We switch it to case 0x800F8160 (itemActionForArrow), which is what heart containers and heart pieces use.
    location_of_items_switch_statement_case = mode_wait_switch_statement_entries_list_start + item_id*4
    write_u32(dol_data, location_of_items_switch_statement_case, 0x800F8160)
  # Also change the switch case used by items with IDs 0x4C+ to go to 800F8160 as well.
  write_u32(dol_data, address_to_offset(0x800F8138), 0x41810028) # bgt 0x800F8160
  
  
  # Also add the Vscroll.arc containing the Hurricane Spin's custom model to the GCM's filesystem.
  vscroll_arc_path = os.path.join(ASSETS_PATH, "Vscroll.arc")
  with open(vscroll_arc_path, "rb") as f:
    data = BytesIO(f.read())
  self.add_new_raw_file("files/res/Object/Vscroll.arc", data)

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

def remove_forsaken_fortress_2_cutscenes(self):
  # Removes the rescuing-Aryll cutscene played by the spawn when you enter the Forsaken Fortress tower.
  dzx = self.get_arc("files/res/Stage/M2tower/Room0.arc").get_file("room.dzr")
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

def make_items_progressive(self):
  # This makes items progressive, so even if you get them out of order, they will always be upgraded, never downgraded.
  
  dol_data = self.get_raw_file("sys/main.dol")
  
  # Update the item get funcs for the items to point to our custom progressive item get funcs instead.
  item_get_funcs_list = address_to_offset(0x803888C8)
  
  for sword_item_id in [0x38, 0x39, 0x3A, 0x3D, 0x3E]:
    sword_item_get_func_offset = item_get_funcs_list + sword_item_id*4
    write_u32(dol_data, sword_item_get_func_offset, self.custom_symbols["progressive_sword_item_func"])
  
  for bow_item_id in [0x27, 0x35, 0x36]:
    bow_item_get_func_offset = item_get_funcs_list + bow_item_id*4
    write_u32(dol_data, bow_item_get_func_offset, self.custom_symbols["progressive_bow_func"])
  
  for wallet_item_id in [0xAB, 0xAC]:
    wallet_item_get_func_offset = item_get_funcs_list + wallet_item_id*4
    write_u32(dol_data, wallet_item_get_func_offset, self.custom_symbols["progressive_wallet_item_func"])
  
  for bomb_bag_item_id in [0xAD, 0xAE]:
    bomb_bag_item_get_func_offset = item_get_funcs_list + bomb_bag_item_id*4
    write_u32(dol_data, bomb_bag_item_get_func_offset, self.custom_symbols["progressive_bomb_bag_item_func"])
  
  for quiver_item_id in [0xAF, 0xB0]:
    quiver_item_get_func_offset = item_get_funcs_list + quiver_item_id*4
    write_u32(dol_data, quiver_item_get_func_offset, self.custom_symbols["progressive_quiver_item_func"])
  
  for picto_box_item_id in [0x23, 0x26]:
    picto_box_item_get_func_offset = item_get_funcs_list + picto_box_item_id*4
    write_u32(dol_data, picto_box_item_get_func_offset, self.custom_symbols["progressive_picto_box_item_func"])
  
  # Register which item ID is for which progressive item.
  self.item_name_to_id["Progressive Sword"] = 0x38
  self.item_name_to_id["Progressive Bow"] = 0x27
  self.item_name_to_id["Progressive Wallet"] = 0xAB
  self.item_name_to_id["Progressive Bomb Bag"] = 0xAD
  self.item_name_to_id["Progressive Quiver"] = 0xAF
  self.item_name_to_id["Progressive Picto Box"] = 0x23
  
  # Modify the item get funcs for bombs and the hero's bow to nop out the code that sets your current and max bombs/arrows to 30.
  # Without this change, getting bombs after a bomb bag upgrade would negate the bomb bag upgrade.
  # Note that normally making this change would cause the player to have 0 max bombs/arrows if they get bombs/bow before any bomb bag/quiver upgrades.
  # But in the new game start code, we set the player's current and max bombs and arrows to 30, so that is no longer an issue.
  write_u32(dol_data, address_to_offset(0x800C36C0), 0x60000000) # Don't set current bombs
  write_u32(dol_data, address_to_offset(0x800C36C4), 0x60000000) # Don't set max bombs
  write_u32(dol_data, address_to_offset(0x800C346C), 0x60000000) # Don't set current arrows
  write_u32(dol_data, address_to_offset(0x800C3470), 0x60000000) # Don't set max arrows
  
  # Modify the item get func for deku leaf to nop out the part where it adds to your magic meter.
  # Instead we start the player with a magic meter when they start a new game.
  # This way other items can use the magic meter before the player gets deku leaf.
  write_u32(dol_data, address_to_offset(0x800C375C), 0x60000000) # Don't set max magic meter
  write_u32(dol_data, address_to_offset(0x800C3768), 0x60000000) # Don't set current magic meter

def make_sail_behave_like_swift_sail(self):
  # Causes the wind direction to always change to face the direction KoRL is facing as long as the sail is out.
  # Also doubles KoRL's speed.
  # And changes the textures to match the swift sail from HD.
  
  ship_data = self.get_raw_file("files/rels/d_a_ship.rel")
  # Change the relocation for line B9FC, which originally called setShipSailState.
  write_u32(ship_data, 0x11C94, self.custom_symbols["set_wind_dir_to_ship_dir"])
  
  write_float(ship_data, 0xDBE8, 55.0*2) # Sailing speed
  write_float(ship_data, 0xDBC0, 80.0*2) # Initial speed
  
  # Also increase deceleration when the player is stopping or is knocked out of the ship.
  apply_patch(self, "swift_sail")
  
  # Update the pause menu name for the sail.
  msg = self.bmg.messages_by_id[463]
  msg.string = "Swift Sail"
  
  new_sail_tex_image_path = os.path.join(ASSETS_PATH, "swift sail texture.png")
  new_sail_icon_image_path = os.path.join(ASSETS_PATH, "swift sail icon.png")
  new_sail_itemget_tex_image_path = os.path.join(ASSETS_PATH, "swift sail item get texture.png")
  
  # Modify the sail's texture while sailing.
  ship_arc = self.get_arc("files/res/Object/Ship.arc")
  sail_image = ship_arc.get_file("new_ho1.bti")
  sail_image.replace_image_from_path(new_sail_tex_image_path)
  sail_image.save_changes()
  
  # Modify the sail's item icon.
  itemicon_arc = self.get_arc("files/res/Msg/itemicon.arc")
  sail_icon_image = itemicon_arc.get_file("sail_00.bti")
  sail_icon_image.replace_image_from_path(new_sail_icon_image_path)
  sail_icon_image.save_changes()
  
  # Modify the sail's item get texture.
  sail_itemget_arc = self.get_arc("files/res/Object/Vho.arc")
  sail_itemget_model = sail_itemget_arc.get_file("vho.bdl")
  sail_itemget_tex_image = sail_itemget_model.tex1.textures_by_name["Vho"][0]
  sail_itemget_tex_image.replace_image_from_path(new_sail_itemget_tex_image_path)
  sail_itemget_model.save_changes()

def add_ganons_tower_warp_to_ff2(self):
  # Normally the warp object from Forsaken Fortress down to Ganon's Tower only appears in FF3.
  # But we changed Forsaken Fortress to remain permanently as FF2.
  # So we need to add the warp object to FF2 as well so the player can conveniently go between the sea and Ganon's Tower.
  # To do this we copy the warp entity from layer 2 onto layer 1.
  
  dzx = self.get_arc("files/res/Stage/sea/Room1.arc").get_file("room.dzr")
  
  layer_2_actors = dzx.entries_by_type_and_layer("ACTR", 2)
  layer_2_warp = next(x for x in layer_2_actors if x.name == "Warpmj")
  
  layer_1_warp = dzx.add_entity("ACTR", layer=1)
  layer_1_warp.name = layer_2_warp.name
  layer_1_warp.params = layer_2_warp.params
  layer_1_warp.x_pos = layer_2_warp.x_pos
  layer_1_warp.y_pos = layer_2_warp.y_pos
  layer_1_warp.z_pos = layer_2_warp.z_pos
  layer_1_warp.auxilary_param = layer_2_warp.auxilary_param
  layer_1_warp.y_rot = layer_2_warp.y_rot
  layer_1_warp.auxilary_param_2 = layer_2_warp.auxilary_param_2
  layer_1_warp.enemy_number = layer_2_warp.enemy_number
  
  dzx.save_changes()

def add_chest_in_place_medli_grappling_hook_gift(self):
  # Add a chest in place of Medli locked in the jail cell at the peak of Dragon Roost Cavern.
  
  dzx = self.get_arc("files/res/Stage/M_Dra09/Stage.arc").get_file("stage.dzs")
  
  chest_in_jail = dzx.add_entity("TRES", layer=None)
  chest_in_jail.name = "takara3"
  chest_in_jail.chest_type = 2
  chest_in_jail.opened_flag = 0x11
  chest_in_jail.x_pos = -1620.81
  chest_in_jail.y_pos = 13600
  chest_in_jail.z_pos = 263.034
  chest_in_jail.room_num = 9
  chest_in_jail.y_rot = 0xCC16
  chest_in_jail.item_id = self.item_name_to_id["Grappling Hook"]
  
  dzx.save_changes()

def add_chest_in_place_queen_fairy_cutscene(self):
  # Add a chest in place of the Queen Fairy cutscene inside Mother Isle.
  
  dzx = self.get_arc("files/res/Stage/sea/Room9.arc").get_file("room.dzr")
  
  mother_island_chest = dzx.add_entity("TRES", layer=None)
  mother_island_chest.name = "takara3"
  mother_island_chest.chest_type = 2
  mother_island_chest.opened_flag = 0x1C
  mother_island_chest.x_pos = -180031
  mother_island_chest.y_pos = 723
  mother_island_chest.z_pos = -199995
  mother_island_chest.room_num = 9
  mother_island_chest.y_rot = 0x1000
  mother_island_chest.item_id = self.item_name_to_id["Progressive Bow"]
  
  dzx.save_changes()

def add_cube_to_earth_temple_first_room(self):
  # If the player enters Earth Temple, uses Medli to cross the gap, brings Medli into the next room, then leaves Earth Temple, Medli will no longer be in the first room.
  # This can softlock the player if they don't have Deku Leaf to get across the gap in that first room.
  # So we add a cube to that first room so the player can just climb up.
  
  dzx = self.get_arc("files/res/Stage/M_Dai/Room0.arc").get_file("room.dzr")
  
  cube = dzx.add_entity("ACTR", layer=None)
  cube.name = "Ecube"
  cube.params = 0x8C00FF00
  cube.x_pos = -6986.07
  cube.y_pos = -600
  cube.z_pos = 4077.37
  
  dzx.save_changes()

def add_more_magic_jars(self):
  # Add more magic jar drops to locations where it can be very inconvenient to not have them.
  
  # Dragon Roost Cavern doesn't have any magic jars in it since you normally wouldn't have Deku Leaf for it.
  # But since using Deku Leaf in DRC can be required by the randomizer, it can be annoying to not have any way to refill MP.
  # We change several skulls that originally dropped nothing when destroyed to drop magic jars instead.
  drc_center_room = self.get_arc("files/res/Stage/M_NewD2/Room2.arc").get_file("room.dzr")
  actors = drc_center_room.entries_by_type("ACTR")
  skulls = [actor for actor in actors if actor.name == "Odokuro"]
  skulls[2].pot_item_id = self.item_name_to_id["Small Magic Jar (Pickup)"]
  skulls[2].save_changes()
  skulls[5].pot_item_id = self.item_name_to_id["Large Magic Jar (Pickup)"]
  skulls[5].save_changes()
  drc_before_boss_room = self.get_arc("files/res/Stage/M_NewD2/Room10.arc").get_file("room.dzr")
  actors = drc_before_boss_room.entries_by_type("ACTR")
  skulls = [actor for actor in actors if actor.name == "Odokuro"]
  skulls[0].pot_item_id = self.item_name_to_id["Large Magic Jar (Pickup)"]
  skulls[0].save_changes()
  skulls[9].pot_item_id = self.item_name_to_id["Large Magic Jar (Pickup)"]
  skulls[9].save_changes()
  
  # The grass on the small elevated islands around DRI have a lot of grass that can drop magic, but it's not guaranteed.
  # Add a new piece of grass to each of the 2 small islands that are guaranteed to drop magic.
  dri = self.get_arc("files/res/Stage/sea/Room13.arc").get_file("room.dzr")
  grass1 = dri.add_entity("ACTR", layer=None)
  grass1.name = "kusax1"
  grass1.grass_type = 0
  grass1.grass_subtype = 0
  grass1.grass_item_drop_type = 0x38 # 62.50% chance of small magic, 37.50% chance of large magic
  grass1.x_pos = 209694
  grass1.y_pos = 1900
  grass1.z_pos = -202463
  grass2 = dri.add_entity("ACTR", layer=None)
  grass2.name = "kusax1"
  grass2.grass_type = 0
  grass2.grass_subtype = 0
  grass2.grass_item_drop_type = 0x38 # 62.50% chance of small magic, 37.50% chance of large magic
  grass2.x_pos = 209333
  grass2.y_pos = 1300
  grass2.z_pos = -210145
  dri.save_changes()
  
  # Make one of the pots next to the entrance to the TotG miniboss always drop large magic.
  totg_before_miniboss_room = self.get_arc("files/res/Stage/Siren/Room14.arc").get_file("room.dzr")
  actors = totg_before_miniboss_room.entries_by_type("ACTR")
  pots = [actor for actor in actors if actor.name == "kotubo"]
  pots[1].pot_item_id = self.item_name_to_id["Large Magic Jar (Pickup)"]
  pots[1].save_changes()

def remove_title_and_ending_videos(self):
  # Remove the huge video files that play during the ending and if you sit on the title screen a while.
  # We replace them with a very small blank video file to save space.
  
  blank_video_path = os.path.join(ASSETS_PATH, "blank.thp")
  with open(blank_video_path, "rb") as f:
    new_data = BytesIO(f.read())
  self.replace_raw_file("files/thpdemo/title_loop.thp", new_data)
  self.replace_raw_file("files/thpdemo/end_st_epilogue.thp", new_data)

def modify_title_screen_logo(self):
  new_title_image_path = os.path.join(ASSETS_PATH, "title.png")
  new_subtitle_image_path = os.path.join(ASSETS_PATH, "subtitle.png")
  tlogoe_arc = self.get_arc("files/res/Object/TlogoE.arc")
  
  title_image = tlogoe_arc.get_file("logo_zelda_main.bti")
  title_image.replace_image_from_path(new_title_image_path)
  title_image.save_changes()
  
  subtitle_model = tlogoe_arc.get_file("subtitle_start_anim_e.bdl")
  subtitle_image = subtitle_model.tex1.textures_by_name["logo_sub_e"][0]
  subtitle_image.replace_image_from_path(new_subtitle_image_path)
  subtitle_model.save_changes()
  
  subtitle_glare_model = tlogoe_arc.get_file("subtitle_kirari_e.bdl")
  subtitle_glare_image = subtitle_glare_model.tex1.textures_by_name["logo_sub_e"][0]
  subtitle_glare_image.replace_image_from_path(new_subtitle_image_path)
  subtitle_glare_model.save_changes()
  
  # Move where the subtitle is drawn downwards a bit so the word "the" doesn't get covered up by the main logo.
  title_data = self.get_raw_file("files/rels/d_a_title.rel")
  y_pos = read_float(title_data, 0x1F44)
  y_pos -= 13.0
  write_float(title_data, 0x1F44, y_pos)
  
  # Move the sparkle particle effect down a bit to fit the taller logo better.
  # (This has the side effect of also moving down the clouds below the ship, but this is not noticeable.)
  data = tlogoe_arc.get_file_entry("title_logo_e.blo").data
  write_u16(data, 0x162, 0x106) # Increase Y pos by 16 pixels (0xF6 -> 0x106)

def update_game_name_icon_and_banners(self):
  new_game_name = "Wind Waker Randomized %s" % self.seed
  banner_data = self.get_raw_file("files/opening.bnr")
  write_str(banner_data, 0x1860, new_game_name, 0x40)
  
  new_game_id = "GZLE99"
  boot_data = self.get_raw_file("sys/boot.bin")
  write_str(boot_data, 0, new_game_id, 6)
  
  dol_data = self.get_raw_file("sys/main.dol")
  new_memory_card_game_name = "Wind Waker Randomizer"
  write_str(dol_data, address_to_offset(0x80339690), new_memory_card_game_name, 21)
  
  new_image_file_path = os.path.join(ASSETS_PATH, "banner.png")
  image_format = texture_utils.ImageFormat.RGB5A3
  palette_format = texture_utils.PaletteFormat.RGB5A3
  image_data, _, _ = texture_utils.encode_image_from_path(new_image_file_path, image_format, palette_format)
  image_data.seek(0)
  write_bytes(banner_data, 0x20, image_data.read())
  
  cardicon_arc = self.get_arc("files/res/CardIcon/cardicon.arc")
  
  memory_card_icon_file_path = os.path.join(ASSETS_PATH, "memory card icon.png")
  memory_card_icon = cardicon_arc.get_file("ipl_icon1.bti")
  memory_card_icon.replace_image_from_path(memory_card_icon_file_path)
  memory_card_icon.save_changes()
  
  memory_card_banner_file_path = os.path.join(ASSETS_PATH, "memory card banner.png")
  memory_card_banner = cardicon_arc.get_file("ipl_banner.bti")
  memory_card_banner.replace_image_from_path(memory_card_banner_file_path)
  memory_card_banner.save_changes()

def allow_dungeon_items_to_appear_anywhere(self):
  dol_data = self.get_raw_file("sys/main.dol")
  item_get_funcs_list = address_to_offset(0x803888C8)
  item_resources_list_start = address_to_offset(0x803842B0)
  field_item_resources_list_start = address_to_offset(0x803866B0)
  
  dungeon_items = [
    ("DRC", "Small Key", 0x13),
    ("DRC", "Big Key", 0x14),
    ("DRC", "Dungeon Map", 0x1B),
    ("DRC", "Compass", 0x1C),
    ("FW", "Small Key", 0x1D),
    ("FW", "Big Key", 0x40),
    ("FW", "Dungeon Map", 0x41),
    ("FW", "Compass", 0x5A),
    ("TotG", "Small Key", 0x5B),
    ("TotG", "Big Key", 0x5C),
    ("TotG", "Dungeon Map", 0x5D),
    ("TotG", "Compass", 0x5E),
    ("FF", "Dungeon Map", 0x5F),
    ("FF", "Compass", 0x60),
    ("ET", "Small Key", 0x73),
    ("ET", "Big Key", 0x74),
    ("ET", "Dungeon Map", 0x75),
    ("ET", "Compass", 0x76),
    ("WT", "Small Key", 0x77),
    ("WT", "Big Key", 0x81),
    ("WT", "Dungeon Map", 0x84),
    ("WT", "Compass", 0x85),
  ]
  
  for short_dungeon_name, base_item_name, item_id in dungeon_items:
    item_name = short_dungeon_name + " " + base_item_name
    base_item_id = self.item_name_to_id[base_item_name]
    dungeon_name = self.logic.DUNGEON_NAMES[short_dungeon_name]
    
    # Register the proper item ID for this item with the randomizer.
    self.item_name_to_id[item_name] = item_id
    
    # Update the item get funcs for the dungeon items to point to our custom item get funcs instead.
    custom_symbol_name = item_name.lower().replace(" ", "_") + "_item_get_func"
    item_get_func_offset = item_get_funcs_list + item_id*4
    write_u32(dol_data, item_get_func_offset, self.custom_symbols[custom_symbol_name])
    
    # Add item get messages for the items.
    if base_item_name == "Small Key":
      description_format_string = "\\{1A 05 00 00 01}You got %s \\{1A 06 FF 00 00 01}%s small key\\{1A 06 FF 00 00 00}!"
      description = word_wrap_string(description_format_string % (get_indefinite_article(dungeon_name), dungeon_name))
    elif base_item_name == "Big Key":
      description_format_string = "\\{1A 05 00 00 01}You got the \\{1A 06 FF 00 00 01}%s Big Key\\{1A 06 FF 00 00 00}!"
      description = word_wrap_string(description_format_string % dungeon_name)
    elif base_item_name == "Dungeon Map":
      description_format_string = "\\{1A 05 00 00 01}You got the \\{1A 06 FF 00 00 01}%s Dungeon Map\\{1A 06 FF 00 00 00}!"
      description = word_wrap_string(description_format_string % dungeon_name)
    elif base_item_name == "Compass":
      description_format_string = "\\{1A 05 00 00 01}You got the \\{1A 06 FF 00 00 01}%s Compass\\{1A 06 FF 00 00 00}!"
      description = word_wrap_string(description_format_string % dungeon_name)
    
    msg = self.bmg.add_new_message(101 + item_id)
    msg.string = description
    msg.text_box_type = 9 # Item get message box
    msg.initial_draw_type = 2 # Slow initial message speed
    msg.display_item_id = item_id
    
    # Update item resources and field item resources so the models/icons show correctly for these items.
    item_resources_offset_to_copy_from = item_resources_list_start + base_item_id*0x24
    field_item_resources_offset_to_copy_from = field_item_resources_list_start + base_item_id*0x24
    item_resources_offset = item_resources_list_start + item_id*0x24
    field_item_resources_offset = field_item_resources_list_start + item_id*0x1C
    
    arc_name_pointer = self.arc_name_pointers[base_item_id]
    
    write_u32(dol_data, field_item_resources_offset, arc_name_pointer)
    write_u32(dol_data, item_resources_offset, arc_name_pointer)
    
    item_icon_filename_pointer = self.icon_name_pointer[base_item_id]
    write_u32(dol_data, item_resources_offset+4, item_icon_filename_pointer)
    
    data1 = read_bytes(dol_data, item_resources_offset_to_copy_from+8, 0xD)
    write_bytes(dol_data, item_resources_offset+8, data1)
    write_bytes(dol_data, field_item_resources_offset+4, data1)
    data2 = read_bytes(dol_data, item_resources_offset_to_copy_from+0x1C, 4)
    write_bytes(dol_data, item_resources_offset+0x1C, data2)
    write_bytes(dol_data, field_item_resources_offset+0x14, data2)
    
    data3 = read_bytes(dol_data, item_resources_offset_to_copy_from+0x15, 7)
    write_bytes(dol_data, item_resources_offset+0x15, data3)
    data4 = read_bytes(dol_data, item_resources_offset_to_copy_from+0x20, 4)
    write_bytes(dol_data, item_resources_offset+0x20, data4)
    
    data5 = read_bytes(dol_data, field_item_resources_offset_to_copy_from+0x11, 3)
    write_bytes(dol_data, field_item_resources_offset+0x11, data5)
    data6 = read_bytes(dol_data, field_item_resources_offset_to_copy_from+0x18, 4)
    write_bytes(dol_data, field_item_resources_offset+0x18, data6)

def word_wrap_string(string, max_line_length=34):
  index_in_str = 0
  wordwrapped_str = ""
  current_word = ""
  current_word_length = 0
  length_of_curr_line = 0
  while index_in_str < len(string):
    char = string[index_in_str]
    
    if char == "\\":
      assert string[index_in_str+1] == "{"
      substr = string[index_in_str:]
      control_code_str_len = substr.index("}") + 1
      substr = substr[:control_code_str_len]
      current_word += substr
      index_in_str += control_code_str_len
    elif char == "\n":
      wordwrapped_str += current_word
      wordwrapped_str += char
      length_of_curr_line = 0
      current_word = ""
      current_word_length = 0
      index_in_str += 1
    elif char == " ":
      wordwrapped_str += current_word
      wordwrapped_str += char
      length_of_curr_line += current_word_length + len(char)
      current_word = ""
      current_word_length = 0
      index_in_str += 1
    else:
      current_word += char
      current_word_length += 1
      index_in_str += 1
      
      if length_of_curr_line + current_word_length > max_line_length:
        wordwrapped_str += "\n"
        length_of_curr_line = 0
        
        if current_word_length > max_line_length:
          wordwrapped_str += current_word + "\n"
          current_word = ""
  
  wordwrapped_str += current_word
  
  return wordwrapped_str

def get_indefinite_article(string):
  first_letter = string.strip()[0].lower()
  if first_letter in ["a", "e", "i", "o", "u"]:
    return "an"
  else:
    return "a"

def pad_string_to_next_4_lines(string):
  lines = string.split("\n")
  padding_lines_needed = (4 - len(lines) % 4) % 4
  for i in range(padding_lines_needed):
    lines.append("")
  return "\n".join(lines) + "\n"

def remove_ballad_of_gales_warp_in_cutscene(self):
  for island_index in range(1, 49+1):
    dzx = self.get_arc("files/res/Stage/sea/Room%d.arc" % island_index).get_file("room.dzr")
    for spawn in dzx.entries_by_type("PLYR"):
      if spawn.spawn_type == 9: # Spawn type is warping in on a cyclone
        spawn.spawn_type = 2 # Change to spawn type of instantly spawning on KoRL instead
        spawn.save_changes()

def fix_shop_item_y_offsets(self):
  dol_data = self.get_raw_file("sys/main.dol")
  shop_item_display_data_list_start = address_to_offset(0x8034FD10)
  
  for item_id in range(0, 0xFE+1):
    display_data_offset = shop_item_display_data_list_start + item_id*0x20
    y_offset = read_float(dol_data, display_data_offset+0x10)
    
    if y_offset == 0 and item_id not in [0x10, 0x11, 0x12]:
      # If the item didn't originally have a Y offset we need to give it one so it's not sunken into the pedestal.
      # Only exception are for items 10 11 and 12 - arrow refill pickups. Those have no Y offset but look fine already.
      new_y_offset = 20.0
      write_float(dol_data, display_data_offset+0x10, new_y_offset)

def update_shop_item_descriptions(self):
  item_name = self.logic.done_item_locations["The Great Sea - Beedle's Shop Ship - 20 Rupee Item"]
  cost = 20
  msg = self.bmg.messages_by_id[3906]
  msg.string = "\\{1A 06 FF 00 00 01}%s  %d Rupees\\{1A 06 FF 00 00 00}" % (item_name, cost)
  msg = self.bmg.messages_by_id[3909]
  msg.string = "%s   %d Rupees\nWill you buy it?\n\\{1A 05 00 00 08}I'll buy it\nNo thanks" % (item_name, cost)
  
  item_name = self.logic.done_item_locations["Rock Spire Isle - Beedle's Special Shop Ship - 500 Rupee Item"]
  cost = 500
  msg = self.bmg.messages_by_id[12106]
  msg.string = "\\{1A 06 FF 00 00 01}%s  %d Rupees\n\\{1A 06 FF 00 00 00}This is my last one." % (item_name, cost)
  msg = self.bmg.messages_by_id[12109]
  msg.string = "This \\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 00} is a mere \\{1A 06 FF 00 00 01}%d Rupees\\{1A 06 FF 00 00 00}!\nBuy it! Buy it! Buy buy buy!\n\\{1A 05 00 00 08}I'll buy it\nNo thanks" % (item_name, cost)
  
  item_name = self.logic.done_item_locations["Rock Spire Isle - Beedle's Special Shop Ship - 950 Rupee Item"]
  cost = 950
  msg = self.bmg.messages_by_id[12107]
  msg.string = "\\{1A 06 FF 00 00 01}%s  %d Rupees\n\\{1A 06 FF 00 00 00}This is my last one of these, too." % (item_name, cost)
  msg = self.bmg.messages_by_id[12110]
  msg.string = "This \\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 00} is only \\{1A 06 FF 00 00 01}%d Rupees\\{1A 06 FF 00 00 00}!\nBuy it! Buy it! Buy buy buy!\n\\{1A 05 00 00 08}I'll buy it\nNo thanks" % (item_name, cost)
  
  item_name = self.logic.done_item_locations["Rock Spire Isle - Beedle's Special Shop Ship - 900 Rupee Item"]
  cost = 900
  msg = self.bmg.messages_by_id[12108]
  msg.string = "\\{1A 06 FF 00 00 01}%s  %d Rupees\n\\{1A 06 FF 00 00 00}The price may be high, but it'll pay\noff handsomely in the end!" % (item_name, cost)
  msg = self.bmg.messages_by_id[12111]
  msg.string = "This \\{1A 06 FF 00 00 01}%s \\{1A 06 FF 00 00 00}is just \\{1A 06 FF 00 00 01}%d Rupees!\\{1A 06 FF 00 00 00}\nBuy it! Buy it! Buy buy buy!\n\\{1A 05 00 00 08}I'll buy it\nNo thanks" % (item_name, cost)

def update_auction_item_names(self):
  item_name = self.logic.done_item_locations["Windfall Island - 40 Rupee Auction"]
  msg = self.bmg.messages_by_id[7440]
  msg.string = "\\{1A 06 FF 00 00 01}%s" % item_name
  
  item_name = self.logic.done_item_locations["Windfall Island - 5 Rupee Auction"]
  msg = self.bmg.messages_by_id[7441]
  msg.string = "\\{1A 06 FF 00 00 01}%s" % item_name
  
  item_name = self.logic.done_item_locations["Windfall Island - 60 Rupee Auction"]
  msg = self.bmg.messages_by_id[7442]
  msg.string = "\\{1A 06 FF 00 00 01}%s" % item_name
  
  item_name = self.logic.done_item_locations["Windfall Island - 80 Rupee Auction"]
  msg = self.bmg.messages_by_id[7443]
  msg.string = "\\{1A 06 FF 00 00 01}%s" % item_name

def update_battlesquid_item_names(self):
  item_name = self.logic.done_item_locations["Windfall Island - Battlesquid - First Prize"]
  msg = self.bmg.messages_by_id[7520]
  msg.string = "\\{1A 05 01 00 8E}Hoorayyy! Yayyy! Yayyy!\nOh, thank you, Mr. Sailor!\n\n\n"
  msg.string += word_wrap_string(
    "Please take this \\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 00} as a sign of our gratitude. You are soooooo GREAT!" % item_name,
    max_line_length=43
  )
  
  item_name = self.logic.done_item_locations["Windfall Island - Battlesquid - Second Prize"]
  msg = self.bmg.messages_by_id[7521]
  msg.string = "\\{1A 05 01 00 8E}Hoorayyy! Yayyy! Yayyy!\nOh, thank you so much, Mr. Sailor!\n\n\n"
  msg.string += word_wrap_string(
    "This is our thanks to you! It's been passed down on our island for many years, so don't tell the island elder, OK? Here...\\{1A 06 FF 00 00 01}\\{1A 05 00 00 39} \\{1A 06 FF 00 00 00}Please accept this \\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 00}!" % item_name,
    max_line_length=43
  )
  
  # The high score one doesn't say the item name in text anywhere, so no need to update it.
  #item_name = self.logic.done_item_locations["Windfall Island - Battlesquid - 20 Shots or Less Prize"]
  #msg = self.bmg.messages_by_id[7523]

def update_item_names_in_letter_advertising_rock_spire_shop(self):
  item_name_1 = self.logic.done_item_locations["Rock Spire Isle - Beedle's Special Shop Ship - 500 Rupee Item"]
  item_name_2 = self.logic.done_item_locations["Rock Spire Isle - Beedle's Special Shop Ship - 950 Rupee Item"]
  item_name_3 = self.logic.done_item_locations["Rock Spire Isle - Beedle's Special Shop Ship - 900 Rupee Item"]
  msg = self.bmg.messages_by_id[3325]
  
  lines = msg.string.split("\n")
  unchanged_string_before = "\n".join(lines[0:8]) + "\n"
  unchanged_string_after = "\n".join(lines[12:])
  
  hint_string = "Do you have need of %s \\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 00}, %s \\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 00}, or %s \\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 00}? We have them at special bargain prices." % (
    get_indefinite_article(item_name_1), item_name_1,
    get_indefinite_article(item_name_2), item_name_2,
    get_indefinite_article(item_name_3), item_name_3,
  )
  
  # Letters have 2 spaces at the start of each line, so word wrap to 41 chars instead of 43, then add 2 spaces to each line.
  hint_string = word_wrap_string(hint_string, max_line_length=41)
  hint_string = pad_string_to_next_4_lines(hint_string)
  hint_lines = hint_string.split("\n")
  leading_spaces_hint_lines = []
  for hint_line in hint_lines:
    if hint_line == "":
      leading_spaces_hint_lines.append(hint_line)
    else:
      leading_spaces_hint_lines.append("  " + hint_line)
  hint_string = "\n".join(leading_spaces_hint_lines)
  
  msg.string = unchanged_string_before
  msg.string += hint_string
  msg.string += unchanged_string_after

def update_savage_labyrinth_hint_tablet(self):
  # Update the tablet on the first floor of savage labyrinth to give hints as to the items inside the labyrinth.
  
  floor_30_item_name = self.logic.done_item_locations["Outset Island - Savage Labyrinth - Floor 30"]
  floor_50_item_name = self.logic.done_item_locations["Outset Island - Savage Labyrinth - Floor 50"]
  
  floor_30_is_progress = (floor_30_item_name in self.logic.all_progress_items)
  floor_50_is_progress = (floor_50_item_name in self.logic.all_progress_items)
  
  if self.options.get("progression_triforce_charts"):
    if floor_30_item_name.startswith("Triforce Chart"):
      floor_30_item_name = "Triforce Chart"
    if floor_50_item_name.startswith("Triforce Chart"):
      floor_50_item_name = "Triforce Chart"
  
  if self.options.get("progression_treasure_charts"):
    if floor_30_item_name.startswith("Treasure Chart"):
      floor_30_item_name = "Treasure Chart"
    if floor_50_item_name.startswith("Treasure Chart"):
      floor_50_item_name = "Treasure Chart"
  
  if self.options.get("progression_dungeons"):
    if floor_30_item_name.endswith("Small Key"):
      floor_30_item_name = "Small Key"
    if floor_30_item_name.endswith("Big Key"):
      floor_30_item_name = "Big Key"
    if floor_50_item_name.endswith("Small Key"):
      floor_50_item_name = "Small Key"
    if floor_50_item_name.endswith("Big Key"):
      floor_50_item_name = "Big Key"
  
  if floor_30_is_progress and not floor_30_item_name in self.progress_item_hints:
    raise Exception("Could not find progress item hint for item: %s" % floor_30_item_name)
  if floor_50_is_progress and not floor_50_item_name in self.progress_item_hints:
    raise Exception("Could not find progress item hint for item: %s" % floor_50_item_name)
  
  if floor_30_is_progress and floor_50_is_progress:
    floor_30_item_hint = self.progress_item_hints[floor_30_item_name]
    floor_50_item_hint = self.progress_item_hints[floor_50_item_name]
    hint = "\\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 00}" % floor_30_item_hint
    hint += " and "
    hint += "\\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 00}" % floor_50_item_hint
    hint += " await"
  elif floor_30_is_progress:
    floor_30_item_hint = self.progress_item_hints[floor_30_item_name]
    hint = "\\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 00}" % floor_30_item_hint
    hint += " and "
    hint += "challenge"
    hint += " await"
  elif floor_50_is_progress:
    floor_50_item_hint = self.progress_item_hints[floor_50_item_name]
    hint = "challenge"
    hint += " and "
    hint += "\\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 00}" % floor_50_item_hint
    hint += " await"
  else:
    hint = "challenge"
    hint += " awaits"
  msg = self.bmg.messages_by_id[837]
  msg.string = "\\{1A 07 FF 00 01 00 96}\\{1A 06 FF 00 00 01}The Savage Labyrinth\n\\{1A 07 FF 00 01 00 64}\n\n\n"
  msg.string += word_wrap_string(
    "\\{1A 06 FF 00 00 00}Deep in the never-ending darkness, the way to %s." % hint,
    max_line_length=43
  )

def update_randomly_chosen_hints(self):
  hints = []
  unique_items_given_hint_for = []
  possible_item_locations = list(self.logic.done_item_locations.keys())
  self.rng.shuffle(possible_item_locations)
  num_fishman_hints = 15
  desired_num_hints = 1 + num_fishman_hints
  min_num_hints_needed = 1 + 1
  while True:
    if not possible_item_locations:
      if len(hints) >= min_num_hints_needed:
        break
      else:
        raise Exception("Not enough valid items to give hints for")
    
    location_name = possible_item_locations.pop()
    
    item_name = self.logic.done_item_locations[location_name]
    if item_name not in self.logic.all_progress_items:
      continue
    if self.logic.is_dungeon_item(item_name):
      continue
    if item_name in unique_items_given_hint_for:
      # Don't give hints for 2 instances of the same item (e.g. empty bottle, progressive bow, etc).
      continue
    if item_name not in self.progress_item_hints:
      # Charts and dungeon items don't have hints
      continue
    if item_name == "Bait Bag":
      # Can't access fishmen hints until you already have the bait bag
      continue
    if len(hints) >= desired_num_hints:
      break
    
    zone_name, specific_location_name = self.logic.split_location_name_by_zone(location_name)
    is_dungeon = "Dungeon" in self.logic.item_locations[location_name]["Types"]
    is_puzzle_cave = "Puzzle Secret Cave" in self.logic.item_locations[location_name]["Types"]
    is_combat_cave = "Combat Secret Cave" in self.logic.item_locations[location_name]["Types"]
    is_savage = "Savage Labyrinth" in self.logic.item_locations[location_name]["Types"]
    if zone_name in self.dungeon_and_cave_island_locations and (is_dungeon or is_puzzle_cave or is_combat_cave or is_savage):
      # If the location is in a dungeon or cave, use the hint for whatever island the dungeon/cave is located on.
      island_name = self.dungeon_and_cave_island_locations[zone_name]
      island_hint_name = self.island_name_hints[island_name]
    elif zone_name in self.island_name_hints:
      island_hint_name = self.island_name_hints[zone_name]
    elif zone_name in self.logic.DUNGEON_NAMES.values():
      continue
    else:
      continue
    
    item_hint_name = self.progress_item_hints[item_name]
    
    hints.append((item_hint_name, island_hint_name))
    
    unique_items_given_hint_for.append(item_name)
  
  update_big_octo_great_fairy_item_name_hint(self, hints[0])
  update_fishmen_hints(self, hints[1:])

def update_fishmen_hints(self, hints):
  for fishman_island_number in range(1, 49+1):
    item_hint_name, island_hint_name = self.rng.choice(hints)
    
    hint_lines = []
    hint_lines.append(
      "I've heard from my sources that \\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 00} is located in \\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 00}." % (item_hint_name, island_hint_name)
    )
    # Add a two-second wait command (delay) to prevent the player from skipping over the hint accidentally.
    hint_lines[-1] += "\\{1A 07 00 00 07 00 3C}"
    
    hint_lines.append("Could be worth a try checking that place out. If you know where it is, of course.")
    if self.options.get("instant_text_boxes"):
      # If instant text mode is on, we need to reset the text speed to instant after the wait command messed it up.
      hint_lines[-1] = "\\{1A 05 00 00 01}" + hint_lines[-1]
    
    hint = ""
    for hint_line in hint_lines:
      hint_line = word_wrap_string(hint_line)
      hint_line = pad_string_to_next_4_lines(hint_line)
      hint += hint_line
    
    msg_id = 13026 + fishman_island_number
    msg = self.bmg.messages_by_id[msg_id]
    msg.string = hint

def update_big_octo_great_fairy_item_name_hint(self, hint):
  item_hint_name, island_hint_name = hint
  self.bmg.messages_by_id[12015].string = word_wrap_string(
    "\\{1A 06 FF 00 00 05}In \\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 05}, you will find an item." % island_hint_name,
    max_line_length=43
  )
  self.bmg.messages_by_id[12016].string = word_wrap_string(
    "\\{1A 06 FF 00 00 05}...\\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 05} which may help you on your quest." % item_hint_name.capitalize(),
    max_line_length=43
  )
  self.bmg.messages_by_id[12017].string = word_wrap_string(
    "\\{1A 06 FF 00 00 05}When you find you have need of such an item, you must journey to that place.",
    max_line_length=43
  )

def shorten_zephos_event(self):
  # Make the Zephos event end when the player gets the item from the shrine, before Zephos actually appears.
  
  event_list = self.get_arc("files/res/Stage/sea/Stage.arc").get_file("event_list.dat")
  wind_shrine_event = event_list.events_by_name["TACT_HT"]
  zephos = next(actor for actor in wind_shrine_event.actors if actor.name == "Hr")
  link = next(actor for actor in wind_shrine_event.actors if actor.name == "Link")
  camera = next(actor for actor in wind_shrine_event.actors if actor.name == "CAMERA")
  
  zephos.actions = zephos.actions[0:7]
  link.actions = link.actions[0:7]
  camera.actions = camera.actions[0:5]
  wind_shrine_event.ending_flags = [
    zephos.actions[-1].flag_id_to_set,
    link.actions[-1].flag_id_to_set,
    camera.actions[-1].flag_id_to_set,
  ]

def update_korl_dialogue(self):
  msg = self.bmg.messages_by_id[3443]
  msg.string = "\\{1A 05 00 00 00}, the sea is all yours.\n"
  msg.string += "Make sure you explore every corner\n"
  msg.string += "in search of items to help you. Remember\n"
  msg.string += "that your quest is to defeat Ganondorf."

def set_num_starting_triforce_shards(self):
  num_starting_triforce_shards = int(self.options.get("num_starting_triforce_shards", 0))
  num_shards_address = self.custom_symbols["num_triforce_shards_to_start_with"]
  dol_data = self.get_raw_file("sys/main.dol")
  write_u8(dol_data, address_to_offset(num_shards_address), num_starting_triforce_shards)

def add_pirate_ship_to_windfall(self):
  windfall_dzx = self.get_arc("files/res/Stage/sea/Room11.arc").get_file("room.dzr")
  
  windfall_layer_2_actors = windfall_dzx.entries_by_type_and_layer("ACTR", 2)
  layer_2_pirate_ship = next(x for x in windfall_layer_2_actors if x.name == "Pirates")
  
  default_layer_pirate_ship = windfall_dzx.add_entity("ACTR", layer=None)
  default_layer_pirate_ship.name = layer_2_pirate_ship.name
  default_layer_pirate_ship.params = layer_2_pirate_ship.params
  default_layer_pirate_ship.x_pos = layer_2_pirate_ship.x_pos
  default_layer_pirate_ship.y_pos = layer_2_pirate_ship.y_pos
  default_layer_pirate_ship.z_pos = layer_2_pirate_ship.z_pos
  default_layer_pirate_ship.auxilary_param = layer_2_pirate_ship.auxilary_param
  default_layer_pirate_ship.y_rot = layer_2_pirate_ship.y_rot
  default_layer_pirate_ship.auxilary_param_2 = layer_2_pirate_ship.auxilary_param_2
  default_layer_pirate_ship.enemy_number = layer_2_pirate_ship.enemy_number
  
  # Change the door to not require a password.
  default_layer_pirate_ship.pirate_ship_door_type = 0
  
  windfall_dzx.save_changes()
  
  # Remove Niko to get rid of his events.
  ship_dzx = self.get_arc("files/res/Stage/Asoko/Room0.arc").get_file("room.dzr")
  for layer_num in [2, 3]:
    ship_actors_on_this_layer = ship_dzx.entries_by_type_and_layer("ACTR", layer_num)
    niko = next(x for x in ship_actors_on_this_layer if x.name == "P2b")
    ship_dzx.remove_entity(niko, "ACTR", layer=layer_num)
    ship_dzx.save_changes()

WarpPotData = namedtuple("WarpPotData", 'stage_name room_num x y z y_rot event_reg_index')
INTER_DUNGEON_WARP_DATA = [
  [
    WarpPotData("M_NewD2", 2, 2185, 0, 590, 0xA000, 2), # DRC
    WarpPotData("kindan", 1, 986, 3956.43, 9588, 0xB929, 2), # FW
    WarpPotData("Siren", 6, 277, 229.42, -6669, 0xC000, 2), # TotG
  ],
  [
    WarpPotData("ma2room", 2, 1556, 728.46, -7091, 0xEAA6, 5), # FF
    WarpPotData("M_Dai", 3, -358, 0, -778, 0x4000, 5), # ET
    WarpPotData("kaze", 3, -4333, 1100, 48, 0x4000, 5), # WT
  ],
]

def add_inter_dungeon_warp_pots(self):
  for warp_pot_datas_in_this_cycle in INTER_DUNGEON_WARP_DATA:
    for warp_pot_index, warp_pot_data in enumerate(warp_pot_datas_in_this_cycle):
      room_arc_path = "files/res/Stage/%s/Room%d.arc" % (warp_pot_data.stage_name, warp_pot_data.room_num)
      stage_arc_path = "files/res/Stage/%s/Stage.arc" % warp_pot_data.stage_name
      room_dzx = self.get_arc(room_arc_path).get_file("room.dzr")
      stage_dzx = self.get_arc(stage_arc_path).get_file("stage.dzs")
      
      # Add new player spawn locations.
      if warp_pot_data.stage_name in ["M_Dai", "kaze"]:
        # Earth and Wind temple spawns must be in the stage instead of the room or the game will crash. Not sure why.
        dzx_for_spawn = stage_dzx
      else:
        dzx_for_spawn = room_dzx
      spawn = dzx_for_spawn.add_entity("PLYR", layer=None)
      spawn.spawn_type = 7 # Flying out of a warp pot
      spawn.room_num = warp_pot_data.room_num
      spawn.x_pos = warp_pot_data.x
      spawn.y_pos = warp_pot_data.y
      spawn.z_pos = warp_pot_data.z
      spawn.y_rot = warp_pot_data.y_rot
      spawn.spawn_id = 69
      
      # Ensure there wasn't already a spawn using the ID we chose, just to be safe.
      spawns = dzx_for_spawn.entries_by_type("PLYR")
      spawn_id_69s = [x for x in spawns if x.spawn_id == 69]
      assert len(spawn_id_69s) == 1
      
      # Add new exits.
      for other_warp_pot_data in warp_pot_datas_in_this_cycle:
        scls_exit = room_dzx.add_entity("SCLS", layer=None)
        scls_exit.dest_stage_name = other_warp_pot_data.stage_name
        scls_exit.spawn_id = 69
        scls_exit.room_index = other_warp_pot_data.room_num
        scls_exit.fade_type = 4 # Warp pot fade out
      
      all_scls_exits = room_dzx.entries_by_type_and_layer("SCLS", None)
      scls_exit_index_1 = len(all_scls_exits)-3
      scls_exit_index_2 = len(all_scls_exits)-2
      scls_exit_index_3 = len(all_scls_exits)-1
      
      # Add the warp pots themselves.
      warp_pot = room_dzx.add_entity("ACTR", layer=None)
      warp_pot.name = "Warpts%d" % (warp_pot_index+1) # Warpts1 Warpts2 or Warpts3
      warp_pot.warp_pot_type = warp_pot_index + 2 # 2 3 or 4
      warp_pot.warp_pot_event_reg_index = warp_pot_data.event_reg_index
      warp_pot.warp_pot_dest_1 = scls_exit_index_1
      warp_pot.warp_pot_dest_2 = scls_exit_index_2
      warp_pot.warp_pot_dest_3 = scls_exit_index_3
      warp_pot.x_pos = warp_pot_data.x
      warp_pot.y_pos = warp_pot_data.y
      warp_pot.z_pos = warp_pot_data.z
      warp_pot.y_rot = warp_pot_data.y_rot
      warp_pot.auxilary_param = 0xFFFF
      warp_pot.auxilary_param_2 = 0xFFFF
      
      room_dzx.save_changes()
      stage_dzx.save_changes()
  
  # We also need to copy the particles used by the warp pots into the FF and TotG particle banks.
  # Without this the warp pots would have no particles, and the game would crash on real hardware.
  drc_jpc = self.get_jpc("files/res/Particle/Pscene035.jpc")
  totg_jpc = self.get_jpc("files/res/Particle/Pscene050.jpc")
  ff_jpc = self.get_jpc("files/res/Particle/Pscene043.jpc")
  
  for particle_id in [0x8161, 0x8162, 0x8165, 0x8166]:
    particle = drc_jpc.particles_by_id[particle_id]
    
    for dest_jpc in [totg_jpc, ff_jpc]:
      copied_particle = copy.deepcopy(particle)
      dest_jpc.add_particle(copied_particle)
      
      for texture_filename in copied_particle.tdb1.texture_filenames:
        if texture_filename not in dest_jpc.textures_by_filename:
          texture = drc_jpc.textures_by_filename[texture_filename]
          copied_texture = copy.deepcopy(texture)
          dest_jpc.add_texture(copied_texture)

def remove_makar_kidnapping_event(self):
  dzx = self.get_arc("files/res/Stage/kaze/Room3.arc").get_file("room.dzr")
  actors = dzx.entries_by_type_and_layer("ACTR", None)
  
  # Remove the AND switch actor that makes the Floormasters appear after unlocking the door.
  and_switch_actor = next(x for x in actors if x.name == "AND_SW2")
  dzx.remove_entity(and_switch_actor, "ACTR", layer=None)
  
  # Remove the prerequisite switch index from the Wizzrobe so it's just always there.
  wizzrobe = next(x for x in actors if x.name == "wiz_r")
  wizzrobe.wizzrobe_prereq_switch_index = 0xFF
  wizzrobe.save_changes()
  
  dzx.save_changes()

def increase_player_movement_speeds(self):
  dol_data = self.get_raw_file("sys/main.dol")
  
  # Double crawling speed
  write_float(dol_data, address_to_offset(0x8035DB94), 3.0*2)
  
  # Change rolling so that it scales from 20.0 to 26.0 speed depending on the player's speed when they roll.
  # (In vanilla, it scaled from 0.5 to 26.0 instead.)
  write_float(dol_data, address_to_offset(0x8035D3D0), 6.0/17.0) # Rolling speed multiplier on walking speed
  write_float(dol_data, address_to_offset(0x8035D3D4), 20.0) # Rolling base speed

def add_chart_number_to_item_get_messages(self):
  for item_id, item_name in self.item_names.items():
    if item_name.startswith("Treasure Chart "):
      msg = self.bmg.messages_by_id[101 + item_id]
      msg.string = msg.string.replace("a \\{1A 06 FF 00 00 01}Treasure Chart", "\\{1A 06 FF 00 00 01}%s" % item_name)
    elif item_name.startswith("Triforce Chart ") and not "deciphered" in item_name:
      msg = self.bmg.messages_by_id[101 + item_id]
      msg.string = msg.string.replace("a \\{1A 06 FF 00 00 01}Triforce Chart", "\\{1A 06 FF 00 00 01}%s" % item_name)


# Speeds up the grappling hook significantly to behave similarly to HD
def increase_grapple_animation_speed(self):
  dol_data = self.get_raw_file("sys/main.dol")
  
  # Double the velocity the grappling hook is thrown out (from 20.0 to 40.0)
  write_float(dol_data, address_to_offset(0x803F9D28), 40.0) # Grappling hook velocity
  
  # Half the number of frames grappling hook extends outward in 1st person (from 40 to 20 frames)
  write_u32(dol_data, address_to_offset(0x800EDB74), 0x38030014) # addi r0,r3,20
  
  # Half the number of frames grappling hook extends outward in 3rd person (from 20 to 10)
  write_u32(dol_data, address_to_offset(0x800EDEA4), 0x3803000A) # addi r0,r3,10
  
  # Increase the speed in which the grappling hook falls onto it's target (from 10.0 to 20.0)
  write_float(dol_data, address_to_offset(0x803F9C44), 20.0) 
  
  # Increase grappling hook speed as it wraps around it's target (from 17.0 to 25.0)
  write_float(dol_data, address_to_offset(0x803F9D60), 25.0) 
  
  # Increase the counter that determines how fast to end the wrap around animation. (From +1 each frame to +6 each frame)
  write_u32(dol_data, address_to_offset(0x800EECA8), 0x38A30006) # addi r5,r3,6

# Speeds up the rate in which blocks move when pushed/pulled
def increase_block_moving_animation(self):
  dol_data = self.get_raw_file("sys/main.dol")
  
  #increase Link's pulling animation from 1.0 to 1.4 (purely visual)
  write_float(dol_data, address_to_offset(0x8035DBB0), 1.4)
  
  #increase Link's pushing animation from 1.0 to 1.4 (purely visual)
  write_float(dol_data, address_to_offset(0x8035DBB8), 1.4)
  
  block_data = self.get_raw_file("files/rels/d_a_obj_movebox.rel")
  
  offset = 0x54B0 # M_attr__Q212daObjMovebox5Act_c. List of various data for each type of block.
  for i in range(13): # 13 types of blocks total.
    write_u16(block_data, offset + 4, 12) # Reduce number frames for pushing to last from 20 to 12
    write_u16(block_data, offset + 0xA, 12) # Reduce number frames for pulling to last from 20 to 12
    offset += 0x9C

def increase_misc_animations(self):
  dol_data = self.get_raw_file("sys/main.dol")
  
  #increase the animation speed that Link initiates a climb (0.8 -> 1.6)
  write_float(dol_data, address_to_offset(0x8035D738), 1.6)
  
  #increase speed Link climbs ladders/vines (1.2 -> 1.6)
  write_float(dol_data, address_to_offset(0x8035DB38), 1.6)
  
  #increase speed Link starts climbing a ladder/vine (1.0 -> 1.6)
  write_float(dol_data, address_to_offset(0x8035DB18), 1.6)
  
  #increase speed Links ends climbing a ladder/vine (0.9 -> 1.4)
  write_float(dol_data, address_to_offset(0x8035DB20), 1.4)
  
  # Half the number of frames camera takes to focus on an npc for a conversation (from 20 to 10)
  write_u32(dol_data, address_to_offset(0x8016DA2C), 0x3800000A) # li r0,10
  
  # Half the number of frames zooming into first person takes (from 10 to 5)
  #Commented out, doesn't improve speed in which first person items can be used and can cause minor visual oddities
  #write_u32(dol_data, address_to_offset(0x80170B20), 0x3BA00005) # li r29,5 
  
  #increase the rotation speed on ropes (64.0 -> 100.0)
  write_float(dol_data, address_to_offset(0x803FA2E8), 100.0)


def change_starting_clothes(self):
  custom_model_metadata = customizer.get_model_metadata(self.custom_model_name)
  disable_casual_clothes = custom_model_metadata.get("disable_casual_clothes", False)
  
  should_start_with_heros_clothes_address = self.custom_symbols["should_start_with_heros_clothes"]
  dol_data = self.get_raw_file("sys/main.dol")
  if self.options.get("player_in_casual_clothes") and not disable_casual_clothes:
    write_u8(dol_data, address_to_offset(should_start_with_heros_clothes_address), 0)
  else:
    write_u8(dol_data, address_to_offset(should_start_with_heros_clothes_address), 1)

def shorten_auction_intro_event(self):
  event_list = self.get_arc("files/res/Stage/Orichh/Stage.arc").get_file("event_list.dat")
  wind_shrine_event = event_list.events_by_name["AUCTION_START"]
  camera = next(actor for actor in wind_shrine_event.actors if actor.name == "CAMERA")
  
  pre_pan_delay = camera.actions[2]
  pan_action = camera.actions[3]
  post_pan_delay = camera.actions[4]
  
  # Remove the 200 frame long panning action and the 30 frame delay after panning.
  # We don't remove the 30 frame delay before panning, because of the intro is completely removed or only a couple frames long, there is a race condition where the timer entity may not be finished being asynchronously created until the intro is over. If this happens the auction entity will have no reference to the timer entity, causing a crash later on.
  camera.actions.remove(pan_action)
  camera.actions.remove(post_pan_delay)

def disable_invisible_walls(self):
  # Remove some invisible walls to allow sequence breaking.
  # In vanilla switch index FF meant an invisible wall appears only when you have no sword.
  # But we remove that in randomizer, so invisible walls with switch index FF act effectively completely disabled. So we use this to disable these invisible walls.
  
  # Remove an invisible wall in the second room of DRC.
  dzx = self.get_arc("files/res/Stage/M_NewD2/Room2.arc").get_file("room.dzr")
  invisible_wall = next(x for x in dzx.entries_by_type("SCOB") if x.name == "Akabe")
  invisible_wall.invisible_wall_switch_index = 0xFF
  invisible_wall.save_changes()

def update_skip_rematch_bosses_game_variable(self):
  skip_rematch_bosses_address = self.custom_symbols["skip_rematch_bosses"]
  dol_data = self.get_raw_file("sys/main.dol")
  if self.options.get("skip_rematch_bosses"):
    write_u8(dol_data, address_to_offset(skip_rematch_bosses_address), 1)
  else:
    write_u8(dol_data, address_to_offset(skip_rematch_bosses_address), 0)

def update_sword_mode_game_variable(self):
  sword_mode_address = self.custom_symbols["sword_mode"]
  dol_data = self.get_raw_file("sys/main.dol")
  if self.options.get("sword_mode") == "Start with Sword":
    write_u8(dol_data, address_to_offset(sword_mode_address), 0)
  elif self.options.get("sword_mode") == "Randomized Sword":
    write_u8(dol_data, address_to_offset(sword_mode_address), 1)
  elif self.options.get("sword_mode") == "Swordless":
    write_u8(dol_data, address_to_offset(sword_mode_address), 2)
  else:
    raise Exception("Unknown sword mode: %s" % self.options.get("sword_mode"))

def update_starting_gear(self):
  starting_gear = self.options.get("starting_gear")
  if len(starting_gear) > MAXIMUM_ADDITIONAL_STARTING_ITEMS:
    raise Exception("Tried to start with more starting items than the maximum number that was allocated")
  starting_gear_array_address = self.custom_symbols["starting_gear"]
  dol_data = self.get_raw_file("sys/main.dol")
  normal_items = 0
  for i in range(len(starting_gear)):
    item_id = self.item_name_to_id[starting_gear[i]]
    write_u8(dol_data,
             address_to_offset(starting_gear_array_address + i),
             item_id)
  write_u8(dol_data,
           address_to_offset(starting_gear_array_address + len(starting_gear)),
           0xFF)

def update_text_for_swordless(self):
  msg = self.bmg.messages_by_id[1128]
  msg.string = "\\{1A 05 00 00 00}, you may not have the\nMaster Sword, but do not be afraid!\n\n\n"
  msg.string += "The hammer of the dead is all you\nneed to crush your foe...\n\n\n"
  msg.string += "Even as his ball of fell magic bears down\non you, you can \\{1A 06 FF 00 00 01}knock it back\nwith an empty bottle\\{1A 06 FF 00 00 00}!\n\n"
  msg.string += "...I am sure you will have a shot at victory!"
  
  msg = self.bmg.messages_by_id[1590]
  msg.string = "\\{1A 05 00 00 00}! Do not run! Trust in the\n"
  msg.string += "power of the Skull Hammer!"

def add_hint_signs(self):
  # Add a hint sign to the second room of DRC with an arrow pointing to the passage to the Big Key Chest.
  new_message_id = 847
  msg = self.bmg.add_new_message(new_message_id)
  msg.string = "\\{1A 05 00 00 15}" # Right arrow
  msg.text_box_type = 2 # Wooden sign message box
  msg.initial_draw_type = 1 # Instant initial message speed
  msg.text_alignment = 3 # Centered text alignment
  
  dzx = self.get_arc("files/res/Stage/M_NewD2/Room2.arc").get_file("room.dzr")
  bomb_flowers = [actor for actor in dzx.entries_by_type_and_layer("ACTR", None) if actor.name == "BFlower"]
  bomb_flowers[1].name = "Kanban"
  bomb_flowers[1].params = new_message_id
  bomb_flowers[1].y_rot = 0x2000
  bomb_flowers[1].save_changes()

def prevent_door_boulder_softlocks(self):
  # DRC has a couple of doors that are blocked by boulders on one side.
  # This is an issue if the player sequence breaks and goes backwards - when they open the door Link will be stuck walking into the boulder forever and the player will have no control.
  # To avoid this, add an event trigger on the back side of those doors that causes the boulder to disappear when the player touches it.
  # This allows us to keep the boulder when the player goes forward through the dungeon, but not backwards.
  
  # Add a new dummy event that doesn't do anything.
  event_list = self.get_arc("files/res/Stage/M_NewD2/Stage.arc").get_file("event_list.dat")
  dummy_event = event_list.add_event("dummy_event")
  event_list.save_changes()
  
  # Add a new EVNT entry for the dummy event.
  dzs = self.get_arc("files/res/Stage/M_NewD2/Stage.arc").get_file("stage.dzs")
  dummy_evnt = dzs.add_entity("EVNT")
  dummy_evnt.name = dummy_event.name
  dzs.save_changes()
  dummy_evnt_index = dzs.entries_by_type("EVNT").index(dummy_evnt)
  
  # Add a TagEv (event trigger region) on the other side of the first door blocked by a boulder.
  boulder_destroyed_switch_index = 5
  dzr = self.get_arc("files/res/Stage/M_NewD2/Room13.arc").get_file("room.dzr")
  tag_ev = dzr.add_entity("SCOB", layer=None)
  tag_ev.name = "TagEv"
  tag_ev.params = 0x00FF00FF
  tag_ev.event_trigger_seen_switch_index = boulder_destroyed_switch_index
  tag_ev.event_trigger_evnt_index = dummy_evnt_index
  tag_ev.x_pos = 2635
  tag_ev.y_pos = 0
  tag_ev.z_pos = 227
  tag_ev.auxilary_param = 0
  tag_ev.y_rot = 0xC000
  tag_ev.auxilary_param_2 = 0xFFFF
  tag_ev.scale_x = 32
  tag_ev.scale_y = 16
  tag_ev.scale_z = 16
  dzr.save_changes()
  
  # Add a TagEv (event trigger region) on the other side of the second door blocked by a boulder.
  boulder_destroyed_switch_index = 6
  dzr = self.get_arc("files/res/Stage/M_NewD2/Room14.arc").get_file("room.dzr")
  tag_ev = dzr.add_entity("SCOB", layer=None)
  tag_ev.name = "TagEv"
  tag_ev.params = 0x00FF00FF
  tag_ev.event_trigger_seen_switch_index = boulder_destroyed_switch_index
  tag_ev.event_trigger_evnt_index = dummy_evnt_index
  tag_ev.x_pos = -4002
  tag_ev.y_pos = 1950
  tag_ev.z_pos = -2156
  tag_ev.auxilary_param = 0
  tag_ev.y_rot = 0xA000
  tag_ev.auxilary_param_2 = 0xFFFF
  tag_ev.scale_x = 32
  tag_ev.scale_y = 16
  tag_ev.scale_z = 16
  dzr.save_changes()

def update_tingle_statue_item_get_funcs(self):
  dol_data = self.get_raw_file("sys/main.dol")
  item_get_funcs_list = address_to_offset(0x803888C8)
  
  for tingle_statue_item_id in [0xA3, 0xA4, 0xA5, 0xA6, 0xA7]:
    item_get_func_offset = item_get_funcs_list + tingle_statue_item_id*4
    item_name = self.item_names[tingle_statue_item_id]
    custom_symbol_name = item_name.lower().replace(" ", "_") + "_item_get_func"
    write_u32(dol_data, item_get_func_offset, self.custom_symbols[custom_symbol_name])

def make_tingle_statue_reward_rupee_rainbow_colored(self):
  # Change the color index of the special 500 rupee to be 7 - this is a special value (originally unused) we use to indicate to our custom code that it's the special rupee, and so it should have its color animated.
  
  item_resources_list_start = address_to_offset(0x803842B0)
  dol_data = self.get_raw_file("sys/main.dol")
  
  item_id = self.item_name_to_id["Rainbow Rupee"]
  rainbow_rupee_item_resource_offset = item_resources_list_start + item_id*0x24
  
  write_u8(dol_data, rainbow_rupee_item_resource_offset+0x14, 7)

def show_seed_hash_on_name_entry_screen(self):
  # Add some text to the name entry screen which has two random character names that vary based on the permalink (so the seed and settings both change it).
  # This is so two players intending to play the same seed can verify if they really are on the same seed or not.
  
  if not self.permalink:
    return
  
  integer_seed = self.convert_string_to_integer_md5(self.permalink)
  temp_rng = Random()
  temp_rng.seed(integer_seed)
  
  with open(os.path.join(SEEDGEN_PATH, "names.txt")) as f:
    all_names = f.read().splitlines()
  valid_names = [name for name in all_names if len(name) <= 5]
  
  name_1, name_2 = temp_rng.sample(valid_names, 2)
  name_1 = name_1.capitalize()
  name_2 = name_2.capitalize()
  
  # Since actually adding new text to the UI would be very difficult, instead hijack the "Name Entry" text, and put the seed hash after several linebreaks.
  # (The three linebreaks we insert before "Name Entry" are so it's still in the correct spot after vertical centering happens.)
  msg = self.bmg.messages_by_id[40]
  msg.string = "\n\n\n" + msg.string + "\n\n" + "Seed hash:" + "\n" + name_1 + " " + name_2

def fix_ghost_ship_chest_crash(self):
  # There's a vanilla crash that happens if you jump attack on top of the chest in the Ghost Ship.
  # The cause of the crash is that there are unused rooms in the Ghost Ship stage with unused chests at the same position as the used chest.
  # When Link lands on top of the overlapping chests the game thinks Link is in one of the unused rooms.
  # The ky_tag0 object in the Ghost Ship checks a zone bit every frame, but checking a zone bit crashes if the current room is not loaded in because the zone was never initialized.
  # So we simply move the other two unused chests away from the real one so they're far out of bounds.
  # (Actually deleting them would mess up the entity indexes in the logic files, so it's simpler to move them.)
  
  dzs = self.get_arc("files/res/Stage/PShip/Stage.arc").get_file("stage.dzs")
  chests = dzs.entries_by_type("TRES")
  for chest in chests:
    if chest.room_num == 2:
      # The chest for room 2 is the one that is actually used, so don't move this one.
      continue
    chest.x_pos += 2000.0
    chest.save_changes()

def implement_key_bag(self):
  # Replaces the Pirate's Charm description with a description that changes dynamically depending on the dungeon keys you have.
  # To do this new text commands are implemented to show the dynamic numbers. There are 5 new commands, 0x4B to 0x4F, one for each dungeon. (Forsaken Fortress and Ganon's Tower are not included as they have no keys.)
  
  self.bmg.messages_by_id[403].string = "Key Bag"
  str = "A handy bag for holding your keys!\n"
  str += "Here's how many you've got with you:\n"
  str += "DRC: \\{1A 05 00 00 4B}    "
  str += "FW: \\{1A 05 00 00 4C}    "
  str += "TotG: \\{1A 05 00 00 4D}\n"
  str += "ET: \\{1A 05 00 00 4E}      "
  str += "WT: \\{1A 05 00 00 4F}"
  self.bmg.messages_by_id[603].string = str
  
  itemicons_arc = self.get_arc("files/res/Msg/itemicon.arc")
  pirate_charm_icon = itemicons_arc.get_file("amulet_00.bti")
  key_bag_icon_image_path = os.path.join(ASSETS_PATH, "key bag.png")
  pirate_charm_icon.replace_image_from_path(key_bag_icon_image_path)
  pirate_charm_icon.save_changes()

DUNGEON_NAME_TO_SEA_CHART_QUEST_MARKER_INDEX = OrderedDict([
  ("Dragon Roost Cavern", 7),
  ("Forbidden Woods", 5),
  ("Tower of the Gods", 3), # Originally Southern Triangle Island
  ("Forsaken Fortress", 2), # Originally Eastern Triangle Island
  ("Earth Temple", 0),
  ("Wind Temple", 1),
])
# Note: 4 is Northern Triangle Island and 6 is Greatfish Isle, these are not used by the randomizer.

def show_quest_markers_on_sea_chart_for_dungeons(self, dungeon_names=[]):
  # Uses the blue quest markers on the sea chart to highlight certain dungeons.
  # This is done by toggling visibility on them and moving some Triangle Island ones around to repurpose them as dungeon ones.
  # When the dungeon entrance rando is on, different entrances can lead into dungeons, so the positions of the markers are updated to point to the appropriate island in that case (including secret cave entrances).
  
  sea_chart_ui = self.get_arc("files/res/Msg/fmapres.arc").get_file_entry("f_map.blo")
  sea_chart_ui.decompress_data_if_necessary()
  first_quest_marker_pic1_offset = 0x43B0
  
  for dungeon_name in dungeon_names:
    quest_marker_index = DUNGEON_NAME_TO_SEA_CHART_QUEST_MARKER_INDEX[dungeon_name]
    
    offset = first_quest_marker_pic1_offset + quest_marker_index*0x40
    
    # Make the quest marker icon be visible.
    write_u8(sea_chart_ui.data, offset+9, 1)
    
    if dungeon_name == "Forsaken Fortress":
      island_name = "Forsaken Fortress"
    else:
      island_name = self.dungeon_and_cave_island_locations[dungeon_name]
    island_number = self.island_name_to_number[island_name]
    sector_x = (island_number-1) % 7
    sector_y = (island_number-1) // 7
    
    write_s16(sea_chart_ui.data, offset+0x10, sector_x*0x37-0xFA)
    write_s16(sea_chart_ui.data, offset+0x12, sector_y*0x38-0xBC)

def disable_ice_ring_isle_and_fire_mountain_effects_indoors(self):
  # Ice Ring Isle and Fire Mountain both have an entity inside of them that kills the player if the timer is inactive or reaches 0.
  # This is an issue in secret cave entrance rando since entering these from any entrance that doesn't start the timer would cause the player to die instantly.
  # To avoid this, the entity is removed from inside both of these caves.
  # That same entity is also responsible for setting the event flags to permanently deactivate Ice Ring Isle and Fire Mountain when the chest inside is opened, so removing it is also useful to prevent sequence breaking (e.g. enter Ice Ring cave from wrong entrance, open chest, now go to Ice Ring Isle and you don't need fire arrows to reach that entrance).
  
  # Remove the entity from Ice Ring Isle.
  iri_dzx = self.get_arc("files/res/Stage/MiniHyo/Room0.arc").get_file("room.dzr")
  actors = iri_dzx.entries_by_type_and_layer("ACTR", None)
  kill_trigger = next(x for x in actors if x.name == "VolTag")
  iri_dzx.remove_entity(kill_trigger, "ACTR", layer=None)
  iri_dzx.save_changes()
  
  # Remove the entity from Fire Mountain.
  fm_dzx = self.get_arc("files/res/Stage/MiniKaz/Room0.arc").get_file("room.dzr")
  actors = fm_dzx.entries_by_type_and_layer("ACTR", None)
  kill_trigger = next(x for x in actors if x.name == "VolTag")
  fm_dzx.remove_entity(kill_trigger, "ACTR", layer=None)
  fm_dzx.save_changes()

def prevent_fire_mountain_lava_softlock(self):
  # Sometimes when spawning from spawn ID 0 outside fire mountain, the player will get stuck in an infinite loop of taking damage from lava.
  # The reason for this is that when the player enters the sea stage, the ship is spawned in at its new game starting position (either Outset or a randomized starting island) and the player is put on the ship.
  # Then after a frame or two the ship is teleported to its proper spawn position near the island the player is supposed to be on, along with the player.
  # The game's collision detection system draws a huge line between where the player was a frame ago (starting island) and where the player is right now (whatever the correct island is, such as Fire Mountain).
  # If that collision line happens to pass through the Fire Mountain volcano, the player will be considered to be standing on the volcano for one frame.
  # Because the volcano's collision is set to have the lava attribute, this results in the player taking lava damage.
  # In order to avoid this, the Y coordinate of the ship's position when starting a new game is simply moved down to be extremely far below the ocean surface. This is so that any collision line in between it and any of the various other ship spawns will not hit anything at all.
  # This does not result in the ship actually visibly spawning far below the sea when you start a new game, because the sea actor is smart enough to instantly teleport the ship on top whenever it falls below the surface.
  
  sea_dzs = self.get_arc("files/res/Stage/sea/Stage.arc").get_file("stage.dzs")
  sea_actors = sea_dzs.entries_by_type("ACTR")
  ship_actor = next(x for x in sea_actors if x.name == "Ship")
  ship_actor.y_pos = -500000
  ship_actor.save_changes()

def add_chest_in_place_of_jabun_cutscene(self):
  # Add a chest on a raft to Jabun's cave to replace the cutscene item you would normally get there.
  
  jabun_dzr = self.get_arc("files/res/Stage/Pjavdou/Room0.arc").get_file("room.dzr")
  
  raft = jabun_dzr.add_entity("ACTR", layer=None)
  raft.name = "Ikada"
  raft.y_rot = 0x8000
  
  # Turn wind on inside the cave so that the flag on the raft blows in the wind.
  # Otherwise it clips inside the flagpole and looks bad.
  room_props = jabun_dzr.entries_by_type("FILI")[0]
  room_props.wind_type = 0 # Weakest wind (0.3 strength)
  
  jabun_chest = jabun_dzr.add_entity("TRES", layer=None)
  jabun_chest.name = "takara3"
  jabun_chest.params = 0xFF000000
  jabun_chest.chest_type = 2
  jabun_chest.appear_condition_switch = 0xFF
  jabun_chest.opened_flag = 6
  jabun_chest.behavior_type = 5 # Necessary for the chest to bob up and down with the raft it's on
  jabun_chest.x_pos = 0
  jabun_chest.y_pos = 300
  jabun_chest.z_pos = -200
  jabun_chest.room_num = 0
  jabun_chest.y_rot = 0x8000
  jabun_chest.item_id = self.item_name_to_id["Nayru's Pearl"]
  
  jabun_dzr.save_changes()
  
  
  # Also move the big stone door and whirlpool blocking Jabun's cave entrance from layer 5 to the default layer.
  # This is so they appear during the day too, not just at night.
  outset_dzr = self.get_arc("files/res/Stage/sea/Room44.arc").get_file("room.dzr")
  
  layer_5_actors = outset_dzr.entries_by_type_and_layer("ACTR", 5)
  layer_5_door = next(x for x in layer_5_actors if x.name == "Ajav")
  layer_5_whirlpool = next(x for x in layer_5_actors if x.name == "Auzu")
  
  layer_none_door = outset_dzr.add_entity("ACTR", layer=None)
  layer_none_door.name = layer_5_door.name
  layer_none_door.params = layer_5_door.params
  layer_none_door.x_pos = layer_5_door.x_pos
  layer_none_door.y_pos = layer_5_door.y_pos
  layer_none_door.z_pos = layer_5_door.z_pos
  layer_none_door.auxilary_param = layer_5_door.auxilary_param
  layer_none_door.y_rot = layer_5_door.y_rot
  layer_none_door.auxilary_param_2 = layer_5_door.auxilary_param_2
  layer_none_door.enemy_number = layer_5_door.enemy_number
  
  layer_none_whirlpool = outset_dzr.add_entity("ACTR", layer=None)
  layer_none_whirlpool.name = layer_5_whirlpool.name
  layer_none_whirlpool.params = layer_5_whirlpool.params
  layer_none_whirlpool.x_pos = layer_5_whirlpool.x_pos
  layer_none_whirlpool.y_pos = layer_5_whirlpool.y_pos
  layer_none_whirlpool.z_pos = layer_5_whirlpool.z_pos
  layer_none_whirlpool.auxilary_param = layer_5_whirlpool.auxilary_param
  layer_none_whirlpool.y_rot = layer_5_whirlpool.y_rot
  layer_none_whirlpool.auxilary_param_2 = layer_5_whirlpool.auxilary_param_2
  layer_none_whirlpool.enemy_number = layer_5_whirlpool.enemy_number
  
  outset_dzr.remove_entity(layer_5_door, "ACTR", layer=5)
  outset_dzr.remove_entity(layer_5_whirlpool, "ACTR", layer=5)
  
  outset_dzr.save_changes()
  
  
  # Also modify the event that happens when you destroy the big stone door so that KoRL doesn't automatically enter the cave.
  event_list = self.get_arc("files/res/Stage/sea/Stage.arc").get_file("event_list.dat")
  unlock_cave_event = event_list.events_by_name["ajav_uzu"]
  director = next(actor for actor in unlock_cave_event.actors if actor.name == "DIRECTOR")
  camera = next(actor for actor in unlock_cave_event.actors if actor.name == "CAMERA")
  ship = next(actor for actor in unlock_cave_event.actors if actor.name == "Ship")
  
  director.actions = director.actions[0:1]
  camera.actions = camera.actions[0:2]
  ship.actions = ship.actions[0:2]
  unlock_cave_event.ending_flags = [
    director.actions[-1].flag_id_to_set,
    camera.actions[-1].flag_id_to_set,
    -1
  ]

def add_chest_in_place_of_master_sword(self):
  # Add a chest to the Master Sword chamber that only materializes after you beat the Mighty Darknuts there.
  
  ms_chamber_dzr = self.get_arc("files/res/Stage/kenroom/Room0.arc").get_file("room.dzr")
  
  # Remove the Master Sword entities.
  ms_actors = [x for x in ms_chamber_dzr.entries_by_type_and_layer("ACTR", None) if x.name in ["VmsMS", "VmsDZ"]]
  for actor in ms_actors:
    ms_chamber_dzr.remove_entity(actor, "ACTR", layer=None)
  
  # Copy the entities necessary for the Mighty Darknuts fight from layer 5 to the default layer.
  layer_5_actors = ms_chamber_dzr.entries_by_type_and_layer("ACTR", 5)
  layer_5_actors_to_copy = [x for x in layer_5_actors if x.name in ["Tn", "ALLdie", "Yswdr00"]]
  
  for orig_actor in layer_5_actors_to_copy:
    new_actor = ms_chamber_dzr.add_entity("ACTR", layer=None)
    new_actor.name = orig_actor.name
    new_actor.params = orig_actor.params
    new_actor.x_pos = orig_actor.x_pos
    new_actor.y_pos = orig_actor.y_pos
    new_actor.z_pos = orig_actor.z_pos
    new_actor.auxilary_param = orig_actor.auxilary_param
    new_actor.y_rot = orig_actor.y_rot
    new_actor.auxilary_param_2 = orig_actor.auxilary_param_2
    new_actor.enemy_number = orig_actor.enemy_number
  
  # Remove the entities on layer 5 that are no longer necessary.
  for orig_actor in layer_5_actors:
    ms_chamber_dzr.remove_entity(orig_actor, "ACTR", layer=5)
  
  
  # Add the chest.
  ms_chest = ms_chamber_dzr.add_entity("TRES", layer=None)
  ms_chest.name = "takara3"
  ms_chest.params = 0xFF000000
  ms_chest.chest_type = 2
  ms_chest.appear_condition_switch = 5 # The Mighty Darknuts set switch 5 when they die.
  ms_chest.opened_flag = 0
  ms_chest.behavior_type = 4
  ms_chest.x_pos = -123.495
  ms_chest.y_pos = -3220
  ms_chest.z_pos = -7787.13 - 50
  ms_chest.room_num = 0
  ms_chest.y_rot = 0x0000
  ms_chest.item_id = self.item_name_to_id["Progressive Sword"]
  
  
  # Normally if the player saves and reloads or dies and respawns in this fight, they'll be put right back into it.
  # But that would be bad in swordless mode since the player might not have anything to kill the Darknuts with and be stuck forever.
  # So the spawn is moved back away from the fight's trigger area so that the player isn't forced back into the fight immediately.
  spawn = next(spawn for spawn in ms_chamber_dzr.entries_by_type("PLYR") if spawn.spawn_id == 10)
  spawn.y_pos = -2949.39
  spawn.z_pos = -4240.7
  
  ms_chamber_dzr.save_changes()

def update_beedle_spoil_selling_text(self):
  # Update Beedle's dialogue when you try to sell something to him so he mentions he doesn't want Blue Chu Jelly.
  msg = self.bmg.messages_by_id[3957]
  lines = msg.string.split("\n")
  lines[2] = "And no Blue Chu Jelly, either!"
  msg.string = "\n".join(lines)

def fix_totg_warp_out_spawn_pos(self):
  # Normally the spawn point used when the player teleports out after beating the dungeon boss would put the player right on top of the Hyrule warp, which takes the player there immediately if it's active.
  # Move the spawn forward a bit to avoid to avoid this.
  
  dzr = self.get_arc("files/res/Stage/sea/Room26.arc").get_file("room.dzr")
  spawn = next(x for x in dzr.entries_by_type("PLYR") if x.spawn_id == 1)
  spawn.z_pos += 1000.0
  spawn.save_changes()

def remove_phantom_ganon_requirement_from_eye_reefs(self):
  # Go through all the eye reef cannons that don't appear until you defeat Phantom Ganon and remove that switch requirement.
  
  for island_number in [24, 46, 22, 8, 37, 25]:
    eye_reef_dzr = self.get_arc("files/res/Stage/sea/Room%d.arc" % island_number).get_file("room.dzr")
    actors = eye_reef_dzr.entries_by_type("ACTR")
    cannons = [x for x in actors if x.name == "Ocanon"]
    for cannon in cannons:
      if cannon.cannon_appear_condition_switch == 0x2A: # Switch 2A is Phantom Ganon being dead.
        cannon.cannon_appear_condition_switch = 0xFF
        cannon.save_changes()
    gunboats = [x for x in actors if x.name == "Oship"]
    for gunboat in gunboats:
      if (gunboat.auxilary_param & 0xFF) == 0x2A: # Switch 2A is Phantom Ganon being dead.
        gunboat.auxilary_param = (gunboat.auxilary_param & 0xFF00) | 0xFF
        gunboat.save_changes()

def test_room(self):
  apply_patch(self, "test_room")
  
  dol_data = self.get_raw_file("sys/main.dol")
  
  stage_name_ptr = self.custom_symbols["test_room_stage_name"]
  room_index_ptr = self.custom_symbols["test_room_room_index"]
  spawn_id_ptr = self.custom_symbols["test_room_spawn_id"]
  
  write_str(dol_data, address_to_offset(stage_name_ptr), self.test_room_args["stage"], 8)
  write_u8(dol_data, address_to_offset(room_index_ptr), self.test_room_args["room"])
  write_u8(dol_data, address_to_offset(spawn_id_ptr), self.test_room_args["spawn"])
