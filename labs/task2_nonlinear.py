# -*- coding: utf-8 -*-
"""ЗАДАНИЕ № 2. РЕШЕНИЕ НЕЛИНЕЙНЫХ УРАВНЕНИЙ f(x) = 0 на отрезке [0, 1].

Реализованы три метода:
  * дихотомия (половинное деление) -- безусловно сходящийся;
  * касательных (Ньютона)          -- условно сходящийся, f'(x) точная (дуальные числа);
  * секущих                        -- условно сходящийся, двухшаговый.

Запуск:
    python3 task2_nonlinear.py                       # вариант 1, k=m=j=l=1
    python3 task2_nonlinear.py -v 7 -k 2 -m 1 -j 2   # свой вариант и параметры
    python3 task2_nonlinear.py --list                # список всех вариантов
"""

import argparse
import math
import os

import numpy as np

import nm_core as core
import nm_style as st
from nm_style import SERIES, MARKERS, INK, INK2, MUTED, ZERO

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")


# ==========================================================================
#                              МЕТОДЫ
# ==========================================================================
def bisection(f, a, b, eps=1e-6, imax=100):
    """Метод дихотомии. На каждой итерации вычисляется лишь одно новое f(x)."""
    fa, fb = f(a), f(b)
    if fa * fb > 0:
        raise ValueError("на концах [%g, %g] функция одного знака" % (a, b))
    hist = []                       # (i, x, f(x), длина отрезка)
    x = 0.5 * (a + b)
    for i in range(1, imax + 1):
        x = 0.5 * (a + b)
        fx = f(x)
        hist.append((i, x, fx, b - a))
        if abs(fx) < eps or (b - a) < 2 * eps:
            break
        if fa * fx < 0:
            b, fb = x, fx
        else:
            a, fa = x, fx
    return x, hist


def newton(f, x0, eps=1e-6, imax=30):
    """Метод касательных: x_{n+1} = x_n - f(x_n)/f'(x_n)."""
    hist = []                       # (i, x, f(x), |x_n - x_{n-1}|)
    x = float(x0)
    hist.append((0, x, f(x), float("nan")))
    for i in range(1, imax + 1):
        fx = f(x)
        d = core.derivative(f, x)
        if d == 0.0 or not math.isfinite(d):
            raise ValueError("f'(x) = 0 на итерации %d" % i)
        xn = x - fx / d
        hist.append((i, xn, f(xn), abs(xn - x)))
        if abs(xn - x) < eps or abs(f(xn)) < eps:
            x = xn
            break
        x = xn
    return x, hist


def secant(f, x0, x1, eps=1e-6, imax=30):
    """Метод секущих: производная заменена первой разделённой разностью."""
    hist = []
    x_prev, x = float(x0), float(x1)
    f_prev, fx = f(x_prev), f(x)
    hist.append((0, x_prev, f_prev, float("nan")))
    hist.append((1, x, fx, abs(x - x_prev)))
    for i in range(2, imax + 1):
        if fx == f_prev:
            break
        xn = x - fx * (x - x_prev) / (fx - f_prev)
        fn = f(xn)                                  # одно новое значение f за итерацию
        hist.append((i, xn, fn, abs(xn - x)))
        x_prev, f_prev = x, fx
        x, fx = xn, fn
        if abs(x - x_prev) < eps or abs(fx) < eps:
            break
    return x, hist


def find_bracket(f, a=0.0, b=1.0, parts=20):
    """Отделение корня: сначала пробуем весь отрезок, затем дробим его."""
    try:
        if float(f(a)) * float(f(b)) <= 0:
            return a, b
    except Exception:
        pass
    xs = np.linspace(a, b, parts + 1)
    vals = []
    for x in xs:
        try:
            vals.append(float(f(x)))
        except Exception:
            vals.append(float("nan"))
    for i in range(parts):
        u, v = vals[i], vals[i + 1]
        if np.isfinite(u) and np.isfinite(v) and u * v <= 0:
            return xs[i], xs[i + 1]
    return None


# ==========================================================================
#                              ТАБЛИЦЫ
# ==========================================================================
def print_table(title, hist, col4):
    print("\n" + title)
    print("  %3s | %-18s | %-14s | %-12s" % ("i", "x_i", "f(x_i)", col4))
    print("  " + "-" * 56)
    for i, x, fx, d in hist:
        ds = "   --   " if (isinstance(d, float) and math.isnan(d)) else "%.3e" % d
        print("  %3d | %18.12f | %14.3e | %12s" % (i, x, fx, ds))


