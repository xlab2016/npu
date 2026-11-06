"""Уроки учителя снизу вверх. Строчные _имена это настоящие инструкции CPU, ЗАГЛАВНЫЕ это уже выученные навыки."""
L = {}
def lv(n):
    def d(f): L.setdefault(n, []).append(f); return f
    return d
@lv(0)
def AND(a, b): return _and(a, b)
@lv(0)
def OR(a, b): return _or(a, b)
@lv(0)
def XOR(a, b): return _xor(a, b)
@lv(0)
def ADD(a, b): return _add(a, b)
@lv(0)
def SUB(a, b): return _sub(a, b)
@lv(0)
def SHL(a): return _shl(a)
@lv(0)
def SHR(a): return _shr(a)
@lv(0)
def LT(a, b): return _lt(a, b)
@lv(0)
def EQ(a, b): return _eq(a, b)
@lv(0)
def GET(i): return _load(i)
@lv(0)
def LEN(x):
    z = 0
    return _load(z)
@lv(1)
def INC(a): return ADD(a, 1)
@lv(1)
def DEC(a): return SUB(a, 1)
@lv(1)
def MIN(a, b):
    if LT(b, a): return b
    return a
@lv(1)
def MAX(a, b):
    if LT(a, b): return b
    return a
@lv(1)
def MUL(a, b):
    r = 0
    while b != 0:
        if odd(b): r = ADD(r, a)
        a = SHL(a)
        b = SHR(b)
    return r
@lv(1)
def UMOD(a, b):
    if b == 0: _throw(0)
    d = b
    while LT(0, SHL(d)) and not LT(a, SHL(d)):
        d = SHL(d)
    while not LT(a, b):
        if not LT(a, d): a = SUB(a, d)
        d = SHR(d)
    return a
@lv(1)
def UDIV(a, b):
    if b == 0: _throw(0)
    q = 0
    d = b
    p = 1
    while LT(0, SHL(d)) and not LT(a, SHL(d)):
        d = SHL(d)
        p = SHL(p)
    while p != 0:
        if not LT(a, d):
            a = SUB(a, d)
            q = ADD(q, p)
        d = SHR(d)
        p = SHR(p)
    return q
@lv(1)
def NEG(a): return SUB(0, a)
@lv(2)
def ABS(a):
    if LT(a, 0): return NEG(a)
    return a
@lv(3)
def DIV(a, b):
    q = UDIV(ABS(a), ABS(b))
    if LT(a, 0):
        if not LT(b, 0): return NEG(q)
        return q
    if LT(b, 0): return NEG(q)
    return q
@lv(3)
def MOD(a, b):
    r = UMOD(ABS(a), ABS(b))
    if LT(a, 0): return NEG(r)
    return r
@lv(2)
def SQUARE(a): return MUL(a, a)
@lv(2)
def POW(a, b):
    r = 1
    while b != 0:
        if odd(b): r = MUL(r, a)
        a = MUL(a, a)
        b = SHR(b)
    return r
@lv(2)
def GCD(a, b):
    while b != 0:
        t = UMOD(a, b)
        a = b
        b = t
    return a
@lv(2)
def FACT(n):
    r = 1
    while n != 0:
        r = MUL(r, n)
        n = DEC(n)
    return r
@lv(2)
def FIB(n):
    a = 0
    b = 1
    while n != 0:
        t = ADD(a, b)
        a = b
        b = t
        n = DEC(n)
    return a
@lv(2)
def DIGSUM(n):
    s = 0
    while n != 0:
        s = ADD(s, UMOD(n, 10))
        n = UDIV(n, 10)
    return s
@lv(2)
def ISQRT(n):
    r = 0
    while not LT(n, SQUARE(INC(r))):
        r = INC(r)
    return r
@lv(2)
def COLLATZ(n):
    c = 0
    while not EQ(n, 1):
        if odd(n): n = INC(MUL(n, 3))
        else: n = SHR(n)
        c = INC(c)
    return c
@lv(3)
def LCM(a, b): return MUL(UDIV(a, GCD(a, b)), b)
@lv(3)
def ISPRIME(n):
    if LT(n, 2): return 0
    d = 2
    while not LT(n, SQUARE(d)):
        if UMOD(n, d) == 0: return 0
        d = INC(d)
    return 1
