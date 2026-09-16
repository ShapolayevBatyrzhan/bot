# -*- coding: utf-8 -*-
"""Единый стиль графиков для заданий № 2 и № 3."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Палитра (проверена на различимость при дальтонизме).
SURFACE = "#fcfcfb"
INK     = "#0b0b0b"
INK2    = "#52514e"
MUTED   = "#8a8983"
GRID    = "#e6e5e1"
SERIES  = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]   # синий, оранжевый, бирюзовый, жёлтый
ZERO    = "#52514e"

# Маркеры -- вторая (не цветовая) кодировка рядов.
MARKERS = ["o", "s", "^", "D"]


def apply_style():
    plt.rcParams.update({
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.titlecolor": INK,
        "axes.labelsize": 11,
        "axes.labelcolor": INK2,
        "axes.edgecolor": GRID,
        "axes.linewidth": 1.0,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "xtick.color": INK2,
        "ytick.color": INK2,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "grid.color": GRID,
        "grid.linewidth": 0.8,
        "axes.grid": True,
        "legend.frameon": False,
        "legend.fontsize": 10,
        "legend.labelcolor": INK2,
        "lines.linewidth": 2.0,
        "lines.markersize": 7,
        "figure.dpi": 150,
        "savefig.dpi": 150,
        "savefig.bbox": "tight",
    })


def finish(ax, title=None, xlabel=None, ylabel=None, subtitle=None):
    if title:
        ax.set_title(title, loc="left", pad=26 if subtitle else 10)
    if subtitle:
        ax.text(0.0, 1.02, subtitle, transform=ax.transAxes,
                fontsize=10, color=MUTED, ha="left", va="bottom")
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    ax.set_axisbelow(True)
