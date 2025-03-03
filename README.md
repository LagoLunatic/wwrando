
# Wind Waker Randomizer

This is a randomizer for The Legend of Zelda: The Wind Waker.  
It randomizes all the items in the game so that each playthrough is unique and you never know where a particular item will be.  
It also makes the game completely open world from the start, removes most cutscenes from the game, and increases sailing speed and text speed.

If you're new here, check out the official website for details on how to get started playing: https://lagolunatic.github.io/wwrando/

Or you can download the randomizer here: https://github.com/LagoLunatic/wwrando/releases/latest

## Information

The randomizer only supports the North American GameCube version of Wind Waker. (MD5: d8e4d45af2032a081a0f446384e9261b)  
The European and Japanese versions of Wind Waker won't work, and neither will Wind Waker HD.

The randomizer guarantees that every playthrough will be completable, and that you don't need to use any glitches or tricks to beat it.

All items are randomized, but because Wind Waker is such a large game, a single run of it would take a very long time if you had to check every single location. Therefore the randomizer has options to limit where progress items can appear based on the type of the location.  
For example, you can limit progress items to appearing in dungeons and secret caves only, or secret caves sidequests and mail, or any other combination you want.  
Location types that you don't select will only have unimportant items that you don't need to beat the game - like rupees, heart pieces, bomb bag upgrades, etc. So you can skip checking them entirely, unless you want some of those optional items.

### Randomizer won't launch?

If the randomizer gives an error saying "Failed to execute script wwrando", or if the executable disappears before you can launch it, then your antivirus software may be incorrectly detecting the randomizer as malware. You should add an exception/exclusion for the randomizer into your antivirus software so that it will ignore the randomizer if this happens.

### Got stuck in a seed?

If you seem to be stuck and can't find anywhere to progress, you should first read the Frequently Asked Questions page on the official website: https://lagolunatic.github.io/wwrando/faq/  

If you've read the FAQ and consulted the spoiler log but you're still stuck, it's possible you've encountered a bug in the randomizer.  
Please report bugs like that here: https://github.com/LagoLunatic/wwrando/issues  
In the bug report be sure to include the permalink for the seed you encountered the bug on.  

## Discord Server

If you have any questions or are looking for people to play/race with, why not join the official Wind Waker Randomizer Discord server?  
https://discord.gg/r2963mt

## Credits

The randomizer was created and programmed by LagoLunatic, with help from:  
Aelire (additional programming)  
CryZe (event flag documentation)  
EthanArmbrust (Mac and Linux support)  
Fig (additional programming)  
Gamma / SageOfMirrors (custom model conversion, file format documentation, additional programming)  
Hypatia (textures)  
JarheadHME (additional programming)  
LordNed (file format documentation)  
MelonSpeedruns (game design suggestions, graphic design)  
nbouteme (starting items programming)  
tanjo3 (CTMC and hint programming)  
TrogWW (additional programming)  
wooferzfg (additional programming)  

## Running the randomizer from source

If you want to run the latest development version of the randomizer from source, follow the instructions below.  
Note that this is only recommended for advanced users or those interested in helping develop the randomizer.  

Download and install git from here: https://git-scm.com/downloads  
Then clone this repository with git by running this in a command prompt:  
`git clone --recurse-submodules https://github.com/LagoLunatic/wwrando.git`  

Download and install Python 3.12 from here: https://www.python.org/downloads/release/python-3121/  
"Windows installer (64-bit)" is the one you want if you're on Windows, "macOS 64-bit universal2 installer" if you're on Mac.  
If you're on Linux, run this command instead: `sudo apt-get install python3.12`  

Open the wwrando folder in a command prompt and install dependencies by running:  
`py -3.12 -m pip install -r requirements.txt` (on Windows)  
`python3 -m pip install -r requirements.txt` (on Mac)  
`python3 -m pip install -r requirements.txt --user` (on Linux)  

Then run the randomizer with:  
`py -3.12 wwrando.py` (on Windows)  
`python3 wwrando.py` (on Mac)  
`python3 wwrando.py` (on Linux)  

Optionally, you can also install `requirements_full.txt` with the same process you used for `requirements.txt` above.  
`requirements_full.txt` will install additional libraries that speed up texture recoloring, as well as for building a distributable version of the randomizer. You can still run the randomizer from source without these.  

If you are on Windows 8 or below, use `requirements_qt5.txt`/`requirements_qt5_full.txt` instead of the normal requirements files.  
