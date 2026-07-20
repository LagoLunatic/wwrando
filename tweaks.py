from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
  from randomizer import WWRandomizer

from gclib.bti import BTI
from gclib.j3d import BDL

import re
import os
from io import BytesIO
from dataclasses import dataclass
import copy
import math
import colorsys

from gclib import fs_helpers as fs
from asm import patcher
from gclib import texture_utils
from gclib.rel import REL
from gclib.bmg import TextBoxType
import gclib.gx_enums as GX
from wwrando_paths import ASSETS_PATH, ASM_PATH
import customizer
from logic.item_types import PROGRESS_ITEMS, NONPROGRESS_ITEMS, CONSUMABLE_ITEMS, DUPLICATABLE_CONSUMABLE_ITEMS
from data_tables import DataTables
from wwlib.events import EventList
from wwlib.dzx import DZx, DZxLayer, ACTR, EVNT, FILI, PLYR, SCLS, SCOB, SHIP, TGDR, TRES, Pale
from options.wwrando_options import SwordMode

try:
  from keys.seed_key import SEED_KEY # type: ignore
except ImportError:
  SEED_KEY = ""

ORIGINAL_FREE_SPACE_RAM_ADDRESS = 0x803FCFA8
ORIGINAL_DOL_SIZE = 0x3A52C0

# Number of slots allocated for starting items (when changing this also update the code in custom_funcs.asm)
MAXIMUM_ADDITIONAL_STARTING_ITEMS = 103


def set_new_game_starting_spawn_id(self: WWRandomizer, spawn_id: int):
  self.dol.write_data(fs.write_u8, 0x80058BAF, spawn_id)

def set_new_game_starting_room(self: WWRandomizer, room_number: int):
  self.dol.write_data(fs.write_u8, 0x80058BA7, room_number)

def change_ship_starting_island(self: WWRandomizer, room_number: int):
  island_dzx = self.get_arc(f"files/res/Stage/sea/Room{room_number}.arc").get_file("room.dzr", DZx)
  ship_spawns = island_dzx.entries_by_type(SHIP)
  island_ship_spawn_0 = next(x for x in ship_spawns if x.ship_id == 0)
  
  sea_dzx = self.get_arc("files/res/Stage/sea/Stage.arc").get_file("stage.dzs", DZx)
  sea_actors = sea_dzx.entries_by_type(ACTR)
  ship_actor = next(x for x in sea_actors if x.name == "Ship")
  ship_actor.x_pos = island_ship_spawn_0.x_pos
  ship_actor.y_pos = island_ship_spawn_0.y_pos
  ship_actor.z_pos = island_ship_spawn_0.z_pos
  ship_actor.y_rot = island_ship_spawn_0.y_rot
  ship_actor.save_changes()

def skip_wakeup_intro_and_start_at_dock(self: WWRandomizer):
  # When the player starts a new game they usually start at spawn ID 206, which plays the wakeup event and puts the player on Aryll's lookout.
  # We change the starting spawn ID to 0, which does not play the wakeup event and puts the player on the dock next to the ship.
  set_new_game_starting_spawn_id(self, 0)

def start_ship_at_outset(self: WWRandomizer):
  # Change the King of Red Lions' default position so that he appears on Outset at the start of the game.
  change_ship_starting_island(self, 44)
  
def make_all_text_instant(self: WWRandomizer):
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
  patcher.apply_patch(self, "b_button_skips_text")

def fix_deku_leaf_model(self: WWRandomizer):
  # The Deku Leaf is a unique object not used for other items. It's easy to change what item it gives you, but the visual model cannot be changed.
  # So instead we replace the unique Deku Leaf actor ("itemDek") with a more general actor that can be for any field item ("item").
  
  dzx = self.get_arc("files/res/Stage/Omori/Room0.arc").get_file("room.dzr", DZx)
  deku_leaf_actors = [actor for actor in dzx.entries_by_type(ACTR) if actor.name == "itemDek"]
  for actor in deku_leaf_actors:
    actor.name = "item"
    actor.params = 0x01FF0000 # Misc params, one of which makes the item not fade out over time
    actor.item_id = self.item_name_to_id["Deku Leaf"]
    actor.item_pickup_flag = 2 # This is the same item pickup flag that itemDek originally had in its params.
    actor.enable_activation_switch = 0xFF # Necessary for the item to be pickupable.
    actor.save_changes()

def allow_all_items_to_be_field_items(self: WWRandomizer):
  # Most items cannot be field items (items that appear freely floating on the ground) because they don't have a field model defined.
  # Here we copy the regular item get model to the field model so that any item can be a field item.
  # We also change the code run when you touch the item so that these items play out the full item get animation with text, instead of merely popping up above the player's head like a rupee.
  # And we change the Y offsets so the items don't appear lodged inside the floor, and can be picked up easily.
  # And also change the radius for items that had 0 radius so the player doesn't need to be right inside the item to pick it up.
  # Also change the code run by items during the wait state, which affects the physics when shot out of Gohdan's nose for example.
  
  item_resources_list_start = 0x803842B0
  field_item_resources_list_start = 0x803866B0
  itemGetExecute_switch_statement_entries_list_start = 0x8038CA6C
  mode_wait_switch_statement_entries_list_start = 0x8038CC7C
  
  for item_id in self.item_ids_without_a_field_model:
    if item_id in [0x39, 0x3A, 0x3E]:
      # Master Swords don't have a proper item get model defined, so we need to use the Hero's Sword instead.
      item_id_to_copy_from = 0x38
      # We also change the item get model too, not just the field model.
      item_resources_addr_to_fix = item_resources_list_start + item_id*0x24
    elif item_id in [0x6D, 0x6E, 0x6F, 0x70, 0x71, 0x72]:
      # Songs use the Pirate's Charm model by default, so we change it to use the Wind Waker model instead.
      item_id_to_copy_from = 0x22
      # We also change the item get model too, not just the field model.
      item_resources_addr_to_fix = item_resources_list_start + item_id*0x24
    elif item_id in [0xB1, 0xB2]:
      # The Magic Meter and Magic Meter Upgrade have no models, so we have to copy the Green Potion model.
      item_id_to_copy_from = 0x52
      # We also change the item get model too, not just the field model.
      item_resources_addr_to_fix = item_resources_list_start + item_id*0x24
    else:
      item_id_to_copy_from = item_id
      item_resources_addr_to_fix = None
    
    item_resources_addr_to_copy_from = item_resources_list_start + item_id_to_copy_from*0x24
    field_item_resources_addr = field_item_resources_list_start + item_id*0x1C
    
    arc_name_pointer = self.arc_name_pointers[item_id_to_copy_from]
    
    if item_id == 0xAA:
      # Hurricane Spin, switch it to using the custom scroll model instead of the sword model.
      arc_name_pointer = self.main_custom_symbols["hurricane_spin_item_resource_arc_name"]
      item_resources_addr_to_fix = item_resources_list_start + item_id*0x24
    
    self.dol.write_data(fs.write_u32, field_item_resources_addr, arc_name_pointer)
    if item_resources_addr_to_fix:
      self.dol.write_data(fs.write_u32, item_resources_addr_to_fix, arc_name_pointer)
    
    data1 = self.dol.read_data(fs.read_bytes, item_resources_addr_to_copy_from+8, 0xD)
    data2 = self.dol.read_data(fs.read_bytes, item_resources_addr_to_copy_from+0x1C, 4)
    self.dol.write_data(fs.write_bytes, field_item_resources_addr+4, data1)
    self.dol.write_data(fs.write_bytes, field_item_resources_addr+0x14, data2)
    if item_resources_addr_to_fix:
      self.dol.write_data(fs.write_bytes, item_resources_addr_to_fix+8, data1)
      self.dol.write_data(fs.write_bytes, item_resources_addr_to_fix+0x1C, data2)
  
  # Also nop out the 7 lines of code that initialize the arc filename pointer for the 6 songs and the Hurricane Spin.
  # These lines would overwrite the changes we made to their arc names.
  for address in [0x800C1970, 0x800C1978, 0x800C1980, 0x800C1988, 0x800C1990, 0x800C1998, 0x800C1BA8]:
    self.dol.write_data(fs.write_u32, address, 0x60000000) # nop
  
  
  # Fix which code runs when the player touches the field item to pick the item up.
  for item_id in range(0, 0x83+1):
    # Update the switch statement cases in function itemGetExecute for items that originally used the default case (0x800F6C8C).
    # This default case wouldn't give the player the item. It would just appear above the player's head for a moment like a Rupee and not be added to the player's inventory.
    # We switch it to case 0x800F675C, which will use the proper item get event with all the animations, text, etc.
    location_of_items_switch_statement_case = itemGetExecute_switch_statement_entries_list_start + item_id*4
    original_switch_case = self.dol.read_data(fs.read_u32, location_of_items_switch_statement_case)
    if original_switch_case == 0x800F6C8C:
      self.dol.write_data(fs.write_u32, location_of_items_switch_statement_case, 0x800F675C)
  
  # Also change the switch case in itemGetExecute used by items with IDs 0x84+ to go to 800F675C as well.
  self.dol.write_data(fs.write_u32, 0x800F6468, 0x418102F4) # bgt 0x800F675C
  
  
  # Update the visual Y offsets so the item doesn't look like it's halfway inside the floor and difficult to see.
  # First update the default case of the switch statement in the function getYOffset so that it reads from 803F9E84 (value: 23.0), instead of 803F9E80 (value: 0.0).
  self.dol.write_data(fs.write_u32, 0x800F4CD0, 0xC022A184) # lfs f1, -0x5E7C(rtoc)
  # And fix the Big Key so it uses the default case with the 23.0 offset, instead of using the 0.0 offset. (Other items already use the default case, so we don't need to fix any besides Big Key.)
  self.dol.write_data(fs.write_u32, 0x8038C8B8 + 0x4E*4, 0x800F4CD0)
  
  
  # We also change the Y offset of the hitbox for any items that have 0 for the Y offset.
  # Without this change the item would be very difficult to pick up, the only way would be to stand on top of it and do a spin attack.
  # And also change the radius of the hitbox for items that have 0 for the radius.
  item_info_list_start = 0x803882B0
  for item_id in range(0, 0xFF+1):
    item_info_entry_addr = item_info_list_start+4*item_id
    original_y_offset = self.dol.read_data(fs.read_u8, item_info_entry_addr+1)
    if original_y_offset == 0:
      self.dol.write_data(fs.write_u8, item_info_entry_addr+1, 0x28) # Y offset of 0x28
    original_radius = self.dol.read_data(fs.read_u8, item_info_entry_addr+2)
    if original_radius == 0:
      self.dol.write_data(fs.write_u8, item_info_entry_addr+2, 0x28) # Radius of 0x28
  
  
  for item_id in range(0x20, 0x44+1):
    # Update the switch statement cases in function mode_wait for certain items that originally used the default case (0x800F8190 - leads to calling itemActionForRupee).
    # This default case caused items to have the physics of rupees, which causes them to shoot out too far from Gohdan's nose.
    # We switch it to case 0x800F8160 (itemActionForArrow), which is what heart containers and heart pieces use.
    location_of_items_switch_statement_case = mode_wait_switch_statement_entries_list_start + item_id*4
    self.dol.write_data(fs.write_u32, location_of_items_switch_statement_case, 0x800F8160)
  # Also change the switch case used by items with IDs 0x4C+ to go to 800F8160 as well.
  self.dol.write_data(fs.write_u32, 0x800F8138, 0x41810028) # bgt 0x800F8160
  
  
  # Also add the Vscroll.arc containing the Hurricane Spin's custom model to the GCM's filesystem.
  vscroll_arc_path = os.path.join(ASSETS_PATH, "Vscroll.arc")
  with open(vscroll_arc_path, "rb") as f:
    data = BytesIO(f.read())
  self.add_new_raw_file("files/res/Object/Vscroll.arc", data)

def remove_shop_item_forced_uniqueness_bit(self: WWRandomizer):
  # Some shop items have a bit set that disallows you from buying the item if you already own one of that item.
  # This can be undesirable depending on what we randomize the items to be, so we unset this bit.
  # Also, Beedle doesn't have a message to say when you try to buy an item with this bit you already own. So the game would just crash if the player tried to buy these items while already owning them.
  
  shop_item_data_list_start = 0x80375E1C
  
  for shop_item_index in [0, 0xB, 0xC, 0xD]: # Bait Bag, Empty Bottle, Piece of Heart, and Treasure Chart 4 in Beedle's shops
    shop_item_data_addr = shop_item_data_list_start + shop_item_index*0x10
    buy_requirements_bitfield = self.dol.read_data(fs.read_u8, shop_item_data_addr+0xC)
    buy_requirements_bitfield = (buy_requirements_bitfield & (~2)) # Bit 02 specifies that the player must not already own this item
    self.dol.write_data(fs.write_u8, shop_item_data_addr+0xC, buy_requirements_bitfield)

def remove_forsaken_fortress_2_cutscenes(self: WWRandomizer):
  # Removes the rescuing Aryll cutscene played by the spawn when you enter the Forsaken Fortress tower.
  dzx = self.get_arc("files/res/Stage/M2tower/Room0.arc").get_file("room.dzr", DZx)
  spawn = next(spawn for spawn in dzx.entries_by_type(PLYR) if spawn.spawn_id == 16)
  spawn.evnt_index = 0xFF
  spawn.save_changes()
  
  # Removes the Ganon cutscene by making the door to his room lead back to the start of Forsaken Fortress instead.
  exit = next((exit for exit in dzx.entries_by_type(SCLS) if exit.dest_stage_name == "M2ganon"), None)
  if exit:
    exit.dest_stage_name = "sea"
    exit.room_index = 1
    exit.spawn_id = 0
    exit.save_changes()

def make_items_progressive(self: WWRandomizer):
  # This makes items progressive, so even if you get them out of order, they will always be upgraded, never downgraded.
  
  patcher.apply_patch(self, "make_items_progressive")
  
  # Update the item get funcs for the items to point to our custom progressive item get funcs instead.
  item_get_funcs_list = 0x803888C8
  
  for sword_item_id in [0x38, 0x39, 0x3A, 0x3D, 0x3E]:
    sword_item_get_func_addr = item_get_funcs_list + sword_item_id*4
    self.dol.write_data(fs.write_u32, sword_item_get_func_addr, self.main_custom_symbols["progressive_sword_item_func"])
  
  for shield_item_id in [0x3B, 0x3C]:
    shield_item_get_func_addr = item_get_funcs_list + shield_item_id*4
    self.dol.write_data(fs.write_u32, shield_item_get_func_addr, self.main_custom_symbols["progressive_shield_item_func"])
  
  for bow_item_id in [0x27, 0x35, 0x36]:
    bow_item_get_func_addr = item_get_funcs_list + bow_item_id*4
    self.dol.write_data(fs.write_u32, bow_item_get_func_addr, self.main_custom_symbols["progressive_bow_func"])
  
  for wallet_item_id in [0xAB, 0xAC]:
    wallet_item_get_func_addr = item_get_funcs_list + wallet_item_id*4
    self.dol.write_data(fs.write_u32, wallet_item_get_func_addr, self.main_custom_symbols["progressive_wallet_item_func"])
  
  for bomb_bag_item_id in [0xAD, 0xAE]:
    bomb_bag_item_get_func_addr = item_get_funcs_list + bomb_bag_item_id*4
    self.dol.write_data(fs.write_u32, bomb_bag_item_get_func_addr, self.main_custom_symbols["progressive_bomb_bag_item_func"])
  
  for quiver_item_id in [0xAF, 0xB0]:
    quiver_item_get_func_addr = item_get_funcs_list + quiver_item_id*4
    self.dol.write_data(fs.write_u32, quiver_item_get_func_addr, self.main_custom_symbols["progressive_quiver_item_func"])
  
  for picto_box_item_id in [0x23, 0x26]:
    picto_box_item_get_func_addr = item_get_funcs_list + picto_box_item_id*4
    self.dol.write_data(fs.write_u32, picto_box_item_get_func_addr, self.main_custom_symbols["progressive_picto_box_item_func"])
  
  for magic_meter_item_id in [0xB1, 0xB2]:
    magic_meter_item_get_func_addr = item_get_funcs_list + magic_meter_item_id*4
    self.dol.write_data(fs.write_u32, magic_meter_item_get_func_addr, self.main_custom_symbols["progressive_magic_meter_item_func"])
  
  # Register which item ID is for which progressive item.
  self.register_renamed_item(0x38, "Progressive Sword")
  self.register_renamed_item(0x3B, "Progressive Shield")
  self.register_renamed_item(0x27, "Progressive Bow")
  self.register_renamed_item(0xAB, "Progressive Wallet")
  self.register_renamed_item(0xAD, "Progressive Bomb Bag")
  self.register_renamed_item(0xAF, "Progressive Quiver")
  self.register_renamed_item(0x23, "Progressive Picto Box")
  self.register_renamed_item(0xB1, "Progressive Magic Meter")
  
  # Modify the item get funcs for bombs and the hero's bow to nop out the code that sets your current and max bombs/arrows to 30.
  # Without this change, getting bombs after a bomb bag upgrade would negate the bomb bag upgrade.
  # Note that normally making this change would cause the player to have 0 max bombs/arrows if they get bombs/bow before any bomb bag/quiver upgrades.
  # But in the new game start code, we set the player's current and max bombs and arrows to 30, so that is no longer an issue.
  self.dol.write_data(fs.write_u32, 0x800C36C0, 0x60000000) # Don't set current bombs
  self.dol.write_data(fs.write_u32, 0x800C36C4, 0x60000000) # Don't set max bombs
  self.dol.write_data(fs.write_u32, 0x800C346C, 0x60000000) # Don't set current arrows
  self.dol.write_data(fs.write_u32, 0x800C3470, 0x60000000) # Don't set max arrows
  
  # Modify the item get func for deku leaf to nop out the part where it adds to your magic meter.
  # Instead we make the magic meter a seperate item that the player starts with by default.
  # This way other items can use the magic meter before the player gets deku leaf.
  self.dol.write_data(fs.write_u32, 0x800C375C, 0x60000000) # Don't set max magic meter
  self.dol.write_data(fs.write_u32, 0x800C3768, 0x60000000) # Don't set current magic meter
  
  # Add an item get message for the normal magic meter since it didn't have one in vanilla.
  magic_meter_item_id = 0xB1
  description = "\\{1A 05 00 00 01}You got \\{1A 06 FF 00 00 01}magic power\\{1A 06 FF 00 00 00}!\nNow you can use magic items!"
  msg = self.bmg.add_new_message(101 + magic_meter_item_id)
  msg.string = description
  msg.text_box_type = TextBoxType.ITEM_GET
  msg.initial_draw_type = 2 # Slow initial message speed
  msg.display_item_id = magic_meter_item_id

