"""Учитель: показывает навык через порт. Урок это функция на простом Python, teacher переводит её в фигуры памяти.
Сам навык после урока живёт только в процессоре, учитель для работы не нужен."""
import ast, sys, os, socket, json, inspect, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from machine import *
BUILTIN = {k: v[0] for k, v in CMDS.items() if k in ('ABS','MIN','MAX','POW','GCD','LCM','FACT','FIB','ISQRT','PRIME','MODPOW','NCR','NPRIME','PHI','DIGSUM','COLLATZ','MODINV','MUL','DIV','MOD')}
class Teacher:
    def __init__(s, sock_file):
        s.f = sock_file; s.rows, s.lab = assemble(); s.lab['disp'] = s.lab['e3'] + 1; s.lab['power_t'] = s.lab['power'] + 1; s.lab['calc_t'] = s.lab['calc_go'] + 1; s.disp_lab = 'disp'; s.next = 1024; s.code = 36; s.nodes = {}; s.height = {}; s.count = 0; s.uid = 0; s.fnroot = {}
        s.taught = {}; s.disp = s.lab['e3'] + 1; s.tmp = 0
        s.install(WORK_RT); s.patch(s.lab['done'], ('f', D_OD+11, 1), s.lab['doneret'])
        for n, c in BUILTIN.items(): s.add_fn(n, c); s.f.write(f"@K {n} {c} 0 0\n")
        for r_ in (s.lab['line2'], s.lab['line2p']): s.fig(r_, 0xFF << 2, ord('#') << 2, s.base_word(r_, s.lab['hash']))
        s.fig(s.lab['atom'], 0xFF << 2, ord('#') << 2, s.base_word(s.lab['atom'], s.lab['ath']))
        for nm, flag in (('LIST', 0), ('LISTQ', 1)):
            s.uid += 1; lb = f"lt{s.uid}"; s.install(f"{lb}: LDI T4 {flag}\n  GOTO lst_cmd")
            for e in s.walk(nm): s.link(e, b' \n\r', s.lab[lb])
        s.f.flush()
    def fig(s, pc, m, v, w): s.f.write(f"@F {pc} {m:x} {v:x} {w:x}\n"); s.count += 1
    def base_word(s, pc, nxt):
        r = s.rows[pc]; return word(r.op, r.a, r.b, nxt)
    def cond_mv(s, c):
        if c[0] == 'cc': return 0xFF << 2, c[1] << 2
        if c[0] == 'f': b = c[1] - 10; return 1 << b, c[2] << b
    def patch(s, pc, cond, target): s.fig(pc, *s.cond_mv(cond), s.base_word(pc, target))
    def install(s, text):
        """Строки новой зоны превращаются в фигуры: одна фигура на условие и одна на путь по умолчанию."""
        out, lab = parse(text, s.lab, s.next); s.lab = lab
        for i, r in enumerate(out):
            pc = s.next + i; s.rows.extend([]) ; ret = r.op == OPI['RET']; has = False
            for c in r.conds:
                if c[0] == 'else': s.fig(pc, 0, 0, word(r.op, r.a, r.b, c[1])); has = True; break
                if c[0] == 'c':
                    for ch in sorted(c[1]): s.fig(pc, 0xFF << 2, ch << 2, word(r.op, r.a, r.b, c[2]))
                else: b = c[1] - 10; s.fig(pc, 1 << b, c[2] << b, word(r.op, r.a, r.b, c[3]))
            if not has: s.fig(pc, 0, 0, word(r.op, r.a, r.b, 0 if ret else pc + 1))
        s.next += len(out); assert s.next < 4096
    # слова: и команды порта, и функции в выражениях растут как дерево фигур
    def node(s):
        s.uid += 1; n = f"n{s.uid}"; s.install(f"{n}: RX\n  NOP | else:err"); return dict(sw=s.lab[n]+1, kids={}, rx=s.lab[n])
    def child(s, parent_pc, kids, ch):
        k = ch.upper()
        if k in kids: return kids[k]
        n = s.node(); kids[k] = n
        for c in (ord(k), ord(k.lower())):
            s.fig(parent_pc, 0xFF << 2, c << 2, word(OPI['NOP'], 0, 0, n['rx']))
        return n
    def base_child(s, sw, ch):
        for c in s.rows[sw].conds:
            if c[0] == 'c' and ord(ch) in c[1] and c[2] < len(s.rows) and s.rows[c[2]].op == OPI['RX']: return c[2]
        return None
    def walk(s, name):
        """Идёт по дереву слов от начала строки, недостающие ветви выращивает. Возвращает концы слова."""
        ends = []
        for root in (s.lab['line2'], s.lab['line2p']):
            sw, zone = root, None
            for ch in name:
                if zone is None:
                    t = s.base_child(sw, ch)
                    if t is not None: sw = t + 1; continue
                    zone = s.child(sw, s.nodes.setdefault(sw, {}), ch)
                else: zone = s.child(zone['sw'], zone['kids'], ch)
            ends.append((zone['sw'], True) if zone else (sw, False))
        return ends
    def link(s, end, chars, target):
        sw, zone = end
        for c in chars: s.fig(sw, 0xFF << 2, c << 2, word(OPI['NOP'], 0, 0, target) if zone else s.base_word(sw, target))
    def add_cmd(s, name, code):
        s.uid += 1; lb = f"term{s.uid}"; s.install(f"{lb}: LDI T4 {code}\n  GOTO cmd_args")
        for e in s.walk(name): s.link(e, b' \n\r', s.lab[lb])
    def add_fn(s, name, code):
        s.uid += 1; lb = f"fc{s.uid}"; lf = f"lf{s.uid}"
        s.install(f"{lb}: LDI T7 {code}\n  PUSH T7\n  GOTO fargs\n{lf}: CALL {lb}\n  CALL power_t\n  CALL te1\n  CALL ex1\n  GOTO calc_t"); n = None
        for ch in name:
            if n is None: n = s.child(s.lab['atom'], s.fnroot, ch)
            else: n = s.child(n['sw'], n['kids'], ch)
        s.fig(n['sw'], 0xFF << 2, ord('(') << 2, word(OPI['NOP'], 0, 0, s.lab[lb]))
        for e in s.walk(name): s.link(e, b'(', s.lab[lf])     # функция в начале строки: дальше идёт разбор выражения
    def teach(s, fn):
        name = fn.__name__; code = s.code; s.code += 1; t = time.time(); c0 = s.count
        src = inspect.getsource(fn); tree = ast.parse(src).body[0]; text, h = Compiler(s, tree).run()
        s.install(text); s.taught[name] = (len(tree.args.args), h)
        s.uid += 1; lb = f"zop{s.uid}"; s.install(f"{lb}: CALL z_{name}\n  GOTO done")
        s.fig(s.disp, 0xFF << 2, code << 2, s.base_word(s.disp, s.lab[lb]))
        s.add_cmd(name, code); s.add_fn(name, code); s.f.write(f"@S {name} {len(tree.args.args)}\n@K {name} {code} {h} {s.lab['z_'+name]}\n@END\n"); s.f.flush()
        a = s.f.readline().strip(); return s.count - c0, (time.time()-t)*1000
