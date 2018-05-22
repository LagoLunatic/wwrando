
from collections import OrderedDict

OPTIONS = OrderedDict([
  ("progression_dungeons", "This controls whether dungeons can contain progress items.\nIf this is not checked, dungeons will only contain optional items you don't need to beat the game."),
  ("progression_secret_caves", "This controls whether secret caves can contain progress items.\nIf this is not checked, secret caves will only contain optional items you don't need to beat the game."),
  ("progression_sidequests", "This controls whether sidequests can reward progress items.\nIf this is not checked, sidequests will only reward optional items you don't need to beat the game."),
  ("progression_minigames", "This controls whether minigames can reward progress items.\nIf this is not checked, minigames will only reward optional items you don't need to beat the game."),
  ("progression_platforms_rafts", "This controls whether lookout platforms and rafts can contain progress items.\nIf this is not checked, lookout platforms and rafts will only contain optional items you don't need to beat the game."),
  ("progression_submarines", "This controls whether submarines can contain progress items.\nIf this is not checked, submarines will only contain optional items you don't need to beat the game."),
  ("progression_triforce_charts", "This controls whether the sunken treasure chests marked on Triforce Charts can contain progress items.\nIf this is not checked, they will only contain optional items you don't need to beat the game."),
  ("progression_treasure_charts", "This controls whether the sunken treasure chests marked on Treasure Charts can contain progress items.\nIf this is not checked, they will only contain optional items you don't need to beat the game."),
  ("progression_expensive_purchases", "This controls whether the three expensive items sold in the Rock Spire Shop Ship can be progress items.\nIf this is not checked, the Rock Spire Shop Ship will only sell optional items you don't need to beat the game."),
  ("progression_misc", "Miscellaneous locations not listed above, such as outdoors chests and free gifts.\nThese locations can always have progress items."),
  
  ("randomize_charts", "Randomizes which sectors are drawn on each Triforce/Treasure Chart."),
  ("randomize_starting_island", "Randomizes which island you start the game on."),
  
  ("swift_sail", "Sailing speed is doubled and the direction of the wind is always at your back as long as the sail is out."),
  
  ("instant_text_boxes", "Text appears instantly for most text boxes."),
  
  ("reveal_full_sea_chart", "Start the game with the sea chart fully drawn out."),
])
