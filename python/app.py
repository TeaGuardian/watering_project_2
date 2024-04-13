from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot, QTimer, QThread, QIODevice
from source.mainwindow import UI
from source.windows import *
from PyQt5.QtGui import QPixmap
from PyQt5 import QtSerialPort
from source.backend import *
from source.const import *


class MyApp(QMainWindow, UI):
    content_usb = {}
    sensors_manager = {}
    sensors = [8, 9, 10, 11, 16, 17, 18, 19, 20, 21, 22, 23, 25, 26]
    floating = [19, 20, 21, 22, 23]
    auto = []
    com_buf = []
    modules = []
    settings = get_backup()
    last_catched = datetime.now()
    chsd_timer, chsd_flag = Timer(20), False

    def __init__(self):
        """подтягиваем данные и устанавливаем дефолтные значения"""
        super().__init__()
        self.setupUi(self)
        self.grafick_im.setText("Ожидание данных...")
        self.serial = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.step)
        self.timer.start(int(60000 / int(self.settings["dss"])))   # таймер обновления модулей
        self.buf_timer = QTimer()
        self.buf_timer.timeout.connect(self.step_auto)
        self.buf_timer.start(int(120000 / int(self.settings["dss"])))  # таймер обновления автоматики
        self.updateSerial_b.clicked.connect(self.upd_coms_f)
        self.hiden_thr = QThread()
        self.com_upd_thr = GetSerialInfo()
        self.com_upd_thr.moveToThread(self.hiden_thr)
        self.com_upd_thr.data.connect(self._upd_coms_f)
        self.conSerial_b.clicked.connect(self.connect_f)
        self.choosePy_b.clicked.connect(self.update_files)
        self.updateModules_b.clicked.connect(self.update_modules)
        self.reindex_b.clicked.connect(self.reindex_modules)
        self.clearData_b.clicked.connect(self.clear_data)
        self.setValue_b.clicked.connect(self.set_value_f)
        self.comSend_b.clicked.connect(self.send_command)
        self.setWindowIcon(QIcon(ICO_PATCH))
        self.qrCode_lb.setPixmap(QPixmap(QR_PATCH).scaled(self.qrCode_lb.width(), self.qrCode_lb.height()))

        self.confirm_settings()
        self.load_modules()

    def send_command(self):
        """отправка команды вручную"""
        if self.connectSerial_ind.value() > 0 and len(self.comInput_t.toPlainText()) >= 12:
            self.send_function(self.comInput_t.toPlainText())
        elif self.connectSerial_ind.value() > 0 and len(self.comInput_t.toPlainText()) < 12:
            er = ErrorDialog(title="Команда должна состоять из 6 значений!")
            if er.exec_():
                pass
        else:
            er = ErrorDialog(title="Нет подключенных переходников!")
            if er.exec_():
                pass

    def clear_data(self):
        """очистка данных"""
        self.sensors_manager = {}
        self.reselection()
        self.comOutput.clear()

    def set_value_f(self):
        """функция установки значения"""
        if self.connectSerial_ind.value() > 0 and self.moduleSelector_sb.currentText():
            sel = LoadDialog()
            if sel.exec_():
                sid = int(sel.getInputs())
                if sid == 7:
                    dd = IndexDialog()
                    if dd.exec_():
                        self.send_function(f"0#{self.moduleSelector_sb.currentText()}#1#7#{dd.getInputs()}#{dd.getInputs()}")
                        self.modules.pop(self.modules.index(int(self.moduleSelector_sb())))
                elif sid == 6:
                    self.send_function(f"0#{self.moduleSelector_sb.currentText()}#1#6#0#0")
                elif sid in [12, 13, 27, 28]:
                    dd = BoolDialog()
                    if dd.exec_():
                        self.send_function(f"0#{self.moduleSelector_sb.currentText()}#1#{sid}#{dd.getInputs()}#{dd.getInputs()}")
                elif sid in [14, 24]:
                    dd = AnalogDialog()
                    if dd.exec_():
                        self.send_function(
                            f"0#{self.moduleSelector_sb.currentText()}#1#{sid}#{dd.getInputs()}#{dd.getInputs()}")
                elif sid == 15:
                    dd = SpeakerDialog()
                    if dd.exec_():
                        self.send_function(f"0#{self.moduleSelector_sb.currentText()}#1#15#{dd.getInputs()[1]}#{dd.getInputs()[0]}")
                elif sid == 29:
                    dd = ServoDialog()
                    if dd.exec_():
                        self.send_function(f"0#{self.moduleSelector_sb.currentText()}#1#29#{dd.getInputs()}#{dd.getInputs()}")
        else:
            er = ErrorDialog(title="Нет подключенных переходников!")
            if er.exec_():
                pass

    def reindex_modules(self):
        """обновить индексы модулей"""
        if self.connectSerial_ind.value() > 0 and self.serial is not None:
            self.modules = []
            self.moduleSelector_sb.clear()
            self.chsd_flag = False
            self.chsd_timer.tk()
            self.serial.write("0#1#1#0#0#0".encode())
        else:
            er = ErrorDialog(title="Нет подключенных переходников!")
            if er.exec_():
                pass

    def update_modules(self):
        """найти модули"""
        if self.connectSerial_ind.value() > 0 and self.serial is not None:
            self.modules = []
            self.moduleSelector_sb.clear()
            self.chsd_flag = False
            self.chsd_timer.tk()
            self.serial.write("0#1#1#1#0#0".encode())
        else:
            er = ErrorDialog(title="Нет подключенных переходников!")
            if er.exec_():
                pass

    def step(self):
        """выполнить команду из буфера"""
        if self.chsd_flag:
            if self.connectSerial_ind.value() > 0 and self.serial is not None and not self.serial.canReadLine():
                com = self.com_buf.pop(0).encode()
                self.serial.write(com)
                self.comOutput.append(f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')} --> {com}")
            if self.serial is not None and self.serial.canReadLine():
                self.recive()
        else:
            if self.chsd_timer.tk():
                self.chsd_flag = Timer

    def send_function(self, command):
        """добавляем команду в буфер"""
        self.com_buf.append(command)

    def step_auto(self):
        """выполнить автоматизацию"""
        if self.connectSerial_ind.value() > 0:
            for module in self.auto:
                module.main(self.modules, self.send_function, self.com_buf, self.sensors_manager)

    def update_settings(self):
        """сохраняем настройки"""
        self.settings["server"] = self.serverLink_in.toPlainText()
        self.settings["key"] = self.serverKey_in.toPlainText()
        self.settings["pass"] = self.serverPass_in.toPlainText()
        self.settings["maxi"] = self.maxcurrent_sp.value()
        self.settings["voltage"] = self.maxvoltage_sp.value()
        self.settings["dss"] = self.speedModules_sb.value()
        self.settings["dsc"] = self.speedServer_sb.value()
        self.settings["sensors"] = self.sensors_manager.copy()

    def closeEvent(self, a0) -> None:
        """реакция на закрытие программы"""
        self.update_settings()
        write_backup(self.settings)
        self.close()

    def update_files(self):
        """активируем окно выбора файлов автоматизации"""
        fmng = FileManager(self._update_files)
        fmng.show()

    def load_modules(self):
        """подгружаем модули после старта софта"""
        for file in self.settings["files"]:
            if isfile(file):
                try:
                    module = import_module(file)
                    if module.confirm():
                        self.auto.append(module)
                except Exception as e:
                    print(e)

    def _update_files(self, files: list):
        """подгружаем выбранные модули"""
        self.auto = []
        self.settings["files"] = []
        for file in files:
            if isfile(file):
                try:
                    module = import_module(file)
                    if module.confirm():
                        self.auto.append(module)
                        self.settings["files"].append(file)
                except Exception as e:
                    print(e)
        if not files:
            self.choosePy_view.setText('автоматика отключена (выберите файлы, чтобы включить)')
        else:
            self.choosePy_view.setText(f'{self.settings["files"]}')

    def confirm_settings(self):
        """применяем настройки из памяти к текущему меню"""
        self.serverLink_in.setText(self.settings["server"])
        self.serverKey_in.setText(self.settings["key"])
        self.serverPass_in.setText(self.settings["pass"])
        self.maxcurrent_sp.setValue(self.settings["maxi"])
        self.maxvoltage_sp.setValue(self.settings["voltage"])
        self.speedModules_sb.setValue(self.settings["dss"])
        self.speedServer_sb.setValue(self.settings["dsc"])
        self.choosePy_view.setText(f'{self.settings["files"] if self.settings["files"] else "автоматика отключена (выберите файлы, чтобы включить)"}')

    def _upd_coms_f(self, data: dict):
        """заполняем результаты поиска портов"""
        self.content_usb = data.copy()
        self.selectSerial_l.clear()
        for ke in data.keys():
            self.selectSerial_l.addItem(ke)
        self.hiden_thr.terminate()

    def upd_coms_f(self):
        """вызываем поиск портов в отдельном потоке"""
        self.hiden_thr.terminate()
        self.hiden_thr.started.connect(self.com_upd_thr.run)
        self.hiden_thr.start()

    def reselection(self):
        """обновляем график при смене датчика или модуля"""
        self.update_label(self.moduleSelector_sb.currentText(), self.sensorSelector_sb.currentData())

    def recive(self):
        """приём данных с порта"""
        if self.serial is None:
            return False
        while self.serial.canReadLine():
            subn = self.serial.readLine().data()
            if len(subn) > 12:
                try:
                    text = subn.decode().rstrip('\r\n').rstrip('$')
                    self.last_catched = datetime.now()
                    for fraq in text.split("$"):
                        self.comOutput.append(f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')} <-- {fraq}")
                        fraq = fraq.split("#")
                        data = [int(fraq[0]), int(fraq[1]), int(fraq[2]), int(fraq[3]), float(fraq[4]), int(fraq[5])]
                        if data[0] not in self.modules:
                            self.modules.append(data[0])
                            self.moduleSelector_sb.addItem(data[0])
                            self.sensors_manager[data[0]] = {}
                        if data[3]:
                            self.update_pixmap(data[0], data[3], data[4] if data[3] in self.floating else data[5])
                except Exception as ex:
                    print(ex)

    def connect_f(self):
        """подключение к выбранному порту"""
        if self.conSerial_b.text() == "подключиться":
            if self.selectSerial_l.currentText():
                self.serial = QtSerialPort.QSerialPort(self.content_usb[self.selectSerial_l.currentText()], baudRate=QtSerialPort.QSerialPort.Baud115200, readyRead=self.receive)
                if not self.serial.isOpen():
                    if not self.serial.open(QIODevice.ReadWrite):
                        self.conSerial_b.setText("подключиться")
                        self.connectSerial_ind.setValue(0)
                        return 0
                    else:
                        self.connectSerial_ind.setValue(100)
                        self.conSerial_b.setText("отключиться")
                        return 1
        if self.serial is not None:
            self.serial.close()
            self.conSerial_b.setText("подключиться")
            self.connectSerial_ind.setValue(0)

    def update_pixmap(self, mid: int, sid: int, up_data: int):
        """обновляем график и данные"""
        if mid not in self.sensors_manager:
            self.sensors_manager[mid] = {}
        if sid not in self.sensors_manager[mid].keys():
            self.sensors_manager[mid][sid] = []
        self.sensors_manager[mid][sid].append(up_data)
        while len(self.sensors_manager[mid][sid]) > GRAPHIC_BUF_SIZE:
            self.sensors_manager[mid][sid].pop(0)
        if self.moduleSelector_sb.currentText() == mid and self.sensorSelector_sb.currentData() == sid:
            create_pixmap(mid, sid, self.sensors_manager[mid][sid][:])
            self.update_label(mid, sid)

    def update_label(self, mid: int, sid: int):
        """функция обновления графика"""
        if isfile(f"{GRAPHICS_PATCH}/{mid}/{sid}.png"):
            self.grafick_im.setText("")
            self.grafick_im.setPixmap(QPixmap(f"{GRAPHICS_PATCH}/{mid}/{sid}.png"))
        else:
            self.grafick_im.setText("Данных пока не обнаружено, ожидаем.")


class GetSerialInfo(QObject):
    """получение информации"""
    data = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

    @pyqtSlot()
    def run(self):
        data = {}
        for i in QtSerialPort.QSerialPortInfo.availablePorts():
            if i.isValid():
                ke = f"{i.description()} ({i.portName()})"
                data[ke] = i.portName()
        self.data.emit(data)


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == "__main__":
    """точка входа в приложение"""
    import sys
    app = QApplication(sys.argv)
    ex = MyApp()
    ex.show()
    sys.excepthook = except_hook
    sys.exit(app.exec_())
    """
    python -m PyQt5.uic.pyuic -x untitled.ui -o main.py
    """