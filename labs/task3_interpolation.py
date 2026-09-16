# -*- coding: utf-8 -*-
"""ЗАДАНИЕ № 3. ИНТЕРПОЛИРОВАНИЕ. Многочлен Ньютона 2-го порядка.

Этапы (по методичке):
  1) таблица y_j = y(x_j) в равноотстоящих узлах x_j = j*h, h = 1/n, j = 0..n;
  2) таблица первых разностей      Δy_j = y_(j+1) − y_j  и  f[x_j,x_(j+1)] = Δy_j/h;
  3) таблица вторых разделённых разностей  f[x_j,x_(j+1),x_(j+2)] = Δ²y_j/(2h²);
  4) вычисление P(x) по многочлену Ньютона 2-го порядка
        P(x) = y_i + (x−x_i)·f[x_i,x_(i+1)] + (x−x_i)(x−x_(i+1))·f[x_i,x_(i+1),x_(i+2)]
     в узлах с полуцелыми индексами x_(j+1/2) = x_j + h/2;
  5) погрешности ε_(j+1/2) = P(x_(j+1/2)) − y(x_(j+1/2)), ε_max, средний квадрат, ε_m;
  6) исследование зависимости ε_max и ε_m от n.

Запуск:
    python3 task3_interpolation.py                    # вариант 1, a=b=k=m=1, n=20
    python3 task3_interpolation.py -v 33 -n 50
    python3 task3_interpolation.py -v 0               # тест y = x^2 (погрешности = 0)
    python3 task3_interpolation.py --list
"""

import argparse
import os

import numpy as np

import nm_core as core
import nm_style as st
from nm_style import SERIES, MARKERS, INK, INK2, MUTED

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")


# ==========================================================================
#                        ЯДРО: интерполяция Ньютона
# ==========================================================================
def interpolate(y, n):
    """Возвращает словарь со всеми таблицами задания для заданного n."""
    h = 1.0 / n
    x = np.linspace(0.0, 1.0, n + 1)            # узлы x_j, j = 0..n
    yv = np.asarray(y(x), dtype=float)          # значения y_j

    dy = np.diff(yv)                            # первые разности Δy_j, j = 0..n-1
    d1 = dy / h                                 # f[x_j, x_(j+1)]
    d2 = np.diff(dy) / (2.0 * h * h)            # f[x_j, x_(j+1), x_(j+2)], j = 0..n-2

    xh = x[:-1] + h / 2.0                       # узлы с полуцелыми индексами
    # база интерполяции: тройка (x_i, x_(i+1), x_(i+2)); у правого края сдвигаем влево
    base = np.minimum(np.arange(n), n - 2)

    P = (yv[base]
         + (xh - x[base]) * d1[base]
         + (xh - x[base]) * (xh - x[base + 1]) * d2[base])

    y_exact = np.asarray(y(xh), dtype=float)
    err = P - y_exact                           # погрешность интерполирования

    eps_max = float(np.max(np.abs(err)))
    mean_sq = float(np.mean(err ** 2))          # средний квадрат погрешности
    eps_m = float(np.sqrt(mean_sq))             # среднеквадратичная погрешность

    return dict(h=h, x=x, y=yv, dy=dy, d1=d1, d2=d2, xh=xh, P=P,
                y_exact=y_exact, err=err, eps_max=eps_max,
                mean_sq=mean_sq, eps_m=eps_m, base=base, n=n)


# ==========================================================================
#                              ТАБЛИЦЫ
# ==========================================================================
def print_tables(r, rows=12):
    n = r["n"]
    show = min(rows, n)
    print(u"\nТАБЛИЦА УЗЛОВ, ПЕРВЫХ И ВТОРЫХ РАЗДЕЛЁННЫХ РАЗНОСТЕЙ  (первые %d строк из %d)" % (show, n + 1))
    print("  %3s | %-10s | %-14s | %-14s | %-14s | %-14s"
          % ("j", "x_j", "y_j", "Δy_j", "f[x_j,x_j+1]", "f[..,x_j+2]"))
    print("  " + "-" * 82)
    for j in range(show):
        d1s = "%14.6f" % r["d1"][j] if j < n else " " * 14
        dys = "%14.6e" % r["dy"][j] if j < n else " " * 14
        d2s = "%14.6f" % r["d2"][j] if j < n - 1 else " " * 14
        print("  %3d | %10.6f | %14.6f | %s | %s | %s"
              % (j, r["x"][j], r["y"][j], dys, d1s, d2s))
    if show < n + 1:
        print("  ... (%d строк опущено)" % (n + 1 - show))

    print(u"\nТАБЛИЦА ПОГРЕШНОСТЕЙ В УЗЛАХ С ПОЛУЦЕЛЫМИ ИНДЕКСАМИ  (первые %d строк из %d)"
          % (show, n))
    print("  %5s | %-10s | %-14s | %-14s | %-13s"
          % ("j+1/2", "x", "P(x)", "y(x)", "ε = P − y"))
    print("  " + "-" * 70)
    for j in range(show):
        print("  %5s | %10.6f | %14.8f | %14.8f | %13.3e"
              % ("%d+1/2" % j, r["xh"][j], r["P"][j], r["y_exact"][j], r["err"][j]))
    if show < n:
        print("  ... (%d строк опущено)" % (n - show))


