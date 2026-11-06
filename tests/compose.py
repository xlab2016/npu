"""Заморозка и новые навыки как формулы. Веса проверяются контрольной суммой, ответы независимым эталоном."""
import sys, math, random, socket, subprocess, time, json, statistics
sys.path.insert(0, 'nc'); import practice as P
def serve(port, plan=True):
    a = ['./nc_bin', '--model', 'models/nc2.bin', '--mem', 'models/skills.mem', '--tcp', str(port), '--noexp'] + (['--planner', 'models/planner.bin'] if plan else [])
    p = subprocess.Popen(a, stderr=subprocess.DEVNULL)
    for _ in range(200):
        try: s = socket.create_connection(('127.0.0.1', port)); break
        except OSError: time.sleep(.05)
    s.settimeout(300); f = s.makefile('rw', newline='\n')
    def ask(l): f.write(l+'\n'); f.flush(); return f.readline().strip()
    return p, ask
B = {k: v[1] for k, v in P.BI.items()}; r = random.Random(2026)
p, ask = serve(17841); h0 = ask('@FREEZE'); print('сумма весов до', h0)
# 1. формулы и цепочки шагов
D = [('DEF K1(a) = FIB(a)+DIGSUM(a)', 'K1', lambda a: B['FIB'](a)+B['DIGSUM'](a), 1, 60),
     ('DEF K2(a,b) = t = GCD(a,b); u = LCM(a,b); t+u*2', 'K2', lambda a, b: math.gcd(a, b)+2*math.lcm(a, b), 2, 500),
     ('DEF K3(a) = s = SUMDIV(a); d = DIVCOUNT(a); s*d-a', 'K3', lambda a: B['SUMDIV'](a)*B['DIVCOUNT'](a)-a, 1, 300),
     ('DEF K4(a) = K1(a)*2+K3(a)', 'K4', lambda a: 2*(B['FIB'](a)+B['DIGSUM'](a))+B['SUMDIV'](a)*B['DIVCOUNT'](a)-a, 1, 60),
     ('DEF K5(a,b) = K2(K1(a),b)+K4(b)', 'K5', lambda a, b: (lambda x: math.gcd(x, b)+2*math.lcm(x, b))(B['FIB'](a)+B['DIGSUM'](a))+2*(B['FIB'](b)+B['DIGSUM'](b))+B['SUMDIV'](b)*B['DIVCOUNT'](b)-b, 2, 30),
     ('DEF K6(a) = t = TRIB(a); u = REVDIG(t+1); u+CATALAN(a%10)', 'K6', lambda a: int(str(B['TRIB'](a)+1)[::-1])+B['CATALAN'](a % 10), 1, 40)]
ok = n = 0
for d, name, fn, ar, hi in D:
    print(' ', d, '->', ask(d)); c = 0
    for _ in range(60):
        x = [r.randint(1, hi) for _ in range(ar)]; c += ask(f"{name}({','.join(map(str, x))})") == str(fn(*x))
    c2 = 0
    for _ in range(20):
        x = [r.randint(1, hi) for _ in range(ar)]; c2 += ask(f"{name} {' '.join(map(str, x))}") == str(fn(*x))
    print(f"    {name}: выражение {c}/60, команда {c2}/20", flush=True); ok += c+c2; n += 80
print(f"Составные навыки: {ok}/{n}")
print('Запрет на изменение:', [ask(q) for q in ('DEF FIB(a) = 1', 'DEF K1(a) = 2', 'DEF PRIME(a) = a')], '| FIB 10 =', ask('FIB 10'), '| K1(5) =', ask('K1(5)'))
print('Попытка учителя перезаписать фигуру:', end=' ')
for l in open('models/skills.mem'):
    if l.startswith('F '):
        _, q, m, v, w = l.split(); ask(f"@F {q} {m} {v} 0\n@END"); break
print(ask('@HASH')); print('FIB 10 после неё:', ask('FIB 10'))
# 2. лестница: каждый новый навык опирается на прошлый, примеры без подсказки формулы
Lad = [lambda a: B['DIGSUM'](a)+1]
for k, f in enumerate([lambda u: u*2, lambda u: B['FIB'](u % 30+1), lambda u: u+3, lambda u: u*u, lambda u: B['DIGSUM'](u)+7]): pass
def seq(a):
    v = [B['DIGSUM'](a)+1]; v.append(B['FIB'](v[-1])); v.append(B['DIGSUM'](v[-1])+2); v.append(B['FIB'](v[-1])); v.append(B['DIGSUM'](v[-1])+3); v.append(v[-1]*5); return v
p2, ask2 = serve(17842); res = []
for lvl in range(6):
    xs = r.sample(range(1, 80), 8); ex = [(x, seq(x)[lvl]) for x in xs]; q = '? '+'; '.join(f"{a} = {v}" for a, v in ex[:7])+f"; {ex[7][0]}"
    g = ask(q); okk = g.split(' ')[0] == str(ex[7][1]); s = ask(f"SAVE L{lvl}") if 'НЕ' not in g else '-'; b = ask2(q); res.append((lvl+1, okk, g[:58], b[:30]))
    print(f"  уровень {lvl+1}: {g[:58]} | без лестницы: {b[:30]}", flush=True)
p2.kill()
# 3. выбор сетью составного навыка: веса планировщика не менялись
T = [(f"K{i}", D[i-1][2], D[i-1][3], D[i-1][4]) for i in (1, 2, 3, 6)]; tr = []
for _ in range(5):
    for nm, fn, ar, hi in T:
        xs = [tuple(r.randint(1, hi) for _ in range(ar)) for _ in range(5)]
        q = '? '+'; '.join(' '.join(map(str, x))+f" = {fn(*x)}" for x in xs[:4])+'; '+' '.join(map(str, xs[4])); g = ask(q); tr.append((nm, g.split(' ')[0] == str(fn(*xs[4])), g[:50]))
print('Сеть выбирает составной навык:', sum(x[1] for x in tr), '/', len(tr), tr[:4])
# 4. старое после всего
Q = [(n, a) for n, a in [('FIB', 50), ('FACT', 12), ('GCD 48', 18), ('ISQRT', 1000000), ('PRIME', 97), ('TRIB', 30), ('CATALAN', 10)]]
print('Старые навыки:', [ask(f"{n} {a}") for n, a in Q]); print('сумма весов после', ask('@HASH')); p.kill()
