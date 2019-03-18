# Can't use logic's PROGRESS_ITEMS because we don't want all items
# to be accessible early and remove too much fun
# And also because progressive items require special handling
REGULAR_ITEMS = [
  "Telescope",
  "Magic Armor",
  "Hero's Charm",
  "Grappling Hook",
  "Power Bracelets",
  "Iron Boots",
  "Boomerang",
  "Hookshot",
  "Bombs",
  "Skull Hammer",
  "Deku Leaf",
  "Mirror Shield",
  "Hurricane Spin",
]

PROGRESSIVE_ITEMS = \
    ["Progressive Bow"]       * 3 + \
    ["Progressive Quiver"]    * 2 + \
    ["Progressive Bomb Bag"]  * 2 + \
    ["Progressive Wallet"]    * 2 + \
    ["Progressive Picto Box"] * 2

INVENTORY_ITEMS = REGULAR_ITEMS + PROGRESSIVE_ITEMS
# Not sure how the Progressive Bomb Bag and Quiver play with their
# respective items themselves so to be safe they aren't supported yet.
