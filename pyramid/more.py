def SUMSQ(n):
    s = 0
    while n != 0:
        s = ADD(s, SQUARE(n))
        n = DEC(n)
    return s
def LPRIMES(x):
    n = LEN(0)
    c = 0
    i = 1
    while not LT(n, i):
        if ISPRIME(GET(i)): c = INC(c)
        i = INC(i)
    return c
