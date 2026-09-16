# -*- coding: utf-8 -*-
"""Блок-схемы программ заданий № 2 и № 3 (рисуются кодом, без внешних редакторов).

    python3 flowcharts.py          -> out/flow_*.png
"""

import os

from nm_flow import Chart

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")


# ==========================================================================
# Задание № 2. Метод дихотомии
# ==========================================================================
def bisection_chart():
    ch = Chart(17.6, 19.6,
               title=u"Задание № 2. Блок-схема: метод дихотомии (половинного деления)",
               subtitle=u"соответствует функции bisection() в task2_nonlinear.py")
    cx = 6.0

    b1 = ch.terminator(cx, 1.6, u"Начало", num=1)
    b2 = ch.io(cx, 3.6, u"a, b, ε, i$_{max}$", w=4.6, num=2)
    b3 = ch.process(cx, 5.7, u"fa = f(a),   i = 0", w=5.2, num=3)
    cn = ch.connector(cx, 7.5)
    b4 = ch.process(cx, 9.4, u"x = (a + b) / 2\nfx = f(x)\ni = i + 1", w=5.2, h=2.2, num=4)
    fx = ch.predefined(11.9, 9.4, u"f(x)", w=2.6)
    b5 = ch.decision(cx, 12.6, u"|b − a| > 2ε   и\n|fx| > ε   и   i < i$_{max}$",
                     w=6.6, h=2.6, num=5)
    b6 = ch.decision(cx, 15.7, u"fa · fx > 0", w=4.8, h=2.0, num=6)
    b7 = ch.process(3.3, 18.2, u"a = x\nfa = fx", w=3.8, h=1.5, num=7)
    b8 = ch.process(10.1, 18.2, u"b = x", w=3.2, h=1.5, num=8)
    b9 = ch.io(13.1, 12.6, u"x = (a + b) / 2,   i", w=5.2, num=9)
    b10 = ch.terminator(13.1, 15.1, u"Конец", num=10)

    ch.arrow(b1.s, b2.n)
    ch.arrow(b2.s, b3.n)
    ch.arrow(b3.s, cn.n)
    ch.arrow(cn.s, b4.n)
    ch.link(b4.e, fx.w_)
    ch.arrow(b4.s, b5.n)
    ch.arrow(b5.e, b9.w_, label=u"Нет", lpos=0.5, loff=(0.0, -0.45))
    ch.arrow(b9.s, b10.n)
    ch.arrow(b5.s, b6.n, label=u"Да", loff=(0.55, 0.0))
    ch.route([b6.w_, (b7.x, b6.y), b7.n], label=u"Да", loff=(0.0, 0.5))
    ch.route([b6.e, (b8.x, b6.y), b8.n], label=u"Нет", loff=(0.0, -0.45))
    # возвраты в начало цикла
    ch.route([b7.w_, (0.4, b7.y), (0.4, cn.y), cn.w_])
    ch.route([b8.e, (16.9, b8.y), (16.9, cn.y), cn.e])
    ch.save(os.path.join(OUT, "flow_task2_bisection.png"))


# ==========================================================================
# Задание № 2. Методы касательных и секущих (одинаковая структура)
# ==========================================================================
def iterative_chart(kind):
    if kind == "newton":
        title = u"Задание № 2. Блок-схема: метод касательных (Ньютона)"
        sub = u"соответствует функции newton() в task2_nonlinear.py"
        init = u"i = 0\nx$_i$ = x$_0$"
        body = (u"f$_i$ = f(x$_i$),   f'$_i$ = f'(x$_i$)\n"
                u"x$_{i+1}$ = x$_i$ − f$_i$ / f'$_i$\n"
                u"ξ$_i$ = |x$_{i+1}$ − x$_i$|")
        pre = u"f(x), f'(x)"
        step = u"x$_i$ = x$_{i+1}$\ni = i + 1"
        name = "flow_task2_newton.png"
        bw = 7.0
    else:
        title = u"Задание № 2. Блок-схема: метод секущих"
        sub = u"соответствует функции secant() в task2_nonlinear.py"
        init = u"i = 1\nx$_{i-1}$ = x$_0$,   x$_i$ = x$_1$\nf$_{i-1}$ = f(x$_{i-1}$)"
        body = (u"f$_i$ = f(x$_i$)\n"
                u"x$_{i+1}$ = x$_i$ − (x$_i$ − x$_{i-1}$) f$_i$ / (f$_i$ − f$_{i-1}$)\n"
                u"ξ$_i$ = |x$_{i+1}$ − x$_i$|")
        pre = u"f(x)"
        step = u"x$_{i-1}$ = x$_i$,   f$_{i-1}$ = f$_i$\nx$_i$ = x$_{i+1}$,   i = i + 1"
        name = "flow_task2_secant.png"
        bw = 8.2

    ch = Chart(18.4, 20.4, title=title, subtitle=sub)
    lx, rx = 4.2, 12.4

    b1 = ch.terminator(lx, 1.8, u"Начало", num=1)
    b2 = ch.io(lx, 3.9, u"Начальные данные\nx$_0$, ε, i$_{max}$", w=5.2, h=1.8, num=2)
    b3 = ch.process(lx, 6.4, init, w=5.4, h=2.0, num=3)
    fx = ch.predefined(10.4, 6.4, pre, w=3.4)
    cn = ch.connector(lx, 8.6)
    b4 = ch.decision(lx, 10.9, u"i > i$_{max}$", w=4.8, h=2.2, num=4)
    b5 = ch.process(rx, 10.9, body, w=bw, h=3.0, num=5, fs=9.5)
    b6 = ch.decision(rx, 14.5, u"ξ$_i$ < ε    или\n|f(x$_{i+1}$)| < ε", w=5.8, h=2.4, num=6)
    b7 = ch.process(rx, 17.6, step, w=6.0, h=2.0, num=7)
    cn2 = ch.connector(lx, 14.5)
    b8 = ch.io(lx, 16.9, u"График f(x)\nРезультаты: x*, i", w=5.6, h=1.8, num=8)
    b9 = ch.terminator(lx, 19.3, u"Конец", num=9)

    ch.arrow(b1.s, b2.n)
    ch.arrow(b2.s, b3.n)
    ch.link(b3.e, fx.w_)
    ch.route([fx.s, (fx.x, ch.Y(9.0)), (b5.x, ch.Y(9.0)), b5.n])
    ch.arrow(b3.s, cn.n)
    ch.arrow(cn.s, b4.n)
    ch.arrow(b4.e, b5.w_, label=u"Нет", loff=(0.0, -0.45))
    ch.arrow(b4.s, cn2.n, label=u"Да", loff=(0.55, 0.0))
    ch.arrow(b5.s, b6.n)
    ch.arrow(b6.w_, cn2.e, label=u"Да", loff=(0.0, -0.45))
    ch.arrow(b6.s, b7.n, label=u"Нет", loff=(0.6, 0.0))
    ch.route([b7.e, (17.6, b7.y), (17.6, cn.y), cn.e])
    ch.arrow(cn2.s, b8.n)
    ch.arrow(b8.s, b9.n)
    ch.save(os.path.join(OUT, name))


