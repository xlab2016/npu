"""Команды порта, которые выросли из программ, найденных только по примерам."""
import random, socket, subprocess, sys, time, math
BIN, MODEL = sys.argv[1], sys.argv[2]; N = int(sys.argv[3]); PORT = 17801
p = subprocess.Popen([BIN, '--model', MODEL, '--tcp', str(PORT)], stderr=subprocess.DEVNULL)
for _ in range(100):
    try: s = socket.create_connection(('127.0.0.1', PORT)); break
    except OSError: time.sleep(.05)
s.settimeout(30); f = s.makefile('rw', newline='\n'); r = random.Random(4242)
def ask(l): f.write(l+'\n'); f.flush(); return f.readline().strip()
T = {'XA умножение': lambda: (lambda a, b: (f"XA {a} {b}", a*b))(r.randint(1, 1 << 31), r.randint(1, 1 << 30)),
     'XB число единиц': lambda: (lambda a: (f"XB {a}", bin(a).count('1')))(r.randint(1, 1 << 62)),
     'XC log2': lambda: (lambda a: (f"XC {a}", a.bit_length()-1))(r.randint(1, 1 << 62)),
     'XD сумма 1..n': lambda: (lambda a: (f"XD {a}", a*(a+1)//2))(r.randint(1, 20000)),
     'XE факториал': lambda: (lambda a: (f"XE {a}", math.factorial(a)))(r.randint(1, 20))}
tot = 0
try:
    for n, g in T.items():
        ok = 0
        for _ in range(N):
            c, w = g(); got = ask(c); ok += got == str(w)
            if got != str(w): print(' сбой', c, w, got)
        print(n, ok, N); tot += ok
    print('Старые команды:', ask('MUL 6 7'), ask('2+3*(4-1)^2'), ask('GCD 48 18'), ask('FOO'))
finally: p.kill()
print('ИТОГО', tot, N*len(T))
