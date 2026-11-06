"""Такт за тактом сравнивает решение сети (веса из файла, numpy) с эталоном."""
import sys, struct, numpy as np
sys.path.insert(0, '.')
from machine import *
def load(p):
    b = open(p, 'rb').read(); _, D, WB, K, NL, G = struct.unpack('<4sIIIII', b[:24]); o = 24
    def rd(n):
        nonlocal o
        a = np.frombuffer(b, '<f4', n, o); o += 4*n; return a
    b0 = rd(WB); O0 = rd(WB*D).reshape(WB, D); L = []
    for i in range(NL):
        n, d = struct.unpack('<II', b[o:o+8]); o += 8
        L.append((rd(n*d).reshape(n, d), rd(n), rd(K*d).reshape(K, d), rd(n*K).reshape(n, K), rd(WB*n).reshape(WB, n)))
    return b0, O0, L
def fwd(m, f):
    b0, O0, L = m; x = np.array(f, 'f4')*2-1; y = b0 + O0 @ x; i = x
    for W, b, P, Q, O in L:
        h = np.maximum(W @ i + b + Q @ ((P @ i)**2), 0); y = y + O @ h; i = np.concatenate([x, h])
    return sum(1 << k for k in range(len(y)) if y[k] > 0)
if __name__ == '__main__':
    m = load(sys.argv[1]); rows, lab = assemble()
    t = sys.argv[2].encode().decode('unicode_escape').encode()
    M = Machine(rows, t); bad = n = 0
    while M.cycles < int(sys.argv[3]):
        f = M.feat(); w = M.teach(f); W = word(*w); g = fwd(m, f); n += 1
        if g != W:
            bad += 1
            if bad < 12: print('pc', M.pc, rows[M.pc].src, 'want', w, 'got', g&31, g>>5&15, g>>9&255, g>>17, 'bits', [k for k in range(27) if (g^W)>>k&1])
        if not M.exec(*w): break
    print('cycles', n, 'bad', bad, M.out)
