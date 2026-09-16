# -*- coding: utf-8 -*-
"""Общее ядро для заданий № 2 (нелинейные уравнения) и № 3 (интерполирование).

Содержит:
  * Dual  -- дуальные числа (forward-mode AD), дают ТОЧНУЮ производную f'(x)
             для метода касательных, без конечных разностей;
  * набор элементарных функций, работающих и с числами/массивами numpy,
    и с дуальными числами;
  * таблицы вариантов функций f(x) (задание № 2) и y(x) (задание № 3).
"""

import math
import numpy as np


# --------------------------------------------------------------------------
# Дуальные числа: x + eps*x', eps^2 = 0
# --------------------------------------------------------------------------
class Dual:
    __slots__ = ("a", "b")

    def __init__(self, a, b=0.0):
        self.a = float(a)   # значение
        self.b = float(b)   # производная

    def __repr__(self):
        return "Dual(%g, %g)" % (self.a, self.b)

    def __add__(self, o):
        o = o if isinstance(o, Dual) else Dual(o)
        return Dual(self.a + o.a, self.b + o.b)
    __radd__ = __add__

    def __neg__(self):
        return Dual(-self.a, -self.b)

    def __sub__(self, o):
        o = o if isinstance(o, Dual) else Dual(o)
        return Dual(self.a - o.a, self.b - o.b)

    def __rsub__(self, o):
        return Dual(o) - self

    def __mul__(self, o):
        o = o if isinstance(o, Dual) else Dual(o)
        return Dual(self.a * o.a, self.a * o.b + self.b * o.a)
    __rmul__ = __mul__

    def __truediv__(self, o):
        o = o if isinstance(o, Dual) else Dual(o)
        return Dual(self.a / o.a, (self.b * o.a - self.a * o.b) / (o.a * o.a))

    def __rtruediv__(self, o):
        return Dual(o) / self

    def __pow__(self, p):
        if isinstance(p, Dual):                      # u^v = exp(v*ln u)
            return exp(p * log(self))
        v = self.a ** p
        return Dual(v, p * (self.a ** (p - 1.0)) * self.b)

    def __rpow__(self, base):                        # c^u
        v = base ** self.a
        return Dual(v, v * math.log(base) * self.b)


def _dispatch(np_fn, val_fn, der_fn):
    """Одна функция и для float/ndarray, и для Dual."""
    def f(x):
        if isinstance(x, Dual):
            return Dual(val_fn(x.a), der_fn(x.a) * x.b)
        return np_fn(x)
    return f


sin  = _dispatch(np.sin,  math.sin,  math.cos)
cos  = _dispatch(np.cos,  math.cos,  lambda t: -math.sin(t))
tan  = _dispatch(np.tan,  math.tan,  lambda t: 1.0 / math.cos(t) ** 2)
exp  = _dispatch(np.exp,  math.exp,  math.exp)
log  = _dispatch(np.log,  math.log,  lambda t: 1.0 / t)
sinh = _dispatch(np.sinh, math.sinh, math.cosh)
cosh = _dispatch(np.cosh, math.cosh, math.sinh)
asin = _dispatch(np.arcsin, math.asin, lambda t: 1.0 / math.sqrt(1.0 - t * t))
acos = _dispatch(np.arccos, math.acos, lambda t: -1.0 / math.sqrt(1.0 - t * t))
atan = _dispatch(np.arctan, math.atan, lambda t: 1.0 / (1.0 + t * t))

PI = math.pi


def value(x):
    """Числовое значение (снимает дуальную оболочку)."""
    return x.a if isinstance(x, Dual) else x


def derivative(f, x):
    """f'(x) через дуальные числа -- точно, без конечных разностей."""
    return f(Dual(x, 1.0)).b


