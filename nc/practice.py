"""Практика: сеть сама решает тренировочные задачи и учится выбирать навык по примерам."""
import math, random, sys, json, argparse, struct, time, numpy as np, torch, torch.nn.functional as F, inspect, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tests'))
import lessons
from functools import lru_cache
def isp(n):
    if n < 2: return 0
    i = 2
    while i*i <= n:
        if n % i == 0: return 0
        i += 1
    return 1
PR = [p for p in range(2, 9000) if isp(p)]
def collatz(n):
    c = 0
    while n != 1: n = n//2 if n % 2 == 0 else 3*n+1; c += 1
    return c
@lru_cache(None)
def phi(n): return sum(math.gcd(i, n) == 1 for i in range(1, n+1))
def fib(n):
    a, b = 0, 1
    for _ in range(n): a, b = b, a+b
    return a
BI = {'ABS': (1, abs, 3000), 'MIN': (2, min, 3000), 'MAX': (2, max, 3000), 'POW': (2, lambda a, b: a**b if b <= 40 else None, 60), 'GCD': (2, math.gcd, 3000), 'LCM': (2, math.lcm, 3000),
      'FACT': (1, math.factorial, 20), 'FIB': (1, fib, 90), 'ISQRT': (1, math.isqrt, 10**6), 'PRIME': (1, isp, 3000), 'NCR': (2, math.comb, 60), 'NPRIME': (1, lambda n: PR[n-1], 100),
      'PHI': (1, phi, 400), 'DIGSUM': (1, lambda n: sum(map(int, str(n))), 10**6), 'COLLATZ': (1, collatz, 3000), 'MODINV': (2, lambda a, b: pow(a, -1, b) if b > 1 and math.gcd(a, b) == 1 else None, 3000)}
for k, (ar, hi) in {'TRIB': (1, 60), 'SUMDIV': (1, 800), 'PERFECT': (1, 800), 'REVDIG': (1, 10**6), 'PALIN': (1, 10**6), 'DIVCOUNT': (1, 800), 'CATALAN': (1, 15), 'COPRIME': (2, 3000), 'PRIMEPI': (1, 200), 'SUMSQ': (1, 3000), 'BINOMSUM': (1, 25)}.items():
    # уроки вызывают NCR, GCD и другие встроенные навыки по именам
    fn = getattr(lessons, k); BI[k] = (ar, (lambda fn: lambda *a: int(fn(*a)))(fn), hi)
for k in ('NCR', 'GCD', 'PRIME'): setattr(lessons, k, BI[k][1])
NAMES = list(BI); ARGS = ['a', 'b', 'a-1', 'a+1', 'a*a', 'a+b', 'a*b', 'a-b', 'b-a']; FORMS = ['one', 'two', 'const', 'nest']; OPS = '+-*'
def arg(i, a, b): return (a, b, a-1, a+1, a*a, a+b, a*b, a-b, b-a)[i]
def call(n, x, y):
    ar, f, hi = BI[n]
    if x < 1 or x > hi or (ar == 2 and (y < 1 or y > hi)): return None
    try: return f(x) if ar == 1 else f(x, y)
    except Exception: return None
def plan_val(p, a, b):
    form, f, x, y, g, gx, gy, op, c = p
    u = call(f, arg(x, a, b), arg(y, a, b))
    if u is None or abs(u) > 1 << 61: return None
    if form == 0: return u
    if form == 2: return u+c if op == 0 else u-c if op == 1 else u*c
    if form == 3: return call(g, u, 0) if BI[g][0] == 1 else None
    v = call(g, arg(gx, a, b), arg(gy, a, b))
    if v is None or abs(v) > 1 << 61: return None
    return u+v if op == 0 else u-v if op == 1 else u*v