def save_csv(r, path):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("j;x_half;P;y;eps\n")
        for j in range(r["n"]):
            fh.write("%d;%.10f;%.12f;%.12f;%.6e\n"
                     % (j, r["xh"][j], r["P"][j], r["y_exact"][j], r["err"][j]))


# ==========================================================================
#                              ГРАФИКИ
# ==========================================================================
def plot_function(y, r, formula, params, tag):
    """y(x), узлы интерполяции и значения P(x) в полуцелых узлах."""
    import matplotlib.pyplot as plt
    t = np.linspace(0, 1, 1000)
    fig, ax = plt.subplots(figsize=(8.6, 4.8))
    ax.plot(t, y(t), color=SERIES[0], lw=2, label=u"y(x) — точная")
    ax.plot(r["x"], r["y"], "o", ms=6, color=SERIES[0],
            markeredgecolor=st.SURFACE, markeredgewidth=1.4,
            ls="none", label=u"узлы x_j (n = %d)" % r["n"])
    ax.plot(r["xh"], r["P"], "s", ms=5, color=SERIES[1],
            markeredgecolor=st.SURFACE, markeredgewidth=1.2,
            ls="none", label=u"P(x) в узлах x_(j+1/2)")
    ax.legend(loc="best")
    st.finish(ax, u"Задание № 3. Функция, узлы и интерполяция",
              "x", "y", subtitle=formula + u"    " + params)
    fig.savefig(os.path.join(OUT, "task3_%s_function.png" % tag))
    plt.close(fig)


def plot_error(r, params, tag):
    """Погрешность в полуцелых узлах."""
    import matplotlib.pyplot as plt
    # масштабируем ось вручную, чтобы множитель 1e-k стоял в подписи, а не «висел» у заголовка
    p10 = int(np.floor(np.log10(r["eps_max"]))) if r["eps_max"] > 0 else 0
    scale = 10.0 ** p10
    e = r["err"] / scale

    fig, ax = plt.subplots(figsize=(8.6, 4.4))
    ax.axhline(0, color=MUTED, lw=1.0, ls="--", alpha=0.8)
    ax.plot(r["xh"], e, color=SERIES[0], marker=MARKERS[0], ms=5,
            markeredgecolor=st.SURFACE, markeredgewidth=1.0)
    k = int(np.argmax(np.abs(e)))
    ax.plot([r["xh"][k]], [e[k]], "o", ms=9, color=SERIES[1],
            markeredgecolor=st.SURFACE, markeredgewidth=2, zorder=5)
    ax.annotate(u"ε_max = %.3e" % r["eps_max"], xy=(r["xh"][k], e[k]),
                xytext=(-12, 18), ha="right", textcoords="offset points",
                color=INK, fontsize=10,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=1))
    st.finish(ax, u"Погрешность интерполирования ε = P(x) − y(x)",
              u"x (узлы с полуцелыми индексами)",
              u"ε,  ×10^%d" % p10, subtitle=params)
    fig.savefig(os.path.join(OUT, "task3_%s_error.png" % tag))
    plt.close(fig)


def plot_differences(r, params, tag):
    """Первые и вторые разделённые разности."""
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.3))
    axes[0].plot(r["x"][:-1], r["d1"], color=SERIES[0], lw=2)
    st.finish(axes[0], u"Первая разделённая разность", "x", u"f[x_j, x_j+1] = Δy_j / h")
    axes[1].plot(r["x"][:-2], r["d2"], color=SERIES[1], lw=2)
    st.finish(axes[1], u"Вторая разделённая разность", "x", u"f[x_j, x_j+1, x_j+2]")
    fig.suptitle(params, x=0.012, y=0.995, ha="left", va="top", color=MUTED, fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.965))
    fig.savefig(os.path.join(OUT, "task3_%s_differences.png" % tag))
    plt.close(fig)


