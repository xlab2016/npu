"""Открытие навыков только по примерам. Режимы: geo (геометрическая сеть), mlp, blind (без сети)."""
import sys, json, time, math, argparse, numpy as np, torch, torch.nn.functional as F, ctypes
from core import *
ap = argparse.ArgumentParser(); ap.add_argument('--mode', default='geo'); ap.add_argument('--budget', type=float, default=3e8); ap.add_argument('--rounds', type=int, default=5); ap.add_argument('--dreams', type=int, default=30000); ap.add_argument('--tasks', default=''); ap.add_argument('--maxb', type=float, default=0); ap.add_argument('--seed', type=int, default=1); ap.add_argument('--tag', default=''); a = ap.parse_args()
torch.set_num_threads(1); torch.manual_seed(a.seed); K = 8
class Guide:
    """geo: один проход. hyper: два прохода с рёбрами-гиперсвязями между фигурами. mlp: без квадрики."""
    TOPK = 3
    def __init__(s, d, out):
        s.geo = a.mode in ('geo', 'hyper'); s.hyper = a.mode == 'hyper'; n = 32; s.d = d
        s.W = (torch.randn(n, d)*.1).requires_grad_(); s.b = torch.zeros(n).requires_grad_(); s.P = (torch.randn(K, d)*.05).requires_grad_(); s.Q = (torch.randn(n, K)*.05).requires_grad_()
        s.O = torch.zeros(out, n).requires_grad_(); s.c = torch.full((out,), -1.).requires_grad_()
        s.M = torch.zeros(n, 0)                      # кто входит в ребро (разреженная маска, не обучается)
        s.H = torch.zeros(n, 0).requires_grad_(); s.th = torch.zeros(0).requires_grad_(); s.C = torch.zeros(0, d).requires_grad_()
    def ps(s): return [s.W, s.b, s.O, s.c] + ([s.P, s.Q] if s.geo else []) + ([s.H, s.th, s.C] if s.hyper else [])
    def figures(s, x):
        f = x @ s.W.T + s.b
        if s.geo: f = f + (x @ s.P.T).pow(2) @ s.Q.T
        return F.relu(f)
    def edges(s, a1): return F.relu(a1 @ (s.H * s.M) - s.th)      # ребро горит, когда активны его фигуры
    def __call__(s, x):
        a1 = s.figures(x)                                         # проход 1: активация фигур
        if not s.hyper or s.M.shape[1] == 0: return a1 @ s.O.T + s.c
        ctx = s.edges(a1) @ s.C                                   # контекст по рёбрам активных фигур
        return s.figures(x + ctx) @ s.O.T + s.c                   # проход 2: данные + контекст как residual
    def grow_edges(s, m, x, y):
        """Новые рёбра соединяют фигуры, совместно активные на самых трудных примерах. Контекст стартует с нуля."""
        with torch.no_grad():
            l = F.binary_cross_entropy_with_logits(s(x), y, reduction='none').mean(1); idx = l.topk(min(m, len(x))).indices
            a1 = s.figures(x[idx]); top = a1.topk(s.TOPK, 1); n = s.W.shape[0]; k = len(idx)
            M = torch.zeros(n, k); H = torch.zeros(n, k); M.scatter_(0, top.indices.T.reshape(s.TOPK, k)[0:0], 0.) if False else None
            for j in range(k):
                M[top.indices[j], j] = 1; H[top.indices[j], j] = 1
            th = (a1.gather(1, top.indices).sum(1) * .6)
        s.M = torch.cat([s.M, M], 1); s.H = torch.cat([s.H.detach(), H], 1).requires_grad_(); s.th = torch.cat([s.th.detach(), th]).requires_grad_(); s.C = torch.cat([s.C.detach(), torch.zeros(k, s.d)]).requires_grad_()
    def grow_n(s, m, x):
        ce = x[torch.randperm(len(x))[:m]]; W = ce*.15 + torch.randn(m, s.d)*.02
        s.W = torch.cat([s.W.detach(), W]).requires_grad_(); s.b = torch.cat([s.b.detach(), torch.zeros(m)]).requires_grad_()
        s.Q = torch.cat([s.Q.detach(), torch.randn(m, K)*.02]).requires_grad_(); s.O = torch.cat([s.O.detach(), torch.zeros(s.O.shape[0], m)], 1).requires_grad_()
        e = s.M.shape[1]; s.M = torch.cat([s.M, torch.zeros(m, e)]); s.H = torch.cat([s.H.detach(), torch.zeros(m, e)]).requires_grad_()
    def grow_out(s):
        s.O = torch.cat([s.O.detach(), torch.zeros(1, s.O.shape[1])]).requires_grad_(); s.c = torch.cat([s.c.detach(), torch.tensor([-1.])]).requires_grad_()
def dreams(N, nops, seed):
    L.rseed(seed); B = 20000; np_ = len(PROBES); ps = (Prog*B)(); out = np.zeros((B, np_), 'i8'); X, Y, seen = [], [], set()
    px = np.array([p[0] for p in PROBES], 'i8'); py = np.array([p[1] for p in PROBES], 'i8'); P = ctypes.POINTER(ctypes.c_int64)
    for _ in range(400):
        L.dream_batch(B, ps, out.ctypes.data_as(P), px.ctypes.data_as(P), py.ctypes.data_as(P), np_)
        NONE = 1 << 62; good = ((out != NONE).sum(1) >= 30) & (np.where(out == NONE, 0, out).min(1) >= 0) & (out.max(1) != out.min(1))
        for i in good.nonzero()[0]:
            r = out[i]; k = r.tobytes()
            if k in seen: continue
            o = [None if v == NONE else int(v) for v in r]
            if len({v for v in o if v is not None}) < 4: continue
            seen.add(k); X.append(features(o, int(i) % 3 == 0)); Y.append(tokens(ps[int(i)], nops))
        if len(X) >= N: break
    return torch.tensor(X[:N], dtype=torch.float32), torch.tensor(np.array(Y[:N]))
