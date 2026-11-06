"""Полная школа: уроки навыков, циклов и списков, затем заморозка. Результат в models/skills.mem."""
import sys, os, socket, subprocess, time, inspect
sys.path.insert(0, 'nc'); sys.path.insert(0, 'tests')
from teacher import Teacher
import lessons, loops
p = subprocess.Popen(['./nc_bin', '--model', 'models/nc2.bin', '--tcp', '17855'], stderr=subprocess.DEVNULL)
for _ in range(100):
    try: s = socket.create_connection(('127.0.0.1', 17855)); break
    except OSError: time.sleep(.05)
f = s.makefile('rw', newline='\n'); T = Teacher(f); t = time.time()
for m in (lessons, loops):
    for fn in [v for v in vars(m).values() if inspect.isfunction(v)]: T.teach(fn)
print(T.finish(), f"{(time.time()-t)*1000:.0f} мс, строк {T.next-1024}")
f.write(f"@SAVE {os.path.abspath('models/skills.mem')}\n"); f.flush(); print(f.readline().strip()); p.kill()
