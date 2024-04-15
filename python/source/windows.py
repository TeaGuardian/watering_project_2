# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QWidget, QFileDialog, QSpinBox, QCheckBox, QComboBox, QLabel
from PyQt5.QtWidgets import QDialog, QLineEdit, QDialogButtonBox, QFormLayout, QDoubleSpinBox
from PyQt5.QtGui import QIcon
from .const import *


class FileManager(QWidget):
    """окно выбора файлов"""
    def __init__(self, callback=print):
        super().__init__()
        self.title = 'choose control file'
        self.callback = callback
        self.left = 10
        self.top = 10
        self.width = 640
        self.height = 480
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setWindowIcon(QIcon(ICO_PATCH))
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.openFilesDialog()

    def openFilesDialog(self):
        """выбор файлов"""
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        files, _ = QFileDialog.getOpenFileNames(self, "выберете файл(ы)", "", "Python Files (*.py);;All Files (*)", options=options)
        self.callback(files)
        self.close()


class LoadDialog(QDialog):
    """диалоговое окно выбора нагрузки"""
    def __init__(self, parent=None, title="выберете нагрузку"):
        super().__init__(parent)
        self.setWindowIcon(QIcon(ICO_PATCH))
        self.setWindowTitle(title)
        self.first = QComboBox(self)
        self.first.addItem("установить индекс (7)", 7)
        self.first.addItem("отключить всю нагрузку (6)", 6)
        self.first.addItem("силовая шина 1 (12)", 12)
        self.first.addItem("силовая шина 2 (13)", 13)
        self.first.addItem("светодиод load~ (14)", 14)
        self.first.addItem("динамик (15)", 15)
        self.first.addItem("силовая шина с шим (24)", 24)
        self.first.addItem("реле 1 (27)", 27)
        self.first.addItem("реле 2 (28)", 28)
        self.first.addItem("сервопривод (29)", 29)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)

        layout = QFormLayout(self)
        layout.addRow("--> ", self.first)
        layout.addWidget(buttonBox)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

    def getInputs(self):
        return self.first.currentData()


class AnalogDialog(QDialog):
    """диалоговое окно отправки числа"""
    def __init__(self, parent=None, title="analog"):
        super().__init__(parent)
        self.setWindowIcon(QIcon(ICO_PATCH))
        self.setWindowTitle(title)
        self.first = QSpinBox(self)
        self.first.setMaximum(643)
        self.first.setSingleStep(10)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)

        layout = QFormLayout(self)
        layout.addRow("value", self.first)
        layout.addWidget(buttonBox)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

    def getInputs(self):
        return self.first.value()


class IndexDialog(QDialog):
    """диалоговое окно установки индекса модуля"""
    def __init__(self, parent=None, title="set index"):
        super().__init__(parent)
        self.setWindowIcon(QIcon(ICO_PATCH))
        self.setWindowTitle(title)
        self.first = QSpinBox(self)
        self.first.setMaximum(65532)
        self.first.setSingleStep(1)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)

        layout = QFormLayout(self)
        layout.addRow("value", self.first)
        layout.addWidget(buttonBox)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

    def getInputs(self):
        return self.first.value()


class ServoDialog(QDialog):
    """диалоговое окно отправки угла"""
    def __init__(self, parent=None, title="servo"):
        super().__init__(parent)
        self.setWindowIcon(QIcon(ICO_PATCH))
        self.setWindowTitle(title)
        self.first = QSpinBox(self)
        self.first.setMaximum(180)
        self.first.setSingleStep(10)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)

        layout = QFormLayout(self)
        layout.addRow("angle", self.first)
        layout.addWidget(buttonBox)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

    def getInputs(self):
        return self.first.value()


class SpeakerDialog(QDialog):
    """диалоговое окно отправки данных для спикера"""
    def __init__(self, parent=None, title="динамик"):
        super().__init__(parent)
        self.setWindowIcon(QIcon(ICO_PATCH))
        self.setWindowTitle(title)
        self.first = QSpinBox(self)
        self.first.setSingleStep(100)
        self.first.setMaximum(20000)
        self.second = QDoubleSpinBox(self)
        self.second.setSingleStep(100)
        self.second.setMaximum(100000)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)

        layout = QFormLayout(self)
        layout.addRow("freq (Hz)", self.first)
        layout.addRow("time (ms)", self.second)
        layout.addWidget(buttonBox)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

    def getInputs(self):
        return (self.first.value(), self.second.value())


class BoolDialog(QDialog):
    """диалог отправки флага"""
    def __init__(self, parent=None, title="bool"):
        super().__init__(parent)
        self.setWindowIcon(QIcon(ICO_PATCH))
        self.setWindowTitle(title)
        self.first = QCheckBox(self)
        self.first.setText("включено")
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)

        layout = QFormLayout(self)
        layout.addRow("value", self.first)
        layout.addWidget(buttonBox)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

    def getInputs(self):
        return self.first.isChecked()


class ErrorDialog(QDialog):
    """диалог ошибки"""
    def __init__(self, parent=None, title="ошибка"):
        super().__init__(parent)
        self.setWindowIcon(QIcon(ICO_PATCH))
        self.setWindowTitle("ошибка")
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok, self)
        self.lb = QLabel(self, text=title)
        layout = QFormLayout(self)
        layout.addRow("", self.lb)
        layout.addWidget(buttonBox)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)


