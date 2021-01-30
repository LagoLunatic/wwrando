# Can't use logic's PROGRESS_ITEMS because there's some items that we can't start with, and also because progressive items require special handling.
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
  "Hurricane Spin",
  "Din's Pearl",
  "Farore's Pearl",
  "Nayru's Pearl",
  "Command Melody",
  "Earth God's Lyric",
  "Wind God's Aria",
  "Spoils Bag",
  "Bait Bag",
  "Delivery Bag",
  "Note to Mom",
  "Maggie's Letter",
  "Moblin's Letter",
  "Cabana Deed",
  "Ghost Ship Chart",
  "Empty Bottle",
  "Magic Meter Upgrade",
]
REGULAR_ITEMS.sort()

PROGRESSIVE_ITEMS = \
  ["Progressive Bow"]       * 3 + \
  ["Progressive Quiver"]    * 2 + \
  ["Progressive Bomb Bag"]  * 2 + \
  ["Progressive Wallet"]    * 2 + \
  ["Progressive Picto Box"] * 2 + \
  ["Progressive Sword"]     * 3 + \
  ["Progressive Shield"]    * 2
PROGRESSIVE_ITEMS.sort()

INVENTORY_ITEMS = REGULAR_ITEMS + PROGRESSIVE_ITEMS

DEFAULT_STARTING_ITEMS = [
  "Progressive Shield",
]

DEFAULT_RANDOMIZED_ITEMS = INVENTORY_ITEMS.copy()
for item_name in DEFAULT_STARTING_ITEMS:
  DEFAULT_RANDOMIZED_ITEMS.remove(item_name)
