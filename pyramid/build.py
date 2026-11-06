"""Пирамида: каждый навык своя сеть. Учится только новый навык, нижние не загружаются в обучение вовсе."""
import ast, inspect, hashlib, json, struct, sys, time, torch, torch.nn.functional as F
sys.path.insert(0, '.'); import lessons
torch.set_num_threads(2)
HW = ['and','or','xor','add','sub','shl','shr','lt','eq','load','const','mov','nop','ret','store','rx','tx','call','try','throw','bad','plan','txplan','rxnum','atoms','unary','txcombo','txnest','obs','dev','txop','txs','txf']   # настоящие инструкции
HI = {n: i for i, n in enumerate(HW)}
NREG = 16
PCB = 10
D_IN = PCB + 2*NREG           # адрес строки 10 бит, ноль и нечётность каждого регистра
class C:
    """Перевод показанного урока в строки: что делать и куда идти в зависимости от одного бита состояния."""
    def __init__(s, f, voc):
        s.t = ast.parse(inspect.getsource(f)).body[0]; s.voc = voc; s.reg = {a.arg: i for i, a in enumerate(s.t.args.args)}; s.ar = len(s.reg)
        s.rows = []; s.k = []; s.tmp = 0; s.lab = {}; s.nl = 0
    def r(s, v):
        if v not in s.reg: s.reg[v] = len(s.reg); assert len(s.reg) <= NREG-6, v
        return s.reg[v]
    def t_(s):
        s.tmp += 1; assert s.tmp <= 6, s.t.name; return NREG-7+s.tmp
    def row(s, op, d=0, a=0, b=0, c=0, e=0, k=0, cond=None, to=None): s.rows.append(dict(op=op, d=d, a=a, b=b, c=c, e=e, k=k, cond=cond, to=to)); return len(s.rows)-1
    def konst(s, v, d):
        if v not in s.k: s.k.append(v)
        s.row(HI['const'], d, k=s.k.index(v))
    def val(s, n, want=None):
        if isinstance(n, ast.Name):
            if n.id in s.voc:
                d = s.t_() if want is None else want; s.konst(s.voc[n.id]-len(HW), d); return d
            return s.r(n.id)
        d = s.t_() if want is None else want
        if isinstance(n, ast.Constant): s.konst(int(n.value), d); return d
        if isinstance(n, ast.UnaryOp): raise SyntaxError('минус')
        if isinstance(n, ast.Call):
            f = n.func.id; sv = s.tmp; kk = 0
            if f == '_try':
                v = n.args[-1].value
                if v not in s.k: s.k.append(v)
                kk = s.k.index(v); n = ast.Call(n.func, n.args[:-1], [])
            a = [s.val(x) for x in n.args]+[0, 0, 0, 0]; s.tmp = sv
            s.row(HI[f[1:]] if f[0] == '_' else s.voc[f], d, a[0], a[1], a[2], a[3], k=kk); return d
        raise SyntaxError(ast.dump(n))
    def lb(s): s.nl += 1; return s.nl
    def jump(s, cond, l): s.row(HI['nop'], cond=cond, to=l)
    def test(s, n, false):
        """В ложном случае перейти на метку false."""
        sv = s.tmp
        if isinstance(n, ast.BoolOp):
            if isinstance(n.op, ast.And):
                for v in n.values: s.test(v, false)
            else:
                ok = s.lb()
                for v in n.values[:-1]:
                    nx = s.lb(); s.test(v, nx); s.jump(None, ok); s.lab[nx] = len(s.rows)
                s.test(n.values[-1], false); s.lab[ok] = len(s.rows)
            return
        if isinstance(n, ast.Constant): return
        if isinstance(n, ast.Compare):
            r = s.val(n.left); o = type(n.ops[0]).__name__; assert n.comparators[0].value == 0
            s.jump(('z', r, 0 if o == 'Eq' else 1), false)
        elif isinstance(n, ast.UnaryOp):
            
            ok = s.lb(); s.test(n.operand, ok); s.jump(None, false); s.lab[ok] = len(s.rows)
        elif isinstance(n, ast.Call) and n.func.id == 'odd': r = s.val(n.args[0]); s.jump(('o', r, 0), false)
        else: r = s.val(n); s.jump(('z', r, 1), false)
        s.tmp = sv
    def st(s, n):
        if isinstance(n, ast.Assign): s.val(n.value, s.r(n.targets[0].id)) if not isinstance(n.value, ast.Name) else s.row(HI['mov'], s.r(n.targets[0].id), s.r(n.value.id)); s.tmp = 0
        elif isinstance(n, ast.Return):
            r = s.val(n.value); s.row(HI['ret'], 0, r); s.tmp = 0
        elif isinstance(n, ast.If):
            f, e = s.lb(), s.lb(); s.test(n.test, f)
            for x in n.body: s.st(x)
            s.jump(None, e); s.lab[f] = len(s.rows)
            for x in n.orelse: s.st(x)
            s.lab[e] = len(s.rows)
        elif isinstance(n, ast.While):
            a, b = s.lb(), s.lb(); s.lab[a] = len(s.rows); s.test(n.test, b)
            for x in n.body: s.st(x)
            s.jump(None, a); s.lab[b] = len(s.rows)
        elif isinstance(n, ast.Expr): s.val(n.value, NREG-1); s.tmp = 0
        else: raise SyntaxError(ast.dump(n))
    def run(s):
        for n in s.t.body: s.st(n)
        s.row(HI['ret'], 0, 0); R = s.rows
        out = []
        for i, q in enumerate(R):
            if q['to'] is None: nx = {None: i+1}
            elif q['cond'] is None: nx = {None: s.lab[q['to']]}
            else: nx = {q['cond'][2]: s.lab[q['to']], 1-q['cond'][2]: i+1}
            out.append((q, nx))
        return out
