# Can't use logic's PROGRESS_ITEMS because we don't want all items
# to be accessible early and remove too much fun
# And also because progressive items require special handling
INVENTORY_ITEMS = [
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
] + ["Progressive Bow"]      * 3 + \
    ["Progressive Wallet"]   * 2

# Not sure how the Progressive Bomb Bag and Quiver play with their
# respective items themselves so to be safe they aren't supported yet. 