# Can't use logic's PROGRESS_ITEMS because there's some items
# that we can't start with
# And also because progressive items require special handling
REGULAR_ITEMS = [
  "Telescope",
  "Magic Armor",
  "Hero's Charm",
  "Tingle Tuner",
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
  "Din's Pearl",
  "Farore's Pearl",
  "Nayru's Pearl",
  "Command Melody",
  "Earth God's Lyric",
  "Wind God's Aria",
] + ["Empty Bottle"] * 4
REGULAR_ITEMS.sort()

PROGRESSIVE_ITEMS = \
    ["Progressive Bow"]       * 3 + \
    ["Progressive Quiver"]    * 2 + \
    ["Progressive Bomb Bag"]  * 2 + \
    ["Progressive Wallet"]    * 2 + \
    ["Progressive Picto Box"] * 2 + \
    ["Progressive Sword"]     * 3
PROGRESSIVE_ITEMS.sort()

INVENTORY_ITEMS = REGULAR_ITEMS + PROGRESSIVE_ITEMS
