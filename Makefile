nc_bin: runtime/nc.c runtime/work.h
	gcc -O3 -march=native -ffast-math -funroll-loops runtime/nc.c -o nc_bin -lm
train:
	cd nc && python3 train.py
check: nc_bin
	python3 tests/check.py ./nc_bin models/nc.bin 200