@lv(3)
def MODMUL(a, b, m): return UMOD(MUL(UMOD(a, m), UMOD(b, m)), m)
@lv(3)
def NCR(n, k):
    r = 1
    i = 1
    while not LT(k, i):
        r = UDIV(MUL(r, SUB(n, SUB(k, i))), i)
        i = INC(i)
    return r
@lv(3)
def COPRIME(a, b): return EQ(GCD(a, b), 1)
@lv(3)
def SUMDIV(n):
    s = 0
    d = 1
    while not LT(n, d):
        if UMOD(n, d) == 0: s = ADD(s, d)
        d = INC(d)
    return s
@lv(4)
def MODPOW(a, b, m):
    r = 1
    while b != 0:
        if odd(b): r = MODMUL(r, a, m)
        a = MODMUL(a, a, m)
        b = SHR(b)
    return r
@lv(4)
def NPRIME(n):
    k = 1
    while n != 0:
        k = INC(k)
        if ISPRIME(k): n = DEC(n)
    return k
@lv(4)
def PHI(n):
    c = 0
    k = 1
    while not LT(n, k):
        if COPRIME(k, n): c = INC(c)
        k = INC(k)
    return c
@lv(4)
def PERFECT(n): return EQ(SUMDIV(n), SHL(n))
@lv(4)
def CATALAN(n): return UDIV(NCR(SHL(n), n), INC(n))
@lv(4)
def SORTED(x):
    n = LEN(0)
    i = 1
    while LT(i, n):
        if LT(GET(INC(i)), GET(i)): return 0
        i = INC(i)
    return 1
@lv(4)
def LSUM(x):
    n = LEN(0)
    s = 0
    i = 1
    while not LT(n, i):
        s = ADD(s, GET(i))
        i = INC(i)
    return s
@lv(4)
def LMAX(x):
    n = LEN(0)
    m = GET(1)
    i = 2
    while not LT(n, i):
        m = MAX(m, GET(i))
        i = INC(i)
    return m
@lv(5)
def DISTINCT(x):
    n = LEN(0)
    i = 1
    while LT(i, n):
        j = INC(i)
        while not LT(n, j):
            if EQ(GET(i), GET(j)): return 0
            j = INC(j)
        i = INC(i)
    return 1
@lv(5)
def INVERS(x):
    n = LEN(0)
    c = 0
    i = 1
    while LT(i, n):
        j = INC(i)
        while not LT(n, j):
            if LT(GET(j), GET(i)): c = INC(c)
            j = INC(j)
        i = INC(i)
    return c
@lv(5)
def NSORTED(x):
    return EQ(INVERS(0), 0)

# ---- уровень 6: текст порта. Клетки памяти: 65000 текущий символ, 65001 отложенное слово
@lv(6)
def NEXT(x):
    c = _rx(0)
    _store(65000, c)
    return c
@lv(6)
def CUR(x): return _load(65000)
@lv(6)
def WS(x):
    while EQ(CUR(0), 32) or EQ(CUR(0), 13):
        NEXT(0)
    return 0
@lv(6)
def ISDIG(c): return AND(LT(47, c), LT(c, 58))
@lv(6)
def ISLET(c):
    c = OR(c, 32)
    return AND(LT(96, c), LT(c, 123))
@lv(7)
def NUM(x): return _rxnum(0)
@lv(7)
def SNUM(x):
    WS(0)
    if EQ(CUR(0), 45):
        NEXT(0)
        if not ISDIG(CUR(0)): _throw(0)
        return NEG(NUM(0))
    if not ISDIG(CUR(0)): _throw(0)
    return NUM(0)
@lv(7)
def WORD(x):
    h = 0
    while ISLET(CUR(0)) or ISDIG(CUR(0)):
        c = CUR(0)
        if LT(96, c): c = SUB(c, 32)
        h = ADD(MUL(h, 31), c)
        NEXT(0)
    return h
@lv(7)
def FIND(h):
    n = _load(60000)
    i = 0
    while LT(i, n):
        if EQ(_load(ADD(60001, MUL(i, 3))), h): return INC(i)
        i = INC(i)
    return 0
