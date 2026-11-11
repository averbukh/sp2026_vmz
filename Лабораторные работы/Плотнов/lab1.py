"""
Лабораторная работа №1. Методы и средства обработки сигналов.
Студент: Плотнов А. А., группа 24-ВМз.

Расчёт функции y(x) = a1*sin(b1*x) + a2*sin(b2*x) + a3*sin(b3*x)
на отрезке [x0, xк] с шагом Δx, вывод векторов x и y в таблицу
и построение графика. Графический интерфейс — tkinter (входит в Python),
график можно сохранить в векторный формат SVG (файл формируется вручную,
без сторонних библиотек).
"""

import math
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

MAX_POINTS = 100_000


# ---------------------------------------------------------------- расчёт ---

def parse_number(text, name):
    """Преобразует строку в число; допускает точку и запятую."""
    try:
        value = float(text.strip().replace(",", "."))
    except ValueError:
        raise ValueError(f"Поле «{name}»: «{text}» не является числом.")
    if not math.isfinite(value):
        raise ValueError(f"Поле «{name}»: число должно быть конечным.")
    return value


def calc_vectors(a1, b1, a2, b2, a3, b3, x0, xk, dx):
    """Возвращает векторы x и y. Аргументы синусов — в радианах."""
    if dx <= 0:
        raise ValueError("Шаг Δx должен быть больше нуля.")
    if xk < x0:
        raise ValueError("Конечное значение xк должно быть не меньше x0.")
    # число узлов сетки; 1e-9 защищает от ошибки округления (6.2/0.1 = 61.999...)
    n = int(math.floor((xk - x0) / dx + 1e-9)) + 1
    if n > MAX_POINTS:
        raise ValueError(f"Слишком много точек ({n}). Увеличьте шаг Δx.")
    xs, ys = [], []
    for i in range(n):
        x = x0 + i * dx  # без накопления ошибки, в отличие от x += dx
        y = a1 * math.sin(b1 * x) + a2 * math.sin(b2 * x) + a3 * math.sin(b3 * x)
        xs.append(x)
        ys.append(y)
    return xs, ys


# ------------------------------------------------------------ оси и сетка ---

def nice_step(span, ticks=8):
    """Подбирает «красивый» шаг сетки: 1, 2 или 5, умноженные на 10^k."""
    if span <= 0:
        return 1.0
    raw = span / ticks
    power = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 5, 10):
        if raw <= m * power:
            return m * power
    return 10 * power


def axis_range(values):
    lo, hi = min(values), max(values)
    if lo == hi:  # горизонтальная линия — даём запас
        lo, hi = lo - 1, hi + 1
    return lo, hi


def ticks(lo, hi):
    step = nice_step(hi - lo)
    start = math.ceil(lo / step - 1e-9) * step
    result, t = [], start
    while t <= hi + step * 1e-9:
        result.append(0.0 if abs(t) < step * 1e-9 else t)
        t += step
    return result, step


def fmt(v, step):
    digits = max(0, -int(math.floor(math.log10(step)))) if step < 1 else 0
    return f"{v:.{digits}f}"


class Plot:
    """Пересчёт координат функции в пиксели; общий для Canvas и SVG."""

    def __init__(self, xs, ys, width, height, left=60, right=20, top=40, bottom=45):
        self.xs, self.ys = xs, ys
        self.w, self.h = width, height
        self.l, self.r, self.t, self.b = left, right, top, bottom
        self.xmin, self.xmax = axis_range(xs)
        self.ymin, self.ymax = axis_range(ys)
        pad = (self.ymax - self.ymin) * 0.05
        self.ymin -= pad
        self.ymax += pad

    def px(self, x):
        return self.l + (x - self.xmin) / (self.xmax - self.xmin) * (self.w - self.l - self.r)

    def py(self, y):
        return self.h - self.b - (y - self.ymin) / (self.ymax - self.ymin) * (self.h - self.t - self.b)


