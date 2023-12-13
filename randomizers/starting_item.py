import typing
from logic.item_types import DUNGEON_PROGRESS_ITEMS

from randomizers.base_randomizer import BaseRandomizer
import tweaks

DISALLOWED_RANDOM_STARTING_ITEMS = set([
  # There's a separate option for number of starting triforce shards that we'd need to mess with
  # It's also 8 items and would have a fairly large impact on the seed, so we'd probably want
  # to weigh it less than other items if allowed
  "Triforce Shards",
  # Other items that you can't start with in the UI, but we allow anyway:
  # "Treasure Charts", "Triforce Charts" # These seem to work fine to start with, even if not very fun
  # "Tingle Statues", # seem to work fine
  # "Boat's Sail", "Wind Waker", "Wind's Requiem" # Mandatory starting items
  # "Empty Bottle", # Can only start with one Empty Bottle from the UI, but seems to work ok with more
  # DUNGEON_PROGRESS_ITEMS # Seem to work fine at least in keylunacy (enforced below)
])

DELIVERY_BAG_ITEMS = set([
  "Note to Mom",
  "Maggie's Letter",
  "Moblin's Letter",
  "Cabana Deed",
])

class StartingItemRandomizer(BaseRandomizer):

  def __init__(self, rando):
    super().__init__(rando)
    self.random_starting_items = []

  def is_enabled(self) -> bool:
    return (
      self.rando.items.is_enabled() and
      self.options.get("num_random_starting_items", 0) > 0
    )

  def _randomize(self):
    initial_sphere_0_checks = self.logic.get_accessible_remaining_locations(for_progression=True)
    items_to_place = self.options.get("num_random_starting_items")
    for remaining_random_starting_items in range(items_to_place, 0, -1):
      max_fraction = remaining_random_starting_items
      if len(self.logic.get_accessible_remaining_locations(for_progression=True)) > len(initial_sphere_0_checks):
        # If we've already unlocked at least one check, we can use any items for the remaining slots
        # We still want to avoid completely useless ones though (f.ex dungeon items for non-race-mode dungeons)
        max_fraction = 9998
      available_items = self.filter_possible_random_starting_items(max_fraction)

      if len(available_items) == 0:
        break

      selected = self.rng.choice(available_items)

      if selected in ("Treasure Chart", "Triforce Chart"):
        chart_usefulness = self.logic.get_items_by_usefulness_fraction(self.logic.treasure_chart_names + self.logic.triforce_chart_names)
        selected = self.rng.choice([
          chart for chart in self.logic.unplaced_progress_items
          if chart.startswith(selected) and chart in chart_usefulness and chart_usefulness[chart] <= max_fraction
        ])

      # Sync the added items back to the other lists:
      self.logic.add_owned_item_or_item_group(selected)
      self.random_starting_items.append(selected)
      # Do *not* add it to the base starting items list, as it would mess up the
      # hints since they'd start with a different set of starting items when
      # demoting some progress items to nonprogress.
      # Eg big octos with a starting boomerang would make the quiver foolish,
      # which is (maybe?) confusing and would lead you to never check octos
      # self.rando.starting_items.extend(self.logic.expand_item_groups([selected]))

    # Confirm that we opened at least one new check if we assigned an item
    if self.random_starting_items and len(self.logic.get_accessible_remaining_locations(for_progression=True)) <= len(initial_sphere_0_checks):
      # This would indicate a logic bug, the filtering above should prevent it
      raise Exception("Random starting items didn't unlock at least one check")
      
  def filter_possible_random_starting_items(self, max_fraction: int) -> list[str]:
    items_by_usefulness = self.logic.get_items_by_usefulness_fraction(self.logic.get_flattened_unplaced_progression_items())
    # Since we assign items in groups all at once, add back in synthetic items with the group names
    available_items: set[str] = set()
    for item, fraction in items_by_usefulness.items():
      group_name = next(
        (group for group, group_items in self.logic.progress_item_groups.items() 
         if item in group_items),
        None
      )
      # However we only want to merge the group if all the items are progression
      # (specifically for pearls where Farore's can be useful without the
      # others being progression)
      if (
        group_name and 
        all((item in self.logic.get_flattened_unplaced_progression_items()) for item in self.logic.progress_item_groups[group_name])
      ):
        item = group_name
        fraction = min((items_by_usefulness[item]) for item in self.logic.progress_item_groups[group_name])
        fraction -= (len(self.logic.progress_item_groups[group_name]) - 1)

      if fraction <= max_fraction:
        available_items.add(item)

    available_items -= DISALLOWED_RANDOM_STARTING_ITEMS
    if not "Delivery Bag" in self.logic.currently_owned_items:
      # Delivery bag is the only bag that can hold progression items, and we
      # don't want to give a progression item if we don't have its bag since
      # it's impossible to see the item until you get delivery bag in that case
      available_items -= DELIVERY_BAG_ITEMS
    if not self.options.get("keylunacy"):
      available_items -= set(DUNGEON_PROGRESS_ITEMS)

    # To avoid treasure charts overwhelming everything when enabled, group them so they have the same weight as any other item
    if set(self.logic.treasure_chart_names).intersection(available_items):
        available_items -= set(self.logic.treasure_chart_names)
        available_items.add('Treasure Chart')
    if set(self.logic.triforce_chart_names).intersection(available_items):
        available_items -= set(self.logic.triforce_chart_names)
        available_items.add('Triforce Chart')

    # If sword_mode is No Starting Sword, adding swords would desync the
    # sword_mode option from the actual number of swords.
    # Swordless doesn't put the Progressive Swords in the progress items in the
    # first place so doesn't need this
    # This might be removable if we can make a random starting progressive sword
    # automatically change the sword_mode variable and its consequences
    if self.options.get("sword_mode") == "No Starting Sword" and "Progressive Sword" in available_items:
      available_items.remove("Progressive Sword")

    # We need to sort before converting to lists because sets have per-process hash seeding
    # and could otherwise lead to different randomization between processes with the same seed
    return sorted(available_items)

  def _save(self):
    # This tweak is written in an idempotent way, so this should be ok to
    # call a second time when this randomizer is enabled
    tweaks.update_starting_gear(
      self.rando,
      self.options.get("starting_gear") + self.logic.expand_item_groups(self.random_starting_items)
    )

  def write_to_spoiler_log(self) -> str:
    if self.random_starting_items:
      return f"Random starting item: {', '.join(self.random_starting_items)}\n\n"
    else:
      return ""