@lv(7)
def SKID(k): return _load(ADD(59999, MUL(k, 3)))
@lv(8)
def SKAR(k): return _load(ADD(60000, MUL(k, 3)))
@lv(8)
def PRD(n):
    if not LT(n, 10): PRD(UDIV(n, 10))
    return _tx(ADD(48, UMOD(n, 10)))
@lv(9)
def PRN(n):
    if LT(n, 0):
        _tx(45)
        return PRD(NEG(n))
    return PRD(n)
@lv(9)
def PRINT(n):
    PRN(n)
    _tx(10)
    _store(65002, 1)
    return 0
@lv(10)
def FARGS(k):
    a = 0
    b = 0
    c = 0
    n = 0
    NEXT(0)
    WS(0)
    if not EQ(CUR(0), 41):
        a = EXPR(0)
        n = 1
        if EQ(CUR(0), 44):
            NEXT(0)
            b = EXPR(0)
            n = 2
            if EQ(CUR(0), 44):
                NEXT(0)
                c = EXPR(0)
                n = 3
    if not EQ(CUR(0), 41): _throw(0)
    NEXT(0)
    if EQ(SKAR(k), 9): _throw(0)
    return _call(SKID(k), a, b, c, 0)
@lv(10)
def ATOM(x):
    h = _load(65001)
    if h != 0:
        _store(65001, 0)
        k = FIND(h)
        if k == 0: _throw(0)
        return FARGS(k)
    WS(0)
    c = CUR(0)
    if ISDIG(c): return NUM(0)
    if EQ(c, 40):
        NEXT(0)
        v = EXPR(0)
        WS(0)
        if not EQ(CUR(0), 41): _throw(0)
        NEXT(0)
        return v
    if ISLET(c):
        k = FIND(WORD(0))
        if k == 0 or not EQ(CUR(0), 40): _throw(0)
        return FARGS(k)
    _throw(0)
    return 0
@lv(10)
def POWER(x):
    v = ATOM(0)
    WS(0)
    if EQ(CUR(0), 94):
        NEXT(0)
        e = UNARY(0)
        if LT(e, 0): _throw(0)
        return POW(v, e)
    return v
@lv(10)
def UNARY(x):
    WS(0)
    if EQ(CUR(0), 45) and _load(65001) == 0:
        NEXT(0)
        return NEG(UNARY(0))
    return POWER(0)
@lv(10)
def TERM(x):
    v = UNARY(0)
    while EQ(CUR(0), 42) or EQ(CUR(0), 47) or EQ(CUR(0), 37):
        c = CUR(0)
        NEXT(0)
        w = UNARY(0)
        if EQ(c, 42): v = MUL(v, w)
        else:
            if EQ(c, 47): v = DIV(v, w)
            else: v = MOD(v, w)
        WS(0)
    return v
@lv(10)
def EXPR(x):
    v = TERM(0)
    WS(0)
    while EQ(CUR(0), 43) or EQ(CUR(0), 45):
        c = CUR(0)
        NEXT(0)
        w = TERM(0)
        if EQ(c, 43): v = ADD(v, w)
        else: v = SUB(v, w)
        WS(0)
    return v
@lv(11)
def LISTARGS(x):
    n = 0
    WS(0)
    while not EQ(CUR(0), 10):
        n = INC(n)
        _store(n, SNUM(0))
        WS(0)
    _store(0, n)
    return n
@lv(11)
def CMDARGS(k):
    a = 0
    b = 0
    c = 0
    WS(0)
    if not EQ(CUR(0), 10):
        a = UNARY(0)
        WS(0)
        if not EQ(CUR(0), 10):
            b = UNARY(0)
            WS(0)
            if not EQ(CUR(0), 10):
                c = UNARY(0)
                WS(0)
    if not EQ(CUR(0), 10): _throw(0)
    return _call(SKID(k), a, b, c, 0)
# ---- уровень 12: выбор навыка. Примеры в памяти с 51000: a, b, ответ
@lv(12)
def ARGV(x, a, b):
    if EQ(x, 0): return a
    if EQ(x, 1): return b
    if EQ(x, 2): return DEC(a)
    if EQ(x, 3): return INC(a)
    if EQ(x, 4): return MUL(a, a)
    if EQ(x, 5): return ADD(a, b)
    if EQ(x, 6): return MUL(a, b)
    if EQ(x, 7): return SUB(a, b)
    return SUB(b, a)
