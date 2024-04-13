from datetime import datetime, timedelta
from os.path import isfile, isdir
from os import mkdir, getcwd
from json import load, dump
import matplotlib.pyplot as plt
import importlib.util
from .const import *


def import_module(file_path):
    """функция динамического импорта модулей"""
    spec = importlib.util.spec_from_file_location("module_name", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Timer:
    """вспомогательный таймер"""
    def __init__(self, tick):
        self.tick, self.last = tick, datetime.now()

    def tk(self):
        """таймер тикнул?"""
        if (datetime.now() - self.last) > timedelta(seconds=self.tick):
            self.last = datetime.now()
            return True
        return False


def get_backup() -> dict:
    """получение настроек"""
    if isfile(SETTINGS_PATCH):
        with open(SETTINGS_PATCH, mode="r+", encoding=ENCODING) as fi:
            return load(fi)
    else:
        data = {"server": "http://127.0.0.1:8000/remouteAPI", "key": "", "pass": "", "maxi": 3.0, "voltage": 13.0,
                "dss": 30, "dsc": 120, "files": ["data/auto/example.py"], "sensors": []}
        return data


def write_backup(data: dict):
    """запись настроек"""
    with open(SETTINGS_PATCH, mode="w+", encoding=ENCODING) as fi:
        dump(data, fi)


def create_pixmap(mid=1, sid=8, data=(0, -2, 1, 4, 5, 0, -1, 2)):
    """рисуем график по данным"""
    fig, ax = plt.subplots()
    fig.set_size_inches(700 / 100, 300 / 100)
    ax.plot([i for i in range(len(data))], data)
    pp = f"{GRAPHICS_PATCH}/{mid}"
    if not isdir(pp):
        mkdir(pp)
    fig.savefig(f"{pp}/{sid}.png", bbox_inches='tight')