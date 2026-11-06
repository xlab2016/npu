"""Доводка и проверка готовой модели: случайный шум плюс атака на нерелевантные входы (ищем худшую комбинацию)."""
import os, time, sys, struct, json, random, torch, numpy as np, torch.nn.functional as F
sys.path.insert(0, '.')
from machine import *
import train as T
from lockstep import load
sys.argv, out = sys.argv[:2], sys.argv[1]
rows, lab = assemble(); names = list(CMDS) + list(DIRECT)
data = dict(rows={})
STG = (1, 2, 3, 4, 5) if os.path.exists('found.uasm') else (1, 2, 3, 4)
for st in STG: T.collect(rows, st, 4000, 100 + st, names, data)
X, M, Y, S = T.tensors(data); print('состояний', len(X), flush=True)
b0, O0, L = load(out); net = T.Net(True)
net.b0 = torch.tensor(b0.copy()).requires_grad_(); net.O0 = torch.tensor(O0.copy()).requires_grad_(); net.L = []
for W, b, P, Q, O in L:
    net.L.append({k: torch.tensor(v.copy()).requires_grad_() for k, v in dict(W=W, b=b, P=P, Q=Q, O=O).items()})
ne = int(T.errors(net, X, M, Y, 4).sum()); print('ошибок до дообучения', ne, 'строк микрокода', len(rows), flush=True)
if ne: T.solve(net, X, M, Y, [], 5, time.time())
def attack(steps=6, restarts=2):
    bad = torch.zeros(len(X), dtype=torch.bool); adv = []
    for _ in range(restarts):
        x = T.noisy(X, M)
        for s in range(steps):
            x = x.detach().requires_grad_(); y = net(x); m = ((Y * 2 - 1) * y).min(1).values; g, = torch.autograd.grad(m.sum(), x)
            with torch.no_grad():
                bad |= m <= 0; x = torch.where(M > 0, X, -torch.sign(g) * (g != 0) + x * (g == 0))
        with torch.no_grad(): bad |= ((Y * 2 - 1) * net(x)).min(1).values <= 0
        adv.append(x.detach())
    return bad, adv
for r in range(200):
    bad, adv = attack(); e = int(bad.sum()); e2 = int(T.errors(net, X, M, Y, 256).sum())
    print(f"раунд {r}: атака {e}, случайный шум {e2}, нейроны {net.size()}", flush=True); T.export(net, out + '.hard')
    if e == 0 and e2 == 0: break
    o = torch.optim.Adam(net.params(), 2e-4 if r < 40 else 1e-4); hard = bad.nonzero()[:, 0]
    if r % 4 == 3 and len(hard):
        i = hard[:32]
        with torch.no_grad(): lg = net(adv[0][i])
        net.patch(X[i], M[i], Y[i], lg); o = torch.optim.Adam(net.params(), 2e-4)
    for s in range(300):
        idx = torch.randint(0, len(X), (2048,)); x = T.noisy(X[idx], M[idx])
        if len(hard):
            h = hard[torch.randint(0, len(hard), (512,))]; x = torch.cat([x, adv[r % 2][h]]); idx = torch.cat([idx, h])
        o.zero_grad(); F.binary_cross_entropy_with_logits(net(x), Y[idx]).backward(); o.step()
print('нейроны', net.size()); T.export(net, out)
