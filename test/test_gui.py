
def test_gui_launches(qtbot):
  from wwrando import make_argparser
  from wwr_ui.randomizer_window import WWRandomizerWindow
  args = make_argparser().parse_args(args=[])
  window = WWRandomizerWindow(cmd_line_args=args)
