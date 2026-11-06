"""Сверка nc через порт с независимым эталоном на Python. Числа новые: другое зерно и другие диапазоны, чем в обучении."""
import math, random, socket, subprocess, sys, time, os, json, ast, collections
BIN, MODEL = sys.argv[1], sys.argv[2]; N = int(sys.argv[3]) if len(sys.argv) > 3 else 200; PORT = int(sys.argv[4]) if len(sys.argv) > 4 else 17771
def s64(v):
    v &= (1 << 64) - 1
    return v - (1 << 64) if v >> 63 else v
def tdiv(a, b): q = abs(a) // abs(b); return q if (a < 0) == (b < 0) else -q
def tmod(a, b): return a - b * tdiv(a, b)
def isprime(n):
    if n < 2: return 0
    i = 2
    while i * i <= n:
        if n % i == 0: return 0
        i += 1
    return 1
def nprime(n):
    c, k = 0, 1
    while c < n:
        k += 1; c += isprime(k)
    return k
def phi(n):
    return sum(1 for i in range(1, n + 1) if math.gcd(i, n) == 1)
def collatz(n):
    c = 0
    while n != 1: n = n // 2 if n % 2 == 0 else 3 * n + 1; c += 1
    return c
def fib(n):
    a, b = 0, 1
    for _ in range(n): a, b = b, a + b
    return a
r = random.Random(987654)
big = lambda hi=1 << 61: r.randint(-hi, hi)
pos = lambda hi: r.randint(1, hi)
def ev(n):
    if isinstance(n, ast.Constant): return n.value
    if isinstance(n, ast.UnaryOp): return s64(-ev(n.operand))
    a, b = ev(n.left), ev(n.right)
    if isinstance(n.op, ast.Add): return s64(a + b)
    if isinstance(n.op, ast.Sub): return s64(a - b)
    if isinstance(n.op, ast.Mult): return s64(a * b)
    if isinstance(n.op, ast.Pow): return s64(pow(a, b, 1 << 64))
    if b == 0: raise ZeroDivisionError
    return s64(tdiv(a, b)) if isinstance(n.op, ast.Div) else s64(tmod(a, b))
def gen_expr(d=0):
    x = r.random()
    if d > 4 or x < .3: return str(r.randint(0, 10**6))
    if x < .42: return '(' + gen_expr(d + 1) + ')'
    if x < .5: return '-' + gen_expr(d + 1)
    if x < .56: return f"{r.randint(2, 9)}^{r.randint(0, 9)}"
    return gen_expr(d + 1) + r.choice(['+', '-', '*', '/', '%', ' + ', ' * ']) + gen_expr(d + 1)
def T(name):
    if name == 'ADD': a, b = big(), big(); return f"ADD {a} {b}", s64(a + b)
    if name == 'SUB': a, b = big(), big(); return f"SUB {a} {b}", s64(a - b)
    if name == 'MUL': a, b = big(), big(); return f"MUL {a} {b}", s64(a * b)
    if name == 'DIV': a, b = big(), big(1 << 40) or 1; return f"DIV {a} {b}", tdiv(a, b)
    if name == 'MOD': a, b = big(), big(1 << 40) or 1; return f"MOD {a} {b}", tmod(a, b)
    if name == 'ABS': a = big(); return f"ABS {a}", abs(a)
    if name == 'MIN': a, b = big(), big(); return f"MIN {a} {b}", min(a, b)
    if name == 'MAX': a, b = big(), big(); return f"MAX {a} {b}", max(a, b)
    if name == 'POW': a, b = r.randint(-99, 99), r.randint(0, 200); return f"POW {a} {b}", s64(pow(a, b, 1 << 64))
    if name == 'expr':
        while True:
            e = gen_expr()
            try:
                t = ast.parse(e.replace('/', '/').replace('^', '**'), mode='eval').body; return e, ev(t)
            except (ZeroDivisionError, ValueError): continue
    if name == 'GCD': a, b = big(), big(); return f"GCD {a} {b}", math.gcd(a, b)
    if name == 'LCM': a, b = big(1 << 30), big(1 << 30); return f"LCM {a} {b}", math.lcm(a, b)
    if name == 'FACT': a = r.randint(0, 20); return f"FACT {a}", math.factorial(a)
    if name == 'FIB': a = r.randint(0, 92); return f"FIB {a}", fib(a)
    if name == 'ISQRT': a = r.randint(0, (1 << 63) - 1); return f"ISQRT {a}", math.isqrt(a)
    if name == 'PRIME': a = r.randint(0, 10**7); return f"PRIME {a}", isprime(a)
    if name == 'MODPOW': a, b, m = pos(1 << 61), pos(1 << 61), pos(1 << 60) + 1; return f"MODPOW {a} {b} {m}", pow(a, b, m)
    if name == 'NCR': n = r.randint(0, 60); k = r.randint(0, n); return f"NCR {n} {k}", math.comb(n, k)
    if name == 'NPRIME': a = r.randint(1, 300); return f"NPRIME {a}", nprime(a)
    if name == 'PHI': a = r.randint(1, 5000); return f"PHI {a}", phi(a)
    if name == 'DIGSUM': a = big(); return f"DIGSUM {a}", sum(map(int, str(abs(a))))
    if name == 'COLLATZ': a = r.randint(1, 10**6); return f"COLLATZ {a}", collatz(a)
    if name == 'MODINV':
        while True:
            a, m = pos(1 << 40), pos(1 << 40) + 1
            if math.gcd(a, m) == 1: return f"MODINV {a} {m}", pow(a, -1, m)
    raise KeyError(name)
