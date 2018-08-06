
import re
import yaml
import os
from io import BytesIO
from collections import namedtuple
import copy
from random import Random

from fs_helpers import *
from wwlib import texture_utils
from wwlib.rarc import RARC
from paths import ASSETS_PATH, ASM_PATH
import customizer

ORIGINAL_FREE_SPACE_RAM_ADDRESS = 0x803FCFA8
ORIGINAL_DOL_SIZE = 0x3A52C0

# These are from main.dol. Hardcoded since it's easier than reading them from the dol.
TEXT0_SECTION_OFFSET = 0x100
TEXT0_SECTION_ADDRESS = 0x80003100
TEXT0_SECTION_SIZE = 0x2520
TEXT1_SECTION_OFFSET = 0x2620
TEXT1_SECTION_ADDRESS = 0x800056E0
TEXT1_SECTION_SIZE = 0x332FA0
TEXT2_SECTION_OFFSET = ORIGINAL_DOL_SIZE
TEXT2_SECTION_ADDRESS = ORIGINAL_FREE_SPACE_RAM_ADDRESS
TEXT2_SECTION_SIZE = -1

DATA4_SECTION_OFFSET = 0x335840
DATA4_SECTION_ADDRESS = 0x80338840
DATA4_SECTION_SIZE = 0x38D40
DATA5_SECTION_OFFSET = 0x36E580
DATA5_SECTION_ADDRESS = 0x80371580
DATA5_SECTION_SIZE = 0x313E0
DATA7_SECTION_OFFSET = 0x3A00A0
DATA7_SECTION_ADDRESS = 0x803F7D00
DATA7_SECTION_SIZE = 0x5220

def address_to_offset(address):
  # Takes an address in one of the sections of main.dol and converts it to an offset within main.dol.
  # (Currently only supports the .text0, .text1, .text2, .data4, and .data5 sections.)
  if TEXT0_SECTION_ADDRESS <= address < TEXT0_SECTION_ADDRESS+TEXT0_SECTION_SIZE:
    offset = address - TEXT0_SECTION_ADDRESS + TEXT0_SECTION_OFFSET
  elif TEXT1_SECTION_ADDRESS <= address < TEXT1_SECTION_ADDRESS+TEXT1_SECTION_SIZE:
    offset = address - TEXT1_SECTION_ADDRESS + TEXT1_SECTION_OFFSET
  elif DATA4_SECTION_ADDRESS <= address < DATA4_SECTION_ADDRESS+DATA4_SECTION_SIZE:
    offset = address - DATA4_SECTION_ADDRESS + DATA4_SECTION_OFFSET
  elif DATA5_SECTION_ADDRESS <= address < DATA5_SECTION_ADDRESS+DATA5_SECTION_SIZE:
    offset = address - DATA5_SECTION_ADDRESS + DATA5_SECTION_OFFSET
  elif DATA7_SECTION_ADDRESS <= address < DATA7_SECTION_ADDRESS+DATA7_SECTION_SIZE:
    offset = address - DATA7_SECTION_ADDRESS + DATA7_SECTION_OFFSET
  elif TEXT2_SECTION_ADDRESS <= address <= TEXT2_SECTION_ADDRESS+TEXT2_SECTION_SIZE:
    # Newly added .text2 section.
    offset = address - TEXT2_SECTION_ADDRESS + TEXT2_SECTION_OFFSET
  else:
    raise Exception("Unknown address: %08X" % address)
  return offset

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
    diffs = yaml.load(f)
  
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
  
  # Update the constant for how large the .text section is so that addresses in this section can be converted properly by address_to_offset.
  global TEXT2_SECTION_SIZE
  TEXT2_SECTION_SIZE = patch_length
  
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
  for address in [0x800C1970, 0x800C1978, 0x800C1980, 0x800C1988, 0x800C1990, 0x800C1998]:
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
  # Originally it used image format 0xE, which is lossy DXT1 compression.
  # But implementing this while having the texture actually look good is too difficult, so instead switch this to image format 9 and palette format 1 (C8 with a 255 color RGB565 palette).
  sail_itemget_tex_image.image_format = 9
  sail_itemget_tex_image.palette_format = 1
  sail_itemget_tex_image.replace_image_from_path(new_sail_itemget_tex_image_path)
  sail_itemget_model.save_changes()