# --------------------------------------------------------------------------
# ЗАДАНИЕ № 2. Варианты функций f(x), корень ищется на [0, 1].
# Параметры l, k, j, m принимают значения от 1 до 4.
# sh = sinh, ch = cosh, tg = tan.
# --------------------------------------------------------------------------
F_VARIANTS = {
    1:  (r"$f(x)=-\cos^{k}(\pi x^{m}/2)+2x^{j}$",
         lambda x, k, m, j, l: -cos(PI * x ** m / 2) ** k + 2 * x ** j),
    2:  (r"$f(x)=\sin^{k}(\pi x^{m}/2)-(1-x)^{j}$",
         lambda x, k, m, j, l: sin(PI * x ** m / 2) ** k - (1 - x) ** j),
    3:  (r"$f(x)=\mathrm{sh}\,x^{j}-\cos^{k}(\pi x^{m})$",
         lambda x, k, m, j, l: sinh(x ** j) - cos(PI * x ** m) ** k),
    4:  (r"$f(x)=1-x^{j}-\mathrm{tg}^{k}(\pi x^{m}/4)$",
         lambda x, k, m, j, l: 1 - x ** j - tan(PI * x ** m / 4) ** k),
    5:  (r"$f(x)=(1-x)^{j}-\mathrm{tg}^{k}(\pi x^{m}/4)$",
         lambda x, k, m, j, l: (1 - x) ** j - tan(PI * x ** m / 4) ** k),
    6:  (r"$f(x)=(1-x)^{1/j}-\mathrm{tg}^{k}(\pi x^{m}/4)$",
         lambda x, k, m, j, l: (1 - x) ** (1.0 / j) - tan(PI * x ** m / 4) ** k),
    7:  (r"$f(x)=e^{-x^{j}}-\sin(\pi x^{m}/2)$",
         lambda x, k, m, j, l: exp(-(x ** j)) - sin(PI * x ** m / 2)),
    8:  (r"$f(x)=e^{-x^{j}}-x^{k}\sin(\pi x^{m}/2)$",
         lambda x, k, m, j, l: exp(-(x ** j)) - x ** k * sin(PI * x ** m / 2)),
    9:  (r"$f(x)=(1-x)^{m}-2x^{j}$",
         lambda x, k, m, j, l: (1 - x) ** m - 2 * x ** j),
    10: (r"$f(x)=(1-x)^{1/m}-2x^{1/j}$",
         lambda x, k, m, j, l: (1 - x) ** (1.0 / m) - 2 * x ** (1.0 / j)),
    11: (r"$f(x)=(1-x)^{j}\,\mathrm{ch}^{k}x^{m}-x^{l}$",
         lambda x, k, m, j, l: (1 - x) ** j * cosh(x ** m) ** k - x ** l),
    12: (r"$f(x)=(1-x)^{j}\cos^{k}(\pi x^{m}/2)-x^{l}$",
         lambda x, k, m, j, l: (1 - x) ** j * cos(PI * x ** m / 2) ** k - x ** l),
    13: (r"$f(x)=(1-x)^{j}-\mathrm{sh}^{k}x^{m}$",
         lambda x, k, m, j, l: (1 - x) ** j - sinh(x ** m) ** k),
    14: (r"$f(x)=(1-x)^{1/j}-\mathrm{sh}^{k}x^{m}$",
         lambda x, k, m, j, l: (1 - x) ** (1.0 / j) - sinh(x ** m) ** k),
    15: (r"$f(x)=(1-x)^{j}-\mathrm{sh}^{1/k}x^{m}$",
         lambda x, k, m, j, l: (1 - x) ** j - sinh(x ** m) ** (1.0 / k)),
    16: (r"$f(x)=(1-x)^{j}\,\mathrm{ch}^{k}x^{m}-x^{l}$",
         lambda x, k, m, j, l: (1 - x) ** j * cosh(x ** m) ** k - x ** l),
    17: (r"$f(x)=\arcsin x^{m}-(1-x^{j})^{k}$",
         lambda x, k, m, j, l: asin(x ** m) - (1 - x ** j) ** k),
    18: (r"$f(x)=k\cos(\pi x^{m})+x^{l}(1-x)$",
         lambda x, k, m, j, l: k * cos(PI * x ** m) + x ** l * (1 - x)),
    19: (r"$f(x)=\ln^{m}(1+x^{j})-(1-x)^{k}$",
         lambda x, k, m, j, l: log(1 + x ** j) ** m - (1 - x) ** k),
    20: (r"$f(x)=\ln^{m}(1+x^{j})-(1-x)^{k}\,\mathrm{ch}\,x^{l}$",
         lambda x, k, m, j, l: log(1 + x ** j) ** m - (1 - x) ** k * cosh(x ** l)),
}


def f_variant(number, k=1, m=1, j=1, l=1):
    """Возвращает (formula, f) для варианта задания № 2."""
    formula, body = F_VARIANTS[number]
    return formula, (lambda x: body(x, k, m, j, l))


