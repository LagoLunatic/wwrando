# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'randomizer_window.ui'
#
# Created: Thu Apr 26 18:02:19 2018
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 159)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.seed = QtGui.QLineEdit(self.centralwidget)
        self.seed.setObjectName("seed")
        self.gridLayout.addWidget(self.seed, 2, 1, 1, 1)
        self.label = QtGui.QLabel(self.centralwidget)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.label_2 = QtGui.QLabel(self.centralwidget)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)
        self.clean_files_path = QtGui.QLineEdit(self.centralwidget)
        self.clean_files_path.setObjectName("clean_files_path")
        self.gridLayout.addWidget(self.clean_files_path, 0, 1, 1, 1)
        self.output_folder = QtGui.QLineEdit(self.centralwidget)
        self.output_folder.setObjectName("output_folder")
        self.gridLayout.addWidget(self.output_folder, 1, 1, 1, 1)
        self.label_3 = QtGui.QLabel(self.centralwidget)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 2, 0, 1, 1)
        self.clean_files_path_browse_button = QtGui.QPushButton(self.centralwidget)
        self.clean_files_path_browse_button.setObjectName("clean_files_path_browse_button")
        self.gridLayout.addWidget(self.clean_files_path_browse_button, 0, 2, 1, 1)
        self.output_folder_browse_button = QtGui.QPushButton(self.centralwidget)
        self.output_folder_browse_button.setObjectName("output_folder_browse_button")
        self.gridLayout.addWidget(self.output_folder_browse_button, 1, 2, 1, 1)
        self.generate_seed_button = QtGui.QPushButton(self.centralwidget)
        self.generate_seed_button.setObjectName("generate_seed_button")
        self.gridLayout.addWidget(self.generate_seed_button, 2, 2, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.about_button = QtGui.QPushButton(self.centralwidget)
        self.about_button.setObjectName("about_button")
        self.horizontalLayout.addWidget(self.about_button)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.randomize_button = QtGui.QPushButton(self.centralwidget)
        self.randomize_button.setObjectName("randomize_button")
        self.horizontalLayout.addWidget(self.randomize_button)
        self.verticalLayout.addLayout(self.horizontalLayout)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "Wind Waker Randomizer", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("MainWindow", "Clean WW Files", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("MainWindow", "Output Folder", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("MainWindow", "Seed (optional)", None, QtGui.QApplication.UnicodeUTF8))
        self.clean_files_path_browse_button.setText(QtGui.QApplication.translate("MainWindow", "Browse", None, QtGui.QApplication.UnicodeUTF8))
        self.output_folder_browse_button.setText(QtGui.QApplication.translate("MainWindow", "Browse", None, QtGui.QApplication.UnicodeUTF8))
        self.generate_seed_button.setText(QtGui.QApplication.translate("MainWindow", "New seed", None, QtGui.QApplication.UnicodeUTF8))
        self.about_button.setText(QtGui.QApplication.translate("MainWindow", "About", None, QtGui.QApplication.UnicodeUTF8))
        self.randomize_button.setText(QtGui.QApplication.translate("MainWindow", "Randomize", None, QtGui.QApplication.UnicodeUTF8))

