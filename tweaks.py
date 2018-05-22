
import re
import yaml
import os

from fs_helpers import *

ORIGINAL_FREE_SPACE_RAM_ADDRESS = 0x803FCFA8
ORIGINAL_DOL_SIZE = 0x3A52C0

# These are from main.dol. Hardcoded since it's easier than reading them from the dol.
TEXT1_SECTION_OFFSET = 0x2620
TEXT1_SECTION_ADDRESS = 0x800056E0
TEXT1_SECTION_SIZE = 0x332FA0
DATA5_SECTION_OFFSET = 0x36E580
DATA5_SECTION_ADDRESS = 0x80371580
DATA5_SECTION_SIZE = 0x313E0

def address_to_offset(address):
  # Takes an address in one of the sections of main.dol and converts it to an offset within main.dol.
  # (Currently only supports the .text1 and .data5 sections.)
  if TEXT1_SECTION_ADDRESS <= address < TEXT1_SECTION_ADDRESS+TEXT1_SECTION_SIZE:
    offset = address - TEXT1_SECTION_ADDRESS + TEXT1_SECTION_OFFSET
  elif DATA5_SECTION_ADDRESS <= address < DATA5_SECTION_ADDRESS+DATA5_SECTION_SIZE:
    offset = address - DATA5_SECTION_ADDRESS + DATA5_SECTION_OFFSET
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
  try:
    from sys import _MEIPASS
    asm_path = os.path.join(_MEIPASS, "asm")
  except ImportError:
    asm_path = "asm"
  
  with open(os.path.join(asm_path, patch_name + "_diff.txt")) as f:
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

def set_new_game_starting_spawn_id(self, spawn_id):
  dol_data = self.get_raw_file("sys/main.dol")
  write_u8(dol_data, address_to_offset(0x80058BAF), spawn_id)

def set_new_game_starting_room_index(self, room_index):
  dol_data = self.get_raw_file("sys/main.dol")
  write_u8(dol_data, address_to_offset(0x80058BA7), room_index)

def change_ship_starting_island(self, starting_island_room_index):
  island_dzx = self.get_arc("files/res/Stage/sea/Room%d.arc" % starting_island_room_index).dzx_files[0]
  ship_spawns = island_dzx.entries_by_type("SHIP")
  island_ship_spawn_0 = next(x for x in ship_spawns if x.ship_id == 0)
  
  sea_dzx = self.get_arc("files/res/Stage/sea/Stage.arc").dzx_files[0]
  sea_actors = sea_dzx.entries_by_type("ACTR")
  ship_actor = next(x for x in sea_actors if x.name == "Ship")
  ship_actor.x_pos = island_ship_spawn_0.x_pos
  ship_actor.y_pos = island_ship_spawn_0.y_pos
  ship_actor.z_pos = island_ship_spawn_0.z_pos
  ship_actor.x_rot = 0
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
  bmg = self.get_arc("files/res/Msg/bmgres.arc").bmg_files[0]
  for msg in bmg.messages:
    msg.initial_draw_type = 1 # Instant draw
    msg.save_changes()

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
  
  item_resources_list_start = address_to_offset(0x803842B0)
  field_item_resources_list_start = address_to_offset(0x803866B0)
  itemGetExecute_switch_statement_entries_list_start = address_to_offset(0x8038CA6C)
  
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
  extra_item_data_list_start = address_to_offset(0x803882B0)
  for item_id in range(0, 0xFF+1):
    item_extra_data_entry_offset = extra_item_data_list_start+4*item_id
    original_y_offset = read_u8(dol_data, item_extra_data_entry_offset+1)
    if original_y_offset == 0:
      write_u8(dol_data, item_extra_data_entry_offset+1, 0x28) # Y offset of 0x28

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
  
  
  # Also update the item get descriptions of progressive items to just generically say you got *a* upgrade, without saying which.
  sword_id = self.item_name_to_id["Progressive Sword"]
  sword_msg = self.bmg.messages_by_id[101 + sword_id]
  sword_msg.string = "\{1A 05 00 00 01}You got a \{1A 06 FF 00 00 01}sword upgrade\{1A 06 FF 00 00 00}!"
  sword_msg.save_changes()
  
  bow_id = self.item_name_to_id["Progressive Bow"]
  bow_msg = self.bmg.messages_by_id[101 + bow_id]
  bow_msg.string = "\{1A 05 00 00 01}You got a \{1A 06 FF 00 00 01}bow upgrade\{1A 06 FF 00 00 00}!"
  bow_msg.save_changes()
  
  wallet_id = self.item_name_to_id["Progressive Wallet"]
  wallet_msg = self.bmg.messages_by_id[101 + wallet_id]
  wallet_msg.string = "\{1A 05 00 00 01}You can now carry more \{1A 06 FF 00 00 01}Rupees\{1A 06 FF 00 00 00}!"
  wallet_msg.save_changes()
  
  bomb_bag_id = self.item_name_to_id["Progressive Bomb Bag"]
  bomb_bag_msg = self.bmg.messages_by_id[101 + bomb_bag_id]
  bomb_bag_msg.string = "\{1A 05 00 00 01}You can now carry more \{1A 06 FF 00 00 01}bombs\{1A 06 FF 00 00 00}!"
  bomb_bag_msg.save_changes()
  
  quiver_id = self.item_name_to_id["Progressive Quiver"]
  quiver_msg = self.bmg.messages_by_id[101 + quiver_id]
  quiver_msg.string = "\{1A 05 00 00 01}You can now carry more \{1A 06 FF 00 00 01}arrows\{1A 06 FF 00 00 00}!"
  quiver_msg.save_changes()
  
  picto_box_id = self.item_name_to_id["Progressive Picto Box"]
  picto_box_msg = self.bmg.messages_by_id[101 + picto_box_id]
  picto_box_msg.string = "\{1A 05 00 00 01}You got a \{1A 06 FF 00 00 01}Picto Box upgrade\{1A 06 FF 00 00 00}!"
  picto_box_msg.save_changes()

