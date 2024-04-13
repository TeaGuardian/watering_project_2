sensors = [8, 9, 10, 11, 16, 17, 18, 19, 20, 21, 22, 23, 25, 26]
MIN_H = 400
MAX_T = 30


def confirm() -> bool:
    """подтверждение того, что файл поддерживает автоматику"""
    return True


def build_command(module: int | str, command: int | str, float_data: float | int | str, int_data: int | str):
    """вспомогательная функция"""
    return f"0#{module}#1#{command}#{float_data}#{int_data}"


def main(modules: list, write: classmethod, buffer: list, data: dict) -> None:
    if len(buffer) < 20:
        for module in modules:   # проходимся по всем модулям
            for sensor in sensors:   # проходимся по всем сенсорам текущего модуля
                write(build_command(module, sensor, 0, 0))   # запрашиваем данные с датчика в очередь
            if module in data.keys():   # если есть данные с модуля
                if 8 in data[module].keys() and 9 in data[module].keys() and len(data[module][8]) and len(data[module][9]):
                    if data[module][8][-1] < MIN_H or data[module][9][-1] < MIN_H:   # если почва сухая
                        for _ in range(10):
                            write(build_command(module, 13, 1, 1))   # полить
                        write(build_command(module, 13, 0, 0))   # прекратить полив
                        write(build_command(module, 13, 0, 0))
                if 19 in data[module].keys() and len(data[module][19]):
                    if data[module][19][-1] > MAX_T:   # если слишком жарко
                        for _ in range(10):
                            write(build_command(module, 19, 0, 640))   # включить вентилятор
                        write(build_command(module, 19, 0, 0))   # выключить
                        write(build_command(module, 19, 0, 0))

