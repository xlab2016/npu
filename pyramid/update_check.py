"""Проверка управления обновлениями: сверка планов с алгоритмом GERON и сценарии на настоящем git."""
import heapq, json, os, random, shutil, socket, subprocess, sys, tempfile, time
d = json.load(open('operations.json')); F = [l[2:].strip() for l in open('update.tab') if l[0] == 'F']; B = {f: i for i, f in enumerate(F)}
m = lambda l: sum(1 << B[x] for x in l); O = [(m(o['requires']), m(o['produces']), m(o['invalidates']), round(o['cost']*100)) for o in d['operations']]; G = m(d['goalFacts'])
def astar(s):
    """Тот же поиск, что GeronPlanner.BuildPlan: требования, снятие, добавление, минимальная цена."""
    q = [(0, 0, s)]; best = {s: 0}; n = 0
    while q:
        c, _, f = heapq.heappop(q)
        if c > best.get(f, 1 << 60): continue
        if f & G == G: return c
        for r, p, i, k in O:
            if f & r != r: continue
            g = (f & ~i) | p
            if g == f: continue
            if c+k < best.get(g, 1 << 60): best[g] = c+k; n += 1; heapq.heappush(q, (c+k, n, g))
    return -1
def serve(env, port):
    p = subprocess.Popen(['./npu', '--tcp', str(port), 'pyramid.bin'], env={**os.environ, **env}, stderr=subprocess.DEVNULL)
    for _ in range(200):
        try: s = socket.create_connection(('127.0.0.1', port)); break
        except OSError: time.sleep(.05)
    s.settimeout(60); return p, s.makefile('rw', newline='\n')
p, f = serve({}, 17881)
def ask(l): f.write(l+'\n'); f.flush(); return f.readline().strip()
r = random.Random(11); ok = n = 0; noplan = 0; base = ['REPOSITORY_EXISTS', 'ON_TARGET_BRANCH', 'WORKTREE_CLEAN', 'GIT_PULL_REQUIRED', 'NO_OPERATION_ERROR', 'ASPIRE_RUNNING']
for i in range(400):
    s = set(base) if r.random() < .6 else set()
    s |= set(r.sample(F, r.randint(0, 9)))
    s = {x for x in s if r.random() > .08}; mk = m(s); w = astar(mk); g = ask(f"PLANCOST {mk}"); n += 1; ok += g == str(w); noplan += w < 0
    if g != str(w) and n-ok < 4: print(' сбой', sorted(s), w, g)
    if w >= 0:
        seq = int(ask(f"PLANOPS {mk}")); ops = []
        while seq: ops.insert(0, seq % 16-1); seq //= 16
        h = mk
        for o in ops: assert h & O[o][0] == O[o][0]; h = (h & ~O[o][2]) | O[o][1]
        assert h & G == G
print(f"Планы против алгоритма GERON: {ok}/{n} совпала минимальная цена, без плана {noplan}, все планы выполнимы", flush=True); p.kill()
T = tempfile.mkdtemp(); R = T+'/remote.git'; W = T+'/seed'; Q = T+'/repo'; L = T+'/log'
def sh(c, cwd=None): return subprocess.run(c, shell=True, cwd=cwd, capture_output=True, text=True)
sh(f"git init -q --bare -b main {R}; git clone -q {R} {W}; git config --global user.email t@t; git config --global user.name t; git -C {W} checkout -q -b main; echo 1 > {W}/a; git -C {W} add .; git -C {W} commit -qm 1; git -C {W} push -q origin main; git clone -q {R} {Q}; echo Running > {T}/state; echo ok > {T}/health")
open(T+'/fa', 'w').write(f'#!/bin/bash\ncase "$1" in describe) cat {T}/state;; resource) echo "aspire $3" >> {L}; [ "$3" = stop ] && echo Stopped > {T}/state || echo Running > {T}/state;; esac\n')
open(T+'/fd', 'w').write(f'#!/bin/bash\necho "dotnet $1" >> {L}\nif [ "$1" = build ] && [ -e {T}/buildfail ]; then rm {T}/buildfail; echo "error CS1002"; exit 1; fi\n')
open(T+'/wrap', 'w').write(f'#!/bin/bash\nif [ "$1" = run ] && [ "$2" = GIT_PULL_MAIN ] && [ -e {T}/netfail ]; then rm {T}/netfail; echo ERROR:GIT_NETWORK; exit 1; fi\nexec {os.getcwd()}/device.sh "$@"\n')
os.chmod(T+'/fa', 0o755); os.chmod(T+'/fd', 0o755); os.chmod(T+'/wrap', 0o755)
open(T+'/conf', 'w').write(f'REPO={Q}\nBRANCH=main\nREMOTE=origin\nCLONE_URL={R}\nBUILD_TARGET=x.sln\nAPPHOST=h.csproj\nRESOURCE=Ticketing\nHEALTH_URL=file://{T}/health\nDOTNET={T}/fd\nASPIRE={T}/fa\nNETWORK_WAIT=0\nREADY_SLEEP=0\nHEALTH_TRIES=2\n')
p, f = serve({'NPU_DEVICE': T+'/wrap', 'NPU_DEVICE_CONF': T+'/conf'}, 17882)
def cmd(c, until):
    f.write(c+'\n'); f.flush(); o = []
    while True:
        l = f.readline().strip(); o.append(l)
        if any(u in l for u in until): return o
