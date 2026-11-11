"""
Лабораторная работа №2. Методы и средства обработки сигналов.
Студент: Плотнов А. А., группа 24-ВМз.

Сигнал y(x) = μ1(x) — результат наложения фильтра F1 теории активного
восприятия (один уровень Q-пирамиды) на часть изображения шириной w и высотой,
равной высоте изображения. Окно сдвигается слева направо с шагом d.
У фильтра F1 заштрихованы два правых столбца из четырёх, поэтому
μ1 = (суммарная яркость правой половины окна) − (суммарная яркость левой половины).

Изображение загружается библиотекой Pillow и переводится в оттенки серого
(яркость пикселя 0…255). Интерфейс — tkinter: изображение и график под ним
в одном масштабе по x, таблица векторов x и y, сохранение графика в SVG.
"""

import math
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from PIL import Image, ImageTk


# ---------------------------------------------------------------- расчёт ---

def load_gray(path):
    """Загружает изображение и возвращает (ширина, высота, яркости по строкам)."""
    img = Image.open(path)
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        rgba = img.convert("RGBA")
        bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        img = Image.alpha_composite(bg, rgba)  # прозрачность -> белый фон
    gray = img.convert("L")  # L = 0.299 R + 0.587 G + 0.114 B
    w, h = gray.size
    data = list(gray.getdata())
    return w, h, [data[r * w:(r + 1) * w] for r in range(h)]


def column_sums(width, rows):
    """Суммарная яркость каждого столбца изображения."""
    return [sum(row[c] for row in rows) for c in range(width)]


def mu1_signal(cols, w, d):
    """
    Векторы x и y. Окно начинается в s = 0, d, 2d, ... и берётся только целиком
    (s + w <= ширина изображения). x — середина окна: s + w/2.
    """
    width = len(cols)
    if w <= 0 or w % 4 != 0:
        raise ValueError("Ширина фильтра w должна быть положительным числом, кратным 4.")
    if w > width:
        raise ValueError(f"Ширина фильтра w = {w} больше ширины изображения ({width} пикс.).")
    if d <= 0:
        raise ValueError("Шаг сдвига d должен быть положительным целым числом.")
    pref = [0]
    for v in cols:
        pref.append(pref[-1] + v)  # pref[i] = сумма столбцов 0..i-1
    half = w // 2
    xs, ys = [], []
    s = 0
    while s + w <= width:
        left = pref[s + half] - pref[s]
        right = pref[s + w] - pref[s + half]
        xs.append(s + half)
        ys.append(right - left)
        s += d
    return xs, ys


def parse_int(text, name):
    try:
        return int(text.strip())
    except ValueError:
        raise ValueError(f"Поле «{name}»: «{text}» не является целым числом.")


# ------------------------------------------------------------ оси и сетка ---

def nice_step(span, ticks=8):
    if span <= 0:
        return 1.0
    raw = span / ticks
    power = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 5, 10):
        if raw <= m * power:
            return m * power
    return 10 * power


def ticks(lo, hi, n=8):
    step = nice_step(hi - lo, n)
    t = math.ceil(lo / step - 1e-9) * step
    out = []
    while t <= hi + step * 1e-9:
        out.append(0.0 if abs(t) < step * 1e-9 else t)
        t += step
    return out, step


def fmt(v):
    return f"{v:.0f}" if abs(v - round(v)) < 1e-9 else f"{v:g}"


class Axes:
    """Пересчёт (x, y) в пиксели. По x — координаты пикселей изображения 0…ширина."""

    def __init__(self, img_width, ys, left, top, plot_w, plot_h):
        self.iw = img_width
        self.l, self.t, self.pw, self.ph = left, top, plot_w, plot_h
        lo, hi = min(ys + [0]), max(ys + [0])
        if lo == hi:
            lo, hi = lo - 1, hi + 1
        pad = (hi - lo) * 0.05
        self.ymin, self.ymax = lo - pad, hi + pad

    def px(self, x):
        return self.l + x / self.iw * self.pw

    def py(self, y):
        return self.t + (self.ymax - y) / (self.ymax - self.ymin) * self.ph