# --------------------------------------------------------------------------
# ЗАДАНИЕ № 3. Варианты функций y(x) на [0, 1].
# a, b = 1..5;  k, m = 1..4;  n = 20..100.
# Знак "+-" в исходных формулах взят как "+".
# --------------------------------------------------------------------------
Y_VARIANTS = {
    1:  (r"$y(x)=\sin^{k}(\pi x^{m})$",       lambda x, a, b, k, m: sin(PI * x ** m) ** k),
    2:  (r"$y(x)=\cos^{k}(\pi x^{m})$",       lambda x, a, b, k, m: cos(PI * x ** m) ** k),
    3:  (r"$y(x)=\sin^{k}(\pi x^{1/m})$",     lambda x, a, b, k, m: sin(PI * x ** (1.0 / m)) ** k),
    4:  (r"$y(x)=\cos^{k}(\pi x^{1/m})$",     lambda x, a, b, k, m: cos(PI * x ** (1.0 / m)) ** k),
    5:  (r"$y(x)=\mathrm{tg}^{k}(\pi x^{m}/4)$",   lambda x, a, b, k, m: tan(PI * x ** m / 4) ** k),
    6:  (r"$y(x)=\mathrm{tg}^{k}(\pi x^{1/m}/4)$", lambda x, a, b, k, m: tan(PI * x ** (1.0 / m) / 4) ** k),
    7:  (r"$y(x)=ax^{4}+bx^{3}$",             lambda x, a, b, k, m: a * x ** 4 + b * x ** 3),
    8:  (r"$y(x)=(a+bx^{m})^{-k}$",           lambda x, a, b, k, m: (a + b * x ** m) ** (-k)),
    9:  (r"$y(x)=(a+bx^{m})^{-1/k}$",         lambda x, a, b, k, m: (a + b * x ** m) ** (-1.0 / k)),
    10: (r"$y(x)=(a+bx^{1/m})^{-k}$",         lambda x, a, b, k, m: (a + b * x ** (1.0 / m)) ** (-k)),
    11: (r"$y(x)=(a+bx^{1/m})^{-1/k}$",       lambda x, a, b, k, m: (a + b * x ** (1.0 / m)) ** (-1.0 / k)),
    12: (r"$y(x)=x^{k}/(a+bx^{m})$",          lambda x, a, b, k, m: x ** k / (a + b * x ** m)),
    13: (r"$y(x)=x^{k}/(a+bx)^{m}$",          lambda x, a, b, k, m: x ** k / (a + b * x) ** m),
    14: (r"$y(x)=x^{1/k}/(a+bx)^{m}$",        lambda x, a, b, k, m: x ** (1.0 / k) / (a + b * x) ** m),
    15: (r"$y(x)=x^{k}/(a+bx)^{1/m}$",        lambda x, a, b, k, m: x ** k / (a + b * x) ** (1.0 / m)),
    16: (r"$y(x)=x^{1/k}/(a+bx)^{1/m}$",      lambda x, a, b, k, m: x ** (1.0 / k) / (a + b * x) ** (1.0 / m)),
    17: (r"$y(x)=(a+x^{2})^{k}/(b+x^{4})^{m}$",
         lambda x, a, b, k, m: (a + x ** 2) ** k / (b + x ** 4) ** m),
    18: (r"$y(x)=(a+x^{2})^{1/k}/(b+x^{4})^{m}$",
         lambda x, a, b, k, m: (a + x ** 2) ** (1.0 / k) / (b + x ** 4) ** m),
    19: (r"$y(x)=(a+x^{2})^{k}/(b+x^{4})^{1/m}$",
         lambda x, a, b, k, m: (a + x ** 2) ** k / (b + x ** 4) ** (1.0 / m)),
    20: (r"$y(x)=(a+x^{2})^{1/k}/(b+x^{4})^{1/m}$",
         lambda x, a, b, k, m: (a + x ** 2) ** (1.0 / k) / (b + x ** 4) ** (1.0 / m)),
    21: (r"$y(x)=x^{k}/(a+bx^{m})$",          lambda x, a, b, k, m: x ** k / (a + b * x ** m)),
    22: (r"$y(x)=x^{1/k}/(a+bx^{m})$",        lambda x, a, b, k, m: x ** (1.0 / k) / (a + b * x ** m)),
    23: (r"$y(x)=x^{k}/(a+bx^{1/m})$",        lambda x, a, b, k, m: x ** k / (a + b * x ** (1.0 / m))),
    24: (r"$y(x)=x^{1/k}/(a+bx^{1/m})$",      lambda x, a, b, k, m: x ** (1.0 / k) / (a + b * x ** (1.0 / m))),
    25: (r"$y(x)=\ln^{k}(1+x^{m})$",          lambda x, a, b, k, m: log(1 + x ** m) ** k),
    26: (r"$y(x)=\ln^{1/k}(1+x^{m})$",        lambda x, a, b, k, m: log(1 + x ** m) ** (1.0 / k)),
    27: (r"$y(x)=\ln^{k}(1+x^{1/m})$",        lambda x, a, b, k, m: log(1 + x ** (1.0 / m)) ** k),
    28: (r"$y(x)=\ln^{1/k}(1+x^{1/m})$",      lambda x, a, b, k, m: log(1 + x ** (1.0 / m)) ** (1.0 / k)),
    29: (r"$y(x)=x^{k}e^{-2x^{2}}$",          lambda x, a, b, k, m: x ** k * exp(-2 * x ** 2)),
    30: (r"$y(x)=x^{1/k}e^{-2x^{2}}$",        lambda x, a, b, k, m: x ** (1.0 / k) * exp(-2 * x ** 2)),
    31: (r"$y(x)=x^{k}e^{-2x^{1/m}}$",        lambda x, a, b, k, m: x ** k * exp(-2 * x ** (1.0 / m))),
    32: (r"$y(x)=x^{1/k}e^{-2x^{1/m}}$",      lambda x, a, b, k, m: x ** (1.0 / k) * exp(-2 * x ** (1.0 / m))),
    33: (r"$y(x)=e^{-8(x-0.5)^{2}}$",         lambda x, a, b, k, m: exp(-8 * (x - 0.5) ** 2)),
    34: (r"$y(x)=x^{k}e^{-8(x-0.5)^{2}}$",    lambda x, a, b, k, m: x ** k * exp(-8 * (x - 0.5) ** 2)),
    35: (r"$y(x)=x^{1/k}e^{-8(x-0.5)^{2}}$",  lambda x, a, b, k, m: x ** (1.0 / k) * exp(-8 * (x - 0.5) ** 2)),
    36: (r"$y(x)=(a+bx^{m})^{1/k}$",          lambda x, a, b, k, m: (a + b * x ** m) ** (1.0 / k)),
    37: (r"$y(x)=(a+bx^{1/m})^{1/k}$",        lambda x, a, b, k, m: (a + b * x ** (1.0 / m)) ** (1.0 / k)),
    38: (r"$y(x)=(a+bx^{m})^{-k}$",           lambda x, a, b, k, m: (a + b * x ** m) ** (-k)),
    39: (r"$y(x)=(a+bx^{m})^{-1/k}$",         lambda x, a, b, k, m: (a + b * x ** m) ** (-1.0 / k)),
    40: (r"$y(x)=(a+bx^{1/m})^{-1/k}$",       lambda x, a, b, k, m: (a + b * x ** (1.0 / m)) ** (-1.0 / k)),
    41: (r"$y(x)=\arcsin[\cos^{k}(0.5\pi x^{m})]$",
         lambda x, a, b, k, m: asin(cos(0.5 * PI * x ** m) ** k)),
    42: (r"$y(x)=\arccos[\sin^{k}(0.5\pi x^{m})]$",
         lambda x, a, b, k, m: acos(sin(0.5 * PI * x ** m) ** k)),
    43: (r"$y(x)=\arcsin[\cos^{k}(0.5\pi x^{1/m})]$",
         lambda x, a, b, k, m: asin(cos(0.5 * PI * x ** (1.0 / m)) ** k)),
    44: (r"$y(x)=\arccos[\sin^{k}(0.5\pi x^{1/m})]$",
         lambda x, a, b, k, m: acos(sin(0.5 * PI * x ** (1.0 / m)) ** k)),
    45: (r"$y(x)=\mathrm{arctg}(a+bx^{m})$",   lambda x, a, b, k, m: atan(a + b * x ** m)),
    46: (r"$y(x)=\mathrm{arctg}(a+bx^{1/m})$", lambda x, a, b, k, m: atan(a + b * x ** (1.0 / m))),
    47: (r"$y(x)=\mathrm{sh}(a+bx)^{-m}$",     lambda x, a, b, k, m: sinh((a + b * x) ** (-m))),
    48: (r"$y(x)=\mathrm{sh}(a+bx)^{-1/m}$",   lambda x, a, b, k, m: sinh((a + b * x) ** (-1.0 / m))),
    49: (r"$y(x)=\mathrm{ch}(a+bx)^{-m}$",     lambda x, a, b, k, m: cosh((a + b * x) ** (-m))),
    50: (r"$y(x)=\mathrm{ch}(a+bx)^{-1/m}$",   lambda x, a, b, k, m: cosh((a + b * x) ** (-1.0 / m))),
    # Тестовая функция из методички: для неё eps_max и eps_m должны быть нулями.
    0:  (r"$y(x)=x^{2}$  (тест)",              lambda x, a, b, k, m: x ** 2),
}


def y_variant(number, a=1, b=1, k=1, m=1):
    """Возвращает (formula, y) для варианта задания № 3."""
    formula, body = Y_VARIANTS[number]
    return formula, (lambda x: body(x, a, b, k, m))
