#!/bin/bash
# первый круг: три зерна для одного и двух проходов, затем mlp и слепой перебор
for s in 2 3 4; do
 python3 learn.py --mode geo --rounds 1 --seed $s --tag .s$s > geo.s$s.log 2>&1 &
 python3 learn.py --mode hyper --rounds 1 --seed $s --tag .s$s > hyper.s$s.log 2>&1 &
 wait
done
python3 learn.py --mode mlp --rounds 1 --seed 2 --tag .s2 > mlp.s2.log 2>&1 &
python3 learn.py --mode blind --rounds 1 --tag .s2 > blind.s2.log 2>&1 &
wait
touch cmp.done