END = ['ГОТОВО', 'Ждёт подтверждения', 'ЗАПРЕЩЕНО', 'НЕТ БЕЗОПАСНОГО', 'НЕТ ПЛАНА', 'ОТМЕНЕНО']
def push(t='x'): sh(f"echo {t} >> a; git add .; git commit -qm c; git push -q origin main", W)
head = lambda: sh('git rev-parse HEAD', Q).stdout.strip(); rem = lambda: sh('git rev-parse main', R).stdout.strip(); log = lambda: open(L).read().split('\n')[:-1] if os.path.exists(L) else []
res = []
def check(n, c): res.append((n, bool(c))); print(' ', 'OK ' if c else 'FAIL', n, flush=True)
push(); h0 = head(); o = cmd('UPDATE', END); print('\n'.join('    '+x for x in o))
check('до подтверждения ничего не выполнено', head() == h0 and not log())
o = cmd('APPROVE', END); check('обновление дошло до цели', 'ГОТОВО' in o[-1] and head() == rem())
check('порядок команд GERON', log() == ['aspire stop', 'dotnet clean', 'dotnet restore', 'dotnet build', 'aspire start'])
check('повторный APPROVE отклонён', 'НЕТ ПЛАНА' in cmd('APPROVE', END)[-1]); open(L, 'w').close()
push(); h0 = head(); cmd('UPDATE', END); check('CANCEL отменяет план', 'ОТМЕНЕНО' in cmd('CANCEL', END)[-1] and 'НЕТ ПЛАНА' in cmd('APPROVE', END)[-1] and head() == h0 and not log())
open(Q+'/dirty', 'w').write('x'); o = cmd('UPDATE', END); check('локальные изменения блокируют', 'ЗАПРЕЩЕНО' in o[-1] and any('локальные' in x for x in o)); check('заблокированный план нельзя подтвердить', 'НЕТ ПЛАНА' in cmd('APPROVE', END)[-1] and head() == h0); os.remove(Q+'/dirty')
open(T+'/netfail', 'w').close(); cmd('UPDATE', END); o = cmd('APPROVE', END); check('сбой сети даёт план восстановления', 'Ждёт' in o[-1] and any('ВОССТАНОВЛЕНИЯ' in x for x in o) and any('WAIT_NETWORK' in x for x in o))
o = cmd('APPROVE', END); check('восстановление завершило обновление', 'ГОТОВО' in o[-1] and head() == rem()); open(L, 'w').close()
push(); open(T+'/buildfail', 'w').close(); cmd('UPDATE', END); o = cmd('APPROVE', END); check('сбой сборки останавливает без угадывания', 'НЕТ БЕЗОПАСНОГО' in o[-1] and any('CS1002' in x for x in o) and 'aspire start' not in log())
cmd('UPDATE', END); o = cmd('APPROVE', END); check('после исправления обновление проходит', 'ГОТОВО' in o[-1] and open(T+'/state').read().strip() == 'Running')
shutil.rmtree(Q); o = cmd('UPDATE', END); check('нет репозитория: план с GIT_CLONE', any('GIT_CLONE' in x for x in o)); o = cmd('APPROVE', END); check('клонирование и запуск', 'ГОТОВО' in o[-1] and head() == rem())
print('STATUS:', cmd('STATUS', ['NO_OPERATION'])[-1][:110]); print('MUL после всего:', ask('MUL 6 7'))
p.kill(); shutil.rmtree(T); print('ИТОГО сценариев', sum(c for _, c in res), '/', len(res))
