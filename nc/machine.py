"""Тракт данных neurocpu, ассемблер микрокода и эталонный учитель."""
import re, os, random
OPS = "NOP MOV LDI ADD SUB SHL SHR NEG CMP INC DEC PUSH POP LD ST RX SETC GETC TX TXC CALL RET RST CALLR".split()
OPI = {o: i for i, o in enumerate(OPS)}
PC_BITS, OP_BITS, A_BITS, B_BITS = 10, 5, 4, 8
NREG, RAM = 12, 8192
WORD_BITS = OP_BITS + A_BITS + B_BITS + PC_BITS
# вход сети: pc(10) Z N c(8) zero(12) odd(12)
D_PC, D_Z, D_N, D_C, D_ZR, D_OD = 0, 10, 11, 12, 20, 32
D_IN = 44
M64 = (1 << 64) - 1
# мнемоника: (код, метка, этап). Код 0 не используется, это конец программы.
CMDS = {
 'SET':(1,'op_set',1),'PRINT':(2,'op_print',1),'JMP':(3,'op_jmp',1),'JZ':(4,'op_jz',1),'JNZ':(5,'op_jnz',1),
 'JLT':(6,'op_jlt',1),'HALT':(7,'op_halt',1),'ADD':(8,'op_add',1),'SUB':(9,'op_sub',1),
 'MUL':(11,'op_mul',2),'DIV':(12,'op_div',2),'MOD':(13,'op_mod',2),'ABS':(14,'op_abs',2),'MIN':(15,'op_min',2),
 'MAX':(16,'op_max',2),'POW':(17,'op_pow',2),
 'GCD':(18,'op_gcd',3),'LCM':(19,'op_lcm',3),'FACT':(20,'op_fact',3),'FIB':(21,'op_fib',3),'ISQRT':(22,'op_isqrt',3),
 'PRIME':(23,'op_prime',3),
 'MODPOW':(24,'op_modpow',4),'NCR':(25,'op_ncr',4),'NPRIME':(26,'op_nprime',4),'PHI':(27,'op_phi',4),
 'DIGSUM':(28,'op_digsum',4),'COLLATZ':(29,'op_collatz',4),'MODINV':(30,'op_modinv',4)}
DIRECT = {'PROG':'cmd_prog','END':'cmd_end','RUN':'cmd_run','CALC':'cmd_calc'}

class Row:
    __slots__ = ('op','a','b','conds','src','dims')

def trie_rows():
    """Дерево разбора мнемоник: сеть сама декодирует текст команды символ за символом."""
    names = dict(CMDS); names.update({k:(0,v,1) for k,v in DIRECT.items()})
    root = {}
    for n in names:
        t = root
        for ch in n: t = t.setdefault(ch, {})
        t['$'] = n
    lines, cnt = [], [0]
    def sw(node):
        return ' '.join(f"'{k}':tr{node[k]['#']} '{k.lower()}':tr{node[k]['#']}" for k in sorted(node) if k not in '$#')
    def number(node):
        for k, v in node.items():
            if k not in '$#' and isinstance(v, dict):
                v['#'] = cnt[0]; cnt[0] += 1; number(v)
    number(root)
    def emit(node):
        for k in sorted(k for k in node if k not in '$#'):
            v = node[k]; i = v['#']; lines.append(f"tr{i}: RX")
            e = v.get('$')
            if e in DIRECT:   tail = f"else:{DIRECT[e]}"
            elif e:           tail = f"else:tre{i}"
            else:             tail = "else:err"
            sub = sw(v)
            lines.append(f"       NOP | {sub} {tail}")
            if e in CMDS:
                lines.append(f"tre{i}: LDI T4 {CMDS[e][0]}"); lines.append("       GOTO cmd_args")
            emit(v)
    emit(root)
    return sw(root), lines

CH_ESC = {'\\n':10,'\\r':13}
def char(tok):
    b = tok[1:-1]
    return CH_ESC.get(b, ord(b) if len(b) == 1 else None)

