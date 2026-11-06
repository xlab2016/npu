"""Манифест операций в таблицу для процессора. Данные, а не логика: новый манифест не трогает навыки."""
import json, sys
d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else 'operations.json')); F = sorted({f for o in d['operations'] for k in ('requires', 'produces', 'invalidates') for f in o[k]} | set(d['goalFacts']))
assert len(F) <= 30; b = {f: i for i, f in enumerate(F)}; m = lambda l: sum(1 << b[x] for x in l)
run = [f for f in F if f.endswith('_THIS_RUN') or f in ('SERVICE_STARTING', 'GIT_CHANGES_APPLIED', 'UPDATE_COMPLETE')]
with open('update.tab', 'w') as o:
    o.write(f"H {len(d['operations'])} {m(d['goalFacts'])} {m(run)} {1 << b['NO_OPERATION_ERROR']} {len(F)}\n")
    for f in F: o.write(f"F {f}\n")
    for x in d['operations']: o.write(f"O {x['id']} {m(x['requires'])} {m(x['produces'])} {m(x['invalidates'])} {round(x['cost']*100)} {x['displayName']}\n")
print(len(F), 'фактов', len(d['operations']), 'операций')