def dataset(rows):
    X, M, T = [], [], []
    for pc, (q, nx) in enumerate(rows):
        for v, n in nx.items():
            x = [(pc >> i & 1)*2-1. for i in range(PCB)]+[0.]*(2*NREG); m = [1.]*PCB+[0.]*(2*NREG)
            if q['cond']:
                d = PCB+(0 if q['cond'][0] == 'z' else NREG)+q['cond'][1]; x[d] = v*2-1.; m[d] = 1.
            X.append(x); M.append(m); T.append([q['op'], q['d'], q['a'], q['b'], q['c'], q['e'], q['k'], n])
    return torch.tensor(X), torch.tensor(M), torch.tensor(T)
class Net:
    def __init__(s, nv, nn, nk):
        s.h = [nv, NREG, NREG, NREG, NREG, NREG, nk, nn]; o = sum(s.h); n = 6; K = 4; s.K = K
        s.W = (torch.randn(n, D_IN)*.3).requires_grad_(); s.b = torch.zeros(n).requires_grad_(); s.P = (torch.randn(K, D_IN)*.1).requires_grad_(); s.Q = torch.zeros(n, K).requires_grad_(); s.O = torch.zeros(o, n).requires_grad_(); s.c = torch.zeros(o).requires_grad_(); s.D = torch.zeros(o, D_IN).requires_grad_()
    def ps(s): return [s.W, s.b, s.P, s.Q, s.O, s.c, s.D]
    def __call__(s, x): return F.relu(x @ s.W.T + s.b + (x @ s.P.T).pow(2) @ s.Q.T) @ s.O.T + x @ s.D.T + s.c
    def errs(s, X, M, T, c=64, noise=True):
        bad = torch.zeros(len(X), dtype=torch.bool)
        for _ in range(c):
            y = s(noisy(X, M)); o = 0
            for j, h in enumerate(s.h): bad |= y[:, o:o+h].argmax(1) != T[:, j]; o += h
        return bad
    def grow(s, X, M, T, y):
        m = len(X); a = 2.; W = a*X*M; b = -a*(M.sum(1)-1); n = s.W.shape[0]; O = torch.zeros(s.O.shape[0], m); o = 0
        for j, h in enumerate(s.h):
            O[o+T[:, j], torch.arange(m)] = 6.; o += h
        for k, v, dm in (('W', W, 0), ('b', b, 0), ('Q', torch.zeros(m, s.K), 0), ('O', O, 1)): setattr(s, k, torch.cat([getattr(s, k).detach(), v], dm).requires_grad_())
def noisy(X, M): return X*M+(torch.randint(0, 2, X.shape).float()*2-1)*(1-M)
def train(rows, nv, nk):
    X, M, T = dataset(rows); net = Net(nv, len(rows)+1, nk); best = 1e9; rd = 0
    while True:
        o = torch.optim.Adam(net.ps(), 5e-3)
        for s in range(150):
            x = noisy(X, M); y = net(x); l = 0; i = 0
            for j, h in enumerate(net.h): l = l+F.cross_entropy(y[:, i:i+h], T[:, j]); i += h
            o.zero_grad(); l.backward(); o.step()
        with torch.no_grad(): bad = net.errs(X, M, T); e = int(bad.sum())
        rd += 1
        if e == 0 and l.item() < .02: break
        if rd > 150: raise Exception('не сошлось')
        if e and e >= best*.9:
            i = bad.nonzero()[:, 0][:6]; net.grow(X[i], M[i], T[i], None)
        best = min(best, e) if e else best
    return net, rd, len(X)