GROUPS = {'Калькулятор': ['ADD','SUB','MUL','DIV','MOD','ABS','MIN','MAX','POW','expr'], 'Теория чисел': ['GCD','LCM','FACT','FIB','ISQRT','PRIME'],
          'Сложная математика': ['MODPOW','NCR','NPRIME','PHI','DIGSUM','COLLATZ','MODINV']}
p = subprocess.Popen([BIN, '--model', MODEL, '--tcp', str(PORT)] + (['--mem', sys.argv[5]] if len(sys.argv) > 5 else []), stderr=subprocess.DEVNULL)
for _ in range(100):
    try: s = socket.create_connection(('127.0.0.1', PORT)); break
    except OSError: time.sleep(.05)
s.settimeout(20); f = s.makefile('rw', newline='\n')
def ask(l):
    f.write(l + '\n'); f.flush(); return f.readline().strip()
res = collections.OrderedDict(); fails = []
try:
    t0 = time.time()
    for g, ns in GROUPS.items():
        for nm in ns:
            ok = 0; tn = time.time()
            for _ in range(N):
                c, want = T(nm); got = ask(c)
                if got == str(want): ok += 1
                elif len(fails) < 12: fails.append((c, want, got))
            res[nm] = dict(group=g, ok=ok, n=N, ms=round((time.time() - tn) / N * 1000, 2)); print(g, nm, ok, N, res[nm]['ms'], 'мс', flush=True)
    # программа на ISA: сумма 1..n с циклом, выполняется выборкой из памяти
    prog_ok = 0
    for _ in range(30):
        n = r.randint(1, 500); out = []
        for l in ['PROG', 'SET R0 0', f'SET R1 {n}', 'ADD R0 R1', 'SUB R1 1', 'JNZ R1 2', 'PRINT R0', 'HALT', 'END']: out.append(ask(l)) if l in ('PROG', 'END') else f.write(l + '\n')
        f.flush(); a = ask('RUN'); b = f.readline().strip()
        prog_ok += (a == str(n * (n + 1) // 2) and b == 'OK')
    res['PROG'] = dict(group='Программа', ok=prog_ok, n=30, ms=0)
    err_ok = sum(ask(c) == 'ERR' for c in ['FOO 1', 'DIV 1 0', '(2', '1+', 'MOD 7 0', 'POW 2 -1', 'ADD 1 2 3 4', 'MUL R9 1', 'FACT -1', 'MODINV 2 4'])
    res['ERR'] = dict(group='Ошибки', ok=err_ok, n=10, ms=0)
finally:
    p.kill()
print('сбои:', *fails, sep='\n  ')
tot = sum(v['ok'] for v in res.values()); n = sum(v['n'] for v in res.values())
print(f"ИТОГО {tot}/{n}"); json.dump(dict(res=res, fails=[list(map(str, x)) for x in fails], tot=tot, n=n), open(MODEL + '.check.json', 'w'), ensure_ascii=False, indent=1)
