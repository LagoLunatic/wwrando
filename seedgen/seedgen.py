
import os
import string
import random

from wwrando_paths import SEEDGEN_PATH

def make_random_seed_name():
  random.seed(None)
  
  with open(os.path.join(SEEDGEN_PATH, "adjectives.txt")) as f:
    adjectives = random.sample(f.read().splitlines(), 2)
  noun_file_to_use = random.choice(["nouns.txt", "names.txt"])
  with open(os.path.join(SEEDGEN_PATH, noun_file_to_use)) as f:
    noun = random.choice(f.read().splitlines())
  words = adjectives + [noun]
  
  capitalized_words = []
  for word in words:
    capitalized_word = ""
    seen_first_letter = False
    for char in word:
      if char in string.ascii_letters and not seen_first_letter:
        capitalized_word += char.capitalize()
        seen_first_letter = True
      else:
        capitalized_word += char
    capitalized_words.append(capitalized_word)
  seed = "".join(capitalized_words)
  
  return seed