def make_sail_behave_like_swift_sail(self: WWRandomizer):
  # Causes the wind direction to always change to face the direction KoRL is facing as long as the sail is out.
  # Also doubles KoRL's speed.
  # And changes the textures to match the swift sail from HD.
  
  # Apply the asm patch.
  patcher.apply_patch(self, "swift_sail")
  
  # Update the pause menu name for the sail.
  msg = self.bmg.messages_by_id[463]
  msg.string = "Swift Sail"
  
  new_sail_tex_image_path = os.path.join(ASSETS_PATH, "swift sail texture.png")
  new_sail_icon_image_path = os.path.join(ASSETS_PATH, "swift sail icon.png")
  new_sail_itemget_tex_image_path = os.path.join(ASSETS_PATH, "swift sail item get texture.png")
  
  if not self.using_custom_sail_texture:
    # Modify the sail's texture while sailing (only if the custom player model didn't already change the sail texture).
    ship_arc = self.get_arc("files/res/Object/Ship.arc")
    sail_image = ship_arc.get_file("new_ho1.bti", BTI)
    sail_image.replace_image_from_path(new_sail_tex_image_path)
    sail_image.save_changes()
  
  # Modify the sail's item icon.
  itemicon_arc = self.get_arc("files/res/Msg/itemicon.arc")
  sail_icon_image = itemicon_arc.get_file("sail_00.bti", BTI)
  sail_icon_image.replace_image_from_path(new_sail_icon_image_path)
  sail_icon_image.save_changes()
  
  # Modify the sail's item get texture.
  sail_itemget_arc = self.get_arc("files/res/Object/Vho.arc")
  sail_itemget_model = sail_itemget_arc.get_file("vho.bdl", BDL)
  sail_itemget_tex_image = sail_itemget_model.tex1.textures_by_name["Vho"][0]
  sail_itemget_tex_image.replace_image_from_path(new_sail_itemget_tex_image_path)
  sail_itemget_model.save()

def add_ganons_tower_warp_to_ff2(self: WWRandomizer):
  # Normally the warp object from Forsaken Fortress down to Ganon's Tower only appears in FF3.
  # But we changed Forsaken Fortress to remain permanently as FF2.
  # So we need to add the warp object to FF2 as well so the player can conveniently go between the sea and Ganon's Tower.
  # To do this we copy the warp entity from layer 2 onto layer 1.
  
  dzx = self.get_arc("files/res/Stage/sea/Room1.arc").get_file("room.dzr", DZx)
  
  layer_2_actors = dzx.entries_by_type_and_layer(ACTR, layer=DZxLayer.Layer2)
  layer_2_warp = next(x for x in layer_2_actors if x.name == "Warpmj")
  
  layer_1_warp = dzx.add_entity(ACTR, layer=DZxLayer.Layer1)
  layer_1_warp.name = layer_2_warp.name
  layer_1_warp.params = layer_2_warp.params
  layer_1_warp.x_pos = layer_2_warp.x_pos
  layer_1_warp.y_pos = layer_2_warp.y_pos
  layer_1_warp.z_pos = layer_2_warp.z_pos
  layer_1_warp.x_rot = layer_2_warp.x_rot
  layer_1_warp.y_rot = layer_2_warp.y_rot
  layer_1_warp.z_rot = layer_2_warp.z_rot
  layer_1_warp.enemy_number = layer_2_warp.enemy_number
  
  dzx.save_changes()

def add_chest_in_place_medli_grappling_hook_gift(self: WWRandomizer):
  # Add a chest in place of Medli locked in the jail cell at the peak of Dragon Roost Cavern.
  
  dzs = self.get_arc("files/res/Stage/M_Dra09/Stage.arc").get_file("stage.dzs", DZx)
  
  chest_in_jail = dzs.add_entity(TRES)
  chest_in_jail.name = "takara3"
  chest_in_jail.params = 0xFF000000
  chest_in_jail.switch_to_set = 0xFF
  chest_in_jail.chest_type = 2
  chest_in_jail.opened_flag = 0x11
  chest_in_jail.x_pos = -1620.81
  chest_in_jail.y_pos = 13600
  chest_in_jail.z_pos = 263.034
  chest_in_jail.room_num = 9
  chest_in_jail.y_rot = 0xCC16
  chest_in_jail.item_id = self.item_name_to_id["Grappling Hook"]
  
  dzs.save_changes()
  
  dzs = self.get_arc("files/res/Stage/M_NewD2/Stage.arc").get_file("stage.dzs", DZx)
  
  dummy_chest = dzs.add_entity(TRES)
  dummy_chest.name = chest_in_jail.name
  dummy_chest.params = chest_in_jail.params
  dummy_chest.switch_to_set = chest_in_jail.switch_to_set
  dummy_chest.chest_type = chest_in_jail.chest_type
  dummy_chest.opened_flag = chest_in_jail.opened_flag
  dummy_chest.x_pos = chest_in_jail.x_pos
  dummy_chest.y_pos = chest_in_jail.y_pos
  dummy_chest.z_pos = chest_in_jail.z_pos
  dummy_chest.room_num = chest_in_jail.room_num
  dummy_chest.y_rot = chest_in_jail.y_rot
  dummy_chest.item_id = 0xFF
  
  dzs.save_changes()

def add_chest_in_place_queen_fairy_cutscene(self: WWRandomizer):
  # Add a chest in place of the Queen Fairy cutscene inside Mother Isle.
  
  dzx = self.get_arc("files/res/Stage/sea/Room9.arc").get_file("room.dzr", DZx)
  
  mother_island_chest = dzx.add_entity(TRES)
  mother_island_chest.name = "takara3"
  mother_island_chest.params = 0xFF000000
  mother_island_chest.switch_to_set = 0xFF
  mother_island_chest.chest_type = 2
  mother_island_chest.opened_flag = 0x1C
  mother_island_chest.x_pos = -180031
  mother_island_chest.y_pos = 723
  mother_island_chest.z_pos = -199995
  mother_island_chest.room_num = 9
  mother_island_chest.y_rot = 0x1000
  mother_island_chest.item_id = self.item_name_to_id["Progressive Bow"]
  
  dzx.save_changes()

def add_cube_to_earth_temple_first_room(self: WWRandomizer):
  # If the player enters Earth Temple, uses Medli to cross the gap, brings Medli into the next room, then leaves Earth Temple, Medli will no longer be in the first room.
  # This can softlock the player if they don't have Deku Leaf to get across the gap in that first room.
  # So we add a cube to that first room so the player can just climb up.
  
  dzx = self.get_arc("files/res/Stage/M_Dai/Room0.arc").get_file("room.dzr", DZx)
  
  cube = dzx.add_entity(ACTR)
  cube.name = "Ecube"
  cube.params = 0x8C00FF00
  cube.x_pos = -6986.07
  cube.y_pos = -600
  cube.z_pos = 4077.37
  
  dzx.save_changes()

def add_more_magic_jars(self: WWRandomizer):
  # Add more magic jar drops to locations where it can be very inconvenient to not have them.
  
  # Dragon Roost Cavern doesn't have any magic jars in it since you normally wouldn't have Deku Leaf for it.
  # But since using Deku Leaf in DRC can be required by the randomizer, it can be annoying to not have any way to refill MP.
  # We change several skulls that originally dropped nothing when destroyed to drop magic jars instead.
  drc_center_room = self.get_arc("files/res/Stage/M_NewD2/Room2.arc").get_file("room.dzr", DZx)
  actors = drc_center_room.entries_by_type(ACTR)
  skulls = [actor for actor in actors if actor.name == "Odokuro"]
  skulls[2].dropped_item_id = self.item_name_to_id["Small Magic Jar (Pickup)"]
  skulls[2].save_changes()
  skulls[5].dropped_item_id = self.item_name_to_id["Large Magic Jar (Pickup)"]
  skulls[5].save_changes()
  drc_before_boss_room = self.get_arc("files/res/Stage/M_NewD2/Room10.arc").get_file("room.dzr", DZx)
  actors = drc_before_boss_room.entries_by_type(ACTR)
  skulls = [actor for actor in actors if actor.name == "Odokuro"]
  skulls[0].dropped_item_id = self.item_name_to_id["Large Magic Jar (Pickup)"]
  skulls[0].save_changes()
  skulls[9].dropped_item_id = self.item_name_to_id["Large Magic Jar (Pickup)"]
  skulls[9].save_changes()
  
  # The grass on the small elevated islands around DRI have a lot of grass that can drop magic, but it's not guaranteed.
  # Add a new piece of grass to each of the 2 small islands that are guaranteed to drop magic.
  dri = self.get_arc("files/res/Stage/sea/Room13.arc").get_file("room.dzr", DZx)
  grass1 = dri.add_entity(ACTR)
  grass1.name = "kusax1"
  grass1.grass_type = 0
  grass1.grass_subtype = 0
  grass1.grass_item_drop_type = 0x38 # 62.50% chance of small magic, 37.50% chance of large magic
  grass1.x_pos = 209694
  grass1.y_pos = 1900
  grass1.z_pos = -202463
  grass2 = dri.add_entity(ACTR)
  grass2.name = "kusax1"
  grass2.grass_type = 0
  grass2.grass_subtype = 0
  grass2.grass_item_drop_type = 0x38 # 62.50% chance of small magic, 37.50% chance of large magic
  grass2.x_pos = 209333
  grass2.y_pos = 1300
  grass2.z_pos = -210145
  dri.save_changes()
  
  # Make one of the pots next to the entrance to the TotG miniboss always drop large magic.
  totg_before_miniboss_room = self.get_arc("files/res/Stage/Siren/Room14.arc").get_file("room.dzr", DZx)
  actors = totg_before_miniboss_room.entries_by_type(ACTR)
  pots = [actor for actor in actors if actor.name == "kotubo"]
  pots[1].dropped_item_id = self.item_name_to_id["Large Magic Jar (Pickup)"]
  pots[1].save_changes()

def remove_title_and_ending_videos(self: WWRandomizer):
  # Remove the huge video files that play during the ending and if you sit on the title screen a while.
  # We replace them with a very small blank video file to save space.
  
  blank_video_path = os.path.join(ASSETS_PATH, "blank.thp")
  with open(blank_video_path, "rb") as f:
    new_data = BytesIO(f.read())
  self.replace_raw_file("files/thpdemo/title_loop.thp", new_data)
  self.replace_raw_file("files/thpdemo/end_st_epilogue.thp", new_data)

def modify_title_screen_logo(self: WWRandomizer):
  new_title_image_path = os.path.join(ASSETS_PATH, "title.png")
  new_subtitle_image_path = os.path.join(ASSETS_PATH, "subtitle.png")
  tlogoe_arc = self.get_arc("files/res/Object/TlogoE.arc")
  
  title_image = tlogoe_arc.get_file("logo_zelda_main.bti", BTI)
  title_image.replace_image_from_path(new_title_image_path)
  title_image.save_changes()
  
  subtitle_model = tlogoe_arc.get_file("subtitle_start_anim_e.bdl", BDL)
  subtitle_image = subtitle_model.tex1.textures_by_name["logo_sub_e"][0]
  subtitle_image.replace_image_from_path(new_subtitle_image_path)
  subtitle_model.save()
  
  subtitle_glare_model = tlogoe_arc.get_file("subtitle_kirari_e.bdl", BDL)
  subtitle_glare_image = subtitle_glare_model.tex1.textures_by_name["logo_sub_e"][0]
  subtitle_glare_image.replace_image_from_path(new_subtitle_image_path)
  subtitle_glare_model.save()
  
  # Move where the subtitle is drawn downwards a bit so the word "the" doesn't get covered up by the main logo.
  title_rel = self.get_rel("files/rels/d_a_title.rel")
  y_pos = title_rel.read_data(fs.read_float, 0x1F44)
  y_pos -= 13.0
  title_rel.write_data(fs.write_float, 0x1F44, y_pos)
  
  # Move the sparkle particle effect down a bit to fit the taller logo better.
  # (This has the side effect of also moving down the clouds below the ship, but this is not noticeable.)
  data = tlogoe_arc.get_file_entry("title_logo_e.blo").data
  fs.write_u16(data, 0x162, 0x106) # Increase Y pos by 16 pixels (0xF6 -> 0x106)

def update_game_name_icon_and_banners(self: WWRandomizer):
  new_game_name = "Wind Waker Randomized %s" % self.seed
  banner_data = self.get_raw_file("files/opening.bnr")
  fs.write_magic_str(banner_data, 0x1860, new_game_name, 0x40)
  
  new_game_id = "GZLE99"
  boot_data = self.get_raw_file("sys/boot.bin")
  fs.write_magic_str(boot_data, 0, new_game_id, 6)
  
  new_memory_card_game_name = "Wind Waker Randomizer"
  self.dol.write_data(fs.write_magic_str, 0x80339690, new_memory_card_game_name, 21)
  
  new_image_file_path = os.path.join(ASSETS_PATH, "banner.png")
  image_format = GX.ImageFormat.RGB5A3
  palette_format = GX.PaletteFormat.RGB5A3
  image_data, _, _, image_width, image_height = texture_utils.encode_image_from_path(new_image_file_path, image_format, palette_format)
  assert image_width == 96
  assert image_height == 32
  assert fs.data_len(image_data) == 0x1800
  image_data.seek(0)
  fs.write_bytes(banner_data, 0x20, image_data.read())
  
  cardicon_arc = self.get_arc("files/res/CardIcon/cardicon.arc")
  
  memory_card_icon_file_path = os.path.join(ASSETS_PATH, "memory card icon.png")
  memory_card_icon = cardicon_arc.get_file("ipl_icon1.bti", BTI)
  memory_card_icon.replace_image_from_path(memory_card_icon_file_path)
  memory_card_icon.save_changes()
  
  memory_card_banner_file_path = os.path.join(ASSETS_PATH, "memory card banner.png")
  memory_card_banner = cardicon_arc.get_file("ipl_banner.bti", BTI)
  memory_card_banner.replace_image_from_path(memory_card_banner_file_path)
  memory_card_banner.save_changes()

def allow_dungeon_items_to_appear_anywhere(self: WWRandomizer):
  item_get_funcs_list = 0x803888C8
  item_resources_list_start = 0x803842B0
  field_item_resources_list_start = 0x803866B0
  item_info_list_start = 0x803882B0
  
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
    self.register_renamed_item(item_id, item_name)
    
    # Update the item get funcs for the dungeon items to point to our custom item get funcs instead.
    custom_symbol_name = item_name.lower().replace(" ", "_") + "_item_get_func"
    item_get_func_addr = item_get_funcs_list + item_id*4
    self.dol.write_data(fs.write_u32, item_get_func_addr, self.main_custom_symbols[custom_symbol_name])
    
    # Add item get messages for the items.
    if base_item_name == "Small Key":
      description_format_string = "\\{1A 05 00 00 01}You got %s \\{1A 06 FF 00 00 01}%s small key\\{1A 06 FF 00 00 00}!"
      description = description_format_string % (get_indefinite_article(dungeon_name), dungeon_name)
    elif base_item_name == "Big Key":
      description_format_string = "\\{1A 05 00 00 01}You got the \\{1A 06 FF 00 00 01}%s Big Key\\{1A 06 FF 00 00 00}!"
      description = description_format_string % dungeon_name
    elif base_item_name == "Dungeon Map":
      description_format_string = "\\{1A 05 00 00 01}You got the \\{1A 06 FF 00 00 01}%s Dungeon Map\\{1A 06 FF 00 00 00}!"
      description = description_format_string % dungeon_name
    elif base_item_name == "Compass":
      description_format_string = "\\{1A 05 00 00 01}You got the \\{1A 06 FF 00 00 01}%s Compass\\{1A 06 FF 00 00 00}!"
      description = description_format_string % dungeon_name
    
    msg = self.bmg.add_new_message(101 + item_id)
    msg.text_box_type = TextBoxType.ITEM_GET
    msg.initial_draw_type = 2 # Slow initial message speed
    msg.display_item_id = item_id
    msg.string = description
    msg.word_wrap_string(self.bfn)
    
    # Update item resources and field item resources so the models/icons show correctly for these items.
    item_resources_addr_to_copy_from = item_resources_list_start + base_item_id*0x24
    field_item_resources_addr_to_copy_from = field_item_resources_list_start + base_item_id*0x24
    item_resources_addr = item_resources_list_start + item_id*0x24
    field_item_resources_addr = field_item_resources_list_start + item_id*0x1C
    
    arc_name_pointer = self.arc_name_pointers[base_item_id]
    
    self.dol.write_data(fs.write_u32, field_item_resources_addr, arc_name_pointer)
    self.dol.write_data(fs.write_u32, item_resources_addr, arc_name_pointer)
    
    item_icon_filename_pointer = self.icon_name_pointer[base_item_id]
    self.dol.write_data(fs.write_u32, item_resources_addr+4, item_icon_filename_pointer)
    
    data1 = self.dol.read_data(fs.read_bytes, item_resources_addr_to_copy_from+8, 0xD)
    self.dol.write_data(fs.write_bytes, item_resources_addr+8, data1)
    self.dol.write_data(fs.write_bytes, field_item_resources_addr+4, data1)
    data2 = self.dol.read_data(fs.read_bytes, item_resources_addr_to_copy_from+0x1C, 4)
    self.dol.write_data(fs.write_bytes, item_resources_addr+0x1C, data2)
    self.dol.write_data(fs.write_bytes, field_item_resources_addr+0x14, data2)
    
    data3 = self.dol.read_data(fs.read_bytes, item_resources_addr_to_copy_from+0x15, 7)
    self.dol.write_data(fs.write_bytes, item_resources_addr+0x15, data3)
    data4 = self.dol.read_data(fs.read_bytes, item_resources_addr_to_copy_from+0x20, 4)
    self.dol.write_data(fs.write_bytes, item_resources_addr+0x20, data4)
    
    data5 = self.dol.read_data(fs.read_bytes, field_item_resources_addr_to_copy_from+0x11, 3)
    self.dol.write_data(fs.write_bytes, field_item_resources_addr+0x11, data5)
    data6 = self.dol.read_data(fs.read_bytes, field_item_resources_addr_to_copy_from+0x18, 4)
    self.dol.write_data(fs.write_bytes, field_item_resources_addr+0x18, data6)
    
    # Also set the item info for all custom dungeon items to match the vanilla dungeon items.
    # This includes the bit that causes the item to not fade out over time.
    if base_item_name == "Small Key":
      item_info_value = 0x14281E05
    elif base_item_name == "Big Key":
      item_info_value = 0x00282805
    else:
      item_info_value = 0x00282800
    item_info_entry_addr = item_info_list_start+4*item_id
    self.dol.write_data(fs.write_u32, item_info_entry_addr, item_info_value)