def add_ganons_tower_warp_to_ff2(self):
  # Normally the warp object from Forsaken Fortress down to Ganon's Tower only appears in FF3.
  # But we changed Forsaken Fortress to remain permanently as FF2.
  # So we need to add the warp object to FF2 as well so the player can conveniently go between the sea and Ganon's Tower.
  # To do this we copy the warp entity from layer 2 onto layer 1.
  
  dzx = self.get_arc("files/res/Stage/sea/Room1.arc").get_file("room.dzr")
  
  layer_1_actors = dzx.entries_by_type_and_layer("ACTR", 1)
  if any(x for x in layer_1_actors if x.name == "Warpmj"):
    return # This tweak was already applied, don't double up the warp
  
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
  
  chests = dzx.entries_by_type("TRES")
  if any(x for x in chests if x.opened_flag == 0x11):
    return # This tweak was already applied, don't double up the chest
  
  chest_in_jail = dzx.add_entity("TRES", layer=None)
  chest_in_jail.name = "takara3"
  chest_in_jail.params = 0xFF000000 # Unknown param, probably unused
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
  
  chests = dzx.entries_by_type("TRES")
  if any(x for x in chests if x.opened_flag == 0x1C):
    return # This tweak was already applied, don't double up the chest
  
  mother_island_chest = dzx.add_entity("TRES", layer=None)
  mother_island_chest.name = "takara3"
  mother_island_chest.params = 0xFF000000 # Unknown param, probably unused
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

def add_more_magic_jars_to_dungeons(self):
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
  
  new_game_id = "GZLR01"
  boot_data = self.get_raw_file("sys/boot.bin")
  write_str(boot_data, 0, new_game_id, 6)
  
  dol_data = self.get_raw_file("sys/main.dol")
  new_memory_card_game_name = "Wind Waker Randomizer"
  write_str(dol_data, address_to_offset(0x80339690), new_memory_card_game_name, 21)
  
  new_image_file_path = os.path.join(ASSETS_PATH, "banner.png")
  image_format = 5
  palette_format = 2
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
      description_format_string = "\\{1A 05 00 00 01}You got a \\{1A 06 FF 00 00 01}%s small key\\{1A 06 FF 00 00 00}!"
    elif base_item_name == "Big Key":
      description_format_string = "\\{1A 05 00 00 01}You got the \\{1A 06 FF 00 00 01}%s Big Key\\{1A 06 FF 00 00 00}!"
    elif base_item_name == "Dungeon Map":
      description_format_string = "\\{1A 05 00 00 01}You got the \\{1A 06 FF 00 00 01}%s Dungeon Map\\{1A 06 FF 00 00 00}!"
    elif base_item_name == "Compass":
      description_format_string = "\\{1A 05 00 00 01}You got the \\{1A 06 FF 00 00 01}%s Compass\\{1A 06 FF 00 00 00}!"
    
    msg = self.bmg.add_new_message(101 + item_id)
    msg.string = word_wrap_string(description_format_string % dungeon_name)
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
  item_name = self.logic.done_item_locations["The Great Sea - Beedle's Shop Ship - Bait Bag"]
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

