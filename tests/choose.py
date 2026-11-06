"""Сеть сама выбирает навык. Задачи новые, пары навыков скрыты от практики, память опыта выключена."""
import sys, random, socket, subprocess, time, statistics, json
sys.path.insert(0, 'nc'); import practice as P
def serve(port, plan):
    a = ['./nc_bin', '--model', 'models/nc2.bin', '--mem', 'models/skills.mem', '--tcp', str(port), '--noexp'] + (['--planner', plan] if plan else [])
    p = subprocess.Popen(a, stderr=subprocess.DEVNULL)
    for _ in range(200):
        try: s = socket.create_connection(('127.0.0.1', port)); break
        except OSError: time.sleep(.05)
    s.settimeout(300); return p, s.makefile('rw', newline='\n')
late = ['PERFECT', 'SUMSQ', 'TRIB']; r = random.Random(555); names = P.NAMES
def cat(c):
    if c == 'один навык': return lambda p: p[0] != 0 or p[1] in late
    if c == 'навык+константа': return lambda p: p[0] != 2 or p[1] in late
    if c == 'скрытая пара': return lambda p: not (p[0] in (1, 3) and P.hold(p))
    if c == 'новый навык': return lambda p: p[0] != 0 or p[1] not in late
Q = []
for c, n in (('один навык', 60), ('навык+константа', 40), ('скрытая пара', 60), ('новый навык', 30)):
    for _ in range(n):
        t = None
        while t is None: t = P.make_task(r, names, cat(c))
        Q.append((c, t))
res = {}
for mode, plan, port in (('сеть', 'models/planner.bin', 17831),):
    p, f = serve(port, plan); out = {}; t0 = time.time()
    for c, (pl, nv, ex) in Q:
        q = '? ' + '; '.join(f"{e[0]} {e[1]} = {e[2]}" if nv == 2 else f"{e[0]} = {e[2]}" for e in ex[:4]) + '; ' + (f"{ex[4][0]} {ex[4][1]}" if nv == 2 else f"{ex[4][0]}")
        f.write(q+'\n'); f.flush(); g = f.readline().strip(); w = str(ex[4][2]); ok = g.split(' ')[0] == w; tr = int(g.split('проб ')[1].rstrip(']')) if 'проб' in g else None
        out.setdefault(c, []).append((ok, tr, g[:60], P.plan_text(pl)))
        if sum(len(v) for v in out.values()) % 40 == 0: print('  ...', sum(len(v) for v in out.values()), round(time.time()-t0), flush=True)
    p.kill(); res[mode] = out; print(mode, 'сек', round(time.time()-t0), flush=True)
    for c, v in out.items():
        trs = [x[1] for x in v if x[1] is not None]; print(f"  {c:18s} верно {sum(x[0] for x in v)}/{len(v)}, план найден {len(trs)}, медиана проб {statistics.median(trs) if trs else '-'}", flush=True)
for x in res['сеть']['скрытая пара'][:8]: print('  ', x)
json.dump(res, open('models/choose2.json', 'w'), ensure_ascii=False)
