
from wwrando import make_argparser
from wwr_ui.randomizer_window import WWRandomizerWindow

def make_rando_window() -> WWRandomizerWindow:
  args = make_argparser().parse_args(args=[])
  window = WWRandomizerWindow(cmd_line_args=args)
  return window

def test_gui_launches(qtbot):
  window = make_rando_window()
  window.save_settings()

def test_cosmetic_tab(qtbot):
  window = make_rando_window()
  cosmetic_tab = window.ui.tab_player_customization
  cosmetic_tab.ui.custom_player_model.setCurrentIndex(cosmetic_tab.ui.custom_player_model.findText("Link"))
  cosmetic_tab.ui.randomize_all_custom_colors_separately.click()
  cosmetic_tab.ui.randomize_all_custom_colors_together.click()
  cosmetic_tab.ui.custom_color_preset.setCurrentIndex(cosmetic_tab.ui.custom_color_preset.findText("Dark Link"))
