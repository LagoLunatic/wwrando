# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'randomizer_window.ui'
##
## Created by: Qt User Interface Compiler version 6.8.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QAbstractSpinBox, QApplication, QCheckBox,
    QComboBox, QFrame, QGridLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QListView,
    QMainWindow, QPushButton, QScrollArea, QSizePolicy,
    QSpacerItem, QSpinBox, QTabWidget, QVBoxLayout,
    QWidget)

from wwr_ui.cosmetic_tab import CosmeticTab

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(914, 830)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.scrollArea = QScrollArea(self.centralwidget)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setMinimumSize(QSize(600, 400))
        self.scrollArea.setFrameShape(QFrame.NoFrame)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 879, 673))
        self.verticalLayout_2 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.tabWidget = QTabWidget(self.scrollAreaWidgetContents)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setEnabled(True)
        self.tab_randomizer_settings = QWidget()
        self.tab_randomizer_settings.setObjectName(u"tab_randomizer_settings")
        self.verticalLayout_3 = QVBoxLayout(self.tab_randomizer_settings)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.layout_files = QGridLayout()
        self.layout_files.setObjectName(u"layout_files")
        self.seed = QLineEdit(self.tab_randomizer_settings)
        self.seed.setObjectName(u"seed")

        self.layout_files.addWidget(self.seed, 2, 1, 1, 1)

        self.label_for_clean_iso_path = QLabel(self.tab_randomizer_settings)
        self.label_for_clean_iso_path.setObjectName(u"label_for_clean_iso_path")
        self.label_for_clean_iso_path.setTextFormat(Qt.MarkdownText)

        self.layout_files.addWidget(self.label_for_clean_iso_path, 0, 0, 1, 1)

        self.clean_iso_path = QLineEdit(self.tab_randomizer_settings)
        self.clean_iso_path.setObjectName(u"clean_iso_path")

        self.layout_files.addWidget(self.clean_iso_path, 0, 1, 1, 1)

        self.label_for_output_folder = QLabel(self.tab_randomizer_settings)
        self.label_for_output_folder.setObjectName(u"label_for_output_folder")

        self.layout_files.addWidget(self.label_for_output_folder, 1, 0, 1, 1)

        self.output_folder = QLineEdit(self.tab_randomizer_settings)
        self.output_folder.setObjectName(u"output_folder")

        self.layout_files.addWidget(self.output_folder, 1, 1, 1, 1)

        self.output_folder_browse_button = QPushButton(self.tab_randomizer_settings)
        self.output_folder_browse_button.setObjectName(u"output_folder_browse_button")

        self.layout_files.addWidget(self.output_folder_browse_button, 1, 2, 1, 1)

        self.label_for_seed = QLabel(self.tab_randomizer_settings)
        self.label_for_seed.setObjectName(u"label_for_seed")

        self.layout_files.addWidget(self.label_for_seed, 2, 0, 1, 1)

        self.generate_seed_button = QPushButton(self.tab_randomizer_settings)
        self.generate_seed_button.setObjectName(u"generate_seed_button")

        self.layout_files.addWidget(self.generate_seed_button, 2, 2, 1, 1)

        self.clean_iso_path_browse_button = QPushButton(self.tab_randomizer_settings)
        self.clean_iso_path_browse_button.setObjectName(u"clean_iso_path_browse_button")

        self.layout_files.addWidget(self.clean_iso_path_browse_button, 0, 2, 1, 1)


        self.verticalLayout_3.addLayout(self.layout_files)

        self.progression_locations_groupbox = QGroupBox(self.tab_randomizer_settings)
        self.progression_locations_groupbox.setObjectName(u"progression_locations_groupbox")
        self.gridLayout_2 = QGridLayout(self.progression_locations_groupbox)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.progression_submarines = QCheckBox(self.progression_locations_groupbox)
        self.progression_submarines.setObjectName(u"progression_submarines")
        self.progression_submarines.setChecked(False)

        self.gridLayout_2.addWidget(self.progression_submarines, 1, 3, 1, 1)

        self.progression_battlesquid = QCheckBox(self.progression_locations_groupbox)
        self.progression_battlesquid.setObjectName(u"progression_battlesquid")

        self.gridLayout_2.addWidget(self.progression_battlesquid, 5, 2, 1, 1)

        self.progression_mail = QCheckBox(self.progression_locations_groupbox)
        self.progression_mail.setObjectName(u"progression_mail")

        self.gridLayout_2.addWidget(self.progression_mail, 5, 4, 1, 1)

        self.progression_puzzle_secret_caves = QCheckBox(self.progression_locations_groupbox)
        self.progression_puzzle_secret_caves.setObjectName(u"progression_puzzle_secret_caves")
        self.progression_puzzle_secret_caves.setChecked(True)

        self.gridLayout_2.addWidget(self.progression_puzzle_secret_caves, 0, 1, 1, 1)

        self.progression_island_puzzles = QCheckBox(self.progression_locations_groupbox)
        self.progression_island_puzzles.setObjectName(u"progression_island_puzzles")

        self.gridLayout_2.addWidget(self.progression_island_puzzles, 0, 4, 1, 1)

        self.progression_big_octos_gunboats = QCheckBox(self.progression_locations_groupbox)
        self.progression_big_octos_gunboats.setObjectName(u"progression_big_octos_gunboats")

        self.gridLayout_2.addWidget(self.progression_big_octos_gunboats, 4, 4, 1, 1)

        self.progression_triforce_charts = QCheckBox(self.progression_locations_groupbox)
        self.progression_triforce_charts.setObjectName(u"progression_triforce_charts")

        self.gridLayout_2.addWidget(self.progression_triforce_charts, 6, 1, 1, 2)

        self.progression_minigames = QCheckBox(self.progression_locations_groupbox)
        self.progression_minigames.setObjectName(u"progression_minigames")

        self.gridLayout_2.addWidget(self.progression_minigames, 5, 1, 1, 1)

        self.progression_dungeons = QCheckBox(self.progression_locations_groupbox)
        self.progression_dungeons.setObjectName(u"progression_dungeons")
        self.progression_dungeons.setChecked(True)

        self.gridLayout_2.addWidget(self.progression_dungeons, 0, 0, 1, 1)

        self.progression_treasure_charts = QCheckBox(self.progression_locations_groupbox)
        self.progression_treasure_charts.setObjectName(u"progression_treasure_charts")

        self.gridLayout_2.addWidget(self.progression_treasure_charts, 6, 3, 1, 2)

        self.progression_expensive_purchases = QCheckBox(self.progression_locations_groupbox)
        self.progression_expensive_purchases.setObjectName(u"progression_expensive_purchases")
        self.progression_expensive_purchases.setChecked(True)

        self.gridLayout_2.addWidget(self.progression_expensive_purchases, 6, 0, 1, 1)

        self.progression_short_sidequests = QCheckBox(self.progression_locations_groupbox)
        self.progression_short_sidequests.setObjectName(u"progression_short_sidequests")

        self.gridLayout_2.addWidget(self.progression_short_sidequests, 4, 0, 1, 1)

        self.progression_combat_secret_caves = QCheckBox(self.progression_locations_groupbox)
        self.progression_combat_secret_caves.setObjectName(u"progression_combat_secret_caves")

        self.gridLayout_2.addWidget(self.progression_combat_secret_caves, 0, 2, 1, 1)

        self.progression_spoils_trading = QCheckBox(self.progression_locations_groupbox)
        self.progression_spoils_trading.setObjectName(u"progression_spoils_trading")

        self.gridLayout_2.addWidget(self.progression_spoils_trading, 4, 2, 1, 1)

        self.progression_dungeon_secrets = QCheckBox(self.progression_locations_groupbox)
        self.progression_dungeon_secrets.setObjectName(u"progression_dungeon_secrets")

        self.gridLayout_2.addWidget(self.progression_dungeon_secrets, 1, 0, 1, 1)

        self.progression_great_fairies = QCheckBox(self.progression_locations_groupbox)
        self.progression_great_fairies.setObjectName(u"progression_great_fairies")
        self.progression_great_fairies.setChecked(True)

        self.gridLayout_2.addWidget(self.progression_great_fairies, 1, 2, 1, 1)

        self.progression_eye_reef_chests = QCheckBox(self.progression_locations_groupbox)
        self.progression_eye_reef_chests.setObjectName(u"progression_eye_reef_chests")

        self.gridLayout_2.addWidget(self.progression_eye_reef_chests, 4, 3, 1, 1)

        self.progression_free_gifts = QCheckBox(self.progression_locations_groupbox)
        self.progression_free_gifts.setObjectName(u"progression_free_gifts")
        self.progression_free_gifts.setChecked(True)

        self.gridLayout_2.addWidget(self.progression_free_gifts, 5, 3, 1, 1)

        self.progression_tingle_chests = QCheckBox(self.progression_locations_groupbox)
        self.progression_tingle_chests.setObjectName(u"progression_tingle_chests")

        self.gridLayout_2.addWidget(self.progression_tingle_chests, 1, 1, 1, 1)

        self.progression_savage_labyrinth = QCheckBox(self.progression_locations_groupbox)
        self.progression_savage_labyrinth.setObjectName(u"progression_savage_labyrinth")

        self.gridLayout_2.addWidget(self.progression_savage_labyrinth, 0, 3, 1, 1)

        self.progression_long_sidequests = QCheckBox(self.progression_locations_groupbox)
        self.progression_long_sidequests.setObjectName(u"progression_long_sidequests")

        self.gridLayout_2.addWidget(self.progression_long_sidequests, 4, 1, 1, 1)

        self.progression_misc = QCheckBox(self.progression_locations_groupbox)
        self.progression_misc.setObjectName(u"progression_misc")
        self.progression_misc.setChecked(True)

        self.gridLayout_2.addWidget(self.progression_misc, 5, 0, 1, 1)

        self.progression_platforms_rafts = QCheckBox(self.progression_locations_groupbox)
        self.progression_platforms_rafts.setObjectName(u"progression_platforms_rafts")

        self.gridLayout_2.addWidget(self.progression_platforms_rafts, 1, 4, 1, 1)


        self.verticalLayout_3.addWidget(self.progression_locations_groupbox)

        self.item_randomizer_modes_groupbox = QGroupBox(self.tab_randomizer_settings)
        self.item_randomizer_modes_groupbox.setObjectName(u"item_randomizer_modes_groupbox")
        self.gridLayout_3 = QGridLayout(self.item_randomizer_modes_groupbox)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.layout_num_starting_triforce_shards = QHBoxLayout()
        self.layout_num_starting_triforce_shards.setObjectName(u"layout_num_starting_triforce_shards")
        self.label_for_num_starting_triforce_shards = QLabel(self.item_randomizer_modes_groupbox)
        self.label_for_num_starting_triforce_shards.setObjectName(u"label_for_num_starting_triforce_shards")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_for_num_starting_triforce_shards.sizePolicy().hasHeightForWidth())
        self.label_for_num_starting_triforce_shards.setSizePolicy(sizePolicy)

        self.layout_num_starting_triforce_shards.addWidget(self.label_for_num_starting_triforce_shards)

        self.num_starting_triforce_shards = QSpinBox(self.item_randomizer_modes_groupbox)
        self.num_starting_triforce_shards.setObjectName(u"num_starting_triforce_shards")

        self.layout_num_starting_triforce_shards.addWidget(self.num_starting_triforce_shards)


        self.gridLayout_3.addLayout(self.layout_num_starting_triforce_shards, 0, 1, 1, 1)

        self.layout_shuffle_maps_and_compasses = QHBoxLayout()
        self.layout_shuffle_maps_and_compasses.setObjectName(u"layout_shuffle_maps_and_compasses")
        self.label_for_shuffle_maps_and_compasses = QLabel(self.item_randomizer_modes_groupbox)
        self.label_for_shuffle_maps_and_compasses.setObjectName(u"label_for_shuffle_maps_and_compasses")

        self.layout_shuffle_maps_and_compasses.addWidget(self.label_for_shuffle_maps_and_compasses)

        self.shuffle_maps_and_compasses = QComboBox(self.item_randomizer_modes_groupbox)
        self.shuffle_maps_and_compasses.addItem("")
        self.shuffle_maps_and_compasses.addItem("")
        self.shuffle_maps_and_compasses.addItem("")
        self.shuffle_maps_and_compasses.addItem("")
        self.shuffle_maps_and_compasses.addItem("")
        self.shuffle_maps_and_compasses.addItem("")
        self.shuffle_maps_and_compasses.setObjectName(u"shuffle_maps_and_compasses")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(1)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.shuffle_maps_and_compasses.sizePolicy().hasHeightForWidth())
        self.shuffle_maps_and_compasses.setSizePolicy(sizePolicy1)

        self.layout_shuffle_maps_and_compasses.addWidget(self.shuffle_maps_and_compasses)


        self.gridLayout_3.addLayout(self.layout_shuffle_maps_and_compasses, 2, 2, 1, 1)

        self.layout_shuffle_big_keys = QHBoxLayout()
        self.layout_shuffle_big_keys.setObjectName(u"layout_shuffle_big_keys")
        self.label_for_shuffle_big_keys = QLabel(self.item_randomizer_modes_groupbox)
        self.label_for_shuffle_big_keys.setObjectName(u"label_for_shuffle_big_keys")

        self.layout_shuffle_big_keys.addWidget(self.label_for_shuffle_big_keys)

        self.shuffle_big_keys = QComboBox(self.item_randomizer_modes_groupbox)
        self.shuffle_big_keys.addItem("")
        self.shuffle_big_keys.addItem("")
        self.shuffle_big_keys.addItem("")
        self.shuffle_big_keys.addItem("")
        self.shuffle_big_keys.addItem("")
        self.shuffle_big_keys.addItem("")
        self.shuffle_big_keys.setObjectName(u"shuffle_big_keys")
        sizePolicy1.setHeightForWidth(self.shuffle_big_keys.sizePolicy().hasHeightForWidth())
        self.shuffle_big_keys.setSizePolicy(sizePolicy1)

        self.layout_shuffle_big_keys.addWidget(self.shuffle_big_keys)


        self.gridLayout_3.addLayout(self.layout_shuffle_big_keys, 2, 1, 1, 1)

        self.layout_sword_mode = QHBoxLayout()
        self.layout_sword_mode.setObjectName(u"layout_sword_mode")
        self.label_for_sword_mode = QLabel(self.item_randomizer_modes_groupbox)
        self.label_for_sword_mode.setObjectName(u"label_for_sword_mode")

        self.layout_sword_mode.addWidget(self.label_for_sword_mode)

        self.sword_mode = QComboBox(self.item_randomizer_modes_groupbox)
        self.sword_mode.addItem("")
        self.sword_mode.addItem("")
        self.sword_mode.addItem("")
        self.sword_mode.setObjectName(u"sword_mode")
        sizePolicy1.setHeightForWidth(self.sword_mode.sizePolicy().hasHeightForWidth())
        self.sword_mode.setSizePolicy(sizePolicy1)

        self.layout_sword_mode.addWidget(self.sword_mode)


        self.gridLayout_3.addLayout(self.layout_sword_mode, 0, 0, 1, 1)

        self.layout_shuffle_small_keys = QHBoxLayout()
        self.layout_shuffle_small_keys.setObjectName(u"layout_shuffle_small_keys")
        self.label_for_shuffle_small_keys = QLabel(self.item_randomizer_modes_groupbox)
        self.label_for_shuffle_small_keys.setObjectName(u"label_for_shuffle_small_keys")

        self.layout_shuffle_small_keys.addWidget(self.label_for_shuffle_small_keys)

        self.shuffle_small_keys = QComboBox(self.item_randomizer_modes_groupbox)
        self.shuffle_small_keys.addItem("")
        self.shuffle_small_keys.addItem("")
        self.shuffle_small_keys.addItem("")
        self.shuffle_small_keys.addItem("")
        self.shuffle_small_keys.addItem("")
        self.shuffle_small_keys.addItem("")
        self.shuffle_small_keys.setObjectName(u"shuffle_small_keys")
        sizePolicy1.setHeightForWidth(self.shuffle_small_keys.sizePolicy().hasHeightForWidth())
        self.shuffle_small_keys.setSizePolicy(sizePolicy1)

        self.layout_shuffle_small_keys.addWidget(self.shuffle_small_keys)


        self.gridLayout_3.addLayout(self.layout_shuffle_small_keys, 2, 0, 1, 1)

        self.chest_type_matches_contents = QCheckBox(self.item_randomizer_modes_groupbox)
        self.chest_type_matches_contents.setObjectName(u"chest_type_matches_contents")

        self.gridLayout_3.addWidget(self.chest_type_matches_contents, 3, 0, 1, 1)

        self.trap_chests = QCheckBox(self.item_randomizer_modes_groupbox)
        self.trap_chests.setObjectName(u"trap_chests")

        self.gridLayout_3.addWidget(self.trap_chests, 3, 1, 1, 1)


        self.verticalLayout_3.addWidget(self.item_randomizer_modes_groupbox)

        self.layout_other_randomizer_settings = QGridLayout()
        self.layout_other_randomizer_settings.setObjectName(u"layout_other_randomizer_settings")
        self.entrance_randomizer_groupbox = QGroupBox(self.tab_randomizer_settings)
        self.entrance_randomizer_groupbox.setObjectName(u"entrance_randomizer_groupbox")
        self.gridLayout_9 = QGridLayout(self.entrance_randomizer_groupbox)
        self.gridLayout_9.setObjectName(u"gridLayout_9")
        self.randomize_dungeon_entrances = QCheckBox(self.entrance_randomizer_groupbox)
        self.randomize_dungeon_entrances.setObjectName(u"randomize_dungeon_entrances")

        self.gridLayout_9.addWidget(self.randomize_dungeon_entrances, 0, 0, 1, 1)

        self.randomize_fairy_fountain_entrances = QCheckBox(self.entrance_randomizer_groupbox)
        self.randomize_fairy_fountain_entrances.setObjectName(u"randomize_fairy_fountain_entrances")

        self.gridLayout_9.addWidget(self.randomize_fairy_fountain_entrances, 1, 2, 1, 1)

        self.randomize_miniboss_entrances = QCheckBox(self.entrance_randomizer_groupbox)
        self.randomize_miniboss_entrances.setObjectName(u"randomize_miniboss_entrances")

        self.gridLayout_9.addWidget(self.randomize_miniboss_entrances, 0, 2, 1, 1)

        self.randomize_boss_entrances = QCheckBox(self.entrance_randomizer_groupbox)
        self.randomize_boss_entrances.setObjectName(u"randomize_boss_entrances")

        self.gridLayout_9.addWidget(self.randomize_boss_entrances, 0, 1, 1, 1)

        self.randomize_secret_cave_inner_entrances = QCheckBox(self.entrance_randomizer_groupbox)
        self.randomize_secret_cave_inner_entrances.setObjectName(u"randomize_secret_cave_inner_entrances")

        self.gridLayout_9.addWidget(self.randomize_secret_cave_inner_entrances, 1, 1, 1, 1)

        self.randomize_secret_cave_entrances = QCheckBox(self.entrance_randomizer_groupbox)
        self.randomize_secret_cave_entrances.setObjectName(u"randomize_secret_cave_entrances")

        self.gridLayout_9.addWidget(self.randomize_secret_cave_entrances, 1, 0, 1, 1)

        self.layout_mix_entrances = QHBoxLayout()
        self.layout_mix_entrances.setObjectName(u"layout_mix_entrances")
        self.label_for_mix_entrances = QLabel(self.entrance_randomizer_groupbox)
        self.label_for_mix_entrances.setObjectName(u"label_for_mix_entrances")

        self.layout_mix_entrances.addWidget(self.label_for_mix_entrances)

        self.mix_entrances = QComboBox(self.entrance_randomizer_groupbox)
        self.mix_entrances.addItem("")
        self.mix_entrances.addItem("")
        self.mix_entrances.setObjectName(u"mix_entrances")
        sizePolicy1.setHeightForWidth(self.mix_entrances.sizePolicy().hasHeightForWidth())
        self.mix_entrances.setSizePolicy(sizePolicy1)

        self.layout_mix_entrances.addWidget(self.mix_entrances)


        self.gridLayout_9.addLayout(self.layout_mix_entrances, 2, 0, 1, 3)


        self.layout_other_randomizer_settings.addWidget(self.entrance_randomizer_groupbox, 0, 0, 1, 1)

        self.other_randomizers_groupbox = QGroupBox(self.tab_randomizer_settings)
        self.other_randomizers_groupbox.setObjectName(u"other_randomizers_groupbox")
        self.gridLayout_10 = QGridLayout(self.other_randomizers_groupbox)
        self.gridLayout_10.setObjectName(u"gridLayout_10")
        self.randomize_enemy_palettes = QCheckBox(self.other_randomizers_groupbox)
        self.randomize_enemy_palettes.setObjectName(u"randomize_enemy_palettes")

        self.gridLayout_10.addWidget(self.randomize_enemy_palettes, 1, 0, 1, 1)

        self.randomize_charts = QCheckBox(self.other_randomizers_groupbox)
        self.randomize_charts.setObjectName(u"randomize_charts")

        self.gridLayout_10.addWidget(self.randomize_charts, 0, 1, 1, 1)

        self.randomize_starting_island = QCheckBox(self.other_randomizers_groupbox)
        self.randomize_starting_island.setObjectName(u"randomize_starting_island")

        self.gridLayout_10.addWidget(self.randomize_starting_island, 0, 0, 1, 1)

        self.randomize_enemies = QCheckBox(self.other_randomizers_groupbox)
        self.randomize_enemies.setObjectName(u"randomize_enemies")

        self.gridLayout_10.addWidget(self.randomize_enemies, 1, 1, 1, 1)

        self.widget = QWidget(self.other_randomizers_groupbox)
        self.widget.setObjectName(u"widget")

        self.gridLayout_10.addWidget(self.widget, 2, 0, 1, 1)


        self.layout_other_randomizer_settings.addWidget(self.other_randomizers_groupbox, 0, 1, 1, 1)


        self.verticalLayout_3.addLayout(self.layout_other_randomizer_settings)

        self.convenience_tweaks_groupbox = QGroupBox(self.tab_randomizer_settings)
        self.convenience_tweaks_groupbox.setObjectName(u"convenience_tweaks_groupbox")
        self.gridLayout_4 = QGridLayout(self.convenience_tweaks_groupbox)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.switch_targeting_mode = QCheckBox(self.convenience_tweaks_groupbox)
        self.switch_targeting_mode.setObjectName(u"switch_targeting_mode")

        self.gridLayout_4.addWidget(self.switch_targeting_mode, 0, 2, 1, 1)

        self.invert_sea_compass_x_axis = QCheckBox(self.convenience_tweaks_groupbox)
        self.invert_sea_compass_x_axis.setObjectName(u"invert_sea_compass_x_axis")

        self.gridLayout_4.addWidget(self.invert_sea_compass_x_axis, 0, 4, 1, 1)

        self.add_shortcut_warps_between_dungeons = QCheckBox(self.convenience_tweaks_groupbox)
        self.add_shortcut_warps_between_dungeons.setObjectName(u"add_shortcut_warps_between_dungeons")

        self.gridLayout_4.addWidget(self.add_shortcut_warps_between_dungeons, 1, 1, 1, 1)

        self.invert_camera_x_axis = QCheckBox(self.convenience_tweaks_groupbox)
        self.invert_camera_x_axis.setObjectName(u"invert_camera_x_axis")

        self.gridLayout_4.addWidget(self.invert_camera_x_axis, 1, 4, 1, 1)

        self.instant_text_boxes = QCheckBox(self.convenience_tweaks_groupbox)
        self.instant_text_boxes.setObjectName(u"instant_text_boxes")
        self.instant_text_boxes.setChecked(True)

        self.gridLayout_4.addWidget(self.instant_text_boxes, 0, 1, 1, 1)

        self.skip_rematch_bosses = QCheckBox(self.convenience_tweaks_groupbox)
        self.skip_rematch_bosses.setObjectName(u"skip_rematch_bosses")
        self.skip_rematch_bosses.setChecked(True)

        self.gridLayout_4.addWidget(self.skip_rematch_bosses, 1, 0, 1, 1)

        self.swift_sail = QCheckBox(self.convenience_tweaks_groupbox)
        self.swift_sail.setObjectName(u"swift_sail")
        self.swift_sail.setChecked(True)

        self.gridLayout_4.addWidget(self.swift_sail, 0, 0, 1, 1)

        self.reveal_full_sea_chart = QCheckBox(self.convenience_tweaks_groupbox)
        self.reveal_full_sea_chart.setObjectName(u"reveal_full_sea_chart")
        self.reveal_full_sea_chart.setChecked(True)

        self.gridLayout_4.addWidget(self.reveal_full_sea_chart, 0, 3, 1, 1)

        self.remove_title_and_ending_videos = QCheckBox(self.convenience_tweaks_groupbox)
        self.remove_title_and_ending_videos.setObjectName(u"remove_title_and_ending_videos")
        self.remove_title_and_ending_videos.setChecked(True)

        self.gridLayout_4.addWidget(self.remove_title_and_ending_videos, 1, 2, 1, 1)

        self.remove_music = QCheckBox(self.convenience_tweaks_groupbox)
        self.remove_music.setObjectName(u"remove_music")

        self.gridLayout_4.addWidget(self.remove_music, 1, 3, 1, 1)


        self.verticalLayout_3.addWidget(self.convenience_tweaks_groupbox)

        self.randomizer_settings_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_3.addItem(self.randomizer_settings_spacer)

        self.tabWidget.addTab(self.tab_randomizer_settings, "")
        self.tab_starting_items = QWidget()
        self.tab_starting_items.setObjectName(u"tab_starting_items")
        self.tab_starting_items.setEnabled(True)
        self.verticalLayout_4 = QVBoxLayout(self.tab_starting_items)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.layout_gear = QHBoxLayout()
        self.layout_gear.setObjectName(u"layout_gear")
        self.layout_randomized_gear = QVBoxLayout()
        self.layout_randomized_gear.setObjectName(u"layout_randomized_gear")
        self.label_for_randomized_gear = QLabel(self.tab_starting_items)
        self.label_for_randomized_gear.setObjectName(u"label_for_randomized_gear")

        self.layout_randomized_gear.addWidget(self.label_for_randomized_gear)

        self.randomized_gear = QListView(self.tab_starting_items)
        self.randomized_gear.setObjectName(u"randomized_gear")
        self.randomized_gear.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.randomized_gear.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.layout_randomized_gear.addWidget(self.randomized_gear)


        self.layout_gear.addLayout(self.layout_randomized_gear)

        self.layout_gear_buttons = QVBoxLayout()
        self.layout_gear_buttons.setObjectName(u"layout_gear_buttons")
        self.gear_buttons_spacer_top = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.layout_gear_buttons.addItem(self.gear_buttons_spacer_top)

        self.remove_gear = QPushButton(self.tab_starting_items)
        self.remove_gear.setObjectName(u"remove_gear")
        self.remove_gear.setMinimumSize(QSize(0, 80))

        self.layout_gear_buttons.addWidget(self.remove_gear)

        self.add_gear = QPushButton(self.tab_starting_items)
        self.add_gear.setObjectName(u"add_gear")
        self.add_gear.setMinimumSize(QSize(0, 80))

        self.layout_gear_buttons.addWidget(self.add_gear)

        self.gear_buttons_spacer_bottom = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.layout_gear_buttons.addItem(self.gear_buttons_spacer_bottom)


        self.layout_gear.addLayout(self.layout_gear_buttons)

        self.layout_starting_gear = QVBoxLayout()
        self.layout_starting_gear.setObjectName(u"layout_starting_gear")
        self.label_for_starting_gear = QLabel(self.tab_starting_items)
        self.label_for_starting_gear.setObjectName(u"label_for_starting_gear")

        self.layout_starting_gear.addWidget(self.label_for_starting_gear)

        self.starting_gear = QListView(self.tab_starting_items)
        self.starting_gear.setObjectName(u"starting_gear")
        self.starting_gear.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.starting_gear.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.layout_starting_gear.addWidget(self.starting_gear)


        self.layout_gear.addLayout(self.layout_starting_gear)


        self.verticalLayout_4.addLayout(self.layout_gear)

        self.layout_starting_health = QHBoxLayout()
        self.layout_starting_health.setObjectName(u"layout_starting_health")
        self.label_for_starting_hcs = QLabel(self.tab_starting_items)
        self.label_for_starting_hcs.setObjectName(u"label_for_starting_hcs")

        self.layout_starting_health.addWidget(self.label_for_starting_hcs)

        self.starting_hcs = QSpinBox(self.tab_starting_items)
        self.starting_hcs.setObjectName(u"starting_hcs")
        self.starting_hcs.setLayoutDirection(Qt.LeftToRight)
        self.starting_hcs.setMinimum(1)
        self.starting_hcs.setMaximum(9)
        self.starting_hcs.setValue(3)
        self.starting_hcs.setDisplayIntegerBase(10)

        self.layout_starting_health.addWidget(self.starting_hcs)

        self.label_for_starting_pohs = QLabel(self.tab_starting_items)
        self.label_for_starting_pohs.setObjectName(u"label_for_starting_pohs")

        self.layout_starting_health.addWidget(self.label_for_starting_pohs)

        self.starting_pohs = QSpinBox(self.tab_starting_items)
        self.starting_pohs.setObjectName(u"starting_pohs")
        self.starting_pohs.setMaximum(44)
        self.starting_pohs.setValue(0)
        self.starting_pohs.setDisplayIntegerBase(10)

        self.layout_starting_health.addWidget(self.starting_pohs)

        self.current_health = QLabel(self.tab_starting_items)
        self.current_health.setObjectName(u"current_health")

        self.layout_starting_health.addWidget(self.current_health)

        self.starting_health_spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.layout_starting_health.addItem(self.starting_health_spacer)


        self.verticalLayout_4.addLayout(self.layout_starting_health)

        self.layout_random_starting_items = QHBoxLayout()
        self.layout_random_starting_items.setObjectName(u"layout_random_starting_items")
        self.label_for_num_extra_starting_items = QLabel(self.tab_starting_items)
        self.label_for_num_extra_starting_items.setObjectName(u"label_for_num_extra_starting_items")

        self.layout_random_starting_items.addWidget(self.label_for_num_extra_starting_items)

        self.num_extra_starting_items = QSpinBox(self.tab_starting_items)
        self.num_extra_starting_items.setObjectName(u"num_extra_starting_items")
        self.num_extra_starting_items.setLayoutDirection(Qt.LeftToRight)
        self.num_extra_starting_items.setMaximum(3)
        self.num_extra_starting_items.setValue(0)
        self.num_extra_starting_items.setDisplayIntegerBase(10)

        self.layout_random_starting_items.addWidget(self.num_extra_starting_items)

        self.random_starting_items_spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.layout_random_starting_items.addItem(self.random_starting_items_spacer)


        self.verticalLayout_4.addLayout(self.layout_random_starting_items)

        self.tabWidget.addTab(self.tab_starting_items, "")
        self.tab_advanced = QWidget()
        self.tab_advanced.setObjectName(u"tab_advanced")
        self.verticalLayout_8 = QVBoxLayout(self.tab_advanced)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.required_bosses_groupbox = QGroupBox(self.tab_advanced)
        self.required_bosses_groupbox.setObjectName(u"required_bosses_groupbox")
        self.gridLayout_6 = QGridLayout(self.required_bosses_groupbox)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.widget_2 = QWidget(self.required_bosses_groupbox)
        self.widget_2.setObjectName(u"widget_2")

        self.gridLayout_6.addWidget(self.widget_2, 0, 2, 1, 1)

        self.layout_required_bosses = QHBoxLayout()
        self.layout_required_bosses.setObjectName(u"layout_required_bosses")
        self.label_for_num_required_bosses = QLabel(self.required_bosses_groupbox)
        self.label_for_num_required_bosses.setObjectName(u"label_for_num_required_bosses")
        sizePolicy.setHeightForWidth(self.label_for_num_required_bosses.sizePolicy().hasHeightForWidth())
        self.label_for_num_required_bosses.setSizePolicy(sizePolicy)

        self.layout_required_bosses.addWidget(self.label_for_num_required_bosses)

        self.num_required_bosses = QSpinBox(self.required_bosses_groupbox)
        self.num_required_bosses.setObjectName(u"num_required_bosses")

        self.layout_required_bosses.addWidget(self.num_required_bosses)


        self.gridLayout_6.addLayout(self.layout_required_bosses, 0, 1, 1, 1)

        self.required_bosses = QCheckBox(self.required_bosses_groupbox)
        self.required_bosses.setObjectName(u"required_bosses")

        self.gridLayout_6.addWidget(self.required_bosses, 0, 0, 1, 1)

        self.widget_3 = QWidget(self.required_bosses_groupbox)
        self.widget_3.setObjectName(u"widget_3")

        self.gridLayout_6.addWidget(self.widget_3, 0, 3, 1, 1)


        self.verticalLayout_8.addWidget(self.required_bosses_groupbox)

        self.difficulty_options_groupbox = QGroupBox(self.tab_advanced)
        self.difficulty_options_groupbox.setObjectName(u"difficulty_options_groupbox")
        self.gridLayout_5 = QGridLayout(self.difficulty_options_groupbox)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.hero_mode = QCheckBox(self.difficulty_options_groupbox)
        self.hero_mode.setObjectName(u"hero_mode")

        self.gridLayout_5.addWidget(self.hero_mode, 0, 0, 1, 1)

        self.layout_logic_precision = QHBoxLayout()
        self.layout_logic_precision.setObjectName(u"layout_logic_precision")
        self.label_for_logic_precision = QLabel(self.difficulty_options_groupbox)
        self.label_for_logic_precision.setObjectName(u"label_for_logic_precision")

        self.layout_logic_precision.addWidget(self.label_for_logic_precision)

        self.logic_precision = QComboBox(self.difficulty_options_groupbox)
        self.logic_precision.addItem("")
        self.logic_precision.addItem("")
        self.logic_precision.addItem("")
        self.logic_precision.addItem("")
        self.logic_precision.setObjectName(u"logic_precision")

        self.layout_logic_precision.addWidget(self.logic_precision)


        self.gridLayout_5.addLayout(self.layout_logic_precision, 0, 2, 1, 1)

        self.layout_logic_obscurity = QHBoxLayout()
        self.layout_logic_obscurity.setObjectName(u"layout_logic_obscurity")
        self.label_for_logic_obscurity = QLabel(self.difficulty_options_groupbox)
        self.label_for_logic_obscurity.setObjectName(u"label_for_logic_obscurity")

        self.layout_logic_obscurity.addWidget(self.label_for_logic_obscurity)

        self.logic_obscurity = QComboBox(self.difficulty_options_groupbox)
        self.logic_obscurity.addItem("")
        self.logic_obscurity.addItem("")
        self.logic_obscurity.addItem("")
        self.logic_obscurity.addItem("")
        self.logic_obscurity.setObjectName(u"logic_obscurity")

        self.layout_logic_obscurity.addWidget(self.logic_obscurity)


        self.gridLayout_5.addLayout(self.layout_logic_obscurity, 0, 1, 1, 1)

        self.widget_4 = QWidget(self.difficulty_options_groupbox)
        self.widget_4.setObjectName(u"widget_4")

        self.gridLayout_5.addWidget(self.widget_4, 0, 3, 1, 1)


        self.verticalLayout_8.addWidget(self.difficulty_options_groupbox)

        self.hint_options_groupbox = QGroupBox(self.tab_advanced)
        self.hint_options_groupbox.setObjectName(u"hint_options_groupbox")
        self.gridLayout_7 = QGridLayout(self.hint_options_groupbox)
        self.gridLayout_7.setObjectName(u"gridLayout_7")
        self.hoho_hints = QCheckBox(self.hint_options_groupbox)
        self.hoho_hints.setObjectName(u"hoho_hints")
        self.hoho_hints.setChecked(True)

        self.gridLayout_7.addWidget(self.hoho_hints, 4, 0, 1, 1)

        self.prioritize_remote_hints = QCheckBox(self.hint_options_groupbox)
        self.prioritize_remote_hints.setObjectName(u"prioritize_remote_hints")

        self.gridLayout_7.addWidget(self.prioritize_remote_hints, 6, 1, 1, 1)

        self.korl_hints = QCheckBox(self.hint_options_groupbox)
        self.korl_hints.setObjectName(u"korl_hints")

        self.gridLayout_7.addWidget(self.korl_hints, 4, 2, 1, 1)

        self.layout_num_barren_hints = QHBoxLayout()
        self.layout_num_barren_hints.setObjectName(u"layout_num_barren_hints")
        self.label_for_num_barren_hints = QLabel(self.hint_options_groupbox)
        self.label_for_num_barren_hints.setObjectName(u"label_for_num_barren_hints")

        self.layout_num_barren_hints.addWidget(self.label_for_num_barren_hints)

        self.num_barren_hints = QSpinBox(self.hint_options_groupbox)
        self.num_barren_hints.setObjectName(u"num_barren_hints")
        self.num_barren_hints.setCorrectionMode(QAbstractSpinBox.CorrectToNearestValue)
        self.num_barren_hints.setMinimum(0)
        self.num_barren_hints.setMaximum(15)
        self.num_barren_hints.setValue(0)

        self.layout_num_barren_hints.addWidget(self.num_barren_hints)

        self.widget_7 = QWidget(self.hint_options_groupbox)
        self.widget_7.setObjectName(u"widget_7")

        self.layout_num_barren_hints.addWidget(self.widget_7)


        self.gridLayout_7.addLayout(self.layout_num_barren_hints, 5, 2, 1, 1)

        self.cryptic_hints = QCheckBox(self.hint_options_groupbox)
        self.cryptic_hints.setObjectName(u"cryptic_hints")
        self.cryptic_hints.setChecked(True)

        self.gridLayout_7.addWidget(self.cryptic_hints, 6, 0, 1, 1)

        self.fishmen_hints = QCheckBox(self.hint_options_groupbox)
        self.fishmen_hints.setObjectName(u"fishmen_hints")
        self.fishmen_hints.setChecked(True)

        self.gridLayout_7.addWidget(self.fishmen_hints, 4, 1, 1, 1)

        self.layout_num_location_hints = QHBoxLayout()
        self.layout_num_location_hints.setObjectName(u"layout_num_location_hints")
        self.label_for_num_location_hints = QLabel(self.hint_options_groupbox)
        self.label_for_num_location_hints.setObjectName(u"label_for_num_location_hints")

        self.layout_num_location_hints.addWidget(self.label_for_num_location_hints)

        self.num_location_hints = QSpinBox(self.hint_options_groupbox)
        self.num_location_hints.setObjectName(u"num_location_hints")
        self.num_location_hints.setCorrectionMode(QAbstractSpinBox.CorrectToNearestValue)
        self.num_location_hints.setMinimum(0)
        self.num_location_hints.setMaximum(15)
        self.num_location_hints.setValue(5)

        self.layout_num_location_hints.addWidget(self.num_location_hints)

        self.widget_6 = QWidget(self.hint_options_groupbox)
        self.widget_6.setObjectName(u"widget_6")

        self.layout_num_location_hints.addWidget(self.widget_6)


        self.gridLayout_7.addLayout(self.layout_num_location_hints, 5, 1, 1, 1)

        self.layout_num_item_hints = QHBoxLayout()
        self.layout_num_item_hints.setObjectName(u"layout_num_item_hints")
        self.label_for_num_item_hints = QLabel(self.hint_options_groupbox)
        self.label_for_num_item_hints.setObjectName(u"label_for_num_item_hints")

        self.layout_num_item_hints.addWidget(self.label_for_num_item_hints)

        self.num_item_hints = QSpinBox(self.hint_options_groupbox)
        self.num_item_hints.setObjectName(u"num_item_hints")
        self.num_item_hints.setCorrectionMode(QAbstractSpinBox.CorrectToNearestValue)
        self.num_item_hints.setMinimum(0)
        self.num_item_hints.setMaximum(15)
        self.num_item_hints.setValue(15)

        self.layout_num_item_hints.addWidget(self.num_item_hints)

        self.widget_5 = QWidget(self.hint_options_groupbox)
        self.widget_5.setObjectName(u"widget_5")

        self.layout_num_item_hints.addWidget(self.widget_5)


        self.gridLayout_7.addLayout(self.layout_num_item_hints, 5, 0, 1, 1)

        self.layout_num_path_hints = QHBoxLayout()
        self.layout_num_path_hints.setObjectName(u"layout_num_path_hints")
        self.label_for_num_path_hints = QLabel(self.hint_options_groupbox)
        self.label_for_num_path_hints.setObjectName(u"label_for_num_path_hints")

        self.layout_num_path_hints.addWidget(self.label_for_num_path_hints)

        self.num_path_hints = QSpinBox(self.hint_options_groupbox)
        self.num_path_hints.setObjectName(u"num_path_hints")
        self.num_path_hints.setCorrectionMode(QAbstractSpinBox.CorrectToNearestValue)
        self.num_path_hints.setMinimum(0)
        self.num_path_hints.setMaximum(15)
        self.num_path_hints.setValue(0)

        self.layout_num_path_hints.addWidget(self.num_path_hints)

        self.widget_8 = QWidget(self.hint_options_groupbox)
        self.widget_8.setObjectName(u"widget_8")

        self.layout_num_path_hints.addWidget(self.widget_8)


        self.gridLayout_7.addLayout(self.layout_num_path_hints, 5, 3, 1, 1)

        self.hint_importance = QCheckBox(self.hint_options_groupbox)
        self.hint_importance.setObjectName(u"hint_importance")

        self.gridLayout_7.addWidget(self.hint_importance, 6, 2, 1, 1)


        self.verticalLayout_8.addWidget(self.hint_options_groupbox)

        self.additional_advanced_groupbox = QGroupBox(self.tab_advanced)
        self.additional_advanced_groupbox.setObjectName(u"additional_advanced_groupbox")
        self.gridLayout_8 = QGridLayout(self.additional_advanced_groupbox)
        self.gridLayout_8.setObjectName(u"gridLayout_8")
        self.do_not_generate_spoiler_log = QCheckBox(self.additional_advanced_groupbox)
        self.do_not_generate_spoiler_log.setObjectName(u"do_not_generate_spoiler_log")

        self.gridLayout_8.addWidget(self.do_not_generate_spoiler_log, 0, 0, 1, 1)

        self.widget_9 = QWidget(self.additional_advanced_groupbox)
        self.widget_9.setObjectName(u"widget_9")

        self.gridLayout_8.addWidget(self.widget_9, 0, 2, 1, 1)

        self.widget_10 = QWidget(self.additional_advanced_groupbox)
        self.widget_10.setObjectName(u"widget_10")

        self.gridLayout_8.addWidget(self.widget_10, 0, 3, 1, 1)

        self.dry_run = QCheckBox(self.additional_advanced_groupbox)
        self.dry_run.setObjectName(u"dry_run")

        self.gridLayout_8.addWidget(self.dry_run, 0, 1, 1, 1)


        self.verticalLayout_8.addWidget(self.additional_advanced_groupbox)

        self.advanced_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_8.addItem(self.advanced_spacer)

        self.tabWidget.addTab(self.tab_advanced, "")
        self.tab_player_customization = CosmeticTab()
        self.tab_player_customization.setObjectName(u"tab_player_customization")
        self.tabWidget.addTab(self.tab_player_customization, "")

        self.verticalLayout_2.addWidget(self.tabWidget)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout.addWidget(self.scrollArea)

        self.option_description = QLabel(self.centralwidget)
        self.option_description.setObjectName(u"option_description")
        self.option_description.setMinimumSize(QSize(0, 32))
        self.option_description.setTextFormat(Qt.RichText)
        self.option_description.setWordWrap(True)

        self.verticalLayout.addWidget(self.option_description)

        self.layout_permalink = QHBoxLayout()
        self.layout_permalink.setObjectName(u"layout_permalink")
        self.label_for_permalink = QLabel(self.centralwidget)
        self.label_for_permalink.setObjectName(u"label_for_permalink")

        self.layout_permalink.addWidget(self.label_for_permalink)

        self.permalink = QLineEdit(self.centralwidget)
        self.permalink.setObjectName(u"permalink")

        self.layout_permalink.addWidget(self.permalink)


        self.verticalLayout.addLayout(self.layout_permalink)

        self.update_checker_label = QLabel(self.centralwidget)
        self.update_checker_label.setObjectName(u"update_checker_label")
        self.update_checker_label.setOpenExternalLinks(True)

        self.verticalLayout.addWidget(self.update_checker_label)

        self.layout_bottom_buttons = QHBoxLayout()
        self.layout_bottom_buttons.setObjectName(u"layout_bottom_buttons")
        self.about_button = QPushButton(self.centralwidget)
        self.about_button.setObjectName(u"about_button")

        self.layout_bottom_buttons.addWidget(self.about_button)

        self.bottom_buttons_spacer_left = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.layout_bottom_buttons.addItem(self.bottom_buttons_spacer_left)

        self.reset_settings_to_default = QPushButton(self.centralwidget)
        self.reset_settings_to_default.setObjectName(u"reset_settings_to_default")
        self.reset_settings_to_default.setMinimumSize(QSize(180, 0))

        self.layout_bottom_buttons.addWidget(self.reset_settings_to_default)

        self.bottom_buttons_spacer_right = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.layout_bottom_buttons.addItem(self.bottom_buttons_spacer_right)

        self.randomize_button = QPushButton(self.centralwidget)
        self.randomize_button.setObjectName(u"randomize_button")

        self.layout_bottom_buttons.addWidget(self.randomize_button)


        self.verticalLayout.addLayout(self.layout_bottom_buttons)

        MainWindow.setCentralWidget(self.centralwidget)
        QWidget.setTabOrder(self.tabWidget, self.scrollArea)
        QWidget.setTabOrder(self.scrollArea, self.clean_iso_path)
        QWidget.setTabOrder(self.clean_iso_path, self.clean_iso_path_browse_button)
        QWidget.setTabOrder(self.clean_iso_path_browse_button, self.output_folder)
        QWidget.setTabOrder(self.output_folder, self.output_folder_browse_button)
        QWidget.setTabOrder(self.output_folder_browse_button, self.seed)
        QWidget.setTabOrder(self.seed, self.generate_seed_button)
        QWidget.setTabOrder(self.generate_seed_button, self.progression_dungeons)
        QWidget.setTabOrder(self.progression_dungeons, self.progression_puzzle_secret_caves)
        QWidget.setTabOrder(self.progression_puzzle_secret_caves, self.progression_combat_secret_caves)
        QWidget.setTabOrder(self.progression_combat_secret_caves, self.progression_savage_labyrinth)
        QWidget.setTabOrder(self.progression_savage_labyrinth, self.progression_island_puzzles)
        QWidget.setTabOrder(self.progression_island_puzzles, self.progression_dungeon_secrets)
        QWidget.setTabOrder(self.progression_dungeon_secrets, self.progression_tingle_chests)
        QWidget.setTabOrder(self.progression_tingle_chests, self.progression_great_fairies)
        QWidget.setTabOrder(self.progression_great_fairies, self.progression_submarines)
        QWidget.setTabOrder(self.progression_submarines, self.progression_platforms_rafts)
        QWidget.setTabOrder(self.progression_platforms_rafts, self.progression_short_sidequests)
        QWidget.setTabOrder(self.progression_short_sidequests, self.progression_long_sidequests)
        QWidget.setTabOrder(self.progression_long_sidequests, self.progression_spoils_trading)
        QWidget.setTabOrder(self.progression_spoils_trading, self.progression_eye_reef_chests)
        QWidget.setTabOrder(self.progression_eye_reef_chests, self.progression_big_octos_gunboats)
        QWidget.setTabOrder(self.progression_big_octos_gunboats, self.progression_misc)
        QWidget.setTabOrder(self.progression_misc, self.progression_minigames)
        QWidget.setTabOrder(self.progression_minigames, self.progression_battlesquid)
        QWidget.setTabOrder(self.progression_battlesquid, self.progression_free_gifts)
        QWidget.setTabOrder(self.progression_free_gifts, self.progression_mail)
        QWidget.setTabOrder(self.progression_mail, self.progression_expensive_purchases)
        QWidget.setTabOrder(self.progression_expensive_purchases, self.progression_triforce_charts)
        QWidget.setTabOrder(self.progression_triforce_charts, self.progression_treasure_charts)
        QWidget.setTabOrder(self.progression_treasure_charts, self.sword_mode)
        QWidget.setTabOrder(self.sword_mode, self.num_starting_triforce_shards)
        QWidget.setTabOrder(self.num_starting_triforce_shards, self.shuffle_small_keys)
        QWidget.setTabOrder(self.shuffle_small_keys, self.shuffle_big_keys)
        QWidget.setTabOrder(self.shuffle_big_keys, self.shuffle_maps_and_compasses)
        QWidget.setTabOrder(self.shuffle_maps_and_compasses, self.chest_type_matches_contents)
        QWidget.setTabOrder(self.chest_type_matches_contents, self.trap_chests)
        QWidget.setTabOrder(self.trap_chests, self.randomize_dungeon_entrances)
        QWidget.setTabOrder(self.randomize_dungeon_entrances, self.randomize_boss_entrances)
        QWidget.setTabOrder(self.randomize_boss_entrances, self.randomize_miniboss_entrances)
        QWidget.setTabOrder(self.randomize_miniboss_entrances, self.randomize_secret_cave_entrances)
        QWidget.setTabOrder(self.randomize_secret_cave_entrances, self.randomize_secret_cave_inner_entrances)
        QWidget.setTabOrder(self.randomize_secret_cave_inner_entrances, self.randomize_fairy_fountain_entrances)
        QWidget.setTabOrder(self.randomize_fairy_fountain_entrances, self.mix_entrances)
        QWidget.setTabOrder(self.mix_entrances, self.randomize_starting_island)
        QWidget.setTabOrder(self.randomize_starting_island, self.randomize_charts)
        QWidget.setTabOrder(self.randomize_charts, self.randomize_enemy_palettes)
        QWidget.setTabOrder(self.randomize_enemy_palettes, self.randomize_enemies)
        QWidget.setTabOrder(self.randomize_enemies, self.swift_sail)
        QWidget.setTabOrder(self.swift_sail, self.instant_text_boxes)
        QWidget.setTabOrder(self.instant_text_boxes, self.switch_targeting_mode)
        QWidget.setTabOrder(self.switch_targeting_mode, self.reveal_full_sea_chart)
        QWidget.setTabOrder(self.reveal_full_sea_chart, self.invert_sea_compass_x_axis)
        QWidget.setTabOrder(self.invert_sea_compass_x_axis, self.skip_rematch_bosses)
        QWidget.setTabOrder(self.skip_rematch_bosses, self.add_shortcut_warps_between_dungeons)
        QWidget.setTabOrder(self.add_shortcut_warps_between_dungeons, self.remove_title_and_ending_videos)
        QWidget.setTabOrder(self.remove_title_and_ending_videos, self.remove_music)
        QWidget.setTabOrder(self.remove_music, self.invert_camera_x_axis)
        QWidget.setTabOrder(self.invert_camera_x_axis, self.permalink)
        QWidget.setTabOrder(self.permalink, self.about_button)
        QWidget.setTabOrder(self.about_button, self.reset_settings_to_default)
        QWidget.setTabOrder(self.reset_settings_to_default, self.randomize_button)
        QWidget.setTabOrder(self.randomize_button, self.randomized_gear)
        QWidget.setTabOrder(self.randomized_gear, self.starting_gear)
        QWidget.setTabOrder(self.starting_gear, self.remove_gear)
        QWidget.setTabOrder(self.remove_gear, self.add_gear)
        QWidget.setTabOrder(self.add_gear, self.starting_hcs)
        QWidget.setTabOrder(self.starting_hcs, self.starting_pohs)
        QWidget.setTabOrder(self.starting_pohs, self.num_extra_starting_items)
        QWidget.setTabOrder(self.num_extra_starting_items, self.required_bosses)
        QWidget.setTabOrder(self.required_bosses, self.num_required_bosses)
        QWidget.setTabOrder(self.num_required_bosses, self.hero_mode)
        QWidget.setTabOrder(self.hero_mode, self.logic_obscurity)
        QWidget.setTabOrder(self.logic_obscurity, self.logic_precision)
        QWidget.setTabOrder(self.logic_precision, self.hoho_hints)
        QWidget.setTabOrder(self.hoho_hints, self.fishmen_hints)
        QWidget.setTabOrder(self.fishmen_hints, self.korl_hints)
        QWidget.setTabOrder(self.korl_hints, self.num_item_hints)
        QWidget.setTabOrder(self.num_item_hints, self.num_location_hints)
        QWidget.setTabOrder(self.num_location_hints, self.num_barren_hints)
        QWidget.setTabOrder(self.num_barren_hints, self.num_path_hints)
        QWidget.setTabOrder(self.num_path_hints, self.cryptic_hints)
        QWidget.setTabOrder(self.cryptic_hints, self.prioritize_remote_hints)
        QWidget.setTabOrder(self.prioritize_remote_hints, self.hint_importance)
        QWidget.setTabOrder(self.hint_importance, self.do_not_generate_spoiler_log)
        QWidget.setTabOrder(self.do_not_generate_spoiler_log, self.dry_run)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Wind Waker Randomizer", None))
        self.label_for_clean_iso_path.setText(QCoreApplication.translate("MainWindow", u"Vanilla Wind Waker ISO [[?]](help)", None))
        self.label_for_output_folder.setText(QCoreApplication.translate("MainWindow", u"Randomized Output Folder", None))
        self.output_folder_browse_button.setText(QCoreApplication.translate("MainWindow", u"Browse", None))
        self.label_for_seed.setText(QCoreApplication.translate("MainWindow", u"Random Seed (optional)", None))
        self.generate_seed_button.setText(QCoreApplication.translate("MainWindow", u"New seed", None))
        self.clean_iso_path_browse_button.setText(QCoreApplication.translate("MainWindow", u"Browse", None))
        self.progression_locations_groupbox.setTitle(QCoreApplication.translate("MainWindow", u"Progression Locations: Where Should Progress Items Be Placed?", None))
        self.progression_submarines.setText(QCoreApplication.translate("MainWindow", u"Submarines", None))
        self.progression_battlesquid.setText(QCoreApplication.translate("MainWindow", u"Battlesquid Minigame", None))
        self.progression_mail.setText(QCoreApplication.translate("MainWindow", u"Mail", None))
        self.progression_puzzle_secret_caves.setText(QCoreApplication.translate("MainWindow", u"Puzzle Secret Caves", None))
        self.progression_island_puzzles.setText(QCoreApplication.translate("MainWindow", u"Island Puzzles", None))
        self.progression_big_octos_gunboats.setText(QCoreApplication.translate("MainWindow", u"Big Octos and Gunboats", None))
        self.progression_triforce_charts.setText(QCoreApplication.translate("MainWindow", u"Sunken Treasure (From Triforce Charts)", None))
        self.progression_minigames.setText(QCoreApplication.translate("MainWindow", u"Minigames", None))
        self.progression_dungeons.setText(QCoreApplication.translate("MainWindow", u"Dungeons", None))
        self.progression_treasure_charts.setText(QCoreApplication.translate("MainWindow", u"Sunken Treasure (From Treasure Charts)", None))
        self.progression_expensive_purchases.setText(QCoreApplication.translate("MainWindow", u"Expensive Purchases", None))
        self.progression_short_sidequests.setText(QCoreApplication.translate("MainWindow", u"Short Sidequests", None))
        self.progression_combat_secret_caves.setText(QCoreApplication.translate("MainWindow", u"Combat Secret Caves", None))
        self.progression_spoils_trading.setText(QCoreApplication.translate("MainWindow", u"Spoils Trading", None))
        self.progression_dungeon_secrets.setText(QCoreApplication.translate("MainWindow", u"Dungeon Secrets", None))
        self.progression_great_fairies.setText(QCoreApplication.translate("MainWindow", u"Great Fairies", None))
        self.progression_eye_reef_chests.setText(QCoreApplication.translate("MainWindow", u"Eye Reef Chests", None))
        self.progression_free_gifts.setText(QCoreApplication.translate("MainWindow", u"Free Gifts", None))
        self.progression_tingle_chests.setText(QCoreApplication.translate("MainWindow", u"Tingle Chests", None))
        self.progression_savage_labyrinth.setText(QCoreApplication.translate("MainWindow", u"Savage Labyrinth", None))
        self.progression_long_sidequests.setText(QCoreApplication.translate("MainWindow", u"Long Sidequests", None))
        self.progression_misc.setText(QCoreApplication.translate("MainWindow", u"Miscellaneous", None))
        self.progression_platforms_rafts.setText(QCoreApplication.translate("MainWindow", u"Lookout Platforms and Rafts", None))
        self.item_randomizer_modes_groupbox.setTitle(QCoreApplication.translate("MainWindow", u"Item Randomizer Modes", None))
        self.label_for_num_starting_triforce_shards.setText(QCoreApplication.translate("MainWindow", u"Triforce Shards to Start With", None))
        self.label_for_shuffle_maps_and_compasses.setText(QCoreApplication.translate("MainWindow", u"Dungeon Maps and Compasses", None))
        self.shuffle_maps_and_compasses.setItemText(0, QCoreApplication.translate("MainWindow", u"Vanilla", None))
        self.shuffle_maps_and_compasses.setItemText(1, QCoreApplication.translate("MainWindow", u"Start With", None))
        self.shuffle_maps_and_compasses.setItemText(2, QCoreApplication.translate("MainWindow", u"Own Dungeon", None))
        self.shuffle_maps_and_compasses.setItemText(3, QCoreApplication.translate("MainWindow", u"Any Dungeon", None))
        self.shuffle_maps_and_compasses.setItemText(4, QCoreApplication.translate("MainWindow", u"Overworld", None))
        self.shuffle_maps_and_compasses.setItemText(5, QCoreApplication.translate("MainWindow", u"Anywhere", None))

        self.shuffle_maps_and_compasses.setCurrentText(QCoreApplication.translate("MainWindow", u"Vanilla", None))
        self.label_for_shuffle_big_keys.setText(QCoreApplication.translate("MainWindow", u"Big Keys", None))
        self.shuffle_big_keys.setItemText(0, QCoreApplication.translate("MainWindow", u"Vanilla", None))
        self.shuffle_big_keys.setItemText(1, QCoreApplication.translate("MainWindow", u"Start With", None))
        self.shuffle_big_keys.setItemText(2, QCoreApplication.translate("MainWindow", u"Own Dungeon", None))
        self.shuffle_big_keys.setItemText(3, QCoreApplication.translate("MainWindow", u"Any Dungeon", None))
        self.shuffle_big_keys.setItemText(4, QCoreApplication.translate("MainWindow", u"Overworld", None))
        self.shuffle_big_keys.setItemText(5, QCoreApplication.translate("MainWindow", u"Anywhere", None))

        self.shuffle_big_keys.setCurrentText(QCoreApplication.translate("MainWindow", u"Vanilla", None))
        self.label_for_sword_mode.setText(QCoreApplication.translate("MainWindow", u"Sword Mode", None))
        self.sword_mode.setItemText(0, QCoreApplication.translate("MainWindow", u"Start with Hero's Sword", None))
        self.sword_mode.setItemText(1, QCoreApplication.translate("MainWindow", u"No Starting Sword", None))
        self.sword_mode.setItemText(2, QCoreApplication.translate("MainWindow", u"Swordless", None))

        self.label_for_shuffle_small_keys.setText(QCoreApplication.translate("MainWindow", u"Small Keys", None))
        self.shuffle_small_keys.setItemText(0, QCoreApplication.translate("MainWindow", u"Vanilla", None))
        self.shuffle_small_keys.setItemText(1, QCoreApplication.translate("MainWindow", u"Start With", None))
        self.shuffle_small_keys.setItemText(2, QCoreApplication.translate("MainWindow", u"Own Dungeon", None))
        self.shuffle_small_keys.setItemText(3, QCoreApplication.translate("MainWindow", u"Any Dungeon", None))
        self.shuffle_small_keys.setItemText(4, QCoreApplication.translate("MainWindow", u"Overworld", None))
        self.shuffle_small_keys.setItemText(5, QCoreApplication.translate("MainWindow", u"Anywhere", None))

        self.shuffle_small_keys.setCurrentText(QCoreApplication.translate("MainWindow", u"Vanilla", None))
        self.chest_type_matches_contents.setText(QCoreApplication.translate("MainWindow", u"Chest Type Matches Contents", None))
        self.trap_chests.setText(QCoreApplication.translate("MainWindow", u"Enable Trap Chests", None))
        self.entrance_randomizer_groupbox.setTitle(QCoreApplication.translate("MainWindow", u"Entrance Randomizer Options", None))
        self.randomize_dungeon_entrances.setText(QCoreApplication.translate("MainWindow", u"Dungeons", None))
        self.randomize_fairy_fountain_entrances.setText(QCoreApplication.translate("MainWindow", u"Fairy Fountains", None))
        self.randomize_miniboss_entrances.setText(QCoreApplication.translate("MainWindow", u"Nested Minibosses", None))
        self.randomize_boss_entrances.setText(QCoreApplication.translate("MainWindow", u"Nested Bosses", None))
        self.randomize_secret_cave_inner_entrances.setText(QCoreApplication.translate("MainWindow", u"Inner Secret Caves", None))
        self.randomize_secret_cave_entrances.setText(QCoreApplication.translate("MainWindow", u"Secret Caves", None))
        self.label_for_mix_entrances.setText(QCoreApplication.translate("MainWindow", u"Mixing", None))
        self.mix_entrances.setItemText(0, QCoreApplication.translate("MainWindow", u"Separate Dungeons From Caves & Fountains", None))
        self.mix_entrances.setItemText(1, QCoreApplication.translate("MainWindow", u"Mix Dungeons & Caves & Fountains", None))

        self.other_randomizers_groupbox.setTitle(QCoreApplication.translate("MainWindow", u"Other Randomizers", None))
        self.randomize_enemy_palettes.setText(QCoreApplication.translate("MainWindow", u"Randomize Enemy Palettes", None))
        self.randomize_charts.setText(QCoreApplication.translate("MainWindow", u"Randomize Charts", None))
        self.randomize_starting_island.setText(QCoreApplication.translate("MainWindow", u"Randomize Starting Island", None))
        self.randomize_enemies.setText(QCoreApplication.translate("MainWindow", u"Randomize Enemy Locations", None))
        self.convenience_tweaks_groupbox.setTitle(QCoreApplication.translate("MainWindow", u"Convenience Tweaks", None))
        self.switch_targeting_mode.setText(QCoreApplication.translate("MainWindow", u"Use 'Switch' Targeting Mode", None))
        self.invert_sea_compass_x_axis.setText(QCoreApplication.translate("MainWindow", u"Invert Sea Compass X-Axis", None))
        self.add_shortcut_warps_between_dungeons.setText(QCoreApplication.translate("MainWindow", u"Add Inter-Dungeon Shortcuts", None))
        self.invert_camera_x_axis.setText(QCoreApplication.translate("MainWindow", u"Invert Camera X-Axis", None))
        self.instant_text_boxes.setText(QCoreApplication.translate("MainWindow", u"Instant Text Boxes", None))
        self.skip_rematch_bosses.setText(QCoreApplication.translate("MainWindow", u"Skip Boss Rematches", None))
        self.swift_sail.setText(QCoreApplication.translate("MainWindow", u"Swift Sail", None))
        self.reveal_full_sea_chart.setText(QCoreApplication.translate("MainWindow", u"Reveal Full Sea Chart", None))
        self.remove_title_and_ending_videos.setText(QCoreApplication.translate("MainWindow", u"Remove Title and Ending Videos", None))
        self.remove_music.setText(QCoreApplication.translate("MainWindow", u"Remove Music", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_randomizer_settings), QCoreApplication.translate("MainWindow", u"Randomizer Settings", None))
        self.label_for_randomized_gear.setText(QCoreApplication.translate("MainWindow", u"Randomized Gear", None))
        self.remove_gear.setText(QCoreApplication.translate("MainWindow", u"<-", None))
        self.add_gear.setText(QCoreApplication.translate("MainWindow", u"->", None))
        self.label_for_starting_gear.setText(QCoreApplication.translate("MainWindow", u"Starting Gear", None))
        self.label_for_starting_hcs.setText(QCoreApplication.translate("MainWindow", u"Heart Containers", None))
        self.label_for_starting_pohs.setText(QCoreApplication.translate("MainWindow", u"Heart Pieces", None))
        self.current_health.setText(QCoreApplication.translate("MainWindow", u"Current Starting Health: 3 hearts", None))
        self.label_for_num_extra_starting_items.setText(QCoreApplication.translate("MainWindow", u"Extra Random Starting Items", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_starting_items), QCoreApplication.translate("MainWindow", u"Starting Items", None))
        self.required_bosses_groupbox.setTitle(QCoreApplication.translate("MainWindow", u"Required Bosses", None))
        self.label_for_num_required_bosses.setText(QCoreApplication.translate("MainWindow", u"Number of Required Bosses", None))
        self.required_bosses.setText(QCoreApplication.translate("MainWindow", u"Required Bosses Mode", None))
        self.difficulty_options_groupbox.setTitle(QCoreApplication.translate("MainWindow", u"Difficulty Options", None))
        self.hero_mode.setText(QCoreApplication.translate("MainWindow", u"Hero Mode", None))
        self.label_for_logic_precision.setText(QCoreApplication.translate("MainWindow", u"Precise Tricks Required", None))
        self.logic_precision.setItemText(0, QCoreApplication.translate("MainWindow", u"None", None))
        self.logic_precision.setItemText(1, QCoreApplication.translate("MainWindow", u"Normal", None))
        self.logic_precision.setItemText(2, QCoreApplication.translate("MainWindow", u"Hard", None))
        self.logic_precision.setItemText(3, QCoreApplication.translate("MainWindow", u"Very Hard", None))

        self.label_for_logic_obscurity.setText(QCoreApplication.translate("MainWindow", u"Obscure Tricks Required", None))
        self.logic_obscurity.setItemText(0, QCoreApplication.translate("MainWindow", u"None", None))
        self.logic_obscurity.setItemText(1, QCoreApplication.translate("MainWindow", u"Normal", None))
        self.logic_obscurity.setItemText(2, QCoreApplication.translate("MainWindow", u"Hard", None))
        self.logic_obscurity.setItemText(3, QCoreApplication.translate("MainWindow", u"Very Hard", None))

        self.hint_options_groupbox.setTitle(QCoreApplication.translate("MainWindow", u"Hint Options", None))
        self.hoho_hints.setText(QCoreApplication.translate("MainWindow", u"Place Hints on Old Man Ho Ho", None))
        self.prioritize_remote_hints.setText(QCoreApplication.translate("MainWindow", u"Prioritize Remote Location Hints", None))
        self.korl_hints.setText(QCoreApplication.translate("MainWindow", u"Place Hints on King of Red Lions", None))
        self.label_for_num_barren_hints.setText(QCoreApplication.translate("MainWindow", u"Barren Hints", None))
        self.cryptic_hints.setText(QCoreApplication.translate("MainWindow", u"Use Cryptic Text for Hints", None))
        self.fishmen_hints.setText(QCoreApplication.translate("MainWindow", u"Place Hints on Fishmen", None))
        self.label_for_num_location_hints.setText(QCoreApplication.translate("MainWindow", u"Location Hints", None))
        self.label_for_num_item_hints.setText(QCoreApplication.translate("MainWindow", u"Item Hints", None))
        self.label_for_num_path_hints.setText(QCoreApplication.translate("MainWindow", u"Path Hints", None))
        self.hint_importance.setText(QCoreApplication.translate("MainWindow", u"Hint Importance", None))
        self.additional_advanced_groupbox.setTitle(QCoreApplication.translate("MainWindow", u"Additional Advanced Options", None))
        self.do_not_generate_spoiler_log.setText(QCoreApplication.translate("MainWindow", u"Do Not Generate Spoiler Log", None))
        self.dry_run.setText(QCoreApplication.translate("MainWindow", u"Dry Run", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_advanced), QCoreApplication.translate("MainWindow", u"Advanced Options", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_player_customization), QCoreApplication.translate("MainWindow", u"Player Customization", None))
        self.option_description.setText("")
        self.label_for_permalink.setText(QCoreApplication.translate("MainWindow", u"Permalink (copy paste to share your settings):", None))
        self.update_checker_label.setText(QCoreApplication.translate("MainWindow", u"Checking for updates to the randomizer...", None))
        self.about_button.setText(QCoreApplication.translate("MainWindow", u"About", None))
        self.reset_settings_to_default.setText(QCoreApplication.translate("MainWindow", u"Reset All Settings to Default", None))
        self.randomize_button.setText(QCoreApplication.translate("MainWindow", u"Randomize", None))
    # retranslateUi

