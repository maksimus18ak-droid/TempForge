"""
temp_convert.py - Конвертер температур на Python (CLI + Tkinter GUI)
Поддерживает 8 шкал, пакетную обработку, таблицу эквивалентов.
"""
import argparse
import sys
import os
import csv
import json
from math import isnan
from typing import Optional, List, Tuple

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, scrolledtext
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False

# ========== ОПРЕДЕЛЕНИЯ ШКАЛ ==========
# Каждая шкала определяется функцией преобразования в Кельвин и обратно
# Формат: (to_kelvin_func, from_kelvin_func, name, symbol)
SCALES = {
    'c': (lambda x: x + 273.15, lambda x: x - 273.15, 'Цельсий', '°C'),
    'f': (lambda x: (x - 32) * 5/9 + 273.15, lambda x: (x - 273.15) * 9/5 + 32, 'Фаренгейт', '°F'),
    'k': (lambda x: x, lambda x: x, 'Кельвин', 'K'),
    'ra': (lambda x: x * 5/9, lambda x: x * 9/5, 'Ранкин', '°Ra'),
    're': (lambda x: x * 5/4 + 273.15, lambda x: (x - 273.15) * 4/5, 'Реомюр', '°Ré'),
    'n': (lambda x: x * 100/33 + 273.15, lambda x: (x - 273.15) * 33/100, 'Ньютон', '°N'),
    'de': (lambda x: 373.15 - x * 2/3, lambda x: (373.15 - x) * 3/2, 'Делиль', '°De'),
    'ro': (lambda x: (x - 7.5) * 40/21 + 273.15, lambda x: (x - 273.15) * 21/40 + 7.5, 'Рёмер', '°Rø'),
}

# ========== ОСНОВНАЯ ЛОГИКА ==========
class TemperatureConverter:
    @staticmethod
    def convert(value: float, from_scale: str, to_scale: str) -> float:
        if from_scale == to_scale:
            return value
        if from_scale not in SCALES or to_scale not in SCALES:
            raise ValueError(f"Неизвестная шкала: {from_scale} или {to_scale}")
        to_kelvin, _ = SCALES[from_scale]
        _, from_kelvin = SCALES[to_scale]
        kelvin = to_kelvin(value)
        return from_kelvin(kelvin)

    @staticmethod
    def convert_batch(values: List[float], from_scale: str, to_scale: str) -> List[float]:
        return [TemperatureConverter.convert(v, from_scale, to_scale) for v in values]

    @staticmethod
    def get_scale_info(scale: str) -> Tuple[str, str]:
        if scale not in SCALES:
            raise ValueError(f"Неизвестная шкала: {scale}")
        _, _, name, symbol = SCALES[scale]
        return name, symbol

    @staticmethod
    def list_scales() -> List[str]:
        return list(SCALES.keys())

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def format_temp(value: float, scale: str, precision: int = 2) -> str:
    name, symbol = TemperatureConverter.get_scale_info(scale)
    return f"{value:.{precision}f} {symbol}"

def generate_table(start: float, end: float, step: float, from_scale: str, to_scale: str, precision: int = 2) -> List[Tuple[str, str]]:
    rows = []
    current = start
    while current <= end + 1e-9:
        conv = TemperatureConverter.convert(current, from_scale, to_scale)
        rows.append((format_temp(current, from_scale, precision), format_temp(conv, to_scale, precision)))
        current += step
    return rows