def get_indefinite_article(string: str):
  first_letter = string.strip()[0].lower()
  if first_letter in ["a", "e", "i", "o", "u"]:
    return "an"
  else:
    return "a"

def add_article_before_item_name(item_name: str):
  """Adds a grammatical article ("a", "an", "the", or nothing) in front an item's name."""
  
  article = None
  if re.search(r"\d$", item_name):
    article = None
  elif (PROGRESS_ITEMS + NONPROGRESS_ITEMS).count(item_name) > 1:
    article = get_indefinite_article(item_name)
  elif item_name in CONSUMABLE_ITEMS:
    article = get_indefinite_article(item_name)
  elif item_name in DUPLICATABLE_CONSUMABLE_ITEMS:
    article = get_indefinite_article(item_name)
  elif item_name.lower().endswith(" small key"):
    article = get_indefinite_article(item_name)
  elif item_name.endswith(" Trap Chest"):
    article = get_indefinite_article(item_name)
  elif item_name in ["Delivery Bag", "Boat's Sail", "Note to Mom"]:
    article = get_indefinite_article(item_name)
  elif item_name in ["Beedle's Chart", "Bombs", "Tingle's Chart", "Maggie's Letter", "Father's Letter"]:
    article = None
  elif item_name in ["Nayru's Pearl", "Din's Pearl", "Farore's Pearl"]:
    article = None
  else:
    article = "the"
  
  if article:
    item_name = article + " " + item_name
  
  return item_name

def upper_first_letter(string):
  first_letter = string[0].upper()
  return first_letter + string[1:]

def remove_ballad_of_gales_warp_in_cutscene(self: WWRandomizer):
  for island_index in range(1, 49+1):
    dzx = self.get_arc("files/res/Stage/sea/Room%d.arc" % island_index).get_file("room.dzr", DZx)
    for spawn in dzx.entries_by_type(PLYR):
      if spawn.spawn_type == 9: # Spawn type is warping in on a cyclone
        spawn.spawn_type = 2 # Change to spawn type of instantly spawning on KoRL instead
        spawn.save_changes()

def fix_shop_item_y_offsets(self: WWRandomizer):
  shop_item_display_data_list_start = 0x8034FD10
  
  for item_id in range(0, 0xFE+1):
    display_data_addr = shop_item_display_data_list_start + item_id*0x20
    y_offset = self.dol.read_data(fs.read_float, display_data_addr+0x10)
    
    if y_offset == 0 and item_id not in [0x10, 0x11, 0x12]:
      # If the item didn't originally have a Y offset we need to give it one so it's not sunken into the pedestal.
      # Only exceptions are for items 10 11 and 12 - arrow refill pickups. Those have no Y offset but look fine already.
      new_y_offset = 20.0
      self.dol.write_data(fs.write_float, display_data_addr+0x10, new_y_offset)

def update_shop_item_descriptions(self: WWRandomizer):
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

def update_auction_item_names(self: WWRandomizer):
  item_name = self.logic.done_item_locations["Windfall Island - 5 Rupee Auction"]
  msg = self.bmg.messages_by_id[7441]
  msg.string = "\\{1A 06 FF 00 00 01}%s" % item_name
  
  item_name = self.logic.done_item_locations["Windfall Island - 40 Rupee Auction"]
  msg = self.bmg.messages_by_id[7440]
  msg.string = "\\{1A 06 FF 00 00 01}%s" % item_name
  
  item_name = self.logic.done_item_locations["Windfall Island - 60 Rupee Auction"]
  msg = self.bmg.messages_by_id[7442]
  msg.string = "\\{1A 06 FF 00 00 01}%s" % item_name
  
  item_name = self.logic.done_item_locations["Windfall Island - 80 Rupee Auction"]
  msg = self.bmg.messages_by_id[7443]
  msg.string = "\\{1A 06 FF 00 00 01}%s" % item_name

def update_battlesquid_item_names(self: WWRandomizer):
  item_name = self.logic.done_item_locations["Windfall Island - Battlesquid - First Prize"]
  msg = self.bmg.messages_by_id[7520]
  msg.string = (
    "\\{1A 05 01 00 8E}Hoorayyy! Yayyy! Yayyy!\nOh, thank you, Mr. Sailor!\n\n\n"
    "Please take this \\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 00} as a sign of our gratitude. You are soooooo GREAT!" % item_name
  )
  msg.word_wrap_string(self.bfn)
  
  item_name = self.logic.done_item_locations["Windfall Island - Battlesquid - Second Prize"]
  msg = self.bmg.messages_by_id[7521]
  msg.string = (
    "\\{1A 05 01 00 8E}Hoorayyy! Yayyy! Yayyy!\nOh, thank you so much, Mr. Sailor!\n\n\n"
    "This is our thanks to you! It's been passed down on our island for many years, so don't tell the island elder, OK? "
    "Here...\\{1A 06 FF 00 00 01}\\{1A 05 00 00 39} \\{1A 06 FF 00 00 00}Please accept this \\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 00}!" % item_name
  )
  msg.word_wrap_string(self.bfn)
  
  # The high score one doesn't say the item name in text anywhere, so no need to update it.
  #item_name = self.logic.done_item_locations["Windfall Island - Battlesquid - 20 Shots or Less Prize"]
  #msg = self.bmg.messages_by_id[7523]

def update_item_names_in_letter_advertising_rock_spire_shop(self: WWRandomizer):
  item_name_1 = self.logic.done_item_locations["Rock Spire Isle - Beedle's Special Shop Ship - 500 Rupee Item"]
  item_name_2 = self.logic.done_item_locations["Rock Spire Isle - Beedle's Special Shop Ship - 950 Rupee Item"]
  item_name_3 = self.logic.done_item_locations["Rock Spire Isle - Beedle's Special Shop Ship - 900 Rupee Item"]
  msg = self.bmg.messages_by_id[3325]
  
  lines = msg.string.split("\n")
  unchanged_string_before = "\n".join(lines[0:8]) + "\n"
  unchanged_string_after = "\n".join(lines[12:])
  
  hint_string = (
    "Do you have need of %s \\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 00}, " % (get_indefinite_article(item_name_1), item_name_1) +
    "%s \\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 00}, " % (get_indefinite_article(item_name_2), item_name_2) +
    "or %s \\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 00}? " % (get_indefinite_article(item_name_3), item_name_3) +
    "We have them at special bargain prices."
  )
  
  # Letters are supposed to have 2 spaces at the start of each line, so word wrap to a reduced width
  # to account for that, and then add the 2 spaces to each line.
  space_width = self.bfn.get_char_width(" ")
  hint_string = msg.word_wrap_string_part(self.bfn, hint_string, extra_line_length=-2*space_width)
  hint_string = msg.pad_string_to_next_4_lines(hint_string)
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

def shorten_zephos_event(self: WWRandomizer):
  # Make the Zephos event end when the player gets the item from the shrine, before Zephos actually appears.
  
  event_list = self.get_arc("files/res/Stage/sea/Stage.arc").get_file("event_list.dat", EventList)
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

def update_korl_dialogue(self: WWRandomizer):
  msg = self.bmg.messages_by_id[3443]
  msg.string = "\\{1A 05 00 00 00}, the sea is all yours.\n"
  msg.string += "Make sure you explore every corner\n"
  msg.string += "in search of items to help you. Remember\n"
  msg.string += "that your quest is to defeat Ganondorf."

def set_num_starting_triforce_shards(self: WWRandomizer):
  num_shards_address = self.main_custom_symbols["num_triforce_shards_to_start_with"]
  self.dol.write_data(fs.write_u8, num_shards_address, self.options.num_starting_triforce_shards)

def set_starting_health(self: WWRandomizer):
  heart_pieces = self.options.starting_pohs
  heart_containers = self.options.starting_hcs * 4
  
  starting_health = heart_containers + heart_pieces
  
  starting_quarter_hearts_address = self.main_custom_symbols["starting_quarter_hearts"]
  
  self.dol.write_data(fs.write_u16, starting_quarter_hearts_address, starting_health)
  if starting_health < 8:
    patcher.apply_patch(self, "remove_low_health_beep_anim")

def set_starting_magic(self: WWRandomizer, starting_magic):
  starting_magic_address = self.main_custom_symbols["starting_magic"]
  self.dol.write_data(fs.write_u8, starting_magic_address, starting_magic)

def add_pirate_ship_to_windfall(self: WWRandomizer):
  windfall_dzr = self.get_arc("files/res/Stage/sea/Room11.arc").get_file("room.dzr", DZx)
  ship_dzr = self.get_arc("files/res/Stage/Asoko/Room0.arc").get_file("room.dzr", DZx)
  ship_dzs = self.get_arc("files/res/Stage/Asoko/Stage.arc").get_file("stage.dzs", DZx)
  event_list = self.get_arc("files/res/Stage/Asoko/Stage.arc").get_file("event_list.dat", EventList)
  
  windfall_layer_2_actors = windfall_dzr.entries_by_type_and_layer(ACTR, layer=DZxLayer.Layer2)
  layer_2_pirate_ship = next(x for x in windfall_layer_2_actors if x.name == "Pirates")
  
  default_layer_pirate_ship = windfall_dzr.add_entity(ACTR)
  default_layer_pirate_ship.name = layer_2_pirate_ship.name
  default_layer_pirate_ship.params = layer_2_pirate_ship.params
  default_layer_pirate_ship.x_pos = layer_2_pirate_ship.x_pos
  default_layer_pirate_ship.y_pos = layer_2_pirate_ship.y_pos
  default_layer_pirate_ship.z_pos = layer_2_pirate_ship.z_pos
  default_layer_pirate_ship.x_rot = layer_2_pirate_ship.x_rot
  default_layer_pirate_ship.y_rot = layer_2_pirate_ship.y_rot
  default_layer_pirate_ship.z_rot = layer_2_pirate_ship.z_rot
  default_layer_pirate_ship.enemy_number = layer_2_pirate_ship.enemy_number
  
  # Change the door to not require a password.
  default_layer_pirate_ship.pirate_ship_door_type = 0
  
  windfall_dzr.save_changes()
  
  # Remove Niko from the ship to get rid of his events.
  for layer_num in [2, 3]:
    actors_on_this_layer = ship_dzr.entries_by_type_and_layer(ACTR, layer=layer_num)
    niko = next(x for x in actors_on_this_layer if x.name == "P2b")
    ship_dzr.remove_entity(niko, ACTR, layer=layer_num)
  
  # Add Aryll to the ship instead.
  aryll = ship_dzr.add_entity(ACTR)
  aryll.name = "Ls1"
  aryll.which_aryll = 0 # Looking out of her lookout (though we change her animation to just stand there via asm).
  aryll.x_pos = 600
  aryll.y_pos = -550
  aryll.z_pos = -200
  aryll.y_rot = 0xC000
  
  # Change Aryll's text when you talk to her.
  msg = self.bmg.messages_by_id[3008]
  #msg.initial_sound = 1 # "Ah!"
  #msg.initial_sound = 2 # "Wah!?"
  #msg.initial_sound = 7 # "Auhh!?"
  #msg.initial_sound = 95 # "Hai!"
  #msg.initial_sound = 104 # "Oyyyy!"
  #msg.initial_sound = 105 # "Hoyyyy!"
  msg.initial_sound = 106 # "Haiiii~!"
  msg.construct_string_from_parts(self.bfn, [
    "'Hoy! Big Brother!\n" + "Wanna play a game? It's fun, trust me!",
    "Just \\{1A 06 FF 00 00 01}step on this button\\{1A 06 FF 00 00 00}, "
    "and try to swing across the ropes to reach that door over there before time's up!"
  ])
  
  # We need to make the pirate ship stage (Asoko) load the wave bank with Aryll's voice in it.
  stage_bgm_info_list_start = 0x8039C30C
  second_dynamic_scene_waves_list_start = 0x8039C2E4
  asoko_spot_id = 0xC
  new_second_scene_wave_index = 0x0E # Second dynamic scene wave indexes 0E-13 are unused free slots, so we use one of them.
  isle_link_0_aw_index = 0x19 # The index of IsleLink_0.aw, the wave bank containing Aryll's voice.
  
  asoko_bgm_info_ptr = stage_bgm_info_list_start + asoko_spot_id*4
  new_second_scene_wave_ptr = second_dynamic_scene_waves_list_start + new_second_scene_wave_index*2
  self.dol.write_data(fs.write_u8, asoko_bgm_info_ptr+3, new_second_scene_wave_index)
  self.dol.write_data(fs.write_u8, new_second_scene_wave_ptr+0, isle_link_0_aw_index)
  
  
  # Add a custom event where Aryll notices if the player got trapped in the chest room after the timer ran out and opens the door for them.
  
  event = event_list.add_event("AryllOpensDoor")
  
  camera = event.add_actor("CAMERA")
  camera.staff_type = 2
  
  aryll_actor = event.add_actor("Ls1")
  aryll_actor.staff_type = 0
  
  link = event.add_actor("Link")
  link.staff_type = 0
  
  act = camera.add_action("FIXEDFRM", properties=[
    ("Eye", (aryll.x_pos, aryll.y_pos+90, aryll.z_pos-120)),
    ("Center", (aryll.x_pos, aryll.y_pos+70, aryll.z_pos)),
    ("Fovy", 60.0),
    ("Timer", 30),
  ])
  
  # Make Aryll look at the player.
  act = aryll_actor.add_action("LOK_PLYER", properties=[
    ("prm_0", 8),
  ])
  
  # Some of Aryll's animations that can be used here (incomplete list):
  # 2: Arms behind back, lightly moving body
  # 4: Arms behind back, swaying head back and forth
  # 5: Idle
  # 6: Giving present
  # 8: Looking through telescope
  # 9: Item get anim
  act = aryll_actor.add_action("ANM_CHG", properties=[
    ("AnmNo", 8), # Looking through telescope
  ])
  
  act = aryll_actor.add_action("WAIT", properties=[
    ("Timer", 30),
  ])
  
  # Set Aryll's text for when you're trapped in the chest room.
  new_message_id = 849
  msg = self.bmg.add_new_message(new_message_id)
  msg.text_box_type = TextBoxType.DIALOG
  msg.initial_draw_type = 0 # Normal
  msg.text_alignment = 4 # Bottom text box
  msg.string = "Oh! Did you get stuck in there, Big Brother?"
  
  act = aryll_actor.add_action("TALK_MSG", properties=[
    ("msg_num", new_message_id),
  ])
  
  act = aryll_actor.add_action("ANM_CHG", properties=[
    ("AnmNo", 4), # Arms behind back, swaying head back and forth
  ])
  
  new_message_id = 850
  msg = self.bmg.add_new_message(new_message_id)
  msg.text_box_type = TextBoxType.DIALOG
  msg.initial_draw_type = 0 # Normal
  msg.text_alignment = 4 # Bottom text box
  msg.string = "Don't worry, I'll open the door for you."
  
  act = aryll_actor.add_action("TALK_MSG", properties=[
    ("msg_num", new_message_id),
  ])
  
  # Reset Aryll to her idle animation at the end of the event.
  act = aryll_actor.add_action("ANM_CHG", properties=[
    ("AnmNo", 5), # Idle
  ])
  
  # Make sure Link still animates during the event instead of freezing.
  act = link.add_action("001wait")
  
  event.ending_flags[0] = aryll_actor.actions[-1].flag_id_to_set
  
  event_list.save_changes()
  
  new_evnt = ship_dzs.add_entity(EVNT)
  new_evnt.name = event.name
  new_event_index_in_evnt = ship_dzs.entries_by_type(EVNT).index(new_evnt)
  
  
  # Change the facial animation used by Aryll animation 4 (arms behind back, swaying back and forth) to be 5 (smug expression).
  aryll_rel = self.get_rel("files/rels/d_a_npc_ls1.rel")
  aryll_rel.write_data(fs.write_u8, 0x5D18 + 4*0x10 + 1, 5)
  
  
  # Now that we have a custom event, we must actually detect when the player is trapped in the chest room and trigger it.
  # To do this, we use a custom switch logic operator actor.
  
  # Set up the switches we will use.
  countdown_happening_switch = 0xC0
  aryll_opened_door_switch = 0xC1
  countdown_not_happening_switch = 0xC2
  inside_chest_room_switch = 0xC3
  door_should_be_open_switch = 0xC4
  
  
  # Detect when the player is inside the chest room.
  swc00 = ship_dzr.add_entity(SCOB)
  swc00.name = "SW_C00"
  swc00.switch_to_set = inside_chest_room_switch
  swc00.behavior_type = 0 # Unset the switch when leaving the region
  swc00.prerequisite_switch = 0xFF
  swc00.x_pos = 0
  swc00.y_pos = -550
  swc00.z_pos = -3900
  swc00.scale_x = 64
  swc00.scale_y = 36
  swc00.scale_z = 64
  
  
  # Detect when the countdown is not currently going on.
  sw_op = ship_dzr.add_entity(ACTR)
  sw_op.name = "SwOp"
  sw_op.operation = 3 # NOR
  sw_op.is_continuous = 1
  sw_op.num_switches_to_check = 1
  sw_op.first_switch_to_check = countdown_happening_switch
  sw_op.switch_to_set = countdown_not_happening_switch
  sw_op.evnt_index = 0xFF
  sw_op.x_pos = 0
  sw_op.y_pos = 0
  sw_op.z_pos = -4400
  
  
  # Handle starting the event for Aryll noticing the player is trapped.
  aryll_opens_door_switches = [
    countdown_not_happening_switch,
    inside_chest_room_switch,
  ]
  assert switches_are_contiguous(aryll_opens_door_switches)
  sw_op = ship_dzr.add_entity(ACTR)
  sw_op.name = "SwOp"
  sw_op.operation = 0 # AND
  sw_op.is_continuous = 1
  sw_op.num_switches_to_check = len(aryll_opens_door_switches)
  sw_op.first_switch_to_check = min(aryll_opens_door_switches)
  sw_op.switch_to_set = aryll_opened_door_switch
  sw_op.evnt_index = new_event_index_in_evnt
  sw_op.delay = 150
  sw_op.x_pos = 0
  sw_op.y_pos = 0
  sw_op.z_pos = -3900
  
  
  # Handle opening the door.
  door_is_open_switches = [
    countdown_happening_switch,
    aryll_opened_door_switch,
  ]
  assert switches_are_contiguous(door_is_open_switches)
  sw_op = ship_dzr.add_entity(ACTR)
  sw_op.name = "SwOp"
  sw_op.operation = 2 # OR
  sw_op.is_continuous = 1
  sw_op.num_switches_to_check = len(door_is_open_switches)
  sw_op.first_switch_to_check = min(door_is_open_switches)
  sw_op.switch_to_set = door_should_be_open_switch
  sw_op.evnt_index = 0xFF
  sw_op.x_pos = 0
  sw_op.y_pos = 0
  sw_op.z_pos = -3400
  for layer_num in [2, 3]:
    actors_on_this_layer = ship_dzr.entries_by_type_and_layer(ACTR, layer=layer_num)
    ashut = next(x for x in actors_on_this_layer if x.name == "Ashut")
    ashut.switch_to_check = door_should_be_open_switch
  
  
  ship_dzr.save_changes()
  ship_dzs.save_changes()