class Compiler:
    def __init__(c, T, tree):
        c.T, c.t, c.o, c.l, c.n = T, tree, [], {}, 0
        callees = [x.func.id for x in ast.walk(tree) if isinstance(x, ast.Call) and x.func.id in T.taught]
        c.base = 14 + max([T.taught[k][1] for k in callees] or [0])
    def slot(c, v):
        if v not in c.l:
            c.l[v] = c.base + len(c.l); assert c.l[v] < 64, 'мало памяти для локальных'
        return c.l[v]
    def lb(c): c.T.uid += 1; return f"L{c.T.uid}"
    def e(c, *x): c.o.extend('  ' + i for i in x)
    def num(c, v):
        if v < 0: c.num(-v); c.e('NEG T3'); return
        if v < 256: c.e(f"LDI T3 {v}"); return
        c.num(v >> 8); c.e(*['SHL T3']*8, f"LDI T7 {v & 255}", 'ADD T3 T7')
    def expr(c, n):
        if isinstance(n, ast.Constant): c.num(int(n.value))
        elif isinstance(n, ast.Name): c.e(f"LDI T8 {c.slot(n.id)}", "LD T3 T8")
        elif isinstance(n, ast.UnaryOp): c.expr(n.operand); c.e('NEG T3')
        elif isinstance(n, ast.BinOp):
            c.expr(n.left); c.e('PUSH T3'); c.expr(n.right); c.e('MOV T1 T3', 'POP T0'); o = type(n.op).__name__
            c.e(*{'Add': ['MOV T3 T0', 'ADD T3 T1'], 'Sub': ['MOV T3 T0', 'SUB T3 T1'], 'Mult': ['CALL mul'], 'FloorDiv': ['CALL div'], 'Div': ['CALL div'], 'Mod': ['CALL div', 'MOV T3 T4'], 'Pow': ['CALL pow']}[o])
        elif isinstance(n, ast.Compare) or isinstance(n, ast.BoolOp):
            f, e = c.lb(), c.lb(); c.cond(n, f); c.e('LDI T3 1', f'GOTO {e}'); c.o.append(f"{f}:"); c.e('LDI T3 0'); c.o.append(f"{e}:"); c.e('NOP')
        elif isinstance(n, ast.Call):
            for a in n.args: c.expr(a); c.e('PUSH T3')
            f = n.func.id
            if f == 'CALLF':
                for i in reversed(range(len(n.args)-1)): c.e(f"POP T{i}")
                c.e('POP T6')
                sv = [x for s_ in c.locs for x in (f"LDI T8 {s_}", 'LD T7 T8', 'PUSH T7')]; rs = [x for s_ in reversed(c.locs) for x in ('POP T7', f"LDI T8 {s_}", 'ST T8 T7')]
                return c.e(*sv, 'CALLR T6', *rs)
            if f == 'PEEK': return c.e('POP T3', 'LD T3 T3')
            if f == 'POKE': return c.e('POP T1', 'POP T0', 'ST T0 T1')
            for i in reversed(range(len(n.args))): c.e(f"POP T{i}")
            if f in c.T.taught: c.e(f"CALL z_{f}")
            else:
                for i in range(len(n.args), 3): c.e(f"LDI T{i} 0")
                c.e(f"LDI T4 {BUILTIN[f]}", 'SETC T4', 'PUSH T11', 'LDI T11 1', f"CALL {c.T.disp_lab}", 'POP T11')
        else: raise SyntaxError(ast.dump(n))
    def cond(c, n, false):
        if isinstance(n, ast.BoolOp):
            if isinstance(n.op, ast.And):
                for v in n.values: c.cond(v, false)
            else:
                ok = c.lb()
                for v in n.values[:-1]:
                    nx = c.lb(); c.cond(v, nx); c.e(f'GOTO {ok}'); c.o.append(f"{nx}:"); c.e('NOP')
                c.cond(n.values[-1], false); c.o.append(f"{ok}:"); c.e('NOP')
        elif isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.Not):
            t = c.lb(); c.cond(n.operand, t); c.e(f'GOTO {false}'); c.o.append(f"{t}:"); c.e('NOP')
        elif isinstance(n, ast.Compare):
            c.expr(n.left); c.e('PUSH T3'); c.expr(n.comparators[0]); c.e('MOV T1 T3', 'POP T0'); o = type(n.ops[0]).__name__
            c.e(*{'Eq': ['CMP T0 T1', f'NOP | NZ:{false}'], 'NotEq': ['CMP T0 T1', f'NOP | Z:{false}'], 'Lt': ['CMP T0 T1', f'NOP | NN:{false}'], 'GtE': ['CMP T0 T1', f'NOP | N:{false}'], 'Gt': ['CMP T1 T0', f'NOP | NN:{false}'], 'LtE': ['CMP T1 T0', f'NOP | N:{false}']}[o])
        else: c.expr(n); c.e('MOV T3 T3', f'NOP | Z:{false}')
    def store(c, t, reg='T3'): c.e(f"LDI T8 {c.slot(t.id)}", f"ST T8 {reg}")
    def st(c, n):
        if isinstance(n, ast.Assign):
            t = n.targets[0]
            if isinstance(t, ast.Tuple):
                for v in n.value.elts: c.expr(v); c.e('PUSH T3')
                for x in reversed(t.elts): c.e('POP T3'); c.store(x)
            else: c.expr(n.value); c.store(t)
        elif isinstance(n, ast.AugAssign):
            c.expr(ast.BinOp(ast.Name(n.target.id), n.op, n.value)); c.store(n.target)
        elif isinstance(n, ast.While):
            a, b = c.lb(), c.lb(); c.o.append(f"{a}:"); c.e('NOP'); c.cond(n.test, b)
            for x in n.body: c.st(x)
            c.e(f'GOTO {a}'); c.o.append(f"{b}:"); c.e('NOP')
        elif isinstance(n, ast.For):
            r = n.iter.args; lo, hi = (ast.Constant(0), r[0]) if len(r) == 1 else r[:2]; c.tmp = getattr(c, 'tmp', 0) + 1; h = ast.Name(f"_h{c.tmp}")
            c.st(ast.Assign([n.target], lo)); c.st(ast.Assign([h], hi))
            a, b = c.lb(), c.lb(); c.o.append(f"{a}:"); c.e('NOP'); c.cond(ast.Compare(n.target, [ast.Lt()], [h]), b)
            for x in n.body: c.st(x)
            c.st(ast.AugAssign(n.target, ast.Add(), ast.Constant(1))); c.e(f'GOTO {a}'); c.o.append(f"{b}:"); c.e('NOP')
        elif isinstance(n, ast.If):
            f, e = c.lb(), c.lb(); c.cond(n.test, f)
            for x in n.body: c.st(x)
            c.e(f'GOTO {e}'); c.o.append(f"{f}:"); c.e('NOP')
            for x in n.orelse: c.st(x)
            c.o.append(f"{e}:"); c.e('NOP')
        elif isinstance(n, ast.Return): c.expr(n.value); c.e('RET')
        elif isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant): pass
        elif isinstance(n, ast.Expr): c.expr(n.value)
        else: raise SyntaxError(ast.dump(n))
    def run(c):
        c.o.append(f"z_{c.t.name}:"); ar = [a.arg for a in c.t.args.args]
        for a in ar: c.slot(a)
        for v in sorted({x.id for x in ast.walk(c.t) if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Store)}): c.slot(v)
        c.locs = list(c.l.values())
        for i, a in enumerate(ar): c.e(f"LDI T8 {c.slot(a)}", f"ST T8 T{i}")
        for n in c.t.body: c.st(n)
        c.e('LDI T3 0', 'RET'); return '\n'.join(c.o), c.base - 14 + len(c.l)
