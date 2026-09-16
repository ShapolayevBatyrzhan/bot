# -*- coding: utf-8 -*-
"""Мини-библиотека для рисования блок-схем (ГОСТ 19.701) средствами matplotlib.

Фигуры:
    terminator  -- «Начало» / «Конец»      (скруглённый прямоугольник)
    io          -- ввод/вывод              (параллелограмм)
    process     -- вычисления              (прямоугольник)
    predefined  -- предопределённый процесс (прямоугольник с двойными боковинами)
    decision    -- развилка                (ромб)
    loop_start  -- начало цикла            (срезаны верхние углы)
    loop_end    -- конец цикла             (срезаны нижние углы)
    connector   -- соединитель             (кружок)

Система координат: x вправо, y ВНИЗ (как читается схема).
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle
from matplotlib.lines import Line2D

INK = "#1a1a19"
SURFACE = "#fcfcfb"
MUTED = "#6f6e69"

FILL = {
    "terminator": "#eceae5",
    "io": "#fdf0e9",
    "process": "#ffffff",
    "predefined": "#ffffff",
    "decision": "#e8f1fc",
    "loop": "#eaf7f2",
    "connector": "#ffffff",
}


class Node(object):
    """Блок схемы; хранит центр и полуразмеры, отдаёт точки привязки."""

    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h

    @property
    def n(self):
        return (self.x, self.y - self.h / 2.0)

    @property
    def s(self):
        return (self.x, self.y + self.h / 2.0)

    @property
    def e(self):
        return (self.x + self.w / 2.0, self.y)

    @property
    def w_(self):
        return (self.x - self.w / 2.0, self.y)

    @property
    def c(self):
        return (self.x, self.y)


class Chart(object):
    def __init__(self, width, height, title=None, subtitle=None, scale=0.62, top=1.5):
        self.dy = float(top)                     # запас сверху под заголовок
        self.W, self.H = float(width), float(height) + self.dy
        self.fig, self.ax = plt.subplots(figsize=(self.W * scale, self.H * scale))
        self.ax.set_xlim(0, self.W)
        self.ax.set_ylim(self.H, 0)                 # ось y вниз
        self.ax.set_aspect("equal")
        self.ax.axis("off")
        self.fig.patch.set_facecolor(SURFACE)
        if title:
            self.ax.text(0.2, 0.30, title, fontsize=13, fontweight="bold",
                         color=INK, ha="left", va="top")
        if subtitle:
            self.ax.text(0.2, 1.15, subtitle, fontsize=10, color=MUTED,
                         ha="left", va="top")

    def Y(self, v):
        """Абсолютная ордината для «сырой» координаты (с учётом верхнего поля)."""
        return float(v) + self.dy

    # ---------------------------------------------------------------- фигуры
    def _label(self, x, y, text, fs=10):
        self.ax.text(x, y, text, fontsize=fs, color=INK, ha="center", va="center",
                     linespacing=1.55, zorder=5)

    def _num(self, node, num):
        if num is None:
            return
        self.ax.text(node.x - node.w / 2.0 - 0.45, node.y - node.h / 2.0 + 0.32,
                     str(num), fontsize=9, color=MUTED, ha="right", va="center")

    def _add(self, patch):
        patch.set_zorder(2)
        self.ax.add_patch(patch)

    def process(self, x, y, text, w=4.4, h=1.3, num=None, fs=10):
        y += self.dy
        self._add(Rectangle((x - w / 2.0, y - h / 2.0), w, h,
                            facecolor=FILL["process"], edgecolor=INK, lw=1.4))
        self._label(x, y, text, fs)
        node = Node(x, y, w, h)
        self._num(node, num)
        return node

    def predefined(self, x, y, text, w=2.6, h=1.1, num=None, fs=10):
        y += self.dy
        self._add(Rectangle((x - w / 2.0, y - h / 2.0), w, h,
                            facecolor=FILL["predefined"], edgecolor=INK, lw=1.4))
        for dx in (-w / 2.0 + 0.22, w / 2.0 - 0.22):
            self.ax.add_line(Line2D([x + dx, x + dx], [y - h / 2.0, y + h / 2.0],
                                    color=INK, lw=1.2, zorder=3))
        self._label(x, y, text, fs)
        node = Node(x, y, w, h)
        self._num(node, num)
        return node

    def terminator(self, x, y, text, w=3.4, h=1.1, num=None, fs=10):
        y += self.dy
        self._add(FancyBboxPatch((x - w / 2.0 + h / 2.0, y - h / 2.0 + 0.02),
                                 w - h, h - 0.04,
                                 boxstyle="round,pad=%.3f,rounding_size=%.3f" % (h / 2.0 - 0.02, h / 2.0),
                                 facecolor=FILL["terminator"], edgecolor=INK, lw=1.4))
        self._label(x, y, text, fs)
        node = Node(x, y, w, h)
        self._num(node, num)
        return node

    def io(self, x, y, text, w=4.4, h=1.3, num=None, fs=10, skew=0.45):
        y += self.dy
        pts = [(x - w / 2.0 + skew, y - h / 2.0), (x + w / 2.0, y - h / 2.0),
               (x + w / 2.0 - skew, y + h / 2.0), (x - w / 2.0, y + h / 2.0)]
        self._add(Polygon(pts, closed=True, facecolor=FILL["io"], edgecolor=INK, lw=1.4))
        self._label(x, y, text, fs)
        node = Node(x, y, w, h)
        self._num(node, num)
        return node

    def decision(self, x, y, text, w=5.6, h=2.2, num=None, fs=10):
        y += self.dy
        pts = [(x, y - h / 2.0), (x + w / 2.0, y), (x, y + h / 2.0), (x - w / 2.0, y)]
        self._add(Polygon(pts, closed=True, facecolor=FILL["decision"], edgecolor=INK, lw=1.4))
        self._label(x, y, text, fs)
        node = Node(x, y, w, h)
        self._num(node, num)
        return node

    def _loop(self, x, y, text, w, h, num, fs, top):
        y += self.dy
        c = 0.55
        if top:
            pts = [(x - w / 2.0 + c, y - h / 2.0), (x + w / 2.0 - c, y - h / 2.0),
                   (x + w / 2.0, y - h / 2.0 + c), (x + w / 2.0, y + h / 2.0),
                   (x - w / 2.0, y + h / 2.0), (x - w / 2.0, y - h / 2.0 + c)]
        else:
            pts = [(x - w / 2.0, y - h / 2.0), (x + w / 2.0, y - h / 2.0),
                   (x + w / 2.0, y + h / 2.0 - c), (x + w / 2.0 - c, y + h / 2.0),
                   (x - w / 2.0 + c, y + h / 2.0), (x - w / 2.0, y + h / 2.0 - c)]
        self._add(Polygon(pts, closed=True, facecolor=FILL["loop"], edgecolor=INK, lw=1.4))
        self._label(x, y, text, fs)
        node = Node(x, y, w, h)
        self._num(node, num)
        return node

    def loop_start(self, x, y, text, w=4.4, h=1.4, num=None, fs=10):
        return self._loop(x, y, text, w, h, num, fs, True)

    def loop_end(self, x, y, text, w=4.4, h=1.4, num=None, fs=10):
        return self._loop(x, y, text, w, h, num, fs, False)

    def connector(self, x, y, r=0.26, num=None):
        y += self.dy
        self._add(Circle((x, y), r, facecolor=FILL["connector"], edgecolor=INK, lw=1.4))
        node = Node(x, y, 2 * r, 2 * r)
        self._num(node, num)
        return node

    # ---------------------------------------------------------------- связи
    def arrow(self, p1, p2, label=None, lpos=0.5, loff=(0.0, -0.3), fs=10):
        self.ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=13,
                                          lw=1.4, color=INK, shrinkA=0, shrinkB=0,
                                          zorder=4))
        if label:
            mx = p1[0] + (p2[0] - p1[0]) * lpos + loff[0]
            my = p1[1] + (p2[1] - p1[1]) * lpos + loff[1]
            self.ax.text(mx, my, label, fontsize=fs, color=INK, ha="center",
                         va="center", zorder=5,
                         bbox=dict(boxstyle="square,pad=0.12", fc=SURFACE, ec="none"))

    def route(self, points, label=None, lat=0, loff=(0.0, -0.3), fs=10):
        """Ломаная со стрелкой на конце; label ставится у сегмента номер `lat`."""
        for i in range(len(points) - 2):
            self.ax.add_line(Line2D([points[i][0], points[i + 1][0]],
                                    [points[i][1], points[i + 1][1]],
                                    color=INK, lw=1.4, zorder=3,
                                    solid_capstyle="projecting"))
        self.ax.add_patch(FancyArrowPatch(points[-2], points[-1], arrowstyle="-|>",
                                          mutation_scale=13, lw=1.4, color=INK,
                                          shrinkA=0, shrinkB=0, zorder=4))
        if label:
            p1, p2 = points[lat], points[lat + 1]
            mx = (p1[0] + p2[0]) / 2.0 + loff[0]
            my = (p1[1] + p2[1]) / 2.0 + loff[1]
            self.ax.text(mx, my, label, fontsize=fs, color=INK, ha="center",
                         va="center", zorder=5,
                         bbox=dict(boxstyle="square,pad=0.12", fc=SURFACE, ec="none"))

    def link(self, p1, p2):
        """Линия без стрелки (например, к блоку f(x))."""
        self.ax.add_line(Line2D([p1[0], p2[0]], [p1[1], p2[1]], color=INK,
                                lw=1.4, zorder=3))

    def save(self, path):
        self.fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=SURFACE)
        plt.close(self.fig)
