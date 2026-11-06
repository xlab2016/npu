"""Уроки циклов и списков. Цикл получает тело как адрес подпрограммы f."""
def ALL(f, lo, hi):
    i = lo
    while i <= hi:
        if CALLF(f, i) == 0:
            return 0
        i = i + 1
    return 1
def ANY(f, lo, hi):
    i = lo
    while i <= hi:
        if CALLF(f, i) != 0:
            return 1
        i = i + 1
    return 0
def SUM(f, lo, hi):
    i = lo
    s = 0
    while i <= hi:
        s = s + CALLF(f, i)
        i = i + 1
    return s
def PROD(f, lo, hi):
    i = lo
    s = 1
    while i <= hi:
        s = s * CALLF(f, i)
        i = i + 1
    return s
def COUNT(f, lo, hi):
    i = lo
    s = 0
    while i <= hi:
        if CALLF(f, i) != 0:
            s = s + 1
        i = i + 1
    return s
def FIRST(f, lo, hi):
    i = lo
    while i <= hi:
        if CALLF(f, i) != 0:
            return i
        i = i + 1
    return 0
def FOLD(f, lo, hi, s):
    i = lo
    while i <= hi:
        s = CALLF(f, s, i)
        i = i + 1
    return s
def ITER(c, g, x):
    while CALLF(c, x) != 0:
        x = CALLF(g, x)
    return x
def AT(i):
    return PEEK(4096 + i)
def LEN(x):
    return PEEK(4096)