def assemble(path=None):
    path = path or os.path.join(os.path.dirname(__file__), 'micro.uasm')
    txt = open(path, encoding='utf8').read()
    root, trie = trie_rows()
    disp = ' '.join(f"#{c}:{l}" for c, l, _ in CMDS.values())
    fnd, fp = '', os.path.join(os.path.dirname(path), 'found.uasm')   # навыки, найденные по примерам
    if os.path.exists(fp):
        fnd = open(fp, encoding='utf8').read(); root += " 'X':tx 'x':tx"; disp += ' ' + open(fp[:-4] + 'disp').read()
    txt = txt.replace('%TRIE%', root).replace('%DISPATCH%', disp) + '\n' + '\n'.join(trie) + '\n' + fnd
    return parse(txt)

def parse(txt, known=None, base=0):
    rows, lab = [], dict(known or {})
    for ln in txt.split('\n'):
        ln = ln.split(' ;')[0] if not ln.startswith(';') else ''
        ln = ln.strip()
        if not ln: continue
        m = re.match(r'^(\w+):\s*(.*)$', ln)
        if m and m.group(2).split(' ')[0] in OPI | {'GOTO':0} or (m and not m.group(2)):
            lab[m.group(1)] = base + len(rows); ln = m.group(2).strip()
            if not ln: continue
        rows.append(ln)
    out = []
    def reg(t): return int(t[1:])
    for i, ln in enumerate(rows):
        head, _, tail = ln.partition('|')
        p = head.split(); r = Row(); r.src = ln; r.conds = []
        if p[0] == 'GOTO': r.op, r.a, r.b = OPI['NOP'], 0, 0; r.conds = [('else', lab[p[1]])]
        else:
            r.op = OPI[p[0]]; a = b = 0
            if p[0] == 'CALL': r.conds = [('else', lab[p[1]])]
            elif p[0] == 'TXC': b = char(p[1]) 
            elif p[0] == 'LDI': a = reg(p[1]); b = int(p[2])
            else:
                if len(p) > 1: a = reg(p[1])
                if len(p) > 2: b = reg(p[2])
            r.a, r.b = a, b
        for tok in re.findall(r"('(?:\\.|[^'])':\w+|\S+:\w+)", tail):
            c, t = tok.rsplit(':', 1); t = lab[t]
            if c[0] == "'":      r.conds.append(('c', {char(c)}, t))
            elif c == 'DIG':     r.conds.append(('c', set(range(48,58)), t))
            elif c[0] == '#':    r.conds.append(('c', {int(c[1:])}, t))
            elif c == 'Z':       r.conds.append(('f', D_Z, 1, t))
            elif c == 'NZ':      r.conds.append(('f', D_Z, 0, t))
            elif c == 'N':       r.conds.append(('f', D_N, 1, t))
            elif c == 'NN':      r.conds.append(('f', D_N, 0, t))
            elif c == 'else':    r.conds.append(('else', t))
            else:
                m = re.match(r'T(\d+)(=0|!=0|odd|even)$', c); q, k = int(m[1]), m[2]
                if k in ('=0', '!=0'): r.conds.append(('f', D_ZR+q, int(k == '=0'), t))
                else:                  r.conds.append(('f', D_OD+q, int(k == 'odd'), t))
        r_i = base + i
        d = set(range(D_PC, D_PC+PC_BITS))
        for c in r.conds:
            if c[0] == 'c': d |= set(range(D_C, D_C+8))
            if c[0] == 'f': d.add(c[1])
        r.dims = sorted(d)
        out.append(r)
    assert base or len(out) < 1 << PC_BITS, len(out)
    return out, lab