# ==========================================================================
#                              ГРАФИКИ
# ==========================================================================
def plot_function(f, formula, params, root, tag):
    import matplotlib.pyplot as plt
    x = np.linspace(0, 1, 800)
    y = np.array([float(f(t)) for t in x])

    fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.axhline(0, color=ZERO, lw=1.0, ls="--", alpha=0.7)
    ax.plot(x, y, color=SERIES[0])
    ax.plot([root], [0], "o", ms=9, color=SERIES[1],
            markeredgecolor=st.SURFACE, markeredgewidth=2, zorder=5)
    ax.annotate("корень  x* = %.6f" % root, xy=(root, 0),
                xytext=(14, 26), textcoords="offset points",
                color=INK, fontsize=10,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=1))
    st.finish(ax, u"Задание № 2. График функции f(x) на [0, 1]", "x", "f(x)",
              subtitle=formula + u"    " + params)
    fig.savefig(os.path.join(OUT, "task2_%s_function.png" % tag))
    plt.close(fig)


def plot_convergence(hists, root, eps, tag, params):
    """|x_i - x*| по итерациям, логарифмическая ось."""
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    floor = 1e-17
    # Прямые подписи кривых разнесены по вертикали, чтобы не сливались.
    voff = [0, 16, -16, 16]
    for idx, (name, hist) in enumerate(hists):
        it = [h[0] for h in hist]
        err = [max(abs(h[1] - root), floor) for h in hist]
        ax.semilogy(it, err, color=SERIES[idx], marker=MARKERS[idx],
                    markeredgecolor=st.SURFACE, markeredgewidth=1.2, label=name)
        ax.annotate(name, xy=(it[-1], err[-1]), xytext=(9, voff[idx]),
                    textcoords="offset points", color=INK2, fontsize=10, va="center")
    ax.axhline(eps, color=MUTED, lw=1.0, ls=":")
    ax.text(0.995, eps, u" ε = %g" % eps, transform=ax.get_yaxis_transform(),
            color=MUTED, fontsize=9, ha="right", va="bottom")
    xmax = max(h[0] for _, hist in hists for h in hist)
    ax.set_xlim(-0.6, xmax * 1.22 + 1)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.legend(loc="upper right")
    st.finish(ax, u"Скорость сходимости методов",
              u"номер итерации i", u"|x_i − x*|", subtitle=params)
    fig.savefig(os.path.join(OUT, "task2_%s_convergence.png" % tag))
    plt.close(fig)


