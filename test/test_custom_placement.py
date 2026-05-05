"""
Tests for the custom item placement feature.
Ensures that items assigned to specific locations are correctly placed and do not violate item pool constraints.
"""

import os
import pytest
from wwrando import make_argparser
from randomizer import WWRandomizer
from options.wwrando_options import Options
from test.test_dry import dry_rando_with_options


def test_custom_item_placement_hookshot():
    options = Options()
    # Ensure Hookshot is in randomized_gear
    assert "Hookshot" in options.randomized_gear

    # Pick a location.
    location = "Outset Island - Underneath Link's House"
    item = "Hookshot"

    options.custom_item_locations = {location: item}

    rando = dry_rando_with_options(options)
    rando.randomize_all()

    # Verify it's in the requested location
    assert rando.logic.done_item_locations[location] == item

    # Verify it's NOT in any other location
    found_count = 0
    for loc, placed_item in rando.logic.done_item_locations.items():
        if placed_item == item:
            found_count += 1
            assert loc == location, f"Item {item} was found at unexpected location {loc}"

    assert found_count == 1, f"Item {item} should be found exactly once, but was found {found_count} times"


def test_custom_item_placement_multiple():
    options = Options()

    # Progressive Sword usually has 3 copies in the pool
    item = "Progressive Sword"
    sword_count = options.randomized_gear.count(item)
    assert sword_count >= 2

    loc1 = "Outset Island - Underneath Link's House"
    loc2 = "Outset Island - Mesa the Grasscutter's House"

    options.custom_item_locations = {
        loc1: item,
        loc2: item
    }

    rando = dry_rando_with_options(options)
    rando.randomize_all()

    assert rando.logic.done_item_locations[loc1] == item
    assert rando.logic.done_item_locations[loc2] == item

    # Check total count of item in all locations
    total_placed = list(rando.logic.done_item_locations.values()).count(item)
    assert total_placed == sword_count, f"Expected {sword_count} {item} to be placed, but found {total_placed}"


def test_custom_item_placement_and_starting_gear():
    options = Options()

    # Put one Progressive Sword in starting gear
    options.starting_gear = ["Progressive Sword"]
    options.randomized_gear.remove("Progressive Sword")

    item = "Progressive Sword"
    sword_count_in_pool = options.randomized_gear.count(item)

    loc = "Outset Island - Underneath Link's House"
    options.custom_item_locations = {loc: item}

    rando = dry_rando_with_options(options)
    rando.randomize_all()

    assert rando.logic.done_item_locations[loc] == item

    # Check total count in pool
    total_placed = list(rando.logic.done_item_locations.values()).count(item)
    assert total_placed == sword_count_in_pool


def test_custom_item_placement_non_progress_item():
    options = Options()

    # Telescope is usually randomized if not starting gear.
    # By default it is randomized.
    item = "Telescope"
    assert item in options.randomized_gear

    location = "Outset Island - Underneath Link's House"
    options.custom_item_locations = {location: item}

    rando = dry_rando_with_options(options)
    rando.randomize_all()

    assert rando.logic.done_item_locations[location] == item