@dataclass(frozen=True)
class CyclicWarpPotData:
  stage_name: str
  room_num: int
  x: float
  y: float
  z: float
  y_rot: int
  event_reg_index: int

INTER_DUNGEON_WARP_DATA = [
  [
    CyclicWarpPotData("M_NewD2", 2, 2185, 0, 590, 0xA000, 2), # DRC
    CyclicWarpPotData("kindan", 1, 986, 3956.43, 9588, 0xB929, 2), # FW
    CyclicWarpPotData("Siren", 6, 277, 229.42, -6669, 0xC000, 2), # TotG
  ],
  [
    CyclicWarpPotData("ma2room", 2, 1556, 728.46, -7091, 0xEAA6, 5), # FF
    CyclicWarpPotData("M_Dai", 1, -8010, 1010, -1610, 0, 5), # ET
    CyclicWarpPotData("kaze", 3, -4333, 1100, 48, 0x4000, 5), # WT
  ],
]

def add_inter_dungeon_warp_pots(self: WWRandomizer):
  for warp_pot_datas_in_this_cycle in INTER_DUNGEON_WARP_DATA:
    for warp_pot_index, warp_pot_data in enumerate(warp_pot_datas_in_this_cycle):
      room_arc_path = "files/res/Stage/%s/Room%d.arc" % (warp_pot_data.stage_name, warp_pot_data.room_num)
      stage_arc_path = "files/res/Stage/%s/Stage.arc" % warp_pot_data.stage_name
      room_dzx = self.get_arc(room_arc_path).get_file("room.dzr", DZx)
      stage_dzx = self.get_arc(stage_arc_path).get_file("stage.dzs", DZx)
      
      # Add new player spawn locations.
      if warp_pot_data.stage_name in ["M_Dai", "kaze"]:
        # Earth and Wind temple spawns must be in the stage instead of the room or the game will crash. Not sure why.
        dzx_for_spawn = stage_dzx
      else:
        dzx_for_spawn = room_dzx
      spawn = dzx_for_spawn.add_entity(PLYR)
      spawn.spawn_type = 7 # Flying out of a warp pot
      spawn.room_num = warp_pot_data.room_num
      spawn.x_pos = warp_pot_data.x
      spawn.y_pos = warp_pot_data.y
      spawn.z_pos = warp_pot_data.z
      spawn.y_rot = warp_pot_data.y_rot
      spawn.spawn_id = 69
      
      # Ensure there wasn't already a spawn using the ID we chose, just to be safe.
      spawns = dzx_for_spawn.entries_by_type(PLYR)
      spawn_id_69s = [x for x in spawns if x.spawn_id == 69]
      assert len(spawn_id_69s) == 1
      
      # Add new exits.
      pot_index_to_exit_index = []
      for other_warp_pot_data in warp_pot_datas_in_this_cycle:
        scls_exit = room_dzx.add_entity(SCLS)
        scls_exit.dest_stage_name = other_warp_pot_data.stage_name
        scls_exit.spawn_id = 69
        scls_exit.room_index = other_warp_pot_data.room_num
        scls_exit.fade_type = 4 # Warp pot fade out
        pot_index_to_exit_index.append(len(room_dzx.entries_by_type(SCLS))-1)
      
      # Add the warp pots themselves.
      warp_pot = room_dzx.add_entity(ACTR)
      warp_pot.name = "Warpts%d" % (warp_pot_index+1) # Warpts1 Warpts2 or Warpts3
      warp_pot.type = warp_pot_index + 2 # 2 3 or 4
      warp_pot.cyclic_event_reg_index = warp_pot_data.event_reg_index
      warp_pot.cyclic_dest_1_exit = pot_index_to_exit_index[0]
      warp_pot.cyclic_dest_2_exit = pot_index_to_exit_index[1]
      warp_pot.cyclic_dest_3_exit = pot_index_to_exit_index[2]
      warp_pot.x_pos = warp_pot_data.x
      warp_pot.y_pos = warp_pot_data.y
      warp_pot.z_pos = warp_pot_data.z
      warp_pot.y_rot = warp_pot_data.y_rot
      warp_pot.x_rot = 0xFFFF
      warp_pot.z_rot = 0xFFFF
      
      room_dzx.save_changes()
      stage_dzx.save_changes()
  
  # We also need to copy the particles used by the warp pots into the FF and TotG particle banks.
  # Without this the warp pots would have no particles, and the game would crash on real hardware.
  drc_jpc = self.get_jpc("files/res/Particle/Pscene035.jpc")
  totg_jpc = self.get_jpc("files/res/Particle/Pscene050.jpc")
  ff_jpc = self.get_jpc("files/res/Particle/Pscene043.jpc")
  
  for particle_id in [0x8161, 0x8162, 0x8165, 0x8166, 0x8112]:
    particle = drc_jpc.particles_by_id[particle_id]
    
    for dest_jpc in [totg_jpc, ff_jpc]:
      if particle_id in dest_jpc.particles_by_id:
        continue
      
      copied_particle = copy.deepcopy(particle)
      dest_jpc.add_particle(copied_particle)
      
      for texture_filename in copied_particle.tdb1.texture_filenames:
        if texture_filename not in dest_jpc.textures_by_filename:
          texture = drc_jpc.textures_by_filename[texture_filename]
          copied_texture = copy.deepcopy(texture)
          dest_jpc.add_texture(copied_texture)

def remove_makar_kidnapping_event(self: WWRandomizer):
  dzx = self.get_arc("files/res/Stage/kaze/Room3.arc").get_file("room.dzr", DZx)
  actors = dzx.entries_by_type_and_layer(ACTR, layer=DZxLayer.Default)
  
  # Remove the AND switch actor that makes the Floormasters appear after unlocking the door.
  and_switch_actor = next(x for x in actors if x.name == "AND_SW2")
  dzx.remove_entity(and_switch_actor, ACTR, layer=DZxLayer.Default)
  
  # Remove the enable spawn switch from the Wizzrobe so it's just always there.
  wizzrobe = next(x for x in actors if x.name == "wiz_r")
  wizzrobe.enable_spawn_switch = 0xFF
  wizzrobe.save_changes()

def increase_player_movement_speeds(self: WWRandomizer):
  # Double crawling speed.
  self.dol.write_data(fs.write_float, 0x8035DB94, 3.0*2)
  
  # Change rolling so that it scales from 20.0 to 26.0 speed depending on the player's speed when they roll.
  # In vanilla, it scaled from 0.5 to 26.0 instead.
  self.dol.write_data(fs.write_float, 0x8035D3D0, 6.0/17.0) # Rolling speed multiplier on walking speed
  self.dol.write_data(fs.write_float, 0x8035D3D4, 20.0) # Rolling base speed

def add_chart_number_to_item_get_messages(self: WWRandomizer):
  for item_id, item_name in self.item_names.items():
    if item_name.startswith("Treasure Chart "):
      msg = self.bmg.messages_by_id[101 + item_id]
      msg.string = msg.string.replace("a \\{1A 06 FF 00 00 01}Treasure Chart", "\\{1A 06 FF 00 00 01}%s" % item_name)
    elif item_name.startswith("Triforce Chart ") and "deciphered" not in item_name:
      msg = self.bmg.messages_by_id[101 + item_id]
      msg.string = msg.string.replace("a \\{1A 06 FF 00 00 01}Triforce Chart", "\\{1A 06 FF 00 00 01}%s" % item_name)


# Speeds up the grappling hook significantly to behave similarly to HD
def increase_grapple_animation_speed(self: WWRandomizer):
  # Double the velocity the grappling hook is thrown out (from 20.0 to 40.0)
  # Instead of reading 20.0 from 803F9D28, read 40.0 from 803F9DAC.
  # (We can't just change the float value itself because it's used for multiple things.)
  self.dol.write_data(fs.write_s16, 0x800EE0E4+2, 0x803F9DAC-0x803FFD00)
  
  # Halve the number of frames grappling hook extends outward in 1st person (from 40 to 20 frames)
  self.dol.write_data(fs.write_u32, 0x800EDB74, 0x38030014) # addi r0,r3,20
  
  # Halve the number of frames grappling hook extends outward in 3rd person (from 20 to 10)
  self.dol.write_data(fs.write_u32, 0x800EDEA4, 0x3803000A) # addi r0,r3,10
  
  # Increase the speed at which the grappling hook falls onto its target (from 10.0 to 20.0)
  # Instead of reading 10.0 from 803F9C44, read 20.0 from 803F9D28.
  # (We can't just change the float value itself because it's used for multiple things.)
  self.dol.write_data(fs.write_s16, 0x800EEC40+2, 0x803F9D28-0x803FFD00)
  
  # Increase grappling hook speed as it wraps around its target (from 17.0 to 25.0)
  # (Only read in one spot, so we can change the value directly.)
  self.dol.write_data(fs.write_float, 0x803F9D60, 25.0)
  
  # Increase the counter that determines how fast to end the wrap around animation. (From +1 each frame to +6 each frame)
  self.dol.write_data(fs.write_u32, 0x800EECA8, 0x38A30006) # addi r5,r3,6

# Speeds up the rate in which blocks move when pushed/pulled
def increase_block_moving_animation(self: WWRandomizer):
  # Increase Link's pushing animation speed from 1.0 to 1.4
  # Note that this causes a softlock when opening a specific door in Forsaken Fortress - see fix_forsaken_fortress_door_softlock for more details.
  self.dol.write_data(fs.write_float, 0x8035DBB0, 1.4)
  
  # Increase Link's pulling animation speed from 1.0 to 1.4
  self.dol.write_data(fs.write_float, 0x8035DBB8, 1.4)
  
  block_rel = self.get_rel("files/rels/d_a_obj_movebox.rel")
  
  offset = 0x54B0 # M_attr__Q212daObjMovebox5Act_c. List of various data for each type of block.
  for i in range(13): # 13 types of blocks total.
    block_rel.write_data(fs.write_u16, offset + 0x04, 12) # Reduce number frames for pushing to last from 20 to 12
    block_rel.write_data(fs.write_u16, offset + 0x0A, 12) # Reduce number frames for pulling to last from 20 to 12
    offset += 0x9C

def increase_misc_animations(self: WWRandomizer):
  # Increase the animation speed that Link initiates a climb (0.8 -> 1.6)
  self.dol.write_data(fs.write_float, 0x8035D738, 1.6)
  
  # Increase speed Link climbs ladders/vines (1.2 -> 1.6)
  self.dol.write_data(fs.write_float, 0x8035DB38, 1.6)
  
  # Increase speed Link starts climbing a ladder/vine (1.0 -> 1.6)
  self.dol.write_data(fs.write_float, 0x8035DB18, 1.6)
  
  # Increase speed Link ends climbing a ladder/vine (0.9 -> 1.4)
  self.dol.write_data(fs.write_float, 0x8035DB20, 1.4)
  
  # Increase Link's sidle animation speed (1.6 -> 2.0)
  self.dol.write_data(fs.write_float, 0x8035D6AC, 2.0)
  
  # Halve the number of frames camera takes to focus on an npc for a conversation (from 20 to 10)
  self.dol.write_data(fs.write_u32, 0x8016DA2C, 0x3800000A) # li r0,10


def change_starting_clothes(self: WWRandomizer):
  custom_model_metadata = customizer.get_model_metadata(self.custom_model_name)
  disable_casual_clothes = custom_model_metadata.get("disable_casual_clothes", False)
  
  should_start_with_heros_clothes_address = self.main_custom_symbols["should_start_with_heros_clothes"]
  if self.options.player_in_casual_clothes and not disable_casual_clothes:
    self.dol.write_data(fs.write_u8, should_start_with_heros_clothes_address, 0)
  else:
    self.dol.write_data(fs.write_u8, should_start_with_heros_clothes_address, 1)

def check_hide_ship_sail(self: WWRandomizer):
  # Allow the custom model author to specify if they want the ship's sail to be hidden.
  # The reason simply changing the texture to be transparent doesn't work is that even when fully transparent, it will still be rendered over the white lines the ship makes when parting the sea in front of it.
  custom_model_metadata = customizer.get_model_metadata(self.custom_model_name)
  hide_ship_sail = custom_model_metadata.get("hide_ship_sail", False)
  
  if hide_ship_sail:
    # Make the sail's draw function return immediately to hide it.
    sail_draw_func_address = 0x800E93B8 # daHo_packet_c::draw(void)
    self.dol.write_data(fs.write_u32, sail_draw_func_address, 0x4E800020) # blr

def shorten_auction_intro_event(self: WWRandomizer):
  event_list = self.get_arc("files/res/Stage/Orichh/Stage.arc").get_file("event_list.dat", EventList)
  auction_start_event = event_list.events_by_name["AUCTION_START"]
  camera = next(actor for actor in auction_start_event.actors if actor.name == "CAMERA")
  
  #pre_pan_delay = camera.actions[2]
  pan_action = camera.actions[3]
  post_pan_delay = camera.actions[4]
  
  # Remove the 200 frame long panning action and the 30 frame delay after panning.
  # We don't remove the 30 frame delay before panning, because if the intro is completely removed or only a couple frames long, there is a race condition where the timer entity may not be finished being asynchronously created until the intro is over. If this happens the auction entity will have no reference to the timer entity, causing a crash later on.
  camera.actions.remove(pan_action)
  camera.actions.remove(post_pan_delay)

def disable_invisible_walls(self: WWRandomizer):
  # Remove some invisible walls to allow sequence breaking.
  # In vanilla switch index FF meant an invisible wall appears only when you have no sword.
  # But we remove that in the randomizer, so invisible walls with switch index FF are effectively completely disabled. So we use this to disable these invisible walls.
  
  # Remove an invisible wall in the second room of DRC.
  dzx = self.get_arc("files/res/Stage/M_NewD2/Room2.arc").get_file("room.dzr", DZx)
  invisible_wall = next(x for x in dzx.entries_by_type(SCOB) if x.name == "Akabe")
  invisible_wall.disable_spawn_switch = 0xFF
  invisible_wall.save_changes()