def train(g, X, Y, extra):
    n = len(X); nv = n//10; Xv, Yv = X[:nv], Y[:nv]; Xt, Yt = X[nv:], Y[nv:]; best = 9e9; stall = 0; out = []
    if extra: Xe = torch.tensor([e[0] for e in extra], dtype=torch.float32); Ye = torch.tensor(np.array([e[1] for e in extra]))
    for gr in range(10):
        o = torch.optim.Adam(g.ps(), 2e-3)
        for s in range(800):
            i = torch.randint(0, len(Xt), (256,)); x, y = Xt[i], Yt[i]
            if extra: x = torch.cat([x, Xe]); y = torch.cat([y, Ye])
            o.zero_grad(); F.binary_cross_entropy_with_logits(g(x), y).backward(); o.step()
        with torch.no_grad(): v = F.binary_cross_entropy_with_logits(g(Xv), Yv).item()
        print(f"   сеть: нейронов {g.W.shape[0]}, рёбер {g.M.shape[1]}, ошибка на новых программах {v:.4f}", flush=True)
        stall = stall + 1 if v > best*.997 else 0
        if stall >= 2: break
        best = min(best, v); g.grow_n(16, Xt)
        if g.hyper: g.grow_edges(16, Xt[:4000], Yt[:4000])
def weights(g, n, nops):
    o, un = probe_out(n)
    with torch.no_grad(): p = torch.sigmoid(g(torch.tensor([features(o, un)], dtype=torch.float32)))[0].numpy()
    p = np.clip(p, .02, .98)
    def norm(v): v = v/v.sum(); return list(-np.log2(v))
    return norm(p[:NG]), norm(p[2*NG:2*NG+NBASE+nops]), norm(p[NG:2*NG])
names = list(T) if not a.tasks else a.tasks.split(','); lib = []; progs = {}; ledger = []; todo = list(names); total = 0; t0 = time.time(); extra_tr = []; cegis = {n: [] for n in names}
g = None
for rnd in range(a.rounds):
    nops = len(lib); print(f"== круг {rnd}: библиотека {lib}", flush=True)
    if a.mode != 'blind':
        X, Y = dreams(a.dreams, nops, 7+rnd+100*a.seed); print(f"   случайных программ {len(X)}", flush=True)
        if g is None: g = Guide(X.shape[1], Y.shape[1])
        while g.O.shape[0] < Y.shape[1]: g.grow_out()
        ex = []
        for n, y in extra_tr:
            o, un = probe_out(n); yy = np.zeros(Y.shape[1], 'f4'); yy[:len(y)] = y; ex.append((features(o, un), yy))
        train(g, X, Y, ex)
    new = 0
    for n in list(todo):
        if a.mode == 'blind': u = math.log2; wg, wo, wl = [u(7)]*7, [u(10+nops)]*(10+nops), [u(7)]*7
        else: wg, wo, wl = weights(g, n, nops)
        spent = 0; tt = time.time(); res = None
        for attempt in range(4):
            ok, p, c, bits = do_search(n, wg, wo, wl, int(a.budget), cegis[n]); spent += c
            if not ok: break
            bad = verify(n, p)
            if bad is None: res = p; break
            cegis[n].append(bad); print(f"   {n}: нашлась неверная программа, контрпример {bad}", flush=True)
        total += spent; ledger.append(dict(round=rnd, task=n, cand=spent, solved=res is not None, sec=round(time.time()-tt, 1)))
        if res is not None:
            pr = Prog.from_buffer_copy(res); txt = show(pr, lib); print(f"   НАЙДЕНО {n}: {spent:.3g} кандидатов, {time.time()-tt:.1f}с  {txt}", flush=True)
            lib_add(pr, T[n][1]); lib.append(n); progs[n] = dict(text=txt, round=rnd, cand=spent, raw=bytes(pr).hex(), arity=T[n][1]); todo.remove(n); new += 1; nops = len(lib)
            extra_tr.append((n, tokens(pr, len(lib))))
            if a.mode != 'blind' and g.O.shape[0] < 2*NG+NBASE+nops:
                g.grow_out()
            if a.mode != 'blind': pass
        else: print(f"   нет {n}: {spent:.3g}", flush=True)
    if not todo: break
    if new == 0:
        if a.budget >= a.maxb: break
        a.budget *= 4
print('ИТОГ', a.mode, 'найдено', len(progs), 'из', len(names), 'кандидатов', f"{total:.3g}", 'время', round(time.time()-t0), 'не найдено', todo, flush=True)
json.dump(dict(mode=a.mode, solved=progs, ledger=ledger, total=total, unsolved=todo, neurons=int(g.W.shape[0]) if g else 0, edges=int(g.M.shape[1]) if g else 0, sec=round(time.time()-t0)), open(f'{a.mode}{a.tag}.json', 'w'), ensure_ascii=False, indent=1)
