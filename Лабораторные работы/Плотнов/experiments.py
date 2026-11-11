"""
Эксперименты к ЛР №2: сигнал μ1(x) при разных w и d и сравнение его
характерных точек с границами символов, найденными по изображению вручную.

Граница символа задаётся координатой x между столбцами:
  левая граница  — первый столбец, где начинается символ;
  правая граница — первый столбец после символа (последний столбец + 1).
Так для тёмного символа на светлом фоне левой границе соответствует минимум μ1,
правой — максимум (это проверено на тестовом изображении test.png).

Характерная точка — локальный минимум (максимум), который является наименьшим
(наибольшим) значением в окрестности ±w/2 пикселей и по модулю не меньше 10 %
от наибольшего |μ1| на этом графике. Для каждой границы ищется ближайшая
характерная точка нужного типа не дальше 5 + d/2 пикселей (d/2 — потому что
при шаге d значения есть только в каждом d-м столбце).

Запуск: python experiments.py  -> results/ (таблицы .txt и графики .png)
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lab2  # noqa: E402
OUT = os.path.join(HERE, "results")

# границы символов, определённые по увеличенному изображению (x, пикс.)
LETTERS = {
    "03.jpg": [("y", 19, 37), ("g", 46, 71), ("h", 67, 95), ("k", 97, 125), ("x", 123, 145), ("r", 158, 169)],
    "08.jpg": [("G", 25, 72), ("b", 70, 104), ("s", 105, 131), ("w", 129, 169), ("7", 166, 202),
               ("3", 196, 229), ("p", 222, 263)],
    "test.png": [("▮1", 20, 40), ("▮2", 70, 90)],
}
RUNS = [(4, 1), (8, 1), (16, 1), (32, 1), (8, 4), (8, 8)]
TOL = 5  # допустимое расхождение, пикс. (плюс d/2 на дискретность шага)


def extrema(xs, ys, w):
    """Характерные точки: список (x, y, 'min'|'max')."""
    lim = 0.1 * max(abs(v) for v in ys)
    res = []
    for i, (x, y) in enumerate(zip(xs, ys)):
        near = [ys[j] for j in range(len(xs)) if abs(xs[j] - x) <= w / 2]
        if y < 0 and abs(y) >= lim and y == min(near):
            if not res or res[-1][2] != "min" or x - res[-1][0] > w / 2:  # плато -> одна точка
                res.append((x, y, "min"))
        if y > 0 and y >= lim and y == max(near):
            if not res or res[-1][2] != "max" or x - res[-1][0] > w / 2:
                res.append((x, y, "max"))
    return res


def match(letters, ext, w, d):
    """Для каждой границы — ближайшая характерная точка нужного типа."""
    tol = TOL + d / 2
    rows, used = [], set()
    for name, lb, rb in letters:
        for side, b, kind in (("лев.", lb, "min"), ("прав.", rb, "max")):
            cand = [(abs(x - b), x) for x, y, k in ext if k == kind and abs(x - b) <= tol]
            if cand:
                dist, x = min(cand)
                used.add((x, kind))
                rows.append((name, side, b, x, x - b))
            else:
                rows.append((name, side, b, None, None))
    extra = sum(1 for x, y, k in ext if (x, k) not in used)
    return rows, extra


def figure(path, xs, ys, w, d, out):
    """Изображение и график под ним в одном масштабе по x."""
    img = Image.open(path).convert("RGB")
    W, H = img.size
    k = max(1, 900 // W)
    PW = W * k
    L, R, T = 70, 20, 10
    GH = 260
    canvas = Image.new("RGB", (L + PW + R, T + H * k + 30 + GH + 40), "white")
    canvas.paste(img.resize((PW, H * k), Image.NEAREST), (L, T))
    dr = ImageDraw.Draw(canvas)
    f = ImageFont.truetype("arial.ttf", 13)
    fb = ImageFont.truetype("arialbd.ttf", 14)
    dr.rectangle([L, T, L + PW, T + H * k], outline=(140, 140, 140))
    top = T + H * k + 30
    a = lab2.Axes(W, ys, L, top, PW, GH)
    dr.text((L + PW // 2 - 140, top - 22), f"{os.path.basename(path)}:  y(x) = μ1(x),  w = {w},  d = {d}",
            fill="black", font=fb)
    xt, _ = lab2.ticks(0, W, 10)
    for t in xt:
        X = a.px(t)
        dr.line([(X, top), (X, top + GH)], fill=(226, 226, 226))
        dr.line([(X, T + H * k), (X, T + H * k + 5)], fill=(140, 140, 140))
        dr.text((X - 8, top + GH + 4), lab2.fmt(t), fill="black", font=f)
    yt, _ = lab2.ticks(a.ymin, a.ymax)
    for t in yt:
        Y = a.py(t)
        dr.line([(L, Y), (L + PW, Y)], fill=(226, 226, 226))
        s = lab2.fmt(t)
        dr.text((L - 8 - dr.textlength(s, font=f), Y - 7), s, fill="black", font=f)
    dr.line([(L, a.py(0)), (L + PW, a.py(0))], fill="black")
    dr.rectangle([L, top, L + PW, top + GH], outline=(140, 140, 140))
    pts = [(a.px(x), a.py(y)) for x, y in zip(xs, ys)]
    if len(pts) > 1:
        dr.line(pts, fill=(31, 95, 191), width=2)
    dr.text((L + PW - 50, top + GH + 20), "x, пикс.", fill="black", font=f)
    canvas.save(out)


def main():
    os.makedirs(OUT, exist_ok=True)
    report = []
    summary = {}
    for fname, letters in LETTERS.items():
        path = os.path.join(HERE, fname)
        W, H, rows = lab2.load_gray(path)
        cols = lab2.column_sums(W, rows)
        report.append(f"\n===== {fname} ({W}×{H}) =====")
        per_run = {}
        for w, d in RUNS:
            xs, ys = lab2.mu1_signal(cols, w, d)
            ext = extrema(xs, ys, w)
            m, extra = match(letters, ext, w, d)
            per_run[(w, d)] = (m, extra, len(xs))
            figure(path, xs, ys, w, d, os.path.join(OUT, f"{os.path.splitext(fname)[0]}_w{w}_d{d}.png"))
            with open(os.path.join(OUT, f"{os.path.splitext(fname)[0]}_w{w}_d{d}.svg"), "w", encoding="utf-8") as fh:
                fh.write(lab2.build_svg(xs, ys, W, f"{fname}, w = {w}, d = {d}"))
            report.append(f"w={w} d={d}: точек {len(xs)}; характерные точки: "
                          + ", ".join(f"{k}({x})" for x, y, k in ext))
        summary[fname] = per_run
        # сводная таблица: строки — границы, столбцы — эксперименты
        head = "символ  граница   x гр. | " + " | ".join(f"w{w}/d{d}".rjust(9) for w, d in RUNS)
        report.append(head)
        for i, (name, side, b, _, _) in enumerate(per_run[RUNS[0]][0]):
            cells = []
            for run in RUNS:
                _, _, _, x, dx = per_run[run][0][i]
                cells.append("—".rjust(9) if x is None else f"{x} ({dx:+d})".rjust(9))
            report.append(f"{name:>5}  {side:<6} {b:6d}   | " + " | ".join(cells))
        found = [sum(1 for r in per_run[run][0] if r[3] is not None) for run in RUNS]
        total = len(per_run[RUNS[0]][0])
        report.append("найдено         " + "        | " + " | ".join(f"{f}/{total}".rjust(9) for f in found))
        report.append("лишние экстр.   " + "        | " + " | ".join(str(per_run[r][1]).rjust(9) for r in RUNS))
    text = "\n".join(report)
    with open(os.path.join(OUT, "сводная_таблица.txt"), "w", encoding="utf-8") as fh:
        fh.write(text + "\n")
    print(text)
    return summary


if __name__ == "__main__":
    main()
