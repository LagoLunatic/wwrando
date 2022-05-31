# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'randomizer_window.ui'
##
## Created by: Qt User Interface Compiler version 6.2.2
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QComboBox,
    QFrame, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QListView, QMainWindow,
    QPushButton, QScrollArea, QSizePolicy, QSpacerItem,
    QSpinBox, QTabWidget, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(943, 844)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.scrollArea = QScrollArea(self.centralwidget)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setFrameShape(QFrame.NoFrame)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 925, 710))
        self.verticalLayout_4 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.tabWidget = QTabWidget(self.scrollAreaWidgetContents)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setEnabled(True)
        self.tab_randomizer_settings = QWidget()
        self.tab_randomizer_settings.setObjectName(u"tab_randomizer_settings")
        self.verticalLayout_2 = QVBoxLayout(self.tab_randomizer_settings)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.seed = QLineEdit(self.tab_randomizer_settings)
        self.seed.setObjectName(u"seed")

        self.gridLayout.addWidget(self.seed, 2, 1, 1, 1)

        self.label_for_clean_iso_path = QLabel(self.tab_randomizer_settings)
        self.label_for_clean_iso_path.setObjectName(u"label_for_clean_iso_path")

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


        self.verticalLayout_2.addLayout(self.gridLayout)

        self.groupBox = QGroupBox(self.tab_randomizer_settings)
        self.groupBox.setObjectName(u"groupBox")
        self.gridLayout_2 = QGridLayout(self.groupBox)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.progression_platforms_rafts = QCheckBox(self.groupBox)
        self.progression_platforms_rafts.setObjectName(u"progression_platforms_rafts")

        self.gridLayout_2.addWidget(self.progression_platforms_rafts, 7, 0, 1, 1)

        self.progression_long_sidequests = QCheckBox(self.groupBox)
        self.progression_long_sidequests.setObjectName(u"progression_long_sidequests")

        self.gridLayout_2.addWidget(self.progression_long_sidequests, 4, 1, 1, 1)

        self.progression_dungeons = QCheckBox(self.groupBox)
        self.progression_dungeons.setObjectName(u"progression_dungeons")
        self.progression_dungeons.setChecked(True)

        self.gridLayout_2.addWidget(self.progression_dungeons, 0, 0, 1, 1)

        self.progression_short_sidequests = QCheckBox(self.groupBox)
        self.progression_short_sidequests.setObjectName(u"progression_short_sidequests")

        self.gridLayout_2.addWidget(self.progression_short_sidequests, 4, 0, 1, 1)

        self.progression_treasure_charts = QCheckBox(self.groupBox)
        self.progression_treasure_charts.setObjectName(u"progression_treasure_charts")

        self.gridLayout_2.addWidget(self.progression_treasure_charts, 9, 1, 1, 1)

        self.progression_submarines = QCheckBox(self.groupBox)
        self.progression_submarines.setObjectName(u"progression_submarines")
        self.progression_submarines.setChecked(False)

        self.gridLayout_2.addWidget(self.progression_submarines, 7, 1, 1, 1)

        self.progression_triforce_charts = QCheckBox(self.groupBox)
        self.progression_triforce_charts.setObjectName(u"progression_triforce_charts")

        self.gridLayout_2.addWidget(self.progression_triforce_charts, 9, 0, 1, 1)

        self.progression_spoils_trading = QCheckBox(self.groupBox)
        self.progression_spoils_trading.setObjectName(u"progression_spoils_trading")

        self.gridLayout_2.addWidget(self.progression_spoils_trading, 4, 2, 1, 1)

        self.progression_minigames = QCheckBox(self.groupBox)
        self.progression_minigames.setObjectName(u"progression_minigames")

        self.gridLayout_2.addWidget(self.progression_minigames, 6, 0, 1, 1)

        self.progression_battlesquid = QCheckBox(self.groupBox)
        self.progression_battlesquid.setObjectName(u"progression_battlesquid")

        self.gridLayout_2.addWidget(self.progression_battlesquid, 6, 1, 1, 1)

        self.progression_big_octos_gunboats = QCheckBox(self.groupBox)
        self.progression_big_octos_gunboats.setObjectName(u"progression_big_octos_gunboats")

        self.gridLayout_2.addWidget(self.progression_big_octos_gunboats, 7, 2, 1, 1)

        self.progression_expensive_purchases = QCheckBox(self.groupBox)
        self.progression_expensive_purchases.setObjectName(u"progression_expensive_purchases")
        self.progression_expensive_purchases.setChecked(True)

        self.gridLayout_2.addWidget(self.progression_expensive_purchases, 6, 2, 1, 1)

        self.progression_great_fairies = QCheckBox(self.groupBox)
        self.progression_great_fairies.setObjectName(u"progression_great_fairies")
        self.progression_great_fairies.setChecked(True)

        self.gridLayout_2.addWidget(self.progression_great_fairies, 1, 0, 1, 1)

        self.progression_combat_secret_caves = QCheckBox(self.groupBox)
        self.progression_combat_secret_caves.setObjectName(u"progression_combat_secret_caves")

        self.gridLayout_2.addWidget(self.progression_combat_secret_caves, 0, 2, 1, 1)

        self.progression_free_gifts = QCheckBox(self.groupBox)
        self.progression_free_gifts.setObjectName(u"progression_free_gifts")
        self.progression_free_gifts.setChecked(True)

        self.gridLayout_2.addWidget(self.progression_free_gifts, 1, 1, 1, 1)

        self.progression_savage_labyrinth = QCheckBox(self.groupBox)
        self.progression_savage_labyrinth.setObjectName(u"progression_savage_labyrinth")

        self.gridLayout_2.addWidget(self.progression_savage_labyrinth, 0, 3, 1, 1)

        self.progression_puzzle_secret_caves = QCheckBox(self.groupBox)
        self.progression_puzzle_secret_caves.setObjectName(u"progression_puzzle_secret_caves")
        self.progression_puzzle_secret_caves.setChecked(True)

        self.gridLayout_2.addWidget(self.progression_puzzle_secret_caves, 0, 1, 1, 1)

        self.progression_misc = QCheckBox(self.groupBox)
        self.progression_misc.setObjectName(u"progression_misc")
        self.progression_misc.setChecked(True)

        self.gridLayout_2.addWidget(self.progression_misc, 1, 2, 1, 1)

        self.progression_eye_reef_chests = QCheckBox(self.groupBox)
        self.progression_eye_reef_chests.setObjectName(u"progression_eye_reef_chests")

        self.gridLayout_2.addWidget(self.progression_eye_reef_chests, 7, 3, 1, 1)

        self.progression_mail = QCheckBox(self.groupBox)
        self.progression_mail.setObjectName(u"progression_mail")

        self.gridLayout_2.addWidget(self.progression_mail, 4, 3, 1, 1)

        self.progression_tingle_chests = QCheckBox(self.groupBox)
        self.progression_tingle_chests.setObjectName(u"progression_tingle_chests")

        self.gridLayout_2.addWidget(self.progression_tingle_chests, 1, 3, 1, 1)

        self.progression_island_puzzles = QCheckBox(self.groupBox)
        self.progression_island_puzzles.setObjectName(u"progression_island_puzzles")

        self.gridLayout_2.addWidget(self.progression_island_puzzles, 6, 3, 1, 1)


        self.verticalLayout_2.addWidget(self.groupBox)

        self.groupBox_2 = QGroupBox(self.tab_randomizer_settings)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.gridLayout_3 = QGridLayout(self.groupBox_2)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.label_for_num_starting_triforce_shards = QLabel(self.groupBox_2)
        self.label_for_num_starting_triforce_shards.setObjectName(u"label_for_num_starting_triforce_shards")
        sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_for_num_starting_triforce_shards.sizePolicy().hasHeightForWidth())
        self.label_for_num_starting_triforce_shards.setSizePolicy(sizePolicy)

        self.horizontalLayout_6.addWidget(self.label_for_num_starting_triforce_shards)

        self.num_starting_triforce_shards = QComboBox(self.groupBox_2)
        self.num_starting_triforce_shards.addItem("")
        self.num_starting_triforce_shards.addItem("")
        self.num_starting_triforce_shards.addItem("")
        self.num_starting_triforce_shards.addItem("")
        self.num_starting_triforce_shards.addItem("")
        self.num_starting_triforce_shards.addItem("")
        self.num_starting_triforce_shards.addItem("")
        self.num_starting_triforce_shards.addItem("")
        self.num_starting_triforce_shards.addItem("")
        self.num_starting_triforce_shards.setObjectName(u"num_starting_triforce_shards")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(1)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.num_starting_triforce_shards.sizePolicy().hasHeightForWidth())
        self.num_starting_triforce_shards.setSizePolicy(sizePolicy1)
        self.num_starting_triforce_shards.setMaximumSize(QSize(40, 16777215))

        self.horizontalLayout_6.addWidget(self.num_starting_triforce_shards)

        self.widget_2 = QWidget(self.groupBox_2)
        self.widget_2.setObjectName(u"widget_2")

        self.horizontalLayout_6.addWidget(self.widget_2)


        self.gridLayout_3.addLayout(self.horizontalLayout_6, 1, 3, 1, 1)

        self.randomize_starting_island = QCheckBox(self.groupBox_2)
        self.randomize_starting_island.setObjectName(u"randomize_starting_island")

        self.gridLayout_3.addWidget(self.randomize_starting_island, 2, 1, 1, 1)

        self.randomize_enemy_palettes = QCheckBox(self.groupBox_2)
        self.randomize_enemy_palettes.setObjectName(u"randomize_enemy_palettes")

        self.gridLayout_3.addWidget(self.randomize_enemy_palettes, 2, 2, 1, 1)

        self.randomize_music = QCheckBox(self.groupBox_2)
        self.randomize_music.setObjectName(u"randomize_music")

        self.gridLayout_3.addWidget(self.randomize_music, 2, 3, 1, 1)

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
        sizePolicy1.setHeightForWidth(self.sword_mode.sizePolicy().hasHeightForWidth())
        self.sword_mode.setSizePolicy(sizePolicy1)

        self.horizontalLayout_3.addWidget(self.sword_mode)


        self.gridLayout_3.addLayout(self.horizontalLayout_3, 0, 0, 1, 1)

        self.randomize_enemies = QCheckBox(self.groupBox_2)
        self.randomize_enemies.setObjectName(u"randomize_enemies")

        self.gridLayout_3.addWidget(self.randomize_enemies, 0, 3, 1, 1)

        self.chest_type_matches_contents = QCheckBox(self.groupBox_2)
        self.chest_type_matches_contents.setObjectName(u"chest_type_matches_contents")

        self.gridLayout_3.addWidget(self.chest_type_matches_contents, 3, 0, 1, 1)

        self.randomize_charts = QCheckBox(self.groupBox_2)
        self.randomize_charts.setObjectName(u"randomize_charts")

        self.gridLayout_3.addWidget(self.randomize_charts, 2, 0, 1, 1)

        self.race_mode = QCheckBox(self.groupBox_2)
        self.race_mode.setObjectName(u"race_mode")

        self.gridLayout_3.addWidget(self.race_mode, 1, 1, 1, 1)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.label_for_num_race_mode_dungeons = QLabel(self.groupBox_2)
        self.label_for_num_race_mode_dungeons.setObjectName(u"label_for_num_race_mode_dungeons")
        sizePolicy.setHeightForWidth(self.label_for_num_race_mode_dungeons.sizePolicy().hasHeightForWidth())
        self.label_for_num_race_mode_dungeons.setSizePolicy(sizePolicy)

        self.horizontalLayout_5.addWidget(self.label_for_num_race_mode_dungeons)

        self.num_race_mode_dungeons = QComboBox(self.groupBox_2)
        self.num_race_mode_dungeons.addItem("")
        self.num_race_mode_dungeons.addItem("")
        self.num_race_mode_dungeons.addItem("")
        self.num_race_mode_dungeons.addItem("")
        self.num_race_mode_dungeons.addItem("")
        self.num_race_mode_dungeons.addItem("")
        self.num_race_mode_dungeons.setObjectName(u"num_race_mode_dungeons")
        sizePolicy1.setHeightForWidth(self.num_race_mode_dungeons.sizePolicy().hasHeightForWidth())
        self.num_race_mode_dungeons.setSizePolicy(sizePolicy1)
        self.num_race_mode_dungeons.setMaximumSize(QSize(40, 16777215))

        self.horizontalLayout_5.addWidget(self.num_race_mode_dungeons)

        self.widget_1 = QWidget(self.groupBox_2)
        self.widget_1.setObjectName(u"widget_1")

        self.horizontalLayout_5.addWidget(self.widget_1)


        self.gridLayout_3.addLayout(self.horizontalLayout_5, 1, 2, 1, 1)

        self.keylunacy = QCheckBox(self.groupBox_2)
        self.keylunacy.setObjectName(u"keylunacy")

        self.gridLayout_3.addWidget(self.keylunacy, 1, 0, 1, 1)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label_for_randomize_entrances = QLabel(self.groupBox_2)
        self.label_for_randomize_entrances.setObjectName(u"label_for_randomize_entrances")

        self.horizontalLayout_4.addWidget(self.label_for_randomize_entrances)

        self.randomize_entrances = QComboBox(self.groupBox_2)
        self.randomize_entrances.addItem("")
        self.randomize_entrances.addItem("")
        self.randomize_entrances.addItem("")
        self.randomize_entrances.addItem("")
        self.randomize_entrances.addItem("")
        self.randomize_entrances.setObjectName(u"randomize_entrances")
        sizePolicy1.setHeightForWidth(self.randomize_entrances.sizePolicy().hasHeightForWidth())
        self.randomize_entrances.setSizePolicy(sizePolicy1)

        self.horizontalLayout_4.addWidget(self.randomize_entrances)

        self.widget = QWidget(self.groupBox_2)
        self.widget.setObjectName(u"widget")

        self.horizontalLayout_4.addWidget(self.widget)


        self.gridLayout_3.addLayout(self.horizontalLayout_4, 0, 1, 1, 2)


        self.verticalLayout_2.addWidget(self.groupBox_2)

        self.groupBox_3 = QGroupBox(self.tab_randomizer_settings)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.gridLayout_7 = QGridLayout(self.groupBox_3)
        self.gridLayout_7.setObjectName(u"gridLayout_7")
        self.fishmen_hints = QCheckBox(self.groupBox_3)
        self.fishmen_hints.setObjectName(u"fishmen_hints")
        self.fishmen_hints.setChecked(True)

        self.gridLayout_7.addWidget(self.fishmen_hints, 0, 0, 1, 1)

        self.hoho_hints = QCheckBox(self.groupBox_3)
        self.hoho_hints.setObjectName(u"hoho_hints")
        self.hoho_hints.setChecked(True)

        self.gridLayout_7.addWidget(self.hoho_hints, 0, 1, 1, 1)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.label_for_num_hints = QLabel(self.groupBox_3)
        self.label_for_num_hints.setObjectName(u"label_for_num_hints")

        self.horizontalLayout_7.addWidget(self.label_for_num_hints)

        self.num_hints = QSpinBox(self.groupBox_3)
        self.num_hints.setObjectName(u"num_hints")
        self.num_hints.setMinimum(1)
        self.num_hints.setMaximum(32)
        self.num_hints.setValue(20)

        self.horizontalLayout_7.addWidget(self.num_hints)

        self.widget_3 = QWidget(self.groupBox_3)
        self.widget_3.setObjectName(u"widget_3")

        self.horizontalLayout_7.addWidget(self.widget_3)


        self.gridLayout_7.addLayout(self.horizontalLayout_7, 0, 2, 1, 1)

        self.widget_4 = QWidget(self.groupBox_3)
        self.widget_4.setObjectName(u"widget_4")

        self.gridLayout_7.addWidget(self.widget_4, 0, 3, 1, 1)


        self.verticalLayout_2.addWidget(self.groupBox_3)

        self.groupBox_4 = QGroupBox(self.tab_randomizer_settings)
        self.groupBox_4.setObjectName(u"groupBox_4")
        self.gridLayout_4 = QGridLayout(self.groupBox_4)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.remove_title_and_ending_videos = QCheckBox(self.groupBox_4)
        self.remove_title_and_ending_videos.setObjectName(u"remove_title_and_ending_videos")
        self.remove_title_and_ending_videos.setChecked(True)

        self.gridLayout_4.addWidget(self.remove_title_and_ending_videos, 1, 2, 1, 1)

        self.instant_text_boxes = QCheckBox(self.groupBox_4)
        self.instant_text_boxes.setObjectName(u"instant_text_boxes")
        self.instant_text_boxes.setChecked(True)

        self.gridLayout_4.addWidget(self.instant_text_boxes, 0, 1, 1, 1)

        self.swift_sail = QCheckBox(self.groupBox_4)
        self.swift_sail.setObjectName(u"swift_sail")
        self.swift_sail.setChecked(True)

        self.gridLayout_4.addWidget(self.swift_sail, 0, 0, 1, 1)

        self.invert_sea_compass_x_axis = QCheckBox(self.groupBox_4)
        self.invert_sea_compass_x_axis.setObjectName(u"invert_sea_compass_x_axis")

        self.gridLayout_4.addWidget(self.invert_sea_compass_x_axis, 2, 0, 1, 1)

        self.remove_music = QCheckBox(self.groupBox_4)
        self.remove_music.setObjectName(u"remove_music")

        self.gridLayout_4.addWidget(self.remove_music, 1, 3, 1, 1)

        self.invert_camera_x_axis = QCheckBox(self.groupBox_4)
        self.invert_camera_x_axis.setObjectName(u"invert_camera_x_axis")

        self.gridLayout_4.addWidget(self.invert_camera_x_axis, 0, 3, 1, 1)

        self.reveal_full_sea_chart = QCheckBox(self.groupBox_4)
        self.reveal_full_sea_chart.setObjectName(u"reveal_full_sea_chart")
        self.reveal_full_sea_chart.setChecked(True)

        self.gridLayout_4.addWidget(self.reveal_full_sea_chart, 0, 2, 1, 1)

        self.add_shortcut_warps_between_dungeons = QCheckBox(self.groupBox_4)
        self.add_shortcut_warps_between_dungeons.setObjectName(u"add_shortcut_warps_between_dungeons")

        self.gridLayout_4.addWidget(self.add_shortcut_warps_between_dungeons, 1, 1, 1, 1)

        self.skip_rematch_bosses = QCheckBox(self.groupBox_4)
        self.skip_rematch_bosses.setObjectName(u"skip_rematch_bosses")
        self.skip_rematch_bosses.setChecked(True)

        self.gridLayout_4.addWidget(self.skip_rematch_bosses, 1, 0, 1, 1)


        self.verticalLayout_2.addWidget(self.groupBox_4)

        self.groupBox_5 = QGroupBox(self.tab_randomizer_settings)
        self.groupBox_5.setObjectName(u"groupBox_5")
        self.gridLayout_6 = QGridLayout(self.groupBox_5)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.widget_6 = QWidget(self.groupBox_5)
        self.widget_6.setObjectName(u"widget_6")

        self.gridLayout_6.addWidget(self.widget_6, 0, 3, 1, 1)

        self.disable_tingle_chests_with_tingle_bombs = QCheckBox(self.groupBox_5)
        self.disable_tingle_chests_with_tingle_bombs.setObjectName(u"disable_tingle_chests_with_tingle_bombs")

        self.gridLayout_6.addWidget(self.disable_tingle_chests_with_tingle_bombs, 0, 1, 1, 1)

        self.do_not_generate_spoiler_log = QCheckBox(self.groupBox_5)
        self.do_not_generate_spoiler_log.setObjectName(u"do_not_generate_spoiler_log")

        self.gridLayout_6.addWidget(self.do_not_generate_spoiler_log, 0, 0, 1, 1)

        self.widget_5 = QWidget(self.groupBox_5)
        self.widget_5.setObjectName(u"widget_5")

        self.gridLayout_6.addWidget(self.widget_5, 0, 2, 1, 1)


        self.verticalLayout_2.addWidget(self.groupBox_5)

        self.tabWidget.addTab(self.tab_randomizer_settings, "")
        self.tab_starting_items = QWidget()
        self.tab_starting_items.setObjectName(u"tab_starting_items")
        self.tab_starting_items.setEnabled(True)
        self.verticalLayout_10 = QVBoxLayout(self.tab_starting_items)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.verticalLayout_8 = QVBoxLayout()
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.label_for_randomized_gear = QLabel(self.tab_starting_items)
        self.label_for_randomized_gear.setObjectName(u"label_for_randomized_gear")

        self.verticalLayout_8.addWidget(self.label_for_randomized_gear)

        self.randomized_gear = QListView(self.tab_starting_items)
        self.randomized_gear.setObjectName(u"randomized_gear")
        self.randomized_gear.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.randomized_gear.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.verticalLayout_8.addWidget(self.randomized_gear)


        self.horizontalLayout_8.addLayout(self.verticalLayout_8)

        self.verticalLayout_7 = QVBoxLayout()
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_7.addItem(self.verticalSpacer)

        self.remove_gear = QPushButton(self.tab_starting_items)
        self.remove_gear.setObjectName(u"remove_gear")
        self.remove_gear.setMinimumSize(QSize(0, 80))

        self.verticalLayout_7.addWidget(self.remove_gear)

        self.add_gear = QPushButton(self.tab_starting_items)
        self.add_gear.setObjectName(u"add_gear")
        self.add_gear.setMinimumSize(QSize(0, 80))

        self.verticalLayout_7.addWidget(self.add_gear)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_7.addItem(self.verticalSpacer_2)


        self.horizontalLayout_8.addLayout(self.verticalLayout_7)

        self.verticalLayout_9 = QVBoxLayout()
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.label_for_starting_gear = QLabel(self.tab_starting_items)
        self.label_for_starting_gear.setObjectName(u"label_for_starting_gear")

        self.verticalLayout_9.addWidget(self.label_for_starting_gear)

        self.starting_gear = QListView(self.tab_starting_items)
        self.starting_gear.setObjectName(u"starting_gear")
        self.starting_gear.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.starting_gear.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.verticalLayout_9.addWidget(self.starting_gear)


        self.horizontalLayout_8.addLayout(self.verticalLayout_9)


        self.verticalLayout_10.addLayout(self.horizontalLayout_8)

        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.label_for_starting_hcs = QLabel(self.tab_starting_items)
        self.label_for_starting_hcs.setObjectName(u"label_for_starting_hcs")

        self.horizontalLayout_9.addWidget(self.label_for_starting_hcs)

        self.starting_hcs = QSpinBox(self.tab_starting_items)
        self.starting_hcs.setObjectName(u"starting_hcs")
        self.starting_hcs.setLayoutDirection(Qt.LeftToRight)
        self.starting_hcs.setMaximum(6)
        self.starting_hcs.setValue(0)
        self.starting_hcs.setProperty("displayIntegerBase", 10)

        self.horizontalLayout_9.addWidget(self.starting_hcs)

        self.label_for_starting_pohs = QLabel(self.tab_starting_items)
        self.label_for_starting_pohs.setObjectName(u"label_for_starting_pohs")

        self.horizontalLayout_9.addWidget(self.label_for_starting_pohs)

        self.starting_pohs = QSpinBox(self.tab_starting_items)
        self.starting_pohs.setObjectName(u"starting_pohs")
        self.starting_pohs.setMaximum(44)
        self.starting_pohs.setValue(0)
        self.starting_pohs.setProperty("displayIntegerBase", 10)

        self.horizontalLayout_9.addWidget(self.starting_pohs)

        self.current_health = QLabel(self.tab_starting_items)
        self.current_health.setObjectName(u"current_health")

        self.horizontalLayout_9.addWidget(self.current_health)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_9.addItem(self.horizontalSpacer_3)


        self.verticalLayout_10.addLayout(self.horizontalLayout_9)

        self.tabWidget.addTab(self.tab_starting_items, "")
        self.tab_player_customization = QWidget()
        self.tab_player_customization.setObjectName(u"tab_player_customization")
        self.verticalLayout_3 = QVBoxLayout(self.tab_player_customization)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.gridLayout_5 = QGridLayout()
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.horizontalLayout_12 = QHBoxLayout()
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.label_for_custom_color_preset = QLabel(self.tab_player_customization)
        self.label_for_custom_color_preset.setObjectName(u"label_for_custom_color_preset")

        self.horizontalLayout_12.addWidget(self.label_for_custom_color_preset)

        self.custom_color_preset = QComboBox(self.tab_player_customization)
        self.custom_color_preset.setObjectName(u"custom_color_preset")

        self.horizontalLayout_12.addWidget(self.custom_color_preset)


        self.gridLayout_5.addLayout(self.horizontalLayout_12, 2, 0, 1, 1)

        self.horizontalLayout_13 = QHBoxLayout()
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.randomize_all_custom_colors_together = QPushButton(self.tab_player_customization)
        self.randomize_all_custom_colors_together.setObjectName(u"randomize_all_custom_colors_together")

        self.horizontalLayout_13.addWidget(self.randomize_all_custom_colors_together)

        self.randomize_all_custom_colors_separately = QPushButton(self.tab_player_customization)
        self.randomize_all_custom_colors_separately.setObjectName(u"randomize_all_custom_colors_separately")

        self.horizontalLayout_13.addWidget(self.randomize_all_custom_colors_separately)


        self.gridLayout_5.addLayout(self.horizontalLayout_13, 2, 1, 1, 1)

        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.label_for_custom_player_model = QLabel(self.tab_player_customization)
        self.label_for_custom_player_model.setObjectName(u"label_for_custom_player_model")

        self.horizontalLayout_10.addWidget(self.label_for_custom_player_model)

        self.custom_player_model = QComboBox(self.tab_player_customization)
        self.custom_player_model.setObjectName(u"custom_player_model")

        self.horizontalLayout_10.addWidget(self.custom_player_model)


        self.gridLayout_5.addLayout(self.horizontalLayout_10, 1, 0, 1, 1)

        self.horizontalLayout_11 = QHBoxLayout()
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.player_in_casual_clothes = QCheckBox(self.tab_player_customization)
        self.player_in_casual_clothes.setObjectName(u"player_in_casual_clothes")

        self.horizontalLayout_11.addWidget(self.player_in_casual_clothes)

        self.disable_custom_player_voice = QCheckBox(self.tab_player_customization)
        self.disable_custom_player_voice.setObjectName(u"disable_custom_player_voice")

        self.horizontalLayout_11.addWidget(self.disable_custom_player_voice)

        self.disable_custom_player_items = QCheckBox(self.tab_player_customization)
        self.disable_custom_player_items.setObjectName(u"disable_custom_player_items")

        self.horizontalLayout_11.addWidget(self.disable_custom_player_items)


        self.gridLayout_5.addLayout(self.horizontalLayout_11, 1, 1, 1, 1)

        self.install_custom_model = QPushButton(self.tab_player_customization)
        self.install_custom_model.setObjectName(u"install_custom_model")

        self.gridLayout_5.addWidget(self.install_custom_model, 0, 0, 1, 2)


        self.verticalLayout_3.addLayout(self.gridLayout_5)

        self.custom_model_comment = QLabel(self.tab_player_customization)
        self.custom_model_comment.setObjectName(u"custom_model_comment")
        self.custom_model_comment.setMaximumSize(QSize(810, 16777215))
        self.custom_model_comment.setWordWrap(True)

        self.verticalLayout_3.addWidget(self.custom_model_comment)

        self.horizontalLayout_14 = QHBoxLayout()
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.custom_colors_layout = QVBoxLayout()
        self.custom_colors_layout.setObjectName(u"custom_colors_layout")

        self.verticalLayout_5.addLayout(self.custom_colors_layout)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_5.addItem(self.verticalSpacer_3)


        self.horizontalLayout_14.addLayout(self.verticalLayout_5)

        self.verticalLayout_6 = QVBoxLayout()
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.custom_model_preview_label = QLabel(self.tab_player_customization)
        self.custom_model_preview_label.setObjectName(u"custom_model_preview_label")

        self.verticalLayout_6.addWidget(self.custom_model_preview_label)

        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_6.addItem(self.verticalSpacer_4)


        self.horizontalLayout_14.addLayout(self.verticalLayout_6)


        self.verticalLayout_3.addLayout(self.horizontalLayout_14)

        self.tabWidget.addTab(self.tab_player_customization, "")

        self.verticalLayout_4.addWidget(self.tabWidget)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout.addWidget(self.scrollArea)

        self.option_description = QLabel(self.centralwidget)
        self.option_description.setObjectName(u"option_description")
        self.option_description.setMinimumSize(QSize(0, 32))
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

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.reset_settings_to_default = QPushButton(self.centralwidget)
        self.reset_settings_to_default.setObjectName(u"reset_settings_to_default")
        self.reset_settings_to_default.setMinimumSize(QSize(180, 0))

        self.horizontalLayout_2.addWidget(self.reset_settings_to_default)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)

        self.randomize_button = QPushButton(self.centralwidget)
        self.randomize_button.setObjectName(u"randomize_button")

        self.horizontalLayout_2.addWidget(self.randomize_button)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(0)
        self.num_race_mode_dungeons.setCurrentIndex(3)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Wind Waker Randomizer", None))
        self.label_for_clean_iso_path.setText(QCoreApplication.translate("MainWindow", u"Clean WW ISO", None))
        self.label_for_output_folder.setText(QCoreApplication.translate("MainWindow", u"Output Folder", None))
        self.output_folder_browse_button.setText(QCoreApplication.translate("MainWindow", u"Browse", None))
        self.label_for_seed.setText(QCoreApplication.translate("MainWindow", u"Seed (optional)", None))
        self.generate_seed_button.setText(QCoreApplication.translate("MainWindow", u"New seed", None))
        self.clean_iso_path_browse_button.setText(QCoreApplication.translate("MainWindow", u"Browse", None))
        self.groupBox.setTitle(QCoreApplication.translate("MainWindow", u"Where Should Progress Items Appear?", None))
        self.progression_platforms_rafts.setText(QCoreApplication.translate("MainWindow", u"Lookout Platforms and Rafts", None))
        self.progression_long_sidequests.setText(QCoreApplication.translate("MainWindow", u"Long Sidequests", None))
        self.progression_dungeons.setText(QCoreApplication.translate("MainWindow", u"Dungeons", None))
        self.progression_short_sidequests.setText(QCoreApplication.translate("MainWindow", u"Short Sidequests", None))
        self.progression_treasure_charts.setText(QCoreApplication.translate("MainWindow", u"Sunken Treasure (From Treasure Charts)", None))
        self.progression_submarines.setText(QCoreApplication.translate("MainWindow", u"Submarines", None))
        self.progression_triforce_charts.setText(QCoreApplication.translate("MainWindow", u"Sunken Treasure (From Triforce Charts)", None))
        self.progression_spoils_trading.setText(QCoreApplication.translate("MainWindow", u"Spoils Trading", None))
        self.progression_minigames.setText(QCoreApplication.translate("MainWindow", u"Minigames", None))
        self.progression_battlesquid.setText(QCoreApplication.translate("MainWindow", u"Battlesquid Minigame", None))
        self.progression_big_octos_gunboats.setText(QCoreApplication.translate("MainWindow", u"Big Octos and Gunboats", None))
        self.progression_expensive_purchases.setText(QCoreApplication.translate("MainWindow", u"Expensive Purchases", None))
        self.progression_great_fairies.setText(QCoreApplication.translate("MainWindow", u"Great Fairies", None))
        self.progression_combat_secret_caves.setText(QCoreApplication.translate("MainWindow", u"Combat Secret Caves", None))
        self.progression_free_gifts.setText(QCoreApplication.translate("MainWindow", u"Free Gifts", None))
        self.progression_savage_labyrinth.setText(QCoreApplication.translate("MainWindow", u"Savage Labyrinth", None))
        self.progression_puzzle_secret_caves.setText(QCoreApplication.translate("MainWindow", u"Puzzle Secret Caves", None))
        self.progression_misc.setText(QCoreApplication.translate("MainWindow", u"Miscellaneous", None))
        self.progression_eye_reef_chests.setText(QCoreApplication.translate("MainWindow", u"Eye Reef Chests", None))
        self.progression_mail.setText(QCoreApplication.translate("MainWindow", u"Mail", None))
        self.progression_tingle_chests.setText(QCoreApplication.translate("MainWindow", u"Tingle Chests", None))
        self.progression_island_puzzles.setText(QCoreApplication.translate("MainWindow", u"Island Puzzles", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("MainWindow", u"Additional Randomization Options", None))
        self.label_for_num_starting_triforce_shards.setText(QCoreApplication.translate("MainWindow", u"Triforce Shards to Start With", None))
        self.num_starting_triforce_shards.setItemText(0, QCoreApplication.translate("MainWindow", u"0", None))
        self.num_starting_triforce_shards.setItemText(1, QCoreApplication.translate("MainWindow", u"1", None))
        self.num_starting_triforce_shards.setItemText(2, QCoreApplication.translate("MainWindow", u"2", None))
        self.num_starting_triforce_shards.setItemText(3, QCoreApplication.translate("MainWindow", u"3", None))
        self.num_starting_triforce_shards.setItemText(4, QCoreApplication.translate("MainWindow", u"4", None))
        self.num_starting_triforce_shards.setItemText(5, QCoreApplication.translate("MainWindow", u"5", None))
        self.num_starting_triforce_shards.setItemText(6, QCoreApplication.translate("MainWindow", u"6", None))
        self.num_starting_triforce_shards.setItemText(7, QCoreApplication.translate("MainWindow", u"7", None))
        self.num_starting_triforce_shards.setItemText(8, QCoreApplication.translate("MainWindow", u"8", None))

        self.randomize_starting_island.setText(QCoreApplication.translate("MainWindow", u"Randomize Starting Island", None))
        self.randomize_enemy_palettes.setText(QCoreApplication.translate("MainWindow", u"Randomize Enemy Palettes", None))
        self.randomize_music.setText(QCoreApplication.translate("MainWindow", u"Randomize Music", None))
        self.label_for_sword_mode.setText(QCoreApplication.translate("MainWindow", u"Sword Mode", None))
        self.sword_mode.setItemText(0, QCoreApplication.translate("MainWindow", u"Start with Hero's Sword", None))
        self.sword_mode.setItemText(1, QCoreApplication.translate("MainWindow", u"No Starting Sword", None))
        self.sword_mode.setItemText(2, QCoreApplication.translate("MainWindow", u"Swordless", None))

        self.randomize_enemies.setText(QCoreApplication.translate("MainWindow", u"Randomize Enemy Locations", None))
        self.chest_type_matches_contents.setText(QCoreApplication.translate("MainWindow", u"Chest Type Matches Contents", None))
        self.randomize_charts.setText(QCoreApplication.translate("MainWindow", u"Randomize Charts", None))
        self.race_mode.setText(QCoreApplication.translate("MainWindow", u"Race Mode", None))
        self.label_for_num_race_mode_dungeons.setText(QCoreApplication.translate("MainWindow", u"Race Mode Required Dungeons", None))
        self.num_race_mode_dungeons.setItemText(0, QCoreApplication.translate("MainWindow", u"1", None))
        self.num_race_mode_dungeons.setItemText(1, QCoreApplication.translate("MainWindow", u"2", None))
        self.num_race_mode_dungeons.setItemText(2, QCoreApplication.translate("MainWindow", u"3", None))
        self.num_race_mode_dungeons.setItemText(3, QCoreApplication.translate("MainWindow", u"4", None))
        self.num_race_mode_dungeons.setItemText(4, QCoreApplication.translate("MainWindow", u"5", None))
        self.num_race_mode_dungeons.setItemText(5, QCoreApplication.translate("MainWindow", u"6", None))

        self.keylunacy.setText(QCoreApplication.translate("MainWindow", u"Key-Lunacy", None))
        self.label_for_randomize_entrances.setText(QCoreApplication.translate("MainWindow", u"Randomize Entrances", None))
        self.randomize_entrances.setItemText(0, QCoreApplication.translate("MainWindow", u"Disabled", None))
        self.randomize_entrances.setItemText(1, QCoreApplication.translate("MainWindow", u"Dungeons", None))
        self.randomize_entrances.setItemText(2, QCoreApplication.translate("MainWindow", u"Secret Caves", None))
        self.randomize_entrances.setItemText(3, QCoreApplication.translate("MainWindow", u"Dungeons & Secret Caves (Separately)", None))
        self.randomize_entrances.setItemText(4, QCoreApplication.translate("MainWindow", u"Dungeons & Secret Caves (Together)", None))

        self.groupBox_3.setTitle(QCoreApplication.translate("MainWindow", u"Hint Options", None))
        self.fishmen_hints.setText(QCoreApplication.translate("MainWindow", u"Place Hints on Fishmen", None))
        self.hoho_hints.setText(QCoreApplication.translate("MainWindow", u"Place Hints on Old Man Ho Ho", None))
        self.label_for_num_hints.setText(QCoreApplication.translate("MainWindow", u"Hint Count", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("MainWindow", u"Convenience Tweaks", None))
        self.remove_title_and_ending_videos.setText(QCoreApplication.translate("MainWindow", u"Remove Title and Ending Videos", None))
        self.instant_text_boxes.setText(QCoreApplication.translate("MainWindow", u"Instant Text Boxes", None))
        self.swift_sail.setText(QCoreApplication.translate("MainWindow", u"Swift Sail", None))
        self.invert_sea_compass_x_axis.setText(QCoreApplication.translate("MainWindow", u"Invert Sea Compass X-Axis", None))
        self.remove_music.setText(QCoreApplication.translate("MainWindow", u"Remove Music", None))
        self.invert_camera_x_axis.setText(QCoreApplication.translate("MainWindow", u"Invert Camera X-Axis", None))
        self.reveal_full_sea_chart.setText(QCoreApplication.translate("MainWindow", u"Reveal Full Sea Chart", None))
        self.add_shortcut_warps_between_dungeons.setText(QCoreApplication.translate("MainWindow", u"Add Shortcut Warps Between Dungeons", None))
        self.skip_rematch_bosses.setText(QCoreApplication.translate("MainWindow", u"Skip Boss Rematches", None))
        self.groupBox_5.setTitle(QCoreApplication.translate("MainWindow", u"Advanced Options", None))
        self.disable_tingle_chests_with_tingle_bombs.setText(QCoreApplication.translate("MainWindow", u"Tingle Bombs Don't Open Tingle Chests", None))
        self.do_not_generate_spoiler_log.setText(QCoreApplication.translate("MainWindow", u"Do Not Generate Spoiler Log", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_randomizer_settings), QCoreApplication.translate("MainWindow", u"Randomizer Settings", None))
        self.label_for_randomized_gear.setText(QCoreApplication.translate("MainWindow", u"Randomized Gear", None))
        self.remove_gear.setText(QCoreApplication.translate("MainWindow", u"<-", None))
        self.add_gear.setText(QCoreApplication.translate("MainWindow", u"->", None))
        self.label_for_starting_gear.setText(QCoreApplication.translate("MainWindow", u"Starting Gear", None))
        self.label_for_starting_hcs.setText(QCoreApplication.translate("MainWindow", u"Heart Containers", None))
        self.label_for_starting_pohs.setText(QCoreApplication.translate("MainWindow", u"Heart Pieces", None))
        self.current_health.setText(QCoreApplication.translate("MainWindow", u"Current Starting Health: 3 hearts", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_starting_items), QCoreApplication.translate("MainWindow", u"Starting Items", None))
        self.label_for_custom_color_preset.setText(QCoreApplication.translate("MainWindow", u"Color Preset", None))
        self.randomize_all_custom_colors_together.setText(QCoreApplication.translate("MainWindow", u"Randomize Colors Orderly", None))
        self.randomize_all_custom_colors_separately.setText(QCoreApplication.translate("MainWindow", u"Randomize Colors Chaotically", None))
        self.label_for_custom_player_model.setText(QCoreApplication.translate("MainWindow", u"Player Model", None))
        self.player_in_casual_clothes.setText(QCoreApplication.translate("MainWindow", u"Casual Clothes", None))
        self.disable_custom_player_voice.setText(QCoreApplication.translate("MainWindow", u"Disable Custom Voice", None))
        self.disable_custom_player_items.setText(QCoreApplication.translate("MainWindow", u"Disable Custom Items", None))
        self.install_custom_model.setText(QCoreApplication.translate("MainWindow", u"Install a Custom Model or Model Pack", None))
        self.custom_model_comment.setText("")
        self.custom_model_preview_label.setText("")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_player_customization), QCoreApplication.translate("MainWindow", u"Player Customization", None))
        self.option_description.setText("")
        self.label_for_permalink.setText(QCoreApplication.translate("MainWindow", u"Permalink (copy paste to share your settings):", None))
        self.update_checker_label.setText(QCoreApplication.translate("MainWindow", u"Checking for updates to the randomizer...", None))
        self.about_button.setText(QCoreApplication.translate("MainWindow", u"About", None))
        self.reset_settings_to_default.setText(QCoreApplication.translate("MainWindow", u"Reset All Settings to Default", None))
        self.randomize_button.setText(QCoreApplication.translate("MainWindow", u"Randomize", None))
    # retranslateUi