def blob(net, c, rows):
    kk = c.k or [0]; b = struct.pack('<IIII', net.W.shape[0], net.K, len(rows)+1, len(kk))+struct.pack(f'<{len(kk)}q', *kk)
    for t in (net.W, net.b, net.P, net.Q, net.O, net.c, net.D): b += t.detach().reshape(-1).numpy().astype('<f4').tobytes()
    return b
def extend(path):
    """Новые навыки поверх готовой пирамиды: файл нижних навыков читается только ради словаря имён и дополняется в конце."""
    import importlib.util, runpy
    b = open('pyramid.bin', 'rb').read(); n, _, _, _ = struct.unpack('<IIII', b[4:20]); o = 20; voc = {}
    for i in range(n):
        nm = b[o:o+16].rstrip(b'\0').decode(); a, nv, ln = struct.unpack('<III', b[o+16:o+28]); voc[nm] = i; o += 28+ln
    sp = importlib.util.spec_from_file_location('more', path); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); out = bytearray(b); old = hashlib.sha256(b[20:]).hexdigest()
    for f in [v for v in vars(m).values() if inspect.isfunction(v)]:
        voc[f.__name__] = len(voc); c = C(f, {k: v+len(HW) for k, v in voc.items()}); rows = c.run(); nv = len(HW)+len(voc); t = time.time(); net, rd, st = train(rows, nv, len(c.k) or 1); bb = blob(net, c, rows)
        out += f.__name__.encode().ljust(16, b'\0')+struct.pack('<III', 9 if list(c.reg)[0] == 'x' else c.ar, nv, len(bb))+bb
        print(f"новый навык {f.__name__}: нейронов {net.W.shape[0]}, {time.time()-t:.1f}с, вызывает {sorted({n.func.id for n in ast.walk(c.t) if isinstance(n, ast.Call) and n.func.id[0] != '_' and n.func.id != 'odd'})}", flush=True)
    out[4:8] = struct.pack('<I', len(voc)); open('pyramid.bin', 'wb').write(out)
    print('нижние байты не изменились:', hashlib.sha256(bytes(out[20:len(b)])).hexdigest() == old)
if __name__ == '__main__' and len(sys.argv) > 2: extend(sys.argv[2]); sys.exit()
if __name__ == '__main__':
    torch.manual_seed(1); voc = {}; names = []; ar = []; lvl = []; bl = []; dep = []; rep = []; t0 = time.time(); H = {}
    for lv in sorted(lessons.L):
        base = len(names)
        for i, f in enumerate(lessons.L[lv]): voc[f.__name__] = base+i
        for f in lessons.L[lv]:
            c = C(f, {k: v+len(HW) for k, v in voc.items()}); rows = c.run(); t = time.time(); nv = len(HW)+len(voc)
            before = dict(H)
            net, rd, st = train(rows, nv, len(c.k) or 1); b = blob(net, c, rows); h = hashlib.sha256(b).hexdigest()[:12]
            assert all(H[k] == before[k] for k in before)    # нижние нетронуты
            names.append(f.__name__); ar.append(9 if list(c.reg)[0]=='x' else c.ar); lvl.append(lv); bl.append((nv, b)); H[f.__name__] = h
            rep.append(dict(name=f.__name__, level=lv, neurons=net.W.shape[0], rows=len(rows), states=st, rounds=rd, sec=round(time.time()-t, 2), calls=sorted({n.func.id for n in ast.walk(c.t) if isinstance(n, ast.Call) and n.func.id[0] != '_' and n.func.id != 'odd'})))
            print(f"L{lv} {f.__name__:9s} нейронов {net.W.shape[0]:3d}, строк {len(rows):3d}, {time.time()-t:.1f}с", flush=True)
    with open('pyramid.bin', 'wb') as o:
        o.write(struct.pack('<4sIIII', b'NPY2', len(names), len(HW), NREG, 0))
        for n, a, (nv, b) in zip(names, ar, bl): o.write(n.encode().ljust(16, b'\0')+struct.pack('<III', a, nv, len(b))+b)
    json.dump(dict(rep=rep, hash=H, sec=round(time.time()-t0)), open('pyramid.json', 'w'), ensure_ascii=False, indent=1)
    print('всего нейронов', sum(r['neurons'] for r in rep), 'навыков', len(rep), 'время', round(time.time()-t0))
