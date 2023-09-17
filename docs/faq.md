---
search:
  boost: 0.5
---

# Frequently Asked Questions

## Help, I'm stuck! I can't find the item I need, am I softlocked?

You're probably not softlocked if you're running the latest official release of the randomizer (currently version {{ rando_version }}) without any other mods or cheats applied on top of it.  

You should first check the spoiler log for your seed to find out where the next item you need was placed. It might be somewhere you forgot to check.  
The spoiler log is a text file in the same folder as your randomized ISO, it tells you the randomized locations of items for your seed.  

If you still can't figure it out, try reading the rest of this FAQ. There are some common pitfalls related to obscure game interactions covered here that you might not be aware of, even if you've beaten vanilla Wind Waker before.  

If you're sure that you're stuck, you should double check if you have any cheat codes or mods enabled besides the official version of Wind Waker Randomizer. For example, the "Full Nintendo Gallery" cheat code that comes with Dolphin is known to cause numerous issues.

If you're sure that you're stuck *and* that you aren't using anything else that modifies the game, it's possible that you encountered a bug in the randomizer.  
Please report the details of the bug on [the issue tracker](https://github.com/LagoLunatic/wwrando/issues) and be sure to include the permalink (found in the spoiler and non-spoiler logs) in your report.

## The randomizer program won't run.

If you get an error that says `Failed to execute script wwrando`, or if the randomizer executable completely vanishes when you try to launch it, then your antivirus software may be assuming that the randomizer is a virus because it hasn't seen the program before.

To fix this, you will need to go into your antivirus software's settings and add an exception/exclusion to let it know the randomizer executable is safe.  
The specifics of how to do this depend on which antivirus software you use, so if you don't know how to, you may want to search the internet for help on using your antivirus software.

## How can I get across magma pools?

Other than using the Grappling Hook or Deku Leaf to go over the magma like normal, you can also shoot an Ice Arrow directly at the surface of the magma to temporarily freeze it, allowing you to walk on top of it safely.

In some places, you can also cross magma pools by using the Hookshot to latch onto something on the other side.

## How can I destroy the mounted cannons on Lookout Platforms?

Besides blowing them up with your ship's cannon or bombs, you can also destroy mounted cannons with the Boomerang.

## How can I destroy big boulders?

Besides blowing them up with bombs, you can also destroy big boulders by lifting them up with Power Bracelets and throwing them.

## Why didn't the Bomb Bag give me Bombs?

In Wind Waker, Bomb Bag upgrades do not actually give you any bombs to use by themselves, they only increase your carrying capacity.

To use bombs, you must first find the item literally named "Bombs".

Once you do, any increases to carrying capacity from Bomb Bags you already obtained will be carried over.

## I found bait/letters/spoils, but I don't have a bag to hold them.

You can't use bait without the Bait Bag, deliver letters without the Delivery Bag, or trade spoils without the Spoils Bag.

But if you find any of those items before obtaining the bags, they won't be lost! Whenever you find the corresponding bag, everything you found earlier will already be in there.

## How do I get the reward for the mail sorting minigame?

You need to complete the minigame 4 separate times to get this item.  

The first time you must reach a score of at least 10, then 20 the second time, and 25 the third time.  
After the third time, you should leave the room and then go back in. The Rito who was originally running the minigame, Koboli, will now be replaced with a Hylian, Baito.  
Complete the minigame a fourth time, again achieving a score of at least 25, and you will be given the randomized item.  

## Where are all the cutscenes?

Most of the game's cutscenes have been cut out for the randomizer, and some of the ones that remain have been sped up.

This is partially because watching the cutscenes can feel slow and repetitive if you've already played the game before.

But the reason there is no option to add cutscenes back in for those that want them is because many cutscenes were not coded in a way that works well when the game is in an open world state. Many of them would crash or behave strangely if not removed.

If you want to experience The Wind Waker's story, it is recommended to play the vanilla game before the randomizer. The randomizer is intended to add replayability for people who have already beaten the game.

## The game freezes when I take a pictograph.

You are most likely using RetroArch or a legacy version of Dolphin. These emulators are very old and sometimes crash when playing Wind Waker (both the vanilla game and the randomizer).

It is recommended that you play on a recent *beta or development* build of Dolphin, which can be downloaded from [here](https://en.dolphin-emu.org/download/).

## The game crashes after the GameCube boot up animation.

On Dolphin, the GameCube animation isn't compatible with the randomizer and will crash.

It should already be disabled by default, but if you have previously enabled the animation in Dolphin's settings you should disable it by going to Config &rarr; GameCube in Dolphin and checking the "Skip Main Menu" option.

## Can you complete the Nintendo Gallery?

Not currently. You can potentially obtain most figurines in the game depending on how late you find the Deluxe Picto Box, but a small number of characters such as Tetra simply do not appear anywhere in the current version of the randomizer, so you can't obtain their figurines.