def build_svg(xs, ys, params_text, width=900, height=500):
    """Формирует текст SVG-файла с графиком."""
    p = Plot(xs, ys, width, height)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
           f'viewBox="0 0 {width} {height}" font-family="Arial" font-size="12">',
           f'<rect width="{width}" height="{height}" fill="white"/>',
           f'<text x="{width / 2}" y="18" text-anchor="middle" font-size="15">'
           f'y(x) = a1·sin(b1·x) + a2·sin(b2·x) + a3·sin(b3·x)</text>',
           f'<text x="{width / 2}" y="34" text-anchor="middle" fill="#555">{params_text}</text>']
    xt, xstep = ticks(p.xmin, p.xmax)
    yt, ystep = ticks(p.ymin, p.ymax)
    for t in xt:
        X = p.px(t)
        out.append(f'<line x1="{X:.1f}" y1="{p.t}" x2="{X:.1f}" y2="{height - p.b}" stroke="#ddd"/>')
        out.append(f'<text x="{X:.1f}" y="{height - p.b + 16}" text-anchor="middle">{fmt(t, xstep)}</text>')
    for t in yt:
        Y = p.py(t)
        out.append(f'<line x1="{p.l}" y1="{Y:.1f}" x2="{width - p.r}" y2="{Y:.1f}" stroke="#ddd"/>')
        out.append(f'<text x="{p.l - 6}" y="{Y + 4:.1f}" text-anchor="end">{fmt(t, ystep)}</text>')
    # оси через ноль, если ноль попадает в диапазон
    if p.ymin <= 0 <= p.ymax:
        out.append(f'<line x1="{p.l}" y1="{p.py(0):.1f}" x2="{width - p.r}" y2="{p.py(0):.1f}" stroke="black"/>')
    if p.xmin <= 0 <= p.xmax:
        out.append(f'<line x1="{p.px(0):.1f}" y1="{p.t}" x2="{p.px(0):.1f}" y2="{height - p.b}" stroke="black"/>')
    out.append(f'<rect x="{p.l}" y="{p.t}" width="{width - p.l - p.r}" height="{height - p.t - p.b}" '
               f'fill="none" stroke="#888"/>')
    pts = " ".join(f"{p.px(x):.2f},{p.py(y):.2f}" for x, y in zip(xs, ys))
    out.append(f'<polyline points="{pts}" fill="none" stroke="#1f5fbf" stroke-width="2"/>')
    out.append(f'<text x="{width - p.r}" y="{height - 8}" text-anchor="end">x</text>')
    out.append(f'<text x="12" y="{p.t - 6}">y</text>')
    out.append('</svg>')
    return "\n".join(out)


# ------------------------------------------------------------- интерфейс ---

