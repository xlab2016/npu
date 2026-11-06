"""Обучение растущей сети: нейрон с квадрикой на общих осях, рост ширины и глубины, этапы с повторением старого."""
import sys, json, time, random, argparse, struct, torch, torch.nn.functional as F
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from machine import *
import curriculum as cu
torch.set_num_threads(2)
K = 8
class Net:
    def __init__(s, geo=True):
        s.geo = geo; s.O0 = torch.zeros(WORD_BITS, D_IN).requires_grad_(); s.b0 = torch.zeros(WORD_BITS).requires_grad_()
        s.L = []; s.layer(12, D_IN)
    def layer(s, n, d):
        s.L.append(dict(W=(torch.randn(n,d)*.3).requires_grad_(), b=torch.zeros(n).requires_grad_(), P=(torch.randn(K,d)*.1).requires_grad_(),
                        Q=(torch.randn(n,K)*.05).requires_grad_(), O=torch.zeros(WORD_BITS,n).requires_grad_()))
    def params(s):
        p = [s.O0, s.b0]
        for l in s.L: p += [l['W'], l['b'], l['O']] + ([l['P'], l['Q']] if s.geo else [])
        return p
    def __call__(s, x):
        y = s.b0 + x @ s.O0.T; h = None
        for l in s.L:
            i = x if h is None else torch.cat([x, h], 1)
            f = i @ l['W'].T + l['b']
            if s.geo: f = f + (i @ l['P'].T).pow(2) @ l['Q'].T
            h = F.relu(f); y = y + h @ l['O'].T
        return y
    def size(s): return [l['W'].shape[0] for l in s.L]
    def patch(s, xs, ms, ys, logits):
        """Новые нейроны садятся прямо на ошибочные состояния: фигура выделяет такой вход, выход чинит нужные биты."""
        l = s.L[0]; n, d = l['W'].shape; m = len(xs); a = 2.
        W = torch.zeros(m, d); W[:, :D_IN] = a * xs * ms
        b = -a * (ms.sum(1) - 1); O = torch.zeros(WORD_BITS, m)
        t = ys * 2 - 1
        fix = (t * logits < 2).float() * (2 + (t * logits).clamp(max=2).neg() + 2) * t
        O = (fix / a).T
        for k, v, dm in (('W', W, 0), ('b', b, 0), ('O', O, 1)):
            l[k] = torch.cat([l[k].detach(), v], dm).requires_grad_()
        l['Q'] = torch.cat([l['Q'].detach(), torch.zeros(m, K)], 0).requires_grad_()
        if len(s.L) > 1:     # следующий слой получает новые входы с нулевым весом
            nx = s.L[1]; c, dd = nx['W'].shape
            nx['W'] = torch.cat([nx['W'].detach(), torch.zeros(c, m)], 1).requires_grad_()
            nx['P'] = torch.cat([nx['P'].detach(), torch.zeros(K, m)], 1).requires_grad_()
    def keep(s, li, idx):
        l = s.L[li]
        for k in 'WbQ': l[k] = l[k].detach()[idx].requires_grad_()
        l['O'] = l['O'].detach()[:, idx].requires_grad_()
        if li + 1 < len(s.L):
            n = s.L[li+1]; dropped = torch.cat([torch.arange(D_IN), D_IN + idx])
            n['W'] = n['W'].detach()[:, dropped].requires_grad_(); n['P'] = n['P'].detach()[:, dropped].requires_grad_()

def collect(rows, stage, n, seed, names, data):
    r = random.Random(seed); added = 0; cu.STAGE = stage
    def hook(pc, f, w):
        nonlocal added
        R = rows[pc]; key = (pc,) + tuple(f[d] for d in R.dims[PC_BITS:])
        if key not in data['rows']:
            data['rows'][key] = (f, R.dims, word(*w), stage); added += 1
    for i in range(n):
        k = r.choice(cu.S[stage]); t = cu.line(r, k, names) + '\n'
        if r.random() < .05: t = t.replace('\n', '\r\n')
        if r.random() < .12: t = t.lower()
        m = Machine(rows, t.encode()); m.run(limit=300000, hook=hook)
    # полнота: строка зависит только от своих битов, поэтому каждая встреченная строка учится на всех их значениях
    m = Machine(rows); done = data.setdefault('full', set())
    for pc in sorted({k[0] for k in data['rows']} - done):
        done.add(pc); R = rows[pc]; ext = R.dims[PC_BITS:]; m.pc = pc
        for v in range(1 << len(ext)):
            f = m.__class__.feat(m); f = [(pc >> i) & 1 if i < PC_BITS else 0 for i in range(D_IN)]
            c = 0
            for j, d in enumerate(ext):
                f[d] = (v >> j) & 1
                if D_C <= d < D_C + 8: c |= f[d] << (d - D_C)
            m.C = c; key = (pc,) + tuple(f[d] for d in ext)
            if key not in data['rows']:
                data['rows'][key] = (f, R.dims, word(*m.teach(f)), stage); added += 1
    return added