@lv(12)
def FIELD(p, i): return _load(ADD(p, i))
@lv(13)
def APPLY1(p, a, b):
    x = ARGV(FIELD(p, 3), a, b)
    y = ARGV(FIELD(p, 4), a, b)
    f = FIELD(p, 1)
    return _call(f, x, y, 0, 0)
@lv(13)
def OPV(o, u, v):
    if EQ(o, 0): return ADD(u, v)
    if EQ(o, 1): return SUB(u, v)
    return MUL(u, v)
@lv(14)
def EVALP(i, a, b):
    p = ADD(52000, MUL(i, 8))
    f = _load(p)
    u = APPLY1(p, a, b)
    if EQ(f, 0): return u
    o = FIELD(p, 5)
    if EQ(f, 2): return OPV(o, u, FIELD(p, 6))
    g = FIELD(p, 2)
    if EQ(f, 3): return _call(g, u, 0, 0, 0)
    x = ARGV(FIELD(p, 7), a, b)
    y = ARGV(FIELD(p, 4), a, b)
    return OPV(o, u, _call(g, x, y, 0, 0))
@lv(15)
def TRYP(i, ne):
    e = 0
    while LT(e, ne):
        q = ADD(51000, MUL(e, 3))
        v = _try(EVALP, i, _load(q), _load(ADD(q, 1)), 300000)
        if not EQ(v, _load(ADD(q, 2))): return 0
        e = INC(e)
    return 1
@lv(15)
def ATCALC(ne):
    n = _atoms(ne)
    i = 0
    while LT(i, n):
        e = 0
        ok = 1
        while LT(e, ne):
            q = ADD(51000, MUL(e, 3))
            v = _try(EVALP, ADD(625, i), _load(q), _load(ADD(q, 1)), 100000)
            if EQ(v, _bad(0)): ok = 0
            _store(ADD(58600, ADD(MUL(i, 8), e)), v)
            e = INC(e)
        _store(ADD(56800, i), ok)
        i = INC(i)
    return n
@lv(15)
def VEC(i, e): return _load(ADD(58600, ADD(MUL(i, 8), e)))
@lv(15)
def RES(e): return _load(ADD(51002, MUL(e, 3)))
@lv(16)
def PAIROK(i, j, o):
    ne = _load(50992)
    e = 0
    while LT(e, ne):
        if not EQ(OPV(o, VEC(i, e), VEC(j, e)), RES(e)): return 0
        e = INC(e)
    return 1
@lv(16)
def NESTT(g, i, ne):
    e = 0
    while LT(e, ne):
        v = VEC(i, e)
        if not EQ(_try(g, v, 0, 0, 30000), RES(e)): return 0
        e = INC(e)
    return 1
@lv(16)
def CONSTOK(i, o, c):
    ne = _load(50992)
    e = 0
    while LT(e, ne):
        if not EQ(OPV(o, VEC(i, e), c), RES(e)): return 0
        e = INC(e)
    return 1
@lv(17)
def CONSTS(ne, n):
    _store(50992, ne)
    i = 0
    while LT(i, n):
        if _load(ADD(56800, i)) != 0:
            o = 0
            while LT(o, 3):
                c = 1
                while LT(c, 13):
                    if CONSTOK(i, o, c):
                        x = _try(EVALP, ADD(625, i), _load(50990), _load(50991), 3000000)
                        if not EQ(x, _bad(0)):
                            PRN(OPV(o, x, c))
                            _txcombo(i, 999, ADD(MUL(o, 16), c))
                            _tx(10)
                            return 1
                    c = INC(c)
                o = INC(o)
        i = INC(i)
    return 0
