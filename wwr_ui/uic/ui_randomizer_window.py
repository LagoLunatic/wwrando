# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'randomizer_window.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
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
        MainWindow.resize(1000, 775)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.scrollArea = QScrollArea(self.centralwidget)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setMinimumSize(QSize(600, 400))
        self.scrollArea.setFrameShape(QFrame.Shape.NoFrame)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 965, 618))
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
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.seed = QLineEdit(self.tab_randomizer_settings)
        self.seed.setObjectName(u"seed")

        self.gridLayout.addWidget(self.seed, 2, 1, 1, 1)

        self.label_for_clean_iso_path = QLabel(self.tab_randomizer_settings)
        self.label_for_clean_iso_path.setObjectName(u"label_for_clean_iso_path")
        self.label_for_clean_iso_path.setTextFormat(Qt.TextFormat.MarkdownText)

        self.gridLayout.addWidget(self.label_for_clean_iso_path, 0, 0, 1, 1)

        self.clean_iso_path = QLineEdit(self.tab_randomizer_settings)
        self.clean_iso_path.setObjectName(u"clean_iso_path")

        self.gridLayout.addWidget(self.clean_iso_path, 0, 1, 1, 1)

        self.label_for_output_folder = QLabel(self.tab_randomizer_settings)
        self.label_for_output_folder.setObjectName(u"label_for_output_folder")

        self.gridLayout.addWidget(self.label_for_output_folder, 1, 0, 1, 1)

        self.output_folder = QLineEdit(self.tab_randomizer_settings)
        self.output_folder.setObjectName(u"output_folder")

        self.gridLayout.addWidget(self.output_folder, 1, 1, 1, 1)

        self.output_folder_browse_button = QPushButton(self.tab_randomizer_settings)
        self.output_folder_browse_button.setObjectName(u"output_folder_browse_button")

        self.gridLayout.addWidget(self.output_folder_browse_button, 1, 2, 1, 1)

        self.label_for_seed = QLabel(self.tab_randomizer_settings)
        self.label_for_seed.setObjectName(u"label_for_seed")

        self.gridLayout.addWidget(self.label_for_seed, 2, 0, 1, 1)

        self.generate_seed_button = QPushButton(self.tab_randomizer_settings)
        self.generate_seed_button.setObjectName(u"generate_seed_button")

        self.gridLayout.addWidget(self.generate_seed_button, 2, 2, 1, 1)

        self.clean_iso_path_browse_button = QPushButton(self.tab_randomizer_settings)
        self.clean_iso_path_browse_button.setObjectName(u"clean_iso_path_browse_button")

        self.gridLayout.addWidget(self.clean_iso_path_browse_button, 0, 2, 1, 1)


        self.verticalLayout_3.addLayout(self.gridLayout)

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

        self.groupBox_2 = QGroupBox(self.tab_randomizer_settings)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.gridLayout_3 = QGridLayout(self.groupBox_2)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.trap_chests = QCheckBox(self.groupBox_2)
        self.trap_chests.setObjectName(u"trap_chests")

        self.gridLayout_3.addWidget(self.trap_chests, 6, 5, 1, 1)

        self.keylunacy = QCheckBox(self.groupBox_2)
        self.keylunacy.setObjectName(u"keylunacy")

        self.gridLayout_3.addWidget(self.keylunacy, 6, 3, 1, 1)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label_for_num_starting_triforce_shards = QLabel(self.groupBox_2)
        self.label_for_num_starting_triforce_shards.setObjectName(u"label_for_num_starting_triforce_shards")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_for_num_starting_triforce_shards.sizePolicy().hasHeightForWidth())
        self.label_for_num_starting_triforce_shards.setSizePolicy(sizePolicy)

        self.horizontalLayout_4.addWidget(self.label_for_num_starting_triforce_shards)

        self.num_starting_triforce_shards = QSpinBox(self.groupBox_2)
        self.num_starting_triforce_shards.setObjectName(u"num_starting_triforce_shards")

        self.horizontalLayout_4.addWidget(self.num_starting_triforce_shards)


        self.gridLayout_3.addLayout(self.horizontalLayout_4, 6, 2, 1, 1)

        self.chest_type_matches_contents = QCheckBox(self.groupBox_2)
        self.chest_type_matches_contents.setObjectName(u"chest_type_matches_contents")

        self.gridLayout_3.addWidget(self.chest_type_matches_contents, 6, 4, 1, 1)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_for_sword_mode = QLabel(self.groupBox_2)
        self.label_for_sword_mode.setObjectName(u"label_for_sword_mode")

        self.horizontalLayout_3.addWidget(self.label_for_sword_mode)

        self.sword_mode = QComboBox(self.groupBox_2)
        self.sword_mode.addItem("")
        self.sword_mode.addItem("")
        self.sword_mode.addItem("")
        self.sword_mode.setObjectName(u"sword_mode")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(1)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.sword_mode.sizePolicy().hasHeightForWidth())
        self.sword_mode.setSizePolicy(sizePolicy1)

        self.horizontalLayout_3.addWidget(self.sword_mode)


        self.gridLayout_3.addLayout(self.horizontalLayout_3, 6, 0, 1, 1)


        self.verticalLayout_3.addWidget(self.groupBox_2)

        self.horizontalLayout_19 = QHBoxLayout()
        self.horizontalLayout_19.setObjectName(u"horizontalLayout_19")
        self.groupBox_7 = QGroupBox(self.tab_randomizer_settings)
        self.groupBox_7.setObjectName(u"groupBox_7")
        self.gridLayout_9 = QGridLayout(self.groupBox_7)
        self.gridLayout_9.setObjectName(u"gridLayout_9")
        self.randomize_miniboss_entrances = QCheckBox(self.groupBox_7)
        self.randomize_miniboss_entrances.setObjectName(u"randomize_miniboss_entrances")

        self.gridLayout_9.addWidget(self.randomize_miniboss_entrances, 0, 2, 1, 1)

        self.randomize_dungeon_entrances = QCheckBox(self.groupBox_7)
        self.randomize_dungeon_entrances.setObjectName(u"randomize_dungeon_entrances")

        self.gridLayout_9.addWidget(self.randomize_dungeon_entrances, 0, 0, 1, 1)

        self.randomize_secret_cave_entrances = QCheckBox(self.groupBox_7)
        self.randomize_secret_cave_entrances.setObjectName(u"randomize_secret_cave_entrances")

        self.gridLayout_9.addWidget(self.randomize_secret_cave_entrances, 1, 0, 1, 1)

        self.randomize_boss_entrances = QCheckBox(self.groupBox_7)
        self.randomize_boss_entrances.setObjectName(u"randomize_boss_entrances")

        self.gridLayout_9.addWidget(self.randomize_boss_entrances, 0, 1, 1, 1)

        self.randomize_secret_cave_inner_entrances = QCheckBox(self.groupBox_7)
        self.randomize_secret_cave_inner_entrances.setObjectName(u"randomize_secret_cave_inner_entrances")

        self.gridLayout_9.addWidget(self.randomize_secret_cave_inner_entrances, 1, 1, 1, 1)

        self.randomize_fairy_fountain_entrances = QCheckBox(self.groupBox_7)
        self.randomize_fairy_fountain_entrances.setObjectName(u"randomize_fairy_fountain_entrances")

        self.gridLayout_9.addWidget(self.randomize_fairy_fountain_entrances, 1, 2, 1, 1)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.label_for_mix_entrances = QLabel(self.groupBox_7)
        self.label_for_mix_entrances.setObjectName(u"label_for_mix_entrances")

        self.horizontalLayout_5.addWidget(self.label_for_mix_entrances)

        self.mix_entrances = QComboBox(self.groupBox_7)
        self.mix_entrances.addItem("")
        self.mix_entrances.addItem("")
        self.mix_entrances.setObjectName(u"mix_entrances")
        sizePolicy1.setHeightForWidth(self.mix_entrances.sizePolicy().hasHeightForWidth())
        self.mix_entrances.setSizePolicy(sizePolicy1)

        self.horizontalLayout_5.addWidget(self.mix_entrances)


        self.gridLayout_9.addLayout(self.horizontalLayout_5, 2, 0, 1, 3)


        self.horizontalLayout_19.addWidget(self.groupBox_7)

        self.groupBox_8 = QGroupBox(self.tab_randomizer_settings)
        self.groupBox_8.setObjectName(u"groupBox_8")
        self.gridLayout_10 = QGridLayout(self.groupBox_8)
        self.gridLayout_10.setObjectName(u"gridLayout_10")
        self.randomize_enemies = QCheckBox(self.groupBox_8)
        self.randomize_enemies.setObjectName(u"randomize_enemies")

        self.gridLayout_10.addWidget(self.randomize_enemies, 1, 1, 1, 1)

        self.randomize_charts = QCheckBox(self.groupBox_8)
        self.randomize_charts.setObjectName(u"randomize_charts")

        self.gridLayout_10.addWidget(self.randomize_charts, 0, 1, 1, 1)

        self.randomize_enemy_palettes = QCheckBox(self.groupBox_8)
        self.randomize_enemy_palettes.setObjectName(u"randomize_enemy_palettes")

        self.gridLayout_10.addWidget(self.randomize_enemy_palettes, 1, 0, 1, 1)

        self.randomize_starting_island = QCheckBox(self.groupBox_8)
        self.randomize_starting_island.setObjectName(u"randomize_starting_island")

        self.gridLayout_10.addWidget(self.randomize_starting_island, 0, 0, 1, 1)

        self.widget_2 = QWidget(self.groupBox_8)
        self.widget_2.setObjectName(u"widget_2")

        self.gridLayout_10.addWidget(self.widget_2, 2, 0, 1, 1)


        self.horizontalLayout_19.addWidget(self.groupBox_8)


        self.verticalLayout_3.addLayout(self.horizontalLayout_19)

        self.groupBox_3 = QGroupBox(self.tab_randomizer_settings)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.gridLayout_4 = QGridLayout(self.groupBox_3)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.switch_targeting_mode = QCheckBox(self.groupBox_3)
        self.switch_targeting_mode.setObjectName(u"switch_targeting_mode")

        self.gridLayout_4.addWidget(self.switch_targeting_mode, 0, 2, 1, 1)

        self.invert_sea_compass_x_axis = QCheckBox(self.groupBox_3)
        self.invert_sea_compass_x_axis.setObjectName(u"invert_sea_compass_x_axis")

        self.gridLayout_4.addWidget(self.invert_sea_compass_x_axis, 0, 4, 1, 1)

        self.add_shortcut_warps_between_dungeons = QCheckBox(self.groupBox_3)
        self.add_shortcut_warps_between_dungeons.setObjectName(u"add_shortcut_warps_between_dungeons")

        self.gridLayout_4.addWidget(self.add_shortcut_warps_between_dungeons, 1, 1, 1, 1)

        self.invert_camera_x_axis = QCheckBox(self.groupBox_3)
        self.invert_camera_x_axis.setObjectName(u"invert_camera_x_axis")

        self.gridLayout_4.addWidget(self.invert_camera_x_axis, 1, 4, 1, 1)

        self.instant_text_boxes = QCheckBox(self.groupBox_3)
        self.instant_text_boxes.setObjectName(u"instant_text_boxes")
        self.instant_text_boxes.setChecked(True)

        self.gridLayout_4.addWidget(self.instant_text_boxes, 0, 1, 1, 1)

        self.skip_rematch_bosses = QCheckBox(self.groupBox_3)
        self.skip_rematch_bosses.setObjectName(u"skip_rematch_bosses")
        self.skip_rematch_bosses.setChecked(True)

        self.gridLayout_4.addWidget(self.skip_rematch_bosses, 1, 0, 1, 1)

        self.swift_sail = QCheckBox(self.groupBox_3)
        self.swift_sail.setObjectName(u"swift_sail")
        self.swift_sail.setChecked(True)

        self.gridLayout_4.addWidget(self.swift_sail, 0, 0, 1, 1)

        self.reveal_full_sea_chart = QCheckBox(self.groupBox_3)
        self.reveal_full_sea_chart.setObjectName(u"reveal_full_sea_chart")
        self.reveal_full_sea_chart.setChecked(True)

        self.gridLayout_4.addWidget(self.reveal_full_sea_chart, 0, 3, 1, 1)

        self.remove_title_and_ending_videos = QCheckBox(self.groupBox_3)
        self.remove_title_and_ending_videos.setObjectName(u"remove_title_and_ending_videos")
        self.remove_title_and_ending_videos.setChecked(True)

        self.gridLayout_4.addWidget(self.remove_title_and_ending_videos, 1, 2, 1, 1)

        self.remove_music = QCheckBox(self.groupBox_3)
        self.remove_music.setObjectName(u"remove_music")

        self.gridLayout_4.addWidget(self.remove_music, 1, 3, 1, 1)


        self.verticalLayout_3.addWidget(self.groupBox_3)

        self.verticalSpacer_7 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer_7)

        self.tabWidget.addTab(self.tab_randomizer_settings, "")
        self.tab_starting_items = QWidget()
        self.tab_starting_items.setObjectName(u"tab_starting_items")
        self.tab_starting_items.setEnabled(True)
        self.verticalLayout_4 = QVBoxLayout(self.tab_starting_items)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.label_for_randomized_gear = QLabel(self.tab_starting_items)
        self.label_for_randomized_gear.setObjectName(u"label_for_randomized_gear")

        self.verticalLayout_5.addWidget(self.label_for_randomized_gear)

        self.randomized_gear = QListView(self.tab_starting_items)
        self.randomized_gear.setObjectName(u"randomized_gear")
        self.randomized_gear.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.randomized_gear.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        self.verticalLayout_5.addWidget(self.randomized_gear)


        self.horizontalLayout_6.addLayout(self.verticalLayout_5)

        self.verticalLayout_6 = QVBoxLayout()
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_6.addItem(self.verticalSpacer)

        self.remove_gear = QPushButton(self.tab_starting_items)
        self.remove_gear.setObjectName(u"remove_gear")
        self.remove_gear.setMinimumSize(QSize(0, 80))

        self.verticalLayout_6.addWidget(self.remove_gear)

        self.add_gear = QPushButton(self.tab_starting_items)
        self.add_gear.setObjectName(u"add_gear")
        self.add_gear.setMinimumSize(QSize(0, 80))

        self.verticalLayout_6.addWidget(self.add_gear)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_6.addItem(self.verticalSpacer_2)


        self.horizontalLayout_6.addLayout(self.verticalLayout_6)

        self.verticalLayout_7 = QVBoxLayout()
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.label_for_starting_gear = QLabel(self.tab_starting_items)
        self.label_for_starting_gear.setObjectName(u"label_for_starting_gear")

        self.verticalLayout_7.addWidget(self.label_for_starting_gear)

        self.starting_gear = QListView(self.tab_starting_items)
        self.starting_gear.setObjectName(u"starting_gear")
        self.starting_gear.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.starting_gear.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        self.verticalLayout_7.addWidget(self.starting_gear)


        self.horizontalLayout_6.addLayout(self.verticalLayout_7)


        self.verticalLayout_4.addLayout(self.horizontalLayout_6)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.label_for_starting_hcs = QLabel(self.tab_starting_items)
        self.label_for_starting_hcs.setObjectName(u"label_for_starting_hcs")

        self.horizontalLayout_7.addWidget(self.label_for_starting_hcs)

        self.starting_hcs = QSpinBox(self.tab_starting_items)
        self.starting_hcs.setObjectName(u"starting_hcs")
        self.starting_hcs.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.starting_hcs.setMinimum(1)
        self.starting_hcs.setMaximum(9)
        self.starting_hcs.setValue(3)
        self.starting_hcs.setDisplayIntegerBase(10)

        self.horizontalLayout_7.addWidget(self.starting_hcs)

        self.label_for_starting_pohs = QLabel(self.tab_starting_items)
        self.label_for_starting_pohs.setObjectName(u"label_for_starting_pohs")

        self.horizontalLayout_7.addWidget(self.label_for_starting_pohs)

        self.starting_pohs = QSpinBox(self.tab_starting_items)
        self.starting_pohs.setObjectName(u"starting_pohs")
        self.starting_pohs.setMaximum(44)
        self.starting_pohs.setValue(0)
        self.starting_pohs.setDisplayIntegerBase(10)

        self.horizontalLayout_7.addWidget(self.starting_pohs)

        self.current_health = QLabel(self.tab_starting_items)
        self.current_health.setObjectName(u"current_health")

        self.horizontalLayout_7.addWidget(self.current_health)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer_3)


        self.verticalLayout_4.addLayout(self.horizontalLayout_7)

        self.horizontalLayout_random_starting_items = QHBoxLayout()
        self.horizontalLayout_random_starting_items.setObjectName(u"horizontalLayout_random_starting_items")
        self.label_for_num_extra_starting_items = QLabel(self.tab_starting_items)
        self.label_for_num_extra_starting_items.setObjectName(u"label_for_num_extra_starting_items")

        self.horizontalLayout_random_starting_items.addWidget(self.label_for_num_extra_starting_items)

        self.num_extra_starting_items = QSpinBox(self.tab_starting_items)
        self.num_extra_starting_items.setObjectName(u"num_extra_starting_items")
        self.num_extra_starting_items.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.num_extra_starting_items.setMaximum(3)
        self.num_extra_starting_items.setValue(0)
        self.num_extra_starting_items.setDisplayIntegerBase(10)

        self.horizontalLayout_random_starting_items.addWidget(self.num_extra_starting_items)

        self.horizontalSpacer_random_starting_item = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_random_starting_items.addItem(self.horizontalSpacer_random_starting_item)


        self.verticalLayout_4.addLayout(self.horizontalLayout_random_starting_items)

        self.tabWidget.addTab(self.tab_starting_items, "")
        self.tab_excluded_locations = QWidget()
        self.tab_excluded_locations.setObjectName(u"tab_excluded_locations")
        self.verticalLayout_12 = QVBoxLayout(self.tab_excluded_locations)
        self.verticalLayout_12.setObjectName(u"verticalLayout_12")
        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.verticalLayout_9 = QVBoxLayout()
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.label_for_progression_locations = QLabel(self.tab_excluded_locations)
        self.label_for_progression_locations.setObjectName(u"label_for_progression_locations")

        self.verticalLayout_9.addWidget(self.label_for_progression_locations)

        self.progression_locations = QListView(self.tab_excluded_locations)
        self.progression_locations.setObjectName(u"progression_locations")
        font = QFont()
        font.setPointSize(8)
        self.progression_locations.setFont(font)
        self.progression_locations.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.progression_locations.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.verticalLayout_9.addWidget(self.progression_locations)


        self.horizontalLayout_10.addLayout(self.verticalLayout_9)

        self.verticalLayout_10 = QVBoxLayout()
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_10.addItem(self.verticalSpacer_4)

        self.include_location = QPushButton(self.tab_excluded_locations)
        self.include_location.setObjectName(u"include_location")
        self.include_location.setMinimumSize(QSize(0, 80))

        self.verticalLayout_10.addWidget(self.include_location)

        self.exclude_location = QPushButton(self.tab_excluded_locations)
        self.exclude_location.setObjectName(u"exclude_location")
        self.exclude_location.setMinimumSize(QSize(0, 80))

        self.verticalLayout_10.addWidget(self.exclude_location)

        self.verticalSpacer_5 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_10.addItem(self.verticalSpacer_5)


        self.horizontalLayout_10.addLayout(self.verticalLayout_10)

        self.verticalLayout_11 = QVBoxLayout()
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.label_for_excluded_locations = QLabel(self.tab_excluded_locations)
        self.label_for_excluded_locations.setObjectName(u"label_for_excluded_locations")

        self.verticalLayout_11.addWidget(self.label_for_excluded_locations)

        self.excluded_locations = QListView(self.tab_excluded_locations)
        self.excluded_locations.setObjectName(u"excluded_locations")
        self.excluded_locations.setFont(font)
        self.excluded_locations.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.excluded_locations.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.verticalLayout_11.addWidget(self.excluded_locations)


        self.horizontalLayout_10.addLayout(self.verticalLayout_11)


        self.verticalLayout_12.addLayout(self.horizontalLayout_10)

        self.tabWidget.addTab(self.tab_excluded_locations, "")
        self.tab_advanced = QWidget()
        self.tab_advanced.setObjectName(u"tab_advanced")
        self.verticalLayout_8 = QVBoxLayout(self.tab_advanced)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.groupBox_4 = QGroupBox(self.tab_advanced)
        self.groupBox_4.setObjectName(u"groupBox_4")
        self.gridLayout_6 = QGridLayout(self.groupBox_4)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.required_bosses = QCheckBox(self.groupBox_4)
        self.required_bosses.setObjectName(u"required_bosses")

        self.gridLayout_6.addWidget(self.required_bosses, 0, 0, 1, 1)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.label_for_num_required_bosses = QLabel(self.groupBox_4)
        self.label_for_num_required_bosses.setObjectName(u"label_for_num_required_bosses")
        sizePolicy.setHeightForWidth(self.label_for_num_required_bosses.sizePolicy().hasHeightForWidth())
        self.label_for_num_required_bosses.setSizePolicy(sizePolicy)

        self.horizontalLayout_8.addWidget(self.label_for_num_required_bosses)

        self.num_required_bosses = QSpinBox(self.groupBox_4)
        self.num_required_bosses.setObjectName(u"num_required_bosses")

        self.horizontalLayout_8.addWidget(self.num_required_bosses)


        self.gridLayout_6.addLayout(self.horizontalLayout_8, 0, 1, 1, 1)

        self.widget_4 = QWidget(self.groupBox_4)
        self.widget_4.setObjectName(u"widget_4")

        self.gridLayout_6.addWidget(self.widget_4, 0, 2, 1, 1)

        self.widget_5 = QWidget(self.groupBox_4)
        self.widget_5.setObjectName(u"widget_5")

        self.gridLayout_6.addWidget(self.widget_5, 0, 3, 1, 1)


        self.verticalLayout_8.addWidget(self.groupBox_4)

        self.groupBox_9 = QGroupBox(self.tab_advanced)
        self.groupBox_9.setObjectName(u"groupBox_9")
        self.horizontalLayout_22 = QHBoxLayout(self.groupBox_9)
        self.horizontalLayout_22.setObjectName(u"horizontalLayout_22")
        self.hero_mode = QCheckBox(self.groupBox_9)
        self.hero_mode.setObjectName(u"hero_mode")

        self.horizontalLayout_22.addWidget(self.hero_mode)

        self.horizontalLayout_20 = QHBoxLayout()
        self.horizontalLayout_20.setObjectName(u"horizontalLayout_20")
        self.label_for_logic_obscurity = QLabel(self.groupBox_9)
        self.label_for_logic_obscurity.setObjectName(u"label_for_logic_obscurity")

        self.horizontalLayout_20.addWidget(self.label_for_logic_obscurity)

        self.logic_obscurity = QComboBox(self.groupBox_9)
        self.logic_obscurity.addItem("")
        self.logic_obscurity.addItem("")
        self.logic_obscurity.addItem("")
        self.logic_obscurity.addItem("")
        self.logic_obscurity.setObjectName(u"logic_obscurity")

        self.horizontalLayout_20.addWidget(self.logic_obscurity)


        self.horizontalLayout_22.addLayout(self.horizontalLayout_20)

        self.horizontalLayout_21 = QHBoxLayout()
        self.horizontalLayout_21.setObjectName(u"horizontalLayout_21")
        self.label_for_logic_precision = QLabel(self.groupBox_9)
        self.label_for_logic_precision.setObjectName(u"label_for_logic_precision")

        self.horizontalLayout_21.addWidget(self.label_for_logic_precision)

        self.logic_precision = QComboBox(self.groupBox_9)
        self.logic_precision.addItem("")
        self.logic_precision.addItem("")
        self.logic_precision.addItem("")
        self.logic_precision.addItem("")
        self.logic_precision.setObjectName(u"logic_precision")

        self.horizontalLayout_21.addWidget(self.logic_precision)


        self.horizontalLayout_22.addLayout(self.horizontalLayout_21)

        self.widget_10 = QWidget(self.groupBox_9)
        self.widget_10.setObjectName(u"widget_10")

        self.horizontalLayout_22.addWidget(self.widget_10)


        self.verticalLayout_8.addWidget(self.groupBox_9)

        self.groupBox_5 = QGroupBox(self.tab_advanced)
        self.groupBox_5.setObjectName(u"groupBox_5")
        self.gridLayout_7 = QGridLayout(self.groupBox_5)
        self.gridLayout_7.setObjectName(u"gridLayout_7")
        self.hoho_hints = QCheckBox(self.groupBox_5)
        self.hoho_hints.setObjectName(u"hoho_hints")
        self.hoho_hints.setChecked(True)

        self.gridLayout_7.addWidget(self.hoho_hints, 4, 0, 1, 1)

        self.prioritize_remote_hints = QCheckBox(self.groupBox_5)
        self.prioritize_remote_hints.setObjectName(u"prioritize_remote_hints")

        self.gridLayout_7.addWidget(self.prioritize_remote_hints, 6, 1, 1, 1)

        self.korl_hints = QCheckBox(self.groupBox_5)
        self.korl_hints.setObjectName(u"korl_hints")

        self.gridLayout_7.addWidget(self.korl_hints, 4, 2, 1, 1)

        self.horizontalLayout_16 = QHBoxLayout()
        self.horizontalLayout_16.setObjectName(u"horizontalLayout_16")
        self.label_for_num_barren_hints = QLabel(self.groupBox_5)
        self.label_for_num_barren_hints.setObjectName(u"label_for_num_barren_hints")

        self.horizontalLayout_16.addWidget(self.label_for_num_barren_hints)

        self.num_barren_hints = QSpinBox(self.groupBox_5)
        self.num_barren_hints.setObjectName(u"num_barren_hints")
        self.num_barren_hints.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        self.num_barren_hints.setMinimum(0)
        self.num_barren_hints.setMaximum(15)
        self.num_barren_hints.setValue(0)

        self.horizontalLayout_16.addWidget(self.num_barren_hints)

        self.widget_7 = QWidget(self.groupBox_5)
        self.widget_7.setObjectName(u"widget_7")

        self.horizontalLayout_16.addWidget(self.widget_7)


        self.gridLayout_7.addLayout(self.horizontalLayout_16, 5, 2, 1, 1)

        self.cryptic_hints = QCheckBox(self.groupBox_5)
        self.cryptic_hints.setObjectName(u"cryptic_hints")
        self.cryptic_hints.setChecked(True)

        self.gridLayout_7.addWidget(self.cryptic_hints, 6, 0, 1, 1)

        self.fishmen_hints = QCheckBox(self.groupBox_5)
        self.fishmen_hints.setObjectName(u"fishmen_hints")
        self.fishmen_hints.setChecked(True)

        self.gridLayout_7.addWidget(self.fishmen_hints, 4, 1, 1, 1)

        self.horizontalLayout_17 = QHBoxLayout()
        self.horizontalLayout_17.setObjectName(u"horizontalLayout_17")
        self.label_for_num_location_hints = QLabel(self.groupBox_5)
        self.label_for_num_location_hints.setObjectName(u"label_for_num_location_hints")

        self.horizontalLayout_17.addWidget(self.label_for_num_location_hints)

        self.num_location_hints = QSpinBox(self.groupBox_5)
        self.num_location_hints.setObjectName(u"num_location_hints")
        self.num_location_hints.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        self.num_location_hints.setMinimum(0)
        self.num_location_hints.setMaximum(15)
        self.num_location_hints.setValue(5)

        self.horizontalLayout_17.addWidget(self.num_location_hints)

        self.widget_8 = QWidget(self.groupBox_5)
        self.widget_8.setObjectName(u"widget_8")

        self.horizontalLayout_17.addWidget(self.widget_8)


        self.gridLayout_7.addLayout(self.horizontalLayout_17, 5, 1, 1, 1)

        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.label_for_num_item_hints = QLabel(self.groupBox_5)
        self.label_for_num_item_hints.setObjectName(u"label_for_num_item_hints")

        self.horizontalLayout_9.addWidget(self.label_for_num_item_hints)

        self.num_item_hints = QSpinBox(self.groupBox_5)
        self.num_item_hints.setObjectName(u"num_item_hints")
        self.num_item_hints.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        self.num_item_hints.setMinimum(0)
        self.num_item_hints.setMaximum(15)
        self.num_item_hints.setValue(15)

        self.horizontalLayout_9.addWidget(self.num_item_hints)

        self.widget_9 = QWidget(self.groupBox_5)
        self.widget_9.setObjectName(u"widget_9")

        self.horizontalLayout_9.addWidget(self.widget_9)


        self.gridLayout_7.addLayout(self.horizontalLayout_9, 5, 0, 1, 1)

        self.horizontalLayout_15 = QHBoxLayout()
        self.horizontalLayout_15.setObjectName(u"horizontalLayout_15")
        self.label_for_num_path_hints = QLabel(self.groupBox_5)
        self.label_for_num_path_hints.setObjectName(u"label_for_num_path_hints")

        self.horizontalLayout_15.addWidget(self.label_for_num_path_hints)

        self.num_path_hints = QSpinBox(self.groupBox_5)
        self.num_path_hints.setObjectName(u"num_path_hints")
        self.num_path_hints.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        self.num_path_hints.setMinimum(0)
        self.num_path_hints.setMaximum(15)
        self.num_path_hints.setValue(0)

        self.horizontalLayout_15.addWidget(self.num_path_hints)

        self.widget_6 = QWidget(self.groupBox_5)
        self.widget_6.setObjectName(u"widget_6")

        self.horizontalLayout_15.addWidget(self.widget_6)


        self.gridLayout_7.addLayout(self.horizontalLayout_15, 5, 3, 1, 1)

        self.hint_importance = QCheckBox(self.groupBox_5)
        self.hint_importance.setObjectName(u"hint_importance")

        self.gridLayout_7.addWidget(self.hint_importance, 6, 2, 1, 1)


        self.verticalLayout_8.addWidget(self.groupBox_5)

        self.groupBox_6 = QGroupBox(self.tab_advanced)
        self.groupBox_6.setObjectName(u"groupBox_6")
        self.gridLayout_8 = QGridLayout(self.groupBox_6)
        self.gridLayout_8.setObjectName(u"gridLayout_8")
        self.do_not_generate_spoiler_log = QCheckBox(self.groupBox_6)
        self.do_not_generate_spoiler_log.setObjectName(u"do_not_generate_spoiler_log")

        self.gridLayout_8.addWidget(self.do_not_generate_spoiler_log, 0, 0, 1, 1)

        self.widget_11 = QWidget(self.groupBox_6)
        self.widget_11.setObjectName(u"widget_11")

        self.gridLayout_8.addWidget(self.widget_11, 0, 2, 1, 1)

        self.widget_12 = QWidget(self.groupBox_6)
        self.widget_12.setObjectName(u"widget_12")

        self.gridLayout_8.addWidget(self.widget_12, 0, 3, 1, 1)

        self.dry_run = QCheckBox(self.groupBox_6)
        self.dry_run.setObjectName(u"dry_run")

        self.gridLayout_8.addWidget(self.dry_run, 0, 1, 1, 1)


        self.verticalLayout_8.addWidget(self.groupBox_6)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_8.addItem(self.verticalSpacer_3)

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
        self.option_description.setTextFormat(Qt.TextFormat.RichText)
        self.option_description.setWordWrap(True)

        self.verticalLayout.addWidget(self.option_description)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_for_permalink = QLabel(self.centralwidget)
        self.label_for_permalink.setObjectName(u"label_for_permalink")

        self.horizontalLayout.addWidget(self.label_for_permalink)

        self.permalink = QLineEdit(self.centralwidget)
        self.permalink.setObjectName(u"permalink")

        self.horizontalLayout.addWidget(self.permalink)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.update_checker_label = QLabel(self.centralwidget)
        self.update_checker_label.setObjectName(u"update_checker_label")
        self.update_checker_label.setOpenExternalLinks(True)

        self.verticalLayout.addWidget(self.update_checker_label)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.about_button = QPushButton(self.centralwidget)
        self.about_button.setObjectName(u"about_button")

        self.horizontalLayout_2.addWidget(self.about_button)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.reset_settings_to_default = QPushButton(self.centralwidget)
        self.reset_settings_to_default.setObjectName(u"reset_settings_to_default")
        self.reset_settings_to_default.setMinimumSize(QSize(180, 0))

        self.horizontalLayout_2.addWidget(self.reset_settings_to_default)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)

        self.randomize_button = QPushButton(self.centralwidget)
        self.randomize_button.setObjectName(u"randomize_button")

        self.horizontalLayout_2.addWidget(self.randomize_button)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

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
        QWidget.setTabOrder(self.num_starting_triforce_shards, self.keylunacy)
        QWidget.setTabOrder(self.keylunacy, self.chest_type_matches_contents)
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
        QWidget.setTabOrder(self.prioritize_remote_hints, self.do_not_generate_spoiler_log)
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
        self.groupBox_2.setTitle(QCoreApplication.translate("MainWindow", u"Item Randomizer Modes", None))
        self.trap_chests.setText(QCoreApplication.translate("MainWindow", u"Enable Trap Chests", None))
        self.keylunacy.setText(QCoreApplication.translate("MainWindow", u"Key-Lunacy", None))
        self.label_for_num_starting_triforce_shards.setText(QCoreApplication.translate("MainWindow", u"Triforce Shards to Start With", None))
        self.chest_type_matches_contents.setText(QCoreApplication.translate("MainWindow", u"Chest Type Matches Contents", None))
        self.label_for_sword_mode.setText(QCoreApplication.translate("MainWindow", u"Sword Mode", None))
        self.sword_mode.setItemText(0, QCoreApplication.translate("MainWindow", u"Start with Hero's Sword", None))
        self.sword_mode.setItemText(1, QCoreApplication.translate("MainWindow", u"No Starting Sword", None))
        self.sword_mode.setItemText(2, QCoreApplication.translate("MainWindow", u"Swordless", None))

        self.groupBox_7.setTitle(QCoreApplication.translate("MainWindow", u"Entrance Randomizer Options", None))
        self.randomize_miniboss_entrances.setText(QCoreApplication.translate("MainWindow", u"Nested Minibosses", None))
        self.randomize_dungeon_entrances.setText(QCoreApplication.translate("MainWindow", u"Dungeons", None))
        self.randomize_secret_cave_entrances.setText(QCoreApplication.translate("MainWindow", u"Secret Caves", None))
        self.randomize_boss_entrances.setText(QCoreApplication.translate("MainWindow", u"Nested Bosses", None))
        self.randomize_secret_cave_inner_entrances.setText(QCoreApplication.translate("MainWindow", u"Inner Secret Caves", None))
        self.randomize_fairy_fountain_entrances.setText(QCoreApplication.translate("MainWindow", u"Fairy Fountains", None))
        self.label_for_mix_entrances.setText(QCoreApplication.translate("MainWindow", u"Mixing", None))
        self.mix_entrances.setItemText(0, QCoreApplication.translate("MainWindow", u"Separate Dungeons From Caves & Fountains", None))
        self.mix_entrances.setItemText(1, QCoreApplication.translate("MainWindow", u"Mix Dungeons & Caves & Fountains", None))

        self.groupBox_8.setTitle(QCoreApplication.translate("MainWindow", u"Other Randomizers", None))
        self.randomize_enemies.setText(QCoreApplication.translate("MainWindow", u"Randomize Enemy Locations", None))
        self.randomize_charts.setText(QCoreApplication.translate("MainWindow", u"Randomize Charts", None))
        self.randomize_enemy_palettes.setText(QCoreApplication.translate("MainWindow", u"Randomize Enemy Palettes", None))
        self.randomize_starting_island.setText(QCoreApplication.translate("MainWindow", u"Randomize Starting Island", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("MainWindow", u"Convenience Tweaks", None))
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
        self.label_for_progression_locations.setText(QCoreApplication.translate("MainWindow", u"Progression Locations", None))
        self.include_location.setText(QCoreApplication.translate("MainWindow", u"<-", None))
        self.exclude_location.setText(QCoreApplication.translate("MainWindow", u"->", None))
        self.label_for_excluded_locations.setText(QCoreApplication.translate("MainWindow", u"Excluded Locations", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_excluded_locations), QCoreApplication.translate("MainWindow", u"Excluded Locations", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("MainWindow", u"Required Bosses", None))
        self.required_bosses.setText(QCoreApplication.translate("MainWindow", u"Required Bosses Mode", None))
        self.label_for_num_required_bosses.setText(QCoreApplication.translate("MainWindow", u"Number of Required Bosses", None))
        self.groupBox_9.setTitle(QCoreApplication.translate("MainWindow", u"Difficulty Options", None))
        self.hero_mode.setText(QCoreApplication.translate("MainWindow", u"Hero Mode", None))
        self.label_for_logic_obscurity.setText(QCoreApplication.translate("MainWindow", u"Obscure Tricks Required", None))
        self.logic_obscurity.setItemText(0, QCoreApplication.translate("MainWindow", u"None", None))
        self.logic_obscurity.setItemText(1, QCoreApplication.translate("MainWindow", u"Normal", None))
        self.logic_obscurity.setItemText(2, QCoreApplication.translate("MainWindow", u"Hard", None))
        self.logic_obscurity.setItemText(3, QCoreApplication.translate("MainWindow", u"Very Hard", None))

        self.label_for_logic_precision.setText(QCoreApplication.translate("MainWindow", u"Precise Tricks Required", None))
        self.logic_precision.setItemText(0, QCoreApplication.translate("MainWindow", u"None", None))
        self.logic_precision.setItemText(1, QCoreApplication.translate("MainWindow", u"Normal", None))
        self.logic_precision.setItemText(2, QCoreApplication.translate("MainWindow", u"Hard", None))
        self.logic_precision.setItemText(3, QCoreApplication.translate("MainWindow", u"Very Hard", None))

        self.groupBox_5.setTitle(QCoreApplication.translate("MainWindow", u"Hint Options", None))
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
        self.groupBox_6.setTitle(QCoreApplication.translate("MainWindow", u"Additional Advanced Options", None))
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

