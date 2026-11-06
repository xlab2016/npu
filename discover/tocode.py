"""Переводит найденные программы в строки микрокода. Сеть-контроллер потом учит их как новые команды порта."""
import json, sys
from core import *
GCOND = {1: 'T{x}even', 2: 'T{x}odd', 3: 'T{x}!=0', 4: 'T{x}=0'}
def stmt(s, names, ar, skip):
    o = []
    if s.g in GCOND: o.append(f"NOP | {GCOND[s.g].format(x=s.gx)}:{skip}")
    elif s.g in (5, 6): o += [f"CMP T{s.gx} T{s.gy}", f"NOP | {'NN' if s.g == 5 else 'N'}:{skip}"]
    a, b = s.a, s.b
    if s.op == 0: o.append(f"MOV T{a} T{b}")
    elif s.op == 1: o.append(f"ADD T{a} T{b}")
    elif s.op == 2: o.append(f"SUB T{a} T{b}")
    elif s.op == 3: o += [f"PUSH T{a}", f"MOV T{a} T{b}", f"POP T{b}"]
    elif s.op == 4: o.append(f"SHL T{a}")
    elif s.op == 5: o.append(f"SHR T{a}")
    elif s.op == 6: o.append(f"INC T{a}")
    elif s.op == 7: o.append(f"DEC T{a}")
    elif s.op == 8: o.append(f"LDI T{a} 0")
    elif s.op == 9: o.append(f"LDI T{a} 10")
    else:
        k = s.op - NBASE; n = names[k]
        o += [f"PUSH T{i}" for i in range(4)] + [f"PUSH T{a}", f"PUSH T{b}", "POP T1", "POP T0"]
        if ar[n] == 1: o.append("LDI T1 0")
        o += ["LDI T2 0", "LDI T3 0", f"CALL z_{n}", "MOV T4 T3"] + [f"POP T{i}" for i in (3, 2, 1, 0)] + [f"MOV T{a} T4"]
    return o
def compile_prog(n, p, names, ar):
    L_ = [f"z_{n}:"]; c = [0]
    def block(arr, cnt):
        for i in range(cnt):
            c[0] += 1; lb = f"zs_{n}_{c[0]}"; L_.extend('  ' + x for x in stmt(arr[i], names, ar, lb)); L_.append(f"{lb}:"); L_.append("  NOP")
    block(p.p, p.np)
    if p.lg:
        l0, l1 = f"zl_{n}", f"ze_{n}"; L_.append(f"{l0}:")
        if p.lg in (5, 6): L_ += [f"  CMP T{p.lx} T{p.ly}", f"  NOP | {'NN' if p.lg == 5 else 'N'}:{l1}"]
        else: L_.append(f"  NOP | {GCOND[p.lg].format(x=p.lx)}:{l1}")
        block(p.b, p.nb); L_ += [f"  GOTO {l0}", f"{l1}:", "  NOP"]; block(p.q, p.nq)
    L_.append("  RET"); return L_
def build(solved, pick):
    names = list(solved); ar = {n: solved[n]['arity'] for n in names}; out = ["; сгенерировано из программ, найденных по примерам"]; root = []
    P = {n: Prog.from_buffer_copy(bytes.fromhex(solved[n]['raw'])) for n in names}; need = []
    def dep(n):
        if n in need: return
        p = P[n]
        for arr, cnt in ((p.p, p.np), (p.b, p.nb), (p.q, p.nq)):
            for i in range(cnt):
                if arr[i].op >= NBASE: dep(names[arr[i].op-NBASE])
        need.append(n)
    for n in pick: dep(n)
    for n in need: out += compile_prog(n, P[n], names, ar)
    sw = []; disp = []
    for i, n in enumerate(pick):
        ch = chr(65 + i); code = 31 + i; sw += [f"'{ch}':tx{i}", f"'{ch.lower()}':tx{i}"]; disp.append(f"#{code}:zop{i}")
        out += [f"tx{i}: RX", f"  LDI T4 {code}", "  GOTO cmd_args", f"zop{i}: LDI T3 0", "  LDI T2 0"] + (["  LDI T1 0"] if ar[n] == 1 else []) + [f"  CALL z_{n}", "  GOTO done"]
    out += ["tx: RX", f"  NOP | {' '.join(sw)} else:err"]
    return '\n'.join(out), ' '.join(disp)
if __name__ == '__main__':
    d = json.load(open(sys.argv[1])); pick = sys.argv[2].split(',')
    t, disp = build(d['solved'], pick); open('../nc/found.uasm', 'w', encoding='utf8').write(t); open('../nc/found.disp', 'w').write(disp)
    print(len([l for l in t.split('\n') if l.startswith('  ') or ': ' in l and not l.startswith(';')]), 'строк примерно'); print(dict(enumerate(pick)))