def tensors(data):
    v = list(data['rows'].values()); X = torch.tensor([a[0] for a in v]).float() * 2 - 1; M = torch.zeros(len(v), D_IN)
    for i, a in enumerate(v): M[i, a[1]] = 1
    Y = torch.tensor([[(a[2] >> b) & 1 for b in range(WORD_BITS)] for a in v]).float()
    return X, M, Y, torch.tensor([a[3] for a in v])
def noisy(X, M, c=1):
    X = X.repeat(c, 1); M = M.repeat(c, 1)
    return X * M + (torch.randint(0, 2, X.shape).float() * 2 - 1) * (1 - M)
def errors(net, X, M, Y, c=8):
    with torch.no_grad():
        bad = torch.zeros(len(X), dtype=torch.bool)
        for _ in range(c):
            bad |= ((net(noisy(X, M)) > 0).float() != Y).any(1)
    return bad
def fit(net, X, M, Y, steps, lr):
    o = torch.optim.Adam(net.params(), lr); N = len(X)
    for i in range(steps):
        idx = torch.randint(0, N, (min(N, 4096),)); x = noisy(X[idx], M[idx])
        o.zero_grad(); l = F.binary_cross_entropy_with_logits(net(x), Y[idx]); l.backward(); o.step()
    return l.item()
def solve(net, X, M, Y, log, stage, t0):
    best, stall, grow = 10**9, 0, 0
    for rnd in range(400):
        l = fit(net, X, M, Y, 150, 2e-3 if rnd % 4 else 1e-3)
        bad = errors(net, X, M, Y); e = int(bad.sum())
        log.append(dict(stage=stage, t=round(time.time()-t0,1), err=e, rows=len(X), neurons=sum(net.size()), layers=len(net.L)))
        print(f"  этап {stage} раунд {rnd}: ошибок {e}/{len(X)}, нейроны {net.size()}, loss {l:.4f}, {time.time()-t0:.0f}с", flush=True)
        if e == 0: return True
        if e < best * .8: best, stall = e, 0
        else: stall += 1
        if stall >= 1:
            grow += 1; stall = 0; best = 10**9
            if grow % 6 == 0 and len(net.L) < 3:
                net.layer(16, D_IN + net.size()[-1]); print('  рост: новый слой', flush=True)
            else:
                i = bad.nonzero()[:, 0]; i = i[torch.randperm(len(i))[:128]]
                x = X[i] * M[i]
                with torch.no_grad(): lg = net(x)
                net.patch(X[i], M[i], Y[i], lg); print(f"  рост: +{len(i)} нейронов", flush=True)
    return False
def polish(net, X, M, Y, log, st, t0):
    """Доводка: малый шаг и проверка на 64 случайных шумах для каждого состояния, при застое снова рост."""
    for r in range(60):
        fit(net, X, M, Y, 400, 2e-4 if r % 2 else 1e-4); bad = errors(net, X, M, Y, 64); e = int(bad.sum())
        print(f"  доводка {r}: ошибок {e}, нейроны {net.size()}", flush=True)
        if e == 0: return 0
        if r % 3 == 2:
            i = bad.nonzero()[:, 0][:32]
            with torch.no_grad(): lg = net(X[i] * M[i])
            net.patch(X[i], M[i], Y[i], lg)
    return e
def prune(net, X, M, Y):
    with torch.no_grad():
        for li in range(len(net.L)):
            x = noisy(X, M, 4); h = None
            for j, l in enumerate(net.L[:li+1]):
                i = x if h is None else torch.cat([x, h], 1)
                f = i @ l['W'].T + l['b']
                if net.geo: f = f + (i @ l['P'].T).pow(2) @ l['Q'].T
                h = F.relu(f)
            l = net.L[li]; imp = h.max(0).values * l['O'].abs().max(0).values
            idx = (imp > 1e-3).nonzero()[:, 0]
            if len(idx) < len(imp): net.keep(li, idx)
def export(net, path):
    with open(path, 'wb') as f:
        f.write(struct.pack('<4sIIIII', b'NCP1', D_IN, WORD_BITS, K, len(net.L), int(net.geo)))
        for t in (net.b0, net.O0.reshape(-1)): f.write(t.detach().numpy().astype('<f4').tobytes())
        d = D_IN
        for l in net.L:
            n, d = l['W'].shape; f.write(struct.pack('<II', n, d))
            for k in ('W', 'b', 'P', 'Q', 'O'): f.write((l[k].detach() * (0 if k == 'Q' and not net.geo else 1)).reshape(-1).numpy().astype('<f4').tobytes())