def update_skip_rematch_bosses_game_variable(self: WWRandomizer):
  skip_rematch_bosses_address = self.main_custom_symbols["skip_rematch_bosses"]
  if self.options.skip_rematch_bosses:
    self.dol.write_data(fs.write_u8, skip_rematch_bosses_address, 1)
  else:
    self.dol.write_data(fs.write_u8, skip_rematch_bosses_address, 0)

def update_sword_mode_game_variable(self: WWRandomizer):
  sword_mode_address = self.main_custom_symbols["sword_mode"]
  if self.options.sword_mode == SwordMode.START_WITH_SWORD:
    self.dol.write_data(fs.write_u8, sword_mode_address, 0)
  elif self.options.sword_mode == SwordMode.NO_STARTING_SWORD:
    self.dol.write_data(fs.write_u8, sword_mode_address, 1)
  elif self.options.sword_mode == SwordMode.SWORDLESS:
    self.dol.write_data(fs.write_u8, sword_mode_address, 2)
  else:
    raise Exception("Unknown sword mode: %s" % self.options.sword_mode)

def update_starting_gear(self: WWRandomizer, starting_gear: list[str]):
  # Saves the list of starting items that should be given to the player when starting a new save.
  # Note: This tweak may be called more than once in a single randomization.
  
  starting_gear = starting_gear.copy()
  
  # Changing starting magic doesn't work when done via our normal starting items initialization code, so we need to handle it specially.
  set_starting_magic(self, 16*starting_gear.count("Progressive Magic Meter"))
  while "Progressive Magic Meter" in starting_gear:
    starting_gear.remove("Progressive Magic Meter")
  
  if len(starting_gear) > MAXIMUM_ADDITIONAL_STARTING_ITEMS:
    raise Exception("Tried to start with more starting items (%d) than the maximum number that was allocated (%d)" % (len(starting_gear), MAXIMUM_ADDITIONAL_STARTING_ITEMS))
  starting_gear_array_address = self.main_custom_symbols["starting_gear"]
  
  # Ensure that the max items constant isn't larger than the actual space we have available.
  # We don't want to go past the end of the allocated space and overwrite other memory.
  next_symbol_addr = min(addr for addr in self.main_custom_symbols.values() if addr > starting_gear_array_address)
  gear_slots_available = (next_symbol_addr - starting_gear_array_address) - 1
  assert gear_slots_available >= MAXIMUM_ADDITIONAL_STARTING_ITEMS, "Max starting items constant is too large"
  
  for i, item_name in enumerate(starting_gear):
    item_id = self.item_name_to_id[item_name]
    self.dol.write_data(fs.write_u8, starting_gear_array_address+i, item_id)
  
  # Write end marker.
  self.dol.write_data(fs.write_u8, starting_gear_array_address+len(starting_gear), 0xFF)

def update_text_for_swordless(self: WWRandomizer):
  msg = self.bmg.messages_by_id[1128]
  msg.string = "\\{1A 05 00 00 00}, you may not have the\nMaster Sword, but do not be afraid!\n\n\n"
  msg.string += "The hammer of the dead is all you\nneed to crush your foe...\n\n\n"
  msg.string += "Even as his ball of fell magic bears down\non you, you can \\{1A 06 FF 00 00 01}knock it back\nwith an empty bottle\\{1A 06 FF 00 00 00}!\n\n"
  msg.string += "...I am sure you will have a shot at victory!"
  
  msg = self.bmg.messages_by_id[1590]
  msg.string = "\\{1A 05 00 00 00}! Do not run! Trust in the\n"
  msg.string += "power of the Skull Hammer!"

def add_hint_signs(self: WWRandomizer):
  # Add a hint sign to the second room of DRC with an arrow pointing to the passage to the Big Key Chest.
  new_message_id = 847
  msg = self.bmg.add_new_message(new_message_id)
  msg.string = "\\{1A 05 00 00 15}" # Right arrow
  msg.text_box_type = TextBoxType.WOOD
  msg.initial_draw_type = 1 # Instant initial message speed
  msg.text_alignment = 3 # Centered text alignment
  
  dzx = self.get_arc("files/res/Stage/M_NewD2/Room2.arc").get_file("room.dzr", DZx)
  bomb_flowers = [actor for actor in dzx.entries_by_type_and_layer(ACTR, layer=DZxLayer.Default) if actor.name == "BFlower"]
  bomb_flowers[1].name = "Kanban"
  bomb_flowers[1].params = new_message_id
  bomb_flowers[1].y_rot = 0x2000
  bomb_flowers[1].save_changes()

def prevent_door_boulder_softlocks(self: WWRandomizer):
  # DRC has a couple of doors that are blocked by boulders on one side.
  # This is an issue if the player sequence breaks and goes backwards - when they open the door Link will be stuck walking into the boulder forever and the player will have no control.
  # To avoid this, add a switch setting trigger on the back side of those doors that causes the boulder to disappear when the player touches it.
  # This allows us to keep the boulder when the player goes forward through the dungeon, but not backwards.
  
  # Add a SW_C00 (switch setting trigger region) on the other side of the first door blocked by a boulder.
  boulder_destroyed_switch_index = 5
  dzr = self.get_arc("files/res/Stage/M_NewD2/Room13.arc").get_file("room.dzr", DZx)
  swc00 = dzr.add_entity(SCOB)
  swc00.name = "SW_C00"
  swc00.params = 0x0000FF00
  swc00.switch_to_set = boulder_destroyed_switch_index
  swc00.behavior_type = 3 # Don't unset the switch when leaving the region
  swc00.x_pos = 2635
  swc00.y_pos = 0
  swc00.z_pos = 227
  swc00.x_rot = 0
  swc00.y_rot = 0xC000
  swc00.z_rot = 0xFFFF
  swc00.scale_x = 32
  swc00.scale_y = 16
  swc00.scale_z = 16
  dzr.save_changes()
  
  # Add a SW_C00 (switch setting trigger region) on the other side of the second door blocked by a boulder.
  boulder_destroyed_switch_index = 6
  dzr = self.get_arc("files/res/Stage/M_NewD2/Room14.arc").get_file("room.dzr", DZx)
  swc00 = dzr.add_entity(SCOB)
  swc00.name = "SW_C00"
  swc00.params = 0x0000FF00
  swc00.switch_to_set = boulder_destroyed_switch_index
  swc00.behavior_type = 3 # Don't unset the switch when leaving the region
  swc00.x_pos = -4002
  swc00.y_pos = 1950
  swc00.z_pos = -2156
  swc00.x_rot = 0
  swc00.y_rot = 0xA000
  swc00.z_rot = 0xFFFF
  swc00.scale_x = 32
  swc00.scale_y = 16
  swc00.scale_z = 16
  dzr.save_changes()

def update_tingle_statue_item_get_funcs(self: WWRandomizer):
  item_get_funcs_list = 0x803888C8
  
  for tingle_statue_item_id in [0xA3, 0xA4, 0xA5, 0xA6, 0xA7]:
    item_get_func_addr = item_get_funcs_list + tingle_statue_item_id*4
    item_name = self.item_names[tingle_statue_item_id]
    custom_symbol_name = item_name.lower().replace(" ", "_") + "_item_get_func"
    self.dol.write_data(fs.write_u32, item_get_func_addr, self.main_custom_symbols[custom_symbol_name])

def make_tingle_statue_reward_rupee_rainbow_colored(self: WWRandomizer):
  # Change the color index of the special 500 rupee to be 7 - this is a special value (originally unused) we use to indicate to our custom code that it's the special rupee, and so it should have its color animated.
  
  # Register the proper item name.
  self.register_renamed_item(0xB8, "Rainbow Rupee")
  
  item_resources_list_start = 0x803842B0
  
  item_id = self.item_name_to_id["Rainbow Rupee"]
  rainbow_rupee_item_resource_addr = item_resources_list_start + item_id*0x24
  
  self.dol.write_data(fs.write_u8, rainbow_rupee_item_resource_addr+0x14, 7)

def show_seed_hash_on_name_entry_screen(self: WWRandomizer):
  # Add some text to the name entry screen which has two random character names that vary based on the permalink (so the seed and settings both change it).
  # This is so two players intending to play the same seed can verify if they really are on the same seed or not.
  # Since actually adding new text to the UI would be very difficult, instead hijack the "Name Entry" text, and put the seed hash after several linebreaks.
  # (The three linebreaks we insert before "Name Entry" are so it's still in the correct spot after vertical centering happens.)
  msg = self.bmg.messages_by_id[40]
  msg.string = "\n\n\n" + msg.string + "\n\n" + "Seed hash:" + "\n" + self.seed_hash

def fix_ghost_ship_chest_crash(self: WWRandomizer):
  # There's a vanilla crash that happens if you jump attack on top of the chest in the Ghost Ship.
  # The cause of the crash is that there are unused rooms in the Ghost Ship stage with unused chests at the same position as the used chest.
  # When Link lands on top of the overlapping chests the game thinks Link is in one of the unused rooms.
  # The ky_tag0 object in the Ghost Ship checks a zone bit every frame, but checking a zone bit crashes if the current room is not loaded in because the zone was never initialized.
  # So we simply move the other two unused chests away from the real one so they're far out of bounds.
  # (Actually deleting them would mess up the entity indexes in the logic files, so it's simpler to move them.)
  
  dzs = self.get_arc("files/res/Stage/PShip/Stage.arc").get_file("stage.dzs", DZx)
  chests = dzs.entries_by_type(TRES)
  for chest in chests:
    if chest.room_num == 2:
      # The chest for room 2 is the one that is actually used, so don't move this one.
      continue
    chest.x_pos += 2000.0
    chest.save_changes()

def implement_key_bag(self: WWRandomizer):
  # Replaces the Pirate's Charm description with a description that changes dynamically depending on the dungeon keys you have.
  # To do this new text commands are implemented to show the dynamic numbers. There are 5 new commands, 0x4B to 0x4F, one for each dungeon. (Forsaken Fortress and Ganon's Tower are not included as they have no keys.)
  
  self.bmg.messages_by_id[403].string = "Key Bag"
  description = "A handy bag for holding your keys!\n"
  description += "Here's how many you've got with you:\n"
  description += "DRC: \\{1A 05 00 00 4B}    "
  description += "FW: \\{1A 05 00 00 4C}    "
  description += "TotG: \\{1A 05 00 00 4D}\n"
  description += "ET: \\{1A 05 00 00 4E}      "
  description += "WT: \\{1A 05 00 00 4F}"
  self.bmg.messages_by_id[603].string = description
  
  itemicons_arc = self.get_arc("files/res/Msg/itemicon.arc")
  pirate_charm_icon = itemicons_arc.get_file("amulet_00.bti", BTI)
  key_bag_icon_image_path = os.path.join(ASSETS_PATH, "key bag.png")
  pirate_charm_icon.replace_image_from_path(key_bag_icon_image_path)
  pirate_charm_icon.save_changes()

def prevent_fire_mountain_lava_softlock(self: WWRandomizer):
  # Sometimes when spawning from spawn ID 0 outside fire mountain, the player will get stuck in an infinite loop of taking damage from lava.
  # The reason for this is that when the player enters the sea stage, the ship is spawned in at its new game starting position (either Outset or a randomized starting island) and the player is put on the ship.
  # Then after a frame or two the ship is teleported to its proper spawn position near the island the player is supposed to be on, along with the player.
  # The game's collision detection system draws a huge line between where the player was a frame ago (starting island) and where the player is right now (whatever the correct island is, such as Fire Mountain).
  # If that collision line happens to pass through the Fire Mountain volcano, the player will be considered to be standing on the volcano for one frame.
  # Because the volcano's collision is set to have the lava attribute, this results in the player taking lava damage.
  # In order to avoid this, the Y coordinate of the ship's position when starting a new game is simply moved down to be extremely far below the ocean surface. This is so that any collision line in between it and any of the various other ship spawns will not hit anything at all.
  # This does not result in the ship actually visibly spawning far below the sea when you start a new game, because the sea actor is smart enough to instantly teleport the ship on top whenever it falls below the surface.
  
  sea_dzs = self.get_arc("files/res/Stage/sea/Stage.arc").get_file("stage.dzs", DZx)
  sea_actors = sea_dzs.entries_by_type(ACTR)
  ship_actor = next(x for x in sea_actors if x.name == "Ship")
  ship_actor.y_pos = -500000
  ship_actor.save_changes()

def add_chest_in_place_of_jabun_cutscene(self: WWRandomizer):
  # Add a chest on a raft to Jabun's cave to replace the cutscene item you would normally get there.
  
  jabun_dzr = self.get_arc("files/res/Stage/Pjavdou/Room0.arc").get_file("room.dzr", DZx)
  
  raft = jabun_dzr.add_entity(ACTR)
  raft.name = "Ikada"
  raft.y_rot = 0x8000
  
  # Turn wind on inside the cave so that the flag on the raft blows in the wind.
  # Otherwise it clips inside the flagpole and looks bad.
  room_props = jabun_dzr.entries_by_type(FILI)[0]
  room_props.wind_type = 0 # Weakest wind (0.3 strength)
  
  jabun_chest = jabun_dzr.add_entity(TRES)
  jabun_chest.name = "takara3"
  jabun_chest.params = 0xFF000000
  jabun_chest.switch_to_set = 0xFF
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
  outset_dzr = self.get_arc("files/res/Stage/sea/Room44.arc").get_file("room.dzr", DZx)
  
  layer_5_actors = outset_dzr.entries_by_type_and_layer(ACTR, layer=DZxLayer.Layer5)
  layer_5_door = next(x for x in layer_5_actors if x.name == "Ajav")
  layer_5_whirlpool = next(x for x in layer_5_actors if x.name == "Auzu")
  
  layer_none_door = outset_dzr.add_entity(ACTR)
  layer_none_door.name = layer_5_door.name
  layer_none_door.params = layer_5_door.params
  layer_none_door.x_pos = layer_5_door.x_pos
  layer_none_door.y_pos = layer_5_door.y_pos
  layer_none_door.z_pos = layer_5_door.z_pos
  layer_none_door.x_rot = layer_5_door.x_rot
  layer_none_door.y_rot = layer_5_door.y_rot
  layer_none_door.z_rot = layer_5_door.z_rot
  layer_none_door.enemy_number = layer_5_door.enemy_number
  
  layer_none_whirlpool = outset_dzr.add_entity(ACTR)
  layer_none_whirlpool.name = layer_5_whirlpool.name
  layer_none_whirlpool.params = layer_5_whirlpool.params
  layer_none_whirlpool.x_pos = layer_5_whirlpool.x_pos
  layer_none_whirlpool.y_pos = layer_5_whirlpool.y_pos
  layer_none_whirlpool.z_pos = layer_5_whirlpool.z_pos
  layer_none_whirlpool.x_rot = layer_5_whirlpool.x_rot
  layer_none_whirlpool.y_rot = layer_5_whirlpool.y_rot
  layer_none_whirlpool.z_rot = layer_5_whirlpool.z_rot
  layer_none_whirlpool.enemy_number = layer_5_whirlpool.enemy_number
  
  outset_dzr.remove_entity(layer_5_door, ACTR, layer=DZxLayer.Layer5)
  outset_dzr.remove_entity(layer_5_whirlpool, ACTR, layer=DZxLayer.Layer5)
  
  outset_dzr.save_changes()
  
  
  # Also modify the event that happens when you destroy the big stone door so that KoRL doesn't automatically enter the cave.
  event_list = self.get_arc("files/res/Stage/sea/Stage.arc").get_file("event_list.dat", EventList)
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

def add_chest_in_place_of_master_sword(self: WWRandomizer):
  # Add a chest to the Master Sword chamber that only materializes after you beat the Mighty Darknuts there.
  
  ms_chamber_dzr = self.get_arc("files/res/Stage/kenroom/Room0.arc").get_file("room.dzr", DZx)
  
  # Remove the Master Sword entities.
  ms_actors = [x for x in ms_chamber_dzr.entries_by_type_and_layer(ACTR, layer=DZxLayer.Default) if x.name in ["VmsMS", "VmsDZ"]]
  for actor in ms_actors:
    ms_chamber_dzr.remove_entity(actor, ACTR, layer=DZxLayer.Default)
  
  # Copy the entities necessary for the Mighty Darknuts fight from layer 5 to the default layer.
  layer_5_actors = ms_chamber_dzr.entries_by_type_and_layer(ACTR, layer=DZxLayer.Layer5)
  layer_5_actors_to_copy = [x for x in layer_5_actors if x.name in ["Tn", "ALLdie", "Yswdr00"]]
  
  for orig_actor in layer_5_actors_to_copy:
    new_actor = ms_chamber_dzr.add_entity(ACTR)
    new_actor.name = orig_actor.name
    new_actor.params = orig_actor.params
    new_actor.x_pos = orig_actor.x_pos
    new_actor.y_pos = orig_actor.y_pos
    new_actor.z_pos = orig_actor.z_pos
    new_actor.x_rot = orig_actor.x_rot
    new_actor.y_rot = orig_actor.y_rot
    new_actor.z_rot = orig_actor.z_rot
    new_actor.enemy_number = orig_actor.enemy_number
  
  # Remove the entities on layer 5 that are no longer necessary.
  for orig_actor in layer_5_actors:
    ms_chamber_dzr.remove_entity(orig_actor, ACTR, layer=DZxLayer.Layer5)
  
  
  # Add the chest.
  ms_chest = ms_chamber_dzr.add_entity(TRES)
  ms_chest.name = "takara3"
  ms_chest.params = 0xFF000000
  ms_chest.switch_to_set = 0xFF
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
  spawn = next(spawn for spawn in ms_chamber_dzr.entries_by_type(PLYR) if spawn.spawn_id == 10)
  spawn.y_pos = -2949.39
  spawn.z_pos = -4240.7
  
  ms_chamber_dzr.save_changes()

