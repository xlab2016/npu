"""Адаптер device.ps1 под настоящим PowerShell 7 и настоящим git; aspire и dotnet заменены заглушками с контрактом GERON."""
import json, os, shutil, socket, subprocess, sys, tempfile, threading, http.server, functools
PW = sys.argv[1]; EXE = sys.argv[2:] or ['./npu']
T = tempfile.mkdtemp(); R = T+'/remote.git'; W = T+'/seed'; Q = T+'/repo'; L = T+'/log'; B = T+'/bin'; os.mkdir(B); os.mkdir(T+'/www'); open(T+'/www/health', 'w').write('ok')
def sh(c, cwd=None): return subprocess.run(c, shell=True, cwd=cwd, capture_output=True, text=True)
sh(f"git init -q --bare -b main {R}; git clone -q {R} {W}; git -C {W} checkout -q -b main; mkdir -p {W}/src/Ticketing {W}/src/Host; touch {W}/src/Ticketing/Ticketing.csproj {W}/src/Host/Host.csproj; echo 1 > {W}/a; git -C {W} add .; git -C {W} commit -qm 1; git -C {W} push -q origin main; git clone -q {R} {Q}; echo up > {T}/state")
h = http.server.ThreadingHTTPServer(('127.0.0.1', 17891), functools.partial(type('Q', (http.server.SimpleHTTPRequestHandler,), {'log_message': lambda *a: None}), directory=T+'/www')); threading.Thread(target=h.serve_forever, daemon=True).start()
open(B+'/aspire', 'w').write(f'''#!/bin/bash
echo "aspire $*" >> {L}.all
case "$1" in describe) exit 0;; wait) s=$(cat {T}/state); [ "$4" = healthy ] && [ "$s" = up ] && exit 0; [ "$4" = "$s" ] && exit 0; exit 1;;
resource) echo "aspire $3" >> {L}; [ "$3" = stop ] && echo down > {T}/state || echo up > {T}/state;; esac
''')
open(B+'/dotnet', 'w').write(f'''#!/bin/bash
echo "dotnet $1" >> {L}; echo "dotnet $*" >> {L}.all
if [ "$1" = build ] && [ -e {T}/buildfail ]; then rm {T}/buildfail; echo "error CS1002"; exit 1; fi
''')
os.chmod(B+'/aspire', 0o755); os.chmod(B+'/dotnet', 0o755)
json.dump({'projects': [{'id': 't', 'repositoryPath': Q, 'cloneUrl': R, 'gitRemote': 'origin', 'gitBranch': 'main', 'aspireAppHostProjectPath': Q+'/src/Host/Host.csproj', 'workingDirectory': Q, 'configuration': 'Release', 'healthUrl': 'http://127.0.0.1:17891/health', 'healthTimeoutSeconds': 10, 'targetResourceName': 'Ticketing', 'targetProjectPath': '', 'environment': {'DOTNET_ENVIRONMENT': 'Development'}}]}, open(T+'/device.json', 'w'))
open(T+'/wrap', 'w').write(f'#!/bin/bash\nexec {PW} -NoLogo -NoProfile -File {os.getcwd()}/device.ps1 "$@"\n'); os.chmod(T+'/wrap', 0o755)
env = {**os.environ, 'PATH': B+':'+os.environ['PATH'], 'NPU_DEVICE': T+'/wrap', 'NPU_DEVICE_CONF': T+'/device.json'}
p = subprocess.Popen(EXE+['--tcp', '17892', 'pyramid.bin'], env=env, stderr=subprocess.DEVNULL)
import time
for _ in range(200):
    try: s = socket.create_connection(('127.0.0.1', 17892)); break
    except OSError: time.sleep(.05)
s.settimeout(90); f = s.makefile('rw', newline='\n')
END = ['ГОТОВО', 'Ждёт подтверждения', 'ЗАПРЕЩЕНО', 'НЕТ БЕЗОПАСНОГО', 'НЕТ ПЛАНА', 'ОТМЕНЕНО']
def cmd(c):
    f.write(c+'\n'); f.flush(); o = []
    while True:
        l = f.readline().strip(); o.append(l)
        if any(u in l for u in END): return o
def push(): sh("echo x >> a; git add .; git commit -qm c; git push -q origin main", W)
head = lambda: sh('git rev-parse HEAD', Q).stdout.strip(); rem = lambda: sh('git rev-parse main', R).stdout.strip(); log = lambda: open(L).read().split('\n')[:-1] if os.path.exists(L) else []
res = []
def check(n, c): res.append(bool(c)); print(' ', 'OK ' if c else 'FAIL', n, flush=True)
push(); h0 = head(); o = cmd('UPDATE'); check('план показан, ничего не выполнено', any('DOTNET_BUILD' in x for x in o) and head() == h0 and not log())
o = cmd('APPROVE'); check('обновление дошло до цели', 'ГОТОВО' in o[-1] and head() == rem()); check('порядок команд', log() == ['aspire stop', 'dotnet clean', 'dotnet restore', 'dotnet build', 'aspire start'])
a = open(L+'.all').read(); check('команды как в GERON', 'dotnet build '+Q+'/src/Ticketing/Ticketing.csproj -c Release --no-restore --verbosity quiet -clp:ErrorsOnly;Summary' in a and 'wait Ticketing --status down --timeout 30' in a)
open(Q+'/dirty', 'w').write('x'); o = cmd('UPDATE'); check('локальные изменения блокируют', 'ЗАПРЕЩЕНО' in o[-1]); os.remove(Q+'/dirty'); open(L, 'w').close()
push(); open(T+'/buildfail', 'w').close(); cmd('UPDATE'); o = cmd('APPROVE'); check('сбой сборки останавливает', 'НЕТ БЕЗОПАСНОГО' in o[-1] and any('CS1002' in x for x in o) and 'aspire start' not in log())
cmd('UPDATE'); o = cmd('APPROVE'); check('после исправления проходит', 'ГОТОВО' in o[-1])
shutil.rmtree(T+'/www'); os.mkdir(T+'/www'); push(); cmd('UPDATE'); o = cmd('APPROVE'); check('неудачная проверка здоровья не считается успехом', 'ГОТОВО' not in o[-1]); open(T+'/www/health', 'w').write('ok')
sh(f"mkdir -p {Q}/x; touch {Q}/x/Ticketing.csproj; git add .; git commit -qm dup", Q); o = cmd('UPDATE'); check('неоднозначный проект блокирует', 'ЗАПРЕЩЕНО' in o[-1])
p.kill(); h.shutdown(); shutil.rmtree(T); print('ИТОГО', sum(res), '/', len(res))
