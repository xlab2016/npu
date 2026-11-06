"""Обёртка над перебором, задачи и признаки. Задача известна только по примерам: вход -> ответ."""
import ctypes, math, random, numpy as np, os
L = ctypes.CDLL(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'libsynth.so'))
NG, NBASE, MAXS = 7, 10, 8
class St(ctypes.Structure): _fields_ = [(n, ctypes.c_int) for n in ('g','gx','gy','op','a','b')]
class Prog(ctypes.Structure):
    _fields_ = [(n, ctypes.c_int) for n in ('np','nb','nq','lg','lx','ly')] + [('p', St*MAXS), ('b', St*MAXS), ('q', St*MAXS)]
assert L.prog_size() == ctypes.sizeof(Prog)
GN = ['','odd','even','zero','nz','lt','ge']; ON = ['MOV','ADD','SUB','SWAP','SHL','SHR','INC','DEC','ZERO','TEN']
L.dream_batch.argtypes = [ctypes.c_int, ctypes.POINTER(Prog), ctypes.POINTER(ctypes.c_int64), ctypes.POINTER(ctypes.c_int64), ctypes.POINTER(ctypes.c_int64), ctypes.c_int]
L.run_one.argtypes = [ctypes.POINTER(Prog), ctypes.c_int64, ctypes.c_int64, ctypes.c_int64, ctypes.c_long, ctypes.POINTER(ctypes.c_int64)]
L.search.argtypes = [ctypes.POINTER(ctypes.c_double)]*3 + [ctypes.POINTER(ctypes.c_int64), ctypes.c_int, ctypes.c_long, ctypes.c_long, ctypes.c_uint64, ctypes.POINTER(Prog), ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_double)]
ARS = []
def lib_add(p, ar):
    L.lib_add(ctypes.byref(p), ar); ARS.append(ar)
def run(p, a, b=0, c=0, lim=2_000_000):
    o = ctypes.c_int64(); ok = L.run_one(ctypes.byref(p), a, b, c, lim, ctypes.byref(o)); return o.value if ok else None
def show(p, names):
    def op(s):
        n = ON[s.op] if s.op < NBASE else names[s.op-NBASE]; two = s.op <= 3 or (s.op >= NBASE and ARS[s.op-NBASE] == 2)
        g = '' if not s.g else f"если {GN[s.g]} r{s.gx}{' r'+str(s.gy) if s.g >= 5 else ''}: "
        return f"{g}{n} r{s.a}" + (f" r{s.b}" if two else '')
    t = [op(p.p[i]) for i in range(p.np)]
    if p.lg:
        t.append(f"пока {GN[p.lg]} r{p.lx}{' r'+str(p.ly) if p.lg >= 5 else ''}:"); t += ['   ' + op(p.b[i]) for i in range(p.nb)]; t += [op(p.q[i]) for i in range(p.nq)]
    return t
def tokens(p, nops):
    """Метки: какие операции, условия и циклы есть в программе."""
    y = np.zeros(2*NG + NBASE + nops, 'f4')
    for arr, n in ((p.p, p.np), (p.b, p.nb if p.lg else 0), (p.q, p.nq if p.lg else 0)):
        for i in range(n):
            y[arr[i].g] = 1; y[2*NG + arr[i].op] = 1
    y[NG + p.lg] = 1
    return y
PROBES = [(a, b) for a in (1, 2, 3, 4, 5, 6, 7, 9, 12, 17) for b in (1, 2, 3, 5)]
def features(out, unary):
    """out: ответы на пробах. Только сравнения и масштаб ответа, ничего про название задачи."""
    f = [float(unary)]
    prev = None
    for (a, b), v in zip(PROBES, out):
        if unary and b != 1: f += [0]*10; continue
        if v is None: f += [0]*9 + [1]; continue
        l = math.log1p(abs(v))/10
        f += [l, l - math.log1p(a)/10, l - math.log1p(b)/10, float(v == a), float(v == b), float(v == 0), float(v == 1), float(v & 1), float(v > a), 0]
    return f
def fact(n): return math.factorial(n)
def fib(n):
    a, b = 0, 1
    for _ in range(n): a, b = b, a+b
    return a
def isprime(n): return int(n > 1 and all(n % i for i in range(2, int(n**.5)+1)))
def digsum(n): return sum(map(int, str(n)))
def collatz(n):
    c = 0
    while n != 1: n = n//2 if n % 2 == 0 else 3*n+1; c += 1
    return c
