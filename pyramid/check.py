"""Экзамен пирамиды через порт: эталон независимый, числа случайные."""
import math, random, socket, subprocess, time, sys, json
p = subprocess.Popen(['./npu', '--tcp', '17871']+sys.argv[1:], stderr=subprocess.DEVNULL)
for _ in range(100):
    try: s = socket.create_connection(('127.0.0.1', 17871)); break
    except OSError: time.sleep(.05)
s.settimeout(120); f = s.makefile('rw', newline='\n')
def ask(l): f.write(l+'\n'); f.flush(); return f.readline().strip()
r = random.Random(4); R = lambda h: r.randint(1, h); N = 1 << 31
s64 = lambda v: (v + (1 << 63)) % (1 << 64) - (1 << 63); isp = lambda n: int(n > 1 and all(n % i for i in range(2, int(n**.5)+1)))
def fib(n):
    a, b = 0, 1
    for _ in range(n): a, b = b, a+b
    return a
def col(n):
    c = 0
    while n != 1: n = n//2 if n % 2 == 0 else 3*n+1; c += 1
    return c
PR = [k for k in range(2, 3000) if isp(k)]; srt = lambda a: int(all(x <= y for x, y in zip(a, a[1:]))); inv = lambda a: sum(a[i] > a[j] for i in range(len(a)) for j in range(i+1, len(a)))
def nearly():
    k = r.choice([1, 2, 3, 10, 100, 1000, 5000]); a = sorted(r.randint(0, 10**9) for _ in range(k))
    if k > 1 and r.random() < .6:
        i = r.randrange(k-1); a[i], a[i+1] = a[i]+1, a[i]
    return a