def update_sinking_ships_item_names(self):
  item_name = self.logic.done_item_locations["Windfall Island - Sinking Ships - First Prize"]
  msg = self.bmg.messages_by_id[7520]
  msg.string = "\\{1A 05 01 00 8E}Hoorayyy! Yayyy! Yayyy!\nOh, thank you, Mr. Sailor!\n\n\n"
  msg.string += word_wrap_string(
    "Please take this \\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 00} as a sign of our gratitude. You are soooooo GREAT!" % item_name,
    max_line_length=43
  )
  
  item_name = self.logic.done_item_locations["Windfall Island - Sinking Ships - Second Prize"]
  msg = self.bmg.messages_by_id[7521]
  msg.string = "\\{1A 05 01 00 8E}Hoorayyy! Yayyy! Yayyy!\nOh, thank you so much, Mr. Sailor!\n\n\n"
  msg.string += word_wrap_string(
    "This is our thanks to you! It's been passed down on our island for many years, so don't tell the island elder, OK? Here...\\{1A 06 FF 00 00 01}\\{1A 05 00 00 39} \\{1A 06 FF 00 00 00}Please accept this \\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 00}!" % item_name,
    max_line_length=43
  )
  
  # The high score one doesn't say the item name in text anywhere, so no need to update it.
  #item_name = self.logic.done_item_locations["Windfall Island - Sinking Ships - 20 Shots or Less Prize"]
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

def update_fishmen_hints(self):
  hints = []
  unique_items_given_hint_for = []
  possible_item_locations = list(self.logic.done_item_locations.keys())
  self.rng.shuffle(possible_item_locations)
  for location_name in possible_item_locations:
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
    if len(hints) >= 3:
      # 3 hints max per seed.
      break
    
    zone_name, specific_location_name = self.logic.split_location_name_by_zone(location_name)
    if zone_name in self.dungeon_island_locations and location_name != "Tower of the Gods - Sunken Treasure":
      # If the location is in a dungeon, use the hint for whatever island the dungeon is located on.
      island_name = self.dungeon_island_locations[zone_name]
      island_hint_name = self.island_name_hints[island_name]
    if zone_name in self.island_name_hints:
      island_hint_name = self.island_name_hints[zone_name]
    elif zone_name in self.logic.DUNGEON_NAMES.values():
      continue
    else:
      continue
    
    item_hint_name = self.progress_item_hints[item_name]
    
    hint_lines = []
    hint_lines.append(
      "I've heard from my sources that \\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 00} is located in \\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 00}." % (item_hint_name, island_hint_name)
    )
    hint_lines.append("Could be worth a try checking that place out. If you know where it is, of course.")
    hint = ""
    for hint_line in hint_lines:
      hint_line = word_wrap_string(hint_line)
      hint_line = pad_string_to_next_4_lines(hint_line)
      hint += hint_line
    hints.append(hint)
    
    unique_items_given_hint_for.append(item_name)
  
  for fishman_island_number in range(1, 49+1):
    hint = self.rng.choice(hints)
    
    msg_id = 13026 + fishman_island_number
    msg = self.bmg.messages_by_id[msg_id]
    msg.string = hint

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
    WarpPotData("M_NewD2", 2, 2178, 0, 488, 0x8000, 2), # DRC
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
  auction = next(actor for actor in wind_shrine_event.actors if actor.name == "Auction")
  camera = next(actor for actor in wind_shrine_event.actors if actor.name == "CAMERA")
  
  pre_pan_delay = camera.actions[2]
  pan_action = camera.actions[3]
  post_pan_delay = camera.actions[4]
  
  # Remove the 30 frame delays before and after panning.
  camera.actions.remove(pre_pan_delay)
  camera.actions.remove(post_pan_delay)
  
  # The actual panning action cannot be skipped for some unknown reason. It would appear to work but the game would crash a little bit later.
  # So instead we change the duration of the panning to be only 1 frame long so it appears to be skipped.
  pan_action.get_prop("Timer").value = 1

def disable_invisible_walls(self):
  # Remove some invisible walls to allow sequence breaking.
  # In vanilla switch index FF meant an invisible wall appears only when you have no sword.
  # But we remove that in randomizer, so invisible walls with switch index FF act effectively completely disabled. So we use this to disable these invisible walls.
  
  # Remove an invisible wall in the second room of DRC.
  dzx = self.get_arc("files/res/Stage/M_NewD2/Room2.arc").get_file("room.dzr")
  invisible_wall = next(x for x in dzx.entries_by_type("SCOB") if x.name == "Akabe")
  invisible_wall.invisible_wall_switch_index = 0xFF
  invisible_wall.save_changes()
