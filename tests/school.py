"""Учёба, затем работа. Эталон ответов считается отдельно от уроков."""
import math, random, socket, subprocess, sys, time, inspect, json, ast
sys.path.insert(0, 'nc'); sys.path.insert(0, 'tests')
from teacher import Teacher
import lessons
BIN, MODEL = './nc_bin', 'models/nc2.bin'; PORT = 17811
p = subprocess.Popen([BIN, '--model', MODEL, '--tcp', str(PORT)], stderr=subprocess.DEVNULL)
for _ in range(100):
    try: s = socket.create_connection(('127.0.0.1', PORT)); break
    except OSError: time.sleep(.05)
s.settimeout(120); f = s.makefile('rw', newline='\n')
def ask(l): f.write(l+'\n'); f.flush(); return f.readline().strip()
isp = lambda n: n > 1 and all(n % i for i in range(2, int(n**.5)+1))
def fib(n):
    a, b = 0, 1
    for _ in range(n): a, b = b, a+b
    return a
def trib(n):
    t = [0, 0, 1]
    while len(t) <= n: t.append(sum(t[-3:]))
    return t[n]
divs = lambda n: [d for d in range(1, n+1) if n % d == 0]
REF = {'TRIB': (trib, lambda r: (r.randint(0, 60),)), 'SUMDIV': (lambda n: sum(divs(n)), lambda r: (r.randint(1, 3000),)), 'PERFECT': (lambda n: int(sum(divs(n)) == 2*n), lambda r: (r.choice([6, 28, 496, 8128, r.randint(1, 3000)]),)),
       'REVDIG': (lambda n: int(str(n)[::-1]), lambda r: (r.randint(1, 10**9),)), 'PALIN': (lambda n: int(str(n) == str(n)[::-1]), lambda r: (r.choice([r.randint(1, 10**6), int(str(x := r.randint(1, 999))+str(x)[::-1])]),)),
       'DIVCOUNT': (lambda n: len(divs(n)), lambda r: (r.randint(1, 3000),)), 'CATALAN': (lambda n: math.comb(2*n, n)//(n+1), lambda r: (r.randint(0, 15),)),
       'COPRIME': (lambda a, b: int(math.gcd(a, b) == 1), lambda r: (r.randint(1, 5000), r.randint(1, 5000))), 'PRIMEPI': (lambda n: sum(isp(k) for k in range(n+1)), lambda r: (r.randint(1, 300),)),
       'SUMSQ': (lambda n: n*(n+1)*(2*n+1)//6, lambda r: (r.randint(1, 10**5),)), 'BINOMSUM': (lambda n: 2**n, lambda r: (r.randint(0, 25),))}
print('== УЧЁБА'); T = Teacher(f); R = {}; r = random.Random(31337)
for n, fn in inspect.getmembers(lessons, inspect.isfunction): pass
order = [v for k, v in vars(lessons).items() if inspect.isfunction(v)]
for fn in order:
    c, ms = T.teach(fn); ref, gen = REF[fn.__name__]; ok = 0
    for _ in range(40):
        a = gen(r); w = ref(*a); got = ask(fn.__name__+' '+' '.join(map(str, a))); ok += got == str(w)
        if got != str(w) and ok == 0: print('   сбой', a, w, got)
    R[fn.__name__] = ok; print(f"  {fn.__name__:9s} фигур {c:4d}, {ms:6.1f} мс на показ, экзамен {ok}/40", flush=True)
f.write('@SAVE models/skills.mem\n'); f.flush(); f.readline()
print('== РАБОТА: новые ситуации без учителя')
BI = {'FIB': (fib, 1, 40), 'FACT': (math.factorial, 1, 12), 'GCD': (math.gcd, 2, 5000), 'ISQRT': (math.isqrt, 1, 10**6), 'DIGSUM': (lambda n: sum(map(int, str(n))), 1, 10**6),
      'TRIB': (trib, 1, 40), 'REVDIG': (lambda n: int(str(n)[::-1]), 1, 10**5), 'SUMSQ': (lambda n: n*(n+1)*(2*n+1)//6, 1, 500), 'LCM': (math.lcm, 2, 300), 'DIVCOUNT': (lambda n: len(divs(n)), 1, 500)}
def gen(d=0):
    x = r.random()
    if d >= 3 or x < .3:
        v = r.randint(1, 30); return str(v), v
    if x < .75:
        n = r.choice(list(BI)); fn, ar, hi = BI[n]
        if ar == 1:
            e, v = gen(d+1)
            if not 0 < v <= hi: return str(max(1, min(abs(v), 30))), max(1, min(abs(v), 30))
            return f"{n}({e})", fn(v)
        e1, v1 = gen(d+1); e2, v2 = gen(d+1)
        if not (0 < v1 <= hi and 0 < v2 <= hi): return str(7), 7
        return f"{n.lower()}({e1},{e2})", fn(v1, v2)
    e1, v1 = gen(d+1); e2, v2 = gen(d+1); o = r.choice('+-*')
    return f"({e1}{o}{e2})", eval(f"{v1}{o}{v2}")
ok = n = 0
for _ in range(400):
    e, v = gen()
    if abs(v) >= 1 << 62: continue
    n += 1; got = ask(e)
    if got == str(v): ok += 1
    elif n - ok < 5: print('   сбой', e, v, got)
print(f"Выражения из навыков, которых вместе не показывали: {ok}/{n}", flush=True)
# программа на ISA с показанным навыком
ok2 = 0
for _ in range(30):
    k = r.randint(1, 25); out = [ask('PROG')]
    for l in ['SET R0 0', f'SET R1 {k}', 'SET R2 R1', 'TRIB R2', 'ADD R0 R2', 'SUB R1 1', 'JNZ R1 2', 'PRINT R0', 'HALT']: f.write(l+'\n')
    f.flush(); ask('END'); got = ask('RUN'); f.readline(); ok2 += got == str(sum(trib(i) for i in range(1, k+1)))
print(f"Программа с навыком TRIB в цикле: {ok2}/30", flush=True)
# навык не назван: только примеры
S = [('сумма делителей', lambda a: sum(divs(a)), 1, 60), ('ряд Фибоначчи', fib, 1, 30), ('факториал', math.factorial, 1, 10), ('НОД', math.gcd, 2, 200), ('НОК', math.lcm, 2, 40), ('квадрат суммы цифр', lambda a: sum(map(int, str(a)))**2, 1, 900),
     ('число делителей', lambda a: len(divs(a)), 1, 300), ('фибоначчи+3', lambda a: fib(a)+3, 1, 25), ('2·факториал', lambda a: 2*math.factorial(a), 1, 9), ('простое-й', lambda a: [p for p in range(2, 700) if isp(p)][a-1], 1, 60),
     ('НОД+НОК', lambda a, b: math.gcd(a, b)+math.lcm(a, b), 2, 40), ('степень', lambda a, b: a**b, 2, 7), ('факт. суммы цифр', lambda a: math.factorial(sum(map(int, str(a)))), 1, 50), ('сумма квадратов', lambda a: a*(a+1)*(2*a+1)//6, 1, 90),
     ('палиндром цифр', lambda a: int(str(a)[::-1])+a, 1, 900), ('Каталан', lambda a: math.comb(2*a, a)//(a+1), 1, 12)]
ok3 = 0; rep = []
for name, fn, ar, hi in S*3:
    xs = [tuple(r.randint(1, hi) for _ in range(ar)) for _ in range(5)]
    while len(set(xs)) < 5: xs = [tuple(r.randint(1, hi) for _ in range(ar)) for _ in range(5)]
    q = '? ' + '; '.join(' '.join(map(str, x))+f" = {fn(*x)}" for x in xs[:4]) + '; ' + ' '.join(map(str, xs[4]))
    got = ask(q); want = str(fn(*xs[4])); good = got.split(' ')[0] == want; ok3 += good; rep.append((name, good, got[:60]))
for x in rep[:16]+rep[-16:]: print('  ', x)
print(f"Задачи без названия навыка: {ok3}/{len(rep)}", flush=True)
for q, w in [('?SEQ 0 1 1 2 3 5 8', '13'), ('?SEQ 1 1 2 6 24 120', None), ('?SEQ 2 3 5 7 11 13', '17'), ('?SEQ 1 3 6 10 15', '21'), ('?SEQ 1 5 14 30 55', '91'), ('?SEQ 1 2 5 14 42', '132')]: print('  ', q, '->', ask(q)[:70])
p.kill()