def make_sail_behave_like_swift_sail(self):
  # Causes the wind direction to always change to face the direction KoRL is facing as long as the sail is out.
  # Also doubles KoRL's speed.
  
  ship_data = self.get_raw_file("files/rels/d_a_ship.rel")
  # Change the relocation for line B9FC, which originally called setShipSailState.
  write_u32(ship_data, 0x11C94, self.custom_symbols["set_wind_dir_to_ship_dir"])
  
  write_float(ship_data, 0xDBE8, 55.0*2) # Sailing speed
  write_float(ship_data, 0xDBC0, 80.0*2) # Initial speed

def add_ganons_tower_warp_to_ff2(self):
  # Normally the warp object from Forsaken Fortress down to Ganon's Tower only appears in FF3.
  # But we changed Forsaken Fortress to remain permanently as FF2.
  # So we need to add the warp object to FF2 as well so the player can conveniently go between the sea and Ganon's Tower.
  # To do this we copy the warp entity from layer 2 onto layer 1.
  
  dzx = self.get_arc("files/res/Stage/sea/Room1.arc").dzx_files[0]
  
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
  layer_1_warp.x_rot = layer_2_warp.x_rot
  layer_1_warp.y_rot = layer_2_warp.y_rot
  layer_1_warp.set_flag = layer_2_warp.set_flag
  layer_1_warp.enemy_number = layer_2_warp.enemy_number
  
  dzx.save_changes()

def add_chest_in_place_medli_grappling_hook_gift(self):
  # Add a chest in place of Medli locked in the jail cell at the peak of Dragon Roost Cavern.
  
  dzx = self.get_arc("files/res/Stage/M_Dra09/Stage.arc").dzx_files[0]
  
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
  chest_in_jail.flag_id = 0xFF
  chest_in_jail.padding = 0xFFFF
  
  dzx.save_changes()

def add_chest_in_place_queen_fairy_cutscene(self):
  # Add a chest in place of the Queen Fairy cutscene inside Mother Isle.
  
  dzx = self.get_arc("files/res/Stage/sea/Room9.arc").dzx_files[0]
  
  chests = dzx.entries_by_type("TRES")
  if any(x for x in chests if x.opened_flag == 0x1C):
    return # This tweak was already applied, don't double up the chest
  
  mother_island_chest = dzx.add_entity("TRES", layer=None)
  mother_island_chest.name = "takara3"
  mother_island_chest.params = 0xFF000000 # Unknown param, probably unused
  mother_island_chest.chest_type = 2
  mother_island_chest.opened_flag = 0x1C
  mother_island_chest.x_pos = -180031
  mother_island_chest.y_pos = 740
  mother_island_chest.z_pos = -199995
  mother_island_chest.room_num = 9
  mother_island_chest.y_rot = 0x1000
  mother_island_chest.item_id = self.item_name_to_id["Progressive Bow"]
  mother_island_chest.flag_id = 0xFF
  mother_island_chest.padding = 0xFFFF
  
  dzx.save_changes()
