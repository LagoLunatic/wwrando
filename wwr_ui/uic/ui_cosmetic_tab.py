# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'cosmetic_tab.ui'
##
## Created by: Qt User Interface Compiler version 6.7.1
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
        self.verticalLayout_10 = QVBoxLayout()
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.gridLayout_5 = QGridLayout()
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.horizontalLayout_11 = QHBoxLayout()
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.randomize_all_custom_colors_together = QPushButton(CosmeticTab)
        self.randomize_all_custom_colors_together.setObjectName(u"randomize_all_custom_colors_together")

        self.horizontalLayout_11.addWidget(self.randomize_all_custom_colors_together)

        self.randomize_all_custom_colors_separately = QPushButton(CosmeticTab)
        self.randomize_all_custom_colors_separately.setObjectName(u"randomize_all_custom_colors_separately")

        self.horizontalLayout_11.addWidget(self.randomize_all_custom_colors_separately)


        self.gridLayout_5.addLayout(self.horizontalLayout_11, 2, 1, 1, 1)

        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.label_for_custom_color_preset = QLabel(CosmeticTab)
        self.label_for_custom_color_preset.setObjectName(u"label_for_custom_color_preset")

        self.horizontalLayout_10.addWidget(self.label_for_custom_color_preset)

        self.custom_color_preset = QComboBox(CosmeticTab)
        self.custom_color_preset.setObjectName(u"custom_color_preset")

        self.horizontalLayout_10.addWidget(self.custom_color_preset)


        self.gridLayout_5.addLayout(self.horizontalLayout_10, 2, 0, 1, 1)

        self.horizontalLayout_12 = QHBoxLayout()
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.label_for_custom_player_model = QLabel(CosmeticTab)
        self.label_for_custom_player_model.setObjectName(u"label_for_custom_player_model")

        self.horizontalLayout_12.addWidget(self.label_for_custom_player_model)

        self.custom_player_model = QComboBox(CosmeticTab)
        self.custom_player_model.setObjectName(u"custom_player_model")

        self.horizontalLayout_12.addWidget(self.custom_player_model)


        self.gridLayout_5.addLayout(self.horizontalLayout_12, 1, 0, 1, 1)

        self.horizontalLayout_13 = QHBoxLayout()
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.player_in_casual_clothes = QCheckBox(CosmeticTab)
        self.player_in_casual_clothes.setObjectName(u"player_in_casual_clothes")

        self.horizontalLayout_13.addWidget(self.player_in_casual_clothes)

        self.disable_custom_player_voice = QCheckBox(CosmeticTab)
        self.disable_custom_player_voice.setObjectName(u"disable_custom_player_voice")

        self.horizontalLayout_13.addWidget(self.disable_custom_player_voice)

        self.disable_custom_player_items = QCheckBox(CosmeticTab)
        self.disable_custom_player_items.setObjectName(u"disable_custom_player_items")

        self.horizontalLayout_13.addWidget(self.disable_custom_player_items)


        self.gridLayout_5.addLayout(self.horizontalLayout_13, 1, 1, 1, 1)

        self.install_custom_model = QPushButton(CosmeticTab)
        self.install_custom_model.setObjectName(u"install_custom_model")

        self.gridLayout_5.addWidget(self.install_custom_model, 0, 0, 1, 2)

        self.custom_model_comment = QLabel(CosmeticTab)
        self.custom_model_comment.setObjectName(u"custom_model_comment")
        self.custom_model_comment.setMaximumSize(QSize(810, 16777215))
        self.custom_model_comment.setTextFormat(Qt.TextFormat.PlainText)
        self.custom_model_comment.setWordWrap(True)

        self.gridLayout_5.addWidget(self.custom_model_comment, 3, 0, 1, 2)


        self.verticalLayout_10.addLayout(self.gridLayout_5)

        self.custom_colors_layout = QVBoxLayout()
        self.custom_colors_layout.setObjectName(u"custom_colors_layout")

        self.verticalLayout_10.addLayout(self.custom_colors_layout)

        self.horizontalLayout_18 = QHBoxLayout()
        self.horizontalLayout_18.setObjectName(u"horizontalLayout_18")
        self.save_custom_color_preset = QPushButton(CosmeticTab)
        self.save_custom_color_preset.setObjectName(u"save_custom_color_preset")

        self.horizontalLayout_18.addWidget(self.save_custom_color_preset)

        self.load_custom_color_preset = QPushButton(CosmeticTab)
        self.load_custom_color_preset.setObjectName(u"load_custom_color_preset")

        self.horizontalLayout_18.addWidget(self.load_custom_color_preset)


        self.verticalLayout_10.addLayout(self.horizontalLayout_18)

        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_10.addItem(self.verticalSpacer_4)


        self.horizontalLayout_14.addLayout(self.verticalLayout_10)

        self.verticalLayout_11 = QVBoxLayout()
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.custom_model_preview_label = QLabel(CosmeticTab)
        self.custom_model_preview_label.setObjectName(u"custom_model_preview_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.custom_model_preview_label.sizePolicy().hasHeightForWidth())
        self.custom_model_preview_label.setSizePolicy(sizePolicy)
        self.custom_model_preview_label.setMinimumSize(QSize(225, 350))

        self.verticalLayout_11.addWidget(self.custom_model_preview_label)

        self.verticalSpacer_5 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_11.addItem(self.verticalSpacer_5)


        self.horizontalLayout_14.addLayout(self.verticalLayout_11)


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

