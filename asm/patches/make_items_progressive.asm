
; This patch modifies the game's code to make certain items progressive, so even if you get them out of order, they will always be upgraded, never downgraded.
; (Note that most of the modifications for this are in the make_items_progressive function of tweaks.py, not here.)


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
.org 0x8B8
  bl convert_progressive_item_id_for_shop_item
.close




; Fix a big where buying a progressive item from the shop would not show the item get animation if it's the tier 2+ item.
.open "files/rels/d_a_npc_bs1.rel"
.org 0x1D00
  ; For the Bait Bag slot.
  bl custom_getSelectItemNo_progressive
.org 0x1F3C
  ; For the 3 Rock Spire Shop Ship slots.
  bl custom_getSelectItemNo_progressive
.close