def plot_geometry(f, a, b, x0, eps, root, tag):
    """Геометрия трёх методов: дихотомия, касательные, секущие."""
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 3, figsize=(14.5, 4.6))

    def curve(ax, lo, hi):
        t = np.linspace(lo, hi, 600)
        v = np.array([float(f(s_)) for s_ in t])
        ax.axhline(0, color=ZERO, lw=1.0, ls="--", alpha=0.7)
        ax.plot(t, v, color=SERIES[0], zorder=2, label="f(x)")
        return t, v

    # --- 1. дихотомия: последовательность вложенных отрезков
    ax = axes[0]
    t, v = curve(ax, a, b)
    aa, bb, fa = a, b, f(a)
    lo, hi = float(np.nanmin(v)), float(np.nanmax(v))
    step = (hi - lo) * 0.085
    for i in range(6):
        xm = 0.5 * (aa + bb)
        lvl = lo - step * (i + 0.8)
        ax.plot([aa, bb], [lvl, lvl], color=SERIES[1], lw=2.5,
                solid_capstyle="butt", zorder=3)
        ax.plot([xm], [lvl], "|", color=INK, ms=11, mew=1.6, zorder=4)
        ax.annotate("%d" % (i + 1), xy=(bb, lvl), xytext=(7, 0),
                    textcoords="offset points", color=MUTED, fontsize=9,
                    ha="left", va="center")
        fm = f(xm)
        if fa * fm < 0:
            bb = xm
        else:
            aa, fa = xm, fm
    ax.set_ylim(lo - step * 7.2, hi + step)
    ax.text(a, lo - step * 7.0, u"отрезки [a, b] по итерациям (| -- середина)",
            color=MUTED, fontsize=9, va="bottom")
    st.finish(ax, u"Дихотомия: отрезок делится пополам", "x", "f(x)")

    # --- окно «зума» вокруг корня и начального приближения
    zlo = min(x0, root) - 0.12 * abs(b - a)
    zhi = max(x0, root) + 0.18 * abs(b - a)
    zlo, zhi = max(a, zlo), min(b, zhi)

    # --- 2. касательные (метод Ньютона)
    ax = axes[1]
    curve(ax, zlo, zhi)
    x = float(x0)
    for i in range(3):
        fx, d = float(f(x)), core.derivative(f, x)
        if d == 0:
            break
        xn = x - fx / d
        ax.plot([x, xn], [fx, 0.0], color=SERIES[1], lw=1.6, zorder=3)
        ax.plot([x, x], [0.0, fx], color=MUTED, lw=0.9, ls=":", zorder=3)
        ax.plot([x], [fx], "o", ms=6, color=SERIES[1],
                markeredgecolor=st.SURFACE, markeredgewidth=1.4, zorder=4)
        ax.annotate("x%d" % i, xy=(x, 0), xytext=(0, 10 + 16 * i), ha="center",
                    textcoords="offset points", color=INK2, fontsize=9)
        x = xn
    ax.plot([root], [0], "o", ms=8, color=SERIES[0],
            markeredgecolor=st.SURFACE, markeredgewidth=1.6, zorder=5)
    st.finish(ax, u"Касательные: x₁ = x₀ − f(x₀)/f′(x₀)", "x", "f(x)")

    # --- 3. секущие
    ax = axes[2]
    curve(ax, zlo, zhi)
    p, q = float(x0), float(x0) + 50 * eps
    fp, fq = float(f(p)), float(f(q))
    for i in range(3):
        if fq == fp:
            break
        xn = q - fq * (q - p) / (fq - fp)
        ax.plot([p, xn], [fp, 0.0], color=SERIES[2], lw=1.6, zorder=3)
        ax.plot([p], [fp], "o", ms=6, color=SERIES[2],
                markeredgecolor=st.SURFACE, markeredgewidth=1.4, zorder=4)
        ax.annotate("x%d" % (i + 2), xy=(xn, 0), xytext=(0, 10 + 16 * i),
                    ha="center", textcoords="offset points", color=INK2, fontsize=9)
        p, fp = q, fq
        q, fq = xn, float(f(xn))
    ax.plot([root], [0], "o", ms=8, color=SERIES[0],
            markeredgecolor=st.SURFACE, markeredgewidth=1.6, zorder=5)
    st.finish(ax, u"Секущие: касательная заменена хордой (x₀≈x₁)", "x", "f(x)")

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "task2_%s_geometry.png" % tag))
    plt.close(fig)


def plot_iters_vs_eps(f, a, b, x0, tag, params):
    """Сколько итераций нужно каждому методу при разной точности."""
    import matplotlib.pyplot as plt
    epss = [10.0 ** (-p) for p in range(3, 13)]
    data = {u"дихотомия": [], u"касательных": [], u"секущих": []}
    for e in epss:
        try:
            data[u"дихотомия"].append(len(bisection(f, a, b, e, 200)[1]))
        except Exception:
            data[u"дихотомия"].append(np.nan)
        try:
            data[u"касательных"].append(len(newton(f, x0, e, 60)[1]) - 1)
        except Exception:
            data[u"касательных"].append(np.nan)
        try:
            data[u"секущих"].append(len(secant(f, x0, x0 + 50 * e, e, 60)[1]) - 1)
        except Exception:
            data[u"секущих"].append(np.nan)

    fig, ax = plt.subplots(figsize=(8, 4.8))
    for idx, (name, vals) in enumerate(data.items()):
        ax.semilogx(epss, vals, color=SERIES[idx], marker=MARKERS[idx],
                    markeredgecolor=st.SURFACE, markeredgewidth=1.2, label=name)
        ax.annotate("%s: %d" % (name, vals[-1]), xy=(epss[-1], vals[-1]),
                    xytext=(-6, 10 if idx != 2 else -18), textcoords="offset points",
                    color=INK2, fontsize=10, ha="right")
    ax.invert_xaxis()
    ax.legend(loc="upper left")
    st.finish(ax, u"Число итераций в зависимости от точности ε",
              u"требуемая точность ε", u"число итераций", subtitle=params)
    fig.savefig(os.path.join(OUT, "task2_%s_iters_vs_eps.png" % tag))
    plt.close(fig)


