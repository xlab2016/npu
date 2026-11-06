"""Верхний уровень. База учится один раз, потом замораживается. Новый навык обучает только свой выход."""
import sys, os, time, torch, torch.nn.functional as F, hashlib
sys.path.insert(0, '../nc'); import practice as P
BI = P.BI; BI['ISPRIME'] = BI.pop('PRIME')
for k in ('MODINV', 'TRIB', 'REVDIG', 'PALIN', 'DIVCOUNT', 'PRIMEPI', 'BINOMSUM'): del BI[k]
P.NAMES[:] = list(BI); late = ['PERFECT', 'CATALAN', 'SUMSQ']; names = [n for n in P.NAMES if n not in late]
torch.set_num_threads(2); torch.manual_seed(1); t0 = time.time()
X, L = P.dataset(90000, names, P.hold, 1); S, h = P.labels(L, names); Xv, Lv = P.dataset(3000, names, P.hold, 999); Sv, hv = P.labels(Lv, names)
net = P.Net(X.shape[1], len(names)+sum(P.HEADS), 'geo'); P.fit(net, X, S, h, names, Xv, Sv, hv, 12, 1500, [])
a0 = P.top1(net, Xv, Sv, names); old = [hashlib.sha256(t.detach().numpy().tobytes()).hexdigest() for t in (net.W, net.b, net.P, net.Q)]; ores = net.O.detach()[:len(names)].clone()
for nm in late:
    ns = net.out-sum(P.HEADS); full = names+[nm]; t = time.time()
    Xn, Ln = P.dataset(6000, full, lambda p: P.hold(p) or not (p[1] == nm or p[4] == nm), ns); Xo, Lo = P.dataset(6000, names, P.hold, ns+50); XX = torch.cat([Xn, Xo]); yy = torch.tensor([float(p[1] == nm or (p[0] in (1, 3) and p[4] == nm)) for p in Ln+Lo])
    with torch.no_grad(): H = net.fig(XX)
    w = torch.zeros(H.shape[1]).requires_grad_(); b = torch.tensor(-2.).requires_grad_(); o = torch.optim.Adam([w, b], 5e-3)
    for s in range(1500):
        i = torch.randint(0, len(XX), (512,)); o.zero_grad(); F.binary_cross_entropy_with_logits(H[i] @ w + b, yy[i]).backward(); o.step()
    net.O = torch.cat([net.O.detach()[:ns], w.detach()[None], net.O.detach()[ns:]]).requires_grad_(); net.c = torch.cat([net.c.detach()[:ns], b.detach()[None], net.c.detach()[ns:]]).requires_grad_(); net.out += 1; names = full
    print(f"выход {nm}: обучен за {time.time()-t:.1f}с, вся сеть ниже заморожена", flush=True)
same = old == [hashlib.sha256(t.detach().numpy().tobytes()).hexdigest() for t in (net.W, net.b, net.P, net.Q)] and bool((net.O.detach()[:len(ores)] == ores).all())
print('старые веса совпали:', same, f"база {a0*100:.1f}%, после новых выходов {P.top1(net, Xv, P.labels(Lv, names)[0], names)*100:.1f}%, нейронов {net.W.shape[0]}, {time.time()-t0:.0f}с")
P.export(net, names, 'planner.bin')