def plot_study(y, ns, formula, params, tag):
    """Как ε_max и ε_m зависят от числа узлов n."""
    import matplotlib.pyplot as plt
    emax, em = [], []
    print(u"\nЗАВИСИМОСТЬ ПОГРЕШНОСТЕЙ ОТ ЧИСЛА УЗЛОВ n")
    print("  %6s | %-12s | %-14s | %-14s | %s" % ("n", "h = 1/n", "ε_max", "ε_m", "порядок p"))
    print("  " + "-" * 70)
    prev = None
    for n in ns:
        r = interpolate(y, n)
        emax.append(r["eps_max"])
        em.append(r["eps_m"])
        if prev is None or r["eps_max"] <= 0 or prev[1] <= 0:
            p = "   --"
        else:
            p = "%5.2f" % (np.log(prev[1] / r["eps_max"]) / np.log(n / prev[0]))
        print("  %6d | %12.6f | %14.6e | %14.6e | %s"
              % (n, 1.0 / n, r["eps_max"], r["eps_m"], p))
        prev = (n, r["eps_max"])

    if max(emax) <= 0:
        print(u"  (погрешности тождественно равны нулю — график зависимости не строится)")
        return

    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    ns = np.asarray(ns, dtype=float)
    for idx, (name, vals) in enumerate(((u"ε_max", emax), (u"ε_m", em))):
        ax.loglog(ns, vals, color=SERIES[idx], marker=MARKERS[idx],
                  markeredgecolor=st.SURFACE, markeredgewidth=1.2, label=name)
        ax.annotate(name, xy=(ns[-1], vals[-1]), xytext=(9, 7 if idx == 0 else -7),
                    textcoords="offset points", color=INK2, fontsize=10, va="center")
    ref = emax[0] * 0.22 * (ns / ns[0]) ** -3.0          # опорный наклон, сдвинут вниз
    ax.loglog(ns, ref, color=MUTED, lw=1.2, ls=":", zorder=1)
    ax.text(0.03, 0.05, u"· · · ·  опорный наклон −3  (ε ~ h³)", transform=ax.transAxes,
            color=MUTED, fontsize=9, ha="left", va="bottom")
    ax.set_xlim(ns[0] * 0.85, ns[-1] * 1.6)
    ax.legend(loc="upper right")
    st.finish(ax, u"Погрешности ε_max и ε_m в зависимости от n",
              u"число интервалов n  (h = 1/n)", u"погрешность", subtitle=params)
    fig.savefig(os.path.join(OUT, "task3_%s_study.png" % tag))
    plt.close(fig)


# ==========================================================================
#                              ОСНОВНАЯ ПРОГРАММА
# ==========================================================================
def main():
    ap = argparse.ArgumentParser(description=u"Задание № 3: интерполирование")
    ap.add_argument("-v", "--variant", type=int, default=1,
                    help=u"номер варианта 1..50 (0 — тест y = x^2)")
    ap.add_argument("-a", type=float, default=1.0, help=u"параметр a (1..5)")
    ap.add_argument("-b", type=float, default=1.0, help=u"параметр b (1..5)")
    ap.add_argument("-k", type=int, default=1, help=u"параметр k (1..4)")
    ap.add_argument("-m", type=int, default=1, help=u"параметр m (1..4)")
    ap.add_argument("-n", type=int, default=20, help=u"число интервалов n (20..100)")
    ap.add_argument("--rows", type=int, default=12, help=u"сколько строк таблиц печатать")
    ap.add_argument("--no-plots", action="store_true")
    ap.add_argument("--list", action="store_true", help=u"показать список вариантов")
    args = ap.parse_args()

    if args.list:
        print(u"Варианты функций y(x) (задание № 3):")
        for n in sorted(core.Y_VARIANTS):
            print("  %2d) %s" % (n, core.Y_VARIANTS[n][0].replace("$", "")))
        return

    formula, y = core.y_variant(args.variant, a=args.a, b=args.b, k=args.k, m=args.m)
    params = u"вариант %d;  a=%g, b=%g, k=%d, m=%d;  n=%d;  h=%.5f" % (
        args.variant, args.a, args.b, args.k, args.m, args.n, 1.0 / args.n)

    print("=" * 72)
    print(u"ЗАДАНИЕ № 3. ИНТЕРПОЛИРОВАНИЕ (многочлен Ньютона 2-го порядка)")
    print("=" * 72)
    print(u"Функция:   %s" % formula.replace("$", ""))
    print(u"Параметры: %s" % params)

    r = interpolate(y, args.n)
    print_tables(r, args.rows)

    print("\n" + "-" * 72)
    print(u"ИТОГОВЫЕ ПОГРЕШНОСТИ при n = %d" % args.n)
    print(u"  максимальная погрешность   ε_max = %.6e" % r["eps_max"])
    print(u"  средний квадрат погрешн.   <ε²>  = %.6e" % r["mean_sq"])
    print(u"  среднеквадратичная погр.   ε_m   = %.6e" % r["eps_m"])
    if r["eps_max"] < 1e-12:
        print(u"  (для многочлена степени ≤ 2 интерполяция точна — погрешности нулевые)")

    tag = "v%d" % args.variant
    csv = os.path.join(OUT, "task3_%s_errors.csv" % tag)
    save_csv(r, csv)
    print(u"\nТаблица погрешностей полностью сохранена: %s" % csv)

    ns = [20, 30, 40, 50, 60, 80, 100, 200, 400, 800]
    if not args.no_plots:
        st.apply_style()
        plot_function(y, r, formula, params, tag)
        plot_error(r, params, tag)
        plot_differences(r, params, tag)
        study_params = u"вариант %d;  a=%g, b=%g, k=%d, m=%d" % (
            args.variant, args.a, args.b, args.k, args.m)
        plot_study(y, ns, formula, study_params, tag)
        print(u"Графики сохранены в %s/task3_%s_*.png" % (OUT, tag))
    else:
        for n in ns:
            rr = interpolate(y, n)
            print("  n=%4d  ε_max=%.6e  ε_m=%.6e" % (n, rr["eps_max"], rr["eps_m"]))


if __name__ == "__main__":
    main()