@lv(17)
def COMBO(ne, n):
    _store(50992, ne)
    qa = _load(50990)
    qb = _load(50991)
    i = 0
    while LT(i, n):
        if _load(ADD(56800, i)) != 0:
            j = 0
            while LT(j, n):
                if _load(ADD(56800, j)) != 0:
                    o = 0
                    while LT(o, 3):
                        if PAIROK(i, j, o):
                            x = _try(EVALP, ADD(625, i), qa, qb, 3000000)
                            y = _try(EVALP, ADD(625, j), qa, qb, 3000000)
                            if not EQ(x, _bad(0)) and not EQ(y, _bad(0)):
                                PRN(OPV(o, x, y))
                                _txcombo(i, j, o)
                                _tx(10)
                                return 1
                        o = INC(o)
                j = INC(j)
        i = INC(i)
    return 0
@lv(17)
def NEST(ne, n):
    qa = _load(50990)
    qb = _load(50991)
    k = 0
    while LT(k, 8):
        g = _unary(k)
        if not LT(g, 0):
            i = 0
            while LT(i, n):
                if _load(ADD(56800, i)) != 0 and NESTT(g, i, ne):
                    x = _try(EVALP, ADD(625, i), qa, qb, 3000000)
                    if not EQ(x, _bad(0)):
                        x = _try(g, x, 0, 0, 3000000)
                        if not EQ(x, _bad(0)):
                            PRN(x)
                            _txnest(g, i)
                            _tx(10)
                            return 1
                i = INC(i)
        k = INC(k)
    return 0
@lv(17)
def FROMP(lo, hi, ne):
    i = lo
    while LT(i, hi):
        if TRYP(i, ne):
            v = _try(EVALP, i, _load(50990), _load(50991), 3000000)
            if not EQ(v, _bad(0)):
                PRN(v)
                _txplan(i)
                _tx(10)
                return 1
        i = INC(i)
    return 0
@lv(18)
def ANSWER(ne, qa, qb):
    _store(50990, qa)
    _store(50991, qb)
    c = _plan(ne)
    if FROMP(0, MIN(c, 60), ne): return 0
    n = ATCALC(ne)
    if CONSTS(ne, n): return 0
    if COMBO(ne, n): return 0
    if NEST(ne, n): return 0
    if FROMP(60, c, ne): return 0
    return _txplan(99999999)
@lv(19)
def SEQ(x):
    n = 0
    WS(0)
    while not EQ(CUR(0), 10):
        q = ADD(51000, MUL(n, 3))
        n = INC(n)
        _store(q, n)
        _store(ADD(q, 1), 0)
        _store(ADD(q, 2), SNUM(0))
        WS(0)
    _store(50999, 1)
    return ANSWER(n, INC(n), 0)
@lv(19)
def SOLVE(x):
    ne = 0
    nv = 1
    while 1:
        a = SNUM(0)
        b = 0
        WS(0)
        if ISDIG(CUR(0)) or EQ(CUR(0), 45):
            b = SNUM(0)
            nv = 2
            WS(0)
        if not EQ(CUR(0), 61):
            _store(50999, nv)
            return ANSWER(ne, a, b)
        NEXT(0)
        q = ADD(51000, MUL(ne, 3))
        _store(q, a)
        _store(ADD(q, 1), b)
        _store(ADD(q, 2), SNUM(0))
        ne = INC(ne)
        WS(0)
        if EQ(CUR(0), 59): NEXT(0)
@lv(20)
def LINE(x):
    _store(65002, 0)
    NEXT(0)
    WS(0)
    c = CUR(0)
    if EQ(c, 10): return 0
    if EQ(c, 63):
        NEXT(0)
        if ISLET(CUR(0)):
            WORD(0)
            return SEQ(0)
        return SOLVE(0)
    if ISLET(c):
        h = WORD(0)
        if EQ(CUR(0), 40):
            _store(65001, h)
            v = EXPR(0)
        else:
            k = FIND(h)
            if k == 0: _throw(0)
            if EQ(SKAR(k), 9):
                LISTARGS(0)
                v = _call(SKID(k), 0, 0, 0, 0)
            else: v = CMDARGS(k)
    else: v = EXPR(0)
    WS(0)
    if not EQ(CUR(0), 10): _throw(0)
    if _load(65002) == 0:
        PRN(v)
        _tx(10)
    return 0
@lv(21)
def MAIN(x):
    while 1:
        v = _try(LINE, 0, 0, 0, 3000000000)
        if EQ(v, _bad(0)):
            _store(65001, 0)
            _tx(69)
            _tx(82)
            _tx(82)
            _tx(10)
            while not EQ(CUR(0), 10):
                NEXT(0)