def build_svg(xs, ys, img_width, title, width=900, height=420):
    L, R, T, B = 80, 20, 50, 45
    a = Axes(img_width, ys, L, T, width - L - R, height - T - B)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
         f'viewBox="0 0 {width} {height}" font-family="Arial" font-size="12">',
         f'<rect width="{width}" height="{height}" fill="white"/>',
         f'<text x="{width / 2}" y="20" text-anchor="middle" font-size="15">y(x) = μ1(x)</text>',
         f'<text x="{width / 2}" y="37" text-anchor="middle" fill="#555">{title}</text>']
    xt, _ = ticks(0, img_width, 10)
    for t in xt:
        X = a.px(t)
        o.append(f'<line x1="{X:.1f}" y1="{T}" x2="{X:.1f}" y2="{height - B}" stroke="#e2e2e2"/>')
        o.append(f'<text x="{X:.1f}" y="{height - B + 16}" text-anchor="middle">{fmt(t)}</text>')
    yt, _ = ticks(a.ymin, a.ymax)
    for t in yt:
        Y = a.py(t)
        o.append(f'<line x1="{L}" y1="{Y:.1f}" x2="{width - R}" y2="{Y:.1f}" stroke="#e2e2e2"/>')
        o.append(f'<text x="{L - 6}" y="{Y + 4:.1f}" text-anchor="end">{fmt(t)}</text>')
    o.append(f'<line x1="{L}" y1="{a.py(0):.1f}" x2="{width - R}" y2="{a.py(0):.1f}" stroke="black"/>')
    o.append(f'<rect x="{L}" y="{T}" width="{a.pw}" height="{a.ph}" fill="none" stroke="#888"/>')
    pts = " ".join(f"{a.px(x):.2f},{a.py(y):.2f}" for x, y in zip(xs, ys))
    o.append(f'<polyline points="{pts}" fill="none" stroke="#1f5fbf" stroke-width="1.6"/>')
    o.append(f'<text x="{width - R}" y="{height - 8}" text-anchor="end">x, пикс.</text>')
    o.append(f'<text x="10" y="{T - 8}">μ1</text>')
    o.append('</svg>')
    return "\n".join(o)


# ------------------------------------------------------------- интерфейс ---