def plan_text(p):
    form, f, x, y, g, gx, gy, op, c = p
    def t(n, x, y): return f"{n}({ARGS[x]})" if BI[n][0] == 1 else f"{n}({ARGS[x]},{ARGS[y]})"
    u = t(f, x, y)
    return u if form == 0 else f"({u}){OPS[op]}{c}" if form == 2 else f"{g}({u})" if form == 3 else f"({u}){OPS[op]}({t(g, gx, gy)})"
def sample_plan(r, names, nv):
    form = r.choices([0, 1, 2, 3], [.4, .2, .2, .2])[0]; pool = range(2) if r.random() < .75 else range(9)
    pick = lambda: [c for c in pool if nv == 2 or ARGS[c].find('b') < 0]
    x = r.choice(pick()); y = r.choice(pick()); f = r.choice(names)
    if nv == 1 and BI[f][0] == 2: y = r.choice(pick())
    g = r.choice([n for n in names if form != 3 or BI[n][0] == 1]); gx = r.choice(pick()); gy = r.choice(pick())
    return (form, f, x, y, g, gx, gy, r.randrange(3), r.randint(1, 12))
def inputs(p, r, nv):
    hi = r.choice([12, 30, 60, 150, 600])
    a = r.randint(1, hi); return (a, r.randint(1, hi) if nv == 2 else 0)
def make_task(r, names, hold):
    for _ in range(300):
        nv = r.choice([1, 1, 2]); p = sample_plan(r, names, nv)
        if hold(p): continue
        ex = []
        for _ in range(60):
            a, b = inputs(p, r, nv); v = plan_val(p, a, b)
            if v is not None: ex.append((a, b, v))
            if len(ex) == 5: break
        if len(ex) == 5 and len({e[2] for e in ex}) >= 2: return p, nv, ex
    return None
def sqr(n): return n >= 0 and math.isqrt(n)**2 == n
def feats(ex, nv):
    """ex: четыре примера (a,b,r). Должно совпадать с features в runtime/plan.h."""
    ex = sorted(ex, key=lambda e: (e[0], e[1])); f = []
    while len(ex) < 4: ex = ex + [ex[-1]]
    for a, b, r in ex[:4]:
        la, lb, lr = math.log1p(abs(a)), math.log1p(abs(b)), math.log1p(abs(r)); ar = abs(r)
        f += [lr/10, (lr-la)/5, (lr-lb)/5, lr/(la+1)/3, r == a, r == b, r == 0, r == 1, r % 2, r % 3 == 0, r < a, r < b, r > a*b, a != 0 and r % a == 0, b != 0 and r % b == 0,
              r != 0 and a % r == 0, r != 0 and b % r == 0, sqr(ar), ar < 10, r < 0, ar < 1 << 30 and isp(ar)]
    lr = [math.log1p(abs(e[2])) for e in ex[:4]]; la = [math.log1p(abs(e[0])) for e in ex[:4]]
    f += [nv == 2, all(lr[i] <= lr[i+1] for i in range(3)), (lr[3]-lr[0])/(la[3]-la[0]+.1)/3, (lr[3]-lr[0])/(ex[3][0]-ex[0][0]+1), len({e[2] for e in ex[:4]})/4, max(lr)/10]
    return [float(v) for v in f]
def dataset(N, names, hold, seed):
    r = random.Random(seed); X = []; L = []
    while len(X) < N:
        t = make_task(r, names, hold)
        if t is None: continue
        p, nv, ex = t; X.append(feats(ex[:4], nv)); L.append(p)
    return torch.tensor(X, dtype=torch.float32), L
def labels(L, names):
    ix = {n: i for i, n in enumerate(names)}; n = len(L); S = torch.zeros(n, len(names)); h = torch.zeros(n, 6, dtype=torch.long)
    for i, (form, f, x, y, g, gx, gy, op, c) in enumerate(L):
        S[i, ix[f]] = 1
        if form in (1, 3): S[i, ix[g]] = 1
        h[i] = torch.tensor([form, x, y, op, c-1, gx])
    return S, h