# ==========================================================================
# Задание № 3. Интерполяция многочленом Ньютона
# ==========================================================================
def interpolation_chart():
    ch = Chart(18.2, 24.6,
               title=u"Задание № 3. Блок-схема программы интерполирования",
               subtitle=u"соответствует функции interpolate() в task3_interpolation.py")
    lx, rx, mid = 4.2, 13.5, 8.0

    b1 = ch.terminator(lx, 2.0, u"Начало", num=1)
    b2 = ch.io(lx, 4.2, u"Начальные данные:\nn, вариант y(x)", w=5.6, h=1.8, num=2)
    b3 = ch.process(lx, 6.4, u"h = 1 / n", w=4.0, h=1.2, num=3)
    b4 = ch.loop_start(lx, 8.5, u"Цикл\nпо j = 0, n", w=5.0, h=1.8, num=4)
    b5 = ch.process(lx, 10.9, u"x$_j$ = j · h\ny$_j$ = y(x$_j$)", w=4.8, h=1.8, num=5)
    b6 = ch.loop_end(lx, 13.1, u"Конец цикла\nпо j", w=5.0, h=1.8, num=6)
    b7 = ch.loop_start(lx, 15.5, u"Цикл\nпо j = 0, n−1", w=5.4, h=1.8, num=7)
    b8 = ch.process(lx, 18.0, u"Δy$_j$ = y$_{j+1}$ − y$_j$\nf[x$_j$, x$_{j+1}$] = Δy$_j$ / h",
                    w=6.4, h=1.8, num=8)
    b9 = ch.loop_end(lx, 20.4, u"Конец цикла\nпо j", w=5.0, h=1.8, num=9)

    b10 = ch.loop_start(rx, 2.4, u"Цикл\nпо j = 0, n−2", w=5.4, h=1.8, num=10)
    b11 = ch.process(rx, 4.9, u"f[x$_j$, x$_{j+1}$, x$_{j+2}$] =\n= (Δy$_{j+1}$ − Δy$_j$) / (2h²)",
                     w=7.0, h=1.8, num=11)
    b12 = ch.loop_end(rx, 7.3, u"Конец цикла\nпо j", w=5.0, h=1.8, num=12)
    b13 = ch.loop_start(rx, 9.7, u"Цикл\nпо j = 0, n−1", w=5.4, h=1.8, num=13)
    b14 = ch.process(rx, 12.8, u"i = min(j, n−2)\nx$_{j+1/2}$ = x$_j$ + h/2\n"
                               u"P(x$_{j+1/2}$) — многочлен Ньютона\n"
                               u"ε$_{j+1/2}$ = P(x$_{j+1/2}$) − y(x$_{j+1/2}$)",
                     w=7.6, h=3.2, num=14, fs=9.5)
    b15 = ch.loop_end(rx, 15.8, u"Конец цикла\nпо j", w=5.0, h=1.8, num=15)
    b16 = ch.process(rx, 18.3, u"ε$_{max}$ = max |ε$_{j+1/2}$|\n"
                               u"⟨ε²⟩ = Σ ε²$_{j+1/2}$ / n,   ε$_m$ = √⟨ε²⟩",
                     w=7.6, h=1.8, num=16)
    b17 = ch.io(rx, 20.6, u"Графики, таблица ε,\nε$_{max}$, ε$_m$", w=5.6, h=1.8, num=17)
    b18 = ch.terminator(rx, 23.3, u"Конец", num=18)

    for a, b in ((b1, b2), (b2, b3), (b3, b4), (b4, b5), (b5, b6), (b6, b7),
                 (b7, b8), (b8, b9)):
        ch.arrow(a.s, b.n)
    ch.route([b9.s, (lx, ch.Y(21.9)), (mid, ch.Y(21.9)), (mid, ch.Y(1.0)),
              (rx, ch.Y(1.0)), b10.n])
    for a, b in ((b10, b11), (b11, b12), (b12, b13), (b13, b14), (b14, b15),
                 (b15, b16), (b16, b17), (b17, b18)):
        ch.arrow(a.s, b.n)
    ch.save(os.path.join(OUT, "flow_task3_interpolation.png"))


if __name__ == "__main__":
    bisection_chart()
    iterative_chart("newton")
    iterative_chart("secant")
    interpolation_chart()
    print(u"Блок-схемы сохранены в %s/flow_*.png" % OUT)