sm = lambda: [r.randint(0, 50) for _ in range(R(40))]
T = {0: {'AND': (2, lambda a, b: a & b, 1 << 62), 'OR': (2, lambda a, b: a | b, 1 << 62), 'XOR': (2, lambda a, b: a ^ b, 1 << 62), 'ADD': (2, lambda a, b: a+b, 1 << 61), 'SUB': (2, lambda a, b: a-b, 1 << 61), 'SHL': (1, lambda a: a*2, 1 << 61), 'SHR': (1, lambda a: a >> 1, 1 << 62), 'LT': (2, lambda a, b: int(a < b), 1 << 10), 'EQ': (2, lambda a, b: int(a == b), 20)},
 1: {'MIN': (2, min, N), 'MAX': (2, max, N), 'MUL': (2, lambda a, b: a*b, N), 'MOD': (2, lambda a, b: a % b, 1 << 60), 'DIV': (2, lambda a, b: a//b, 1 << 61)},
 2: {'POW': (2, lambda a, b: a**b, 6), 'GCD': (2, math.gcd, 1 << 61), 'FACT': (1, math.factorial, 20), 'FIB': (1, fib, 90), 'DIGSUM': (1, lambda n: sum(map(int, str(n))), 1 << 60), 'ISQRT': (1, math.isqrt, 10**6), 'COLLATZ': (1, col, 10**5)},
 3: {'LCM': (2, math.lcm, 1 << 25), 'ISPRIME': (1, isp, 10**6), 'NCR': None, 'COPRIME': (2, lambda a, b: int(math.gcd(a, b) == 1), 5000), 'SUMDIV': (1, lambda n: sum(d for d in range(1, n+1) if n % d == 0), 1000)},
 4: {'MODPOW': None, 'NPRIME': (1, lambda n: PR[n-1], 100), 'PHI': (1, lambda n: sum(math.gcd(i, n) == 1 for i in range(1, n+1)), 300), 'PERFECT': (1, lambda n: int(sum(d for d in range(1, n) if n % d == 0) == n), 500), 'CATALAN': (1, lambda n: math.comb(2*n, n)//(n+1), 15)}}
tot = n = 0; res = {}
for lv, ts in T.items():
    for k, v in ts.items():
        c = 0
        for _ in range(100 if lv < 4 else 30):
            if k == 'NCR': a = R(30); b = r.randint(0, a); w = math.comb(a, b); q = f"NCR {a} {b}"
            elif k == 'MODPOW': a, b, m = R(10**6), R(10**6), R(30000)+1; w = pow(a, b, m); q = f"MODPOW {a} {b} {m}"
            else:
                ar, fn, hi = v; x = [R(hi) for _ in range(ar)]; w = s64(fn(*x)); q = f"{k} {' '.join(map(str, x))}"
            g = ask(q); c += g == str(w)
            if g != str(w) and c < 1: print(' сбой', q, w, g)
            n += 1
        tot += c; res[k] = c; print(f"L{lv} {k:8s} {c}", flush=True)
for k, g, fn in [('SUMSQ', None, None)][:0]+[('SORTED', nearly, srt), ('LSUM', sm, sum), ('LMAX', sm, max), ('DISTINCT', lambda: [r.randint(0, 200) for _ in range(R(30))], lambda a: int(len(set(a)) == len(a))), ('INVERS', sm, inv), ('NSORTED', lambda: sorted(sm()) if r.random() < .5 else sm(), srt)]:
    c = 0
    for _ in range(60):
        a = g(); got = ask(k+' '+' '.join(map(str, a))); w = str(fn(a)); c += got == w; n += 1
        if got != w and c < 1: print(' сбой', k, len(a), w, got)
    tot += c; print(f"L4/5 {k:8s} {c}/60", flush=True)

import ast
def tdiv(a, b): q = abs(a)//abs(b); return q if (a < 0) == (b < 0) else -q
def ev(t):
    if isinstance(t, ast.Constant): return t.value
    if isinstance(t, ast.UnaryOp): return s64(-ev(t.operand))
    if isinstance(t, ast.Call):
        a = [ev(x) for x in t.args]; return {'FIB': fib, 'GCD': math.gcd, 'FACT': math.factorial, 'ISQRT': math.isqrt, 'SUMDIV': lambda n: sum(d for d in range(1, n+1) if n % d == 0)}[t.func.id](*a)
    x, y = ev(t.left), ev(t.right); o = type(t.op).__name__
    if o in ('Div', 'Mod') and y == 0: raise ZeroDivisionError
    return s64({'Add': x+y, 'Sub': x-y, 'Mult': x*y, 'Div': tdiv(x, y) if y else 0, 'Mod': x-y*tdiv(x, y) if y else 0}[o])
def gx(d=0):
    x = r.random()
    if d > 3 or x < .3: return str(r.randint(0, 9999))
    if x < .42: return '(' + gx(d+1) + ')'
    if x < .5: return '-' + gx(d+1)
    if x < .62:
        n = r.randint(1, 20); return r.choice([f"FIB({n})", f"FACT({n})", f"ISQRT({n*99})", f"GCD({n*6},{n*4})", f"SUMDIV({n})"])
    return gx(d+1) + r.choice(['+', '-', '*', '/', '%', ' + ', ' * ']) + gx(d+1)
c = m = 0
for _ in range(400):
    e = gx()
    try: w = ev(ast.parse(e, mode='eval').body)
    except ZeroDivisionError: w = 'ERR'
    g = ask(e); m += 1; c += g == str(w)
    if g != str(w) and m-c < 4: print(' сбой', e, w, g)
print(f"Выражения со знаком и навыками: {c}/{m}", flush=True); tot += c; n += m
c = 0
for _ in range(200):
    a, b = r.randint(-1 << 50, 1 << 50), r.randint(-1 << 30, 1 << 30) or 1; q = tdiv(a, b); c += (ask(f"DIV {a} {b}") == str(q)) + (ask(f"MOD {a} {b}") == str(a-b*q))
print(f"DIV и MOD со знаком: {c}/400", flush=True); tot += c; n += 400
bad = ['FOO 1', '1/0', 'DIV 1 0', '(2', '1+', '2)', 'MOD 7 0', '2^-1', 'fib(', '3 $', 'MUL 1 2 3 4', 'foo(1)']; e = [ask(q) for q in bad]; print('Ошибки:', sum(x == 'ERR' for x in e), '/', len(bad), '| после них', ask('MUL 6 7'), '| пустая строка, CRLF:', (f.write('\n\r\nFIB 10\r\n'), f.flush(), f.readline().strip())[2], flush=True); tot += sum(x == 'ERR' for x in e); n += len(bad)
sys.path.insert(0, '../nc'); import practice as P
BI = P.BI; BI['ISPRIME'] = BI.pop('PRIME')
for k in ('MODINV', 'TRIB', 'REVDIG', 'PALIN', 'DIVCOUNT', 'PRIMEPI', 'BINOMSUM'): del BI[k]
P.NAMES[:] = list(BI); late = ['PERFECT', 'CATALAN', 'SUMSQ']; rr = random.Random(99)
C = {'один навык': (lambda p: p[0] != 0 or p[1] in late, 60), 'навык+константа': (lambda p: p[0] != 2 or p[1] in late, 30), 'скрытая пара': (lambda p: not (p[0] in (1, 3) and P.hold(p)), 30), 'новый навык': (lambda p: p[0] != 0 or p[1] not in late, 30)}
import statistics
for name, (h, k) in C.items():
    c = fail = 0; t0 = time.time()
    for _ in range(k):
        t = None
        while t is None: t = P.make_task(rr, P.NAMES, h)
        pl, nv, ex = t; q = '? '+'; '.join(f"{e[0]} {e[1]} = {e[2]}" if nv == 2 else f"{e[0]} = {e[2]}" for e in ex[:4])+'; '+(f"{ex[4][0]} {ex[4][1]}" if nv == 2 else f"{ex[4][0]}")
        g = ask(q); c += g.split(' ')[0] == str(ex[4][2]); fail += 'НЕ' in g
    print(f"Без названия, {name}: верно {c}/{k}, не знаю {fail}, {(time.time()-t0)/k:.2f}с на задачу", flush=True)
print('Ряды:', [ask(q)[:44] for q in ('?SEQ 0 1 1 2 3 5 8', '?SEQ 2 3 5 7 11 13', '?SEQ 1 5 14 30 55')])
print(f"ИТОГО {tot}/{n}", 'нули и пустой список:', ask('SORTED'), ask('MUL 0 5'), ask('FACT 0')); p.kill()