def update_beedle_spoil_selling_text(self: WWRandomizer):
  # Update Beedle's dialogue when you try to sell something to him so he mentions he doesn't want Blue Chu Jelly.
  msg = self.bmg.messages_by_id[3957]
  lines = msg.string.split("\n")
  lines[2] = "And no Blue Chu Jelly, either!"
  msg.string = "\n".join(lines)

def fix_totg_warp_out_spawn_pos(self: WWRandomizer):
  # Normally the spawn point used when the player teleports out after beating the dungeon boss would put the player right on top of the Hyrule warp, which takes the player there immediately if it's active.
  # Move the spawn forward a bit to avoid this.
  
  dzr = self.get_arc("files/res/Stage/sea/Room26.arc").get_file("room.dzr", DZx)
  spawn = next(x for x in dzr.entries_by_type(PLYR) if x.spawn_id == 1)
  spawn.z_pos += 1000.0
  spawn.save_changes()

def remove_phantom_ganon_requirement_from_eye_reefs(self: WWRandomizer):
  # Go through all the eye reef cannons that don't appear until you defeat Phantom Ganon and remove that switch requirement.
  
  for island_number in [24, 46, 22, 8, 37, 25]:
    eye_reef_dzr = self.get_arc("files/res/Stage/sea/Room%d.arc" % island_number).get_file("room.dzr", DZx)
    actors = eye_reef_dzr.entries_by_type(ACTR)
    cannons = [x for x in actors if x.name == "Ocanon"]
    for cannon in cannons:
      if cannon.enable_spawn_switch == 0x2A: # Switch 2A is Phantom Ganon being dead.
        cannon.enable_spawn_switch = 0xFF
        cannon.save_changes()
    gunboats = [x for x in actors if x.name == "Oship"]
    for gunboat in gunboats:
      if (gunboat.x_rot & 0xFF) == 0x2A: # Switch 2A is Phantom Ganon being dead.
        gunboat.x_rot = (gunboat.x_rot & 0xFF00) | 0xFF
        gunboat.save_changes()

def test_room(self: WWRandomizer):
  patcher.apply_patch(self, "test_room")
  
  stage_name_ptr = self.main_custom_symbols["test_room_stage_name"]
  room_index_ptr = self.main_custom_symbols["test_room_room_index"]
  spawn_id_ptr = self.main_custom_symbols["test_room_spawn_id"]
  
  self.dol.write_data(fs.write_str, stage_name_ptr, self.test_room_args["stage"], 8)
  self.dol.write_data(fs.write_u8, room_index_ptr, self.test_room_args["room"])
  self.dol.write_data(fs.write_u8, spawn_id_ptr, self.test_room_args["spawn"])

def fix_forsaken_fortress_door_softlock(self: WWRandomizer):
  # Fix a bug where entering Forsaken Fortress via the left half of the big door on the second floor (the one you'd normally only exit from and not go back through) would softlock the game.
  # Because of the changes to Link's pushing animation (see increase_block_moving_animation), entering via the left half doesn't make Link walk as far into the door as entering via the right half does.
  # As a result, Link will wind up a couple units short of standing on top of the collision triangles that have an exit index set, softlocking the game because a transition never occurs, but the door animation never ends either.
  # To fix this, we simply make one more collision triangle have the property with an exit index set, so that Link doesn't need to go as far inside the door for the transition to happen.
  
  face_index = 0x1493
  new_property_index = 0x11
  
  ff_dzb = self.get_arc("files/res/Stage/sea/Room1.arc").get_file_entry("room.dzb")
  ff_dzb.decompress_data_if_necessary()
  face_list_offset = fs.read_u32(ff_dzb.data, 0xC)
  face_offset = face_list_offset + face_index*0xA
  fs.write_u16(ff_dzb.data, face_offset+6, new_property_index)

def add_new_bog_warp(self: WWRandomizer):
  # Adds a new Ballad of Gales warp point destination to Forsaken Fortress.
  # To do this we must relocate the lists with data for each warp to free space, modify the code to use the relocated lists, and modify the code to loop the number of times counting the new warp, instead of only the vanilla number of times.
  # We also must add a new message for the confirmation dialog to display when the player selects the Forsaken Fortress warp.
  # (Note that the actual warp spawn point in Forsaken Fortress already existed in the vanilla game unused, so we don't need to add that, it already works perfectly.)
  
  new_num_warps = 10
  
  # Update the pointers to the warp table in various pieces of code to point to a custom one.
  custom_warp_table_address = self.main_custom_symbols["ballad_of_gales_warp_table"]
  high_halfword, low_halfword = patcher.split_pointer_into_high_and_low_half_for_hardcoding(custom_warp_table_address)
  for code_address in [0x801B96DC, 0x801B96F0, 0x801B9790]:
    self.dol.write_data(fs.write_u16, code_address+2, high_halfword)
    self.dol.write_data(fs.write_u16, code_address+6, low_halfword)
  
  # Update the pointers to the float bank of X/Y positions for the warp icons to point to a custom one.
  custom_warp_float_bank_address = self.main_custom_symbols["ballad_of_gales_warp_float_bank"]
  high_halfword, low_halfword = patcher.split_pointer_into_high_and_low_half_for_hardcoding(custom_warp_float_bank_address)
  for code_address in [0x801B9360, 0x801B7C28]:
    self.dol.write_data(fs.write_u16, code_address+2, high_halfword)
    self.dol.write_data(fs.write_u16, code_address+6, low_halfword)
  
  # Update the offsets relative to the float bank symbol since they're all going to be completely different in the custom float bank compared to the original one.
  self.dol.write_data(fs.write_u16, 0x801B7C3C+2, 0) # Reading X positions in dMenu_Fmap_c::init_warpMode
  self.dol.write_data(fs.write_u16, 0x801B7C44+2, new_num_warps*4) # Reading Y positions in dMenu_Fmap_c::init_warpMode
  self.dol.write_data(fs.write_u16, 0x801B9378+2, 0) # Reading X positions in dMenu_Fmap_c::warpAreaAnime0
  self.dol.write_data(fs.write_u16, 0x801B9380+2, new_num_warps*4) # Reading Y positions in dMenu_Fmap_c::warpAreaAnime0
  self.dol.write_data(fs.write_u16, 0x801B93A4+2, new_num_warps*2*4) # Reading unknown value in dMenu_Fmap_c::warpAreaAnime0
  self.dol.write_data(fs.write_u16, 0x801B93C8+2, new_num_warps*2*4 + 4) # Reading unknown value in dMenu_Fmap_c::warpAreaAnime0
  
  # These handle displaying the spinning warp icons on the warp select screen.
  self.dol.write_data(fs.write_u16, 0x801B7988+2, new_num_warps) # dMenu_Fmap_c::_open_warpMode
  self.dol.write_data(fs.write_u16, 0x801B7C80+2, new_num_warps) # dMenu_Fmap_c::init_warpMode
  
  # These handle moving the cursor on the currently selected warp on the warp select screen.
  # They also seem to handle deleting the spinning warp icons when you exit the screen.
  self.dol.write_data(fs.write_u16, 0x801B8414+2, new_num_warps) # dMenu_Fmap_c::wrapMove
  self.dol.write_data(fs.write_u16, 0x801B84D0+2, new_num_warps) # dMenu_Fmap_c::wrapMove
  
  # Necessary for the 10th warp to work correctly.
  self.dol.write_data(fs.write_u16, 0x801B979C+2, new_num_warps) # dMenu_Fmap_c::getWarpAreaTablePtr
  
  # Handles something when you open the warp select screen.
  self.dol.write_data(fs.write_u16, 0x801B6E6C+2, new_num_warps) # dMenu_Fmap_c::paneTranceZoomMap
  
  # Handles something when you cancel a warp at the confirmation prompt.
  self.dol.write_data(fs.write_u16, 0x801B9020+2, new_num_warps) # dMenu_Fmap_c::wrapSelWinFadeOut
  
  # Handles something when you confirm a warp at the confirmation prompt.
  self.dol.write_data(fs.write_u16, 0x801B9230+2, new_num_warps) # dMenu_Fmap_c::wrapSelWarp
  
  # Handles highlighting the currently selected warp icon.
  self.dol.write_data(fs.write_u16, 0x801B936C+2, new_num_warps) # dMenu_Fmap_c::warpAreaAnime0
  
  # Note: The place in memory that stores pointers to the spinning warp icon particle emitter seems to have room for 12 warps total. So we could theoretically add 3 new warps without issue instead of just 1. But any more than that won't work.
  # Example of code dealing with this list: 801BA0F4 stores the emitter pointer to that list.
  
  # Add a new message for the text in the confirmation dialog when selecting the new warp.
  msg = self.bmg.add_new_message(848)
  msg.string = "Warp to \\{1A 06 FF 00 00 01}Forsaken Fortress\\{1A 06 FF 00 00 00}?"
  msg.text_box_type = TextBoxType.DIALOG
  msg.initial_draw_type = 1 # Instant message speed
  msg.text_box_position = 2 # Centered
  msg.num_lines_per_box = 2

def make_rat_holes_visible_from_behind(self: WWRandomizer):
  # Change the cull mode on the rat hole model from backface culling to none.
  # This is so the hole is visible from behind in enemy rando.
  data = self.get_arc("files/res/Object/Nzg.arc").get_file_entry("kana_00.bdl").data
  fs.write_u32(data, 0xC80, 0x00) # Change cull mode in the MAT3 section
  fs.write_u8(data, 0xFCE, 0x04) # Change cull mode in the MDL3 section

def enable_developer_mode(self: WWRandomizer):
  # This enables the developer mode left in the game's code.
  
  self.dol.write_data(fs.write_u8, 0x803F60E0, 1) # mDoMain::developmentMode(void)

def enable_heap_display(self: WWRandomizer):
  # Enables the heap display left in the game's code for viewing how much memory is free in real time.
  
  boot_data = self.get_raw_file("sys/boot.bin")
  
  # Change a variable in the ISO header to allow the heap display to be used.
  fs.write_u8(boot_data, 0x07, 0x91)
  
  # Default the heap display to on when booting up the game so it doesn't need to be toggled on with R+Z on controller 3.
  self.dol.write_data(fs.write_u8, 0x800063E7, 1) # Hardcoded default value for mDisplayHeapSize (in func main01)
  
  # Default tab of the heap display to 1 instead of 4 so it doesn't need to be changed with L+Z on controller 3.
  self.dol.write_data(fs.write_u8, 0x803F60E8, 1) # mHeapBriefType
  
  # Remove a check that a controller must be connected to port 3 for the heap display to be shown.
  self.dol.write_data(fs.write_u32, 0x800084A0, 0x60000000) # nop (in mDoGph_AfterOfDraw)

def add_failsafe_id_0_spawns(self: WWRandomizer):
  # Add spawns with spawn ID 0 to any rooms that didn't originally have them.
  # This is so anything that assumes all rooms have a spawn with ID 0 (for example, Floormasters that don't have an explicit exit set for when they capture you) doesn't crash the game.
  
  # For rooms that already had a spawn in them, copy the existing spawn.
  spawns_to_copy = [
    ("Asoko", 0, 255),
    ("I_TestM", 0, 1),
    ("M_Dai", 20, 23),
    ("M_NewD2", 1, 20),
    ("M_NewD2", 2, 1),
    ("M_NewD2", 3, 6),
    ("M_NewD2", 4, 7),
    ("M_NewD2", 6, 9),
    ("M_NewD2", 8, 14),
    ("M_NewD2", 11, 2),
    ("M_NewD2", 12, 3),
    ("M_NewD2", 13, 4),
    ("M_NewD2", 14, 5),
    ("M_NewD2", 15, 18),
    ("TF_06", 1, 1),
    ("TF_06", 2, 2),
    ("TF_06", 3, 2),
    ("TF_06", 4, 2),
    ("TF_06", 5, 2),
    ("TF_06", 6, 6),
    ("ma2room", 1, 2),
    ("ma2room", 2, 15), # Front door
    ("ma2room", 3, 9), # In the water
    ("ma2room", 4, 6),
    ("ma3room", 1, 2),
    ("ma3room", 2, 15), # Front door
    ("ma3room", 3, 9), # In the water
    ("ma3room", 4, 6),
    ("majroom", 1, 2),
    ("majroom", 2, 15), # Front door
    ("majroom", 3, 9), # In the water
    ("majroom", 4, 6),
  ]
  
  for stage_name, room_number, spawn_id_to_copy in spawns_to_copy:
    dzr = self.get_arc("files/res/Stage/%s/Room%d.arc" % (stage_name, room_number)).get_file("room.dzr", DZx)
    spawns = dzr.entries_by_type(PLYR)
    spawn_to_copy = next(spawn for spawn in spawns if spawn.spawn_id == spawn_id_to_copy)
    
    new_spawn = dzr.add_entity(PLYR)
    new_spawn.spawn_type = spawn_to_copy.spawn_type
    new_spawn.room_num = spawn_to_copy.room_num
    new_spawn.x_pos = spawn_to_copy.x_pos
    new_spawn.y_pos = spawn_to_copy.y_pos
    new_spawn.z_pos = spawn_to_copy.z_pos
    new_spawn.y_rot = spawn_to_copy.y_rot
    new_spawn.spawn_id = 0
    
    dzr.save_changes()
  
  # For rooms that didn't have any existing spawn in them, add a new spawn, automatically placed in front of a door.
  rooms_to_add_new_spawns_to = [
    ("TF_01", 1),
    ("TF_01", 2),
    ("TF_01", 3),
    ("TF_01", 4),
    ("TF_01", 5),
    ("TF_01", 6),
    ("TF_02", 1),
    ("TF_02", 2),
    ("TF_02", 3),
    ("TF_02", 4),
    ("TF_02", 5),
    ("TF_02", 6),
  ]
  
  for stage_name, room_number in rooms_to_add_new_spawns_to:
    dzr = self.get_arc("files/res/Stage/%s/Room%d.arc" % (stage_name, room_number)).get_file("room.dzr", DZx)
    spawns = dzr.entries_by_type(PLYR)
        
    dzs = self.get_arc("files/res/Stage/%s/Stage.arc" % stage_name).get_file("stage.dzs", DZx)
    doors = dzs.entries_by_type(TGDR)
    spawn_dist_from_door = 200
    x_pos = None
    y_pos = None
    z_pos = None
    y_rot = None
    for door in doors:
      assert door.actor_class_name == "d_a_door10"
      if door.from_room_num == room_number or door.to_room_num == room_number:
        y_rot = door.y_rot
        if door.from_room_num != room_number:
          y_rot = (y_rot + 0x8000) % 0x10000
        y_rot_degrees = y_rot * (90.0 / 0x4000)
        x_offset = math.sin(math.radians(y_rot_degrees)) * spawn_dist_from_door
        z_offset = math.cos(math.radians(y_rot_degrees)) * spawn_dist_from_door
        x_pos = door.x_pos + x_offset
        y_pos = door.y_pos
        z_pos = door.z_pos + z_offset
        break
    
    new_spawn = dzr.add_entity(PLYR)
    new_spawn.spawn_type = 0
    new_spawn.room_num = room_number
    new_spawn.x_pos = x_pos
    new_spawn.y_pos = y_pos
    new_spawn.z_pos = z_pos
    new_spawn.y_rot = y_rot
    new_spawn.spawn_id = 0
    
    dzr.save_changes()

def add_spawns_outside_boss_doors(self: WWRandomizer):
  """Creates new spawns in dungeons for use when exiting the boss doors."""
  
  rooms_to_add_new_spawns_to = [
    ("M_NewD2", 10, TGDR, None, "door20"),
    ("kindan", 16, TGDR, None, "door20"), # Already has a spawn, ID 1.
    ("Siren", 18, TGDR, None, "door20"),
    ("sea", 1, ACTR, 1, "SMBdor"),
    ("M_Dai", 15, TGDR, None, "door12"),
    ("kaze", 12, TGDR, None, "door12"),
  ]
  
  for stage_name, room_number, chunk, layer, door_name in rooms_to_add_new_spawns_to:
    new_spawn_id = 27
    
    dzs = self.get_arc("files/res/Stage/%s/Stage.arc" % stage_name).get_file("stage.dzs", DZx)
    dzr = self.get_arc("files/res/Stage/%s/Room%d.arc" % (stage_name, room_number)).get_file("room.dzr", DZx)
    
    if chunk == TGDR:
      dzx_for_door = dzs
    else:
      dzx_for_door = dzr
    
    doors = [
      actor for actor in dzx_for_door.entries_by_type_and_layer(chunk, layer=layer)
      if actor.name == door_name
      and (door_name == "SMBdor" or actor.from_room_num == actor.to_room_num == room_number)
    ]
    assert len(doors) == 1
    door = doors[0]
    
    spawn_dist_from_door = 200
    y_rot = door.y_rot
    if door.from_room_num != room_number and door.from_room_num != 63:
      y_rot = (y_rot + 0x8000) % 0x10000
    y_rot_degrees = y_rot * (90.0 / 0x4000)
    x_offset = math.sin(math.radians(y_rot_degrees)) * spawn_dist_from_door
    z_offset = math.cos(math.radians(y_rot_degrees)) * spawn_dist_from_door
    x_pos = door.x_pos + x_offset
    y_pos = door.y_pos
    z_pos = door.z_pos + z_offset
    
    if stage_name in ["M_Dai", "kaze"]:
      # Earth and Wind temple spawns must be in the stage instead of the room or the game will crash.
      dzx_for_spawn = dzs
    else:
      dzx_for_spawn = dzr
    
    spawns = dzx_for_spawn.entries_by_type(PLYR)
    assert len([spawn for spawn in spawns if spawn.spawn_id == new_spawn_id]) == 0
    
    new_spawn = dzx_for_spawn.add_entity(PLYR)
    new_spawn.spawn_type = 0
    new_spawn.room_num = room_number
    new_spawn.x_pos = x_pos
    new_spawn.y_pos = y_pos
    new_spawn.z_pos = z_pos
    new_spawn.y_rot = y_rot
    new_spawn.spawn_id = new_spawn_id
    if stage_name == "sea":
      new_spawn.ship_id = 0
    
    dzx_for_spawn.save_changes()