class Machine:
    def __init__(s, rows, inp=b''):
        s.rows = rows; s.R = [0]*NREG; s.Z = s.Nf = 0; s.C = 0; s.ram = {}; s.st = []; s.cs = []
        s.pc = 0; s.inp = bytearray(inp); s.ip = 0; s.out = bytearray(); s.cycles = 0
    def feat(s):
        p = s.pc; b = [(p >> i) & 1 for i in range(PC_BITS)] + [s.Z, s.Nf] + [(s.C >> i) & 1 for i in range(8)]
        b += [int(v == 0) for v in s.R] + [v & 1 for v in s.R]
        return b
    def teach(s, f):
        """Учитель: что сделал бы эталон в этом состоянии."""
        r = s.rows[s.pc]; nxt = s.pc + 1
        for c in r.conds:
            if c[0] == 'else': nxt = c[1]; break
            if c[0] == 'c' and s.C in c[1]: nxt = c[2]; break
            if c[0] == 'f' and f[c[1]] == c[2]: nxt = c[3]; break
        if r.op == OPI['RET']: nxt = 0
        return r.op, r.a, r.b, nxt
    def exec(s, op, a, b, nxt):
        R = s.R; b4 = b & 15; o = OPS[op]; res = None
        if o == 'NOP': pass
        elif o == 'MOV': res = R[b4]; R[a] = res
        elif o == 'LDI': R[a] = b
        elif o == 'ADD': res = (R[a]+R[b4]) & M64; R[a] = res
        elif o == 'SUB': res = (R[a]-R[b4]) & M64; R[a] = res
        elif o == 'SHL': res = (R[a] << 1) & M64; R[a] = res
        elif o == 'SHR': res = R[a] >> 1; R[a] = res
        elif o == 'NEG': res = (-R[a]) & M64; R[a] = res
        elif o == 'CMP': res = (R[a]-R[b4]) & M64
        elif o == 'INC': res = (R[a]+1) & M64; R[a] = res
        elif o == 'DEC': res = (R[a]-1) & M64; R[a] = res
        elif o == 'PUSH': s.st.append(R[a])
        elif o == 'POP': R[a] = s.st.pop() if s.st else 0
        elif o == 'LD': R[a] = s.ram.get(R[b4] % RAM, 0)
        elif o == 'ST': s.ram[R[a] % RAM] = R[b4]
        elif o == 'RX':
            if s.ip >= len(s.inp): return False
            s.C = s.inp[s.ip]; s.ip += 1
        elif o == 'SETC': s.C = R[a] & 255
        elif o == 'GETC': R[a] = s.C
        elif o == 'TX': s.out.append(R[a] & 255)
        elif o == 'TXC': s.out.append(b)
        elif o == 'CALL': s.cs.append(s.pc+1)
        elif o == 'RET': nxt = s.cs.pop() if s.cs else 0
        elif o == 'RST': s.st.clear(); s.cs.clear()
        if res is not None:
            s.Z = int(res == 0); s.Nf = res >> 63
            # сравнение знаковое: N = a<b даже при переполнении разности
            if o == 'CMP':
                sa = R[a]-(1 << 64) if R[a] >> 63 else R[a]; sb = R[b4]-(1 << 64) if R[b4] >> 63 else R[b4]
                s.Nf = int(sa < sb)
        s.pc = nxt; s.cycles += 1
        return True
    def run(s, limit=20_000_000, hook=None):
        while s.cycles < limit:
            f = s.feat(); w = s.teach(f)
            if hook: hook(s.pc, f, w)
            if not s.exec(*w): return True
        return False
def word(op, a, b, nxt):
    return op | a << OP_BITS | b << (OP_BITS+A_BITS) | nxt << (OP_BITS+A_BITS+B_BITS)
if __name__ == '__main__':
    rows, lab = assemble(); print(len(rows), 'строк микрокода')
    for t in ["ADD 5 7\nMUL -12 34\nDIV -100 7\nMOD 100 7\n2+3*(4-1)^2\nCALC 7 / 2\nPOW 2 10\nGCD 48 18\nLCM 4 6\nFACT 10\nFIB 50\nISQRT 1000000\nPRIME 97\nPRIME 91\n",
              "MODPOW 3 200 1000007\nNCR 30 15\nNPRIME 100\nPHI 360\nDIGSUM 98765\nCOLLATZ 27\nMODINV 3 11\nFOO\nDIV 1 0\nSET R1 5\nADD R1 R1\nPRINT R1\n",
              "PROG\nSET R0 0\nSET R1 10\nADD R0 R1\nSUB R1 1\nJNZ R1 2\nPRINT R0\nHALT\nEND\nRUN\nmul 6 7\n"]:
        m = Machine(rows, t.encode()); ok = m.run(); print(ok, m.cycles, m.out.decode().replace('\n',' | '))