HEADS = [4, 9, 9, 3, 12, 9]
K = 8
class Net:
    def __init__(s, d, out, mode):
        s.m = mode; s.geo = mode != 'mlp'; s.two = mode == 'hyper'; n = 48; s.d = d; s.out = out
        s.W = (torch.randn(n, d)/d**.5).requires_grad_(); s.b = torch.zeros(n).requires_grad_(); s.P = (torch.randn(K, d)/d**.5).requires_grad_(); s.Q = (torch.randn(n, K)*.05).requires_grad_()
        s.O = (torch.randn(out, n)*.02).requires_grad_(); s.c = torch.zeros(out).requires_grad_(); s.e = 0
    def ps(s): return [s.W, s.b, s.O, s.c] + ([s.P, s.Q] if s.geo else []) + ([s.H, s.th, s.C] if s.e else [])
    def fig(s, x):
        f = x @ s.W.T + s.b
        if s.geo: f = f + (x @ s.P.T).pow(2) @ s.Q.T
        return F.relu(f)
    def __call__(s, x):
        a = s.fig(x)
        if s.e: a = s.fig(x + F.relu(a @ (s.H*s.M) - s.th) @ s.C)
        return a @ s.O.T + s.c
    def grow(s, m, x, l):
        with torch.no_grad():
            idx = l.topk(m).indices; ce = x[idx]; n, d = s.W.shape
            s.W = torch.cat([s.W.detach(), ce*.3+torch.randn(m, d)*.02]).requires_grad_(); s.b = torch.cat([s.b.detach(), -torch.ones(m)*.2]).requires_grad_(); s.Q = torch.cat([s.Q.detach(), torch.randn(m, K)*.02]).requires_grad_()
            s.O = torch.cat([s.O.detach(), torch.randn(s.out, m)*.02], 1).requires_grad_()
            if s.e: s.M = torch.cat([s.M, torch.zeros(m, s.e)]); s.H = torch.cat([s.H.detach(), torch.zeros(m, s.e)]).requires_grad_()
            if s.two:
                k = 32; a = s.fig(x[idx[:k]] if len(idx) >= k else x[idx]); k = len(a); t = a.topk(3, 1); M = torch.zeros(s.W.shape[0], k)
                for j in range(k): M[t.indices[j], j] = 1
                th = a.gather(1, t.indices).sum(1)*.6
                s.M = torch.cat([s.M, M], 1) if s.e else M; s.H = torch.cat([s.H.detach(), M.clone()], 1).requires_grad_() if s.e else M.clone().requires_grad_()
                s.th = torch.cat([s.th.detach(), th]).requires_grad_() if s.e else th.requires_grad_(); s.C = torch.cat([s.C.detach(), torch.zeros(k, d)]).requires_grad_() if s.e else torch.zeros(k, d).requires_grad_(); s.e += k
    def add_out(s, m):
        ns = s.out - sum(HEADS)
        s.O = torch.cat([s.O.detach()[:ns], torch.randn(m, s.O.shape[1])*.02, s.O.detach()[ns:]]).requires_grad_(); s.c = torch.cat([s.c.detach()[:ns], torch.full((m,), -2.), s.c.detach()[ns:]]).requires_grad_(); s.out += m
def loss(y, S, h, names, red='mean'):
    ns = len(names); l = F.binary_cross_entropy_with_logits(y[:, :ns], S, reduction='none').sum(1); o = ns
    for i, c in enumerate(HEADS):
        t = h[:, i]; ce = F.cross_entropy(y[:, o:o+c], t, reduction='none'); form = h[:, 0]; o += c
        if i in (3,): ce = ce*(form != 0).float()*(form != 3).float()
        if i == 4: ce = ce*(form == 2).float()
        if i == 5: ce = ce*(form == 1).float()
        l = l + ce*.5
    return l.mean() if red == 'mean' else l
def top1(net, X, S, names):
    with torch.no_grad():
        y = net(X); ns = len(names); t = y[:, :ns].argmax(1); return S[torch.arange(len(X)), t].float().mean().item()
