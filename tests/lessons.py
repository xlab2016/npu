"""Навыки, которых нет в микрокоде. Учитель показывает их один раз."""
def TRIB(n):
    a, b, c = 0, 0, 1
    for i in range(n):
        a, b, c = b, c, a + b + c
    return a
def SUMDIV(n):
    s = 0
    for d in range(1, n + 1):
        if n % d == 0:
            s = s + d
    return s
def PERFECT(n):
    return SUMDIV(n) == 2 * n
def REVDIG(n):
    r = 0
    while n > 0:
        r = r * 10 + n % 10
        n = n // 10
    return r
def PALIN(n):
    return REVDIG(n) == n
def DIVCOUNT(n):
    c = 0
    d = 1
    while d * d <= n:
        if n % d == 0:
            c = c + 1
            if d * d != n:
                c = c + 1
        d = d + 1
    return c
def CATALAN(n):
    return NCR(2 * n, n) / (n + 1)
def COPRIME(a, b):
    return GCD(a, b) == 1
def PRIMEPI(n):
    c = 0
    for k in range(2, n + 1):
        if PRIME(k):
            c = c + 1
    return c
def SUMSQ(n):
    return n * (n + 1) * (2 * n + 1) / 6
def BINOMSUM(n):
    s = 0
    for k in range(0, n + 1):
        s = s + NCR(n, k)
    return s