HERE = os.path.dirname(os.path.abspath(__file__))
IMG_EXT = (".jpg", ".jpeg", ".png", ".bmp", ".gif")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ЛР №2 — фильтр F1, сигнал μ1(x) (Плотнов А. А., 24-ВМз)")
        self.geometry("1250x700")
        self.minsize(950, 560)
        self.path = None
        self.width_px = self.height_px = 0
        self.cols = []
        self.xs, self.ys = [], []
        self.photo = None
        self.pil = None

        top = ttk.Frame(self, padding=(10, 8))
        top.pack(side="top", fill="x")
        ttk.Label(top, text="Изображение:").pack(side="left")
        files = sorted(f for f in os.listdir(HERE) if f.lower().endswith(IMG_EXT))
        self.combo = ttk.Combobox(top, values=files, width=14, state="readonly")
        self.combo.pack(side="left", padx=(4, 4))
        self.combo.bind("<<ComboboxSelected>>", lambda e: self.open_image(os.path.join(HERE, self.combo.get())))
        ttk.Button(top, text="Открыть…", command=self.choose_file).pack(side="left", padx=(0, 16))
        ttk.Label(top, text="w =").pack(side="left")
        self.e_w = ttk.Entry(top, width=6)
        self.e_w.insert(0, "8")
        self.e_w.pack(side="left", padx=(2, 10))
        ttk.Label(top, text="d =").pack(side="left")
        self.e_d = ttk.Entry(top, width=6)
        self.e_d.insert(0, "1")
        self.e_d.pack(side="left", padx=(2, 10))
        ttk.Button(top, text="Рассчитать", command=self.calculate).pack(side="left", padx=4)
        ttk.Button(top, text="Сохранить график (SVG)", command=self.save_svg).pack(side="left", padx=4)
        self.info = ttk.Label(top, text="", foreground="#555")
        self.info.pack(side="left", padx=12)

        body = ttk.Frame(self, padding=(10, 0, 10, 10))
        body.pack(fill="both", expand=True)
        cols = ("i", "x", "y")
        tf = ttk.Frame(body)
        tf.pack(side="left", fill="y")
        self.table = ttk.Treeview(tf, columns=cols, show="headings")
        for c, w in zip(cols, (50, 60, 90)):
            self.table.heading(c, text=c if c != "y" else "y = μ1")
            self.table.column(c, width=w, anchor="e")
        sb = ttk.Scrollbar(tf, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=sb.set)
        self.table.pack(side="left", fill="y")
        sb.pack(side="left", fill="y")

        self.canvas = tk.Canvas(body, bg="white", highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True, padx=(10, 0))
        self.canvas.bind("<Configure>", lambda e: self.draw())
        self.bind("<Return>", lambda e: self.calculate())

        if files:
            self.combo.current(0)
            self.open_image(os.path.join(HERE, files[0]))

    # --- данные
    def choose_file(self):
        p = filedialog.askopenfilename(initialdir=HERE, filetypes=[("Изображения", "*.jpg *.jpeg *.png *.bmp *.gif")])
        if p:
            self.combo.set(os.path.basename(p))
            self.open_image(p)

    def open_image(self, path):
        try:
            self.width_px, self.height_px, rows = load_gray(path)
            self.pil = Image.open(path).convert("RGB")
        except Exception as err:
            messagebox.showerror("Ошибка", f"Не удалось открыть изображение:\n{err}")
            return
        self.path = path
        self.cols = column_sums(self.width_px, rows)
        self.calculate()

    def calculate(self):
        if not self.path:
            return
        try:
            w = parse_int(self.e_w.get(), "w")
            d = parse_int(self.e_d.get(), "d")
            xs, ys = mu1_signal(self.cols, w, d)
        except ValueError as err:
            messagebox.showerror("Ошибка ввода", str(err))
            return
        self.xs, self.ys, self.w, self.d = xs, ys, w, d
        self.table.delete(*self.table.get_children())
        for i, (x, y) in enumerate(zip(xs, ys)):
            self.table.insert("", "end", values=(i, x, y))
        imin = min(range(len(ys)), key=ys.__getitem__)
        imax = max(range(len(ys)), key=ys.__getitem__)
        self.info.config(text=f"{os.path.basename(self.path)}: {self.width_px}×{self.height_px} пикс.;  "
                              f"точек: {len(xs)};  min {ys[imin]} при x={xs[imin]};  "
                              f"max {ys[imax]} при x={xs[imax]}")
        self.draw()

    # --- рисование: изображение сверху, график под ним в том же масштабе по x
    def draw(self):
        c = self.canvas
        c.delete("all")
        if not self.xs:
            return
        cw, ch = c.winfo_width(), c.winfo_height()
        if cw < 200 or ch < 200:
            return
        L, R = 70, 15
        pw = cw - L - R
        scale = pw / self.width_px
        ih = max(1, int(self.height_px * scale))
        ih = min(ih, int(ch * 0.35))
        img = self.pil.resize((pw, ih), Image.NEAREST)
        self.photo = ImageTk.PhotoImage(img)
        c.create_image(L, 10, image=self.photo, anchor="nw")
        c.create_rectangle(L, 10, L + pw, 10 + ih, outline="#888")

        top = 10 + ih + 30
        a = Axes(self.width_px, self.ys, L, top, pw, ch - top - 35)
        c.create_text(L + pw / 2, top - 14, text=f"y(x) = μ1(x),  w = {self.w},  d = {self.d}",
                      font=("Arial", 11, "bold"))
        xt, _ = ticks(0, self.width_px, 10)
        for t in xt:
            X = a.px(t)
            c.create_line(X, top, X, top + a.ph, fill="#e2e2e2")
            c.create_line(X, 10 + ih, X, 10 + ih + 5, fill="#888")  # риски под изображением
            c.create_text(X, top + a.ph + 12, text=fmt(t), font=("Arial", 9))
        yt, _ = ticks(a.ymin, a.ymax)
        for t in yt:
            Y = a.py(t)
            c.create_line(L, Y, L + pw, Y, fill="#e2e2e2")
            c.create_text(L - 6, Y, text=fmt(t), anchor="e", font=("Arial", 9))
        c.create_line(L, a.py(0), L + pw, a.py(0))
        c.create_rectangle(L, top, L + pw, top + a.ph, outline="#888")
        pts = []
        for x, y in zip(self.xs, self.ys):
            pts += [a.px(x), a.py(y)]
        if len(pts) >= 4:
            c.create_line(*pts, fill="#1f5fbf", width=2)
        else:
            c.create_oval(pts[0] - 3, pts[1] - 3, pts[0] + 3, pts[1] + 3, fill="#1f5fbf")
        c.create_text(L + pw, ch - 8, text="x, пикс.", anchor="e", font=("Arial", 9))
        c.create_text(L - 40, top - 14, text="μ1", font=("Arial", 9))

    def save_svg(self):
        if not self.xs:
            return
        base = os.path.splitext(os.path.basename(self.path))[0]
        p = filedialog.asksaveasfilename(initialdir=HERE, defaultextension=".svg",
                                         initialfile=f"{base}_w{self.w}_d{self.d}.svg",
                                         filetypes=[("SVG", "*.svg")])
        if p:
            with open(p, "w", encoding="utf-8") as f:
                f.write(build_svg(self.xs, self.ys, self.width_px,
                                  f"{os.path.basename(self.path)}, w = {self.w}, d = {self.d}"))
            messagebox.showinfo("Готово", f"График сохранён:\n{p}")


if __name__ == "__main__":
    App().mainloop()