WORK_RT = r'''
hash: RX
  CALL num
  NOP | '(':hfn else:hcmd
hcmd: MOV T4 T5
  GOTO cmd_args
hfn: PUSH T5
  CALL fargs
  CALL power_t
  CALL te1
  CALL ex1
  GOTO calc_t
ath: RX
  CALL num
  NOP | '(':ath2 else:err
ath2: PUSH T5
  GOTO fargs
lst_cmd: LDI T6 0
ll: NOP | ' ':ll_sp '\r':ll_sp '\n':ll_e DIG:ll_n '-':ll_m else:err
ll_sp: RX | else:ll
ll_n: CALL num
ll_s: INC T6
  LDI T8 16
  SHL T8
  SHL T8
  SHL T8
  SHL T8
  SHL T8
  SHL T8
  SHL T8
  SHL T8
  ADD T8 T6
  ST T8 T5
  GOTO ll
ll_m: RX
  NOP | DIG:ll_m2 else:err
ll_m2: CALL num
  NEG T5
  GOTO ll_s
ll_e: LDI T8 16
  SHL T8
  SHL T8
  SHL T8
  SHL T8
  SHL T8
  SHL T8
  SHL T8
  SHL T8
  ST T8 T6
  NOP | T4=0:ok else:line
doneret: RET
fargs: RX
  LDI T7 0
  PUSH T7
fa1: CALL expr
  POP T7
  PUSH T3
  INC T7
  PUSH T7
  NOP | ',':fa2 ')':fa3 else:err
fa2: RX | else:fa1
fa3: RX
  POP T7
  LDI T2 0
  LDI T1 0
  DEC T7
  NOP | Z:fa_1
  DEC T7
  NOP | Z:fa_2
  POP T2
fa_2: POP T1
fa_1: POP T0
  POP T4
  GETC T5
  PUSH T5
  SETC T4
  PUSH T11
  LDI T11 1
  CALL disp
  POP T11
  POP T5
  SETC T5
  CALL ws
  RET
'''
def finish(s):
    L_ = s.lab; s.f.write(f"@L {L_['disp']} {L_['mul']} {L_['div']} {L_['pow']} {L_['done']} {s.next}\n@FREEZE\n"); s.f.flush(); return s.f.readline().strip()
Teacher.finish = finish
if __name__ == '__main__':
    # python3 nc/teacher.py уроки.py 7777 models/skills.mem : показать все функции из файла и сохранить память
    import importlib.util
    sp = importlib.util.spec_from_file_location('lessons', sys.argv[1]); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
    s = socket.create_connection(('127.0.0.1', int(sys.argv[2]))); f = s.makefile('rw', newline='\n'); T = Teacher(f)
    for fn in [v for v in vars(m).values() if inspect.isfunction(v)]:
        c, ms = T.teach(fn); print(fn.__name__, 'фигур', c, f'{ms:.1f} мс')
    f.write(f"@SAVE {os.path.abspath(sys.argv[3])}\n"); f.flush(); print(f.readline().strip())