FIELDS = [("a1", "1"), ("b1", "1"), ("a2", "0,5"), ("b2", "2"),
          ("a3", "0,25"), ("b3", "3"), ("x0", "0"), ("xк", "6,28"), ("Δx", "0,1")]


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ЛР №1 — сумма трёх синусоид (Плотнов А. А., 24-ВМз)")
        self.geometry("1150x620")
        self.minsize(900, 500)
        self.xs, self.ys = [], []
        self.entries = {}

        left = ttk.Frame(self, padding=10)
        left.pack(side="left", fill="y")
        ttk.Label(left, text="y(x) = a1·sin(b1·x) + a2·sin(b2·x)\n          + a3·sin(b3·x)",
                  font=("Arial", 10, "bold")).grid(row=0, column=0, columnspan=4, pady=(0, 10), sticky="w")
        for i, (name, default) in enumerate(FIELDS):
            r, c = divmod(i, 2) if i < 6 else (3 + (i - 6), 0)
            ttk.Label(left, text=name + " =").grid(row=r + 1, column=c * 2, sticky="e", padx=3, pady=3)
            e = ttk.Entry(left, width=9)
            e.insert(0, default)
            e.grid(row=r + 1, column=c * 2 + 1, sticky="w", pady=3)
            self.entries[name] = e

        ttk.Button(left, text="Рассчитать", command=self.calculate).grid(
            row=7, column=0, columnspan=4, sticky="we", pady=(10, 3))
        ttk.Button(left, text="Сохранить график (SVG)", command=self.save_svg).grid(
            row=8, column=0, columnspan=4, sticky="we", pady=3)

        self.info = ttk.Label(left, text="", foreground="#555")
        self.info.grid(row=9, column=0, columnspan=4, sticky="w", pady=(5, 5))

        cols = ("i", "x", "y")
        self.table = ttk.Treeview(left, columns=cols, show="headings", height=14)
        for col, w in zip(cols, (45, 90, 110)):
            self.table.heading(col, text=col)
            self.table.column(col, width=w, anchor="e")
        sb = ttk.Scrollbar(left, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=sb.set)
        self.table.grid(row=10, column=0, columnspan=4, sticky="nsew")
        sb.grid(row=10, column=4, sticky="ns")
        left.rowconfigure(10, weight=1)

        self.canvas = tk.Canvas(self, bg="white", highlightthickness=0)
        self.canvas.pack(side="right", fill="both", expand=True, padx=(0, 10), pady=10)
        self.canvas.bind("<Configure>", lambda e: self.draw())
        self.bind("<Return>", lambda e: self.calculate())

        self.calculate()

    def read_params(self):
        return [parse_number(self.entries[name].get(), name) for name, _ in FIELDS]

    def params_text(self):
        return ", ".join(f"{n}={self.entries[n].get().strip()}" for n, _ in FIELDS)

    def calculate(self):
        try:
            self.xs, self.ys = calc_vectors(*self.read_params())
        except ValueError as err:
            messagebox.showerror("Ошибка ввода", str(err))
            return
        self.table.delete(*self.table.get_children())
        for i, (x, y) in enumerate(zip(self.xs, self.ys)):
            self.table.insert("", "end", values=(i, f"{x:.4f}", f"{y:.6f}"))
        self.info.config(text=f"Точек: {len(self.xs)};  y min = {min(self.ys):.4f},  "
                              f"y max = {max(self.ys):.4f}")
        self.draw()

    def draw(self):
        c = self.canvas
        c.delete("all")
        if not self.xs:
            return
        w, h = c.winfo_width(), c.winfo_height()
        if w < 100 or h < 100:
            return
        p = Plot(self.xs, self.ys, w, h)
        c.create_text(w / 2, 16, text="График y(x)", font=("Arial", 12, "bold"))
        xt, xstep = ticks(p.xmin, p.xmax)
        yt, ystep = ticks(p.ymin, p.ymax)
        for t in xt:
            X = p.px(t)
            c.create_line(X, p.t, X, h - p.b, fill="#ddd")
            c.create_text(X, h - p.b + 12, text=fmt(t, xstep), font=("Arial", 9))
        for t in yt:
            Y = p.py(t)
            c.create_line(p.l, Y, w - p.r, Y, fill="#ddd")
            c.create_text(p.l - 6, Y, text=fmt(t, ystep), anchor="e", font=("Arial", 9))
        if p.ymin <= 0 <= p.ymax:
            c.create_line(p.l, p.py(0), w - p.r, p.py(0))
        if p.xmin <= 0 <= p.xmax:
            c.create_line(p.px(0), p.t, p.px(0), h - p.b)
        c.create_rectangle(p.l, p.t, w - p.r, h - p.b, outline="#888")
        pts = []
        for x, y in zip(self.xs, self.ys):
            pts += [p.px(x), p.py(y)]
        if len(pts) >= 4:
            c.create_line(*pts, fill="#1f5fbf", width=2)
        else:
            c.create_oval(pts[0] - 3, pts[1] - 3, pts[0] + 3, pts[1] + 3, fill="#1f5fbf")
        c.create_text(w - p.r, h - 10, text="x", anchor="e")
        c.create_text(14, p.t - 10, text="y")

    def save_svg(self):
        if not self.xs:
            return
        path = filedialog.asksaveasfilename(defaultextension=".svg", initialfile="graph.svg",
                                            filetypes=[("SVG", "*.svg")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(build_svg(self.xs, self.ys, self.params_text()))
            messagebox.showinfo("Готово", f"График сохранён:\n{path}")


if __name__ == "__main__":
    App().mainloop()