def remove_minor_panning_cutscenes(self: WWRandomizer):
  panning_cutscenes = [
    ("M_NewD2", "Room2", 4),
    ("kindan", "Stage", 2),
    ("Siren", "Room18", 2),
    ("M_Dai", "Room3", 7),
    ("sea", "Room41", 19),
    ("sea", "Room41", 22),
    ("sea", "Room41", 23),
  ]
  
  for stage_name, arc_name, evnt_index in panning_cutscenes:
    arc = self.get_arc("files/res/Stage/%s/%s.arc" % (stage_name, arc_name))
    if arc_name == "Stage":
      dzx = arc.get_file("stage.dzs", DZx)
    else:
      dzx = arc.get_file("room.dzr", DZx)
    
    tagevs = [x for x in dzx.entries_by_type(SCOB) if x.name == "TagEv"]
    for tagev in tagevs:
      if tagev.evnt_index == evnt_index:
        dzx.remove_entity(tagev, SCOB)
    
    spawns = dzx.entries_by_type(PLYR)
    for spawn in spawns:
      if spawn.evnt_index == evnt_index:
        spawn.evnt_index = 0xFF
        spawn.save_changes()

def add_custom_actor_rels(self: WWRandomizer):
  # Add the custom switch operator REL to the game.
  rel_path = os.path.join(ASM_PATH, "d_a_switch_op.rel")
  rel = REL()
  rel.read_from_file(rel_path)
  self.add_new_rel(
    "files/rels/d_a_switch_op.rel",
    rel,
    section_index_of_actor_profile = 2,
    offset_of_actor_profile = 0,
  )
  
  rel_path = os.path.join(ASM_PATH, "d_a_dungeon_flag_sw.rel")
  rel = REL()
  rel.read_from_file(rel_path)
  self.add_new_rel(
    "files/rels/d_a_dungeon_flag_sw.rel",
    rel,
    section_index_of_actor_profile = 4,
    offset_of_actor_profile = 0x20,
  )
  
  # Replace the vanilla treasure chest actor with a modified one.
  # Includes trap chest functionality and the shortened opening cutscene.
  elf_path = os.path.join(ASM_PATH, "d_a_tbox.plf")
  rel_path = "files/rels/d_a_tbox.rel"
  self.replace_rel_from_elf(elf_path, rel_path, "g_profile_TBOX")

def fix_message_closing_sound_on_quest_status_screen(self: WWRandomizer):
  # Fix an issue where the message box closing sound effect would play when opening the quest status pause screen.
  # This issue is caused by the "Options" button on the quest status screen trying to use message ID 704 for its description when you select it, but there is no message with ID 704, so it returns the last message (the message with the highest index) instead.
  # If that last message has a Textbox Style of one of: Dialog, Special, Hint, or Wind Waker Song, and the message displays instantly in a single frame, then it would open and close on the frame the quest status screen is loading, causing that sound to be played.
  # To fix this we simply add a blank message with ID 704 and give it a textbox style that isn't affected by the issue.
  
  msg = self.bmg.add_new_message(704)
  msg.string = ""
  msg.text_box_type = TextBoxType.ITEM_GET

def fix_stone_head_bugs(self: WWRandomizer):
  # Unset the actor status bit for stone heads that makes them not execute on frames where they didn't draw because they weren't in view of the camera.
  # The fact that they don't execute when you're not looking at them can cause various bugs.
  # One of which is that, for the ones that spawn enemies, they set themselves as being enemy-type actors. They only delete themselves after the enemy they spawn is killed and not at the moment the stone head actually breaks. So in "kill all enemies" rooms, you would need to look at the empty spot where the stone head broke apart after killing the enemy it spawned in order for all "enemies" to be considered dead.
  
  head_rel = self.get_rel("files/rels/d_a_obj_homen.rel")
  
  status_bits = head_rel.read_data(fs.read_u32, 0x3450)
  status_bits &= ~0x00000080
  head_rel.write_data(fs.write_u32, 0x3450, status_bits)

def show_number_of_tingle_statues_on_quest_status_screen(self: WWRandomizer):
  # Replaces the visuals of the treasure chart counter on the quest status screen with visuals for a tingle statue counter.
  # That chart counter is redundant since it shows the same number on the chart screen.
  # (The actual counter number itself is modified via asm.)
  
  # Replace the treasure chart item icon on the quest screen with the tingle statue icon.
  self.dol.write_data(fs.write_str, 0x8035F469, "tingle_figure.bti", 0x13)
  
  # Update the "Treasure Chart" text at the bottom of the screen.
  msg = self.bmg.messages_by_id[503]
  msg.string = "Tingle Statues"
  
  # Update the treasure chart description with custom text for tingle statues.
  msg = self.bmg.messages_by_id[703]
  msg.string = (
    "Golden statues of a mysterious dashing figure. "
    "They can be traded to \\{1A 06 FF 00 00 01}Ankle\\{1A 06 FF 00 00 00} on \\{1A 06 FF 00 00 01}Tingle Island\\{1A 06 FF 00 00 00} for a reward!"
  )
  msg.word_wrap_string(self.bfn)

def add_shortcut_warps_into_dungeons(self: WWRandomizer):
  # Add shortcut warps to more quickly re-enter dungeons from the shore after you've already entered them once.
  
  fh_entrance_touched_switch = 0x7F # This switch on the sea should be unused in the vanilla game.
  fh_entrance_scls_exit_index = 6
  
  fh_dzr = self.get_arc("files/res/Stage/sea/Room41.arc").get_file("room.dzr", DZx)
  
  # Add a white light beam warp to the shore of Forest Haven that takes you into the dungeon.
  # This is disabled at first, it becomes active after a switch is set when you've entered the dungeon once normally.
  # (Looks kinda weird since the model doesn't reach all the way up to the sky. Scaling it scales the model, but not the cull box.)
  # This will take the player into whatever the entrance is randomized to lead to, not just Forbidden Woods.
  warp = fh_dzr.add_entity(SCOB)
  warp.name = "Ysdls00"
  warp.type = 1 # White warp
  warp.activation_switch = fh_entrance_touched_switch
  warp.exit_index = fh_entrance_scls_exit_index
  warp.activated_event_index = 0xFF
  warp.x_pos = 217178.1
  warp.y_pos = 34.99997
  warp.z_pos = 195407.7
  
  # Add a SW_C00 (switch setting trigger region) around the entrance to the dungeon.
  # This will set the switch when the player enters the dungeon, enabling the warp for later use.
  swc00 = fh_dzr.add_entity(SCOB)
  swc00.name = "SW_C00"
  swc00.switch_to_set = fh_entrance_touched_switch
  swc00.behavior_type = 3 # Don't unset the switch when leaving the region
  swc00.prerequisite_switch = 0xFF
  swc00.x_pos = 196755.7
  swc00.y_pos = 2952.929
  swc00.z_pos = 198147.1
  swc00.scale_x = 3 * 0x10
  swc00.scale_y = 3 * 0x10
  swc00.scale_z = 3 * 0x10
  
  fh_dzr.save_changes()

def replace_dark_wood_chest_texture(self: WWRandomizer):
  # Replaces the texture of the dark wood chest texture with a custom texture based on the Big Key chest texture.
  # This is used when chest type matches its contents and dungeon keys are placed into dark wood chests.
  # It can be challenging to distinguish light wood from dark wood chests, so this custom texture is used instead.
  # We use the color palette of the Big Key chest to create the association with this chest type and dungeon keys.
  
  dark_wood_chest_arc = self.get_arc("files/res/Object/Dalways.arc")
  dark_wood_chest_model = dark_wood_chest_arc.get_file("boxb.bdl", BDL)
  dark_wood_chest_tex_image = dark_wood_chest_model.tex1.textures_by_name["Ktakara_001"][0]
  dark_wood_chest_tex_image.replace_image_from_path(os.path.join(ASSETS_PATH, "key chest.png"))
  dark_wood_chest_model.save()

def fix_needle_rock_island_salvage_flags(self: WWRandomizer):
  # Salvage flags 0 and 1 for Needle Rock Island are each duplicated in the vanilla game.
  # There are two light ring salvages, using flags 0 and 1.
  # There are three gunboat salvages, using flags 0, 1, and 2. 2 is for the golden gunboat.
  # This causes a bug where you can't get all of these sunken treasures if you salvage the light
  # rings first, or if you salvage the gunboats first and then reload the room.
  # So we have to change the flags used by the two light ring salvages so that they don't conflict
  # with the two non-golden gunboat salvages.
  
  nri_dzr = self.get_arc("files/res/Stage/sea/Room29.arc").get_file("room.dzr", DZx)
  salvages = [
    actor for actor in nri_dzr.entries_by_type(SCOB)
    if DataTables.actor_name_to_class_name[actor.name] == "d_a_salvage"
    and actor.salvage_type in [2, 3, 4]
    and actor.salvage_flag in [0, 1]
  ]
  
  salvages[0].salvage_flag = 8 # Unused in vanilla
  salvages[0].save_changes()
  salvages[1].salvage_flag = 9 # Unused in vanilla
  salvages[1].save_changes()

def switches_are_contiguous(switches):
  return sorted(switches) == list(range(min(switches), max(switches)+1))

