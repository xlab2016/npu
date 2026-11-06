"""Проверка режима COM-порта: nc открывает виртуальный последовательный порт, клиент работает с ним как с файлом устройства."""
import subprocess, re, os, sys, time, termios, tty, select
p = subprocess.Popen([sys.argv[1], '--model', sys.argv[2], '--pty'], stderr=subprocess.PIPE, text=True)
dev = None
while dev is None:
    m = re.search(r'порт (/dev/\S+)', p.stderr.readline())
    if m: dev = m[1]
fd = os.open(dev, os.O_RDWR | os.O_NOCTTY); tty.setraw(fd)
buf = b''
for cmd in [b'MUL 123456789 987654321\n', b'2+3*(4-1)^2\n', b'MODPOW 7 1000000 998244353\n']:
    os.write(fd, cmd); line = b''
    while not line.endswith(b'\n'):
        r, _, _ = select.select([fd], [], [], 10)
        if not r: print('нет ответа'); sys.exit(1)
        line += os.read(fd, 256)
    print(dev, cmd.strip().decode(), '->', line.strip().decode())
p.kill()