# ---- уровни 22-25: управление обновлениями. Манифест операций лежит в памяти как данные:
# 61990 число операций, 61991 цель, 61992 факты сессии, 61993 бит «нет ошибки», 62000 таблица по 5 слов: требует, даёт, снимает, цена
@lv(22)
def NOT(x): return SUB(SUB(0, x), 1)
@lv(22)
def HAS(f, m): return EQ(AND(f, m), m)
@lv(22)
def OPF(i, k): return _load(ADD(62000, ADD(MUL(i, 5), k)))
@lv(23)
def STEPF(f, i): return OR(AND(f, NOT(OPF(i, 2))), OPF(i, 1))
@lv(23)
def MEMOK(f, c):
    h = ADD(64000, MUL(UMOD(f, 499), 2))
    if EQ(_load(h), f) and not LT(c, _load(ADD(h, 1))): return 0
    _store(h, f)
    _store(ADD(h, 1), c)
    return 1
@lv(23)
def KEEP(d, c):
    _store(63000, c)
    _store(63001, d)
    i = 0
    while LT(i, d):
        _store(ADD(63060, i), _load(ADD(63010, i)))
        i = INC(i)
    return 0
@lv(24)
def PDFS(f, d, c):
    if HAS(f, _load(61991)):
        if LT(c, _load(63000)): KEEP(d, c)
        return 0
    if not LT(d, 24): return 0
    i = 0
    n = _load(61990)
    while LT(i, n):
        if HAS(f, OPF(i, 0)):
            g = STEPF(f, i)
            if not EQ(g, f):
                e = ADD(c, OPF(i, 3))
                if LT(e, _load(63000)) and MEMOK(g, e):
                    _store(ADD(63010, d), i)
                    PDFS(g, INC(d), e)
        i = INC(i)
    return 0
@lv(25)
def MKPLAN(f):
    i = 0
    while LT(i, 1000):
        _store(ADD(64000, i), 0)
        i = INC(i)
    _store(63000, 100000000)
    _store(63001, 0)
    PDFS(f, 0, 0)
    return LT(_load(63000), 100000000)
@lv(25)
def PLANCOST(f):
    if MKPLAN(f): return _load(63000)
    return NEG(1)
@lv(25)
def PLANOPS(f):
    MKPLAN(f)
    n = _load(63001)
    r = 0
    i = 0
    while LT(i, n):
        r = ADD(MUL(r, 16), INC(_load(ADD(63060, i))))
        i = INC(i)
    return r
@lv(25)
def SHOWP(x):
    n = _load(63001)
    i = 0
    while LT(i, n):
        _txop(INC(i), _load(ADD(63060, i)))
        i = INC(i)
    return 0
@lv(26)
def PREPARE(f, recov):
    _store(63200, f)
    _store(63201, 0)
    _store(65002, 1)
    if LT(0, _load(63300)): return _txs(2)
    if not MKPLAN(f): return _txs(3)
    _store(63201, 1)
    if recov: _txs(5)
    SHOWP(0)
    return _txs(0)
@lv(26)
def STATUS(x):
    _store(65002, 1)
    return _txf(_obs(0))
@lv(27)
def UPDATE(x): return PREPARE(_obs(0), 0)
@lv(27)
def RECOVER(f, e):
    r = AND(f, _load(61992))
    o = OR(_obs(0), r)
    o = AND(o, NOT(_load(61993)))
    if not LT(30, e): o = OR(o, POW(2, DEC(e)))
    return PREPARE(o, 1)
@lv(28)
def APPROVE(x):
    _store(65002, 1)
    if _load(63201) == 0: return _txs(4)
    _store(63201, 0)
    f = _load(63200)
    n = _load(63001)
    k = 0
    while LT(k, n):
        i = _load(ADD(63060, k))
        if not HAS(f, OPF(i, 0)): return RECOVER(f, 31)
        e = _dev(i)
        if e != 0:
            _txop(0, i)
            return RECOVER(f, e)
        f = STEPF(f, i)
        k = INC(k)
    return _txs(1)
@lv(28)
def CANCEL(x):
    _store(63201, 0)
    _store(65002, 1)
    return _txs(6)