# ==========================================================================
#                              ОСНОВНАЯ ПРОГРАММА
# ==========================================================================
def main():
    ap = argparse.ArgumentParser(description=u"Задание № 2: решение нелинейных уравнений")
    ap.add_argument("-v", "--variant", type=int, default=1, help=u"номер варианта 1..20")
    ap.add_argument("-k", type=int, default=1)
    ap.add_argument("-m", type=int, default=1)
    ap.add_argument("-j", type=int, default=1)
    ap.add_argument("-l", type=int, default=1)
    ap.add_argument("-e", "--eps", type=float, default=1e-6, help=u"точность (1e-5..1e-7)")
    ap.add_argument("-x0", "--x0", type=float, default=0.2, help=u"начальное приближение")
    ap.add_argument("--imax", type=int, default=30, help=u"максимум итераций")
    ap.add_argument("--no-plots", action="store_true")
    ap.add_argument("--list", action="store_true", help=u"показать список вариантов")
    args = ap.parse_args()

    if args.list:
        print(u"Варианты функций f(x) (задание № 2):")
        for n in sorted(core.F_VARIANTS):
            print("  %2d) %s" % (n, core.F_VARIANTS[n][0].replace("$", "")))
        return

    formula, f = core.f_variant(args.variant, k=args.k, m=args.m, j=args.j, l=args.l)
    params = u"вариант %d;  k=%d, m=%d, j=%d, l=%d;  ε=%g;  x₀=%g" % (
        args.variant, args.k, args.m, args.j, args.l, args.eps, args.x0)

    print("=" * 72)
    print(u"ЗАДАНИЕ № 2. РЕШЕНИЕ НЕЛИНЕЙНЫХ УРАВНЕНИЙ")
    print("=" * 72)
    print(u"Функция:   %s" % formula.replace("$", ""))
    print(u"Параметры: %s" % params)
    print(u"f(0) = %+.6f,   f(1) = %+.6f" % (float(f(0.0)), float(f(1.0))))

    # --- отделение корня
    br = find_bracket(f, 0.0, 1.0)
    if br is None:
        print(u"\nНа [0,1] нет смены знака -- корень не отделён. "
              u"Смените вариант или параметры k, m, j, l.")
        return
    a, b = br
    print(u"Отрезок со сменой знака: [%.4f, %.4f]" % (a, b))

    # --- три метода
    x_bis, h_bis = bisection(f, a, b, args.eps, imax=200)
    print_table(u"МЕТОД ДИХОТОМИИ (половинного деления)", h_bis, "b - a")

    try:
        x_new, h_new = newton(f, args.x0, args.eps, args.imax)
        ok_new = True
    except Exception as exc:
        x_new, h_new, ok_new = float("nan"), [], False
        print(u"\nМЕТОД КАСАТЕЛЬНЫХ: не сошёлся (%s)" % exc)
    if ok_new:
        print_table(u"МЕТОД КАСАТЕЛЬНЫХ (Ньютона)", h_new, "|x_i - x_i-1|")

    x1 = args.x0 + 50 * args.eps            # "разгонная" точка: x0 + (10..100)*eps
    x_sec, h_sec = secant(f, args.x0, x1, args.eps, args.imax)
    print_table(u"МЕТОД СЕКУЩИХ", h_sec, "|x_i - x_i-1|")

    # --- эталонный корень (для оценки погрешностей на графике)
    x_ref = bisection(f, a, b, 1e-15, imax=200)[0]

    print("\n" + "-" * 72)
    print(u"РЕЗУЛЬТАТЫ (ε = %g)" % args.eps)
    print("  %-22s | %-16s | %-10s | %s" % (u"метод", u"корень x*", u"итераций", u"|f(x*)|"))
    print("  " + "-" * 66)
    rows = [(u"дихотомия", x_bis, len(h_bis))]
    if ok_new:
        rows.append((u"касательных", x_new, len(h_new) - 1))
    rows.append((u"секущих", x_sec, len(h_sec) - 1))
    for name, xr, it in rows:
        print("  %-22s | %16.12f | %10d | %.2e" % (name, xr, it, abs(float(f(xr)))))
    print(u"\n  Уточнённый корень (ε=1e-15): x* = %.14f" % x_ref)
    print(u"  Вывод: дихотомия сходится линейно (отрезок делится пополам), "
          u"методу касательных\n  (сходимость 2-го порядка) и секущих (порядок ≈1.618) "
          u"хватает единиц итераций.")

    # --- графики
    if not args.no_plots:
        tag = "v%d" % args.variant
        st.apply_style()
        plot_function(f, formula, params, x_ref, tag)
        hists = [(u"дихотомия", h_bis)]
        if ok_new:
            hists.append((u"касательных", h_new))
        hists.append((u"секущих", h_sec))
        plot_convergence(hists, x_ref, args.eps, tag, params)
        plot_geometry(f, a, b, args.x0, args.eps, x_ref, tag)
        plot_iters_vs_eps(f, a, b, args.x0, tag, params)
        print(u"\nГрафики сохранены в %s/task2_%s_*.png" % (OUT, tag))


if __name__ == "__main__":
    main()