def snapshot(net): return [net.O0.detach().clone(), net.b0.detach().clone()], [{k: v.detach().clone() for k, v in l.items()} for l in net.L]
def restore(net, sn):
    net.O0, net.b0 = sn[0][0].clone().requires_grad_(), sn[0][1].clone().requires_grad_()
    net.L = [{k: v.clone().requires_grad_() for k, v in l.items()} for l in sn[1]]
def importance(net, X, M):
    out = []
    with torch.no_grad():
        x = noisy(X, M, 4); h = None
        for l in net.L:
            i = x if h is None else torch.cat([x, h], 1)
            f = i @ l['W'].T + l['b']
            if net.geo: f = f + (i @ l['P'].T).pow(2) @ l['Q'].T
            h = F.relu(f); out.append((h > 0).float().mean(0).sqrt() * h.max(0).values * l['O'].norm(dim=0))
    return out
def compress(net, X, M, Y, log, t0):
    """Сон сети: убираем слабые нейроны и дообучаем; если без них не выходит, откатываемся и берём шаг меньше."""
    frac, fails = .15, 0
    while frac > .01 and time.time() - t0 < a.budget:
        sn = snapshot(net); imp = importance(net, X, M)
        all_i = torch.cat(imp); thr = all_i.kthvalue(max(1, int(len(all_i) * frac))).values
        for li in reversed(range(len(net.L))):
            idx = (imp[li] > thr).nonzero()[:, 0]
            if len(idx) < 4: idx = imp[li].topk(min(4, len(imp[li]))).indices.sort().values
            net.keep(li, idx)
        ok = False
        for r in range(10):
            fit(net, X, M, Y, 300, 1e-3 if r < 6 else 2e-4)
            if int(errors(net, X, M, Y, 8).sum()) == 0 and int(errors(net, X, M, Y, 64).sum()) == 0: ok = True; break
        print(f"  сжатие frac {frac:.3f}: {'да' if ok else 'нет'} нейроны {net.size()} {time.time()-t0:.0f}с", flush=True)
        if ok:
            log.append(dict(stage=5, t=round(time.time()-t0,1), err=0, rows=len(X), neurons=sum(net.size()), layers=len(net.L)))
        else: restore(net, sn); frac /= 2
if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--mlp', action='store_true'); ap.add_argument('--out', default='../models/nc.bin')
    ap.add_argument('--nocompress', action='store_true'); ap.add_argument('--dry', action='store_true'); ap.add_argument('--budget', type=float, default=1500); ap.add_argument('--samples', type=int, default=4000); ap.add_argument('--seed', type=int, default=1); a = ap.parse_args()
    torch.manual_seed(a.seed); rows, lab = assemble(); names = list(CMDS) + list(DIRECT)
    net = Net(geo=not a.mlp); data = dict(rows={}); log = []; t0 = time.time(); summary = []
    for st in (1, 2, 3, 4):
        added = collect(rows, st, a.samples, a.seed*100+st, names, data); X, M, Y, S = tensors(data)
        cov = {k[0] for k in data['rows']}; print(f"этап {st}: новых состояний {added}, всего {len(X)}, строк покрыто {len(cov)}/{len(rows)}", flush=True)
        if st == 4:
            seen = {(k[0], (v[2] >> 17)) for k, v in data['rows'].items()}; miss = []
            for i, q in enumerate(rows):
                if q.op == OPI['RET']: continue
                arcs = [c[-1] for c in q.conds]
                if not any(c[0] == 'else' for c in q.conds): arcs.append(i + 1)
                miss += [(i, q.src[:40], t) for t in arcs if (i, t) not in seen]
            print('непройденные переходы:', len(miss), sorted(set(miss))[:30], flush=True)
            if a.dry: sys.exit()
        if a.dry: continue
        ok = solve(net, X, M, Y, log, st, t0)
        prune(net, X, M, Y); e = polish(net, X, M, Y, log, st, t0)
        summary.append(dict(stage=st, states=len(X), new=added, neurons=net.size(), err=e, seconds=round(time.time()-t0)))
        print('ИТОГ', summary[-1], flush=True)
        export(net, a.out + f'.s{st}')
    if not a.nocompress: compress(net, X, M, Y, log, t0)
    summary.append(dict(stage='сжатие', states=len(X), neurons=net.size(), err=int(errors(net, X, M, Y, 128).sum()), seconds=round(time.time()-t0)))
    print('ИТОГ', summary[-1], flush=True)
    export(net, a.out); json.dump(dict(summary=summary, log=log), open(a.out + '.json', 'w'), ensure_ascii=False)