def allow_nonlinear_servants_of_the_towers(self: WWRandomizer):
  # Allow the sections of Tower of the Gods where you bring three Servants of the Tower into the
  # hub room to be done nonlinearly, so you can return the servants in any order.
  # We change it so the Command Melody tablet appears when any one of the three servants is
  # returned (originally it would only appear when returning the east servant).
  # We also change the final warp upwards to appear only after all three servants have been
  # returned, *and* the item from the Command Melody tablet has been obtained (since that tablet
  # would softlock the game if it was still there when you try to enter the warp).
  # However, the various events for the servants being returned do not behave well with these
  # modifications. So we will need to substantially edit these events.
  
  totg = self.get_arc("files/res/Stage/Siren/Stage.arc").get_file("stage.dzs", DZx)
  event_list: EventList = self.get_arc("files/res/Stage/Siren/Stage.arc").get_file("event_list.dat", EventList)
  hub_room_dzr = self.get_arc("files/res/Stage/Siren/Room7.arc").get_file("room.dzr", DZx)
  
  doors = totg.entries_by_type(TGDR)
  north_door = doors[6]
  west_door = doors[8]
  
  # Remove the open condition switches from the doors, making them unlocked from the start.
  north_door.switch_1 = 0xFF
  west_door.switch_1 = 0xFF
  
  # Note: In vanilla, 0x29 was not set directly by the east servant.
  # Instead, the east servant's event caused the tablet to appear, and then after getting
  # the Command Melody from the tablet, the tablet would set switch 0x29.
  # We change the east servant to work like the others, and directly set the switch.
  east_servant_returned_switch = 0x29
  west_servant_returned_switch = 0x2A
  north_servant_returned_switch = 0x28
  
  # These switches should be unused in vanilla TotG.
  tablet_item_obtained_switch = 0x2B # Must be contiguous with 0x28-0x2A.
  any_servant_returned_switch = 0x7E
  all_servants_returned_switch = 0x7F
  
  original_all_servants_returned_switch = 0x28
  
  # In vanilla, the tablet and the east servant both had their switch set to 0x29.
  # The east servant would start an event that makes the tablet appear, and then after you
  # get the Command Melody from the tablet, the tablet would set switch 0x29.
  # The east servant would check for switch 0x29 to be set, and once it is, start another
  # event where it tells you about its kin and makes the tablet disappear.
  
  # We change how this works so that the east servant sets switch 0x29 in its event.
  # Then we have a custom event that triggers when any of the three servant returned
  # switches have been set. This custom event makes the tablet appear.
  # The switch set by the tablet when you get its item is changed to 0x2B (unused in vanilla).
  # Once all four switches are set, the light beam warp appears.
  
  tablet = next(x for x in hub_room_dzr.entries_by_type(ACTR) if x.name == "Hsh")
  tablet.switch_to_set = tablet_item_obtained_switch
  beam_warp = next(x for x in hub_room_dzr.entries_by_type(ACTR) if x.name == "Ywarp00")
  beam_warp.activation_switch = all_servants_returned_switch
  weather_trigger = next(x for x in hub_room_dzr.entries_by_type(SCOB) if x.name == "kytag00")
  weather_trigger.switch_to_check = all_servants_returned_switch
  attn_tag = next(
    x for x in hub_room_dzr.entries_by_type(SCOB)
    if x.name == "AttTag"
    and x.switch_to_check == original_all_servants_returned_switch
    and x.type == 1
  )
  attn_tag.switch_to_check = all_servants_returned_switch
  
  # East servant returned.
  # Make this servant set its switch directly, instead of making the Command Melody tablet appear
  # and then having the tablet set the switch.
  os0_finish = event_list.events_by_name["Os_Finish"]
  os0 = next(actor for actor in os0_finish.actors if actor.name == "Os")
  tablet = next(actor for actor in os0_finish.actors if actor.name == "Hsh")
  timekeeper = next(actor for actor in os0_finish.actors if actor.name == "TIMEKEEPER")
  camera = next(actor for actor in os0_finish.actors if actor.name == "CAMERA")
  # Set the switch.
  set_switch_action = os0.add_action("SW_ON")
  os0.actions.remove(set_switch_action)
  os0.actions.insert(7, set_switch_action)
  # Remove the tablet.
  os0_finish.actors.remove(tablet)
  # Do not make the other actors wait for the tablet.
  os0.actions[-1].starting_flags[0] = -1
  timekeeper.actions[-2].starting_flags[0] = -1
  camera.actions[6].starting_flags[0] = -1
  # Remove the final countdown and wait, they won't be used for anything.
  timekeeper.actions.remove(timekeeper.actions[-1])
  timekeeper.actions.remove(timekeeper.actions[-1])
  # Adjust the camera angle so the beam doesn't pierce the camera.
  os0_unitrans = camera.actions[3]
  eye_prop = next(prop for prop in os0_unitrans.properties if prop.name == "Eye")
  eye_prop.value = (546.0, 719.0, -8789.0)
  center_prop = next(prop for prop in os0_unitrans.properties if prop.name == "Center")
  center_prop.value = (783.0, 582.0, -9085.0)
  # Do not make the camera look at the tablet appearing.
  camera_tablet_pause_act = camera.actions[7]
  camera_tablet_fixedfrm_act = camera.actions[6]
  camera_tablet_fixedfrm_props = []
  for prop in camera_tablet_fixedfrm_act.properties:
    camera_tablet_fixedfrm_props.append((prop.name, prop.value))
  camera.actions.remove(camera_tablet_pause_act)
  camera.actions.remove(camera_tablet_fixedfrm_act)
  # Make it shoot a light beam.
  finish_action = next(act for act in os0.actions if act.name == "FINISH")
  finish_type_prop = next(prop for prop in finish_action.properties if prop.name == "Type")
  finish_type_prop.value = 2
  
  # West servant returned.
  os1_finish = event_list.events_by_name["Os1_Finish"]
  os1 = next(actor for actor in os1_finish.actors if actor.name == "Os1")
  camera = next(actor for actor in os1_finish.actors if actor.name == "CAMERA")
  # Make it shoot a light beam.
  finish_actions = [act for act in os1.actions if act.name == "FINISH"]
  finish_type_prop = next(prop for prop in finish_actions[1].properties if prop.name == "Type")
  finish_type_prop.value = 2
  # Adjust the camera angle so the beam doesn't pierce the camera.
  os1_unitrans = camera.actions[3]
  os1_cam_eye = (-512.0, 626.0, -8775.0)
  os1_cam_center = (-790.0, 667.0, -9065.0)
  eye_prop = next(prop for prop in os1_unitrans.properties if prop.name == "Eye")
  eye_prop.value = os1_cam_eye
  center_prop = next(prop for prop in os1_unitrans.properties if prop.name == "Center")
  center_prop.value = os1_cam_center
  # Remove the camera zooming in on the north door.
  camera = next(actor for actor in os1_finish.actors if actor.name == "CAMERA")
  camera.actions.remove(camera.actions[-2])
  os1.actions.remove(os1.actions[-1])
  os1_finish.ending_flags[0] = os1.actions[-1].flag_id_to_set
  # Don't make it wait for the countdown before shooting the beam.
  # Instead make it wait for the camera zooming in on the servant.
  os1.actions.remove(finish_actions[0])
  camera_unitrans = camera.actions[-2]
  finish_actions[1].starting_flags[0] = camera_unitrans.flag_id_to_set
  
  # After west servant returned.
  os1_message = event_list.events_by_name["Os1_Message"]
  os1 = next(actor for actor in os1_message.actors if actor.name == "Os1")
  camera = next(actor for actor in os1_message.actors if actor.name == "CAMERA")
  # Remove all but the last action to effectively remove the event.
  os1.actions = os1.actions[-1:]
  camera.actions = camera.actions[-1:]
  
  # North servant returned.
  os2_finish = event_list.events_by_name["Os2_Finish"]
  os0 = next(actor for actor in os2_finish.actors if actor.name == "Os")
  os1 = next(actor for actor in os2_finish.actors if actor.name == "Os1")
  os2 = next(actor for actor in os2_finish.actors if actor.name == "Os2")
  camera = next(actor for actor in os2_finish.actors if actor.name == "CAMERA")
  # Remove the east and west servants from being a part of this event.
  os2_finish.actors.remove(os0)
  os2_finish.actors.remove(os1)
  # Do not make the north servant wait for the east servant to finish before it ends the event.
  os2_sw_on = next(act for act in os2.actions if act.name == "SW_ON")
  os2_sw_on.starting_flags[0] = -1
  # Do not make the camera wait for the west servant to finish before it ends the event.
  camera.actions[-1].starting_flags[0] = -1
  # Do not make the camera look at the east and west servants.
  camera.actions.remove(camera.actions[-3])
  camera.actions.remove(camera.actions[-2])
  # Adjust the camera angle while the camera is following the platform and the servant up.
  # Normally it would adjust the angle after the platform is fully up, but we just skip a step.
  os2_unitrans = camera.actions[3]
  os2_cam_eye = (124.0, 589.0, -9482.0)
  os2_cam_center = (-7.0, 644.0, -9625.0)
  eye_prop = next(prop for prop in os2_unitrans.properties if prop.name == "Eye")
  eye_prop.value = os2_cam_eye
  center_prop = next(prop for prop in os2_unitrans.properties if prop.name == "Center")
  center_prop.value = os2_cam_center
  # Remove the third unitrans, which is when the original event adjusted the camera angle.
  camera.actions.remove(camera.actions[-1])
  camera.actions.remove(camera.actions[-1])
  # And don't make the beam shooting action depend on the deleted unitrans.
  # Instead make it wait for the camera zooming in on the servant.
  finish_actions = [act for act in os2.actions if act.name == "FINISH"]
  os2.actions.remove(finish_actions[0])
  camera_unitrans = camera.actions[-1]
  finish_actions[1].starting_flags[0] = camera_unitrans.flag_id_to_set
  
  # Tablet event where you play the Command Melody and get an item.
  hsehi1_tact = event_list.events_by_name["hsehi1_tact"]
  camera = next(actor for actor in hsehi1_tact.actors if actor.name == "CAMERA")
  hsh = next(actor for actor in hsehi1_tact.actors if actor.name == "Hsh")
  timekeeper = next(actor for actor in hsehi1_tact.actors if actor.name == "TIMEKEEPER")
  link = next(actor for actor in hsehi1_tact.actors if actor.name == "Link")
  # Remove the camera zooming in on the west door.
  camera.actions.remove(camera.actions[-1])
  # Don't make the tablet wait for the camera to zoom in on the west door.
  hsh.actions.remove(hsh.actions[-1])
  # Make the tablet disappear at the end.
  hsh.actions.remove(hsh.actions[-1])
  tablet_hide_player_act = hsh.add_action("Disp", properties=[
    ("target", "@PLAYER"),
    ("disp", "off"),
  ])
  tablet_delete_action = hsh.add_action("Delete")
  # Make the camera zoom in on the tablet while it's disappearing.
  camera_fixedfrm = camera.add_action("FIXEDFRM", properties=[
    ("Eye", (3.314825, 690.2266, -8600.536)),
    ("Center", (0.82259, 677.7084, -8721.426)),
    ("Fovy", 60.0),
    ("Timer", 30),
  ])
  link_get_song_action = link.actions[4] # 059get_dance
  camera_fixedfrm.starting_flags[0] = link_get_song_action.flag_id_to_set
  tablet_delete_action.starting_flags[0] = camera_fixedfrm.flag_id_to_set
  tablet_show_player_act = hsh.add_action("Disp", properties=[
    ("target", "@PLAYER"),
    ("disp", "on"),
  ])
  hsh.add_action("WAIT")
  hsehi1_tact.ending_flags[0] = hsh.actions[-1].flag_id_to_set
  
  # Create the custom event that causes the Command Melody tablet to appear.
  appear_event = event_list.add_event("hsehi1_appear")
  
  camera = appear_event.add_actor("CAMERA")
  camera.staff_type = 2
  
  tablet_actor = appear_event.add_actor("Hsh")
  tablet_actor.staff_type = 0
  tablet_wait_action = tablet_actor.add_action("WAIT")
  
  # Make sure Link still animates during the event instead of freezing.
  link = appear_event.add_actor("Link")
  link.staff_type = 0
  link.add_action("001n_wait")
  
  timekeeper = appear_event.add_actor("TIMEKEEPER")
  timekeeper.staff_type = 4
  timekeeper.add_action("WAIT")
  
  camera_fixedfrm_action = camera.add_action("FIXEDFRM", properties=camera_tablet_fixedfrm_props)
  
  camera.add_action("PAUSE")
  
  tablet_appear_action = tablet_actor.add_action("Appear")
  tablet_appear_action.starting_flags[0] = camera_fixedfrm_action.flag_id_to_set
  
  timekeeper_countdown_90_action = timekeeper.add_action("COUNTDOWN", properties=[
    ("Timer", 90)
  ])
  timekeeper_countdown_90_action.duplicate_id = 1
  timekeeper_countdown_90_action.starting_flags[0] = tablet_appear_action.flag_id_to_set
  
  tablet_wait_action = tablet_actor.add_action("WAIT")
  tablet_wait_action.duplicate_id = 1
  tablet_wait_action.starting_flags[0] = timekeeper_countdown_90_action.flag_id_to_set
  
  appear_event.ending_flags[0] = tablet_wait_action.flag_id_to_set
  
  tablet_appear_evnt = totg.add_entity(EVNT)
  tablet_appear_evnt.name = appear_event.name
  tablet_appear_evnt_index = totg.entries_by_type(EVNT).index(tablet_appear_evnt)
  
  
  # Detect when any servant has been returned and start the tablet event.
  servants_returned_switches = [
    east_servant_returned_switch,
    west_servant_returned_switch,
    north_servant_returned_switch,
  ]
  assert switches_are_contiguous(servants_returned_switches)
  sw_op = hub_room_dzr.add_entity(ACTR)
  sw_op.name = "SwOp"
  sw_op.operation = 2 # OR
  sw_op.is_continuous = 0
  sw_op.num_switches_to_check = len(servants_returned_switches)
  sw_op.first_switch_to_check = min(servants_returned_switches)
  sw_op.switch_to_set = any_servant_returned_switch
  sw_op.evnt_index = tablet_appear_evnt_index
  sw_op.x_pos = -800
  sw_op.y_pos = 1000
  sw_op.z_pos = -9000
  
  # Detect when all servants have been returned and the tablet item is also obtained,
  # and make the warp appear.
  servants_returned_and_tablet_obtained_switches = [
    east_servant_returned_switch,
    west_servant_returned_switch,
    north_servant_returned_switch,
    tablet_item_obtained_switch,
  ]
  assert switches_are_contiguous(servants_returned_and_tablet_obtained_switches)
  sw_op = hub_room_dzr.add_entity(ACTR)
  sw_op.name = "SwOp"
  sw_op.operation = 0 # AND
  sw_op.is_continuous = 0
  sw_op.num_switches_to_check = len(servants_returned_and_tablet_obtained_switches)
  sw_op.first_switch_to_check = min(servants_returned_and_tablet_obtained_switches)
  sw_op.switch_to_set = all_servants_returned_switch
  sw_op.evnt_index = 0xFF
  sw_op.x_pos = 800
  sw_op.y_pos = 1000
  sw_op.z_pos = -9000
  
  # Also add these SwOps to all four events, with a dummy action.
  # This is so their code still runs during these events, allowing them to seamlessly
  # start events, instead of having a janky one or two frame delay where the camera
  # tries to zoom back to the player before realizing it needs to go to the tablet.
  for event in [os0_finish, os1_finish, os2_finish, hsehi1_tact]:
    swop_actor = event.add_actor("SwOp")
    swop_actor.add_action("DUMMY")
  
  
  # Also speed up the events where the servants walk to their respective platforms.
  # They're so slow that it's painful to watch, so we give them a big speed boost.
  servant_speed_multiplier = 4
  platform_speed_multiplier = 2
  beam_delay_multiplier = 2
  for finish_event in [os0_finish, os1_finish, os2_finish]:
    servant = next(actor for actor in finish_event.actors if actor.name in ["Os", "Os1", "Os2"])
    platform = next(actor for actor in finish_event.actors if actor.name in ["Hdai1", "Hdai2", "Hdai3"])
    timekeeper = next(actor for actor in finish_event.actors if actor.name == "TIMEKEEPER")
    camera = next(actor for actor in finish_event.actors if actor.name == "CAMERA")
    
    servant_move_action = next(act for act in servant.actions if act.name == "MOVE")
    stick_prop = next(prop for prop in servant_move_action.properties if prop.name == "Stick")
    stick_prop.value *= servant_speed_multiplier # Originally 0.5
    
    platform_move_action = next(act for act in platform.actions if act.name == "MOVE")
    speed_prop = next(prop for prop in platform_move_action.properties if prop.name == "Speed")
    speed_prop.value *= platform_speed_multiplier # Originally 2.5
    
    countdown_actions = [act for act in timekeeper.actions if act.name == "COUNTDOWN"]
    countdown_timer_props = [
      next(prop for prop in countdown_action.properties if prop.name == "Timer")
      for countdown_action in countdown_actions
    ]
    countdown_timer_props[0].value //= servant_speed_multiplier # Originally 60 frames (2s)
    countdown_timer_props[1].value //= servant_speed_multiplier # Originally 210 frames (7s)
    # countdown_timer_props[2] is 10 frames
    countdown_timer_props[3].value //= beam_delay_multiplier # Originally 60 frames (2s)
    
    unitrans_actions = [act for act in camera.actions if act.name == "UNITRANS"]
    unitrans_timer_props = [
      next(prop for prop in unitrans_action.properties if prop.name == "Timer")
      for unitrans_action in unitrans_actions
    ]
    unitrans_timer_props[0].value //= platform_speed_multiplier # Originally 90 frames (3s)
    # unitrans_timer_props[1] is 30 frames
  
  
  hub_room_dzr.save_changes()
  totg.save_changes()

def fix_helmaroc_king_table_softlock(self: WWRandomizer):
  # When doing the speedrun strat to trick Helmaroc King into landing inside of the tower and attacking
  # you, he could sometimes land on top of the small wooden table in there, which seems to have a
  # small chance of causing him to clip out of bounds and fall into the void forever.
  # Simply remove this table, as this should presumably fix the bug, and the table seems to serve no
  # purpose anyway (the two stools beside it don't appear during the fight to begin with).
  fftower_dzr = self.get_arc("files/res/Stage/M2tower/Room0.arc").get_file("room.dzr", DZx)
  actors = fftower_dzr.entries_by_type_and_layer(ACTR, layer=DZxLayer.Default)
  table = next(x for x in actors if x.name == "Otble")
  fftower_dzr.remove_entity(table, ACTR)

def make_dungeon_joy_pendant_locations_flexible(self: WWRandomizer):
  # There's a purple rupee in the first room of DRC that appears when you use a Tingle Bomb on a
  # crack with steam coming out of it.
  # This purple rupee shares the same item pickup flag (0x06) as one of the joy pendants much later
  # in DRC. Obtaining one of these two items makes the other one unobtainable, which could result in
  # an unbeatable seed if the player gets the purple rupee first.
  # To fix this, we give the purple rupee a different item pickup flag that was originally unused.
  dzr = self.get_arc("files/res/Stage/M_NewD2/Room0.arc").get_file("room.dzr", DZx)
  tingle_item = dzr.entries_by_type_and_layer(ACTR, layer=DZxLayer.Default)[0x1C]
  tingle_item.item_pickup_flag = 0x16 # Unused item pickup flag for Dragon Roost Cavern
  tingle_item.save_changes()
  
  # One of the pots that drops a joy pendant in FW doesn't have an item pickup flag set, meaning the
  # item placed here can be obtained multiple times. This was presumably unintentional as all the
  # other dungeon joy pendants have pickup flags, so we give it a new flag.
  dzr = self.get_arc("files/res/Stage/kindan/Room7.arc").get_file("room.dzr", DZx)
  pot = dzr.entries_by_type_and_layer(ACTR, layer=DZxLayer.Default)[0xE0]
  pot.item_pickup_flag = 0x16 # Unused item pickup flag for Forbidden Woods
  pot.save_changes()
  
  # The stone heads that drop joy pendants have dan bit switches for staying destroyed until you
  # leave and re-enter this dungeon. These switches get set when the stone heads are destroyed, not
  # when the items are collected. This can make it look like you're softlocked if you exit the room
  # after destroying the stone head without picking up the item and then come back.
  # To avoid this, we remove the destroyed switch from the stone heads so that they always reappear.
  dzr = self.get_arc("files/res/Stage/kaze/Room1.arc").get_file("room.dzr", DZx)
  stone_head = dzr.entries_by_type_and_layer(ACTR, layer=DZxLayer.Default)[0x10]
  stone_head.destroyed_switch = 0xFF
  stone_head.save_changes()
  dzr = self.get_arc("files/res/Stage/kaze/Room7.arc").get_file("room.dzr", DZx)
  stone_head = dzr.entries_by_type_and_layer(ACTR, layer=DZxLayer.Default)[0x2E]
  stone_head.destroyed_switch = 0xFF
  stone_head.save_changes()

def prevent_fairy_island_softlocks(self: WWRandomizer):
  # If the player somehow managed to get inside Western Fairy Island's Fairy Fountain without
  # properly solving the puzzle to open the entrance up (e.g. with glitches), then the ring of
  # flames would still be present in front of the pit. Because the ring of flames is so large, it
  # would immediately damage the player as soon as they come back up from the pit, knocking them
  # back in the pit. Under normal circumstances a softlock can be avoided here by saving and
  # reloading inside the Fairy Fountain to be placed back outside the ring of flames, but in
  # entrance randomizer, dungeons will place you back at the beginning of the dungeon, and escaping
  # can be impossible.
  # To fix this, we move the spawn coming out of the pit on Western Fairy Island back a bit so you
  # just barely don't get hit by the ring of flames. Then, you can save and reload while standing
  # behind the flames to be placed outside of them.
  wfi_dzr = self.get_arc("files/res/Stage/sea/Room15.arc").get_file("room.dzr", DZx)
  spawn = next(spawn for spawn in wfi_dzr.entries_by_type(PLYR) if spawn.spawn_id == 1)
  spawn.x_pos = -320170.0
  spawn.save_changes()

def give_fairy_fountains_distinct_colors(self: WWRandomizer):
  stage_groups = [
    ["Fairy01", "Fairy02", "Fairy03", "Fairy04", "Fairy05", "Fairy06"],
  ]
  
  for stage_group in stage_groups:
    hue = 0
    for stage_name in stage_group:
      dzs = self.get_arc(f"files/res/Stage/{stage_name}/Stage.arc").get_file("stage.dzs", DZx)
      
      for pale in dzs.entries_by_type(Pale):
        for color in [pale.bg0_c0, pale.bg0_k0]:
          h, s, v = colorsys.rgb_to_hsv(color.r/255, color.g/255, color.b/255)
          h = hue
          r, g, b = colorsys.hsv_to_rgb(h, s, v)
          color.r, color.g, color.b = int(r*255), int(g*255), int(b*255)
      
      hue += 1.0 / len(stage_group)
      dzs.save_changes()

def add_trap_chest_event_to_stage(self: WWRandomizer, stage_name: str):
  # Add the event DEFAULT_TREASURE_TRAP to the given stage. Necessary for trap chests to function.
  stage_path = "files/res/Stage/{}/Stage.arc".format(stage_name)
  event_list: EventList = self.get_arc(stage_path).get_file("event_list.dat", EventList)
  
  if "DEFAULT_TREASURE_TRAP" in event_list.events_by_name:
    return
  
  trap_event = event_list.add_event("DEFAULT_TREASURE_TRAP")
  
  # Create treasure chest actor
  chest_actor = trap_event.add_actor("TREASURE")
  chest_actor.staff_type = 0
  
  chest_actor.add_action("OPEN_SHORT")
  chest_actor.add_action("SPRING_TRAP")
  chest_actor.add_action("WAIT")
  
  # Create timekeeper actor
  timekeeper_actor = trap_event.add_actor("TIMEKEEPER")
  timekeeper_actor.staff_type = 4
  
  timekeeper_actor.add_action("WAIT")
  
  # Create Link actor
  link_actor = trap_event.add_actor("Link")
  link_actor.staff_type = 0
  
  linke_open_treasure_action = link_actor.add_action("010open_treasure", properties=[
    ("prm0", 1)
  ])
  link_actor.add_action("057rd_stop")
  
  # Create dependent actions between Link and the timekeeper
  timekeeper_countdown_action = timekeeper_actor.add_action("COUNTDOWN", properties=[
    ("Timer", 92)
  ])
  timekeeper_countdown_action.starting_flags[0] = linke_open_treasure_action.flag_id_to_set
  
  link_surprise_action = link_actor.add_action("024surprised")
  link_surprise_action.starting_flags[0] = timekeeper_countdown_action.flag_id_to_set
  
  # Create camera actor
  camera_actor = trap_event.add_actor("CAMERA")
  camera_actor.staff_type = 2
  
  camera_actor.add_action("PAUSE")
  
  # Add ending flag to event
  trap_event.ending_flags[0] = link_surprise_action.flag_id_to_set

def enable_hero_mode(self: WWRandomizer):
  patcher.apply_patch(self, "hero_mode")
  
  multiplier_addr = self.main_custom_symbols["damage_multiplier"]
  self.dol.write_data(fs.write_float, multiplier_addr, 4.0)

def set_default_targeting_mode_to_switch(self: WWRandomizer):
  targeting_mode_addr = self.main_custom_symbols["option_targeting_mode"]
  self.dol.write_data(fs.write_u8, targeting_mode_addr, 1)
