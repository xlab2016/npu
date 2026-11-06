"""Примеры по этапам. Операнды случайные на логарифмической шкале, чтобы встретились и короткие, и длинные числа."""
import random
EDGE = [0, 1, 2, 3, 9, 10, (1<<31)-1, 1<<31, 1<<32, (1<<62)-1, 1<<62, (1<<63)-1]
def num(r, hi=1<<40, neg=True):
    if r.random() < .08:
        v = min(r.choice(EDGE), hi)
        return -v if neg and r.random() < .3 else v
    v = int(2 ** (r.random() * (len(bin(hi)) - 3))) + r.randrange(3) - 1
    v = max(0, min(v, hi))
    return -v if neg and r.random() < .3 else v
def arg(r, **k): return f"R{r.randrange(8)}" if r.random() < .15 else str(num(r, **k))
def expr(r, d=0):
    x = r.random()
    if d > 3 or x < .35: return str(num(r, hi=9999, neg=False))
    if x < .45: return '(' + expr(r, d+1) + ')'
    if x < .52: return '-' + expr(r, d+1)
    if x < .60: return f"{r.randint(0,12)}^{r.randint(0,6)}"
    o = r.choice(['+','-','*','/','%','+','*','-'])
    sp = r.choice(['', '', ' '])
    return expr(r, d+1) + sp + o + sp + expr(r, d+1)
def program(r):
    n = r.randint(2, 40); s = r.randint(1, 5); d = r.randint(2, 20)
    return r.choice([
      f"PROG\nSET R0 0\nSET R1 {n}\nADD R0 R1\nSUB R1 {s}\nJLT 0 R1 2\nJZ R1 7\nJMP 7\nPRINT R0\nHALT\nEND\nRUN\n",
      f"PROG\nSET R0 0\nSET R1 {n}\nADD R0 R1\nSUB R1 1\nJNZ R1 2\nPRINT R0\nHALT\nEND\nRUN\n",
      f"PROG\nSET R2 {d}\nSET R3 {n}\nSET R4 5\nSUB R3 R2\nJLT R2 R3 R4\nPRINT R3\nEND\nRUN\n",
      f"PROG\nSET R5 3\nJMP R5\nPRINT 1\nPRINT {n}\nEND\nRUN\n", "JMP 2", "JZ 0 2", "JNZ 1 2", "JZ 1 2", "JNZ 0 2", "JLT 1 2 3", "JLT 2 1 3", "END", "HALT"])
def noise(r):
    t = ''.join(chr(r.randrange(32, 127)) for _ in range(r.randint(1, 6)))
    return t
def typo(r, names):
    n = r.choice(names); k = r.randrange(len(n)+1)
    return n[:k] + chr(r.randrange(33, 127)) + ' ' + str(r.randrange(100))
S = {
 1: ['SET','PRINT','ADD','SUB','prog','prog','garbage','inprog'],
 2: ['MUL','DIV','MOD','ABS','MIN','MAX','POW','expr','garbage','inprog'],
 3: ['GCD','LCM','FACT','FIB','ISQRT','PRIME','garbage','inprog'],
 4: ['MODPOW','NCR','NPRIME','PHI','DIGSUM','COLLATZ','MODINV','garbage','inprog']}
S[5] = ['XA','XB','XC','XD','XE','garbage']
STAGE = None
def line(r, k, names):
    n = lambda **a: arg(r, **a)
    if k == 'SET': return f"SET R{r.randrange(8)} {n()}"
    if k == 'PRINT': return f"PRINT {n()}"
    if k in ('ADD','SUB','MUL','MIN','MAX'): return f"{k} {n()} {n()}"
    if k == 'DIV' or k == 'MOD': return f"{k} {n()} {num(r, hi=1<<30) if r.random()>.05 else 0}"
    if k == 'ABS': return f"ABS {n()}"
    if k == 'POW': return f"POW {num(r, hi=50)} {r.randint(-1, 30)}"
    if k == 'expr': return r.choice(['', 'CALC ', 'calc ']) + expr(r)
    if k == 'prog': return program(r).rstrip()
    if k == 'inprog':
        pool = [c for c in S[STAGE] if c not in ('garbage', 'inprog', 'prog', 'expr')]
        body = '\n'.join(line(r, r.choice(pool), names) for _ in range(r.randint(1, 3)))
        if r.random() < .2: body += '\n' + r.choice(['PROG', 'CALC 1+1', noise(r), typo(r, names)])
        return f"PROG\n{body}\nEND\nRUN"
    if k in ('XA', 'XF'): return f"{k} {r.randint(0, 1000)} {r.randint(0, 12)}" if k == 'XF' else f"XA {num(r, hi=1<<31, neg=False)} {num(r, hi=1<<31, neg=False)}"
    if k in ('XB', 'XC'): return f"{k} {max(1, num(r, hi=1<<40, neg=False))}"
    if k == 'XD': return f"XD {r.randint(1, 500)}"
    if k == 'XE': return f"XE {r.randint(1, 18)}"
    if k == 'garbage': return r.choice([noise(r), typo(r, names), 'ADD 1 2 3 4', 'MUL R9 1', '1+', '(2', 'DIV 5 0', '2)', '3 $', 'FACT -1', 'MOD 1 0', '1/0', 'CALC 1%0', 'ABS -5', 'SET R8 1', 'PRINT -'])
    if k in ('GCD','LCM'): return f"{k} {num(r, hi=1<<30)} {num(r, hi=1<<30)}"
    if k == 'FACT': return f"FACT {r.randint(-1, 20)}"
    if k == 'FIB': return f"FIB {r.randint(-1, 90)}"
    if k == 'ISQRT': return f"ISQRT {num(r, hi=(1<<63)-1)}"
    if k == 'PRIME': return f"PRIME {r.randint(-3, 3000)}"
    if k == 'MODPOW': return f"MODPOW {num(r,hi=10**9)} {r.randint(-1,1000)} {r.choice([0,-1,1,num(r,hi=1<<40,neg=False)+2])}"
    if k == 'NCR': return f"NCR {r.randint(-1,40)} {r.randint(-1,20)}"
    if k == 'NPRIME': return f"NPRIME {r.randint(-1,40)}"
    if k == 'PHI': return f"PHI {r.randint(-1,3000)}"
    if k == 'DIGSUM': return f"DIGSUM {num(r, hi=1<<60)}"
    if k == 'COLLATZ': return f"COLLATZ {r.randint(-1,3000)}"
    if k == 'MODINV': return f"MODINV {num(r,hi=10**6)} {r.choice([0,-1,1,r.randint(2,100000)])}"
    raise KeyError(k)
