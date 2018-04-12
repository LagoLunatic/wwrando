
import os
from io import BytesIO

from fs_helpers import *
from rarc import RARC

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
  write_u32(ship_data, 0x29EC, 0x48000064) # b 0x80F2EA90
  # Second is the check for whether you've gotten Farore's Pearl. Make this branch unconditional too.
  write_u32(ship_data, 0x2A08, 0x48000048) # b 0x80F2EA90
  # Third is the check for whether you have the Master Sword. Again make the branch unconditional.
  write_u32(ship_data, 0x2A24, 0x48000010) # b 0x80F2EA74
  
  # Skip the check for if you've seen the Dragon Roost Island intro which prevents you from getting in the King of Red Lions.
  write_u32(ship_data, 0xB2D8, 0x48000018)

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
