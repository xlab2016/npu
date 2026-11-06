"""Циклы и списки: формулы из замороженных навыков против независимого эталона."""
import random, socket, subprocess, sys, time, math
p = subprocess.Popen(['./nc_bin', '--model', 'models/nc2.bin', '--mem', 'models/skills.mem', '--tcp', '17861'], stderr=subprocess.DEVNULL)
for _ in range(200):
    try: s = socket.create_connection(('127.0.0.1', 17861)); break
    except OSError: time.sleep(.05)
s.settimeout(120); f = s.makefile('rw', newline='\n')
def ask(l): f.write(l+'\n'); f.flush(); return f.readline().strip()
print('сумма до', ask('@HASH')); r = random.Random(777)
D = ['SORTED(list) = ALL(i,1,LEN(0)-1,AT(i)<=AT(i+1))', 'SORTEDD(list) = ALL(i,1,LEN(0)-1,AT(i)>=AT(i+1))', 'STRICT(list) = ALL(i,1,LEN(0)-1,AT(i)<AT(i+1))', 'LSUM(list) = SUM(i,1,LEN(0),AT(i))',
     'LMAX(list) = FOLD(m,AT(1),i,2,LEN(0),MAX(m,AT(i)))', 'LMIN(list) = FOLD(m,AT(1),i,2,LEN(0),MIN(m,AT(i)))', 'POSMAX(list) = m = LMAX(0); FIRST(i,1,LEN(0),AT(i)==m)', 'EVENS(list) = COUNT(i,1,LEN(0),AT(i)%2==0)',
     'DISTINCT(list) = ALL(i,1,LEN(0),ALL(j,i+1,LEN(0),AT(i)!=AT(j)))', 'INVERS(list) = SUM(i,1,LEN(0),SUM(j,i+1,LEN(0),IF(AT(i)>AT(j),1,0)))', 'PALL(list) = ALL(i,1,LEN(0)/2,AT(i)==AT(LEN(0)+1-i))',
     'ISPR(n) = n>1 and ALL(d,2,ISQRT(n),n%d!=0)', 'SDIV(n) = SUM(d,1,n,IF(n%d==0,d,0))', 'PERF(n) = SDIV(n)==2*n', 'FACT2(n) = PROD(i,1,n,i)', 'TRIPLES(n) = SUM(a,1,n,SUM(b,a,n,COUNT(c,b,n,a*a+b*b==c*c)))', 'STEPS(n) = FOLD(s,0,i,1,0,s)+COLLATZ(n)', 'POW2(n) = ITER(x,1,x*2<=n,x*2)']
for d in D: print(' ', 'DEF', d, '->', ask('DEF '+d))
L = lambda: [r.randint(-1000, 1000) for _ in range(r.choice([1, 2, 3, 5, 10, 50, 100, 500]))]
def nearly(k):
    a = sorted(r.randint(-10**6, 10**6) for _ in range(k))
    if k > 1 and r.random() < .6:
        i = r.choice([0, k-2, r.randrange(k-1)]); a[i], a[i+1] = a[i+1], a[i]
    return a
srt = lambda a: all(a[i] <= a[i+1] for i in range(len(a)-1))
inv = lambda a: sum(a[i] > a[j] for i in range(len(a)) for j in range(i+1, len(a)))
tests = {'SORTED': (lambda: nearly(r.choice([0, 1, 2, 3, 7, 20, 100, 1000])), lambda a: int(srt(a))), 'SORTEDD': (lambda: nearly(r.choice([2, 5, 50]))[::-1], lambda a: int(srt(a[::-1]))), 'STRICT': (lambda: nearly(r.choice([2, 5, 50])), lambda a: int(all(x < y for x, y in zip(a, a[1:])))),
         'LSUM': (L, sum), 'LMAX': (L, max), 'LMIN': (L, min), 'EVENS': (L, lambda a: sum(x % 2 == 0 for x in a)), 'DISTINCT': (lambda: [r.randint(0, 200) for _ in range(r.randint(1, 40))], lambda a: int(len(set(a)) == len(a))),
         'INVERS': (lambda: [r.randint(0, 100) for _ in range(r.randint(1, 40))], inv), 'PALL': (lambda: (lambda h: h+h[::-1] if r.random() < .5 else h+[1]+h)([r.randint(0, 9) for _ in range(r.randint(1, 30))]), lambda a: int(a == a[::-1]))}
tot = n = 0
for k, (g, fn) in tests.items():
    c = 0
    for _ in range(50):
        a = g(); w = fn(a); got = ask(k+' '+' '.join(map(str, a))); c += got == str(w)
        if got != str(w) and c < 2: print('  сбой', k, a[:8], len(a), w, got)
    print(f"  {k:9s} {c}/50", flush=True); tot += c; n += 50
isp = lambda x: int(x > 1 and all(x % i for i in range(2, int(x**.5)+1)))
num = {'ISPR': (lambda: r.randint(1, 10**6), isp), 'SDIV': (lambda: r.randint(1, 500), lambda x: sum(d for d in range(1, x+1) if x % d == 0)), 'PERF': (lambda: r.choice([6, 28, 496, r.randint(1, 500)]), lambda x: int(sum(d for d in range(1, x) if x % d == 0) == x)), 'FACT2': (lambda: r.randint(0, 20), math.factorial),
       'TRIPLES': (lambda: r.randint(1, 30), lambda x: sum(a*a+b*b == c*c for a in range(1, x+1) for b in range(a, x+1) for c in range(b, x+1))), 'POW2': (lambda: r.randint(1, 1 << 40), lambda x: 1 << (x.bit_length()-1))}
for k, (g, fn) in num.items():
    c = 0
    for _ in range(30):
        x = g(); c += ask(f"{k}({x})") == str(fn(x))
    print(f"  {k:9s} {c}/30", flush=True); tot += c; n += 30
print('длины SORTED: ', end='')
for k in (0, 1, 2, 10, 1000, 2000, 4000, 4095):
    a = sorted(r.randint(0, 10**9) for _ in range(k)); t = time.time(); x = ask('SORTED '+' '.join(map(str, a)))
    a2 = a[:]; y = 'н/д'
    if k > 1: a2[-1], a2[-2] = a2[-2]-1, a2[-1]; y = ask('SORTED '+' '.join(map(str, a2)))
    print(f"{k}: да={x}, нарушен конец={y}, {(time.time()-t)*1000:.0f}мс;", end=' ', flush=True); tot += x == '1'; n += 1
print()
print('формула в PROG:', ask('PROG'), [f.write(l+'\n') for l in ('SET R0 0', 'SET R1 5', 'SDIV R1', 'PRINT R1', 'HALT')] and '', (f.flush(), ask('END'))[1], ask('RUN'), f.readline().strip())
print('Старое:', [ask(q) for q in ('FIB 50', 'MUL 6 7', '2+3*(4-1)^2', 'TRIB 20', 'CATALAN(5)+1')]); print('Запрет:', ask('DEF ALL(a) = 1'), ask('DEF SORTED(a) = 1'))
print('сумма после', ask('@HASH')); print(f"ИТОГО {tot}/{n}"); p.kill()