def fit(net, X, S, h, names, Xv, Sv, hv, rounds, steps, log):
    best = 1e9; stall = 0
    for g in range(rounds):
        o = torch.optim.Adam(net.ps(), 2e-3)
        for s in range(steps):
            i = torch.randint(0, len(X), (512,)); o.zero_grad(); loss(net(X[i]), S[i], h[i], names).backward(); o.step()
        with torch.no_grad(): v = loss(net(Xv), Sv, hv, names).item()
        acc = top1(net, Xv, Sv, names); print(f"   нейронов {net.W.shape[0]}, рёбер {net.e}, ошибка {v:.3f}, первый навык верен {acc*100:.1f}%", flush=True); log.append(acc)
        stall = stall+1 if v > best*.995 else 0
        if stall >= 2: break
        best = min(best, v)
        with torch.no_grad(): l = loss(net(X[:6000]), S[:6000], h[:6000], names, 'none')
        net.grow(32, X[:6000], l)
def export(net, names, path):
    with open(path, 'wb') as f:
        f.write(struct.pack('<4sIIII', b'NCPL', net.d, net.W.shape[0], K, len(names)))
        for n in names: f.write(n.encode().ljust(16, b'\0'))
        for t in (net.W, net.b, net.P, net.Q if net.geo else net.Q*0, net.O, net.c): f.write(t.detach().reshape(-1).numpy().astype('<f4').tobytes())
def hold(p):
    """Скрытые сочетания: 20% пар навыков, эти пары сеть не встречает на практике."""
    return p[0] in (1, 3) and hash_pair(p[1], p[4]) % 5 == 0
def hash_pair(a, b): return sum(ord(c)*(i+1) for i, c in enumerate(''.join(sorted((a, b)))))
if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--mode', default='geo'); ap.add_argument('--n', type=int, default=120000); ap.add_argument('--seed', type=int, default=1); ap.add_argument('--out', default='../models/planner.bin'); a = ap.parse_args()
    torch.set_num_threads(1); torch.manual_seed(a.seed); late = ['PERFECT', 'SUMSQ', 'TRIB']; names = [n for n in NAMES if n not in late]; log = []; t0 = time.time()
    X, L_ = dataset(a.n, names, hold, a.seed); S, h = labels(L_, names); Xv, Lv = dataset(4000, names, hold, 999); Sv, hv = labels(Lv, names); print('задач', len(X), round(time.time()-t0), flush=True)
    net = Net(X.shape[1], len(names)+sum(HEADS), a.mode); fit(net, X, S, h, names, Xv, Sv, hv, 12, 1500, log)
    print('== новый навык: короткая практика', late, flush=True)
    full = names + late; net.add_out(len(late))
    new = lambda p: p[1] in late or p[4] in late
    Xn, Ln = dataset(a.n//6, full, lambda p: hold(p) or not new(p), a.seed+1); Xo, Lo = dataset(a.n//6, names, hold, a.seed+2)
    X2 = torch.cat([Xn, Xo]); S2, h2 = labels(Ln+Lo, full); Xv2, Lv2 = dataset(3000, full, lambda p: hold(p) or not new(p), 998); Sv2, hv2 = labels(Lv2, full)
    fit(net, X2, S2, h2, full, Xv2, Sv2, hv2, 3, 800, log); print('старые задачи после новых:', f"{top1(net, Xv, labels(Lv, full)[0], full)*100:.1f}%")
    Xh, Lh = dataset(3000, full, lambda p: not (p[0] in (1, 3) and hold(p)), 997); print('скрытые пары:', f"{top1(net, Xh, labels(Lh, full)[0], full)*100:.1f}%", 'время', round(time.time()-t0))
    export(net, full, a.out + ('' if a.mode == 'geo' else '.'+a.mode)); json.dump(log, open(a.out+'.'+a.mode+'.json', 'w'))