# ========== CLI ==========
def cli():
    parser = argparse.ArgumentParser(description="Конвертер температур")
    parser.add_argument("--value", type=float, help="Значение для конвертации")
    parser.add_argument("--from", "-f", dest="from_scale", default="c", help="Исходная шкала (c, f, k, ra, re, n, de, ro)")
    parser.add_argument("--to", "-t", dest="to_scale", default="f", help="Целевая шкала")
    parser.add_argument("--precision", type=int, default=2, help="Количество знаков после запятой")
    parser.add_argument("--batch", help="Файл со значениями (по одному на строку)")
    parser.add_argument("--output", "-o", help="Файл для сохранения результатов (CSV или TXT)")
    parser.add_argument("--range", nargs=3, metavar=("START", "END", "STEP"), type=float, help="Диапазон для таблицы")
    parser.add_argument("--gui", action="store_true", help="Запустить GUI")
    parser.add_argument("--list", action="store_true", help="Показать список доступных шкал")
    args = parser.parse_args()

    if args.list:
        print("Доступные шкалы:")
        for key in SCALES:
            name, sym = TemperatureConverter.get_scale_info(key)
            print(f"  {key}: {name} ({sym})")
        return

    if args.gui and GUI_AVAILABLE:
        root = tk.Tk()
        app = TempConverterGUI(root)
        root.mainloop()
        return

    if args.range:
        start, end, step = args.range
        if step <= 0:
            print("Шаг должен быть положительным")
            return
        table = generate_table(start, end, step, args.from_scale, args.to_scale, args.precision)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(f"{SCALES[args.from_scale][2]} -> {SCALES[args.to_scale][2]}\n")
                for row in table:
                    f.write(f"{row[0]} = {row[1]}\n")
            print(f"Таблица сохранена в {args.output}")
        else:
            print(f"Таблица {SCALES[args.from_scale][2]} -> {SCALES[args.to_scale][2]}:")
            for row in table:
                print(f"{row[0]} = {row[1]}")
        return

    if args.batch:
        try:
            with open(args.batch, 'r', encoding='utf-8') as f:
                values = [float(line.strip()) for line in f if line.strip()]
        except Exception as e:
            print(f"Ошибка чтения файла: {e}")
            return
        results = TemperatureConverter.convert_batch(values, args.from_scale, args.to_scale)
        if args.output:
            ext = os.path.splitext(args.output)[1].lower()
            if ext == '.csv':
                with open(args.output, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([f"From ({args.from_scale})", f"To ({args.to_scale})"])
                    for v, r in zip(values, results):
                        writer.writerow([v, r])
            else:
                with open(args.output, 'w', encoding='utf-8') as f:
                    for v, r in zip(values, results):
                        f.write(f"{v} -> {r}\n")
            print(f"Результаты сохранены в {args.output}")
        else:
            for v, r in zip(values, results):
                print(f"{v:.{args.precision}f} -> {r:.{args.precision}f}")
        return

    if args.value is not None:
        result = TemperatureConverter.convert(args.value, args.from_scale, args.to_scale)
        from_str = format_temp(args.value, args.from_scale, args.precision)
        to_str = format_temp(result, args.to_scale, args.precision)
        print(f"{from_str} = {to_str}")
    else:
        parser.print_help()

# ========== GUI ==========
if GUI_AVAILABLE:
    class TempConverterGUI:
        def __init__(self, root):
            self.root = root
            self.root.title("Конвертер температур")
            self.root.geometry("500x400")
            self.root.resizable(False, False)

            # Переменные
            self.from_scale = tk.StringVar(value="c")
            self.to_scale = tk.StringVar(value="f")
            self.value_var = tk.StringVar()
            self.result_var = tk.StringVar()
            self.precision_var = tk.IntVar(value=2)

            self.create_widgets()

        def create_widgets(self):
            main = ttk.Frame(self.root, padding="10")
            main.pack(fill=tk.BOTH, expand=True)

            # Ввод значения
            ttk.Label(main, text="Значение:").grid(row=0, column=0, sticky="w", pady=5)
            ttk.Entry(main, textvariable=self.value_var, width=15).grid(row=0, column=1, sticky="w", pady=5)

            # Исходная шкала
            ttk.Label(main, text="Из:").grid(row=1, column=0, sticky="w", pady=5)
            from_combo = ttk.Combobox(main, textvariable=self.from_scale, values=list(SCALES.keys()), state="readonly", width=10)
            from_combo.grid(row=1, column=1, sticky="w", pady=5)

            # Целевая шкала
            ttk.Label(main, text="В:").grid(row=2, column=0, sticky="w", pady=5)
            to_combo = ttk.Combobox(main, textvariable=self.to_scale, values=list(SCALES.keys()), state="readonly", width=10)
            to_combo.grid(row=2, column=1, sticky="w", pady=5)

            # Точность
            ttk.Label(main, text="Точность (знаков):").grid(row=3, column=0, sticky="w", pady=5)
            ttk.Spinbox(main, from_=0, to=10, textvariable=self.precision_var, width=5).grid(row=3, column=1, sticky="w", pady=5)

            # Кнопка
            ttk.Button(main, text="Конвертировать", command=self.convert).grid(row=4, column=0, columnspan=2, pady=10)

            # Результат
            ttk.Label(main, text="Результат:").grid(row=5, column=0, sticky="w", pady=5)
            ttk.Entry(main, textvariable=self.result_var, state="readonly", width=30).grid(row=5, column=1, sticky="w", pady=5)

            # Дополнительные кнопки
            btn_frame = ttk.Frame(main)
            btn_frame.grid(row=6, column=0, columnspan=2, pady=10)
            ttk.Button(btn_frame, text="Обратный", command=self.reverse).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="Таблица", command=self.show_table).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="Сброс", command=self.clear).pack(side=tk.LEFT, padx=5)

        def convert(self):
            try:
                val = float(self.value_var.get())
                res = TemperatureConverter.convert(val, self.from_scale.get(), self.to_scale.get())
                self.result_var.set(format_temp(res, self.to_scale.get(), self.precision_var.get()))
            except ValueError:
                messagebox.showerror("Ошибка", "Введите корректное число")

        def reverse(self):
            # Меняем шкалы местами
            self.from_scale.set(self.to_scale.get())
            self.to_scale.set(self.from_scale.get())
            # Если есть результат, пересчитываем
            if self.result_var.get():
                self.convert()

        def show_table(self):
            # Открываем новое окно для таблицы
            top = tk.Toplevel(self.root)
            top.title("Таблица эквивалентов")
            top.geometry("400x300")
            text = scrolledtext.ScrolledText(top, wrap=tk.WORD)
            text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            try:
                start = float(self.value_var.get()) - 10
                end = float(self.value_var.get()) + 10
                step = 1.0
                table = generate_table(start, end, step, self.from_scale.get(), self.to_scale.get(), self.precision_var.get())
                text.insert(tk.END, f"{SCALES[self.from_scale.get()][2]} -> {SCALES[self.to_scale.get()][2]}\n")
                for row in table:
                    text.insert(tk.END, f"{row[0]} = {row[1]}\n")
                text.config(state='disabled')
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

        def clear(self):
            self.value_var.set("")
            self.result_var.set("")

if __name__ == "__main__":
    cli()
