# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'cosmetic_tab.ui'
##
## Created by: Qt User Interface Compiler version 6.5.2
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QGridLayout,
    QHBoxLayout, QLabel, QPushButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

class Ui_CosmeticTab(object):
    def setupUi(self, CosmeticTab):
        if not CosmeticTab.objectName():
            CosmeticTab.setObjectName(u"CosmeticTab")
        CosmeticTab.resize(864, 553)
        self.horizontalLayout_14 = QHBoxLayout(CosmeticTab)
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.layoutV_for_0_cosmetic_options = QVBoxLayout()
        self.layoutV_for_0_cosmetic_options.setObjectName(u"layoutV_for_0_cosmetic_options")
        self.layoutG_for_0_model_settings = QGridLayout()
        self.layoutG_for_0_model_settings.setObjectName(u"layoutG_for_0_model_settings")
        self.layoutH_for_random_colors = QHBoxLayout()
        self.layoutH_for_random_colors.setObjectName(u"layoutH_for_random_colors")
        self.randomize_all_custom_colors_together = QPushButton(CosmeticTab)
        self.randomize_all_custom_colors_together.setObjectName(u"randomize_all_custom_colors_together")

        self.layoutH_for_random_colors.addWidget(self.randomize_all_custom_colors_together)

        self.randomize_all_custom_colors_separately = QPushButton(CosmeticTab)
        self.randomize_all_custom_colors_separately.setObjectName(u"randomize_all_custom_colors_separately")

        self.layoutH_for_random_colors.addWidget(self.randomize_all_custom_colors_separately)


        self.layoutG_for_0_model_settings.addLayout(self.layoutH_for_random_colors, 2, 1, 1, 1)

        self.layoutH_for_2_color_present = QHBoxLayout()
        self.layoutH_for_2_color_present.setObjectName(u"layoutH_for_2_color_present")
        self.label_for_custom_color_preset = QLabel(CosmeticTab)
        self.label_for_custom_color_preset.setObjectName(u"label_for_custom_color_preset")

        self.layoutH_for_2_color_present.addWidget(self.label_for_custom_color_preset)

        self.custom_color_preset = QComboBox(CosmeticTab)
        self.custom_color_preset.setObjectName(u"custom_color_preset")

        self.layoutH_for_2_color_present.addWidget(self.custom_color_preset)


        self.layoutG_for_0_model_settings.addLayout(self.layoutH_for_2_color_present, 2, 0, 1, 1)

        self.layoutH_for_0_model = QHBoxLayout()
        self.layoutH_for_0_model.setObjectName(u"layoutH_for_0_model")
        self.label_for_custom_player_model = QLabel(CosmeticTab)
        self.label_for_custom_player_model.setObjectName(u"label_for_custom_player_model")

        self.layoutH_for_0_model.addWidget(self.label_for_custom_player_model)

        self.custom_player_model = QComboBox(CosmeticTab)
        self.custom_player_model.setObjectName(u"custom_player_model")

        self.layoutH_for_0_model.addWidget(self.custom_player_model)


        self.layoutG_for_0_model_settings.addLayout(self.layoutH_for_0_model, 1, 0, 1, 1)

        self.layoutH_for_1_custom_options = QHBoxLayout()
        self.layoutH_for_1_custom_options.setObjectName(u"layoutH_for_1_custom_options")
        self.player_in_casual_clothes = QCheckBox(CosmeticTab)
        self.player_in_casual_clothes.setObjectName(u"player_in_casual_clothes")

        self.layoutH_for_1_custom_options.addWidget(self.player_in_casual_clothes)

        self.disable_custom_player_voice = QCheckBox(CosmeticTab)
        self.disable_custom_player_voice.setObjectName(u"disable_custom_player_voice")

        self.layoutH_for_1_custom_options.addWidget(self.disable_custom_player_voice)

        self.disable_custom_player_items = QCheckBox(CosmeticTab)
        self.disable_custom_player_items.setObjectName(u"disable_custom_player_items")

        self.layoutH_for_1_custom_options.addWidget(self.disable_custom_player_items)


        self.layoutG_for_0_model_settings.addLayout(self.layoutH_for_1_custom_options, 1, 1, 1, 1)

        self.install_custom_model = QPushButton(CosmeticTab)
        self.install_custom_model.setObjectName(u"install_custom_model")

        self.layoutG_for_0_model_settings.addWidget(self.install_custom_model, 0, 0, 1, 2)

        self.custom_model_comment = QLabel(CosmeticTab)
        self.custom_model_comment.setObjectName(u"custom_model_comment")
        self.custom_model_comment.setMaximumSize(QSize(810, 16777215))
        self.custom_model_comment.setTextFormat(Qt.PlainText)
        self.custom_model_comment.setWordWrap(True)

        self.layoutG_for_0_model_settings.addWidget(self.custom_model_comment, 3, 0, 1, 2)


        self.layoutV_for_0_cosmetic_options.addLayout(self.layoutG_for_0_model_settings)

        self.custom_colors_layout = QVBoxLayout()
        self.custom_colors_layout.setObjectName(u"custom_colors_layout")

        self.layoutV_for_0_cosmetic_options.addLayout(self.custom_colors_layout)

        self.layoutH_for_1_present = QHBoxLayout()
        self.layoutH_for_1_present.setObjectName(u"layoutH_for_1_present")
        self.save_custom_color_preset = QPushButton(CosmeticTab)
        self.save_custom_color_preset.setObjectName(u"save_custom_color_preset")

        self.layoutH_for_1_present.addWidget(self.save_custom_color_preset)

        self.load_custom_color_preset = QPushButton(CosmeticTab)
        self.load_custom_color_preset.setObjectName(u"load_custom_color_preset")

        self.layoutH_for_1_present.addWidget(self.load_custom_color_preset)


        self.layoutV_for_0_cosmetic_options.addLayout(self.layoutH_for_1_present)

        self.zzzz_spacerV_for_cosmetic_options = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.layoutV_for_0_cosmetic_options.addItem(self.zzzz_spacerV_for_cosmetic_options)


        self.horizontalLayout_14.addLayout(self.layoutV_for_0_cosmetic_options)

        self.layoutV_for_1_preview = QVBoxLayout()
        self.layoutV_for_1_preview.setObjectName(u"layoutV_for_1_preview")
        self.custom_model_preview_label = QLabel(CosmeticTab)
        self.custom_model_preview_label.setObjectName(u"custom_model_preview_label")
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.custom_model_preview_label.sizePolicy().hasHeightForWidth())
        self.custom_model_preview_label.setSizePolicy(sizePolicy)
        self.custom_model_preview_label.setMinimumSize(QSize(225, 350))

        self.layoutV_for_1_preview.addWidget(self.custom_model_preview_label)

        self.zzzz_spacerV_for_preview = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.layoutV_for_1_preview.addItem(self.zzzz_spacerV_for_preview)


        self.horizontalLayout_14.addLayout(self.layoutV_for_1_preview)


        self.retranslateUi(CosmeticTab)

        QMetaObject.connectSlotsByName(CosmeticTab)
    # setupUi

    def retranslateUi(self, CosmeticTab):
        CosmeticTab.setWindowTitle(QCoreApplication.translate("CosmeticTab", u"Form", None))
        self.randomize_all_custom_colors_together.setText(QCoreApplication.translate("CosmeticTab", u"Random (Orderly)", None))
        self.randomize_all_custom_colors_separately.setText(QCoreApplication.translate("CosmeticTab", u"Random (Chaotically)", None))
        self.label_for_custom_color_preset.setText(QCoreApplication.translate("CosmeticTab", u"Color Preset", None))
        self.label_for_custom_player_model.setText(QCoreApplication.translate("CosmeticTab", u"Model", None))
        self.player_in_casual_clothes.setText(QCoreApplication.translate("CosmeticTab", u"Casual Clothes", None))
        self.disable_custom_player_voice.setText(QCoreApplication.translate("CosmeticTab", u"No Custom Voice", None))
        self.disable_custom_player_items.setText(QCoreApplication.translate("CosmeticTab", u"No Custom Items", None))
        self.install_custom_model.setText(QCoreApplication.translate("CosmeticTab", u"Install a Custom Model or Model Pack", None))
        self.custom_model_comment.setText("")
        self.save_custom_color_preset.setText(QCoreApplication.translate("CosmeticTab", u"Save Custom Preset", None))
        self.load_custom_color_preset.setText(QCoreApplication.translate("CosmeticTab", u"Load Custom Preset", None))
        self.custom_model_preview_label.setText("")
    # retranslateUi