def phi(n): return sum(math.gcd(i, n) == 1 for i in range(1, n+1))
# имя, функция, арность, область малых значений, область проверки, нужен быстрый алгоритм
R = random.Random
T = {
 'MIN': (min, 2, 30, 1<<40, 0), 'MAX': (max, 2, 30, 1<<40, 0), 'SUMTO': (lambda a: a*(a+1)//2, 1, 40, 5000, 0),
 'MUL': (lambda a, b: a*b, 2, 30, 1<<30, 1), 'DOUBLE': (lambda a: 2*a, 1, 30, 1<<40, 0), 'HALF': (lambda a: a//2, 1, 30, 1<<40, 0),
 'DIV': (lambda a, b: a//b, 2, 60, 5000, 0), 'MOD': (lambda a, b: a % b, 2, 60, 5000, 0), 'POW': (lambda a, b: a**b, 2, 5, 9, 0),
 'FACT': (fact, 1, 9, 20, 0), 'FIB': (fib, 1, 25, 90, 0), 'GCD': (math.gcd, 2, 60, 5000, 0), 'LCM': (math.lcm, 2, 30, 2000, 0),
 'SQUARE': (lambda a: a*a, 1, 30, 1<<20, 0), 'ISQRT': (math.isqrt, 1, 200, 10**5, 0), 'DIGSUM': (digsum, 1, 2000, 10**9, 0),
 'POPCOUNT': (lambda a: bin(a).count('1'), 1, 500, 1<<40, 0), 'ILOG2': (lambda a: a.bit_length()-1, 1, 500, 1<<40, 0),
 'DIGITS': (lambda a: len(str(a)), 1, 2000, 10**9, 0), 'TRI2': (lambda a: a*(a-1)//2, 1, 40, 5000, 0), 'ISPRIME': (isprime, 1, 60, 3000, 0),
 'COLLATZ': (collatz, 1, 60, 3000, 0), 'PHI': (phi, 1, 60, 600, 0), 'NCR': (math.comb, 2, 12, 30, 0),
}
def domain(n, r, hi, ar):
    if ar == 1: return (r.randint(1, hi), 0)
    if n in ('POW',): return (r.randint(1, hi), r.randint(0, 9))
    if n == 'NCR':
        a = r.randint(1, hi); return (a, r.randint(0, a))
    return (r.randint(1, hi), r.randint(1, hi))
def examples(n, extra=()):
    f, ar, small, big, fast = T[n]; r = R(hash_name(n)); e = []
    pts = [(1, 1) if ar == 2 else (1, 0), (2, 3) if ar == 2 else (2, 0), (3, 2) if ar == 2 else (3, 0)]
    if n == 'NCR': pts = [(1, 1), (3, 2), (4, 2)]
    pts += [domain(n, r, small, ar) for _ in range(21)]
    if fast: pts += [domain(n, r, big, ar) for _ in range(4)]
    pts += list(extra)
    for a, b in pts:
        v = f(a) if ar == 1 else f(a, b)
        if abs(v) < 1 << 62: e += [a, b, 0, v]
    return np.array(e, 'i8')
def hash_name(n): return sum(ord(c)*(i+7) for i, c in enumerate(n))
def verify(n, p, count=300):
    f, ar, small, big, fast = T[n]; r = R(hash_name(n)+999); bad = None
    for i in range(count):
        a, b = domain(n, r, big, ar); v = f(a) if ar == 1 else f(a, b)
        if abs(v) >= 1 << 62: continue
        if run(p, a, b, 0, 3_000_000) != v: return (a, b)
    return None
def probe_out(n):
    f, ar, *_ = T[n]; o = []
    for a, b in PROBES:
        try:
            v = f(a) if ar == 1 else f(a, b)
            o.append(v if abs(v) < 1 << 62 else None)
        except Exception: o.append(None)
    return o, ar == 1
def do_search(n, wg, wo, wl, maxc, extra=()):
    ex = examples(n, extra); c_d = ctypes.c_double
    g = (c_d*NG)(*wg); o = (c_d*len(wo))(*wo); l = (c_d*NG)(*wl); p = Prog(); used = ctypes.c_uint64(); bits = c_d()
    ok = L.search(g, o, l, ex.ctypes.data_as(ctypes.POINTER(ctypes.c_int64)), len(ex)//4, 5000 if T[n][4] else 200000, 400, maxc, ctypes.byref(p), ctypes.byref(used), ctypes.byref(bits))
    return ok, p, used.value, bits.value
